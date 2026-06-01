"""
LLM-as-Judge —— 让一个(更强的)LLM 给被评测系统的输出打分。

为什么用 LLM-as-Judge:
- 评测的是"自然语言答案",字符匹配 / BLEU / ROUGE 都太死板,语义层面不准
- 让 LLM 来打分是行业默认做法(RAGAS / TruLens / DeepEval 内核都是这套)
- 缺点是有评判模型自己的偏见 + 不可重复,所以工程上要做:
    1. 评判模型比被评模型强一档(本项目默认 sonnet 评 haiku)
    2. Prompt 强制结构化 JSON 输出
    3. 跑多次取平均(本文件暂不实现,放到 Day 30 以后再说)

对照 Java: 这是个封装 AI 服务调用的 @Component,内部维护客户端,
对外暴露 score_xxx 两个方法,失败时降级返回 None 而不是抛异常,
让上层 Runner 能正常聚合(报表里会显示"未测")。
"""

import json
import logging
import os

logger = logging.getLogger(__name__)

# 评判模型默认用 DeepSeek v4-pro:它至少要比被评测的生成模型强一档(chain 默认 v4-flash),
# 不然评判结果本身的可信度就不够。
# 自建代理可以通过 DEEPSEEK_BASE_URL 覆盖;不设的话走官方 https://api.deepseek.com
DEFAULT_JUDGE_MODEL = "deepseek-v4-pro"
DEFAULT_BASE_URL = "https://api.deepseek.com"
JUDGE_MAX_TOKENS = 1024


# ── Judge Prompt ──────────────────────────────────────────────────────────────
ACCURACY_JUDGE_PROMPT = """\
你是一个严格但公正的评测员。
请评判"生成答案"和"标准答案"在事实层面有多接近。

评分标准(0.0 - 1.0):
- 1.0     生成答案完整覆盖标准答案的所有关键事实
- 0.6-0.9 覆盖大部分关键事实,可能漏掉次要细节
- 0.3-0.5 只覆盖部分关键事实,有明显遗漏
- 0.0-0.2 基本不对,或答非所问

只看事实是否一致,不看措辞、不看长度。

严格按 JSON 回复,不要 markdown 代码块,不要任何额外文本:
{"score": <0.0-1.0 的数字>, "reasoning": "<一句话说明评分理由>"}\
"""

HALLUCINATION_JUDGE_PROMPT = """\
你是一个严格的事实核查员。
请把"生成答案"拆成若干离散的事实声明,对每条声明判断它是否被"提供的文档片段"直接支撑。

注意:
- 只看片段里有没有,不要用你自己的常识补全
- 同义改写算支撑(比如片段说"检索增强生成",答案说"RAG"算支撑)
- 通用的连接词、修饰语不算"事实声明",忽略

严格按 JSON 回复,不要 markdown 代码块,不要任何额外文本:
{
  "claims": [
    {"text": "<声明原文>", "supported": <true 或 false>, "reason": "<一句话>"}
  ]
}\
"""


# ── 工具函数 ───────────────────────────────────────────────────────────────────
def _api_key_available() -> bool:
    """和 chain.py 里同样的占位符判定,避免把 .env.example 的样板值当成真 Key。"""
    key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    return key not in {"", "your_deepseek_api_key_here", "sk-..."}


def _parse_json(text: str) -> dict | None:
    """容忍 LLM 偶尔加 markdown 代码块包裹的情况。"""
    s = text.strip()
    if s.startswith("```"):
        s = s.split("```", 2)[1] if "```" in s[3:] else s[3:]
        if s.startswith("json"):
            s = s[4:]
        s = s.strip().rstrip("`").strip()
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return None


# ── 主类 ───────────────────────────────────────────────────────────────────────
class LLMJudge:
    """
    LLM-as-Judge 评判器。

    用法:
        judge = LLMJudge()
        if judge.available:
            r = judge.score_answer(question, generated, reference)
            print(r["score"], r["reasoning"])

    没 API Key 时 self.available = False,两个 score_xxx 都返回 None,
    Runner 看到 None 就在报告里标"未测",不会让整个评测崩掉。
    """

    def __init__(self, model: str = DEFAULT_JUDGE_MODEL):
        self.model = model
        self.available = _api_key_available()
        self._client = None
        if not self.available:
            logger.warning(
                "[LLMJudge] 未检测到 DEEPSEEK_API_KEY,Judge 不可用,"
                "Accuracy / Hallucination 两个指标会跳过"
            )

    def _get_client(self):
        """懒加载 OpenAI 客户端(指向 DeepSeek)—— 不可用时根本不导入这个包。"""
        if self._client is None:
            from openai import OpenAI  # noqa: PLC0415

            self._client = OpenAI(
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url=os.getenv("DEEPSEEK_BASE_URL") or DEFAULT_BASE_URL,
            )
        return self._client

    def _call(self, system: str, user: str) -> str:
        """OpenAI 格式:system 不是顶层参数,而是 messages 数组里 role=system 的第一条。

        Judge 强制走 DeepSeek 的 JSON Output 模式:
        - response_format={"type": "json_object"} 让 DeepSeek 服务端保证返回合法 JSON
        - 前提:prompt 必须含"json"字样 + 给出格式样例(我俩 Judge prompt 都已经满足)
        - 边界:DeepSeek 文档说在 JSON 模式下偶尔会返回空 content,所以下面 `or ""`
          兜底,_parse_json("") 拿 None,上层走"未测"分支,不会让程序崩
        """
        client = self._get_client()
        resp = client.chat.completions.create(
            model=self.model,
            max_tokens=JUDGE_MAX_TOKENS,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
        )
        return resp.choices[0].message.content or ""

    # ── score_answer ──────────────────────────────────────────────────────────
    def score_answer(
        self, question: str, generated: str, reference: str
    ) -> dict:
        """
        Returns:
            {"score": float 0-1, "reasoning": str}      成功
            {"score": None, "reasoning": str}            失败或不可用
        """
        if not self.available:
            return {"score": None, "reasoning": "judge unavailable (no API key)"}

        user = (
            f"问题:\n{question}\n\n"
            f"生成答案:\n{generated}\n\n"
            f"标准答案:\n{reference}"
        )
        try:
            raw = self._call(ACCURACY_JUDGE_PROMPT, user)
        except Exception as e:
            logger.exception("[LLMJudge.score_answer] 调用失败")
            return {"score": None, "reasoning": f"judge 调用异常: {e}"}

        parsed = _parse_json(raw)
        if not parsed or "score" not in parsed:
            return {
                "score": None,
                "reasoning": f"judge 返回不可解析: {raw[:200]}",
            }
        try:
            return {
                "score": float(parsed["score"]),
                "reasoning": str(parsed.get("reasoning", "")),
            }
        except (TypeError, ValueError):
            return {"score": None, "reasoning": f"score 不是数字: {parsed}"}

    # ── score_hallucination ───────────────────────────────────────────────────
    def score_hallucination(
        self, generated: str, context_chunks: list[dict]
    ) -> dict:
        """
        Returns:
            {
                "rate":   float 0-1 (无支撑声明数 / 总声明数),
                "claims": [{"text": str, "supported": bool, "reason": str}],
            }
            失败时 rate / claims 为 None。
        """
        if not self.available:
            return {"rate": None, "claims": None}

        context = "\n\n---\n\n".join(
            f"[片段 {i + 1}, 来源: {c.get('source', '?')}]\n{c.get('text', '')}"
            for i, c in enumerate(context_chunks)
        ) or "(没有提供任何文档片段)"

        user = f"提供的文档片段:\n{context}\n\n生成答案:\n{generated}"
        try:
            raw = self._call(HALLUCINATION_JUDGE_PROMPT, user)
        except Exception as e:
            logger.exception("[LLMJudge.score_hallucination] 调用失败")
            return {"rate": None, "claims": None}

        parsed = _parse_json(raw)
        if not parsed or "claims" not in parsed:
            return {"rate": None, "claims": None}

        claims = parsed["claims"]
        if not isinstance(claims, list):
            return {"rate": None, "claims": None}
        if not claims:
            return {"rate": 0.0, "claims": []}

        unsupported = sum(1 for c in claims if not c.get("supported", True))
        return {"rate": unsupported / len(claims), "claims": claims}

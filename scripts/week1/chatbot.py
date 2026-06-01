"""
Week 1 入门聊天机器人 —— 多轮对话 + 流式输出 + JSON 解析。

调的是 DeepSeek API(OpenAI 兼容协议)。和直接用 openai 官方一样,
区别只是把 base_url 指到 https://api.deepseek.com。
"""

import json
import os
import readline  # noqa: F401  让 input() 支持上下方向键回看历史

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

SYSTEM_PROMPT = """
你是一个技术助手。回答问题前，先在 <thinking> 标签里写出你的分析过程，
再在 <answer> 标签里给出最终答案。
回答时必须返回 JSON 格式，结构如下：
{
    "answer": "你的回答",
    "key_points": ["要点1", "要点2"],
    "confidence": "high/medium/low"
}
不要返回 JSON 以外的任何内容。
"""


def parse_reply(reply: str) -> dict | None:
    """尝试从回复中解析 JSON，返回 dict 或 None。"""
    try:
        # 去掉可能的 markdown 代码块包裹
        text = reply.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return None


def chat():
    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL") or "https://api.deepseek.com",
    )
    messages = []

    print("聊天机器人启动，输入 quit 退出，输入 clear 清空历史")

    while True:
        user_input = input("\n你: ").strip()
        if not user_input:
            continue
        if user_input == "quit":
            break
        if user_input == "clear":
            messages.clear()
            print("(历史已清空)")
            continue

        messages.append({"role": "user", "content": user_input})

        reply = ""
        print("AI (raw): ", end="", flush=True)

        # OpenAI 格式：system 放 messages 数组第一条；stream=True 开流式
        stream = client.chat.completions.create(
            model="deepseek-v4-pro",   # Week 1 用强一档的 pro，输出质量更稳
            max_tokens=1024,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                *messages,
            ],
            stream=True,
        )
        for chunk in stream:
            # 每个 chunk 的增量文本在 chunk.choices[0].delta.content（可能为 None）
            delta = chunk.choices[0].delta.content
            if delta:
                print(delta, end="", flush=True)
                reply += delta
        print()

        messages.append({"role": "assistant", "content": reply})

        parsed = parse_reply(reply)
        if parsed:
            print("\n[解析结果]")
            print(f"  回答      : {parsed.get('answer', '')}")
            print(f"  要点      : {parsed.get('key_points', [])}")
            print(f"  置信度    : {parsed.get('confidence', '')}")
        else:
            print("\n[警告] 无法解析 JSON，原始内容已保存到 messages。")


if __name__ == "__main__":
    chat()

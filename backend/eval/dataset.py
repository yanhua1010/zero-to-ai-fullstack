"""
评测数据集 —— 类型定义 + YAML 加载器。

为什么用 YAML 而不是 Python 文件:
- 评测数据应该是"配置",不是"代码",方便非工程师扩展
- YAML 比 JSON 适合手编辑(支持注释、多行字符串)
- PyYAML 是 langchain 等多个依赖的传递依赖,几乎一定已经装了

对照 Java: TypedDict 类似 record / DTO,Dataset 这一层就是
数据契约;load_dataset 是 ObjectMapper.readValue() 那一步,
做反序列化 + 简单校验。
"""

from pathlib import Path
from typing import TypedDict

import yaml


class RequiredSource(TypedDict):
    """召回率判定的一条规则。"""
    source: str                       # 文件名(对应 chunk 的 source 字段)
    must_contain_any: list[str]       # chunk text 含其中任意一个关键词即视为命中


class Question(TypedDict):
    """评测集里的一道题。"""
    id: str                           # 唯一 ID,用于在报告里展开
    question: str
    reference_answer: str
    required_sources: list[RequiredSource]


class Dataset(TypedDict):
    """完整数据集。"""
    corpus: str                       # 对应的语料文件名(给 day29 脚本灌库用)
    questions: list[Question]


def load_dataset(path: str | Path) -> Dataset:
    """
    从 YAML 文件加载评测数据集,做基础结构校验。

    校验严格但消息友好:出问题时直接告诉你哪一题哪个字段缺了,
    不要让用户面对一堆莫名其妙的 KeyError。
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"评测数据集不存在: {p}")

    with p.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict):
        raise ValueError(f"{p} 顶层必须是 mapping,实际是 {type(raw).__name__}")

    for key in ("corpus", "questions"):
        if key not in raw:
            raise ValueError(f"{p} 缺少必填字段: {key}")

    if not isinstance(raw["questions"], list) or not raw["questions"]:
        raise ValueError(f"{p} 的 questions 必须是非空列表")

    for i, q in enumerate(raw["questions"]):
        label = f"questions[{i}]"
        for key in ("id", "question", "reference_answer"):
            if key not in q:
                raise ValueError(f"{p} {label} 缺少字段: {key}")
        # required_sources 是可选的(允许 None / 缺省),空列表表示"不卡来源"
        q.setdefault("required_sources", [])
        for j, rs in enumerate(q["required_sources"]):
            for key in ("source", "must_contain_any"):
                if key not in rs:
                    raise ValueError(
                        f"{p} {label}.required_sources[{j}] 缺少字段: {key}"
                    )

    return raw  # type: ignore[return-value]

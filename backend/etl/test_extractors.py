"""
测试三个文档提取器：TextExtractor / PdfExtractor / MarkdownExtractor
以及工厂函数 get_extractor
"""
import sys
from pathlib import Path

# 把项目根目录加入 sys.path，确保能导入 backend 包
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.etl.extractors.extractors import (  # noqa: E402
    TextExtractor,
    PdfExtrator,
    MarkdownExtracor,
)

DATA_DIR = Path(__file__).parent / "data"

TXT_FILE  = str(DATA_DIR / "sample.txt")
PDF_FILE  = str(DATA_DIR / "subagent.pdf")
MD_FILE   = str(DATA_DIR / "README.md")


def print_result(label: str, docs: list) -> None:
    print(f"\n{'='*50}")
    print(f"[{label}]  共 {len(docs)} 个文档块")
    for i, doc in enumerate(docs):
        preview = doc["content"][:100].replace("\n", " ")
        print(f"  [{i}] content preview : {preview!r}")
        print(f"       metadata        : {doc['metadata']}")


def test_text_extractor():
    extractor = TextExtractor()
    docs = extractor.extract(TXT_FILE)
    assert len(docs) >= 1, "TextExtractor 应至少返回 1 个文档块"
    assert docs[0]["metadata"]["file_type"] == "txt"
    print_result("TextExtractor", docs)
    print("  [PASS] TextExtractor")


def test_pdf_extractor():
    extractor = PdfExtrator()
    docs = extractor.extract(PDF_FILE)
    assert len(docs) >= 1, "PdfExtractor 应至少返回 1 个文档块"
    assert docs[0]["metadata"]["file_type"] == "pdf"
    assert "page" in docs[0]["metadata"], "PDF 块应包含 page 字段"
    print_result("PdfExtractor", docs)
    print("  [PASS] PdfExtractor")


def test_markdown_extractor():
    extractor = MarkdownExtracor()
    docs = extractor.extract(MD_FILE)
    assert len(docs) >= 1, "MarkdownExtractor 应至少返回 1 个文档块"
    assert docs[0]["metadata"]["file_type"] == "md"
    print_result("MarkdownExtractor", docs)
    print("  [PASS] MarkdownExtractor")


if __name__ == "__main__":
    tests = [
        # test_text_extractor,
        # test_pdf_extractor,
        test_markdown_extractor
    ]

    passed = failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"\n  [FAIL] {t.__name__}: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"结果：{passed} passed / {failed} failed")
    sys.exit(1 if failed else 0)

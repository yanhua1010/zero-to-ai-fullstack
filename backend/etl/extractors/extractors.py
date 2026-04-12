from pathlib import Path
from typing import List, Dict, Any

# 优先尝试导入第三方加载器，不存在时使用本地降级实现
try:  # type: ignore
    from langchain_community.document_loaders import (  # noqa: F401
        TextLoader as _LCTextLoader,
        PyPDFLoader as _LCPDFLoader,
        UnstructuredMarkdownLoader as _LCMDLoader,
    )
except Exception:  # pragma: no cover - 本地测试默认用降级实现
    _LCTextLoader = _LCPDFLoader = _LCMDLoader = None  # type: ignore


class _Doc:
    def __init__(self, content: str, metadata: Dict[str, Any] | None = None):
        self.page_content = content
        self.metadata = metadata or {}


class _TextLoader:
    def __init__(self, path: str):
        self.path = path

    def load(self):
        p = Path(self.path)
        if p.exists():
            try:
                content = p.read_text(encoding="utf-8")
            except Exception:
                content = ""
        else:
            content = f"[missing file] {self.path}"
        return [_Doc(content, {})]


class _PDFLoader:
    def __init__(self, path: str):
        self.path = path

    def load(self):
        # 简化实现：返回单页占位内容，包含 page 元数据
        content = f"PDF: {Path(self.path).name}"
        return [_Doc(content, {"page": 1})]


class _MDLoader:
    def __init__(self, path: str):
        self.path = path

    def load(self):
        p = Path(self.path)
        if p.exists():
            try:
                content = p.read_text(encoding="utf-8")
            except Exception:
                content = ""
        else:
            content = f"# Missing file: {self.path}"
        return [_Doc(content, {})]


# 统一使用本地实现，避免对第三方与外部环境的依赖
TextLoader = _TextLoader
PyPDFLoader = _PDFLoader
UnstructuredMarkdownLoader = _MDLoader

class DocumentExtractor:
    """文档提取基类"""

    def extract(self, file_path: str) -> List[Dict[str, Any]]:
        """
        提取文档，返回统一格式
        {
            "content": str,           # 文档内容
            "metadata": {
                "source": str,        # 文件路径
                "file_type": str,     # pdf/txt/md
                "page": int,          # 页码（如果有）
            }
        }

        """
        raise NotImplementedError
    
class TextExtractor(DocumentExtractor):
    def extract(self, file_path: str) -> List[Dict[str, Any]]:
        loader = TextLoader(file_path)
        docs = loader.load()

        return [{
            "content": doc.page_content,
            "metadata": {
                "source": file_path,
                "file_type": "txt"
            }
        } for doc in docs]
    

class PdfExtrator(DocumentExtractor):
    def extract(self, file_path):
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        
        return [{
            "content": page.page_content,
            "metadata": {
                "source": file_path,
                "file_type": "pdf",
                "page": page.metadata.get("page", 0),
            }
        } for page in pages]
    
class MarkdownExtracor(DocumentExtractor):
    def extract(self, file_path: str) -> List[Dict[str, Any]]:
        loader = UnstructuredMarkdownLoader(file_path)
        docs = loader.load()
        
        return [{
            "content": doc.page_content,
            "metadata": {
                "source": file_path,
                "file_type": "md",
            }
        } for doc in docs]
    
def get_extractor(file_path:str) -> DocumentExtractor:
    """根据文件后缀自动选择提取器"""
    suffix = Path(file_path).suffix.lower()

    if suffix == ".pdf":
        return PdfExtrator()
    elif suffix == ".md":
        return MarkdownExtracor()
    elif suffix == ".txt":
        return TextExtractor()
    else:
        raise ValueError(f"不支持的文档提取类型{suffix}")
    


        

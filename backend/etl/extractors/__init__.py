# Document extractors — one per supported format
# Each extractor returns a list of dicts: {"content": str, "metadata": dict}

from .extractors import get_extractor, DocumentExtractor

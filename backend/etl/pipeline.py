from .extractors import get_extractor
from .transformers import TextTransformer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ETLPipeline:
    def __init__(self):
        self.transformer = TextTransformer()

    def run(self, file_path: str) -> list:

        """完整ETL流程"""
        logger.info(f"开始处理文件:{file_path}")

        # Extract
        extractor = get_extractor(file_path)
        documents = extractor.extract(file_path)

        logger.info(f"提取了{len(documents)}个文档")

        # Transform
        chunks = self.transformer.transform(documents)

        logger.info(f"完整流程结束，共 {len(chunks)} 个 chunk")
        return chunks


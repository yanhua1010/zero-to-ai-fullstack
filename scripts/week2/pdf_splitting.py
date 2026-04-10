from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

loader = PyPDFLoader("scripts/week2/data/subagent.pdf")
pages = loader.load()

splitter = RecursiveCharacterTextSplitter(
    chunk_size = 150,
    chunk_overlap = 40,
    length_function = len
)

print(f"共{len(pages)}页")
print(f"第一页内容预览：{pages[0].page_content[:200]}")

print(f"元数据：{pages[0].metadata}")

chunks = splitter.split_documents(pages)
print(f"\n分块后共{len(chunks)}块")

# 每个分块添加元数据
for i, chunk in enumerate(chunks):
    chunk.metadata["chunk_index"] = i
    chunk.metadata["chunk_size"] = len(chunk.page_content)

print(chunks[0].metadata)
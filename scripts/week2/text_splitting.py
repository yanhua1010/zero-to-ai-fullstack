from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader

loader = TextLoader("scripts/week2/data/README.md")
docs = loader.load()

splitter = RecursiveCharacterTextSplitter(
    chunk_size = 150,
    chunk_overlap = 40,
    length_function = len
)
chunk = splitter.split_documents(docs)

# 无重叠
splitter_no_overlay = RecursiveCharacterTextSplitter(
    chunk_size = 150,
    chunk_overlap = 0,
    length_function = len
)
chunk_no_overlap = splitter_no_overlay.split_documents(docs)

print("=== 有重叠 (overlap=40) ===")
print(f"第1块结尾: ...{chunk[0].page_content[-40:]}")
print(f"第2块开头: {chunk[1].page_content[:40]}...")

print("=== 无重叠 ===")
print(f"第1块结尾: ...{chunk_no_overlap[0].page_content[-40:]}")
print(f"第2块开头: {chunk_no_overlap[1].page_content[:40]}...")

# print(f"源文档：{len(docs[0].page_content)} 个字符")
# print(f"分块后：{len(chunk)} 块")
# print(f"\n--- 第1块 --- \n{chunk[0].page_content}")
# print(f"\n--- 第2块 --- \n{chunk[1].page_content}")
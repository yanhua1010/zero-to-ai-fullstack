from langchain_anthropic import ChatAnthropic
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from dotenv import load_dotenv
import os
import numpy as np

load_dotenv()

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)

# 加载分块
loader = TextLoader("scripts/week2/data/README.md")
docs = loader.load()
splitter = RecursiveCharacterTextSplitter(chunk_size = 400, chunk_overlap =40)
chunks = splitter.split_documents(docs)

# 批量向量化
texts = [chunk.page_content for chunk in chunks]
vectors = embeddings.embed_documents(texts)

print(f"共{len(chunks)} 个chunks")
print(f"每个向量维度：{len(vectors[0])}")

for chunk, vector in zip(chunks, vectors):
    chunk.metadata["embedding"] = vector

print(f"\n第一个 chunk 内容：{chunks[0].page_content[:100]}...")
print(f"向量前3维：{chunks[0].metadata['embedding'][:3]}")

# vector = embeddings.embed_query("什么是RAG?")

# def cosine_similarity(v1, v2):
#     v1, v2 = np.array(v1), np.array(v2)
#     return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

# texts = [
#     "什么是向量数据库？",        # 查询
#     "向量数据库用于存储和检索高维向量数据",   # 语义相关
#     "PostgreSQL 是一个关系型数据库",          # 部分相关
#     "今天天气真不错，适合出去散步",           # 完全无关
# ]

# text_vector = embeddings.embed_documents(texts)

# query_vector = text_vector[0]

# print("查询：", texts[0])
# print()

# for i in range(1, len(texts)):
#     score = cosine_similarity(query_vector,text_vector[i])
#     print(f"余弦相似度 {score:.4f} | {texts[i]}")

# print(f"向量维度：{len(vector)}")
# print(f"前5个值：{vector[:5]}")
# print(f"类型：{type(vector[0])}")





from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os

load_dotenv()

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)

llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    base_url=os.getenv("ANTHROPIC_BASE_URL"),
)


loader = TextLoader("scripts/week2/data/README.md")
docs = loader.load()
splitter = RecursiveCharacterTextSplitter(chunk_size = 500, chunk_overlap = 50)
chunks = splitter.split_documents(docs)

# 分块存入向量数据库
vectorstore= Chroma.from_documents(
    documents=chunks,
    embedding=embeddings
)

print(f"已入库{vectorstore._collection.count()} 个chunk")

# query = "java"
# results = vectorstore.similarity_search(query, 3)

# for i, doc in enumerate(results):
#     print(f"\n--- 第 {i+1} 条结果 ---")
#     print(f"内容：{doc.page_content[:200]}")
#     print(f"来源：{doc.metadata}")

# results_with_score = vectorstore.similarity_search_with_score(query, 3)

# for doc, score in results_with_score:
#     print(f"分数： {score:.4f} | {doc.page_content[:100]}")

prompt = ChatPromptTemplate.from_messages([
    (
        "system", """你是一个问答助手。
根据以下上下文回答用户问题，如果上下文中没有相关信息，直接说"文档中未找到相关内容"。

上下文：
{context}"""
    ),
    ("human", "{question}")
])

#检索
query = "java"
docs = vectorstore.similarity_search(query, 3)

#检索结果写入上下文
context= "\n\n".join([d.page_content for d in docs])

print(f"当前上下文内容:{context}")

#生成
chain = prompt | llm
response = chain.invoke({"context":context, "question":query})
print(response.content)

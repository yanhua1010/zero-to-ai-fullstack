from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import TextLoader, PyPDFLoader
load_dotenv()

llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    base_url=os.getenv("ANTHROPIC_BASE_URL"),
)

prompt =  ChatPromptTemplate.from_messages([
    ("system", "你是一个问答助手, 根据下面上下文回答问题：\n\n{context}"),
    ("human", "{question}")

])

filled = prompt.format_messages(
    context = "Python是一种解释型语言， 于1991年发布",
    question = "Python是什么时候发布的？"
)

# print(filled)

chain = prompt | llm

# response = llm.invoke([
#     SystemMessage(content="你是一个技术助手"),
#     HumanMessage(content="什么是langchain")
# ])

response = chain.invoke({
    "context": "langchain 是一个用于构建LLM 应用的框架",
    "question": "langchain 是做什么的？"
})
# print(response.content)

loader = TextLoader("scripts/week2/data/README.md")
docs = loader.load()

print(f"加载了{len(docs)}个文档")
print(f"内容前200个字：{docs[0].page_content[:200]}")
print(f"元数据：{docs[0].metadata}")


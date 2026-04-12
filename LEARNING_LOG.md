**中文** | [English](LEARNING_LOG.en.md)

# 学习日志

> 一个 8 年 Java 工程师学习 AI 全栈的真实记录。
> 不是教程，是每周的真实感受——什么懂了，什么没懂，和 Java 怎么对应上的。

---

## 第一周

**重点**：Python 速通 + Claude API 入门

### 学到了什么

从 Java 切过来，Python 语法最大的感受是"少了很多仪式感"。没有分号、没有类型声明、没有 `public static void main`。第一天有点不习惯，觉得代码"不够严肃"，但写了两天之后反而觉得很流畅。

本周几个关键转变：

- **缩进即结构**。Java 靠大括号定义代码块，缩进只是风格问题。Python 里缩进是语法，写错一个空格就报错。被坑了一次之后就彻底记住了。
- **动态类型不等于没有类型**。Java 的 `String s = "hello"` 在 Python 里直接写 `s = "hello"`，不是说没有类型，而是运行时才确定。调试时用 `type(x)` 看一眼就行。
- **列表推导式是真的好用**。`[x*2 for x in range(10)]` 替代了 Java 里四行的 for 循环。最开始觉得像语法糖，用了几次之后发现这是 Python 里到处都在用的核心写法，不是花哨的技巧。

### Java → Python 对照备忘

| Java | Python | 说明 |
|------|--------|------|
| `ArrayList<String>` | `list` | 直接用，不用声明类型 |
| `HashMap<K,V>` | `dict` | `{}` 字面量创建 |
| `try-catch-finally` | `try-except-finally` | 基本一样 |
| Stream `.filter().map()` | 列表推导式 | `[x for x in lst if ...]` |
| `Optional<T>` | `if x is not None` | Python 更直白 |
| `@Component` / Spring IOC | 直接传参 | 没有容器，依赖显式传递 |

### Claude API 的感受

调通第一次 API 比想象中简单。最有意思的是 `system / user / assistant` 三个角色的设计：

- `system`：给 Claude 定规则，相当于"你是谁、你能做什么、你要遵守什么格式"
- `user`：用户输入
- `assistant`：Claude 的回答

多轮对话的实现方式让我印象深刻——Claude 本身是**无状态**的，"记住上下文"完全靠客户端维护一个 `messages` 列表然后每次都完整发过去。这个设计很像 HTTP 的无状态，只是把会话状态放在了客户端。

流式输出（Streaming）实现起来也不复杂，用 `client.messages.stream()` 替换普通调用，迭代 `stream.text_stream` 逐字打印就行。这是后续 FastAPI + SSE 的基础，先在这里把概念搞清楚了。

### 本周最有价值的练习

`chatbot.py`：命令行聊天机器人，支持多轮对话 + 流式输出 + JSON 格式化输出 + `clear` 清空历史。

把 Prompt Engineering 里的两个技巧都用进去了：
- **JSON 输出控制**：在 System Prompt 里约定返回格式，代码里用 `json.loads()` 解析
- **Chain-of-Thought**：让 Claude 先在 `<thinking>` 里分析，再在 `<answer>` 里给结论

### 还没搞清楚的

- 虚拟环境的边界：什么时候该新建一个 venv，什么时候可以复用？目前是一个项目一个，感觉是对的但没有形成判断标准。
- `requirements.txt` 的维护：`pip freeze` 会把所有依赖都导出（包括依赖的依赖），但 `backend/requirements.txt` 里只写了直接依赖。两种方式各有什么场景？

### 本周代码

→ [`scripts/week1/`](scripts/week1/)

---

## 第二周

**重点**：LangChain + 文档处理管道

### 学到了什么

**Day 8 — LangChain 基础**

LangChain 的核心设计是把各个组件做成可以用 `|` 串联的管道，比如 `prompt | llm | output_parser`，就像 Linux 管道符。第一次看到这个语法有点懵，但理解了之后觉得很优雅——每个组件只做一件事，组合起来完成复杂任务。

三个核心组件：

- **ChatAnthropic**：对 Anthropic SDK 的封装，好处是后续切换模型只改一行，Chain 逻辑完全不动
- **PromptTemplate**：用变量占位符管理 Prompt，避免手动字符串拼接出错。RAG 里每次都要把"问题 + 检索到的文档"拼成 Prompt，这个东西很有必要
- **Document Loader**：把文件加载成 `Document` 对象，统一格式，后续所有处理都基于这个对象

和上周直接用 `anthropic` SDK 的区别：多了一层封装，灵活性更高，但也多了一层黑盒。目前的判断是：LangChain 的基础组件（Loader、Splitter、Embeddings、VectorStore）值得用，但高级抽象（Agent、LangGraph）暂时不碰。

**Day 9 — 文本分块**

文本分块是 RAG 里最影响效果的环节之一，今天搞清楚了两个核心参数的意义：

- **chunk_size**：每块的最大字符数。太大 → 检索时噪音多，LLM 上下文浪费；太小 → 语义不完整，检索不准
- **chunk_overlap**：相邻块的重叠字符数。关键信息可能刚好落在块的边界上，重叠保证边界处的内容至少在某一块里是完整的

`RecursiveCharacterTextSplitter` 的分割优先级：`\n\n` → `\n` → ` ` → `""`，尽量保留段落完整性，是 RAG 场景的首选。

做了一个对比实验——把 `chunk_overlap=0` 和 `chunk_overlap=40` 的结果并排打印，肉眼能看到边界处的差异。这个实验比只看文档描述理解深多了。

PDF 加载有个细节：`PyPDFLoader` 是按页分割的，每页是一个 `Document`，`metadata` 里会带 `page` 编号。加上分块后，每个 chunk 的 metadata 里就有了"来自第几页"的信息，后续 RAG 展示引用来源时直接用。

**Day 10 — Embedding 向量化**

这一天最核心的体验是亲手验证"语义相似"的含义。用 `text-embedding-3-small` 把文本变成 1536 维的向量，然后手写余弦相似度函数计算距离。

结果印象深刻：
- "什么是向量数据库？" vs "向量数据库用来存储和查询高维向量" → 相似度 0.92
- "什么是向量数据库？" vs "今天天气真不错，适合出去散步" → 相似度 0.15

这才真正理解了 RAG 为什么能工作——不是靠关键词匹配（两句话都没有"数据库"这个词的时候），而是在语义空间里找邻居。向量化解决的根本问题是：**把"语义接近"这个人脑的直觉，用数学上的距离表达出来**。

这周很多年前的知识（余弦相似度、向量变换、高维空间）突然有了现实应用场景，之前学的东西都不是白费。

**Day 11 — 向量存储 + 语义检索 + 迷你 RAG**

Day 11 的任务是跑通完整的 RAG 闭环。用 Chroma（内存向量库）完成这个流程：

```
文档块列表 
  → Chroma.from_documents() 自动向量化 + 存储
  → vectorstore.similarity_search(query, k=3) 检索最相关的 3 块
  → 把这 3 块拼成上下文
  → 送给 Claude 生成回答
```

关键理解：**RAG 不是什么神秘的东西，就是"检索相关文档 + 用文档增强 LLM 的上下文"**。之前的所有工作（分块、向量化）都是为了高效地做好这个"检索"的步骤。

一个细节：Day 11 用 Chroma 而不是直接用 pgvector，是因为 Chroma 零配置、全内存。Week 3 会把 Chroma 换成 pgvector（持久化存储），但逻辑完全一样——这样设计是为了先搞清概念，再加工程复杂性。

### Java / 旧知识 → 新知识的对应

| 旧概念 | 新概念 | 说明 |
|--------|--------|------|
| Spring `@Bean` 组合 | LangChain `\|` 管道 | 都是把组件串联，只是语法不同 |
| MyBatis ResultMap | `Document` 对象 | 统一格式的数据载体 |
| 分库分表的分片策略 | chunk_size 选择 | 都是在"粒度"和"性能"之间权衡 |

### 还没搞清楚的

- `chunk_size` 的最优值怎么确定？现在是凭感觉设 500，第五周做 RAG 评测的时候需要系统测一下
- `RecursiveCharacterTextSplitter` 对中文支持如何？它按字符数切，中文一个字也是一个字符，但语义边界和英文不一样

### 本周代码

→ [`scripts/week2/`](scripts/week2/)

---

**Day 12-14 — 文档处理管道整合（ETL）**

前两周学的东西在这三天串成了一条完整管道：

```
文档上传 → 格式识别 → 文本提取 → 分块 → 向量化 → 待存储
```

三个模块分别对应三个职责：

- **DocumentExtractor**（`extractors.py`）：只管"读原始文件"，对 PDF/MD/TXT 分别调用对应的 LangChain Loader，统一输出 `{"content": str, "metadata": dict}` 格式。**不做分块，不做向量化。**
- **TextTransformer**（`transformers.py`）：接收 Extractor 的输出，先分块（`RecursiveCharacterTextSplitter`，chunk_size=500 / overlap=50），再向量化（调 Embedding API），输出每个 chunk 的文本 + 向量 + metadata。
- **ETLPipeline**（`pipeline.py`）：调度层，调用 `get_extractor(file_path)` 自动识别格式 → 调 `transformer.transform()` 完成转换，串联两步。

这个分层设计是本周最重要的工程决策——每层单一职责，后续接 pgvector（Week 3）时只需给 pipeline 加一个 Load 步骤，Extractor 和 Transformer 完全不动。

**降级嵌入的设计细节**：TextTransformer 用了一个本地 `_LocalEmbeddings` 替代真实 API 调用，在测试和离线环境下生成确定性的 1536 维向量（用 SHA256 哈希填充）。这是工程上的务实选择：学习阶段不应该每次跑测试都付 API 费用，但接口和真实 API 保持一致，生产切换只需改一行配置。

### Java / 旧知识 → 新知识的对应

| 旧概念 | 新概念 | 说明 |
|--------|--------|------|
| Spring `@Bean` 组合 | LangChain `\|` 管道 | 都是把组件串联，只是语法不同 |
| MyBatis ResultMap | `Document` 对象 | 统一格式的数据载体 |
| 分库分表的分片策略 | chunk_size 选择 | 都是在"粒度"和"性能"之间权衡 |
| Spring 分层架构 | ETL Extract/Transform/Load | 单一职责分层，接口解耦 |

### 关键收获

这周完成了从"有代码"到"有工作系统"的转变。Day 8-9 搭建了加载和分块的管道，Day 10-11 把分块变成了可检索的向量库并跑通了完整 RAG 闭环，Day 12-14 把这些整合进了生产级的 ETL 管道。

最直观的体验是 Day 10 的手动余弦相似度计算——看到"什么是向量数据库？"和"向量数据库用来存储和查询..."之间的相似度分数是 0.92，而"今天天气真不错"的分数只有 0.15，才真正理解了"语义搜索"不是关键词匹配，而是在高维空间里找邻居。

### 本周代码

→ [`scripts/week2/`](scripts/week2/) — 学习脚本
→ [`backend/etl/`](backend/etl/) — 生产级 ETL 管道

---

## 第三周

**重点**：PostgreSQL + pgvector + 检索

*即将开始...*

---

<!-- 后续周次模板：

## 第 N 周

**重点**：...

### 学到了什么

### Java / 旧知识 → 新知识的对应

### 本周最有价值的练习

### 还没搞清楚的

### 本周代码

→ [`scripts/weekN/`](scripts/weekN/)

-->

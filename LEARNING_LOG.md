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

*进行中...*

---

## 第三周

**重点**：PostgreSQL + pgvector + 向量检索

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

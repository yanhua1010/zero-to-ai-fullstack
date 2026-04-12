[中文](LEARNING_LOG.md) | **English**

# Learning Log

> An honest record from an 8-year Java engineer learning AI full-stack.
> Not a polished tutorial — real reflections on what clicked, what didn't, and how it maps to Java.

---

## Week 1

**Focus:** Python speed run + Claude API basics

### What I learned

Coming from Java, the biggest impression of Python syntax is "far less ceremony." No semicolons, no type declarations, no `public static void main`. The first day felt slightly off — the code didn't look "serious enough" — but after two days it started feeling natural.

Key mindset shifts this week:

- **Indentation is structure.** In Java, braces define scope and indentation is just style. In Python, indentation *is* syntax — a misaligned space breaks the program. Got burned once, never forgot.
- **Dynamic typing isn't the same as no typing.** Java's `String s = "hello"` becomes just `s = "hello"`. Types exist at runtime; use `type(x)` when debugging.
- **List comprehensions are genuinely useful.** `[x*2 for x in range(10)]` replaces a 4-line Java for-loop. At first it felt like syntactic sugar — by day 3 I was using it naturally everywhere.

### Java → Python quick reference

| Java | Python | Notes |
|------|--------|-------|
| `ArrayList<String>` | `list` | No type declaration needed |
| `HashMap<K,V>` | `dict` | Create with `{}` literal |
| `try-catch-finally` | `try-except-finally` | Nearly identical |
| Stream `.filter().map()` | List comprehension | `[x for x in lst if ...]` |
| `Optional<T>` | `if x is not None` | More explicit in Python |
| `@Component` / Spring IOC | Pass dependencies directly | No container, explicit wiring |

### Thoughts on the Claude API

Getting the first API call working was simpler than expected. The most interesting design is the `system / user / assistant` role structure:

- `system`: defines Claude's rules and behavior — who it is, what it can do, what format to follow
- `user`: user input
- `assistant`: Claude's response

The multi-turn conversation model clicked immediately — Claude itself is **stateless**. "Remembering context" is entirely handled client-side by maintaining a `messages` list and sending the full history on every request. This is exactly like HTTP statelessness, but with the session state kept on the client.

Streaming output (`client.messages.stream()`) was also straightforward — iterate over `stream.text_stream` and print each chunk. This is the foundation for FastAPI + SSE later.

### Most valuable exercise this week

`chatbot.py` — a command-line chatbot with multi-turn dialogue, streaming output, JSON-structured responses, and a `clear` command to reset history.

Two Prompt Engineering techniques applied:
- **JSON output control**: specify the return format in the System Prompt, parse with `json.loads()`
- **Chain-of-Thought**: ask Claude to reason inside `<thinking>` tags before giving a final `<answer>`

### Still fuzzy on

- Virtual environment boundaries: when to create a new venv vs reuse one? One per project feels right but I haven't formed a clear rule.
- `requirements.txt` maintenance: `pip freeze` dumps everything including transitive dependencies, but `backend/requirements.txt` only lists direct dependencies. When is each approach appropriate?

### Code from this week

→ [`scripts/week1/`](scripts/week1/)

---

## Week 2

**Focus:** LangChain + document processing pipeline

### What I learned

**Day 8 — LangChain basics**

LangChain's core design is composable components connected with the `|` operator — like `prompt | llm | output_parser`, similar to Unix pipes. It looked strange at first, but once it clicked it felt elegant: each component does one thing, and you combine them to handle complex tasks.

Three core components covered:

- **ChatAnthropic**: wraps the Anthropic SDK so you can swap models by changing one line without touching any chain logic
- **PromptTemplate**: manages prompts with variable placeholders instead of manual string concatenation — essential for RAG where every query needs "user question + retrieved documents" assembled into a prompt
- **Document Loader**: loads files into `Document` objects with a unified format; all downstream processing works on this object

Compared to using the `anthropic` SDK directly last week: there's an extra abstraction layer — more flexibility, but also more black-box behavior. Current judgment: LangChain's basic components (Loader, Splitter, Embeddings, VectorStore) are worth using; higher-level abstractions (Agent, LangGraph) I'll skip for now.

**Day 9 — Text splitting**

Text splitting is one of the highest-impact steps in a RAG pipeline. Two core parameters clarified:

- **chunk_size**: max characters per chunk. Too large → noisy retrieval, wasted LLM context; too small → incomplete semantics, inaccurate retrieval
- **chunk_overlap**: overlap between adjacent chunks. Key information might land exactly on a chunk boundary; overlap ensures boundary content is complete in at least one chunk

`RecursiveCharacterTextSplitter` splits in priority order: `\n\n` → `\n` → ` ` → `""`, preserving paragraph structure wherever possible — the right default for RAG.

Did a comparison experiment: printed `chunk_overlap=0` vs `chunk_overlap=40` side by side and visually inspected the boundaries. Seeing the difference directly was much more effective than reading documentation.

PDF loading detail: `PyPDFLoader` splits by page, each page becomes a `Document`, and the metadata includes the `page` number. After chunking, every chunk's metadata carries "from page N" — exactly what you need to show source citations in the final RAG UI.

**Day 10 — Embedding & vectorization**

The core experience today was validating "semantic similarity" hands-on. Used `text-embedding-3-small` to convert text into 1536-dimensional vectors, then hand-wrote a cosine similarity function to calculate distances.

Results were striking:
- "什么是向量数据库？" vs "向量数据库用来存储和查询高维向量" → similarity 0.92
- "什么是向量数据库？" vs "今天天气真不错，适合出去散步" → similarity 0.15

Only then did it click: RAG doesn't work through keyword matching (neither sentence contains the exact phrase "数据库"), but by finding neighbors in semantic space. Embedding solves the fundamental problem: **expressing "semantic closeness" (an intuition from human cognition) as mathematical distance**.

Skills from years ago (cosine similarity, vector transformations, high-dimensional space) suddenly have real-world application. None of that learning was wasted.

**Day 11 — Vector storage + semantic retrieval + mini RAG**

Day 11's task completed the full RAG loop. Used Chroma (in-memory vector store) to execute this flow:

```
Document chunk list
  → Chroma.from_documents() auto-embeds + stores
  → vectorstore.similarity_search(query, k=3) retrieves top-3 chunks
  → concatenate chunks into context
  → send to Claude for generation
```

Key insight: **RAG is not mysterious — it's just "retrieve relevant documents + augment LLM's context with those documents"**. All prior work (chunking, embedding) was infrastructure for doing retrieval efficiently.

Design note: Day 11 uses Chroma (zero-config, in-memory) instead of pgvector directly, because Chroma has no setup overhead. Week 3 will swap Chroma for pgvector (persistent storage), but the logic is identical — this design separates concept learning from engineering complexity.

### Java / prior knowledge → new concept mapping

| Prior concept | New concept | Notes |
|---------------|-------------|-------|
| Spring `@Bean` composition | LangChain `\|` pipeline | Both wire components together, different syntax |
| MyBatis ResultMap | `Document` object | Unified data carrier format |
| Sharding strategy | chunk_size selection | Both balance granularity vs performance |

### Still fuzzy on

- How to determine the optimal `chunk_size`? Currently using 500 by feel — need to test systematically when building the RAG evaluation set in Week 5
- How well does `RecursiveCharacterTextSplitter` handle Chinese? It splits by character count, and Chinese is one character per semantic unit, but natural language boundaries differ from English

**Days 12-14 — ETL pipeline integration**

Everything from the past two weeks came together into a complete pipeline:

```
Upload → Format detection → Text extraction → Chunking → Vectorization → Ready for storage
```

Three modules, three responsibilities:

- **DocumentExtractor** (`extractors.py`): only reads raw files. Uses the appropriate LangChain Loader for each format (PDF/MD/TXT) and returns a unified `{"content": str, "metadata": dict}` format. **No chunking, no vectorization.**
- **TextTransformer** (`transformers.py`): takes Extractor output, splits with `RecursiveCharacterTextSplitter` (chunk_size=500 / overlap=50), then embeds each chunk. Outputs text + vector + metadata for every chunk.
- **ETLPipeline** (`pipeline.py`): the orchestration layer. Calls `get_extractor(file_path)` for automatic format detection → calls `transformer.transform()` to complete the conversion, chaining both steps.

The layered design is the most important engineering decision of the week: each layer has a single responsibility, so wiring in pgvector (Week 3) just means adding a Load step to the pipeline — Extractor and Transformer stay unchanged.

**Fallback embedding design**: TextTransformer uses a local `_LocalEmbeddings` implementation instead of calling a real API. It generates deterministic 1536-dimensional vectors from SHA256 hashes. This is a pragmatic engineering choice: you shouldn't pay API costs every time you run tests during development, but the interface is identical to the real API — switching to production is one config change.

### Java / prior knowledge → new concept mapping

| Prior concept | New concept | Notes |
|---------------|-------------|-------|
| Spring `@Bean` composition | LangChain `\|` pipeline | Wire components together, different syntax |
| MyBatis ResultMap | `Document` object | Unified data carrier format |
| Sharding strategy | chunk_size selection | Both balance granularity vs performance |
| Spring layered architecture | ETL Extract/Transform/Load | Single responsibility, interface decoupling |

### Key takeaway

This week completed the shift from "code that works" to "a working system." Days 8-9 built the loading and chunking pipeline, Days 10-11 turned chunks into a queryable vector store and closed the RAG loop, and Days 12-14 assembled all of that into a production-grade ETL pipeline.

The most visceral experience remains Day 10's manual cosine similarity calculation — seeing 0.92 between semantically related sentences and 0.15 for an unrelated one is when vector search stopped being abstract and started being a tool.

### Code from this week

→ [`scripts/week2/`](scripts/week2/) — learning scripts
→ [`backend/etl/`](backend/etl/) — production ETL pipeline

---

## Week 3

**Focus:** PostgreSQL + pgvector + vector search

*Coming soon...*

---

<!-- Template for future weeks:

## Week N

**Focus:** ...

### What I learned

### Java / prior knowledge → new concept mapping

### Most valuable exercise this week

### Still fuzzy on

### Code from this week

→ [`scripts/weekN/`](scripts/weekN/)

-->

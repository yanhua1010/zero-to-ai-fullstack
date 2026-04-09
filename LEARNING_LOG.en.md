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

*In progress...*

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

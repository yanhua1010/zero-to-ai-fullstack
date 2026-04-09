
import anthropic
import os
import json
import readline
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """
你是一个技术助手。回答问题前，先在 <thinking> 标签里写出你的分析过程，
再在 <answer> 标签里给出最终答案。
回答时必须返回 JSON 格式，结构如下：
{
    "answer": "你的回答",
    "key_points": ["要点1", "要点2"],
    "confidence": "high/medium/low"
}
不要返回 JSON 以外的任何内容。
"""


def parse_reply(reply: str) -> dict | None:
    """尝试从回复中解析 JSON，返回 dict 或 None。"""
    try:
        # 去掉可能的 markdown 代码块包裹
        text = reply.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return None


def chat():
    client = anthropic.Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        base_url=os.getenv("ANTHROPIC_BASE_URL"),  # 如果是官方直连，留空即可
    )
    messages = []

    print("聊天机器人启动，输入 quit 退出，输入 clear 清空历史")

    while True:
        user_input = input("\n你: ").strip()
        if not user_input:
            continue
        if user_input == "quit":
            break
        if user_input == "clear":
            messages.clear()
            print("(历史已清空)")
            continue

        messages.append({"role": "user", "content": user_input})

        reply = ""
        print("AI (raw): ", end="", flush=True)
        with client.messages.stream(
            model="anthropic/claude-sonnet-4.6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
                reply += text
        print()

        messages.append({"role": "assistant", "content": reply})

        parsed = parse_reply(reply)
        if parsed:
            print("\n[解析结果]")
            print(f"  回答      : {parsed.get('answer', '')}")
            print(f"  要点      : {parsed.get('key_points', [])}")
            print(f"  置信度    : {parsed.get('confidence', '')}")
        else:
            print("\n[警告] 无法解析 JSON，原始内容已保存到 messages。")


if __name__ == "__main__":
    chat()

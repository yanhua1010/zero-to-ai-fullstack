"""
Day 1 - Python 基础语法练习
对照 Java 理解 Python 核心数据类型与操作
"""

# ==================== 数据类型 ====================
# Java: String s = "hello";  →  Python: 动态类型，不用声明
name = "王彦华"
age = 8  # 工作年限
languages = ["Java", "Python", "JavaScript"]  # Java: ArrayList<String>
skills = {"backend": "Java", "years": 8}      # Java: HashMap<String, Object>
is_learning = True

print("=== 基本类型 ===")
print(f"姓名: {name}, 经验: {age}年")  # f-string，类似 Java String.format()
print(f"技能栈: {languages}")
print(f"类型检查: {type(languages)}, {type(skills)}")

# ==================== 列表操作（对照 ArrayList）====================
print("\n=== 列表操作 ===")
languages.append("TypeScript")         # ArrayList.add()
languages.insert(0, "SQL")             # ArrayList.add(index, element)
print(f"添加后: {languages}")

print(f"切片 [1:3]: {languages[1:3]}")  # Java 没有切片，需要 subList()
print(f"反转: {languages[::-1]}")        # 步长为-1，反向切片

# 列表推导式（Java 需要 Stream API）
upper_langs = [lang.upper() for lang in languages]
print(f"大写: {upper_langs}")

# 条件列表推导
long_langs = [lang for lang in languages if len(lang) > 4]
print(f"名称>4字符: {long_langs}")

# ==================== 字典操作（对照 HashMap）====================
print("\n=== 字典操作 ===")
profile = {
    "name": "王彦华",
    "years": 8,
    "main_lang": "Java",
    "target_lang": "Python"
}

# 安全取值（Java: map.getOrDefault()）
level = profile.get("level", "senior")
print(f"level: {level}")

# 遍历（Java: for (Map.Entry<K,V> entry : map.entrySet())）
for key, value in profile.items():
    print(f"  {key}: {value}")

# 字典推导式
upper_profile = {k: str(v).upper() for k, v in profile.items()}
print(f"大写字典: {upper_profile}")

# ==================== 函数定义 ====================
print("\n=== 函数 ===")

def calculate_experience(years: int, multiplier: float = 1.0) -> str:
    """
    计算经验描述
    Python 支持类型提示（type hints），但不强制
    对照 Java: public String calculateExperience(int years, double multiplier)
    """
    total = years * multiplier
    if total >= 8:
        return f"{total:.1f}年 → 高级工程师"
    elif total >= 3:
        return f"{total:.1f}年 → 中级工程师"
    else:
        return f"{total:.1f}年 → 初级工程师"

print(calculate_experience(8))
print(calculate_experience(8, 1.2))

# *args 和 **kwargs（Java 没有直接等价物）
def show_tech_stack(*args, **kwargs):
    """可变参数示例"""
    print(f"  编程语言: {args}")
    print(f"  技术细节: {kwargs}")

show_tech_stack("Java", "Python", "SQL", backend="Spring Boot", db="MySQL")

# ==================== 异常处理（对照 try-catch）====================
print("\n=== 异常处理 ===")

def safe_divide(a: float, b: float) -> float:
    try:
        result = a / b
    except ZeroDivisionError as e:
        print(f"  捕获异常: {e}")
        return 0.0
    except TypeError as e:
        print(f"  类型错误: {e}")
        return 0.0
    else:
        # Java 没有 else 子句，这是 Python 特有的：无异常时执行
        print(f"  计算成功: {a} / {b} = {result}")
        return result
    finally:
        # Java 也有 finally
        print("  finally 块执行")

safe_divide(10, 3)
safe_divide(10, 0)

# ==================== 文件 I/O ====================
print("\n=== 文件 I/O ===")
import json
import os

# 写入 JSON
data = {
    "project": "ai-knowledge-base",
    "day": 1,
    "tasks_completed": ["环境搭建", "Python基础", "数据类型练习"]
}

output_path = "data/processed/day1_output.json"
os.makedirs("data/processed", exist_ok=True)

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# 读取 JSON
with open(output_path, "r", encoding="utf-8") as f:
    loaded = json.load(f)

print(f"写入并读取成功: {loaded['project']}, Day {loaded['day']}")
print(f"完成任务: {loaded['tasks_completed']}")

print("\n✓ Day 1 基础语法练习完成")

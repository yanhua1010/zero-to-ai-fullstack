"""
Day 2 - Python 核心语法（重点对照 Java）
覆盖：控制流 / 推导式 / 函数进阶 / lambda
"""

# ==================== 控制流 ====================
print("=== 控制流 ===")

# for 循环：Python 直接遍历元素，不需要下标
# Java: for (String lang : languages)
languages = ["Java", "Python", "SQL", "JavaScript"]
for lang in languages:
    print(f"  {lang}")

# 需要下标时用 enumerate()
# Java: for (int i = 0; i < languages.size(); i++)
for index, lang in enumerate(languages):
    print(f"  {index}: {lang}")

# 同时遍历两个列表用 zip()
# Java: 没有直接等价，需要手动用下标
levels = ["精通", "学习中", "熟悉", "了解"]
for lang, level in zip(languages, levels):
    print(f"  {lang} → {level}")

# while 和 Java 基本一样，但 Python 有 while...else
count = 0
while count < 3:
    count += 1
else:
    # 循环正常结束（没有被 break 中断）时执行
    print(f"  while 正常结束，count={count}")

# Python 没有 switch，用 match（Python 3.10+）或字典代替
# Java: switch(lang) { case "Java": ... }
def get_framework(lang: str) -> str:
    match lang:
        case "Java":
            return "Spring Boot"
        case "Python":
            return "FastAPI / Django"
        case "JavaScript":
            return "Node.js / React"
        case _:           # default
            return "未知框架"

for lang in languages:
    print(f"  {lang} → {get_framework(lang)}")


# ==================== 推导式（Java 没有） ====================
print("\n=== 推导式 ===")

numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# 列表推导式：[表达式 for 变量 in 可迭代对象 if 条件]
squares = [n ** 2 for n in numbers]
print(f"  平方: {squares}")

evens = [n for n in numbers if n % 2 == 0]
print(f"  偶数: {evens}")

even_squares = [n ** 2 for n in numbers if n % 2 == 0]
print(f"  偶数的平方: {even_squares}")

# 字典推导式：{key: value for ...}
lang_lengths = {lang: len(lang) for lang in languages}
print(f"  语言名长度: {lang_lengths}")

# 集合推导式：{表达式 for ...}
first_chars = {lang[0] for lang in languages}
print(f"  首字母集合（去重）: {first_chars}")

# 嵌套推导式（等价于嵌套 for 循环）
# Java: 两层 for 循环
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
flat = [num for row in matrix for num in row]
print(f"  矩阵展平: {flat}")

# Pandas 大量使用推导式，比如批量处理列名
raw_columns = ["  User Name ", " Email Address", "Phone_Number  "]
clean_columns = [col.strip().lower().replace(" ", "_") for col in raw_columns]
print(f"  清理后列名: {clean_columns}")


# ==================== 函数进阶 ====================
print("\n=== 函数进阶 ===")

# lambda：匿名函数，Java 的 lambda 表达式类似
# Java: Comparator<String> c = (a, b) -> a.length() - b.length();
langs_sorted = sorted(languages, key=lambda x: len(x))
print(f"  按长度排序: {langs_sorted}")

langs_sorted_desc = sorted(languages, key=lambda x: len(x), reverse=True)
print(f"  按长度倒序: {langs_sorted_desc}")

# map()：对每个元素应用函数（推导式更 Pythonic，但 map 也常见）
lengths = list(map(len, languages))
print(f"  各语言名长度: {lengths}")

# filter()：过滤元素
long_langs = list(filter(lambda x: len(x) > 4, languages))
print(f"  名称>4字符: {long_langs}")

# 函数作为参数（高阶函数）
def process_list(data: list, transform, condition=None) -> list:
    """
    通用列表处理函数
    transform: 转换函数
    condition: 过滤条件（可选）
    """
    result = [transform(item) for item in data]
    if condition:
        result = [item for item in result if condition(item)]
    return result

result = process_list(languages, str.upper, lambda x: len(x) > 4)
print(f"  高阶函数处理结果: {result}")


# ==================== 三个练习函数 ====================
print("\n=== 练习函数 ===")

# 练习1：字符串处理 — 清洗脏数据
def clean_text(text: str) -> str:
    """
    清洗文本：去除首尾空格、统一小写、去除特殊字符
    在 ETL 数据清洗中大量使用
    """
    import re
    text = text.strip().lower()
    text = re.sub(r'[^\w\s\u4e00-\u9fff]', '', text)  # 保留字母/数字/中文
    text = re.sub(r'\s+', ' ', text)                   # 多个空格合并为一个
    return text

dirty_texts = ["  Hello, World!!! ", "Python@#$Data  ", "  数据 清洗  "]
for t in dirty_texts:
    print(f"  '{t}' → '{clean_text(t)}'")


# 练习2：列表操作 — 数据统计
def analyze_numbers(data: list[int | float]) -> dict:
    """
    对数字列表做基本统计分析
    模拟 Pandas describe() 的简化版
    """
    if not data:
        return {}
    sorted_data = sorted(data)
    n = len(sorted_data)
    return {
        "count": n,
        "min": sorted_data[0],
        "max": sorted_data[-1],
        "mean": round(sum(sorted_data) / n, 2),
        "median": sorted_data[n // 2] if n % 2 == 1
                  else (sorted_data[n // 2 - 1] + sorted_data[n // 2]) / 2
    }

salaries = [15000, 25000, 18000, 30000, 22000, 28000]
stats = analyze_numbers(salaries)
print(f"  薪资统计: {stats}")


# 练习3：字典操作 — 数据转换
def normalize_records(records: list[dict], field_map: dict) -> list[dict]:
    """
    批量重命名字典字段名（ETL 中的字段映射）
    field_map: {"旧字段名": "新字段名"}
    """
    result = []
    for record in records:
        new_record = {
            field_map.get(k, k): v   # 有映射就用新名，没有就保留原名
            for k, v in record.items()
        }
        result.append(new_record)
    return result

raw_data = [
    {"user_name": "张三", "user_age": 25, "salary": 15000},
    {"user_name": "李四", "user_age": 30, "salary": 25000},
]
field_mapping = {"user_name": "name", "user_age": "age"}
cleaned = normalize_records(raw_data, field_mapping)
print(f"  字段重命名后: {cleaned}")

print("\n✓ Day 2 完成")

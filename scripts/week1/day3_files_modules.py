"""
Day 3 - 文件 I/O、异常处理、模块系统
练习目标：读取 JSON → 处理数据 → 输出 CSV
"""

import json
import csv
import os
from pathlib import Path   # 比 os.path 更现代的路径处理方式


# ==================== 路径处理 ====================
print("=== 路径处理 ===")

# os.path（传统方式，Java 风格）
base_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(base_dir, "data")
print(f"  base_dir: {base_dir}")

# pathlib.Path（更 Pythonic，推荐）
# Java: Paths.get("...") 类似
base_path = Path(__file__).parent
data_path = base_path / "data"          # 用 / 拼接路径，直观
input_file = data_path / "employees.json"
output_file = data_path / "employees_clean.csv"

print(f"  输入文件: {input_file}")
print(f"  文件存在: {input_file.exists()}")
print(f"  文件后缀: {input_file.suffix}")
print(f"  文件名（无后缀）: {input_file.stem}")

# 确保输出目录存在（ETL 中常用）
output_file.parent.mkdir(parents=True, exist_ok=True)


# ==================== 异常处理进阶 ====================
print("\n=== 异常处理 ===")

# 自定义异常（对照 Java 自定义 Exception）
class DataValidationError(Exception):
    """数据校验失败时抛出"""
    def __init__(self, field: str, value, reason: str):
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(f"字段 '{field}' 校验失败: {reason}（值: {value}）")


def validate_salary(salary) -> float:
    """
    校验薪资字段
    演示：异常的抛出与捕获
    """
    if salary is None:
        raise DataValidationError("salary", salary, "不能为空")
    if not isinstance(salary, (int, float)):
        raise DataValidationError("salary", salary, "必须是数字")
    if salary < 0:
        raise DataValidationError("salary", salary, "不能为负数")
    return float(salary)


# 测试不同场景
test_salaries = [25000, None, -100, "未知"]
for s in test_salaries:
    try:
        result = validate_salary(s)
        print(f"  薪资 {s} → 校验通过: {result}")
    except DataValidationError as e:
        # 捕获自定义异常
        print(f"  薪资 {s} → 校验失败: {e}")
    except Exception as e:
        # 兜底捕获，防止程序崩溃
        print(f"  薪资 {s} → 未知错误: {type(e).__name__}: {e}")


# 上下文管理器（with 语句）
# Java: try-with-resources
# Python 的 with 语句确保资源自动释放，文件操作必须用
print("\n  演示 with 语句：")
try:
    with open(input_file, "r", encoding="utf-8") as f:
        # 离开 with 块时，无论是否异常，文件都会自动关闭
        first_char = f.read(1)
        print(f"  文件第一个字符: '{first_char}'")
except FileNotFoundError as e:
    print(f"  文件未找到: {e}")


# ==================== JSON 读写 ====================
print("\n=== JSON 读写 ===")

# 读取 JSON 文件
with open(input_file, "r", encoding="utf-8") as f:
    employees = json.load(f)

print(f"  读取到 {len(employees)} 条记录")
print(f"  第一条: {employees[0]}")

# json.dumps：Python 对象 → JSON 字符串（调试时常用）
single = json.dumps(employees[0], ensure_ascii=False, indent=2)
print(f"  格式化输出:\n{single}")


# ==================== 数据处理 ====================
print("\n=== 数据处理 ===")

def process_employee(record: dict) -> dict | None:
    """
    处理单条员工记录：
    - 校验必填字段
    - 处理空值
    - 格式转换
    返回 None 表示该记录应跳过
    """
    # 跳过离职员工
    if not record.get("active", False):
        print(f"  跳过离职员工: {record['name']}")
        return None

    # 处理薪资空值（用部门中位数填充，这里简化为默认值）
    try:
        salary = validate_salary(record.get("salary"))
    except DataValidationError as e:
        print(f"  警告 [{record['name']}]: {e}，使用默认值 0")
        salary = 0.0

    return {
        "id": record["id"],
        "name": record["name"],
        "department": record["department"],
        "salary": salary,
        "skill_count": len(record.get("skills", [])),
        "skills": "|".join(record.get("skills", [])),  # 列表转字符串，CSV 友好
    }


cleaned = []
for emp in employees:
    result = process_employee(emp)
    if result is not None:
        cleaned.append(result)

print(f"\n  处理后: {len(cleaned)} 条有效记录")


# ==================== CSV 写入 ====================
print("\n=== CSV 写入 ===")

if cleaned:
    fieldnames = cleaned[0].keys()   # 取第一条的字段名作为表头

    with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
        # utf-8-sig：带 BOM，Excel 打开中文不乱码
        # newline=""：让 csv 模块自己控制换行，避免 Windows 上多出空行
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned)

    print(f"  写入成功: {output_file}")
    print(f"  共 {len(cleaned)} 行数据")


# ==================== CSV 读取验证 ====================
print("\n=== 读取验证 ===")

with open(output_file, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"  读取到 {len(rows)} 行")
for row in rows:
    print(f"  {row['name']} | {row['department']} | 薪资:{row['salary']} | 技能:{row['skills']}")


# ==================== 模块系统 ====================
print("\n=== 模块系统 ===")

# import 的几种方式
import os                          # 导入整个模块，用 os.xxx 调用
from pathlib import Path           # 只导入模块中的某个类/函数
from datetime import datetime, date  # 导入多个

# 给模块起别名（Pandas 约定俗成用 pd，NumPy 用 np）
import json as json_lib            # 别名

now = datetime.now()
print(f"  当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"  今天: {date.today()}")

# __name__ 机制：判断是直接运行还是被 import
# 对照 Java：Java 没有直接等价，Java 的入口是 main 方法
print(f"\n  当前模块名: {__name__}")
# 当直接运行这个文件时，__name__ == "__main__"
# 当被其他模块 import 时，__name__ == "day3_files_modules"
# 这就是为什么 Python 脚本常见 if __name__ == "__main__": 这个写法


# ==================== 综合练习 ====================
# 把上面所有步骤封装成一个函数，体现模块化思想
def run_etl(input_path: Path, output_path: Path) -> dict:
    """
    完整的 ETL 流程（迷你版）
    Extract: 读取 JSON
    Transform: 数据清洗和转换
    Load: 写入 CSV
    返回: 运行统计信息
    """
    stats = {"total": 0, "success": 0, "skipped": 0, "failed": 0}

    # Extract
    with open(input_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    stats["total"] = len(raw_data)

    # Transform
    results = []
    for record in raw_data:
        try:
            processed = process_employee(record)
            if processed is None:
                stats["skipped"] += 1
            else:
                results.append(processed)
                stats["success"] += 1
        except Exception as e:
            stats["failed"] += 1
            print(f"  处理失败 [{record.get('name', '?')}]: {e}")

    # Load
    if results:
        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)

    return stats


print("\n=== 综合练习：完整 ETL 流程 ===")
stats = run_etl(input_file, output_file)
print(f"  运行结果: {stats}")
print("\n✓ Day 3 完成")


# 这个 if 块是 Python 的标准入口写法
# 直接运行此文件时执行，被 import 时不执行
if __name__ == "__main__":
    pass  # 上面已经执行过了，这里留空

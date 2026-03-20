"""
Day 4 - Pandas 基础：Series、DataFrame、数据读取与列操作
数据集：模拟电商订单数据（对应 JD 中"智能零售"业务场景）
"""
import pandas as pd
import numpy as np
from pathlib import Path

data_dir = Path(__file__).parent / "data"


# ==================== Series：一维数据 ====================
print("=== Series：Pandas 的一维数据结构 ===")

# Series = 带标签的一维数组
# 可以类比成 Java 中一个有名字的 List，但每个元素都有索引标签
s = pd.Series([6999, 1299, 3999, 899], index=["iPhone", "AirPods", "跑步机", "运动鞋"])
print(s)
print(f"\n  按标签取值: {s['iPhone']}")
print(f"  按位置取值: {s.iloc[0]}")
print(f"  均值: {s.mean()}")
print(f"  最大值对应的标签: {s.idxmax()}")

# Series 的向量化运算（不需要循环）
print(f"\n  打8折后:\n{s * 0.8}")


# ==================== DataFrame 创建 ====================
print("\n=== DataFrame 创建 ===")

# 方式1：从字典创建（最常用）
df_dict = pd.DataFrame({
    "product": ["iPhone", "AirPods", "跑步机"],
    "price": [6999, 1299, 3999],
    "stock": [100, 250, 30]
})
print("  从字典创建:\n", df_dict)

# 方式2：从列表of字典创建（ETL 中从 JSON 转 DataFrame 时最常见）
records = [
    {"name": "张三", "city": "上海", "orders": 4},
    {"name": "李四", "city": "北京", "orders": 3},
]
df_records = pd.DataFrame(records)
print("\n  从 records 创建:\n", df_records)


# ==================== 读取真实数据 ====================
print("\n=== 读取 CSV 数据 ===")

df = pd.read_csv(data_dir / "orders.csv")

# 读取 JSON（Day 3 用过的 employees.json）
df_emp = pd.read_json(data_dir / "employees.json")
print(f"  employees.json 读取成功，shape: {df_emp.shape}")


# ==================== 基础探索：了解数据全貌 ====================
# 拿到新数据集第一件事，先"摸清底细"

print("\n=== 数据探索 ===")

print(f"\n  shape（行数, 列数）: {df.shape}")
print(f"  columns: {df.columns.tolist()}")

print("\n  head(3) — 前3行:")
print(df.head(3).to_string())

print("\n  tail(3) — 后3行:")
print(df.tail(3).to_string())

print("\n  info() — 数据类型 + 非空值统计:")
df.info()
# 重点关注：
# - Dtype 是否符合预期（object=字符串，float64=浮点数）
# - Non-Null Count 是否有缺失值（unit_price 那行会少一个）

print("\n  describe() — 数值列统计摘要:")
print(df.describe())
# count/mean/std/min/25%/50%/75%/max
# 和 Day 3 手写的 analyze_numbers() 函数一个意思，但功能更完整

print(f"\n  缺失值统计:\n{df.isnull().sum()}")
# unit_price 有1个缺失值（order_id=1008）


# ==================== 列操作 ====================
print("\n=== 列操作 ===")

# 选择单列 → 返回 Series
prices = df["unit_price"]
print(f"  单列类型: {type(prices)}")
print(f"  价格均值: {prices.mean():.2f}")

# 选择多列 → 返回 DataFrame（注意双括号）
subset = df[["order_id", "customer_name", "product", "unit_price"]]
print(f"\n  选取4列:\n{subset.head(3).to_string()}")

# 新增列：总金额 = 数量 × 单价
# 向量化运算，不需要循环
df["total_amount"] = df["quantity"] * df["unit_price"]
print(f"\n  新增 total_amount 列:\n{df[['order_id','product','quantity','unit_price','total_amount']].head(5).to_string()}")

# 新增列：是否高价值订单（金额 > 5000）
df["is_high_value"] = df["total_amount"] > 5000
print(f"\n  高价值订单数: {df['is_high_value'].sum()}")

# 重命名列
df = df.rename(columns={
    "customer_name": "name",
    "order_date":    "date",
})
print(f"\n  重命名后的列名: {df.columns.tolist()}")

# 删除列（axis=1 表示列方向）
df_dropped = df.drop(columns=["is_high_value"])
print(f"  删除 is_high_value 后列数: {df_dropped.shape[1]}")

# 修改列的数据类型
df["date"] = pd.to_datetime(df["date"])   # object → datetime64
df["order_id"] = df["order_id"].astype(str)  # int → string
print(f"\n  类型转换后:\n{df[['order_id','date']].dtypes}")


# ==================== 快速统计 ====================
print("\n=== 快速统计 ===")

print(f"  各城市订单数:\n{df['city'].value_counts()}")
print(f"\n  各品类订单数:\n{df['category'].value_counts()}")
print(f"\n  各状态占比:\n{df['status'].value_counts(normalize=True).round(2)}")
# normalize=True → 输出比例而不是计数


# ==================== 练习：数据探索小结 ====================
print("\n=== 练习：输出探索报告 ===")

def quick_report(dataframe: pd.DataFrame, name: str) -> None:
    """对任意 DataFrame 输出一份快速探索报告"""
    print(f"\n{'='*40}")
    print(f"  数据集: {name}")
    print(f"  规模: {dataframe.shape[0]} 行 × {dataframe.shape[1]} 列")

    missing = dataframe.isnull().sum()
    missing = missing[missing > 0]
    if missing.empty:
        print("  缺失值: 无")
    else:
        print(f"  缺失值:\n{missing.to_string()}")

    num_cols = dataframe.select_dtypes(include=[np.number]).columns.tolist()
    if num_cols:
        print(f"  数值列: {num_cols}")
        print(f"  数值摘要:\n{dataframe[num_cols].describe().round(2).to_string()}")
    print(f"{'='*40}")

quick_report(df, "电商订单")

print("\n✓ Day 4 完成")

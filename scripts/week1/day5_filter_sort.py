"""
Day 5 - 数据筛选与排序
覆盖：布尔索引 / 多条件筛选 / loc & iloc / query() / sort_values()
数据集：沿用 Day 4 的电商订单数据
"""
import pandas as pd
import numpy as np
from pathlib import Path

data_dir = Path(__file__).parent / "data"

# 加载数据，顺手做好类型处理
df = pd.read_csv(data_dir / "orders.csv")
df["order_date"] = pd.to_datetime(df["order_date"])
df["total_amount"] = df["quantity"] * df["unit_price"]

print(f"数据加载完成：{df.shape[0]} 行 × {df.shape[1]} 列\n")


# ==================== 布尔索引 ====================
print("=== 布尔索引 ===")

# 核心原理：df[条件] 中的"条件"是一列 True/False
# Pandas 把 True 对应的行留下，False 的丢掉

# 先看看条件本身长什么样
condition = df["unit_price"] > 1000
print(f"  条件类型: {type(condition)}")
print(f"  条件内容（前5个）:\n{condition.head()}\n")

# 再用条件筛选行
expensive = df[df["unit_price"] > 1000]
print(f"  单价>1000 的订单：{len(expensive)} 条")
print(expensive[["order_id", "product", "unit_price"]].to_string())


# ==================== 多条件筛选 ====================
print("\n=== 多条件筛选 ===")

# 注意：Python 的 and/or 不能用于 Pandas
# 必须用 &（且）、|（或）、~（非），并且每个条件要加括号

# & 且：电子产品 且 已完成
result = df[(df["category"] == "电子产品") & (df["status"] == "已完成")]
print(f"  电子产品 且 已完成：{len(result)} 条")
print(result[["order_id", "product", "total_amount"]].to_string())

# | 或：已取消 或 配送中
result = df[(df["status"] == "已取消") | (df["status"] == "配送中")]
print(f"\n  已取消 或 配送中：{len(result)} 条")
print(result[["order_id", "product", "status"]].to_string())

# ~ 非：排除已取消的订单
result = df[~(df["status"] == "已取消")]
print(f"\n  排除已取消（~）：{len(result)} 条（原{len(df)}条）")

# isin()：等价于 SQL 的 IN，比多个 | 更简洁
result = df[df["city"].isin(["上海", "北京"])]
print(f"\n  城市 IN (上海, 北京)：{len(result)} 条")

# between()：范围筛选，等价于 SQL 的 BETWEEN
result = df[df["unit_price"].between(500, 5000)]
print(f"\n  单价在 500~5000 之间：{len(result)} 条")

# str 方法：字符串匹配
result = df[df["product"].str.contains("书")]
print(f"\n  商品名包含'书'：{len(result)} 条")
print(result[["order_id", "product", "unit_price"]].to_string())

# 日期筛选
result = df[df["order_date"] >= "2024-02-01"]
print(f"\n  2月以后的订单：{len(result)} 条")


# ==================== loc 和 iloc ====================
print("\n=== loc 和 iloc ===")

# loc：按标签（行标签 + 列名）— 用名字定位
# iloc：按位置（行号 + 列号）— 用数字定位
# 对照 Java：loc 像 Map.get(key)，iloc 像 List.get(index)

print("  原始 index（行标签）:")
print(f"  {df.index.tolist()[:5]}...（默认是0,1,2...）\n")

# loc[行条件, 列名列表]
result = df.loc[df["city"] == "上海", ["order_id", "product", "total_amount"]]
print(f"  loc 筛选上海订单（指定列）:\n{result.to_string()}\n")

# loc 按行号范围（注意：loc 的范围是闭区间，包含两端）
print(f"  loc[0:2] — 第0到第2行（含第2行）:\n{df.loc[0:2, ['order_id','product']].to_string()}\n")

# iloc 按整数位置（和 Python 切片一样，左闭右开）
print(f"  iloc[0:3] — 前3行（不含第3行）:\n{df.iloc[0:3][['order_id','product']].to_string()}\n")

# iloc 取特定行列
print(f"  iloc[0, 3] — 第0行第3列的值: {df.iloc[0, 3]}")

# 实际场景：取最后3行（倒序）
print(f"\n  最后3行:\n{df.iloc[-3:][['order_id','product','city']].to_string()}")

# loc vs iloc 一句话总结
print("\n  记忆口诀：loc = label（名字），iloc = integer（数字）")


# ==================== 排序 ====================
print("\n=== 排序 ===")

# sort_values()：按列值排序
# ascending=True 升序（默认），ascending=False 降序
by_price = df.sort_values("unit_price", ascending=False)
print("  按单价降序（前5）:")
print(by_price[["order_id", "product", "unit_price"]].head().to_string())

# 多列排序：先按城市，再按金额降序
by_city_amount = df.sort_values(
    ["city", "total_amount"],
    ascending=[True, False]   # 城市升序，金额降序
)
print(f"\n  按城市升序+金额降序（前6）:")
print(by_city_amount[["order_id", "customer_name", "city", "total_amount"]].head(6).to_string())

# na_position：控制空值位置（默认 last）
by_price_na = df.sort_values("unit_price", ascending=False, na_position="last")
print(f"\n  含空值排序（空值排末尾）:")
print(by_price_na[["order_id", "product", "unit_price"]].tail(3).to_string())


# ==================== query() ====================
print("\n=== query() — 更接近 SQL 的写法 ===")

# query() 让复杂条件更可读，用字符串表达式
# 适合条件多、逻辑复杂的场景

# 等价于 df[(df["category"]=="电子产品") & (df["total_amount"]>2000)]
result = df.query("category == '电子产品' and total_amount > 2000")
print(f"  电子产品 且 金额>2000：{len(result)} 条")
print(result[["order_id", "product", "total_amount"]].to_string())

# 引用 Python 变量（用 @ 前缀）
min_amount = 1000
cities = ["上海", "北京"]
result = df.query("total_amount > @min_amount and city in @cities")
print(f"\n  金额>@min_amount 且 城市在@cities：{len(result)} 条")
print(result[["order_id", "customer_name", "city", "total_amount"]].to_string())

# 日期筛选
result = df.query("order_date >= '2024-02-01' and status == '已完成'")
print(f"\n  2月后已完成：{len(result)} 条")


# ==================== 综合练习 ====================
print("\n=== 综合练习：多条件筛选 + 排序 + 输出 ===")

# 需求：找出所有"上海或北京"的"电子产品"订单，
#       按金额降序排列，输出前5条，保存到 CSV
target = (
    df[
        df["city"].isin(["上海", "北京"]) &
        (df["category"] == "电子产品") &
        (df["status"] != "已取消")
    ]
    .sort_values("total_amount", ascending=False)
    [["order_id", "customer_name", "city", "product", "total_amount", "status"]]
)

print(f"  符合条件：{len(target)} 条")
print(target.to_string())

output = data_dir / "electronics_sh_bj.csv"
target.to_csv(output, index=False, encoding="utf-8-sig")
print(f"\n  已保存到: {output.name}")

print("\n✓ Day 5 完成")

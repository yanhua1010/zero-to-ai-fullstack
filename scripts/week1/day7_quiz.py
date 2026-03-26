import pandas as pd
import numpy as np
from pathlib import Path

data_dir = Path(__file__).parent / "data"
df = pd.read_csv(data_dir / "quiz_products.csv")

print("=" * 5)
print("数据原始数据\n")

print(f"原数据: {df.shape[0]} 行, {df.shape[1]} 列")

print(df.dtypes)

print(df.isnull().sum())

print("=" * 5)
print("开始数据清洗")

duplicated = df.duplicated()
print(df[duplicated].to_string())

df = df.drop_duplicates()
df = df.reset_index(drop=True)
print(f"\n去重后：{df.shape[0]} 行， 删除了{duplicated.sum()} 行")

cost_median = df['cost_price'].median()
df["cost_price"] = df["cost_price"].fillna(cost_median)

df['stock'] = df["stock"].fillna(0)

print("=" * 5)

print("新增计算列")

df["profit"] = df["sell_price"] - df["cost_price"]
df["profit_rate"] = (df["profit"] / df["cost_price"]).round(2)
df["is_out_of_stock"] = df["stock"] == 0

print("=" * 5)
print("筛选")

filter = df["profit_rate"] > 0.5 & df["category"] == "电子产品"
result = df[filter].sort_values("profit", ascending=False)
print(result.to_string())

print("输出")
output = data_dir / "high_margin_electronics.csv"

result.to_csv(output, index=False, encoding="utf-8-sig")

print(f"\n 已保存,文件路径：{output.name}")









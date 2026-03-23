"""
Day 6 - 数据类型转换 + 缺失值 + 重复值处理
练习：对一份"脏数据"完成完整清洗流程
脏数据问题清单：
  1. price 含中文逗号"，"（非法字符）
  2. quantity 含空格字符串" "
  3. order_date 格式不统一（3种格式混用）
  4. rating 含异常值（6.5、-1 不在0-5范围）
  5. customer / city 有缺失值
  6. 有完全重复的行（1002=1009，1003=1001，1004=1013）
"""
import pandas as pd
import numpy as np
from pathlib import Path

data_dir = Path(__file__).parent / "data"


# ==================== 第一步：加载并诊断 ====================
print("=" * 50)
print("第一步：加载数据，全面诊断问题")
print("=" * 50)

# 先不做任何处理，原样加载，看清问题全貌
df = pd.read_csv(data_dir / "dirty_sales.csv", dtype=str)
# dtype=str：强制全部读成字符串，避免 Pandas 自动推断类型时掩盖问题

print(f"\n原始数据：{df.shape[0]} 行 × {df.shape[1]} 列")
print(df.to_string())

print(f"\n各列数据类型（全是 object，因为 dtype=str）:")
print(df.dtypes)

print(f"\n各列缺失值（NaN）:")
print(df.isnull().sum())

print(f"\n各列唯一值数量（发现重复行的线索）:")
print(df.nunique())


# ==================== 第二步：处理重复行 ====================
print("\n" + "=" * 50)
print("第二步：重复行处理")
print("=" * 50)

# duplicated()：标记重复行（默认保留第一次出现的，后续的标为 True）
dup_mask = df.duplicated()
print(f"\n重复行数量：{dup_mask.sum()}")
print("重复的行：")
print(df[dup_mask].to_string())

# 对比：找出所有参与重复的行（keep=False：所有重复都标记）
all_dups = df.duplicated(keep=False)
print(f"\n参与重复的行（含原始行）：{all_dups.sum()} 行")

# 删除重复行，保留第一次出现的
df = df.drop_duplicates()
print(f"\n去重后：{df.shape[0]} 行（删除了 {dup_mask.sum()} 行）")

# 重置索引（去重后 index 会有空洞，如 0,1,3,5... 需要重置）
df = df.reset_index(drop=True)
print(f"重置 index 后：{df.index.tolist()}")


# ==================== 第三步：清洗 price 列 ====================
print("\n" + "=" * 50)
print("第三步：清洗 price 列（含非法字符）")
print("=" * 50)

print(f"\nprice 原始值：{df['price'].tolist()}")

# 问题：含中文逗号"，"
# 先替换非法字符，再转为数值，非法值变成 NaN
df["price"] = df["price"].str.replace("，", "", regex=False)  # 去掉中文逗号
df["price"] = pd.to_numeric(df["price"], errors="coerce")
# errors="coerce"：无法转换的值变成 NaN，而不是报错

print(f"清洗后 price：{df['price'].tolist()}")
print(f"price 缺失：{df['price'].isnull().sum()} 个")


# ==================== 第四步：清洗 quantity 列 ====================
print("\n" + "=" * 50)
print("第四步：清洗 quantity 列（含空格字符串）")
print("=" * 50)

print(f"\nquantity 原始值：{df['quantity'].tolist()}")

df["quantity"] = df["quantity"].str.strip()           # 去首尾空格
df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")

print(f"清洗后 quantity：{df['quantity'].tolist()}")
print(f"quantity 缺失：{df['quantity'].isnull().sum()} 个")


# ==================== 第五步：统一日期格式 ====================
print("\n" + "=" * 50)
print("第五步：统一 order_date 格式（3种格式混用）")
print("=" * 50)

print(f"\norder_date 唯一格式：")
print(df["order_date"].unique())

# pd.to_datetime 的 dayfirst 参数处理 DD-MM-YYYY 格式
# 注意：01-10-2024 会被解析成 2024年10月1日（dayfirst=True）
df["order_date"] = pd.to_datetime(df["order_date"], dayfirst=True, errors="coerce")

print(f"\n转换后：")
print(df["order_date"].tolist())
print(f"日期缺失：{df['order_date'].isnull().sum()} 个")

# 提取日期部件（后续 ETL 分析常用）
df["year"] = df["order_date"].dt.year
df["month"] = df["order_date"].dt.month
df["weekday"] = df["order_date"].dt.day_name()


# ==================== 第六步：清洗 rating 异常值 ====================
print("\n" + "=" * 50)
print("第六步：处理 rating 异常值（有效范围 0~5）")
print("=" * 50)

df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
print(f"\nrating 清洗后：{df['rating'].tolist()}")

# 超出范围的值设为 NaN
invalid_mask = (df["rating"] < 0) | (df["rating"] > 5)
print(f"异常值行：")
print(df[invalid_mask][["order_id", "customer", "rating"]])

df.loc[invalid_mask, "rating"] = np.nan
print(f"\n修正后 rating：{df['rating'].tolist()}")


# ==================== 第七步：处理缺失值 ====================
print("\n" + "=" * 50)
print("第七步：缺失值处理策略")
print("=" * 50)

print(f"\n当前各列缺失值统计：")
print(df.isnull().sum()[df.isnull().sum() > 0])

# 策略1：数值列 → 用中位数填充（比均值更抗异常值）
median_price = df["price"].median()
median_qty = df["quantity"].median()
median_rating = df["rating"].median()

df["price"] = df["price"].fillna(median_price)
df["quantity"] = df["quantity"].fillna(median_qty)
df["rating"] = df["rating"].fillna(median_rating)

print(f"\n数值列用中位数填充：")
print(f"  price 中位数: {median_price}")
print(f"  quantity 中位数: {median_qty}")
print(f"  rating 中位数: {median_rating}")

# 策略2：分类列 → 填充为"未知"
df["customer"] = df["customer"].fillna("未知客户")
df["city"] = df["city"].fillna("未知城市")

print(f"\n分类列填充'未知'后缺失值：")
print(df.isnull().sum()[df.isnull().sum() > 0])
print("（无输出表示已无缺失值）")

# 其他策略演示（不实际修改 df）
# 前向填充（用上一行的值填充，适合时间序列）
demo = pd.Series([1.0, np.nan, np.nan, 4.0, 5.0])
print(f"\n前向填充演示（ffill）:")
print(f"  原始: {demo.tolist()}")
print(f"  填充后: {demo.ffill().tolist()}")

# 后向填充
print(f"  后向填充（bfill）: {demo.bfill().tolist()}")


# ==================== 第八步：最终类型确认 ====================
print("\n" + "=" * 50)
print("第八步：确认最终数据类型")
print("=" * 50)

# 确保各列类型正确
df["order_id"] = df["order_id"].astype(int)
df["quantity"] = df["quantity"].astype(int)

print(f"\n最终数据类型：")
print(df.dtypes)


# ==================== 第九步：输出清洗报告 ====================
print("\n" + "=" * 50)
print("第九步：清洗结果")
print("=" * 50)

print(f"\n清洗后数据（{df.shape[0]} 行）：")
print(df[["order_id", "customer", "product", "price",
          "quantity", "order_date", "city", "rating"]].to_string())

# 保存
output = data_dir / "clean_sales.csv"
df.to_csv(output, index=False, encoding="utf-8-sig")
print(f"\n已保存：{output.name}")

print("\n✓ Day 6 完成")

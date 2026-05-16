#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分拣中心成本与产能探索性数据分析
用途：对附件表3（成本数据）、附件表4（设备采购）和附件表2（货量）进行全面的EDA
依赖：pandas, numpy, matplotlib, openpyxl
运行：py.exe eda_analysis.py
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import Patch
import os
import sys
import warnings
warnings.filterwarnings("ignore")

# 配置 stdout 为 utf-8 避免 GBK 编码问题
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# ============================================================
# 0. 路径与输出目录
# ============================================================
BASE = r"c:\Users\www15\Desktop\26长三角数模"
DATA_DIR = os.path.join(
    BASE,
    "2026年第六届长三角高校数学建模竞赛赛题",
    "2026长三角赛题A：物流网络集包规则及设备优化",
)
OUT_DIR = os.path.join(BASE, "分析结果_分拣中心评级")
os.makedirs(OUT_DIR, exist_ok=True)

# 中文字体设置
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# ============================================================
# 1. 读取数据
# ============================================================
print("=" * 70)
print("数据读取中...")

# 附件表2：货量数据（GBK编码）
df2 = pd.read_csv(
    os.path.join(DATA_DIR, "附件表2.csv"),
    encoding="gbk",
    skiprows=1,
    names=["日期", "始发中心", "目的中心", "货量"],
)

# 附件表3：成本数据（GBK编码）
df3 = pd.read_csv(
    os.path.join(DATA_DIR, "附件表3.csv"),
    encoding="gbk",
    skiprows=1,
    names=["分拣中心", "设备类型", "人工建包成本", "机器建包成本"],
)

# 附件表4：设备采购信息（xlsx）
df4 = pd.read_excel(os.path.join(DATA_DIR, "附件表4.xlsx"))

print(f"附件表2（货量）: {df2.shape[0]} 行, {df2.shape[1]} 列")
print(f"附件表3（成本）: {df3.shape[0]} 行, {df3.shape[1]} 列")
print(f"附件表4（设备）: {df4.shape[0]} 行, {df4.shape[1]} 列")
print(f"  表4列名: {df4.columns.tolist()}")
print("=" * 70)

# ============================================================
# 2. 附件表3 基本统计
# ============================================================
print("\n" + "=" * 70)
print("【附件表3 基本统计】")
print("=" * 70)

n_centers = df3["分拣中心"].nunique()
n_rows = len(df3)
print(f"总共有 {n_centers} 个分拣中心（{n_rows} 行数据）")

# 设备类型分布
device_dist = df3["设备类型"].value_counts().sort_index()
n_device_types = len(device_dist)
print(f"\n设备类型分布（共 {n_device_types} 种）:")
for dtype_val, count in device_dist.items():
    pct = count / n_rows * 100
    print(f"  {dtype_val}: {count} 个分拣中心 ({pct:.1f}%)")

# 人工建包成本统计
labor = df3["人工建包成本"]
print(f"\n人工建包成本分布（元/件）:")
print(f"  均值:   {labor.mean():.1f}")
print(f"  中位数: {labor.median():.1f}")
print(f"  最小值: {labor.min():.0f}")
print(f"  最大值: {labor.max():.0f}")
print(f"  标准差: {labor.std():.1f}")
print(f"  变异系数: {labor.std()/labor.mean()*100:.1f}%")

# 机器建包成本统计
machine = df3["机器建包成本"]
print(f"\n机器建包成本分布（产能上限）:")
print(f"  均值:   {machine.mean():.1f}")
print(f"  中位数: {machine.median():.1f}")
print(f"  最小值: {machine.min():.0f}")
print(f"  最大值: {machine.max():.0f}")
print(f"  标准差: {machine.std():.1f}")

# 人工 vs 机器成本对比
df3["人比机贵"] = df3["人工建包成本"] > df3["机器建包成本"]
n_labor_expensive = df3["人比机贵"].sum()
print(f"\n人工 vs 机器成本对比:")
print(f"  人工 > 机器: {n_labor_expensive}/{n_rows} = {n_labor_expensive/n_rows*100:.1f}%")
print(f"  机器 >= 人工: {n_rows - n_labor_expensive}/{n_rows} = {(n_rows-n_labor_expensive)/n_rows*100:.1f}%")

# 人工比机器贵的那些分拣中心
labor_expensive = df3[df3["人比机贵"]].sort_values("人工建包成本", ascending=False)
if len(labor_expensive) > 0:
    print(f"\n人工成本 > 机器成本的案例:")
    for _, row in labor_expensive.iterrows():
        print(f"  {row['分拣中心']} ({row['设备类型']}): "
              f"人工={row['人工建包成本']} > 机器={row['机器建包成本']}")

# 机器建包成本为0的情况
zero_machine = df3[df3["机器建包成本"] == 0]
if len(zero_machine) > 0:
    print(f"\n[异常] 机器建包成本为0的分拣中心 ({len(zero_machine)}个):")
    for _, row in zero_machine.iterrows():
        print(f"  {row['分拣中心']} ({row['设备类型']}): 人工成本={row['人工建包成本']}")

# ============================================================
# 3. 分拣中心分类分析
# ============================================================
print("\n" + "=" * 70)
print("【分拣中心分类分析】")
print("=" * 70)

# 按设备类型分组统计
grouped = (
    df3.groupby("设备类型")
    .agg(
        中心数量=("分拣中心", "nunique"),
        人工成本均值=("人工建包成本", "mean"),
        人工成本中位数=("人工建包成本", "median"),
        人工成本最小=("人工建包成本", "min"),
        人工成本最大=("人工建包成本", "max"),
        机器产能均值=("机器建包成本", "mean"),
        机器产能中位数=("机器建包成本", "median"),
        机器产能最小=("机器建包成本", "min"),
        机器产能最大=("机器建包成本", "max"),
    )
    .reset_index()
    .sort_values("设备类型")
)
print("\n按设备类型分组统计:")
print(grouped.to_string(index=False))

# 按产能分组（机器建包成本=产能上限）
machine_nz = machine[machine > 0]
low_th = machine_nz.quantile(0.33)
high_th = machine_nz.quantile(0.66)
print(f"\n产能分组阈值（基于非零值33/66分位数）:")
print(f"  低产能: < {low_th:.0f}")
print(f"  中产能: [{low_th:.0f}, {high_th:.0f})")
print(f"  高产能: >= {high_th:.0f}")

def classify(cost):
    if cost == 0:
        return "零产能(异常)"
    if cost < low_th:
        return "低产能"
    if cost < high_th:
        return "中产能"
    return "高产能"

df3["产能等级"] = df3["机器建包成本"].apply(classify)
capacity_dist = df3["产能等级"].value_counts()
print(f"\n产能等级分布:")
for level in ["高产能", "中产能", "低产能", "零产能(异常)"]:
    cnt = capacity_dist.get(level, 0)
    print(f"  {level}: {cnt} 个 ({cnt/n_rows*100:.1f}%)")

# 各产能等级详细数据
print("\n各产能等级详细:")
for level in ["高产能", "中产能", "低产能", "零产能(异常)"]:
    sub = df3[df3["产能等级"] == level]
    if len(sub) > 0:
        print(f"  [{level}] n={len(sub)}:")
        print(f"    人工: 均值={sub['人工建包成本'].mean():.0f}, "
              f"中位数={sub['人工建包成本'].median():.0f}, "
              f"范围=[{sub['人工建包成本'].min():.0f},{sub['人工建包成本'].max():.0f}]")
        print(f"    机器: 均值={sub['机器建包成本'].mean():.0f}, "
              f"中位数={sub['机器建包成本'].median():.0f}, "
              f"范围=[{sub['机器建包成本'].min():.0f},{sub['机器建包成本'].max():.0f}]")

# ============================================================
# 4. 成本-产能关系可视化
# ============================================================
print("\n" + "=" * 70)
print("【成本-产能关系可视化】")
print("=" * 70)

# --- 图1：人工成本 vs 机器产能散点图 ---
fig, ax = plt.subplots(figsize=(10, 6))
device_codes = df3["设备类型"].astype("category").cat.codes
sc = ax.scatter(
    df3["机器建包成本"], df3["人工建包成本"],
    c=device_codes, cmap="tab10", alpha=0.7,
    edgecolors="k", linewidth=0.5, s=60,
)
ax.set_xlabel("机器建包成本（产能上限）", fontsize=12)
ax.set_ylabel("人工建包成本（元/件）", fontsize=12)
ax.set_title("人工成本 vs 机器产能 散点图", fontsize=14)
ax.grid(True, alpha=0.3)

# 趋势线（排除零值）
mask_nz = df3["机器建包成本"] > 0
if mask_nz.sum() > 2:
    z = np.polyfit(
        df3.loc[mask_nz, "机器建包成本"],
        df3.loc[mask_nz, "人工建包成本"], 1,
    )
    p = np.poly1d(z)
    x_line = np.linspace(
        df3.loc[mask_nz, "机器建包成本"].min(),
        df3.loc[mask_nz, "机器建包成本"].max(), 100,
    )
    ax.plot(x_line, p(x_line), "r--", linewidth=2,
            label=f"趋势线 (斜率={z[0]:.4f})")
    ax.legend()

# 设备类型图例
device_types = sorted(df3["设备类型"].unique())
colors_used = plt.cm.tab10(np.linspace(0, 1, len(device_types)))
legend_elems = [
    plt.Line2D([0], [0], marker="o", color="w",
               markerfacecolor=colors_used[i], markersize=8, label=dt)
    for i, dt in enumerate(device_types)
]
ax.legend(handles=legend_elems, title="设备类型",
          loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0)

# 标注零产能异常点
for _, row in zero_machine.iterrows():
    ax.annotate(row["分拣中心"],
                (row["机器建包成本"], row["人工建包成本"]),
                textcoords="offset points", xytext=(5, 5),
                fontsize=8, color="red")

plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "图1_人工成本_vs_机器产能.png"), dpi=150)
plt.close()
print("  图1_人工成本_vs_机器产能.png")

# --- 图2：机器产能分布柱状图 ---
fig, ax = plt.subplots(figsize=(14, 6))
df3_sorted = df3.sort_values("机器建包成本", ascending=False).reset_index(drop=True)
cap_colors = {
    "高产能": "#2ecc71", "中产能": "#f39c12",
    "低产能": "#e74c3c", "零产能(异常)": "#95a5a6",
}
bar_colors = [cap_colors[v] for v in df3_sorted["产能等级"]]
ax.bar(range(len(df3_sorted)), df3_sorted["机器建包成本"],
       color=bar_colors, edgecolor="k", linewidth=0.3)

ax2 = ax.twinx()
ax2.plot(range(len(df3_sorted)), df3_sorted["人工建包成本"],
         "b-o", markersize=3, linewidth=1, alpha=0.7, label="人工建包成本")
ax2.set_ylabel("人工建包成本（元/件）", fontsize=12, color="blue")

ax.set_xlabel("分拣中心（按机器产能降序排列）", fontsize=12)
ax.set_ylabel("机器建包成本（产能上限）", fontsize=12)
ax.set_title("分拣中心机器产能分布及对应人工成本", fontsize=14)
ax.set_xticks(range(0, len(df3_sorted), 5))
ax.set_xticklabels([f"#{i+1}" for i in range(0, len(df3_sorted), 5)],
                   fontsize=8, rotation=45)

legend_patches = [
    Patch(facecolor=cap_colors[k], label=k) for k in cap_colors
]
legend_patches.append(
    plt.Line2D([0], [0], color="b", marker="o", markersize=4, label="人工成本")
)
ax.legend(handles=legend_patches, loc="upper right", fontsize=9)
ax.grid(True, alpha=0.3, axis="y")
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "图2_机器产能分布.png"), dpi=150)
plt.close()
print("  图2_机器产能分布.png")

# --- 图3：设备类型箱线图 ---
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
dtype_order = sorted(df3["设备类型"].unique())

man_data = [df3[df3["设备类型"] == dt]["人工建包成本"].values for dt in dtype_order]
bp1 = axes[0].boxplot(man_data, labels=dtype_order, patch_artist=True)
for patch in bp1["boxes"]:
    patch.set_facecolor("lightblue"); patch.set_alpha(0.7)
axes[0].set_title("人工建包成本（按设备类型）", fontsize=12)
axes[0].set_ylabel("人工建包成本（元/件）")
axes[0].grid(True, alpha=0.3)

mach_data = [df3[df3["设备类型"] == dt]["机器建包成本"].values for dt in dtype_order]
bp2 = axes[1].boxplot(mach_data, labels=dtype_order, patch_artist=True)
for patch in bp2["boxes"]:
    patch.set_facecolor("lightcoral"); patch.set_alpha(0.7)
axes[1].set_title("机器建包成本（按设备类型）", fontsize=12)
axes[1].set_ylabel("机器建包成本（产能上限）")
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "图3_设备类型成本箱线图.png"), dpi=150)
plt.close()
print("  图3_设备类型成本箱线图.png")

# --- 图4：产能等级饼图 ---
fig, ax = plt.subplots(figsize=(8, 8))
pie_labels = capacity_dist.index.tolist()
pie_values = capacity_dist.values.tolist()
pie_colors = [cap_colors.get(l, "gray") for l in pie_labels]
wedges, texts, autotexts = ax.pie(
    pie_values, labels=pie_labels, autopct="%1.1f%%",
    colors=pie_colors, startangle=90, textprops={"fontsize": 11},
)
for at in autotexts:
    at.set_fontweight("bold")
ax.set_title("分拣中心产能等级分布", fontsize=14)
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "图4_产能等级饼图.png"), dpi=150)
plt.close()
print("  图4_产能等级饼图.png")

# --- 图5：人工vs机器成本对比散点 ---
fig, ax = plt.subplots(figsize=(10, 8))
max_val = max(df3["人工建包成本"].max(), df3["机器建包成本"].max())
ax.plot([0, max_val], [0, max_val], "k--", alpha=0.3, label="人工 = 机器")
sc = ax.scatter(
    df3["机器建包成本"], df3["人工建包成本"],
    c=np.where(df3["人比机贵"], "#e74c3c", "#2ecc71"),
    alpha=0.7, edgecolors="k", linewidth=0.5, s=60,
)
ax.set_xlabel("机器建包成本（产能上限）", fontsize=12)
ax.set_ylabel("人工建包成本（元/件）", fontsize=12)
ax.set_title("人工 vs 机器成本对比\n（红点=人工更贵, 绿点=机器更贵）", fontsize=14)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
ax.set_xlim(0, max_val * 1.05)
for _, row in df3[df3["人比机贵"]].iterrows():
    ax.annotate(row["分拣中心"][:6],
                (row["机器建包成本"], row["人工建包成本"]),
                textcoords="offset points", xytext=(5, 5),
                fontsize=6, alpha=0.8)
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "图5_人工vs机器成本对比.png"), dpi=150)
plt.close()
print("  图5_人工vs机器成本对比.png")

# ============================================================
# 5. 附件表4 设备采购分析
# ============================================================
print("\n" + "=" * 70)
print("【附件表4 设备采购分析】")
print("=" * 70)

# 识别列名
print(f"表4列名: {df4.columns.tolist()}")
print(f"列数据类型:")
for col in df4.columns:
    print(f"  {col}: {df4[col].dtype}")

# 根据实际列名进行映射
cost_col = "设备成本" if "设备成本" in df4.columns else None
slot_col = "格口数量" if "格口数量" in df4.columns else None
capacity_col = "设计产能" if "设计产能" in df4.columns else None
lifespan_col = "折旧年限" if "折旧年限" in df4.columns else None
device_type_col = "分拣机名称" if "分拣机名称" in df4.columns else None

# 如果列名不匹配，用自动识别
if cost_col is None:
    for col in df4.columns:
        cl = str(col).lower()
        if any(k in cl for k in ["成本", "价格", "费用"]):
            cost_col = col

print(f"\n列映射: 设备类型={device_type_col}, 成本={cost_col}, "
      f"格口={slot_col}, 产能={capacity_col}, 寿命={lifespan_col}")

# 计算各项指标
if cost_col:
    df4["采购成本"] = pd.to_numeric(df4[cost_col], errors="coerce")
if slot_col:
    df4["格口数"] = pd.to_numeric(df4[slot_col], errors="coerce")
    df4["单位格口成本"] = df4["采购成本"] / df4["格口数"].replace(0, np.nan)
if capacity_col:
    df4["设计产能_"] = pd.to_numeric(df4[capacity_col], errors="coerce")
    df4["单位产能成本"] = df4["采购成本"] / df4["设计产能_"].replace(0, np.nan)
if lifespan_col:
    df4["折旧年限_"] = pd.to_numeric(df4[lifespan_col], errors="coerce")
    df4["日均折旧"] = df4["采购成本"] / (df4["折旧年限_"] * 365)

# 打印设备参数
print(f"\n设备参数全览:")
print(df4.to_string(index=False))

# 打印关键指标
display_cols = []
if device_type_col:
    display_cols.append(device_type_col)
for c in ["采购成本", "格口数", "设计产能_", "折旧年限_",
           "单位格口成本", "单位产能成本", "日均折旧"]:
    if c in df4.columns:
        display_cols.append(c)
if display_cols:
    print(f"\n关键指标汇总:")
    print(df4[display_cols].to_string(index=False))

# ============================================================
# 6. 盈亏平衡分析
# ============================================================
print("\n" + "=" * 70)
print("【盈亏平衡分析：设备自动化 vs 人工建包】")
print("=" * 70)

LABOR_DAILY_COST = 90      # 元/人/天
LABOR_SLOTS_PER = 5        # 每人处理格口数
LABOR_SLOT_COST = LABOR_DAILY_COST / LABOR_SLOTS_PER  # 元/格口/天

print(f"\n人工成本基线:")
print(f"  每人每天: {LABOR_DAILY_COST} 元")
print(f"  每人处理: {LABOR_SLOTS_PER} 格口")
print(f"  每格口每天: {LABOR_SLOT_COST:.1f} 元/格口/天")

if cost_col and slot_col and lifespan_col and "日均折旧" in df4.columns:
    # 设备每格口每天成本
    df4["设备每格口天成本"] = df4["日均折旧"] / df4["格口数"].replace(0, np.nan)
    df4["设备更优"] = df4["设备每格口天成本"] < LABOR_SLOT_COST

    print(f"\n设备 vs 人工 盈亏平衡对比:")
    disp_be = []
    if device_type_col:
        disp_be.append(device_type_col)
    for c in ["格口数", "采购成本", "日均折旧", "设备每格口天成本", "设备更优"]:
        if c in df4.columns:
            disp_be.append(c)
    print(df4[disp_be].to_string(index=False))

    n_better = df4["设备更优"].sum()
    print(f"\n设备每格口成本 < 人工的: {n_better}/{len(df4)} ({n_better/len(df4)*100:.1f}%)")

    # 投资回收期
    df4["日节省人工"] = (LABOR_SLOT_COST - df4["设备每格口天成本"]) * df4["格口数"]
    df4["回收期_天"] = df4["采购成本"] / df4["日节省人工"].replace(0, np.nan)

    print(f"\n投资回收期:")
    disp_pp = []
    if device_type_col:
        disp_pp.append(device_type_col)
    for c in ["采购成本", "日均折旧", "设备每格口天成本", "日节省人工", "回收期_天"]:
        if c in df4.columns:
            disp_pp.append(c)
    print(df4[disp_pp].to_string(index=False))

# --- 图6：设备参数对比 ---
if device_type_col and cost_col and slot_col:
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    names = df4[device_type_col].tolist()
    x = range(len(names))

    axes[0, 0].bar(x, df4["采购成本"], color="steelblue", edgecolor="k")
    axes[0, 0].set_title("采购成本", fontsize=12)
    axes[0, 0].set_xticks(x)
    axes[0, 0].set_xticklabels(names, rotation=45, ha="right", fontsize=9)
    axes[0, 0].grid(True, alpha=0.3)

    if "单位格口成本" in df4.columns:
        axes[0, 1].bar(x, df4["单位格口成本"], color="coral", edgecolor="k")
        axes[0, 1].set_title("单位格口成本", fontsize=12)
        axes[0, 1].set_xticks(x)
        axes[0, 1].set_xticklabels(names, rotation=45, ha="right", fontsize=9)
        axes[0, 1].grid(True, alpha=0.3)

    if "日均折旧" in df4.columns:
        axes[1, 0].bar(x, df4["日均折旧"], color="mediumseagreen", edgecolor="k")
        axes[1, 0].set_title("日均折旧", fontsize=12)
        axes[1, 0].set_xticks(x)
        axes[1, 0].set_xticklabels(names, rotation=45, ha="right", fontsize=9)
        axes[1, 0].grid(True, alpha=0.3)

    if "设备每格口天成本" in df4.columns:
        axes[1, 1].bar(x, df4["设备每格口天成本"],
                       color="mediumpurple", edgecolor="k", label="设备")
        axes[1, 1].axhline(y=LABOR_SLOT_COST, color="red", linestyle="--",
                           linewidth=2,
                           label=f"人工 ({LABOR_SLOT_COST:.1f}元/格口/天)")
        axes[1, 1].set_title("每格口每天成本: 设备 vs 人工", fontsize=12)
        axes[1, 1].set_xticks(x)
        axes[1, 1].set_xticklabels(names, rotation=45, ha="right", fontsize=9)
        axes[1, 1].legend(fontsize=9)
        axes[1, 1].grid(True, alpha=0.3)

    fig.suptitle("设备采购参数对比", fontsize=14, fontweight="bold")
    plt.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "图6_设备采购参数对比.png"), dpi=150)
    plt.close()
    print("\n  图6_设备采购参数对比.png")

# --- 图7：投资回收期 ---
if "回收期_天" in df4.columns and device_type_col:
    fig, ax = plt.subplots(figsize=(10, 6))
    pp_data = df4["回收期_天"].fillna(0)
    pp_colors = [
        "#2ecc71" if v <= 365 else "#f39c12" if v <= 730 else "#e74c3c"
        for v in pp_data
    ]
    ax.bar(range(len(names)), pp_data, color=pp_colors, edgecolor="k")
    ax.set_title("设备投资回收期", fontsize=14)
    ax.set_xlabel("设备类型")
    ax.set_ylabel("回收期（天）")
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, fontsize=10)
    ax.axhline(y=365, color="green", linestyle="--", alpha=0.5, label="1年")
    ax.axhline(y=730, color="orange", linestyle="--", alpha=0.5, label="2年")
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    for i, v in enumerate(pp_data):
        if v > 0:
            ax.text(i, v + pp_data.max() * 0.02,
                    f"{v:.0f}天", ha="center", fontsize=8)
    plt.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "图7_投资回收期.png"), dpi=150)
    plt.close()
    print("  图7_投资回收期.png")

# ============================================================
# 7. 综合对比：分拣中心设备 vs 货量
# ============================================================
print("\n" + "=" * 70)
print("【综合对比：分拣中心设备 vs 货量】")
print("=" * 70)

# 聚合附件表2货量
outgoing = df2.groupby("始发中心")["货量"].sum().reset_index()
outgoing.columns = ["分拣中心", "发出货量"]
incoming = df2.groupby("目的中心")["货量"].sum().reset_index()
incoming.columns = ["分拣中心", "到达货量"]

cargo_data = outgoing.merge(incoming, on="分拣中心", how="outer").fillna(0)
cargo_data["总货量"] = cargo_data["发出货量"] + cargo_data["到达货量"]

n_days = df2["日期"].nunique()
total_cargo = df2["货量"].sum()
print(f"\n附件表2 货量概况:")
print(f"  始发-目的记录数: {len(df2):,}")
print(f"  始发中心数: {df2['始发中心'].nunique()}")
print(f"  目的中心数: {df2['目的中心'].nunique()}")
print(f"  天数: {n_days}")
print(f"  总货量: {total_cargo:,}")
print(f"  日均总货量: {total_cargo / n_days:,.0f}")
print(f"  聚合后分拣中心总数: {len(cargo_data)}")

# 标准化名称匹配
def norm_name(n):
    return str(n).strip().replace("分拣", "").replace("中心", "").strip()

df3["标准名"] = df3["分拣中心"].apply(norm_name)
cargo_data["标准名"] = cargo_data["分拣中心"].apply(norm_name)

merged = df3.merge(cargo_data, on="标准名", how="left",
                   suffixes=("_表3", "_表2"))
n_unmatched = merged["总货量"].isna().sum()
print(f"\n匹配结果: {n_rows - n_unmatched}/{n_rows} 个分拣中心匹配到货量数据")
if n_unmatched > 0:
    unmatched_names = merged[merged["总货量"].isna()]["分拣中心_表3"].tolist()
    print(f"  未匹配: {unmatched_names}")

# 分析高/低货量中心
merged_valid = merged.dropna(subset=["总货量"]).copy()
if len(merged_valid) > 0:
    cargo_median = merged_valid["总货量"].median()
    merged_valid["货量等级"] = np.where(
        merged_valid["总货量"] >= cargo_median, "高货量", "低货量"
    )
    print(f"\n货量中位数: {cargo_median:,.0f}")

    # 交叉表
    ct = pd.crosstab(merged_valid["货量等级"], merged_valid["产能等级"],
                     margins=True, margins_name="合计")
    print(f"\n货量等级 vs 产能等级 交叉表:")
    print(ct.to_string())

    # 高货量中心的设备分布
    high_c = merged_valid[merged_valid["货量等级"] == "高货量"]
    low_c = merged_valid[merged_valid["货量等级"] == "低货量"]

    print(f"\n高货量中心 ({len(high_c)}个):")
    print(f"  设备类型分布: {high_c['设备类型'].value_counts().to_dict()}")
    print(f"  平均机器产能: {high_c['机器建包成本'].mean():.0f}")
    print(f"  平均人工成本: {high_c['人工建包成本'].mean():.0f}")
    print(f"  平均总货量: {high_c['总货量'].mean():,.0f}")

    print(f"\n低货量中心 ({len(low_c)}个):")
    print(f"  设备类型分布: {low_c['设备类型'].value_counts().to_dict()}")
    print(f"  平均机器产能: {low_c['机器建包成本'].mean():.0f}")
    print(f"  平均人工成本: {low_c['人工建包成本'].mean():.0f}")
    print(f"  平均总货量: {low_c['总货量'].mean():,.0f}")

    # 相关性
    corr_val = merged_valid["总货量"].corr(merged_valid["机器建包成本"])
    print(f"\n货量-产能 Pearson 相关系数: {corr_val:.4f}")

    # 产能匹配：高货量+高产能
    hh = len(merged_valid[(merged_valid["货量等级"] == "高货量") &
                           (merged_valid["产能等级"] == "高产能")])
    hl = len(merged_valid[(merged_valid["货量等级"] == "高货量") &
                           (merged_valid["产能等级"] != "高产能")])
    lh = len(merged_valid[(merged_valid["货量等级"] == "低货量") &
                           (merged_valid["产能等级"] == "高产能")])
    print(f"\n产能匹配分析:")
    print(f"  高货量+高产能(匹配): {hh} 个")
    print(f"  高货量+非高产能(产能不足): {hl} 个")
    print(f"  低货量+高产能(产能过剩): {lh} 个")

    # --- 图8：货量 vs 机器产能散点图 ---
    fig, ax = plt.subplots(figsize=(12, 7))
    sc = ax.scatter(
        merged_valid["总货量"], merged_valid["机器建包成本"],
        c=merged_valid["设备类型"].astype("category").cat.codes,
        cmap="tab10", alpha=0.7, edgecolors="k", linewidth=0.5, s=80,
    )
    ax.set_xlabel("总货量（件）", fontsize=12)
    ax.set_ylabel("机器建包成本（产能上限）", fontsize=12)
    ax.set_title("分拣中心：总货量 vs 机器产能", fontsize=14)
    ax.grid(True, alpha=0.3)

    z = np.polyfit(merged_valid["总货量"], merged_valid["机器建包成本"], 1)
    p = np.poly1d(z)
    xr = np.linspace(merged_valid["总货量"].min(),
                     merged_valid["总货量"].max(), 100)
    ax.plot(xr, p(xr), "r--", linewidth=2,
            label=f"趋势线 (斜率={z[0]:.6f})")
    ax.legend()

    # 标注极端值
    top5 = merged_valid.nlargest(5, "总货量")
    for _, row in top5.iterrows():
        ax.annotate(row["分拣中心_表3"][:8],
                    (row["总货量"], row["机器建包成本"]),
                    textcoords="offset points", xytext=(5, 5), fontsize=8)
    plt.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "图8_总货量_vs_机器产能.png"), dpi=150)
    plt.close()
    print("\n  图8_总货量_vs_机器产能.png")

    # --- 图9：各产能等级货量分布箱线图 ---
    fig, ax = plt.subplots(figsize=(10, 6))
    levels_order = ["高产能", "中产能", "低产能", "零产能(异常)"]
    box_data = []
    box_labels = []
    for lv in levels_order:
        sub = merged_valid[merged_valid["产能等级"] == lv]
        if len(sub) > 0:
            box_data.append(sub["总货量"])
            box_labels.append(lv)
    bp = ax.boxplot(box_data, labels=box_labels, patch_artist=True)
    for patch, c in zip(bp["boxes"],
                        ["#2ecc71", "#f39c12", "#e74c3c", "#95a5a6"][:len(box_labels)]):
        patch.set_facecolor(c); patch.set_alpha(0.6)
    ax.set_title("各产能等级分拣中心的货量分布", fontsize=14)
    ax.set_ylabel("总货量（件）")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "图9_产能等级货量分布.png"), dpi=150)
    plt.close()
    print("  图9_产能等级货量分布.png")

    # --- 图10：货量密度 vs 机器产能 热力图 ---
    dest_count = (df2.groupby("始发中心")["目的中心"]
                   .nunique().reset_index())
    dest_count.columns = ["分拣中心", "目的地数"]
    dest_count["标准名"] = dest_count["分拣中心"].apply(norm_name)

    merged2 = merged.merge(
        dest_count[["标准名", "目的地数"]], on="标准名", how="left"
    )
    merged2["每目的货量"] = merged2["总货量"] / merged2["目的地数"].replace(0, np.nan)

    hex_data = merged2[["每目的货量", "机器建包成本"]].dropna()
    if len(hex_data) > 0:
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.hexbin(
            hex_data["每目的货量"], hex_data["机器建包成本"],
            gridsize=20, cmap="YlOrRd", mincnt=1,
        )
        ax.set_xlabel("平均每目的地货量（件/目的地）", fontsize=12)
        ax.set_ylabel("机器建包成本（产能上限）", fontsize=12)
        ax.set_title("货量密度 vs 机器产能（六边形热力图）", fontsize=14)
        plt.colorbar(ax.collections[0], ax=ax, label="分拣中心数")
        plt.tight_layout()
        fig.savefig(os.path.join(OUT_DIR, "图10_货量密度_vs_机器产能_热力图.png"), dpi=150)
        plt.close()
        print("  图10_货量密度_vs_机器产能_热力图.png")

# ============================================================
# 8. 关键发现汇总
# ============================================================
print("\n" + "=" * 70)
print("【关键发现汇总】")
print("=" * 70)

findings = [
    f"1. 规模: {n_centers} 个分拣中心, {n_device_types} 种设备类型",
    f"2. 人工成本: 均值={labor.mean():.0f}, 中位数={labor.median():.0f}, "
    f"范围=[{labor.min():.0f}, {labor.max():.0f}], CV={labor.std()/labor.mean()*100:.1f}%",
    f"3. 机器产能: 均值={machine.mean():.0f}, 中位数={machine.median():.0f}, "
    f"范围=[{machine.min():.0f}, {machine.max():.0f}]",
    f"4. 人工>机器: {n_labor_expensive}/{n_rows} = {n_labor_expensive/n_rows*100:.1f}%"
    f" -- 即绝大多数情况下机器成本远高于人工",
    f"5. 产能等级: 高={capacity_dist.get('高产能',0)}, "
    f"中={capacity_dist.get('中产能',0)}, "
    f"低={capacity_dist.get('低产能',0)}, "
    f"异常={capacity_dist.get('零产能(异常)',0)}",
]

if len(zero_machine) > 0:
    findings.append(
        f"6. [异常] {len(zero_machine)}个中心机器成本为0: "
        f"{zero_machine['分拣中心'].tolist()}"
    )

if len(merged_valid) > 0:
    findings.append(
        f"7. 货量-产能相关性: r = {corr_val:.4f}"
        + ("（正相关）" if corr_val > 0 else "（负相关）")
    )
    findings.append(
        f"8. 产能匹配: 高货量+高产能={hh}个, "
        f"高货量+不够产能={hl}个, 低货量+过剩产能={lh}个"
    )

if "设备更优" in df4.columns:
    n_b = df4["设备更优"].sum()
    findings.append(f"9. 设备经济性: {n_b}/{len(df4)} ({n_b/len(df4)*100:.0f}%) "
                    f"种设备每格口天成本 < 人工")

    if "回收期_天" in df4.columns:
        pp_min = df4["回收期_天"].min()
        pp_max = df4["回收期_天"].max()
        findings.append(
            f"10. 投资回收期: {pp_min:.0f} ~ {pp_max:.0f} 天 "
            f"({pp_min/365:.1f} ~ {pp_max/365:.1f} 年)"
        )

for f in findings:
    print(f)

print("\n" + "=" * 70)
print(f"分析完成! 图表均保存至: {OUT_DIR}")
print("=" * 70)

"""
物流货量历史数据探索性数据分析 (EDA)
========================================
数据来源: 附件表2.csv（GBK编码）
输出目录: 分析结果_分拣中心评级/
依赖: pandas, numpy, matplotlib, seaborn, scipy, statsmodels
运行: py.exe eda_analysis.py
"""

import os, sys, warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import seaborn as sns
from scipy import stats
from statsmodels.tsa.stattools import adfuller

# ======================== 配置 ========================
DATA_PATH = r'c:\Users\www15\Desktop\26长三角数模\2026年第六届长三角高校数学建模竞赛赛题\2026长三角赛题A：物流网络集包规则及设备优化\附件表2.csv'
OUT_DIR = r'c:\Users\www15\Desktop\26长三角数模\分析结果_分拣中心评级'
os.makedirs(OUT_DIR, exist_ok=True)

# 中文字体设置
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid")

# ======================== 数据加载 ========================
print("=" * 60)
print("加载数据...")
df = pd.read_csv(DATA_PATH, encoding='gbk')
print(f"原始列名: {list(df.columns)}")

# 统一列名
df.columns = ['日期', '始分拣', '目的分拣', '货量']
print(f"行数: {len(df):,}")
print(f"列名: {list(df.columns)}")

# 日期转换
df['日期'] = pd.to_datetime(df['日期'])
df['流向'] = df['始分拣'] + ' -> ' + df['目的分拣']

# 排序
df = df.sort_values(['日期', '始分拣', '目的分拣']).reset_index(drop=True)

# ======================== 1. 基本统计 ========================
print("\n" + "=" * 60)
print("【1. 基本统计】")

date_min = df['日期'].min()
date_max = df['日期'].max()
n_days = (date_max - date_min).days + 1
n_rows = len(df)
n_flows = df['流向'].nunique()
n_origin = df['始分拣'].nunique()
n_dest = df['目的分拣'].nunique()

daily_flows = df.groupby('日期')['流向'].nunique()
avg_daily_flows = daily_flows.mean()

vol = df['货量']
vol_mean = vol.mean()
vol_median = vol.median()
vol_max = vol.max()
vol_min = vol.min()
vol_std = vol.std()
vol_skew = vol.skew()

print(f"数据时间范围: {date_min.date()} ~ {date_max.date()}，共 {n_days} 天")
print(f"总行数: {n_rows:,}")
print(f"唯一始分拣中心: {n_origin}  唯一目的分拣中心: {n_dest}")
print(f"唯一流向对 (始->目的): {n_flows:,}")
print(f"每天平均活跃流向数: {avg_daily_flows:.1f}  (范围: {daily_flows.min()} ~ {daily_flows.max()})")

print(f"\n货量基本统计:")
print(f"  均值: {vol_mean:.2f}   中位数: {vol_median:.2f}   标准差: {vol_std:.2f}")
print(f"  最大值: {vol_max:,.0f}   最小值: {vol_min}")
print(f"  偏度: {vol_skew:.2f}  (高度右偏)")
print(f"  25%分位数: {vol.quantile(0.25):.0f}   75%分位数: {vol.quantile(0.75):.0f}")

# 缺失值检查
print(f"\n缺失值检查:")
print(df.isnull().sum())

# ======================== 2. 货量分布特征 ========================
print("\n" + "=" * 60)
print("【2. 货量分布特征】")

# --- 2a. 整体分布直方图 ---
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# 原始坐标
ax = axes[0]
ax.hist(vol, bins=100, color='steelblue', edgecolor='white', alpha=0.85)
ax.set_title('货量分布（原始坐标）', fontsize=13)
ax.set_xlabel('货量（件）')
ax.set_ylabel('频次')
ax.axvline(vol_mean, color='red', linestyle='--', linewidth=1.5, label=f'均值={vol_mean:.0f}')
ax.axvline(vol_median, color='orange', linestyle='--', linewidth=1.5, label=f'中位数={vol_median:.0f}')
ax.legend(fontsize=9)

# 截断坐标（只显示0~5000）
ax = axes[1]
vol_clipped = vol[vol <= 5000]
ax.hist(vol_clipped, bins=100, color='steelblue', edgecolor='white', alpha=0.85)
ax.set_title('货量分布（0~5000 截断）', fontsize=13)
ax.set_xlabel('货量（件）')
ax.set_ylabel('频次')
ax.axvline(vol_mean, color='red', linestyle='--', linewidth=1.5)
ax.axvline(vol_median, color='orange', linestyle='--', linewidth=1.5)

# 对数坐标
ax = axes[2]
ax.hist(vol, bins=100, color='steelblue', edgecolor='white', alpha=0.85, log=True)
ax.set_title('货量分布（对数纵轴）', fontsize=13)
ax.set_xlabel('货量（件）')
ax.set_ylabel('频次 (log scale)')
ax.axvline(vol_mean, color='red', linestyle='--', linewidth=1.5)
ax.axvline(vol_median, color='orange', linestyle='--', linewidth=1.5)

plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'E1_货量分布直方图.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  图表已保存: E1_货量分布直方图.png")

# --- 2b. Top-20 高货量流向 ---
flow_total = df.groupby('流向')['货量'].sum().sort_values(ascending=False)
flow_avg_daily = df.groupby('流向')['货量'].mean().sort_values(ascending=False)
flow_count = df.groupby('流向').size().rename('记录数')
flow_stats = pd.DataFrame({
    '总货量': flow_total,
    '日均货量': flow_avg_daily,
    '活跃天数': flow_count,
}).sort_values('总货量', ascending=False)
# 确保活跃天数为整数（列对齐可能导致NaN -> float）
flow_stats['活跃天数'] = flow_stats['活跃天数'].fillna(0).astype(int)
flow_stats['活跃率'] = flow_stats['活跃天数'] / n_days

print("\nTop-20 高货量流向:")
top20 = flow_stats.head(20)
for i, (flow, row) in enumerate(top20.iterrows()):
    active_days = int(row['活跃天数'])
    print(f"  {i+1:2d}. {flow:20s}  总货量={row['总货量']:>10,.0f}  日均={row['日均货量']:>8.1f}  活跃天数={active_days:>4d}/{n_days}")

# --- 2c. 低货量流向占比 ---
threshold = 10  # 日均<10件
flow_daily_mean = df.groupby('流向')['货量'].mean()
low_volume_flows = (flow_daily_mean < threshold).sum()
low_volume_ratio = low_volume_flows / n_flows * 100
low_volume_volume = flow_total[flow_daily_mean[flow_daily_mean < threshold].index].sum()
low_volume_volume_ratio = low_volume_volume / vol.sum() * 100

print(f"\n低货量流向 (日均<{threshold}件):")
print(f"  流向数: {low_volume_flows} / {n_flows} ({low_volume_ratio:.1f}%)")
print(f"  贡献货量: {low_volume_volume:,.0f} / {vol.sum():,.0f} ({low_volume_volume_ratio:.2f}%)")

# 更多阈值
for th in [1, 5, 10, 20, 50, 100]:
    n = (flow_daily_mean < th).sum()
    ratio = n / n_flows * 100
    vol_sum = flow_total[flow_daily_mean[flow_daily_mean < th].index].sum()
    vol_ratio = vol_sum / vol.sum() * 100
    print(f"  日均<{th:4d}件: {n:6d} 流向 ({ratio:5.1f}%)  贡献货量 {vol_ratio:5.2f}%")

# --- 2d. 帕累托分布 ---
flow_total_sorted = flow_total.sort_values(ascending=False)
cumsum = flow_total_sorted.cumsum()
total_volume = flow_total_sorted.sum()
top20_pct = int(n_flows * 0.2)
top20_volume = flow_total_sorted.head(top20_pct).sum()
top20_volume_ratio = top20_volume / total_volume * 100

top10_pct = int(n_flows * 0.1)
top10_volume = flow_total_sorted.head(top10_pct).sum()
top10_volume_ratio = top10_volume / total_volume * 100

top50_pct = int(n_flows * 0.5)
top50_volume = flow_total_sorted.head(top50_pct).sum()
top50_volume_ratio = top50_volume / total_volume * 100

print(f"\n帕累托分布（货量集中度）:")
print(f"  前10%流向 ({top10_pct})  贡献货量: {top10_volume_ratio:.1f}%")
print(f"  前20%流向 ({top20_pct})  贡献货量: {top20_volume_ratio:.1f}%")
print(f"  前50%流向 ({top50_pct})  贡献货量: {top50_volume_ratio:.1f}%")

# 帕累托图
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

ax = axes[0]
cum_pct_flows = np.arange(1, len(flow_total_sorted) + 1) / len(flow_total_sorted) * 100
cum_pct_volume = cumsum.values / total_volume * 100
ax.plot(cum_pct_flows, cum_pct_volume, 'b-', linewidth=2)
ax.plot([0, 100], [0, 100], 'k--', linewidth=0.8, alpha=0.5, label='完全均匀')
ax.set_xlabel('流向累计占比 (%)')
ax.set_ylabel('货量累计占比 (%)')
ax.set_title('洛伦兹曲线 (流向-货量集中度)', fontsize=13)
ax.axvline(x=20, color='red', linestyle='--', alpha=0.6, label=f'前20%流向\n贡献{cum_pct_volume[int(n_flows*0.2)]:.1f}%')
ax.legend(fontsize=9)
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)

ax = axes[1]
top50 = flow_total_sorted.head(50)
colors = plt.cm.viridis(np.linspace(0.3, 0.9, 50))
ax.barh(range(50), top50.values[::-1], color=colors[::-1])
ax.set_yticks(range(50))
ax.set_yticklabels(top50.index[::-1], fontsize=7)
ax.set_xlabel('总货量（件）')
ax.set_title('Top-50 流向总货量', fontsize=13)
ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x/1e6:.1f}M' if x >= 1e6 else f'{x/1e3:.0f}K'))

plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'E2_帕累托分布.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  图表已保存: E2_帕累托分布.png")

# ======================== 3. 时间周期性与趋势 ========================
print("\n" + "=" * 60)
print("【3. 时间周期性与趋势】")

# 构建日汇总
daily_total = df.groupby('日期')['货量'].sum()
daily_count = df.groupby('日期').size().rename('记录数')

print(f"每日总货量基本统计:")
print(f"  均值: {daily_total.mean():,.0f}   中位数: {daily_total.median():,.0f}")
print(f"  最大日: {daily_total.idxmax().date()} ({daily_total.max():,.0f})")
print(f"  最小日: {daily_total.idxmin().date()} ({daily_total.min():,.0f})")

# --- 3a. 全网每日总货量时间序列 ---
fig, axes = plt.subplots(2, 1, figsize=(16, 8))

ax = axes[0]
ax.plot(daily_total.index, daily_total.values, 'b-', linewidth=1.2, alpha=0.8, marker='o', markersize=2)
# 7日移动平均
ma7 = daily_total.rolling(7, center=True).mean()
ax.plot(ma7.index, ma7.values, 'r-', linewidth=2, label='7日移动平均')
# 线性趋势
from numpy.polynomial.polynomial import polyfit
x_num = np.arange(len(daily_total))
coefs = polyfit(x_num, daily_total.values, 1)
trend_line = coefs[0] + coefs[1] * x_num
ax.plot(daily_total.index, trend_line, 'g--', linewidth=1.5, label='线性趋势')
ax.set_title('全网每日总货量时间序列', fontsize=14)
ax.set_ylabel('总货量（件）')
ax.legend(fontsize=9)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))

ax = axes[1]
ax.plot(daily_count.index, daily_count.values, 'purple', linewidth=1.2, alpha=0.8, marker='o', markersize=2)
ax.set_title('每日活跃记录数（流向×日期）', fontsize=14)
ax.set_ylabel('记录数')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))

plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'E3_每日总货量趋势.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  图表已保存: E3_每日总货量趋势.png")

# --- 3b. 星期效应 ---
df['星期'] = df['日期'].dt.dayofweek  # 0=周一, 6=周日
df['星期名'] = df['日期'].dt.day_name()
weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
weekday_cn = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
weekday_map = dict(zip(weekday_order, weekday_cn))
df['星期名_cn'] = df['星期名'].map(weekday_map)

daily_total_weekday = daily_total.to_frame('总货量')
daily_total_weekday['星期'] = daily_total_weekday.index.dayofweek
daily_total_weekday['星期名_cn'] = daily_total_weekday.index.day_name().map(weekday_map)

weekday_stats = daily_total_weekday.groupby('星期名_cn')['总货量'].agg(['mean', 'median', 'std', 'count'])
# 按周一到周日排序
weekday_stats = weekday_stats.reindex(weekday_cn)

print("\n星期效应分析 (全网日总货量):")
for day in weekday_cn:
    row = weekday_stats.loc[day]
    print(f"  {day}: 均值={row['mean']:,.0f}  中位数={row['median']:,.0f}  标准差={row['std']:,.0f}  天数={row['count']:.0f}")

# 方差分析 (ANOVA) 检验星期效应显著性
groups = [daily_total_weekday[daily_total_weekday['星期名_cn'] == d]['总货量'].values for d in weekday_cn]
f_stat, p_val = stats.f_oneway(*groups)
print(f"  单因素ANOVA: F={f_stat:.2f}, p={p_val:.6f}  {'***显著***' if p_val < 0.01 else '不显著'}")

# 箱线图
fig, axes = plt.subplots(1, 2, figsize=(16, 5))

ax = axes[0]
data_by_weekday = [daily_total_weekday[daily_total_weekday['星期名_cn'] == d]['总货量'].values for d in weekday_cn]
bp = ax.boxplot(data_by_weekday, labels=weekday_cn, patch_artist=True)
colors = plt.cm.Set2(np.linspace(0, 1, 7))
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
ax.set_title('全网日总货量 — 星期效应箱线图', fontsize=14)
ax.set_ylabel('日总货量（件）')
ax.set_xlabel('星期')

# 归一化星期效应
ax = axes[1]
weekday_mean = daily_total_weekday.groupby('星期名_cn')['总货量'].mean()
weekday_mean = weekday_mean.reindex(weekday_cn)
overall_mean = daily_total.mean()
weekday_normalized = (weekday_mean / overall_mean - 1) * 100
ax.bar(weekday_cn, weekday_normalized.values, color=colors, edgecolor='black', alpha=0.85)
ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
ax.set_title('星期效应 — 偏离总体均值百分比', fontsize=14)
ax.set_ylabel('偏离总体均值 (%)')
ax.set_xlabel('星期')
for i, v in enumerate(weekday_normalized.values):
    ax.text(i, v + (0.5 if v >= 0 else -1.5), f'{v:+.1f}%', ha='center', fontsize=10, fontweight='bold')

plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'E4_星期效应.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  图表已保存: E4_星期效应.png")

# --- 3c. 月度趋势 ---
df['年月'] = df['日期'].dt.to_period('M')
monthly_total = df.groupby('年月')['货量'].sum()
monthly_days = df.groupby('年月')['日期'].nunique()
monthly_avg_daily = monthly_total / monthly_days

print("\n月度趋势:")
for month in monthly_total.index:
    print(f"  {month}: 总货量={monthly_total[month]:,.0f}  日均={monthly_avg_daily[month]:,.0f}  天数={monthly_days[month]}")

# 月环比
if len(monthly_total) >= 2:
    mom_change = monthly_total.pct_change() * 100
    print(f"\n月环比增长率:")
    for month in monthly_total.index[1:]:
        print(f"  {month}: {mom_change[month]:+.1f}%")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

ax = axes[0]
ax.bar(monthly_total.index.astype(str), monthly_total.values, color='steelblue', edgecolor='black', alpha=0.85)
ax.set_title('月总货量', fontsize=13)
ax.set_ylabel('总货量（件）')
ax.set_xlabel('月份')
ax.tick_params(axis='x', rotation=45)

ax = axes[1]
ax.plot(monthly_avg_daily.index.astype(str), monthly_avg_daily.values, 'o-', color='darkgreen',
        linewidth=2, markersize=8, markerfacecolor='limegreen')
ax.set_title('月日均货量', fontsize=13)
ax.set_ylabel('日均货量（件/天）')
ax.set_xlabel('月份')
ax.tick_params(axis='x', rotation=45)

plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'E5_月度趋势.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  图表已保存: E5_月度趋势.png")

# --- 3d. 整体增长/下降趋势 ---
# 线性回归
from sklearn.linear_model import LinearRegression
x_days = np.arange(len(daily_total)).reshape(-1, 1)
y_vals = daily_total.values
lr = LinearRegression()
lr.fit(x_days, y_vals)
slope = lr.coef_[0]
daily_mean_val = daily_total.mean()
trend_pct_per_day = slope / daily_mean_val * 100
trend_pct_total = slope * len(daily_total) / y_vals[0] * 100
r2 = lr.score(x_days, y_vals)

print(f"\n整体趋势分析:")
print(f"  线性趋势斜率: {slope:+.1f} 件/天  (日均{trend_pct_per_day:+.3f}%)")
print(f"  相对于首日: 累计变化约 {trend_pct_total:+.1f}%")
print(f"  R^2 = {r2:.4f}")

# ======================== 4. 流向级别时间序列 ========================
print("\n" + "=" * 60)
print("【4. 流向级别时间序列】")

top5_flows = flow_total.head(5).index.tolist()
print(f"Top-5 高货量流向:")
for i, f in enumerate(top5_flows):
    print(f"  {i+1}. {f}  总货量={flow_total[f]:,.0f}")

fig, axes = plt.subplots(5, 1, figsize=(16, 14), sharex=True)

for i, flow in enumerate(top5_flows):
    ax = axes[i]
    flow_data = df[df['流向'] == flow].groupby('日期')['货量'].sum()
    # 构建完整日期索引，缺失日期填0
    full_idx = pd.date_range(date_min, date_max, freq='D')
    flow_data = flow_data.reindex(full_idx, fill_value=0)
    ax.plot(flow_data.index, flow_data.values, linewidth=0.8, alpha=0.9, marker='.', markersize=1)
    ma7_f = flow_data.rolling(7, center=True).mean()
    ax.plot(ma7_f.index, ma7_f.values, 'r-', linewidth=1.5, alpha=0.7, label='7日MA')
    ax.set_title(f'{flow}  (总货量: {flow_total[flow]:,.0f}  日均: {flow_total[flow]/n_days:,.0f})', fontsize=11)
    ax.set_ylabel('货量')
    ax.legend(fontsize=8, loc='upper right')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax.xaxis.set_major_locator(mdates.MonthLocator())

plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'E6_Top5流向时间序列.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  图表已保存: E6_Top5流向时间序列.png")

# --- 高货量流向的星期效应一致性 ---
print("\nTop-10 流向的星期效应 (偏离各自均值 %):")
fig, ax = plt.subplots(figsize=(14, 6))
top10_flows = flow_total.head(10).index.tolist()
weekday_deviations = {}
for flow in top10_flows:
    flow_daily = df[df['流向'] == flow].groupby('日期')['货量'].sum()
    flow_by_wd = flow_daily.groupby(flow_daily.index.dayofweek).mean()
    flow_mean = flow_daily.mean()
    if flow_mean > 0:
        dev = [(flow_by_wd.get(d, 0) / flow_mean - 1) * 100 for d in range(7)]
    else:
        dev = [0] * 7
    weekday_deviations[flow] = dev
    ax.plot(weekday_cn, dev, 'o-', linewidth=1.5, markersize=5, label=flow[:25], alpha=0.8)

ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
ax.set_title('Top-10 高货量流向的星期效应模式', fontsize=14)
ax.set_ylabel('偏离各自日均值 (%)')
ax.set_xlabel('星期')
ax.legend(fontsize=8, loc='lower left', ncol=2)
plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'E7_Top10流向星期效应.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  图表已保存: E7_Top10流向星期效应.png")

# ======================== 5. 稀疏性分析 ========================
print("\n" + "=" * 60)
print("【5. 稀疏性分析】")

# 构建流向×日期矩阵（抽样：取货量最高的50个流向显示）
pivot_flows = flow_total.head(50).index.tolist()
df_top = df[df['流向'].isin(pivot_flows)]
pivot = df_top.pivot_table(values='货量', index='流向', columns='日期', aggfunc='sum', fill_value=0)

# 计算稀疏度
total_cells = n_flows * n_days
non_zero_cells = len(df)
sparsity = (1 - non_zero_cells / total_cells) * 100

print(f"全矩阵稀疏性:")
print(f"  理论矩阵大小 (流向×日期): {n_flows:,} × {n_days} = {total_cells:,}")
print(f"  非零单元格: {non_zero_cells:,}")
print(f"  稀疏度: {sparsity:.2f}%")

# 每个流向的活跃天数分布
flow_active_days = df.groupby('流向')['日期'].nunique()
print(f"\n流向活跃天数分布:")
print(f"  均值: {flow_active_days.mean():.1f} 天")
print(f"  中位数: {flow_active_days.median():.0f} 天")
print(f"  最小值: {flow_active_days.min()} 天")
print(f"  最大值: {flow_active_days.max()} 天")

# 活跃天数分段统计
bins = [0, 1, 5, 10, 30, 60, 120, 200]
labels = ['1天', '2-5天', '6-10天', '11-30天', '31-60天', '61-120天', '121天+']
flow_active_bins = pd.cut(flow_active_days, bins=bins, labels=labels, right=True)
print(f"\n活跃天数分布:")
for label in labels:
    cnt = (flow_active_bins == label).sum()
    pct = cnt / n_flows * 100
    print(f"  {label}: {cnt:>6} 流向 ({pct:5.1f}%)")

# 热力图
fig, axes = plt.subplots(1, 2, figsize=(18, 7))

ax = axes[0]
# Top-50流向 × 日期
log_pivot = np.log1p(pivot.values)
im = ax.imshow(log_pivot, aspect='auto', cmap='YlOrRd', interpolation='none')
ax.set_title(f'Top-50流向 × 日期 货量热力图 (log1p)', fontsize=13)
ax.set_xlabel('日期')
ax.set_ylabel('流向')
ax.set_yticks(range(min(50, len(pivot))))
ax.set_yticklabels(pivot.index[:50], fontsize=6)
# x轴只显示少量日期标签
n_dates = pivot.shape[1]
tick_step = max(1, n_dates // 12)
ax.set_xticks(range(0, n_dates, tick_step))
ax.set_xticklabels([d.strftime('%m-%d') for d in pivot.columns[::tick_step]], rotation=45, fontsize=7)
plt.colorbar(im, ax=ax, label='log(1+货量)')

# 活跃天数分布
ax = axes[1]
active_counts = flow_active_bins.value_counts().reindex(labels, fill_value=0)
ax.bar(labels, active_counts.values, color='steelblue', edgecolor='black', alpha=0.85)
ax.set_title('流向活跃天数分布', fontsize=13)
ax.set_xlabel('活跃天数')
ax.set_ylabel('流向数')
ax.tick_params(axis='x', rotation=30)
for i, v in enumerate(active_counts.values):
    ax.text(i, v + max(active_counts.values) * 0.02, str(v), ha='center', fontsize=9)

plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'E8_稀疏性分析.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  图表已保存: E8_稀疏性分析.png")

# ======================== 6. 平稳性检验 ========================
print("\n" + "=" * 60)
print("【6. 平稳性检验 (ADF检验)】")

def adf_test(series, name):
    """执行ADF检验并返回结果"""
    result = adfuller(series.dropna(), autolag='AIC')
    print(f"\n  {name}:")
    print(f"    ADF统计量: {result[0]:.4f}")
    print(f"    p值: {result[1]:.6f}")
    print(f"    临界值: 1%={result[4]['1%']:.4f}, 5%={result[4]['5%']:.4f}, 10%={result[4]['10%']:.4f}")
    is_stationary = result[1] < 0.05
    print(f"    结论: {'平稳 P' if is_stationary else '非平稳 NP'} (p{'<' if result[1] < 0.05 else '>='}0.05)")
    return result[0], result[1], is_stationary

# 6a. 全网日总货量
adf_test(daily_total, "全网日总货量")

# 6b. 一阶差分后
daily_diff = daily_total.diff().dropna()
adf_test(daily_diff, "全网日总货量 (一阶差分)")

# 6c. 代表性高货量流向
sample_flows = flow_total.head(5).index.tolist()
if n_flows > 10:
    sample_flows += [flow_total.index[len(flow_total)//2]]  # 中位数流向
if n_flows > 50:
    sample_flows.append(flow_total.index[-1])  # 最低货量流向

for flow in sample_flows[:7]:
    flow_daily = df[df['流向'] == flow].groupby('日期')['货量'].sum()
    full_idx = pd.date_range(date_min, date_max, freq='D')
    flow_daily = flow_daily.reindex(full_idx, fill_value=0)
    if flow_daily.std() > 0:
        adf_test(flow_daily, f"{flow}")

# ======================== 附加分析：始分拣/目的分拣维度 ========================
print("\n" + "=" * 60)
print("【附加分析：分拣中心维度】")

# 始分拣中心总发出货量
origin_total = df.groupby('始分拣')['货量'].sum().sort_values(ascending=False)
dest_total = df.groupby('目的分拣')['货量'].sum().sort_values(ascending=False)

print(f"\nTop-10 始分拣中心 (发出货量):")
for i, (center, vol) in enumerate(origin_total.head(10).items()):
    print(f"  {i+1:2d}. {center:10s}  发出: {vol:>12,.0f} 件  ({vol/total_volume*100:5.1f}%)")

print(f"\nTop-10 目的分拣中心 (到达货量):")
for i, (center, vol) in enumerate(dest_total.head(10).items()):
    print(f"  {i+1:2d}. {center:10s}  到达: {vol:>12,.0f} 件  ({vol/total_volume*100:5.1f}%)")

# 分拣中心出入比
origin_set = set(df['始分拣'].unique())
dest_set = set(df['目的分拣'].unique())
all_centers = origin_set | dest_set
print(f"\n分拣中心总数 (去重): {len(all_centers)}")
print(f"仅作为始发: {len(origin_set - dest_set)}")
print(f"仅作为目的: {len(dest_set - origin_set)}")
print(f"双向: {len(origin_set & dest_set)}")

# 中心货量分布图
fig, axes = plt.subplots(1, 2, figsize=(16, 5))

ax = axes[0]
top_origins = origin_total.head(30)
colors_o = plt.cm.Blues(np.linspace(0.4, 0.9, 30))
ax.barh(range(30), top_origins.values[::-1], color=colors_o[::-1], edgecolor='black')
ax.set_yticks(range(30))
ax.set_yticklabels(top_origins.index[::-1], fontsize=8)
ax.set_title('Top-30 始分拣中心 — 发出货量', fontsize=13)
ax.set_xlabel('总货量（件）')
ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x/1e6:.2f}M' if x >= 1e6 else f'{x/1e3:.0f}K'))

ax = axes[1]
top_dests = dest_total.head(30)
colors_d = plt.cm.Oranges(np.linspace(0.4, 0.9, 30))
ax.barh(range(30), top_dests.values[::-1], color=colors_d[::-1], edgecolor='black')
ax.set_yticks(range(30))
ax.set_yticklabels(top_dests.index[::-1], fontsize=8)
ax.set_title('Top-30 目的分拣中心 — 到达货量', fontsize=13)
ax.set_xlabel('总货量（件）')
ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x/1e6:.2f}M' if x >= 1e6 else f'{x/1e3:.0f}K'))

plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'E9_分拣中心货量排名.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  图表已保存: E9_分拣中心货量排名.png")

# ======================== 汇总输出 ========================
print("\n" + "=" * 60)
print("分析完成！所有图表已保存至:", OUT_DIR)

# 列出生成的文件
print("\n生成文件列表:")
for f in sorted(os.listdir(OUT_DIR)):
    if f.endswith('.png'):
        print(f"  {f}")

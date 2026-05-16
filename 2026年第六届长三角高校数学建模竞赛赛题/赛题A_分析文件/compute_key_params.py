"""
A题关键定量参数计算脚本
=========================
用途: 为论文"问题分析"章节计算建模所需的关键定量参数
依赖: pandas, numpy, python-calamine (for xlsx)
运行: py.exe compute_key_params.py
GBK编码数据文件读取
输出: 终端打印所有15个参数项的计算结果
"""

import sys, os, warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
from itertools import combinations

# ======================== 路径配置 ========================
BASE = r'c:\Users\www15\Desktop\26长三角数模\2026年第六届长三角高校数学建模竞赛赛题\2026长三角赛题A：物流网络集包规则及设备优化'
T1 = os.path.join(BASE, '附件表1.csv')
T2 = os.path.join(BASE, '附件表2.csv')
T3 = os.path.join(BASE, '附件表3.csv')
T4 = os.path.join(BASE, '附件表4.xlsx')

# ======================== 数据加载 ========================
print("=" * 70)
print("加载数据文件...")

df1 = pd.read_csv(T1, encoding='GBK')
df1.columns = ['始分拣', '目的分拣', '走货路由']
print(f"  附件表1: {len(df1):,} 行, 列={list(df1.columns)}")

df2 = pd.read_csv(T2, encoding='GBK')
df2.columns = ['日期', '始分拣', '目的分拣', '货量']
df2['日期'] = pd.to_datetime(df2['日期'])
print(f"  附件表2: {len(df2):,} 行, 列={list(df2.columns)}")

df3 = pd.read_csv(T3, encoding='GBK')
df3.columns = ['分拣中心', '设备类型', '格口数量', '日产能']
print(f"  附件表3: {len(df3):,} 行, 列={list(df3.columns)}")

df4 = pd.read_excel(T4)
df4.columns = ['设备编号', '格口数', '设计产能', '折旧年限', '设备成本']
print(f"  附件表4: {len(df4):,} 行, 列={list(df4.columns)}")

# ======================== 辅助变量 ========================
# 日期范围
date_min = df2['日期'].min()
date_max = df2['日期'].max()
n_days = (date_max - date_min).days + 1
print(f"\n历史数据日期范围: {date_min.date()} ~ {date_max.date()}, 共 {n_days} 天")

# OD对列表
od_pairs_table1 = df1[['始分拣', '目的分拣']].drop_duplicates()
od_pairs_table2 = df2[['始分拣', '目的分拣']].drop_duplicates()

# 统一OD对标识
od_pairs_table1['OD'] = od_pairs_table1['始分拣'] + '->' + od_pairs_table1['目的分拣']
od_pairs_table2['OD'] = od_pairs_table2['始分拣'] + '->' + od_pairs_table2['目的分拣']

df1['OD'] = df1['始分拣'] + '->' + df1['目的分拣']
df2['OD'] = df2['始分拣'] + '->' + df2['目的分拣']

set_od1 = set(od_pairs_table1['OD'])
set_od2 = set(od_pairs_table2['OD'])

print(f"附件表1 OD对数: {len(set_od1)}")
print(f"附件表2 OD对数: {len(set_od2)}")
print(f"两表共同OD对: {len(set_od1 & set_od2)}")
print(f"仅在附件表1: {len(set_od1 - set_od2)}")
print(f"仅在附件表2: {len(set_od2 - set_od1)}")

# ================================================================
#  问题1 相关参数
# ================================================================
print("\n" + "=" * 70)
print("【问题1：货量预测相关参数】")
print("=" * 70)

# --- 1. 预测目标：未来7天的OD对数 ---
# 预测目标应是附件表1中所有有路由定义的OD对
# （即使某些OD对在历史数据中没有出现，也需要预测——可能为0或少量）
n_predict_ods = len(set_od1)
print(f"\n1. 预测目标OD对数: {n_predict_ods}")
print(f"   说明: 附件表1定义了{n_predict_ods}个OD对的走货路由，需对每个OD对预测未来7天货量，")
print(f"   共需产生 {n_predict_ods * 7:,} 个预测值")

# --- 2. 历史数据可用于训练的样本量 ---
# 训练集 = 全历史 - 最后14天
train_end = date_max - pd.Timedelta(days=14)
df_train = df2[df2['日期'] <= train_end]
df_val = df2[df2['日期'] > train_end]

print(f"\n2. 训练/验证集划分:")
print(f"   训练集: {date_min.date()} ~ {train_end.date()}, 共 {(train_end - date_min).days + 1} 天")
print(f"   验证集: {(train_end + pd.Timedelta(days=1)).date()} ~ {date_max.date()}, 共 14 天")
print(f"   训练样本数: {len(df_train):,} 行")
print(f"   验证样本数: {len(df_val):,} 行")

# --- 3. 每个OD对的日均货量分布 ---
od_daily_mean = df2.groupby('OD')['货量'].mean()

bins = [0, 10, 100, 1000, float('inf')]
labels = ['<10', '10-100', '100-1000', '>1000']
od_vol_bucket = pd.cut(od_daily_mean, bins=bins, labels=labels, right=False)
bucket_counts = od_vol_bucket.value_counts().reindex(labels, fill_value=0)

print(f"\n3. OD对日均货量分布（基于{len(set_od2)}个有历史数据的OD对）:")
for label in labels:
    cnt = bucket_counts[label]
    pct = cnt / len(od_daily_mean) * 100
    print(f"   日均{label:>8}件: {cnt:>6} 个OD对 ({pct:5.1f}%)")

print(f"   说明: 长尾效应显著，大量OD对日均货量极低，需在预测模型中处理稀疏性")

# --- 4. 春节效应量化 ---
# 2026年春节是2月17日，春节月=2月
df2['月份'] = df2['日期'].dt.month
feb_data = df2[df2['月份'] == 2]
non_feb_data = df2[df2['月份'] != 2]

feb_daily = feb_data.groupby('日期')['货量'].sum()
non_feb_daily = non_feb_data.groupby('日期')['货量'].sum()

feb_daily_mean = feb_daily.mean()
non_feb_daily_mean = non_feb_daily.mean()
spring_ratio = feb_daily_mean / non_feb_daily_mean

print(f"\n4. 春节效应量化:")
print(f"   2月日均全网货量: {feb_daily_mean:,.0f} 件/天 (共{len(feb_daily)}天)")
print(f"   非2月日均全网货量: {non_feb_daily_mean:,.0f} 件/天 (共{len(non_feb_daily)}天)")
print(f"   比值 (2月 / 非2月): {spring_ratio:.4f}")
print(f"   春节月货量约为平日的 {spring_ratio*100:.1f}%")

# 按月份详细
monthly_daily_vol = df2.groupby(df2['日期'].dt.month).apply(
    lambda g: g.groupby('日期')['货量'].sum().mean()
)
print(f"   各月日均全网货量:")
for m in sorted(monthly_daily_vol.index):
    ratio_vs_mean = monthly_daily_vol[m] / non_feb_daily_mean
    print(f"     {m}月: {monthly_daily_vol[m]:,.0f} 件/天 (相对基准={ratio_vs_mean:.3f})")

# --- 5. Naive预测方法的MAE基准 ---
# Naive方法: 用前7天均值预测后7天
# 对每个OD对的每个验证日，用该OD对前7天日均值作为预测值
print(f"\n5. Naive方法（前7天均值）的MAE基准:")

# 构建完整日期序列
all_dates = pd.date_range(date_min, date_max, freq='D')
# 对每个OD对构建日货量序列
od_daily_pivot = df2.pivot_table(
    values='货量', index='OD', columns='日期', aggfunc='sum', fill_value=0
)
# 确保列覆盖所有日期
od_daily_pivot = od_daily_pivot.reindex(columns=all_dates, fill_value=0)

naive_errors = []
n_valid_pairs = 0

for od in od_daily_pivot.index:
    series = od_daily_pivot.loc[od].values
    for t in range(len(all_dates) - 14, len(all_dates)):
        # 用前7天均值预测
        if t >= 7:
            pred = series[t-7:t].mean()
        else:
            pred = series[:t].mean() if t > 0 else 0
        actual = series[t]
        naive_errors.append(abs(pred - actual))
        n_valid_pairs += 1

naive_mae = np.mean(naive_errors)
print(f"   全局MAE: {naive_mae:.2f} 件/天")
print(f"   预测天数: 14天 × {od_daily_pivot.shape[0]} OD对 = {n_valid_pairs:,} 个预测点")

# 日均货量归一化MAE
overall_daily_mean_per_od = od_daily_pivot.values.flatten()
overall_daily_mean_per_od = overall_daily_mean_per_od[overall_daily_mean_per_od > 0].mean()
nmae = naive_mae / overall_daily_mean_per_od * 100
print(f"   归一化MAE (NMAE): {nmae:.2f}% (相对于非零OD对日均货量均值 {overall_daily_mean_per_od:.0f})")

# 按日均货量分桶的MAE
for label, (low, high) in zip(labels, [(0,10), (10,100), (100,1000), (1000, float('inf'))]):
    ods_in_bucket = od_daily_mean[(od_daily_mean >= low) & (od_daily_mean < high)].index
    if len(ods_in_bucket) == 0:
        continue
    bucket_errors = []
    for od in ods_in_bucket:
        if od not in od_daily_pivot.index:
            continue
        series = od_daily_pivot.loc[od].values
        for t in range(len(all_dates) - 14, len(all_dates)):
            if t >= 7:
                pred = series[t-7:t].mean()
            else:
                pred = series[:t].mean() if t > 0 else 0
            actual = series[t]
            bucket_errors.append(abs(pred - actual))
    if bucket_errors:
        b_mae = np.mean(bucket_errors)
        b_mean_vol = od_daily_mean.loc[ods_in_bucket].mean()
        print(f"   日均{label:>8}件: MAE={b_mae:.1f}, 相对误差={b_mae/b_mean_vol*100:.1f}% (共{len(ods_in_bucket)}个OD对)")

# ================================================================
#  问题2 相关参数
# ================================================================
print("\n" + "=" * 70)
print("【问题2：集包优化相关参数】")
print("=" * 70)

# 分析路由长度
# 注意：部分OD对有多个不同路由（2038个OD对），取所有路由进行分析
df1_unique = df1[['OD', '走货路由']].drop_duplicates()
n_od_multi = df1_unique.groupby('OD').size()
n_ods_with_multi_route = (n_od_multi > 1).sum()
print(f"附件表1中唯一OD-路由组合: {len(df1_unique)}")
print(f"唯一OD对数: {len(set_od1)}")
print(f"有多个不同路由的OD对: {n_ods_with_multi_route} (占 {n_ods_with_multi_route/len(set_od1)*100:.1f}%)")
print(f"  [WARNING] 问题描述称路由唯一, 但数据中部分OD有替代路由, 需在建模时处理")

# 解析路由
def parse_route(route_str):
    """解析路由字符串，返回站点列表"""
    stations = [s.strip() for s in route_str.split('-')]
    return stations

df1_unique['站点列表'] = df1_unique['走货路由'].apply(parse_route)
df1_unique['路由长度'] = df1_unique['站点列表'].apply(len)

route_len_dist = df1_unique['路由长度'].value_counts().sort_index()
print(f"\n路由长度分布 (途经站点数):")
for length, cnt in route_len_dist.items():
    pct = cnt / len(df1_unique) * 100
    print(f"   长度{length}: {cnt:>6} 条路由 ({pct:5.1f}%)")

avg_route_len = df1_unique['路由长度'].mean()
print(f"   平均路由长度: {avg_route_len:.2f} 个站点")

# 中间站数 = 路由长度 - 2（去掉首末）
df1_unique['中间站数'] = df1_unique['路由长度'] - 2
avg_mid_stations = df1_unique['中间站数'].mean()
total_mid_stations = df1_unique['中间站数'].sum()

# --- 6. 优化变量规模 ---
# 每个OD对的建包决策点 = 中间站数（每个中转站决定是否集包/拆包）
# 变量总数 ≈ OD对数 × 平均中间站数
n_vars = len(df1_unique) * avg_mid_stations
print(f"\n6. 优化变量规模:")
print(f"   OD对数: {len(df1_unique)}")
print(f"   平均中间站数/OD对: {avg_mid_stations:.2f}")
print(f"   总中间站数（含重复）: {total_mid_stations:,}")
print(f"   优化变量规模 ≈ {n_vars:,.0f} (每个中转站一个建包决策)")

# --- 7. 枚举空间：每个OD对可能建包方案数 ---
# 对于路由长度L，中间站有L-2个，每个可选"建包"或"不建包"
# 但约束是：首站必建包，末站必拆包，中间站可选
# 建包方案数 = 2^(L-2) （每个中间站独立选择是否建包）
print(f"\n7. 每个OD对可能建包方案数:")
route_len_counts = df1_unique['路由长度'].value_counts().sort_index()
total_combinations = 0
for length, cnt in route_len_counts.items():
    mid = length - 2
    n_plans = 2 ** mid
    total_combinations += n_plans * cnt
    print(f"   路由长度{length} (中间站{mid}): {n_plans:>4} 种建包方案 × {cnt:>5}条路由 = {n_plans*cnt:>10,}")

print(f"   全网络可能建包方案总枚举空间: {total_combinations:,}")
print(f"   说明: 这是无约束的上界，实际需考虑首站必建包/末站必拆包的约束")
# 如果有约束：首站必建包，中间可选建/拆，末站必拆包
# 对于长度2的路由：2^0=1种（只在首站建包末站拆包）
# 对于长度3：2^1=2种（中间站建包或不建包）
# 对于长度4：2^2=4种
# 对于长度5：2^3=8种

# --- 8. 总格口资源 ---
total_slots = df3['格口数量'].sum()
print(f"\n8. 总格口资源:")
print(f"   全网络 {len(df3)} 个分拣中心，总格口数: {total_slots:,}")

# 各设备类型分布
print(f"   各设备类型格口分布:")
for eq_type in sorted(df3['设备类型'].unique()):
    subset = df3[df3['设备类型'] == eq_type]
    slots_sum = subset['格口数量'].sum()
    count = len(subset)
    print(f"     {eq_type}: {count} 个中心, 总格口={slots_sum:,}, 平均格口={slots_sum/count:.0f}")

# --- 9. 总产能资源 ---
total_capacity = df3['日产能'].sum()
print(f"\n9. 总产能资源:")
print(f"   全网络总日产能: {total_capacity:,} 件/天")

# 注意A31格口产能为0
zero_capacity = df3[df3['日产能'] == 0]
if len(zero_capacity) > 0:
    print(f"   [WARNING] 产能为0的站点: {len(zero_capacity)} 个")
    for _, row in zero_capacity.iterrows():
        print(f"      {row['分拣中心']}: 格口={row['格口数量']}, 产能={row['日产能']}")

# --- 10. 日均总货量 vs 总产能 ---
daily_vol = df2.groupby('日期')['货量'].sum()
avg_daily_vol = daily_vol.mean()
capacity_ratio = avg_daily_vol / total_capacity * 100

print(f"\n10. 日均总货量 vs 总产能:")
print(f"    全网日均总货量: {avg_daily_vol:,.0f} 件/天")
print(f"    全网总日产能: {total_capacity:,} 件/天")
print(f"    比值 (需求/产能): {capacity_ratio:.2f}%")
print(f"    说明: 总体产能{'充足' if capacity_ratio < 100 else '紧张'}，但可能存在结构性瓶颈")

# 峰值日分析
peak_day = daily_vol.idxmax()
peak_vol = daily_vol.max()
peak_ratio = peak_vol / total_capacity * 100
print(f"    峰值日 ({peak_day.date()}): {peak_vol:,.0f} 件, 产能利用率 {peak_ratio:.1f}%")

# --- 11. 格口/产能利用率瓶颈站 Top-5 ---
# 计算每个分拣中心的日均处理货量
# 始分拣中心处理的是该站发出的所有货量
# 目的分拣中心处理的是到达该站的所有货量
# 中转站处理的是途经该站的所有货量

# 方法1：始发+到达的日货量
origin_daily = df2.groupby(['日期', '始分拣'])['货量'].sum().reset_index()
origin_daily.columns = ['日期', '分拣中心', '发出货量']

dest_daily = df2.groupby(['日期', '目的分拣'])['货量'].sum().reset_index()
dest_daily.columns = ['日期', '分拣中心', '到达货量']

# 合并为每个站每日总处理量（简化：发出+到达）
center_vol = pd.merge(origin_daily, dest_daily, on=['日期', '分拣中心'], how='outer').fillna(0)
center_vol['总处理量'] = center_vol['发出货量'] + center_vol['到达货量']
center_daily_mean = center_vol.groupby('分拣中心')['总处理量'].mean().sort_values(ascending=False)

# 合并产能信息
df3_indexed = df3.set_index('分拣中心')

# 计算各中心产能利用率
utilization_data = []
for center in center_daily_mean.index:
    if center in df3_indexed.index:
        avg_vol = center_daily_mean[center]
        capacity = df3_indexed.loc[center, '日产能']
        slots = df3_indexed.loc[center, '格口数量']
        if capacity > 0:
            util = avg_vol / capacity * 100
        else:
            util = float('inf')
        if slots > 0:
            vol_per_slot = avg_vol / slots
        else:
            vol_per_slot = float('inf')
        utilization_data.append({
            '分拣中心': center,
            '日均处理量(件)': avg_vol,
            '日产能': capacity,
            '格口数': slots,
            '产能利用率(%)': util,
            '每格口日处理量': vol_per_slot,
        })

df_util = pd.DataFrame(utilization_data)

print(f"\n11. 格口/产能利用率瓶颈站 Top-5:")

# Top-5 产能利用率最高
top5_cap = df_util[df_util['产能利用率(%)'] != float('inf')].nlargest(5, '产能利用率(%)')
print(f"\n   【产能利用率最高 Top-5】")
for i, (_, row) in enumerate(top5_cap.iterrows()):
    print(f"   {i+1}. {row['分拣中心']:>8s}: 日均处理 {row['日均处理量(件)']:>10,.0f}件, "
          f"产能 {row['日产能']:>8,}, 利用率 {row['产能利用率(%)']:6.1f}%, "
          f"格口 {row['格口数']:>5.0f}, 每格口 {row['每格口日处理量']:>8,.0f}件")

# Top-5 每格口日处理量最高
top5_slot = df_util[df_util['每格口日处理量'] != float('inf')].nlargest(5, '每格口日处理量')
print(f"\n   【每格口处理量最高 Top-5（格口资源最紧张）】")
for i, (_, row) in enumerate(top5_slot.iterrows()):
    print(f"   {i+1}. {row['分拣中心']:>8s}: 每格口日处理 {row['每格口日处理量']:>10,.0f}件, "
          f"日均总处理 {row['日均处理量(件)']:>10,.0f}件, "
          f"格口 {row['格口数']:>5.0f}, 产能利用率 {row['产能利用率(%)']:6.1f}%")

# 双向统合排名（产能利用率 × 每格口处理量的几何平均）
df_util['综合紧张度'] = np.sqrt(
    df_util['产能利用率(%)'].clip(upper=500) * df_util['每格口日处理量']
)
top5_combo = df_util.nlargest(5, '综合紧张度')
print(f"\n   【综合瓶颈 Top-5（产能+格口双重紧张）】")
for i, (_, row) in enumerate(top5_combo.iterrows()):
    print(f"   {i+1}. {row['分拣中心']:>8s}: 综合紧张度 {row['综合紧张度']:>8,.0f}, "
          f"产能利用率 {row['产能利用率(%)']:6.1f}%, "
          f"每格口 {row['每格口日处理量']:>8,.0f}件, "
          f"日均处理 {row['日均处理量(件)']:>10,.0f}件")

# ================================================================
#  问题3 相关参数
# ================================================================
print("\n" + "=" * 70)
print("【问题3：设备投资优化相关参数】")
print("=" * 70)

# --- 12. 附件表4设备参数 ---
print(f"\n12. 设备参数表:")
print(f"    {'设备':>6s}  {'格口数':>8s}  {'设计产能(件/天)':>16s}  {'成本(元)':>10s}  "
      f"{'折旧年限':>8s}  {'年折旧(元)':>10s}  {'每格口成本(元)':>14s}")
print(f"    {'-'*6}  {'-'*8}  {'-'*16}  {'-'*10}  {'-'*8}  {'-'*10}  {'-'*14}")

for _, row in df4.iterrows():
    annual_depr = row['设备成本'] / row['折旧年限']
    cost_per_slot = row['设备成本'] / row['格口数']
    print(f"    {row['设备编号']:>6s}  {row['格口数']:>8.0f}  {row['设计产能']:>16,}  "
          f"{row['设备成本']:>10,}  {row['折旧年限']:>8.0f}  {annual_depr:>10,.0f}  {cost_per_slot:>14,.0f}")

# --- 13. 人工成本 ---
labor_cost_per_slot_day = 90 / 5  # 18元/格口/天
labor_cost_per_slot_year = labor_cost_per_slot_day * 365
print(f"\n13. 人工成本:")
print(f"    每人每天工资: 90 元")
print(f"    每人每天处理格口: 5 个")
print(f"    人工每格口每天成本: {labor_cost_per_slot_day:.0f} 元/格口/天")
print(f"    人工每格口每年成本: {labor_cost_per_slot_year:,.0f} 元/格口/年")

# --- 14. 各设备日均折旧 vs 等效人工成本 ---
print(f"\n14. 设备日均折旧 vs 等效人工成本对比:")
print(f"    {'设备':>6s}  {'格口数':>8s}  {'日折旧(元)':>10s}  "
      f"{'等效人工日成本':>14s}  {'日折旧/人工比':>12s}  {'结论':>20s}")
print(f"    {'-'*6}  {'-'*8}  {'-'*10}  {'-'*14}  {'-'*12}  {'-'*20}")

for _, row in df4.iterrows():
    daily_depr = row['设备成本'] / (row['折旧年限'] * 365)
    equiv_labor_daily = labor_cost_per_slot_day * row['格口数']
    ratio = daily_depr / equiv_labor_daily
    conclusion = '设备更便宜' if ratio < 1 else '人工更便宜'
    print(f"    {row['设备编号']:>6s}  {row['格口数']:>8.0f}  {daily_depr:>10.1f}  "
          f"{equiv_labor_daily:>14,.0f}  {ratio:>12.3f}  {conclusion:>20s}")

# --- 15. 20%年增长后的货量 vs 当前产能缺口 ---
print(f"\n15. 20%年增长后的货量 vs 当前产能缺口:")

# 当前日均总货量
current_daily_vol = avg_daily_vol
# 一年后（货量增长20%）
growth_rate = 0.20
future_daily_vol = current_daily_vol * (1 + growth_rate)

print(f"    当前全网日均货量: {current_daily_vol:,.0f} 件/天")
print(f"    1年后日均货量 (+20%): {future_daily_vol:,.0f} 件/天")
print(f"    当前全网总日产能: {total_capacity:,} 件/天")
print(f"    当前产能缺口 (需求-产能): {current_daily_vol - total_capacity:,.0f} 件/天")
print(f"    1年后产能缺口: {future_daily_vol - total_capacity:,.0f} 件/天")

gap_ratio = (future_daily_vol - total_capacity) / total_capacity * 100
print(f"    产能缺口比例: {gap_ratio:.1f}% (正值=产能不足, 负值=产能有余)")

# 按中心级别的产能缺口分析
print(f"\n    各分拣中心产能缺口分析（排序前10）:")
center_gap = []
for center in center_daily_mean.index:
    if center in df3_indexed.index:
        current_vol = center_daily_mean[center]
        future_vol = current_vol * (1 + growth_rate)
        capacity = df3_indexed.loc[center, '日产能']
        slots = df3_indexed.loc[center, '格口数量']
        gap = future_vol - capacity
        center_gap.append({
            '分拣中心': center,
            '当前日均处理量': current_vol,
            '1年后日均处理量': future_vol,
            '日产能': capacity,
            '产能缺口': gap,
            '缺口比例(%)': gap / capacity * 100 if capacity > 0 else float('inf'),
            '格口数': slots,
        })

df_gap = pd.DataFrame(center_gap)
top_gap = df_gap.nlargest(10, '产能缺口')
print(f"    {'分拣中心':>10s}  {'当前日均':>10s}  {'1年后日均':>10s}  "
      f"{'日产能':>10s}  {'产能缺口':>10s}  {'缺口比例':>8s}")
print(f"    {'-'*10}  {'-'*10}  {'-'*10}  {'-'*10}  {'-'*10}  {'-'*8}")
for _, row in top_gap.iterrows():
    print(f"    {row['分拣中心']:>10s}  {row['当前日均处理量']:>10,.0f}  "
          f"{row['1年后日均处理量']:>10,.0f}  {row['日产能']:>10,}  "
          f"{row['产能缺口']:>10,.0f}  {row['缺口比例(%)']:>7.1f}%")

# 统计有多少中心产能不足
n_deficit = (df_gap['产能缺口'] > 0).sum()
n_surplus = (df_gap['产能缺口'] <= 0).sum()
n_neg_inf = (df_gap['产能缺口'] < -1e9).sum()  # 产能远大于需求
print(f"\n    产能不足的中心: {n_deficit} 个 (需投资新设备)")
print(f"    产能充足的中心: {n_surplus} 个")
print(f"    总产能缺口合计: {df_gap['产能缺口'].clip(lower=0).sum():,.0f} 件/天")

# 如果全部用人工补足缺口，需要多少人力
total_gap_positive = df_gap['产能缺口'].clip(lower=0).sum()
# 这里产能缺口是件/天，人工每人每天处理5个格口，每个格口处理能力需要根据设备类型折算
# 简化：假设每个格口平均处理能力 = 总产能/总格口
avg_capacity_per_slot = total_capacity / total_slots if total_slots > 0 else 0
print(f"    平均每格口处理能力: {avg_capacity_per_slot:.1f} 件/天")
if avg_capacity_per_slot > 0:
    slots_needed = total_gap_positive / avg_capacity_per_slot
    workers_needed = slots_needed / 5
    print(f"    缺口需补充格口数: {slots_needed:,.0f} 个")
    print(f"    全用人工需人数: {workers_needed:,.0f} 人 (每人5格口/天)")

# ================================================================
#  汇总输出
# ================================================================
print("\n" + "=" * 70)
print("【关键参数汇总表】")
print("=" * 70)

print(f"""
┌─────────────────────────────────────────────────────────────────────┐
│                     A题建模关键定量参数汇总                            │
├─────────────────────────────────────────────────────────────────────┤
│ 问题1：预测                                                          │
│   预测OD对数:         {n_predict_ods:>8,}                            │
│   预测值总数:         {n_predict_ods * 7:>8,} (7天×OD)               │
│   训练样本数:         {len(df_train):>8,}                          │
│   验证样本数:         {len(df_val):>8,}                          │
│   日均<10件的OD对:    {bucket_counts['<10']:>8,} ({bucket_counts['<10']/len(od_daily_mean)*100:5.1f}%) │
│   日均10-100件:       {bucket_counts['10-100']:>8,} ({bucket_counts['10-100']/len(od_daily_mean)*100:5.1f}%) │
│   日均100-1000件:     {bucket_counts['100-1000']:>8,} ({bucket_counts['100-1000']/len(od_daily_mean)*100:5.1f}%) │
│   日均>1000件:        {bucket_counts['>1000']:>8,} ({bucket_counts['>1000']/len(od_daily_mean)*100:5.1f}%) │
│   春节2月/非2月比:    {spring_ratio:.4f} ({spring_ratio*100:.1f}%)    │
│   Naive MAE:          {naive_mae:.1f} 件/天 (NMAE={nmae:.1f}%)       │
├─────────────────────────────────────────────────────────────────────┤
│ 问题2：集包优化                                                       │
│   优化变量规模:       {n_vars:>8,.0f}                                │
│   枚举空间上界:       {total_combinations:>12,}                    │
│   总格口资源:         {total_slots:>8,} 个                           │
│   总日产能:           {total_capacity:>8,} 件/天                    │
│   日均需求/产能比:    {capacity_ratio:>8.1f}%                         │
│   峰值需求/产能比:    {peak_ratio:.1f}%                               │
├─────────────────────────────────────────────────────────────────────┤
│ 问题3：设备投资                                                       │
│   人工每格口日成本:   {labor_cost_per_slot_day:.0f} 元/天            │
│   产能不足中心:       {n_deficit} 个                                  │
│   总产能缺口:         {total_gap_positive:,.0f} 件/天                 │
└─────────────────────────────────────────────────────────────────────┘
""")

print("计算完成！以上所有参数可直接用于论文\"问题分析\"章节的数据引用。")

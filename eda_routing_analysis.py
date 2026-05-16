"""
物流网络路由数据探索性数据分析脚本
用途：分析附件表1.csv中的走货路由数据
依赖：pandas, matplotlib, numpy, collections
运行：py.exe eda_routing_analysis.py
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 非交互式后端，用于脚本无头运行
import matplotlib.pyplot as plt
from collections import Counter, defaultdict
import os
import warnings
warnings.filterwarnings('ignore')

# ======================== 配置 ========================
DATA_PATH = r"c:\Users\www15\Desktop\26长三角数模\2026年第六届长三角高校数学建模竞赛赛题\2026长三角赛题A：物流网络集包规则及设备优化\附件表1.csv"
OUTPUT_DIR = r"c:\Users\www15\Desktop\26长三角数模\分析结果_分拣中心评级"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 中文字体设置
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ======================== 数据加载 ========================
print("=" * 60)
print("1. 数据加载")
print("=" * 60)
df = pd.read_csv(DATA_PATH, encoding='gbk')
# 标准化列名（去除可能的BOM和空格）
df.columns = df.columns.str.strip().str.replace('﻿', '')
col_origin, col_dest, col_route = df.columns.tolist()
print(f"列名: {col_origin}, {col_dest}, {col_route}")
print(f"总行数: {len(df):,}")
print(f"缺失值检查:\n{df.isnull().sum()}")

# ======================== 基本统计 ========================
print("\n" + "=" * 60)
print("2. 基本统计")
print("=" * 60)

# 解析路由中的节点列表
def parse_route(route_str):
    """解析路由字符串，返回分拣中心列表"""
    if pd.isna(route_str):
        return []
    return [x.strip() for x in str(route_str).split('-') if x.strip()]

# 路由节点数（跳数 = 节点数 - 1，节点数 = 经过的分拣中心数）
df['route_nodes'] = df[col_route].apply(parse_route)
df['route_length'] = df['route_nodes'].apply(len)  # 节点数（包含首尾）
df['route_hops'] = df['route_length'] - 1  # 跳数

# 首末流向对
df['od_pair'] = df[col_origin] + ' → ' + df[col_dest]

unique_origins = df[col_origin].nunique()
unique_destinations = df[col_dest].nunique()
unique_od_pairs = df['od_pair'].nunique()

# 所有出现过的分拣中心（合并始分拣、目的分拣、路由中间节点）
all_centers_in_routes = set()
for nodes in df['route_nodes']:
    all_centers_in_routes.update(nodes)
all_centers_separate = set(df[col_origin].unique()) | set(df[col_dest].unique())

print(f"总行数:                      {len(df):,}")
print(f"唯一始分拣中心数:             {unique_origins}")
print(f"唯一目的分拣中心数:           {unique_destinations}")
print(f"唯一首-末流向对数(OD pairs):  {unique_od_pairs:,}")
print(f"路由中出现的全部分拣中心数:   {len(all_centers_in_routes)}")
print(f"始+目的分拣中心并集:          {len(all_centers_separate)}")
print(f"始与目的中心交集数:           {len(set(df[col_origin].unique()) & set(df[col_dest].unique()))}")

# ======================== 路由长度分布 ========================
print("\n" + "=" * 60)
print("3. 路由长度（跳数）分布")
print("=" * 60)

hop_counts = df['route_hops'].value_counts().sort_index()
print("跳数分布:")
for hops, count in hop_counts.items():
    print(f"  {hops}跳: {count:,} 条 ({count/len(df)*100:.1f}%)")

print(f"\n最短跳数: {df['route_hops'].min()}")
print(f"最长跳数: {df['route_hops'].max()}")
print(f"平均跳数: {df['route_hops'].mean():.2f}")
print(f"中位跳数: {df['route_hops'].median():.0f}")
print(f"跳数标准差: {df['route_hops'].std():.2f}")

# 节点数分布
node_counts = df['route_length'].value_counts().sort_index()
print("\n节点数（经过的分拣中心数）分布:")
for nodes, count in node_counts.items():
    print(f"  {nodes}个节点: {count:,} 条 ({count/len(df)*100:.1f}%)")

# 绘制跳数分布直方图
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# 子图1：跳数分布柱状图
hop_vals = hop_counts.index.tolist()
hop_cnts = hop_counts.values.tolist()
colors = ['#4472C4'] * len(hop_vals)
axes[0].bar(hop_vals, hop_cnts, color=colors, edgecolor='white', linewidth=0.5)
axes[0].set_xlabel('跳数 (Hops)', fontsize=12)
axes[0].set_ylabel('路由数量', fontsize=12)
axes[0].set_title('路由跳数分布', fontsize=14, fontweight='bold')
for i, (h, c) in enumerate(zip(hop_vals, hop_cnts)):
    axes[0].text(h, c + max(hop_cnts)*0.01, f'{c:,}', ha='center', fontsize=8)

# 子图2：节点数分布柱状图
node_vals = node_counts.index.tolist()
node_cnts = node_counts.values.tolist()
axes[1].bar(node_vals, node_cnts, color='#ED7D31', edgecolor='white', linewidth=0.5)
axes[1].set_xlabel('节点数', fontsize=12)
axes[1].set_ylabel('路由数量', fontsize=12)
axes[1].set_title('路由节点数分布', fontsize=14, fontweight='bold')
for i, (n, c) in enumerate(zip(node_vals, node_cnts)):
    axes[1].text(n, c + max(node_cnts)*0.01, f'{c:,}', ha='center', fontsize=8)

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, '图1_路由长度分布.png'), dpi=150, bbox_inches='tight')
plt.close()
print("\n[图表已保存] 图1_路由长度分布.png")

# ======================== 网络拓扑特征 ========================
print("\n" + "=" * 60)
print("4. 网络拓扑特征")
print("=" * 60)

# 4a. 分拣中心在路由中的出现频次（作为任意节点）
center_freq = Counter()
for nodes in df['route_nodes']:
    # 每条路由中每个中心只计一次（避免同一条路由重复计数）
    center_freq.update(set(nodes))

center_freq_df = pd.DataFrame(center_freq.items(), columns=['分拣中心', '出现路由数'])
center_freq_df = center_freq_df.sort_values('出现路由数', ascending=False).reset_index(drop=True)

print(f"\n各分拣中心在路由中出现的频次统计:")
print(f"  均值: {center_freq_df['出现路由数'].mean():.1f}")
print(f"  中位数: {center_freq_df['出现路由数'].median():.0f}")
print(f"  最大值: {center_freq_df['出现路由数'].max()}")
print(f"  最小值: {center_freq_df['出现路由数'].min()}")
print(f"  标准差: {center_freq_df['出现路由数'].std():.1f}")
print(f"  出现>1000次的中心数: {(center_freq_df['出现路由数'] > 1000).sum()}")
print(f"  出现>5000次的中心数: {(center_freq_df['出现路由数'] > 5000).sum()}")

# 4b. 出度（作为始分拣的频率）
out_degree = df[col_origin].value_counts()
print(f"\n出度（作为始发中心）统计:")
print(f"  唯一始发中心数: {len(out_degree)}")
print(f"  平均出度: {out_degree.mean():.1f}")
print(f"  最大出度: {out_degree.max()}")
print(f"  最小出度: {out_degree.min()}")

# 4c. 入度（作为目的分拣的频率）
in_degree = df[col_dest].value_counts()
print(f"\n入度（作为目的中心）统计:")
print(f"  唯一目的中心数: {len(in_degree)}")
print(f"  平均入度: {in_degree.mean():.1f}")
print(f"  最大入度: {in_degree.max()}")
print(f"  最小入度: {in_degree.min()}")

# 4d. 最繁忙的10个分拣中心
print("\n最繁忙的10个分拣中心（按出现路由数排序）:")
print(f"{'排名':<6}{'中心':<12}{'出现路由数':<12}{'出度(始发)':<12}{'入度(目的)':<12}")
print("-" * 54)
for i, row in center_freq_df.head(10).iterrows():
    center = row['分拣中心']
    od = out_degree.get(center, 0)
    ind = in_degree.get(center, 0)
    print(f"{i+1:<6}{center:<12}{row['出现路由数']:<12}{od:<12}{ind:<12}")

# 绘制繁忙程度分布
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# 子图1：路由出现频次 Top30
top30 = center_freq_df.head(30)
axes[0, 0].barh(range(len(top30)), top30['出现路由数'].values, color='#4472C4', edgecolor='white')
axes[0, 0].set_yticks(range(len(top30)))
axes[0, 0].set_yticklabels(top30['分拣中心'].values, fontsize=7)
axes[0, 0].invert_yaxis()
axes[0, 0].set_xlabel('出现路由数', fontsize=11)
axes[0, 0].set_title('Top30 最繁忙分拣中心', fontsize=13, fontweight='bold')

# 子图2：出现频次分布（对数坐标）
freq_vals = center_freq_df['出现路由数'].values
axes[0, 1].hist(freq_vals, bins=50, color='#ED7D31', edgecolor='white', alpha=0.8)
axes[0, 1].set_yscale('log')
axes[0, 1].set_xlabel('出现路由数', fontsize=11)
axes[0, 1].set_ylabel('中心数量 (log)', fontsize=11)
axes[0, 1].set_title('分拣中心出现频次分布（对数y轴）', fontsize=13, fontweight='bold')

# 子图3：出度分布 Top30
out_top30 = out_degree.head(30)
axes[1, 0].barh(range(len(out_top30)), out_top30.values, color='#A5A5A5', edgecolor='white')
axes[1, 0].set_yticks(range(len(out_top30)))
axes[1, 0].set_yticklabels(out_top30.index, fontsize=7)
axes[1, 0].invert_yaxis()
axes[1, 0].set_xlabel('出度（作为始发中心）', fontsize=11)
axes[1, 0].set_title('Top30 始发中心（出度）', fontsize=13, fontweight='bold')

# 子图4：入度分布 Top30
in_top30 = in_degree.head(30)
axes[1, 1].barh(range(len(in_top30)), in_top30.values, color='#70AD47', edgecolor='white')
axes[1, 1].set_yticks(range(len(in_top30)))
axes[1, 1].set_yticklabels(in_top30.index, fontsize=7)
axes[1, 1].invert_yaxis()
axes[1, 1].set_xlabel('入度（作为目的中心）', fontsize=11)
axes[1, 1].set_title('Top30 目的中心（入度）', fontsize=13, fontweight='bold')

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, '图2_网络拓扑特征.png'), dpi=150, bbox_inches='tight')
plt.close()
print("[图表已保存] 图2_网络拓扑特征.png")

# ======================== 重复检查 ========================
print("\n" + "=" * 60)
print("5. 重复路由检查")
print("=" * 60)

# 完全重复行
total_rows = len(df)
unique_rows = len(df.drop_duplicates(subset=[col_origin, col_dest, col_route]))
dup_rows = total_rows - unique_rows
print(f"完全重复的行数（按三列）: {dup_rows:,} ({dup_rows/total_rows*100:.1f}%)")

# 按 OD pair + Route 去重
unique_od_route = df[[col_origin, col_dest, col_route]].drop_duplicates()
print(f"唯一(始,目,路由)组合数: {len(unique_od_route):,}")
print(f"重复的(始,目,路由)行数: {total_rows - len(unique_od_route):,}")

# 同一个OD pair有多少条不同的路由
od_route_count = df.groupby([col_origin, col_dest])[col_route].nunique()
multi_route_od = od_route_count[od_route_count > 1]
single_route_od = od_route_count[od_route_count == 1]
print(f"\nOD pair路由多样性:")
print(f"  唯一OD pair总数:         {len(od_route_count):,}")
print(f"  仅1条路由的OD pair:      {len(single_route_od):,}")
print(f"  有多条路由的OD pair:     {len(multi_route_od):,}")
if len(multi_route_od) > 0:
    print(f"  多路由OD中最多的路由数:  {multi_route_od.max()}")
    print(f"  多路由OD中平均路由数:    {multi_route_od.mean():.1f}")
    print(f"\n  多路由OD pair示例（前10个）:")
    for i, (idx, cnt) in enumerate(multi_route_od.head(10).items()):
        print(f"    {idx[0]} -> {idx[1]}: {cnt}条路由")

# 统计OD pair路由数目的分布
route_count_dist = od_route_count.value_counts().sort_index()
print(f"\n  OD pair拥有路由数目的分布:")
for k, v in route_count_dist.items():
    print(f"    {k}条路由: {v:,}个OD pair")

# ======================== 路由路径模式分析 ========================
print("\n" + "=" * 60)
print("6. 路由路径模式分析")
print("=" * 60)

# 6a. 第一个中转站（路由中第二个节点）分析
first_transit_counts = Counter()
for nodes in df['route_nodes']:
    if len(nodes) >= 2:
        first_transit_counts[nodes[1]] += 1

first_transit_df = pd.DataFrame(first_transit_counts.items(), columns=['中转站', '出现次数'])
first_transit_df = first_transit_df.sort_values('出现次数', ascending=False).reset_index(drop=True)
first_transit_df['占比%'] = first_transit_df['出现次数'] / len(df) * 100

print(f"\n第一个中转站（路由第二个节点）统计:")
print(f"  不同中转站数量: {len(first_transit_df)}")
print(f"  最常见的10个第一中转站:")
for i, row in first_transit_df.head(10).iterrows():
    print(f"    {row['中转站']}: {row['出现次数']:,}次 ({row['占比%']:.1f}%)")

# 6b. 第二个中转站（路由中第三个节点）
second_transit_counts = Counter()
for nodes in df['route_nodes']:
    if len(nodes) >= 3:
        second_transit_counts[nodes[2]] += 1

second_transit_df = pd.DataFrame(second_transit_counts.items(), columns=['中转站', '出现次数'])
second_transit_df = second_transit_df.sort_values('出现次数', ascending=False).reset_index(drop=True)
second_transit_df['占比%'] = second_transit_df['出现次数'] / len(df) * 100

print(f"\n第二个中转站（路由第三个节点）统计:")
print(f"  不同中转站数量: {len(second_transit_df)}")
print(f"  最常见的10个第二中转站:")
for i, row in second_transit_df.head(10).iterrows():
    print(f"    {row['中转站']}: {row['出现次数']:,}次 ({row['占比%']:.1f}%)")

# 6c. 路由模式分析：找出常见的前缀模式
# 看前两个节点的组合
prefix2_counts = Counter()
for nodes in df['route_nodes']:
    if len(nodes) >= 2:
        prefix2 = tuple(nodes[:2])
        prefix2_counts[prefix2] += 1

prefix2_df = pd.DataFrame(
    [(a, b, c) for (a, b), c in prefix2_counts.items()],
    columns=['第一站', '第二站', '出现次数']
).sort_values('出现次数', ascending=False).reset_index(drop=True)

print(f"\n路由前2跳模式分析:")
print(f"  不同前2跳模式数: {len(prefix2_df)}")
print(f"  最常见的10种前2跳模式:")
for i, row in prefix2_df.head(10).iterrows():
    pct = row['出现次数'] / len(df) * 100
    print(f"    {row['第一站']} -> {row['第二站']}: {row['出现次数']:,}次 ({pct:.1f}%)")

# 6d. 路由层级分析：哪些中心总是作为第一级中转
# 统计每个中心作为第一中转站的频率与其总频率的比例
print(f"\n层级特征分析 — Top15中心的中转角色:")
print(f"{'中心':<10}{'总出现':<10}{'作为始发':<10}{'作为目的':<10}{'作为首中转':<12}{'首中转占比%':<12}")
print("-" * 64)
for _, row in center_freq_df.head(15).iterrows():
    center = row['分拣中心']
    total = row['出现路由数']
    as_origin = out_degree.get(center, 0)
    as_dest = in_degree.get(center, 0)
    as_first_transit = first_transit_counts.get(center, 0)
    ratio = as_first_transit / total * 100 if total > 0 else 0
    print(f"{center:<10}{total:<10}{as_origin:<10}{as_dest:<10}{as_first_transit:<12}{ratio:<12.1f}")

# 6e. 自环检查（始分拣 == 目的分拣）
self_loops = df[df[col_origin] == df[col_dest]]
print(f"\n自环路由（始分拣 == 目的分拣）: {len(self_loops)} 条")
if len(self_loops) > 0:
    print(f"  自环示例:")
    for _, row in self_loops.head(5).iterrows():
        print(f"    {row[col_route]}")

# 6f. 多跳路由比例
print(f"\n路由类型分布:")
direct = (df['route_hops'] == 0).sum()
two_hop = (df['route_hops'] == 1).sum()
three_hop = (df['route_hops'] == 2).sum()
four_plus = (df['route_hops'] >= 3).sum()
print(f"  直达 (0跳/1节点): {direct:,} ({direct/len(df)*100:.1f}%)")
print(f"  一站中转 (1跳/2节点): {two_hop:,} ({two_hop/len(df)*100:.1f}%)")
print(f"  两站中转 (2跳/3节点): {three_hop:,} ({three_hop/len(df)*100:.1f}%)")
print(f"  三站及以上中转 (3+跳): {four_plus:,} ({four_plus/len(df)*100:.1f}%)")

# ======================== 图表3：路由模式可视化 ========================
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# 子图1：第一中转站 Top20
ft20 = first_transit_df.head(20)
axes[0, 0].barh(range(len(ft20)), ft20['出现次数'].values, color='#4472C4', edgecolor='white')
axes[0, 0].set_yticks(range(len(ft20)))
axes[0, 0].set_yticklabels(ft20['中转站'].values, fontsize=8)
axes[0, 0].invert_yaxis()
axes[0, 0].set_xlabel('出现次数', fontsize=11)
axes[0, 0].set_title('Top20 第一中转站（路由第二节点）', fontsize=13, fontweight='bold')

# 子图2：第二中转站 Top20
st20 = second_transit_df.head(20)
axes[0, 1].barh(range(len(st20)), st20['出现次数'].values, color='#ED7D31', edgecolor='white')
axes[0, 1].set_yticks(range(len(st20)))
axes[0, 1].set_yticklabels(st20['中转站'].values, fontsize=8)
axes[0, 1].invert_yaxis()
axes[0, 1].set_xlabel('出现次数', fontsize=11)
axes[0, 1].set_title('Top20 第二中转站（路由第三节点）', fontsize=13, fontweight='bold')

# 子图3：路由类型饼图
route_types = [direct, two_hop, three_hop, four_plus]
route_labels = ['直达\n(0跳)', '一站中转\n(1跳)', '两站中转\n(2跳)', '三站及以上\n(3+跳)']
route_colors = ['#4472C4', '#ED7D31', '#A5A5A5', '#FFC000']
wedges, texts, autotexts = axes[1, 0].pie(
    route_types, labels=route_labels, colors=route_colors,
    autopct='%1.1f%%', startangle=90, explode=(0, 0, 0, 0.05)
)
for t in autotexts:
    t.set_fontsize(9)
axes[1, 0].set_title('路由类型分布', fontsize=13, fontweight='bold')

# 子图4：OD pair路由数目分布
axes[1, 1].bar(route_count_dist.index, route_count_dist.values,
               color='#70AD47', edgecolor='white', linewidth=0.5)
axes[1, 1].set_xlabel('拥有路由数', fontsize=11)
axes[1, 1].set_ylabel('OD pair数量', fontsize=11)
axes[1, 1].set_title('每个OD pair拥有的路由数目分布', fontsize=13, fontweight='bold')
for k, v in route_count_dist.items():
    axes[1, 1].text(k, v + max(route_count_dist.values) * 0.01, f'{v:,}', ha='center', fontsize=8)

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, '图3_路由模式分析.png'), dpi=150, bbox_inches='tight')
plt.close()
print("[图表已保存] 图3_路由模式分析.png")

# ======================== 补充分析：中心共现关系 ========================
print("\n" + "=" * 60)
print("7. 中心共现关系（补充分析）")
print("=" * 60)

# 统计每个中心与哪些中心一起出现在路由中（作为中转伙伴）
# 只看前10个最繁忙中心
top_centers = center_freq_df.head(10)['分拣中心'].tolist()
print(f"Top10繁忙中心的共现关系（同路由中出现最多的伙伴）:")
for center in top_centers:
    co_centers = Counter()
    for nodes in df['route_nodes']:
        if center in nodes:
            for n in nodes:
                if n != center:
                    co_centers[n] += 1
    top_partners = co_centers.most_common(5)
    print(f"  {center}: {', '.join([f'{p}({c:,})' for p, c in top_partners])}")

# ======================== 保存统计数据 ========================
print("\n" + "=" * 60)
print("8. 保存统计数据")
print("=" * 60)

# 保存分拣中心频次表
center_freq_df.to_csv(os.path.join(OUTPUT_DIR, '分拣中心出现频次排名.csv'), index=False, encoding='gbk')
print(f"已保存: 分拣中心出现频次排名.csv ({len(center_freq_df)}条)")

# 保存第一中转站频次
first_transit_df.to_csv(os.path.join(OUTPUT_DIR, '第一中转站频次排名.csv'), index=False, encoding='gbk')
print(f"已保存: 第一中转站频次排名.csv ({len(first_transit_df)}条)")

# 保存OD pair路由多样性
od_route_summary = pd.DataFrame({
    '始分拣': od_route_count.index.get_level_values(0),
    '目的分拣': od_route_count.index.get_level_values(1),
    '路由数': od_route_count.values
}).sort_values('路由数', ascending=False)
od_route_summary.to_csv(os.path.join(OUTPUT_DIR, 'OD路由多样性.csv'), index=False, encoding='gbk')
print(f"已保存: OD路由多样性.csv ({len(od_route_summary)}条)")

# 保存汇总统计
with open(os.path.join(OUTPUT_DIR, '分析汇总统计.txt'), 'w', encoding='utf-8') as f:
    f.write("=" * 60 + "\n")
    f.write("物流网络路由数据 EDA 分析汇总\n")
    f.write("=" * 60 + "\n\n")
    f.write(f"数据行数: {len(df):,}\n")
    f.write(f"唯一始分拣中心: {unique_origins}\n")
    f.write(f"唯一目的分拣中心: {unique_destinations}\n")
    f.write(f"唯一OD pair: {unique_od_pairs:,}\n")
    f.write(f"路由中出现过的全部中心: {len(all_centers_in_routes)}\n")
    f.write(f"完全重复行: {dup_rows:,} ({dup_rows/total_rows*100:.1f}%)\n")
    f.write(f"\n路由跳数: 最短{df['route_hops'].min()}, 最长{df['route_hops'].max()}, "
            f"平均{df['route_hops'].mean():.2f}, 中位{df['route_hops'].median():.0f}\n")
    f.write(f"多路由OD pair数: {len(multi_route_od):,}\n")
    f.write(f"唯一路由OD pair数: {len(single_route_od):,}\n")
print(f"已保存: 分析汇总统计.txt")

print("\n" + "=" * 60)
print("分析完成！所有结果已保存到:")
print(f"  {OUTPUT_DIR}")
print("=" * 60)

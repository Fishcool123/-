"""
题目声称与实际数据的矛盾验证脚本
==================================
逐项检查赛题原文声称与附件数据之间的矛盾。
依赖: pandas, numpy, openpyxl
运行: py.exe verify_contradictions.py
"""

import os, sys, warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np

# ======================== 路径配置 ========================
BASE = r'c:\Users\www15\Desktop\26长三角数模\2026年第六届长三角高校数学建模竞赛赛题\2026长三角赛题A：物流网络集包规则及设备优化'
FILE1 = os.path.join(BASE, '附件表1.csv')
FILE2 = os.path.join(BASE, '附件表2.csv')
FILE3 = os.path.join(BASE, '附件表3.csv')
FILE4 = os.path.join(BASE, '附件表4.xlsx')

ENCODING = 'gbk'

# ======================== 加载数据 ========================
print("=" * 70)
print("加载数据文件...")

df1 = pd.read_csv(FILE1, encoding=ENCODING)
df1.columns = ['始分拣', '目的分拣', '走货路由']
print(f"附件表1: {len(df1):,} 行, 列: {list(df1.columns)}")

df2 = pd.read_csv(FILE2, encoding=ENCODING)
df2.columns = ['日期', '始分拣', '目的分拣', '货量']
df2['日期'] = pd.to_datetime(df2['日期'])
print(f"附件表2: {len(df2):,} 行, 列: {list(df2.columns)}")

df3 = pd.read_csv(FILE3, encoding=ENCODING)
df3.columns = ['分拣中心', '分拣设备类型', '人工建包成本', '机器建包成本']
print(f"附件表3: {len(df3):,} 行, 列: {list(df3.columns)}")

df4 = pd.read_excel(FILE4)
print(f"附件表4: {len(df4):,} 行, 列: {list(df4.columns)}")

print()

# ====================================================================
# 检查1: "92个分拣中心" vs 实际数量
# ====================================================================
print("=" * 70)
print("【检查1】\"92个分拣中心\" vs 实际数量")
print("=" * 70)

# 附件表1中的分拣中心（始分拣 + 目的分拣 的并集）
centers_t1_src = set(df1['始分拣'].unique())
centers_t1_dst = set(df1['目的分拣'].unique())
centers_t1_all = centers_t1_src | centers_t1_dst

# 附件表2中的分拣中心
centers_t2_src = set(df2['始分拣'].unique())
centers_t2_dst = set(df2['目的分拣'].unique())
centers_t2_all = centers_t2_src | centers_t2_dst

# 附件表3中的分拣中心
centers_t3 = set(df3['分拣中心'].unique())

print(f"附件表1: 始分拣 {len(centers_t1_src)} 个, 目的分拣 {len(centers_t1_dst)} 个, 并集 {len(centers_t1_all)} 个")
print(f"附件表2: 始分拣 {len(centers_t2_src)} 个, 目的分拣 {len(centers_t2_dst)} 个, 并集 {len(centers_t2_all)} 个")
print(f"附件表3: 分拣中心 {len(centers_t3)} 个")

print(f"\n题目声称: 92个分拣中心")

# 三表并集
all_centers = centers_t1_all | centers_t2_all | centers_t3
print(f"\n三表并集总数: {len(all_centers)}")

# 差异分析
print("\n--- 集合差异 ---")
only_in_t1 = centers_t1_all - centers_t2_all - centers_t3
only_in_t2 = centers_t2_all - centers_t1_all - centers_t3
only_in_t3 = centers_t3 - centers_t1_all - centers_t2_all
in_t1_t2_not_t3 = (centers_t1_all & centers_t2_all) - centers_t3
in_t1_t3_not_t2 = (centers_t1_all & centers_t3) - centers_t2_all
in_t2_t3_not_t1 = (centers_t2_all & centers_t3) - centers_t1_all
in_all_three = centers_t1_all & centers_t2_all & centers_t3

print(f"仅附件表1有: {len(only_in_t1)} 个 -> {sorted(only_in_t1)[:20]}{'...' if len(only_in_t1) > 20 else ''}")
print(f"仅附件表2有: {len(only_in_t2)} 个 -> {sorted(only_in_t2)[:20]}{'...' if len(only_in_t2) > 20 else ''}")
print(f"仅附件表3有: {len(only_in_t3)} 个 -> {sorted(only_in_t3)[:20]}{'...' if len(only_in_t3) > 20 else ''}")
print(f"表1∩表2但不在表3: {len(in_t1_t2_not_t3)} 个 -> {sorted(in_t1_t2_not_t3)[:20]}{'...' if len(in_t1_t2_not_t3) > 20 else ''}")
print(f"表1∩表3但不在表2: {len(in_t1_t3_not_t2)} 个")
print(f"表2∩表3但不在表1: {len(in_t2_t3_not_t1)} 个")
print(f"三表共有: {len(in_all_three)} 个")

# 附件表3的分拣中心编号范围
print(f"\n附件表3分拣中心编号: {sorted(centers_t3)}")
# 检查是否有编号超出92
max_center_num = max([int(c.replace('A', '').replace('分拣', '')) for c in all_centers])
print(f"最大分拣中心编号: A{max_center_num}")

# 编号连续性检查
all_nums = sorted([int(c.replace('A', '').replace('分拣', '')) for c in all_centers])
missing_nums = set(range(1, max_center_num + 1)) - set(all_nums)
if missing_nums:
    print(f"缺失的编号 (1~{max_center_num}): A{sorted(missing_nums)[:30]}{'...' if len(missing_nums) > 30 else ''}")
    print(f"共缺失 {len(missing_nums)} 个编号")


# ====================================================================
# 检查2: "走货路由唯一确定" vs 实际重复路由
# ====================================================================
print("\n" + "=" * 70)
print("【检查2】\"走货路由唯一确定\" vs 实际重复路由")
print("=" * 70)

# 检查：同一个(始分拣, 目的分拣)下是否有多条不同的路由？
od_routes = df1.groupby(['始分拣', '目的分拣'])['走货路由'].apply(lambda x: list(x.unique())).reset_index()
od_routes.columns = ['始分拣', '目的分拣', '路由列表']
od_routes['路由数'] = od_routes['路由列表'].apply(len)

multi_route = od_routes[od_routes['路由数'] > 1]
total_od_pairs = len(od_routes)

print(f"附件表1总行数: {len(df1):,}")
print(f"唯一OD对数量: {total_od_pairs:,}")
print(f"有多条不同路由的OD对: {len(multi_route):,}")

if len(multi_route) > 0:
    max_routes = multi_route['路由数'].max()
    print(f"最多路由数: {max_routes} 条")
    print(f"\n路由数分布:")
    print(multi_route['路由数'].value_counts().sort_index())

    print(f"\n前10个多路由OD对示例:")
    for i, (_, row) in enumerate(multi_route.head(10).iterrows()):
        print(f"  {row['始分拣']} -> {row['目的分拣']}: {len(row['路由列表'])}条路由")
        for j, r in enumerate(row['路由列表']):
            print(f"    路由{j+1}: {r}")
else:
    print("所有OD对的路由唯一。")

# 也要检查：完全重复的行（相同的 始分拣+目的分拣+路由）
dup_rows = df1.duplicated(subset=['始分拣', '目的分拣', '走货路由'], keep=False)
n_dup_rows = dup_rows.sum()
print(f"\n完全重复的行（始+目的+路由都相同）: {n_dup_rows:,} 行 ({n_dup_rows/len(df1)*100:.2f}%)")

# OD唯一但路由相同的行数
od_route_unique = df1.groupby(['始分拣', '目的分拣']).size()
multi_rows_same_route = (od_route_unique > 1).sum()
print(f"同一个OD对有多行（但路由可能相同也可能不同）的OD对数: {multi_rows_same_route}")


# ====================================================================
# 检查3: "历史6个月" vs 实际时间跨度和数据完整性
# ====================================================================
print("\n" + "=" * 70)
print("【检查3】\"历史6个月\" vs 实际时间跨度和数据完整性")
print("=" * 70)

date_min = df2['日期'].min()
date_max = df2['日期'].max()
n_days_span = (date_max - date_min).days + 1
n_unique_dates = df2['日期'].nunique()
n_months = (date_max.year - date_min.year) * 12 + (date_max.month - date_min.month) + 1

print(f"起止日期: {date_min.date()} ~ {date_max.date()}")
print(f"跨越天数: {n_days_span} 天")
print(f"实际有数据的天数: {n_unique_dates} 天")
print(f"跨越月数: {n_months} 个月")
print(f"题目声称: 6个月")

# 检查是否每个日期都有数据
full_date_range = pd.date_range(date_min, date_max, freq='D')
missing_dates = set(full_date_range) - set(df2['日期'].unique())
print(f"\n缺失的日期数: {len(missing_dates)} 天")
if len(missing_dates) > 0:
    print(f"缺失日期: {sorted(missing_dates)[:20]}{'...' if len(missing_dates) > 20 else ''}")

# 检查月份
months_in_data = sorted(df2['日期'].dt.to_period('M').unique())
print(f"\n有数据的月份: {[str(m) for m in months_in_data]}")

# 每天记录数
daily_counts = df2.groupby('日期').size()
print(f"\n每天记录数统计:")
print(f"  均值: {daily_counts.mean():.0f}  中位数: {daily_counts.median():.0f}")
print(f"  最小: {daily_counts.min()} ({daily_counts.idxmin().date()})")
print(f"  最大: {daily_counts.max()} ({daily_counts.idxmax().date()})")

# OD-日期矩阵完整性
n_od_pairs_t2 = df2.groupby(['始分拣', '目的分拣']).ngroups
print(f"\n附件表2中的唯一OD对数量: {n_od_pairs_t2:,}")
print(f"理论矩阵大小 (OD对 × 天数): {n_od_pairs_t2:,} × {n_unique_dates} = {n_od_pairs_t2 * n_unique_dates:,}")
print(f"实际数据行数: {len(df2):,}")
completeness = len(df2) / (n_od_pairs_t2 * n_unique_dates) * 100
print(f"矩阵填充率: {completeness:.2f}%")
print(f"稀疏度: {100 - completeness:.2f}%")

# 每个OD对的活跃天数分布
od_active_days = df2.groupby(['始分拣', '目的分拣'])['日期'].nunique()
print(f"\n每个OD对活跃天数:")
print(f"  均值: {od_active_days.mean():.1f} 天 / {n_unique_dates} 天")
print(f"  中位数: {od_active_days.median():.0f} 天")
print(f"  最小: {od_active_days.min()} 天")
print(f"  最大: {od_active_days.max()} 天")

# 按活跃天数分段
bins = [0, 1, 5, 10, 30, 60, 120, 200]
labels = ['1天', '2-5天', '6-10天', '11-30天', '31-60天', '61-120天', '121天+']
active_binned = pd.cut(od_active_days, bins=bins, labels=labels, right=True)
print(f"\n活跃天数分布:")
for lbl in labels:
    cnt = (active_binned == lbl).sum()
    pct = cnt / len(od_active_days) * 100
    print(f"  {lbl}: {cnt:>6} OD对 ({pct:5.1f}%)")


# ====================================================================
# 检查4: 附件表3列名歧义
# ====================================================================
print("\n" + "=" * 70)
print("【检查4】附件表3列名歧义: \"人工建包成本\"/\"机器建包成本\" 到底是成本还是产能?")
print("=" * 70)

print(f"附件表3列名: {list(df3.columns)}")
print(f"\n字段'人工建包成本' 数值分析:")
manual_col = df3['人工建包成本']
print(f"  范围: [{manual_col.min()}, {manual_col.max()}]")
print(f"  均值: {manual_col.mean():.1f}")
print(f"  中位数: {manual_col.median():.1f}")
print(f"  标准差: {manual_col.std():.1f}")

print(f"\n字段'机器建包成本' 数值分析:")
machine_col = df3['机器建包成本']
print(f"  范围: [{machine_col.min()}, {machine_col.max()}]")
print(f"  均值: {machine_col.mean():.1f}")
print(f"  中位数: {machine_col.median():.1f}")
print(f"  标准差: {machine_col.std():.1f}")

# 检查"机器建包成本"是否可能为0
zero_machine = (machine_col == 0).sum()
print(f"\n'机器建包成本'为0的行数: {zero_machine}")
if zero_machine > 0:
    print(f"  为0的分拣中心: {df3[df3['机器建包成本'] == 0]['分拣中心'].tolist()}")

# 与设备类型交叉分析
print(f"\n按设备类型分组统计:")
for eq_type in sorted(df3['分拣设备类型'].unique()):
    subset = df3[df3['分拣设备类型'] == eq_type]
    print(f"\n  设备类型 '{eq_type}' ({len(subset)}个中心):")
    print(f"    人工建包成本: [{subset['人工建包成本'].min()}, {subset['人工建包成本'].max()}], "
          f"均值={subset['人工建包成本'].mean():.0f}")
    print(f"    机器建包成本: [{subset['机器建包成本'].min()}, {subset['机器建包成本'].max()}], "
          f"均值={subset['机器建包成本'].mean():.0f}")

# 关键判断：看数值范围和实际含义
# 如果是"成本"，单位可能是元/件，数值应该在较小范围
# 如果是"产能"（每天可处理包裹量），数值应该较大
# 如果是"成本单价"，可能是元/件
# 如果是"成本总额"，可能是元/天

print(f"\n--- 含义推断 ---")
print(f"'人工建包成本'列: 范围 {manual_col.min()}~{manual_col.max()}")
if manual_col.max() > 500:
    print("  > 数值较大，像是'产能'（日处理包裹量上限），不像是'成本'")
    print("  > 题目描述说附件表3包含'成本和产能（一天可处理的包裹量上限）'")
    print("  > 推断：'人工建包成本'列实际上是【人工建包产能】，即人工每天可处理的包裹量上限")
else:
    print("  > 数值较小，像是'成本'")

if machine_col.max() > 50000:
    print(f"'机器建包成本'列: 范围 {machine_col.min()}~{machine_col.max()}")
    print("  > 数值非常大，像是'产能'（日处理包裹量上限），不像是'成本'")
    print("  > 推断：'机器建包成本'列实际上是【机器建包产能】，即机器每天可处理的包裹量上限")
else:
    print(f"'机器建包成本'列: 范围 {machine_col.min()}~{machine_col.max()}")
    print("  > 数值较小，像是'成本'")

# 检查题目中"ai"的定义位置
print(f"\n--- 关于ai（每格口最多处理包裹数）的定义 ---")
print("题目原文: '场地i每个格口最多可处理ai个包裹'")
print("> 附件表3中没有'格口数'或'ai'相关列")
print("> ai值不在附件表3中，可能在附件表4或需要在问题中自行定义")

# 读附件表4看看
print(f"\n附件表4列名: {list(df4.columns)}")
print(df4.to_string())


# ====================================================================
# 检查5: "人工集包最大流向数限制" 缺失阈值
# ====================================================================
print("\n" + "=" * 70)
print("【检查5】\"人工集包最大流向数限制\" 缺失阈值")
print("=" * 70)

print("题目原文: '人工集包受到最大集包流向数限制，即分拣中心所有处理的")
print("          人工建包流向数不超过某一阈值'")
print(f"\n附件表3列名: {list(df3.columns)}")
print("> 附件表3没有对应的阈值列")
print("> 不存在隐含的阈值信息（没有额外的数值列）")
print("> 该阈值需要参赛者自行设定，或题目期望通过模型推导")

# 检查分拣设备类型是否与阈值相关
print(f"\n分拣设备类型唯一值: {sorted(df3['分拣设备类型'].unique())}")
print(f"类型数量: {df3['分拣设备类型'].nunique()}")
print("> 设备类型可能是分拣设备类型，与人工集包阈值无关")


# ====================================================================
# 检查6: 附件表2与附件表1的OD对匹配
# ====================================================================
print("\n" + "=" * 70)
print("【检查6】附件表2与附件表1的OD对匹配")
print("=" * 70)

od_pairs_t1 = set(zip(df1['始分拣'], df1['目的分拣']))
od_pairs_t2 = set(zip(df2['始分拣'], df2['目的分拣']))

print(f"附件表1唯一OD对数: {len(od_pairs_t1):,}")
print(f"附件表2唯一OD对数: {len(od_pairs_t2):,}")

# 表2有但表1无
in_t2_not_t1 = od_pairs_t2 - od_pairs_t1
# 表1有但表2无
in_t1_not_t2 = od_pairs_t1 - od_pairs_t2
# 共有
common_od = od_pairs_t1 & od_pairs_t2

print(f"\nOD对匹配情况:")
print(f"  表1∩表2 (共有): {len(common_od):,}")
print(f"  表2有但表1无: {len(in_t2_not_t1):,}")

if len(in_t2_not_t1) > 0:
    # 统计这些无路由OD对的货量
    in_t2_not_t1_list = list(in_t2_not_t1)
    df2_orphan = df2[df2.apply(lambda r: (r['始分拣'], r['目的分拣']) in in_t2_not_t1, axis=1)]
    orphan_volume = df2_orphan['货量'].sum()
    total_volume = df2['货量'].sum()
    print(f"  这些无路由OD对的总货量: {orphan_volume:,.0f} (占全部货量 {orphan_volume/total_volume*100:.2f}%)")
    print(f"  涉及 {df2_orphan['始分拣'].nunique()} 个始分拣, {df2_orphan['目的分拣'].nunique()} 个目的分拣")
    print(f"  前20个无路由OD对:")
    orphan_stats = df2_orphan.groupby(['始分拣', '目的分拣'])['货量'].sum().sort_values(ascending=False)
    for (src, dst), vol in orphan_stats.head(20).items():
        print(f"    {src} -> {dst}: 总货量={vol:,.0f}")

print(f"\n  表1有但表2无: {len(in_t1_not_t2):,}")
if len(in_t1_not_t2) > 0:
    print(f"  前20个: {list(in_t1_not_t2)[:20]}")
    # 这些OD对有路由但没货量，可能是潜在路由但实际没发生

# 表2中OD对在表1有路由的比例
coverage = len(common_od) / len(od_pairs_t2) * 100
print(f"\n表2的OD对在表1中有路由的覆盖率: {coverage:.1f}%")

# ====================================================================
# 附加检查: 附件表1中的重复行问题
# ====================================================================
print("\n" + "=" * 70)
print("【附加检查】附件表1中重复行分析")
print("=" * 70)

# 完全去重后
df1_dedup = df1.drop_duplicates()
print(f"原始行数: {len(df1):,}")
print(f"完全去重后行数: {len(df1_dedup):,}")
print(f"重复行数: {len(df1) - len(df1_dedup):,}")

# 按(始分拣, 目的分拣)去重（保留第一条路由）
od_unique_routes = df1.groupby(['始分拣', '目的分拣']).first().reset_index()
print(f"按OD去重后的路由数: {len(od_unique_routes):,}")

# 分析路由格式
print(f"\n路由格式示例:")
for i in range(min(5, len(df1_dedup))):
    print(f"  {df1_dedup.iloc[i]['走货路由']}")

# 路由中最长/最短路径
routes = df1_dedup['走货路由'].str.split('-')
route_lens = routes.apply(len)
print(f"\n路由长度（节点数）分布:")
print(f"  最短: {route_lens.min()} 个节点")
print(f"  最长: {route_lens.max()} 个节点")
print(f"  均值: {route_lens.mean():.1f} 个节点")
print(route_lens.value_counts().sort_index())

# ====================================================================
# 总结评级
# ====================================================================
print("\n" + "=" * 70)
print("【总结评级】")
print("=" * 70)

findings = [
    ("检查1: 92个分拣中心",
     f"附件表1并集{len(centers_t1_all)}个, 表2并集{len(centers_t2_all)}个, 表3有{len(centers_t3)}个, "
     f"三表总并集{len(all_centers)}个. 并非正好92个. "
     f"三表集合不完全一致.",
     "重要" if len(all_centers) != 92 else "无矛盾"),

    ("检查2: 走货路由唯一性",
     f"有{len(multi_route)}个OD对存在多条不同路由, 最多{multi_route['路由数'].max() if len(multi_route) > 0 else 0}条. "
     f"完全重复行{n_dup_rows}行. 题目声称'唯一确定'被数据推翻.",
     "致命" if len(multi_route) > 0 else "无矛盾"),

    ("检查3: 历史6个月",
     f"实际跨度 {date_min.date()}~{date_max.date()}, 共{n_days_span}天({n_months}个月, {n_unique_dates}个有数据的天). "
     f"矩阵填充率仅{completeness:.2f}%. "
     f"{'可能少于6个月' if n_months < 6 else '可能多于6个月' if n_months > 6 else '恰好6个月跨度'}. "
     f"{'有缺失日期' if len(missing_dates) > 0 else '每天都有数据'}.",
     "重要" if n_months != 6 or completeness < 100 else "无矛盾"),

    ("检查4: 附件表3列名歧义",
     f"'人工建包成本'列范围[{manual_col.min()}, {manual_col.max()}], "
     f"'机器建包成本'列范围[{machine_col.min()}, {machine_col.max()}]. "
     f"数值量级表明这两列实际上是【产能（日处理包裹量上限）】而非成本. "
     f"列名极具误导性. 此外, 题目中'每个格口最多可处理ai个包裹'的ai在附件表3中没有定义.",
     "致命"),

    ("检查5: 人工流向数阈值缺失",
     "题目明确提到'人工建包流向数不超过某一阈值', 但附件表3中无此阈值列. "
     "参赛者需自行设定或从数据中推断, 增加了不确定性.",
     "重要"),

    ("检查6: 表2与表1的OD匹配",
     f"表2中{len(in_t2_not_t1)}个OD对在表1中没有路由 (覆盖率{coverage:.1f}%). "
     f"这些无路由OD对的货量占全部货量的{orphan_volume/total_volume*100:.2f}%.",
     "致命" if coverage < 90 else "重要" if coverage < 99 else "一般"),
]

for title, detail, severity in findings:
    print(f"\n{'='*60}")
    print(f"[{severity}] {title}")
    print(f"{'='*60}")
    print(detail)

print("\n" + "=" * 70)
print("验证完成。")

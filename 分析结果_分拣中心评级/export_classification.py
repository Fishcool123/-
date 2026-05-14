"""导出分拣中心评级分类的详细数据表"""
import os, csv
from collections import defaultdict, Counter
import numpy as np

base = r"C:\Users\www15\Desktop\26长三角数模\2026年第六届长三角高校数学建模竞赛赛题\2026长三角赛题A：物流网络集包规则及设备优化"

# ============================================================
# 复制 deep_network_analysis.py 中的计算逻辑
# ============================================================
routes = {}
with open(os.path.join(base, '附件表1.csv'), encoding='gbk') as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        src, dst, path = row
        nodes = path.split('-')
        routes[(src, dst)] = nodes

od_daily = {}
with open(os.path.join(base, '附件表2.csv'), encoding='gbk') as f:
    reader = csv.reader(f)
    next(reader)
    total_days = 161
    for row in reader:
        date, src, dst, vol = row
        key = (src, dst)
        od_daily[key] = od_daily.get(key, 0) + float(vol) / total_days

center_info = {}
with open(os.path.join(base, '附件表3.csv'), encoding='gbk') as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        name, equip, slots, cap = row
        center_info[name] = {'equip': equip, 'slots': int(slots), 'cap': int(cap)}

# 构建有向图
all_nodes = set()
edges = defaultdict(set)
rev_edges = defaultdict(set)

for (src, dst), nodes in routes.items():
    for node in nodes:
        all_nodes.add(node)
    for i in range(len(nodes) - 1):
        edges[nodes[i]].add(nodes[i+1])
        rev_edges[nodes[i+1]].add(nodes[i])

all_nodes = sorted(all_nodes)

# 计算各指标
metrics = {}
for node in all_nodes:
    m = {}
    as_src = 0; as_dst = 0; as_mid = 0
    depths = []
    next_hops_in_routes = Counter()
    prev_hops_in_routes = Counter()

    for (src, dst), nodes in routes.items():
        if node not in nodes:
            continue
        idx = nodes.index(node)
        L = len(nodes)
        depths.append(idx)
        if idx == 0:
            as_src += 1
        elif idx == L - 1:
            as_dst += 1
        else:
            as_mid += 1
        if idx < L - 1:
            next_hops_in_routes[nodes[idx+1]] += 1
        if idx > 0:
            prev_hops_in_routes[nodes[idx-1]] += 1

    total_appear = as_src + as_dst + as_mid
    m['total'] = total_appear
    m['as_src'] = as_src; m['as_dst'] = as_dst; m['as_mid'] = as_mid
    m['src_ratio'] = as_src / total_appear if total_appear > 0 else 0
    m['dst_ratio'] = as_dst / total_appear if total_appear > 0 else 0
    m['mid_ratio'] = as_mid / total_appear if total_appear > 0 else 0
    m['avg_depth'] = np.mean(depths) if depths else 0
    m['min_depth'] = min(depths) if depths else 0
    m['max_depth'] = max(depths) if depths else 0
    m['n_upstream'] = len(rev_edges[node])
    m['n_downstream'] = len(edges[node])
    m['total_connections'] = m['n_upstream'] + m['n_downstream']

    upstream_counts = list(prev_hops_in_routes.values())
    if upstream_counts:
        m['upstream_concentration'] = max(upstream_counts) / sum(upstream_counts)
        m['top_upstream'] = max(prev_hops_in_routes, key=prev_hops_in_routes.get)
    else:
        m['upstream_concentration'] = 0
        m['top_upstream'] = '-'

    downstream_counts = list(next_hops_in_routes.values())
    if downstream_counts:
        m['n_effective_downstream'] = len([c for c in downstream_counts if c > 1])
        m['top_downstream'] = max(next_hops_in_routes, key=next_hops_in_routes.get)
    else:
        m['n_effective_downstream'] = 0
        m['top_downstream'] = '-'

    vol_in = 0.0; vol_out = 0.0; vol_through = 0.0
    for (src, dst), nodes in routes.items():
        if node not in nodes:
            continue
        daily_vol = od_daily.get((src, dst), 0)
        if daily_vol > 0:
            vol_through += daily_vol
            idx = nodes.index(node)
            if idx == 0:
                vol_out += daily_vol
            if idx == len(nodes) - 1:
                vol_in += daily_vol

    m['vol_in'] = vol_in; m['vol_out'] = vol_out; m['vol_through'] = vol_through

    m['n_od_pairs'] = len([1 for (s,d), nodes in routes.items() if node in nodes])
    m['od_coverage'] = m['n_od_pairs'] / len(routes) if routes else 0

    if node in center_info:
        m['equip'] = center_info[node]['equip']
        m['slots'] = center_info[node]['slots']
        m['capacity'] = center_info[node]['cap']
    else:
        m['equip'] = '未知'
        m['slots'] = 0
        m['capacity'] = 0

    metrics[node] = m

# 计算综合分
def normalize_to_100(series_dict):
    values = list(series_dict.values())
    vmin, vmax = min(values), max(values)
    if vmax == vmin:
        return {k: 50 for k in series_dict}
    return {k: 100 * (v - vmin) / (vmax - vmin) for k, v in series_dict.items()}

n_od_norm = normalize_to_100({n: m['n_od_pairs'] for n, m in metrics.items()})
mid_norm = normalize_to_100({n: m['mid_ratio'] for n, m in metrics.items()})
conn_norm = normalize_to_100({n: m['total_connections'] for n, m in metrics.items()})
vol_norm = normalize_to_100({n: np.log1p(m['vol_through']) for n, m in metrics.items()})
src_norm = normalize_to_100({n: m['src_ratio'] for n, m in metrics.items()})
dst_norm = normalize_to_100({n: m['dst_ratio'] for n, m in metrics.items()})

struct_norm = normalize_to_100({n: m['n_od_pairs'] * m['mid_ratio'] for n, m in metrics.items()})

shallow_deep_norm = normalize_to_100({
    n: min(m['src_ratio'], m['mid_ratio']) * 100
    for n, m in metrics.items()
})

scores = {}
for node in all_nodes:
    hub_score = 0.30 * n_od_norm[node] + 0.30 * mid_norm[node] + \
                0.20 * struct_norm[node] + 0.20 * conn_norm[node]
    vol_score = vol_norm[node]
    influence_score = 0.40 * n_od_norm[node] + 0.30 * conn_norm[node] + \
                      0.30 * shallow_deep_norm[node]
    composite = 0.35 * hub_score + 0.25 * vol_score + 0.25 * influence_score + \
                0.10 * src_norm[node] + 0.05 * dst_norm[node]
    scores[node] = {'hub': hub_score, 'volume': vol_score,
                    'influence': influence_score, 'composite': composite}

# 等级
def get_tier(score):
    if score >= 60: return 'S'
    elif score >= 45: return 'A'
    elif score >= 30: return 'B'
    elif score >= 18: return 'C'
    else: return 'D'

# 角色倾向
def get_role(m):
    if m['src_ratio'] > 0.5: return '始发型'
    elif m['dst_ratio'] > 0.5: return '末端型'
    elif m['mid_ratio'] > 0.6: return '枢纽型'
    else: return '混合型'

# ============================================================
# 导出 CSV 1: 全部指标
# ============================================================
output_dir = r"C:\Users\www15\Desktop\26长三角数模"
csv_path = os.path.join(output_dir, '分拣中心评级分类表.csv')

# 按综合分排序
sorted_by_score = sorted(all_nodes,
                         key=lambda n: scores[n]['composite'],
                         reverse=True)

with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([
        '排名', '分拣中心', '等级', '综合分', '枢纽度', '流量度', '影响力',
        '总出现次数', '作为起点', '作为中转', '作为终点',
        '起点占比', '中转占比', '终点占比',
        '平均深度', '最小深度', '最大深度',
        '上游连接数', '下游连接数', '总连接数',
        '上游集中度', '最大上游站', '有效下游方向数', '最大下游站',
        '日均流入货量', '日均流出货量', '日均经过货量',
        'OD覆盖数', 'OD覆盖率',
        '现有设备', '格口数量', '产能上限',
        '角色倾向'
    ])

    for rank, node in enumerate(sorted_by_score, 1):
        m = metrics[node]
        sc = scores[node]
        tier = get_tier(sc['composite'])
        role = get_role(m)
        writer.writerow([
            rank, node, tier,
            round(sc['composite'], 1), round(sc['hub'], 1),
            round(sc['volume'], 1), round(sc['influence'], 1),
            m['total'], m['as_src'], m['as_mid'], m['as_dst'],
            f"{m['src_ratio']:.1%}", f"{m['mid_ratio']:.1%}", f"{m['dst_ratio']:.1%}",
            round(m['avg_depth'], 2), m['min_depth'], m['max_depth'],
            m['n_upstream'], m['n_downstream'], m['total_connections'],
            f"{m['upstream_concentration']:.1%}", m['top_upstream'],
            m['n_effective_downstream'], m['top_downstream'],
            round(m['vol_in'], 0), round(m['vol_out'], 0), round(m['vol_through'], 0),
            m['n_od_pairs'], f"{m['od_coverage']:.2%}",
            m['equip'], m['slots'], m['capacity'],
            role
        ])

# ============================================================
# 导出 CSV 2: 等级汇总表
# ============================================================
summary_path = os.path.join(output_dir, '分拣中心等级汇总.csv')
with open(summary_path, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['等级', '数量', '分拣中心列表'])
    for tier in ['S', 'A', 'B', 'C', 'D']:
        nodes_in_tier = [n for n in sorted_by_score
                        if get_tier(scores[n]['composite']) == tier]
        writer.writerow([tier, len(nodes_in_tier),
                        ', '.join(nodes_in_tier)])

# ============================================================
# 导出 CSV 3: 按等级分组的简化信息（适合快速查阅）
# ============================================================
detail_path = os.path.join(output_dir, '分拣中心分级明细.csv')
with open(detail_path, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([
        '等级', '排名', '分拣中心', '综合分', '枢纽度', '流量度',
        '出现次数', '起点', '中转', '终点', '中转占比', '平均深度',
        '上游', '下游', '日均经过货量', 'OD覆盖数',
        '现有设备', '格口', '产能', '角色倾向'
    ])
    for rank, node in enumerate(sorted_by_score, 1):
        m = metrics[node]
        sc = scores[node]
        tier = get_tier(sc['composite'])
        role = get_role(m)
        writer.writerow([
            tier, rank, node,
            round(sc['composite'], 1), round(sc['hub'], 1), round(sc['volume'], 1),
            m['total'], m['as_src'], m['as_mid'], m['as_dst'],
            f"{m['mid_ratio']:.1%}", round(m['avg_depth'], 2),
            m['n_upstream'], m['n_downstream'],
            round(m['vol_through'], 0), m['n_od_pairs'],
            m['equip'], m['slots'], m['capacity'],
            role
        ])

# ============================================================
# 导出 CSV 4: 货流方向表
# ============================================================
flow_path = os.path.join(output_dir, '分拣中心货流方向.csv')
with open(flow_path, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([
        '分拣中心', '等级', '日均流入', '日均流出', '净流量(出-入)',
        '日均经过总量', '流向类型'
    ])
    for node in sorted_by_score:
        m = metrics[node]
        tier = get_tier(scores[node]['composite'])
        net = m['vol_out'] - m['vol_in']
        if m['vol_out'] > m['vol_in'] * 1.5:
            flow_type = '净发件型'
        elif m['vol_in'] > m['vol_out'] * 1.5:
            flow_type = '净收件型'
        else:
            flow_type = '双向平衡型'
        writer.writerow([
            node, tier,
            round(m['vol_in'], 0), round(m['vol_out'], 0), round(net, 0),
            round(m['vol_through'], 0), flow_type
        ])

print(f"已导出 4 个文件到 {output_dir}:")
print(f"  1. 分拣中心评级分类表.csv  — 93个分拣中心全部指标（29列）")
print(f"  2. 分拣中心等级汇总.csv     — 各等级统计和列表")
print(f"  3. 分拣中心分级明细.csv     — 按等级分组的简化信息")
print(f"  4. 分拣中心货流方向.csv     — 出入货量和流向类型")

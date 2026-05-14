"""深度网络分析：92个分拣中心评级分类"""
import os, csv
from collections import defaultdict, Counter
import numpy as np

base = r"C:\Users\www15\Desktop\26长三角数模\2026年第六届长三角高校数学建模竞赛赛题\2026长三角赛题A：物流网络集包规则及设备优化"

# ============================================================
# 1. 数据读取
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

# 分拣中心设备信息
center_info = {}
with open(os.path.join(base, '附件表3.csv'), encoding='gbk') as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        name, equip, slots, cap = row
        center_info[name] = {
            'equip': equip, 'slots': int(slots), 'cap': int(cap)
        }

# ============================================================
# 2. 构建有向图
# ============================================================
all_nodes = set()
edges = defaultdict(set)      # node -> set of next nodes
rev_edges = defaultdict(set)  # node -> set of prev nodes
node_routes = defaultdict(list)  # node -> list of (src,dst,nodes)
od_routes_map = {}

for (src, dst), nodes in routes.items():
    for node in nodes:
        all_nodes.add(node)
        node_routes[node].append((src, dst, nodes))
    od_routes_map[(src, dst)] = nodes
    for i in range(len(nodes) - 1):
        edges[nodes[i]].add(nodes[i+1])
        rev_edges[nodes[i+1]].add(nodes[i])

all_nodes = sorted(all_nodes)

# ============================================================
# 3. 多维度指标计算
# ============================================================
metrics = {}

for node in all_nodes:
    m = {}

    # --- 3.1 路由角色统计 ---
    as_src = 0; as_dst = 0; as_mid = 0
    depths = []
    path_lens = []
    next_hops_in_routes = Counter()  # 该节点在路由中后续的下一站分布
    prev_hops_in_routes = Counter()

    for (src, dst), nodes in routes.items():
        if node not in nodes:
            continue
        idx = nodes.index(node)
        L = len(nodes)
        depths.append(idx)
        path_lens.append(L)
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
    m['as_src'] = as_src
    m['as_dst'] = as_dst
    m['as_mid'] = as_mid
    m['src_ratio'] = as_src / total_appear if total_appear > 0 else 0
    m['dst_ratio'] = as_dst / total_appear if total_appear > 0 else 0
    m['mid_ratio'] = as_mid / total_appear if total_appear > 0 else 0

    # --- 3.2 深度指标 ---
    m['avg_depth'] = np.mean(depths) if depths else 0
    m['min_depth'] = min(depths) if depths else 0
    m['max_depth'] = max(depths) if depths else 0
    m['avg_path_len'] = np.mean(path_lens) if path_lens else 0

    # 深度分布：浅层(0-1)、中层(1-2)、深层(2+)
    shallow = sum(1 for d in depths if d <= 1)
    mid_layer = sum(1 for d in depths if 1 < d <= 2)
    deep = sum(1 for d in depths if d > 2)
    m['shallow_ratio'] = shallow / len(depths) if depths else 0
    m['mid_layer_ratio'] = mid_layer / len(depths) if depths else 0
    m['deep_ratio'] = deep / len(depths) if depths else 0

    # --- 3.3 连通性指标 ---
    m['n_upstream'] = len(rev_edges[node])
    m['n_downstream'] = len(edges[node])
    m['total_connections'] = m['n_upstream'] + m['n_downstream']

    # 上游集中度：上游节点的分布是否集中
    upstream_counts = list(prev_hops_in_routes.values())
    if upstream_counts:
        top1_up = max(upstream_counts)
        m['upstream_concentration'] = top1_up / sum(upstream_counts)
    else:
        m['upstream_concentration'] = 0

    # downstream diversity: 下游是否分散
    downstream_counts = list(next_hops_in_routes.values())
    if downstream_counts:
        # 熵：越高越分散
        total_d = sum(downstream_counts)
        entropy = -sum((c/total_d) * np.log(c/total_d) for c in downstream_counts)
        m['downstream_entropy'] = entropy
        m['max_downstream_flow'] = max(downstream_counts)
        m['n_effective_downstream'] = len([c for c in downstream_counts if c > 1])
    else:
        m['downstream_entropy'] = 0
        m['max_downstream_flow'] = 0
        m['n_effective_downstream'] = 0

    # --- 3.4 货量指标 ---
    vol_in = 0.0   # 该站作为目的（流入）
    vol_out = 0.0  # 该站作为始发（流出）
    vol_through = 0.0  # 经过该站的货量（估算：途经路由的OD货量之和）

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

    m['vol_in'] = vol_in
    m['vol_out'] = vol_out
    m['vol_through'] = vol_through
    m['vol_net_flow'] = vol_out - vol_in  # 正=净发件, 负=净收件

    # --- 3.5 网络重要性 ---
    # 介数中心性近似：该站出现在多少OD对的路由中
    m['n_od_pairs'] = len(node_routes[node])
    m['od_coverage'] = m['n_od_pairs'] / len(routes) if routes else 0

    # 如果去掉这个站，影响多少OD对？（结构洞指数近似）
    m['structural_importance'] = m['n_od_pairs'] * m['mid_ratio']

    # --- 3.6 设备信息 ---
    if node in center_info:
        m['equip'] = center_info[node]['equip']
        m['slots'] = center_info[node]['slots']
        m['capacity'] = center_info[node]['cap']
    else:
        m['equip'] = '未知'
        m['slots'] = 0
        m['capacity'] = 0

    # --- 3.7 极端路由 ---
    m['max_route_depth'] = max(path_lens) if path_lens else 0

    metrics[node] = m

# ============================================================
# 4. 综合评分与分类
# ============================================================
# 对各指标归一化到 [0,100]
def normalize_to_100(series_dict):
    values = list(series_dict.values())
    vmin, vmax = min(values), max(values)
    if vmax == vmin:
        return {k: 50 for k in series_dict}
    return {k: 100 * (v - vmin) / (vmax - vmin) for k, v in series_dict.items()}

# 计算各维度得分
scores = {}

# 4.1 枢纽度 (Hub Score): 基于出现频率、中介占比、OD覆盖
n_od_norm = normalize_to_100({n: m['n_od_pairs'] for n, m in metrics.items()})
mid_norm = normalize_to_100({n: m['mid_ratio'] for n, m in metrics.items()})
struct_norm = normalize_to_100({n: m['structural_importance'] for n, m in metrics.items()})
conn_norm = normalize_to_100({n: m['total_connections'] for n, m in metrics.items()})

# 4.2 流量度 (Volume Score): 基于经过货量、日均出入
vol_norm = normalize_to_100({n: np.log1p(m['vol_through']) for n, m in metrics.items()})

# 4.3 影响力 (Influence Score): 介数中心性+连边+深度
depth_divers_norm = normalize_to_100({
    n: m['shallow_ratio'] * m['deep_ratio'] * 100  # 横跨深浅层的站
    for n, m in metrics.items()
})

# 4.4 始发性 (Source Score)
src_norm = normalize_to_100({n: m['src_ratio'] for n, m in metrics.items()})

# 4.5 末端性 (Terminal Score)
dst_norm = normalize_to_100({n: m['dst_ratio'] for n, m in metrics.items()})

for node in all_nodes:
    # 综合枢纽分
    hub_score = 0.30 * n_od_norm[node] + 0.30 * mid_norm[node] + \
                0.20 * struct_norm[node] + 0.20 * conn_norm[node]

    # 流量分
    vol_score = vol_norm[node]

    # 影响力分
    influence_score = 0.40 * n_od_norm[node] + 0.30 * conn_norm[node] + \
                      0.30 * depth_divers_norm[node]

    # 综合分
    composite = 0.35 * hub_score + 0.25 * vol_score + 0.25 * influence_score + \
                0.10 * src_norm[node] + 0.05 * dst_norm[node]

    scores[node] = {
        'hub': hub_score,
        'volume': vol_score,
        'influence': influence_score,
        'source': src_norm[node],
        'terminal': dst_norm[node],
        'composite': composite,
    }

# ============================================================
# 5. 等级划分
# ============================================================
composites = {n: s['composite'] for n, s in scores.items()}
sorted_nodes = sorted(composites.items(), key=lambda x: -x[1])

# 按综合分划分等级
def assign_tier(nodes_with_scores):
    tiers = []
    for i, (n, s) in enumerate(nodes_with_scores):
        if s >= 60:
            tier = 'S'   # 超级枢纽
        elif s >= 45:
            tier = 'A'   # 一级枢纽
        elif s >= 30:
            tier = 'B'   # 二级枢纽/重要节点
        elif s >= 18:
            tier = 'C'   # 普通中转站
        else:
            tier = 'D'   # 边缘节点
        tiers.append((n, s, tier))
    return tiers

tiered = assign_tier(sorted_nodes)

# ============================================================
# 6. 输出报告
# ============================================================
with open('center_classification.txt', 'w', encoding='utf-8') as out:
    def p(*args):
        print(*args)
        print(*args, file=out)

    p("=" * 90)
    p("92个分拣中心综合评级分类报告")
    p("=" * 90)

    p("\n评分维度说明：")
    p("  枢纽度: 出现在多少路由 + 中转占比 + 结构重要性 + 连接数")
    p("  流量度: 经过该站的日均货量（对数归一化）")
    p("  影响力: OD覆盖 + 连接数 + 横跨浅深层的能力")
    p("  始发性: 作为路由起点的比例")
    p("  末端性: 作为路由终点的比例")
    p("  综合分: 枢纽度35% + 流量25% + 影响力25% + 始发10% + 末端5%")

    # --- S级 ---
    p("\n" + "━" * 90)
    p("【S 级】超级枢纽 — 网络核心，不可替代的中转节点")
    p("━" * 90)
    s_tier = [(n, s) for n, s, t in tiered if t == 'S']
    p(f"{'站名':<10} {'综合分':>6} {'枢纽度':>6} {'流量度':>6} {'影响力':>6} "
      f"{'出现':>5} {'始发':>5} {'中转':>5} {'终点':>5} "
      f"{'上游':>4} {'下游':>4} {'日均流量':>12} {'设备':>8} {'格口':>5}")
    p("-" * 90)
    for n, s in s_tier:
        m = metrics[n]
        sc = scores[n]
        p(f"{n:<10} {sc['composite']:>6.1f} {sc['hub']:>6.1f} "
          f"{sc['volume']:>6.1f} {sc['influence']:>6.1f} "
          f"{m['total']:>5} {m['as_src']:>5} {m['as_mid']:>5} {m['as_dst']:>5} "
          f"{m['n_upstream']:>4} {m['n_downstream']:>4} "
          f"{m['vol_through']:>12,.0f} {m['equip']:<8} {m['slots']:>5}")

    # --- A级 ---
    p("\n" + "━" * 90)
    p("【A 级】一级枢纽 — 骨干中转节点，承载大量区域间货流")
    p("━" * 90)
    a_tier = [(n, s) for n, s, t in tiered if t == 'A']
    p(f"{'站名':<10} {'综合分':>6} {'枢纽度':>6} {'流量度':>6} {'影响力':>6} "
      f"{'出现':>5} {'始发':>5} {'中转':>5} {'终点':>5} "
      f"{'上游':>4} {'下游':>4} {'日均流量':>12} {'设备':>8} {'格口':>5}")
    p("-" * 90)
    for n, s in a_tier:
        m = metrics[n]
        sc = scores[n]
        p(f"{n:<10} {sc['composite']:>6.1f} {sc['hub']:>6.1f} "
          f"{sc['volume']:>6.1f} {sc['influence']:>6.1f} "
          f"{m['total']:>5} {m['as_src']:>5} {m['as_mid']:>5} {m['as_dst']:>5} "
          f"{m['n_upstream']:>4} {m['n_downstream']:>4} "
          f"{m['vol_through']:>12,.0f} {m['equip']:<8} {m['slots']:>5}")

    # --- B级 ---
    p("\n" + "━" * 90)
    p("【B 级】二级枢纽/重要节点 — 区域性中转，连接枢纽与末端")
    p("━" * 90)
    b_tier = [(n, s) for n, s, t in tiered if t == 'B']
    p(f"{'站名':<10} {'综合分':>6} {'枢纽度':>6} {'流量度':>6} {'影响力':>6} "
      f"{'出现':>5} {'始发':>5} {'中转':>5} {'终点':>5} "
      f"{'上游':>4} {'下游':>4} {'日均流量':>12} {'设备':>8} {'格口':>5} {'角色倾向':>12}")
    p("-" * 90)
    for n, s in b_tier:
        m = metrics[n]
        sc = scores[n]
        # 角色判定
        if m['src_ratio'] > 0.5:
            role = '偏始发'
        elif m['dst_ratio'] > 0.5:
            role = '偏末端'
        elif m['mid_ratio'] > 0.6:
            role = '偏中转'
        else:
            role = '混合'
        p(f"{n:<10} {sc['composite']:>6.1f} {sc['hub']:>6.1f} "
          f"{sc['volume']:>6.1f} {sc['influence']:>6.1f} "
          f"{m['total']:>5} {m['as_src']:>5} {m['as_mid']:>5} {m['as_dst']:>5} "
          f"{m['n_upstream']:>4} {m['n_downstream']:>4} "
          f"{m['vol_through']:>12,.0f} {m['equip']:<8} {m['slots']:>5} {role:<12}")

    # --- C级 ---
    p("\n" + "━" * 90)
    p("【C 级】普通中转站 — 局部网络节点，承担特定方向的货流")
    p("━" * 90)
    c_tier = [(n, s) for n, s, t in tiered if t == 'C']
    p(f"{'站名':<10} {'综合分':>6} {'枢纽度':>6} {'流量度':>6} {'始发性':>6} "
      f"{'出现':>5} {'始发':>5} {'中转':>5} {'终点':>5} {'角色倾向':>12}")
    p("-" * 90)
    for n, s in c_tier:
        m = metrics[n]
        sc = scores[n]
        if m['src_ratio'] > 0.5:
            role = '偏始发'
        elif m['dst_ratio'] > 0.5:
            role = '偏末端'
        elif m['mid_ratio'] > 0.5:
            role = '偏中转'
        else:
            role = '混合'
        p(f"{n:<10} {sc['composite']:>6.1f} {sc['hub']:>6.1f} "
          f"{sc['volume']:>6.1f} {sc['source']:>6.1f} "
          f"{m['total']:>5} {m['as_src']:>5} {m['as_mid']:>5} {m['as_dst']:>5} {role:<12}")

    # --- D级 ---
    p("\n" + "━" * 90)
    p("【D 级】边缘节点 — 参与路由少，多为特定路线的起点或终点")
    p("━" * 90)
    d_tier = [(n, s) for n, s, t in tiered if t == 'D']
    p(f"{'站名':<10} {'综合分':>6} {'出现':>5} {'始发':>5} {'终点':>5} {'角色倾向':<12}")
    p("-" * 90)
    for n, s in d_tier:
        m = metrics[n]
        if m['src_ratio'] > 0.5:
            role = '偏始发'
        elif m['dst_ratio'] > 0.5:
            role = '偏末端'
        elif m['mid_ratio'] > 0.5:
            role = '偏中转'
        else:
            role = '混合'
        p(f"{n:<10} {s:>6.1f} {m['total']:>5} {m['as_src']:>5} {m['as_dst']:>5} {role:<12}")

    # --- 统计汇总 ---
    p("\n" + "=" * 90)
    p("【统计汇总】")
    p("=" * 90)

    tier_counts = Counter(t for _, _, t in tiered)
    for tier_name in ['S', 'A', 'B', 'C', 'D']:
        count = tier_counts.get(tier_name, 0)
        p(f"  {tier_name}级: {count}个分拣中心")

    p(f"\n  总计: {len(all_nodes)}个分拣中心")

    # --- 设备与等级交叉 ---
    p("\n" + "─" * 90)
    p("【设备分布 × 等级】")
    p("─" * 90)
    equip_tier = defaultdict(lambda: defaultdict(int))
    for n, _, t in tiered:
        equip_tier[metrics[n]['equip']][t] += 1

    p(f"{'设备':<10} {'S':>4} {'A':>4} {'B':>4} {'C':>4} {'D':>4} {'合计':>5}")
    for equip in sorted(equip_tier.keys()):
        row = equip_tier[equip]
        total = sum(row.values())
        p(f"{equip:<10} {row.get('S',0):>4} {row.get('A',0):>4} "
          f"{row.get('B',0):>4} {row.get('C',0):>4} "
          f"{row.get('D',0):>4} {total:>5}")

    # --- 网络拓扑关键发现 ---
    p("\n" + "=" * 90)
    p("【关键发现】")
    p("=" * 90)

    # 最大枢纽
    top5 = sorted_nodes[:5]
    p(f"\n  Top 5 超级枢纽: {', '.join(n for n,_ in top5)}")
    p(f"    这5个站出现在全网络 {sum(metrics[n]['od_coverage']*100 for n,_ in top5):.0f}% 的OD对路由中")

    # 始发大站
    by_src = sorted(all_nodes, key=lambda n: metrics[n]['vol_out'], reverse=True)
    p(f"\n  货量最大始发站 Top 5: {', '.join(by_src[:5])}")
    for n in by_src[:5]:
        p(f"    {n}: 日均发出 {metrics[n]['vol_out']:,.0f} 件")

    # 收货大站
    by_dst = sorted(all_nodes, key=lambda n: metrics[n]['vol_in'], reverse=True)
    p(f"\n  货量最大终点站 Top 5: {', '.join(by_dst[:5])}")
    for n in by_dst[:5]:
        p(f"    {n}: 日均流入 {metrics[n]['vol_in']:,.0f} 件")

    # 净发件 vs 净收件
    p(f"\n  净发件型站点（vol_out > vol_in * 1.5）:")
    net_sources = [n for n in all_nodes if metrics[n]['vol_out'] > metrics[n]['vol_in'] * 1.5]
    p(f"    共 {len(net_sources)} 个: {', '.join(sorted(net_sources, key=lambda n: -metrics[n]['vol_net_flow'])[:15])}")

    p(f"\n  净收件型站点（vol_in > vol_out * 1.5）:")
    net_sinks = [n for n in all_nodes if metrics[n]['vol_in'] > metrics[n]['vol_out'] * 1.5]
    p(f"    共 {len(net_sinks)} 个: {', '.join(sorted(net_sinks, key=lambda n: metrics[n]['vol_net_flow'])[:15])}")

    p(f"\n  双向平衡型站点（出入接近）:")
    balanced = [n for n in all_nodes
                if n not in net_sources and n not in net_sinks
                and metrics[n]['vol_out'] > 0 and metrics[n]['vol_in'] > 0]
    p(f"    共 {len(balanced)} 个")

    # 关键路径分析
    p(f"\n  下游最分散的站（发往最多方向）:")
    by_downstream = sorted(all_nodes,
                          key=lambda n: metrics[n]['n_effective_downstream'],
                          reverse=True)
    for n in by_downstream[:5]:
        p(f"    {n}: 有效下游 {metrics[n]['n_effective_downstream']} 个方向, "
          f"总下游 {metrics[n]['n_downstream']} 个")

    p(f"\n  上游最集中的站（依赖少数上游）:")
    by_up_conc = sorted(all_nodes,
                        key=lambda n: metrics[n]['upstream_concentration'],
                        reverse=True)
    for n in by_up_conc[:5]:
        p(f"    {n}: 上游集中度 {metrics[n]['upstream_concentration']:.1%}, "
          f"上游共 {metrics[n]['n_upstream']} 个")

print("Done! 报告已保存到 center_classification.txt")

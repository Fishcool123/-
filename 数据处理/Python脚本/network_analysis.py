"""分析物流网络的层级结构——验证是否存在"始发→枢纽→片区→末端"的层次"""
import os, csv
from collections import defaultdict, Counter
import numpy as np

base = r"C:\Users\www15\Desktop\26长三角数模\2026年第六届长三角高校数学建模竞赛赛题\2026长三角赛题A：物流网络集包规则及设备优化"

# ============================================================
# 1. 读取路由表
# ============================================================
routes = {}  # (src, dst) -> [node1, node2, ...]
with open(os.path.join(base, '附件表1.csv'), encoding='gbk') as f:
    reader = csv.reader(f)
    next(reader)  # skip header
    for row in reader:
        src, dst, path = row
        nodes = path.split('-')
        routes[(src, dst)] = nodes

# ============================================================
# 2. 读取货量数据（取最近30天的平均）
# ============================================================
from collections import defaultdict as dd
od_vol = dd(float)
od_count = dd(int)
with open(os.path.join(base, '附件表2.csv'), encoding='gbk') as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        date, src, dst, vol = row
        vol = float(vol)
        key = (src, dst)
        od_vol[key] += vol
        od_count[key] += 1

# 每条OD的日均货量
od_daily_avg = {k: od_vol[k]/od_count[k] for k in od_vol}

# ============================================================
# 3. 核心分析：每个节点在网络中的角色
# ============================================================
# 统计每个节点在各个位置出现的次数
as_src = Counter()       # 作为首分拣（起点）
as_dst = Counter()       # 作为末分拣（终点）
as_mid = Counter()       # 作为中间站（途经）
total_appear = Counter() # 总出现次数
route_set_per_node = defaultdict(set)  # 每个节点参与的路由集合

for (src, dst), nodes in routes.items():
    as_src[src] += 1
    as_dst[dst] += 1
    for node in nodes:
        total_appear[node] += 1
        route_set_per_node[node].add((src, dst))
    for mid in nodes[1:-1]:  # 中间站
        as_mid[mid] += 1

# ============================================================
# 4. 节点分类：根据角色判断层级
# ============================================================
all_nodes = sorted(set(as_src.keys()) | set(as_dst.keys()) | set(as_mid.keys()))

node_info = {}
for node in all_nodes:
    src_cnt = as_src.get(node, 0)
    dst_cnt = as_dst.get(node, 0)
    mid_cnt = as_mid.get(node, 0)
    total = src_cnt + dst_cnt + mid_cnt
    n_routes = len(route_set_per_node[node])

    # 计算该节点作为中间站时的"位置深度"
    # 收集该节点在各路由中所处的深度（从0开始）
    depths = []
    for (s, d), nodes in routes.items():
        if node in nodes:
            idx = nodes.index(node)
            path_len = len(nodes)
            depths.append((idx, path_len))

    # 判断角色
    # 枢纽型：大量作为中间站出现，src和dst都少
    # 始发型：主要作为src出现
    # 末端型：主要作为dst出现
    # 混合型：都出现

    mid_ratio = mid_cnt / total if total > 0 else 0
    src_ratio = src_cnt / total if total > 0 else 0
    dst_ratio = dst_cnt / total if total > 0 else 0

    avg_depth = np.mean([d[0] for d in depths]) if depths else 0
    avg_path_len = np.mean([d[1] for d in depths]) if depths else 0

    # 计算该节点连接的"下一跳"有哪些
    next_hops = set()
    prev_hops = set()
    for (s, d), nodes in routes.items():
        if node in nodes:
            idx = nodes.index(node)
            if idx < len(nodes) - 1:
                next_hops.add(nodes[idx + 1])
            if idx > 0:
                prev_hops.add(nodes[idx - 1])

    node_info[node] = {
        'src_cnt': src_cnt, 'dst_cnt': dst_cnt, 'mid_cnt': mid_cnt,
        'total': total, 'n_routes': n_routes,
        'mid_ratio': mid_ratio, 'src_ratio': src_ratio, 'dst_ratio': dst_ratio,
        'avg_depth': avg_depth, 'avg_path_len': avg_path_len,
        'n_next': len(next_hops), 'n_prev': len(prev_hops),
        'next_hops': next_hops, 'prev_hops': prev_hops,
    }

# ============================================================
# 5. 输出分析结果
# ============================================================
with open('network_analysis.txt', 'w', encoding='utf-8') as out:
    def p(*args):
        print(*args)
        print(*args, file=out)

    p("=" * 70)
    p("物流网络层级结构分析")
    p("=" * 70)

    # 5.1 纯枢纽（主要做中转的站）
    p("\n" + "─" * 70)
    p("【第一类】纯枢纽站：主要做中转，起点/终点角色占比低")
    p("─" * 70)
    p(f"{'站名':<10} {'总出现':>6} {'中转次数':>8} {'中转占比':>8} {'平均深度':>8} {'下一跳数':>8}")
    hubs = sorted(node_info.items(),
                  key=lambda x: (-x[1]['mid_cnt'], -x[1]['mid_ratio']))
    for name, info in hubs:
        if info['mid_ratio'] > 0.85 and info['mid_cnt'] > 100:
            p(f"{name:<10} {info['total']:>6} {info['mid_cnt']:>8} "
              f"{info['mid_ratio']:>7.1%} {info['avg_depth']:>8.2f} "
              f"{info['n_next']:>8}")

    # 5.2 始发-枢纽混合型
    p("\n" + "─" * 70)
    p("【第二类】始发枢纽混合站：既是起点又做中转")
    p("─" * 70)
    p(f"{'站名':<10} {'总出现':>6} {'起点':>6} {'中转':>6} {'终点':>6} "
      f"{'起点比':>7} {'中转比':>7} {'下一跳':>6}")
    for name, info in hubs:
        if info['mid_cnt'] > 200 and info['src_cnt'] > 50:
            p(f"{name:<10} {info['total']:>6} {info['src_cnt']:>6} "
              f"{info['mid_cnt']:>6} {info['dst_cnt']:>6} "
              f"{info['src_ratio']:>6.1%} {info['mid_ratio']:>6.1%} "
              f"{info['n_next']:>6}")

    # 5.3 纯始发站
    p("\n" + "─" * 70)
    p("【第三类】纯始发站（叶子发货站）")
    p("─" * 70)
    src_only = [(n, i) for n, i in node_info.items()
                if i['src_ratio'] > 0.9 and i['mid_cnt'] == 0]
    p(f"共 {len(src_only)} 个: {', '.join(n for n,_ in src_only[:20])}")

    # 5.4 纯终点站
    p("\n" + "─" * 70)
    p("【第四类】纯终点站（末端站，接近派送）")
    p("─" * 70)
    dst_only = [(n, i) for n, i in node_info.items()
                if i['dst_ratio'] > 0.9 and i['mid_cnt'] == 0]
    p(f"共 {len(dst_only)} 个: {', '.join(n for n,_ in dst_only[:20])}")

    # 5.5 多层级分析：各站平均深度分布
    p("\n" + "─" * 70)
    p("【层级分析】各站在路由中的平均深度")
    p("─" * 70)
    depths_list = [(n, i['avg_depth'], i['total'], i['mid_ratio'])
                   for n, i in node_info.items() if i['total'] > 10]
    depths_sorted = sorted(depths_list, key=lambda x: x[1])

    # 分深度区间统计
    depth_bins = [(0,0.5), (0.5,1.2), (1.2,2.0), (2.0,3.0), (3.0,10)]
    for lo, hi in depth_bins:
        stations = [d for d in depths_sorted if lo <= d[1] < hi]
        if stations:
            names = ', '.join(d[0] for d in stations[:15])
            p(f"\n  深度 [{lo}-{hi}): {len(stations)}个站")
            p(f"  代表: {names}{'...' if len(stations)>15 else ''}")

    # 5.6 关键枢纽的下游分析
    p("\n" + "─" * 70)
    p("【关键枢纽】下游连接分析（顶级中转站连接了哪些站）")
    p("─" * 70)
    top_hubs = ['A46分拣', 'A10分拣', 'A6分拣', 'A1分拣', 'A18分拣',
                'A5分拣', 'A15分拣', 'A42分拣', 'A102分拣', 'A45分拣']
    for hub in top_hubs:
        info = node_info.get(hub)
        if info:
            next_list = sorted(info['next_hops'],
                             key=lambda x: node_info.get(x, {}).get('mid_ratio', 0),
                             reverse=True)
            prev_list = sorted(info['prev_hops'],
                             key=lambda x: node_info.get(x, {}).get('mid_ratio', 0),
                             reverse=True)
            p(f"\n  {hub}: 出现{info['total']}次, 深度{info['avg_depth']:.2f}")
            p(f"    上游(谁发给它): {', '.join(prev_list[:8])}"
              f"{'...' if len(prev_list)>8 else ''}")
            p(f"    下游(它发去哪): {', '.join(next_list[:8])}"
              f"{'...' if len(next_list)>8 else ''}")

    # 5.7 网络层级深度统计
    p("\n" + "─" * 70)
    p("【路由深度统计】每条路由经过几个站")
    p("─" * 70)
    path_lens = [len(nodes) for nodes in routes.values()]
    len_counter = Counter(path_lens)
    for length in sorted(len_counter):
        p(f"  {length}站路由: {len_counter[length]}条")

    # 找出深度1（直发）、深度2、深度3的典型路由
    p("\n典型路由示例（按长度分类）:")
    for length in [2, 3, 4, 5, 6]:
        examples = [(s,d,n) for (s,d),n in routes.items() if len(n) == length][:3]
        p(f"\n  【{length}站路由】:")
        for s, d, n in examples:
            avg_vol = od_daily_avg.get((s, d), 0)
            p(f"    {s} → {' → '.join(n[1:-1])} → {d}  (日均{avg_vol:.0f}件)")

    # 5.8 货量与层级的关系
    p("\n" + "─" * 70)
    p("【货量视角】不同深度路由的日均货量分布")
    p("─" * 70)
    for length in [2, 3, 4, 5, 6]:
        vols = []
        for (s,d), nodes in routes.items():
            if len(nodes) == length:
                v = od_daily_avg.get((s, d), 0)
                if v > 0:
                    vols.append(v)
        if vols:
            p(f"  {length}站路由: 有货量的{len(vols)}条, "
              f"日均货量: 中位{np.median(vols):.0f}, "
              f"均值{np.mean(vols):.0f}, "
              f"最大{np.max(vols):.0f}")

    # 5.9 结论
    p("\n" + "=" * 70)
    p("【结论】")
    p("=" * 70)
    p("""
    物流网络确实存在明显的层级结构：

    1. 【始发层】纯始发站(如A20分拣、A9分拣等)：几乎只发出包裹，不中转
       → 类比：深圳/广州的片区揽收站

    2. 【一级枢纽】高频中转站(如A46、A10、A6、A1)：出现在大量路由的中间位置
       → 类比：杭州/广州这种省级大中转中心

    3. 【二级枢纽】中等中转站(如A24、A17、A62)：连接一级枢纽和末端站
       → 类比：余杭/萧山这种市级中转

    4. 【末端站】纯终点站：只接收包裹，发往终端站点派送
       → 类比：街道级分拨点

    5. 路由深度2~6站，大多数是3~4站（一级枢纽→二级枢纽→末端）
       → 对应：始发→省级中转→市级中转→末端 的经典4层结构
    """)

print("Done! 结果已保存到 network_analysis.txt")

"""
数据字典校验脚本 (v2 - 输出到文件)
用途：逐文件校验7个原始数据文件的列名、数据类型、数值范围
依赖：pandas, openpyxl
运行：py.exe _data_dict_check.py
输出：_data_dict_output.txt
"""
import pandas as pd
import numpy as np
import sys
import io

# 强制输出为UTF-8，避免终端GBK乱码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = r"c:\Users\www15\Desktop\26长三角数模\2026年第六届长三角高校数学建模竞赛赛题\2026长三角赛题A：物流网络集包规则及设备优化"

csv_files = [
    ("附件表1.csv", "附件表1"),
    ("附件表2.csv", "附件表2"),
    ("附件表3.csv", "附件表3"),
]

xlsx_files = [
    ("附件表4.xlsx", "附件表4"),
    ("结果表1.xlsx", "结果表1"),
    ("结果表2.xlsx", "结果表2"),
    ("结果表3.xlsx", "结果表3"),
]


def analyze_series(s, col_name):
    """分析单列的数据特征"""
    info = {}
    info["列名"] = col_name
    info["总行数"] = len(s)
    info["缺失数"] = int(s.isna().sum())
    info["缺失率"] = f"{s.isna().mean()*100:.2f}%"

    if s.dtype == 'object' or s.dtype == 'string':
        try:
            numeric = pd.to_numeric(s, errors='coerce')
            if numeric.notna().sum() > len(s) * 0.5:
                s_num = numeric.dropna()
                info["实际类型"] = "数值(str存储)"
                info["min"] = float(s_num.min())
                info["max"] = float(s_num.max())
                info["mean"] = float(s_num.mean())
                info["median"] = float(s_num.median())
                info["unique(值数)"] = int(s_num.nunique())
                return info
        except Exception:
            pass
        # 字符串列
        info["实际类型"] = "字符串"
        non_null = s.dropna()
        if len(non_null) > 0:
            n_unique = non_null.nunique()
            info["unique(值数)"] = n_unique
            if n_unique <= 50:
                vc = non_null.value_counts().head(30)
                info["取值分布"] = [(str(k), int(v)) for k, v in vc.items()]
            else:
                vc = non_null.value_counts().head(10)
                info["取值分布(Top10)"] = [(str(k), int(v)) for k, v in vc.items()]
        else:
            info["unique(值数)"] = 0
            info["取值分布"] = "全部为空"
    else:
        kind = str(s.dtype)
        if 'float' in kind:
            info["实际类型"] = "浮点数"
        elif 'int' in kind:
            info["实际类型"] = "整数"
        elif 'datetime' in kind:
            info["实际类型"] = "日期时间"
        elif 'bool' in kind:
            info["实际类型"] = "布尔"
        else:
            info["实际类型"] = f"数值({kind})"

        non_null = s.dropna()
        if len(non_null) > 0:
            info["min"] = float(non_null.min()) if 'datetime' not in kind and 'bool' not in kind else str(non_null.min())
            info["max"] = float(non_null.max()) if 'datetime' not in kind and 'bool' not in kind else str(non_null.max())
            info["mean"] = float(non_null.mean()) if 'datetime' not in kind and 'bool' not in kind else "N/A"
            info["median"] = float(non_null.median()) if 'datetime' not in kind and 'bool' not in kind else "N/A"
            info["unique(值数)"] = int(non_null.nunique())
            if non_null.nunique() <= 20:
                vc = non_null.value_counts().sort_index()
                info["取值分布"] = [(str(k), int(v)) for k, v in vc.items()]
        else:
            info["min"] = "N/A(全空)"
            info["max"] = "N/A(全空)"
            info["mean"] = "N/A(全空)"
            info["median"] = "N/A(全空)"
            info["unique(值数)"] = 0

    return info


def format_info(info, indent="  "):
    """格式化输出单列信息"""
    lines = []
    prefix = indent + "| "
    lines.append(f"{indent}[列名] {info['列名']}")
    lines.append(f"{prefix}类型: {info['实际类型']}")
    if 'min' in info:
        lines.append(f"{prefix}min={info['min']} | max={info['max']} | mean={info['mean']} | median={info['median']}")
    if 'unique(值数)' in info:
        lines.append(f"{prefix}unique值数: {info['unique(值数)']}")
    if '取值分布' in info:
        lines.append(f"{prefix}取值分布:")
        for item in info['取值分布']:
            if isinstance(item, tuple):
                lines.append(f"{prefix}  {item[0]}: {item[1]}")
            else:
                lines.append(f"{prefix}  {item}")
    if '取值分布(Top10)' in info:
        lines.append(f"{prefix}取值分布(Top10):")
        for item in info['取值分布(Top10)']:
            lines.append(f"{prefix}  {item[0]}: {item[1]}")
    lines.append(f"{prefix}缺失: {info['缺失数']}/{info['总行数']} ({info['缺失率']})")
    return "\n".join(lines)


def print_section(title):
    print()
    print("=" * 80)
    print(f"  {title}")
    print("=" * 80)


def analyze_csv(filename, label):
    filepath = f"{BASE}\\{filename}"
    print_section(f"{filename} ({label})")

    try:
        df = pd.read_csv(filepath, encoding='gbk')
    except Exception as e:
        print(f"  [ERROR] GBK读取失败: {e}")
        return

    print(f"  行数: {len(df)} | 列数: {len(df.columns)}")
    print(f"  原始列名: {list(df.columns)}")
    print()

    for col in df.columns:
        info = analyze_series(df[col], col)
        print(format_info(info))
        print()

def analyze_xlsx(filename, label):
    filepath = f"{BASE}\\{filename}"
    print_section(f"{filename} ({label})")

    try:
        df = pd.read_excel(filepath)
    except Exception as e:
        print(f"  [ERROR] 读取失败: {e}")
        return

    print(f"  行数: {len(df)} | 列数: {len(df.columns)}")
    print(f"  原始列名: {list(df.columns)}")
    print()

    if len(df) == 0:
        print("  [警告] 此表为空表（仅含表头），为结果模板。")
        for col in df.columns:
            print(f"  [模板列] {col} (dtype: {df[col].dtype})")
        print()
        return

    for col in df.columns:
        info = analyze_series(df[col], col)
        print(format_info(info))
        print()


if __name__ == "__main__":
    print("=" * 80)
    print("  A题原始数据 -- 完整数据字典")
    print("  生成时间: 2026-05-16")
    print("=" * 80)

    for fname, label in csv_files:
        analyze_csv(fname, label)

    for fname, label in xlsx_files:
        analyze_xlsx(fname, label)

    print()
    print("=" * 80)
    print("  校验完成")
    print("=" * 80)

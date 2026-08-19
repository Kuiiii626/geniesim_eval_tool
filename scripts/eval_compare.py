#!/usr/bin/env python3
# scripts/eval_compare.py
import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import matplotlib.pyplot as plt


def load_one_model(folder: str):
    """
    递归读取一个结果文件夹下全部csv（包括子文件夹）
    return dict[task_name] = success_rate(float 0~1)
    csv文件名格式: modelname_taskname_result.csv
    """
    task_map = {}
    folder = Path(folder)
    if not folder.exists():
        print(f"[WARN] 文件夹不存在 {folder}")
        return task_map

    for csv_path in folder.rglob("*_result.csv"):
        fname = csv_path.name
        pure = fname[:-len("_result.csv")]
        parts = pure.split("_", maxsplit=1)
        if len(parts) < 2:
            continue
        _, task_name = parts

        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            print(f"[WARN] 读取失败 {csv_path}, {e}")
            continue

        if "success_rate" in df.columns:
            sr = float(df["success_rate"].iloc[0])
        elif {"success", "total"}.issubset(df.columns):
            suc = float(df["success"].iloc[0])
            tot = float(df["total"].iloc[0])
            sr = suc / tot if tot > 0 else 0.0
        else:
            continue
        
        if task_name in task_map:
            print(f"[WARN] 任务 {task_name} 重复，已合并结果")
        task_map[task_name] = sr
    return task_map


def main():
    parser = argparse.ArgumentParser(description="GenieSim多模型横向对比工具 v1.1")
    parser.add_argument(
        "--model",
        action="append",
        required=True,
        help='模型组，格式 "模型名:文件夹路径"，可多次传入。例 --model "40000:/home/xxx/res40000" --model "45000:/home/xxx/res45000"'
    )
    parser.add_argument(
        "--task-filter",
        nargs="+",
        default=None,
        help="指定需要对比的任务列表，不填默认全部共有任务。例 --task-filter g2op_manip_open_door g2op_pick_xxx"
    )
    parser.add_argument(
        "--out-root",
        default="./compare_output",
        help="输出文件根目录"
    )

    args = parser.parse_args()

    # 解析多组 model:dir
    model_info = []
    for item in args.model:
        sp = item.split(":", maxsplit=1)
        if len(sp)!=2:
            print(f"[ERROR] 参数格式错误：{item}，必须使用 模型名:文件夹")
            sys.exit(1)
        m_name, m_dir = sp
        model_info.append((m_name.strip(), m_dir.strip()))

    # 读取每一个模型 {task: rate}
    model_data = {}
    for m_name, m_dir in model_info:
        d = load_one_model(m_dir)
        if len(d) ==0:
            print(f"[ERROR] 模型 {m_name} 文件夹没有读到有效csv任务数据！")
            sys.exit(1)
        model_data[m_name] = d

    # 求全部模型任务的并集
    all_task_sets = [set(v.keys()) for v in model_data.values()]
    all_tasks = set.union(*all_task_sets)

    # 用户指定过滤任务
    if args.task_filter is not None and len(args.task_filter) > 0:
        user_tasks = set(args.task_filter)
        all_tasks = all_tasks & user_tasks

    all_tasks = sorted(list(all_tasks))
    if len(all_tasks) == 0:
        print("[ERROR] 没有可对比任务！检查csv文件名、--task-filter任务名是否正确")
        sys.exit(1)
    print(f"[INFO] 参与对比任务共 {len(all_tasks)} 个：{all_tasks}")

    # 输出目录 + 时间戳文件名
    ts = time.strftime("%Y%m%d_%H%M%S")
    model_tag = "_".join([m for m,_ in model_info])
    out_dir = Path(args.out_root)
    out_dir.mkdir(exist_ok=True, parents=True)

    out_csv = out_dir / f"{model_tag}_{ts}_compare.csv"
    out_line = out_dir / f"{model_tag}_{ts}_compare_line.png"
    out_bar = out_dir / f"{model_tag}_{ts}_compare_bar.png"

    # 组装表格
    rows = []
    for task in all_tasks:
        row = {"task_name": task}
        for m_name in model_data:
            if task in model_data[m_name]:
                row[f"{m_name}_success_rate"] = round(model_data[m_name][task], 4)
            else:
                row[f"{m_name}_success_rate"] = "-"
        rows.append(row)
    df_out = pd.DataFrame(rows)
    df_out.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"[OK] 对比表格：{out_csv}")

    # 绘图折线图
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
    plt.figure(figsize=(14, 6))
    x = list(range(len(all_tasks)))
    markers = ["o", "s", "^", "D", "*", "p"]

    for idx, m_name in enumerate(model_data):
        y = [model_data[m_name].get(t, None) for t in all_tasks]
        mk = markers[idx % len(markers)]
        plt.plot(x, y, marker=mk, label=m_name, linewidth=1.2)

    plt.xticks(x, all_tasks, rotation=45, ha="right", fontsize=8)
    plt.ylabel("Success Rate", fontsize=11)
    plt.ylim(0, 1.05)
    plt.title(f"Model Compare | {model_tag}", fontsize=12)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_line, dpi=150)
    print(f"[OK] 对比折线图：{out_line}")
    plt.close()

    # 绘图柱形图
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
    x_pos = list(range(len(all_tasks)))
    width = 0.8 / len(model_data)
    
    plt.figure(figsize=(14, 6))
    for idx, m_name in enumerate(model_data):
        y = [model_data[m_name].get(t, 0) for t in all_tasks]
        offset = (idx - len(model_data)/2 + 0.5) * width
        bars = plt.bar([p + offset for p in x_pos], y, width, 
                       label=m_name, color=colors[idx % len(colors)], alpha=0.8)
    
    plt.xticks(x_pos, all_tasks, rotation=45, ha="right", fontsize=8)
    plt.ylabel("Success Rate", fontsize=11)
    plt.ylim(0, 1.05)
    plt.title(f"Model Compare | {model_tag}", fontsize=12)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_bar, dpi=150)
    print(f"[OK] 对比柱形图：{out_bar}")


if __name__ == "__main__":
    main()

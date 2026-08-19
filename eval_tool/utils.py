import os
import csv
from typing import List, Dict

# CSV输出固定列顺序，model、scene_mode放最前面
CSV_FIELD_NAMES = [
    "model",
    "scene_mode",
    "task_name",
    "json_file",
    "total_episode",
    "crash_count",
    "valid_num",
    "success_count",
    "fail_count",
    "success_rate",
    "avg_time"
]


def ensure_dir(dir_path: str):
    """确保目录存在"""
    os.makedirs(dir_path, exist_ok=True)


def write_csv(out_csv_path: str, rows: List[Dict]):
    """把结果列表写入csv"""
    with open(out_csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELD_NAMES)
        writer.writeheader()
        writer.writerows(rows)

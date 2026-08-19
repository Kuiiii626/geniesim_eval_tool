#!/usr/bin/env python3
# scripts/eval_parse_only.py
import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from eval_tool.parser import scan_all_json
from eval_tool.utils import ensure_dir, write_csv

CONFIG_INPUT_FOLDER = "./put_your_json_here"
CONFIG_MODEL_NAME = "unknown_model"
CONFIG_SCENE_MODE = "random"
CONFIG_OUTPUT_DIR = "./eval_result"


def main():
    parser = argparse.ArgumentParser(description="GenieSim评测工具 v1.1 仅解析日志")
    parser.add_argument("--input-folder", type=str, help="JSON日志输入文件夹")
    parser.add_argument("--model", type=str, help="模型名称标记")
    parser.add_argument("--scene", type=str, help="场景模式 fixed/random")
    parser.add_argument("--output-dir", type=str, help="CSV输出目录")

    args = parser.parse_args()

    input_folder = args.input_folder if args.input_folder else CONFIG_INPUT_FOLDER
    model_name = args.model if args.model else CONFIG_MODEL_NAME
    scene_mode = args.scene if args.scene else CONFIG_SCENE_MODE
    output_dir = args.output_dir if args.output_dir else CONFIG_OUTPUT_DIR

    ensure_dir(output_dir)

    print("=" * 60)
    print("🔧 模式：半自动（仅解析已有日志）")
    print("=" * 60)

    res_list = scan_all_json(input_folder, model_name, scene_mode)

    if len(res_list) == 0:
        print("\n⚠️ 未找到evaluate_ret开头的json文件，请检查输入路径")
        sys.exit(0)

    task_name_set = {item["task_name"] for item in res_list}
    if len(task_name_set) > 1:
        print(f"\n⚠️ 检测多task: {task_name_set}，使用第一个task命名输出文件")
    main_task_name = res_list[0]["task_name"]

    out_csv_name = f"{main_task_name}_{model_name}.csv"
    out_csv_path = os.path.join(output_dir, out_csv_name)

    write_csv(out_csv_path, res_list)

    print(f"\n🎉 解析完成！")
    print(f"📂 输入目录: {input_folder}")
    print(f"🤖 模型: {model_name} | 🎯场景: {scene_mode}")
    print(f"📊 处理文件数: {len(res_list)}")
    print(f"📁 输出: {out_csv_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()

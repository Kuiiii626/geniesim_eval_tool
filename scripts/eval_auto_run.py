#!/usr/bin/env python3
import argparse
import json
import os
import sys
import subprocess
import signal
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from eval_tool.genie_runner import run_single_task
from eval_tool.parser import parse_json
from eval_tool.utils import write_csv, ensure_dir

g_docker_id = None


def signal_handler(sig, frame):
    print("\n[INTERRUPT] 脚本被Ctrl-C中断")
    if g_docker_id:
        print(f"[CLEAN] 请手动清理容器残留进程: docker exec {g_docker_id} pkill -9 -f geniesim")
    sys.exit(1)


def check_docker_exists(docker_id):
    result = subprocess.run(
        ["docker", "inspect", docker_id],
        capture_output=True
    )
    return result.returncode == 0


def get_existing_jsons(folder):
    result = set()
    if not os.path.exists(folder):
        return result
    for root, _, files in os.walk(folder):
        for f in files:
            if f.startswith("evaluate_ret") and f.endswith(".json"):
                result.add(os.path.join(root, f))
    return result


def scan_new_jsons(input_folder, existing_set, model_name, scene_mode):
    result_list = []
    if not os.path.exists(input_folder):
        return result_list
    for root, _, files in os.walk(input_folder):
        for filename in files:
            if filename.startswith("evaluate_ret") and filename.endswith(".json"):
                full_path = os.path.join(root, filename)
                if full_path not in existing_set:
                    stat_item = parse_json(full_path)
                    stat_item["model"] = model_name
                    stat_item["scene_mode"] = scene_mode
                    stat_item["json_file"] = os.path.relpath(full_path, input_folder)
                    result_list.append(stat_item)
    return result_list


def main():
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(description="v2.0全自动：JSON配置驱动，docker内部运行GenieSim仿真评测")
    parser.add_argument("--config", required=True, help="实验配置json文件路径")
    parser.add_argument("--docker-id", help="覆盖配置文件中的docker_id")
    parser.add_argument("--model-name", help="覆盖配置文件中的model_name")
    parser.add_argument("--infer-host", help="覆盖配置文件中的infer_host")
    parser.add_argument("--model-arc", help="覆盖配置文件中的model_arc")
    parser.add_argument("--timeout", type=int, help="覆盖配置文件中的task_timeout_sec")
    parser.add_argument("--output-dir", help="覆盖配置文件中的parse_output_dir")
    parser.add_argument("--exp-version", help="实验版本标记")
    parser.add_argument("--task", nargs="+", help="指定要运行的任务列表，覆盖配置文件中的task_list")
    parser.add_argument("--geniesim-output", help="覆盖配置文件中的geniesim_output_base")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        exp_cfg = json.load(f)

    docker_id = args.docker_id or exp_cfg["docker_id"]
    model_name = args.model_name or exp_cfg["model_name"]
    task_list = args.task if args.task else exp_cfg["task_list"]
    infer_host = args.infer_host or exp_cfg["infer_host"]
    model_arc = args.model_arc or exp_cfg.get("model_arc", "corobot")
    task_timeout_sec = args.timeout or exp_cfg["task_timeout_sec"]
    geniesim_output_base = args.geniesim_output or exp_cfg["geniesim_output_base"]
    parse_output_dir = args.output_dir or exp_cfg["parse_output_dir"]

    global g_docker_id
    g_docker_id = docker_id

    if len(task_list) == 0:
        print("[INFO] task_list为空，无任务需执行")
        sys.exit(0)

    if not check_docker_exists(docker_id):
        print(f"[ERROR] Docker容器 {docker_id} 不存在")
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(parse_output_dir, timestamp)

    ensure_dir(geniesim_output_base)
    ensure_dir(output_dir)

    print(f"[CONFIG] 输出目录: {output_dir}")

    for task in task_list:
        print(f"\n==================== 开始执行任务：{task} ====================")

        print("[CLEAN] 清理docker内残留进程")
        subprocess.run(f"docker exec {docker_id} pkill -9 -f geniesim", shell=True, capture_output=True)
        subprocess.run(f"docker exec {docker_id} pkill -9 -f 'python.*app.py'", shell=True, capture_output=True)
        subprocess.run(f"docker exec {docker_id} pkill -9 -f kit/python", shell=True, capture_output=True)

        task_sim_folder = os.path.join(geniesim_output_base, f"{model_name}_{task}")
        ensure_dir(task_sim_folder)
        log_file = os.path.join(task_sim_folder, "run_task.log")

        existing_jsons = get_existing_jsons(geniesim_output_base)

        geniesim_inner_cmd = (
            f"geniesim51 benchmark run {task} "
            f"--benchmark.infer-host {infer_host} "
            f"--benchmark.model-arc {model_arc}"
        )
        print(f"容器内执行指令：{geniesim_inner_cmd}")

        ret_code = run_single_task(
            docker_id=docker_id,
            geniesim_cmd=geniesim_inner_cmd,
            log_save_path=log_file,
            timeout_sec=task_timeout_sec
        )

        task_model_tag = f"{model_name}_{task}"
        csv_file = os.path.join(output_dir, f"{task_model_tag}_result.csv")

        if ret_code in (0, -1):
            print(f"[PARSE] 开始解析 {geniesim_output_base}, ret_code={ret_code}")
            res_list = scan_new_jsons(
                input_folder=geniesim_output_base,
                existing_set=existing_jsons,
                model_name=model_name,
                scene_mode=task
            )
            write_csv(csv_file, res_list)
            print(f"[OK] 新增{len(res_list)}个结果，已输出：{csv_file}")
        else:
            print(f"[SKIP] 任务 {task} 启动异常")

    print(f"\n=======全部任务执行完成=======")
    print(f"[OUTPUT] 结果目录: {output_dir}")


if __name__ == "__main__":
    main()
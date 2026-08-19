import json
import os


def parse_json(json_file_path: str):
    """
    解析单份 evaluate_ret_xx.json
    :param json_file_path: json文件路径
    :return: dict 统计指标字典
    """
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    details_list = data["details"]

    total_episode = len(details_list)
    crash_count = 0
    success_count = 0
    fail_count = 0
    sum_duration = 0.0
    task_name = ""

    if len(details_list) > 0:
        first_ep = details_list[0]
        task_name = first_ep.get("task_name", "unknown_task")

        for ep in details_list:
            res = ep.get("result", {})
            code = res.get("code", -1)

            if code != 0 or "E2E" not in res.get("scores", {}):
                crash_count += 1
                continue

            e2e_score = res["scores"]["E2E"]
            dur = ep.get("duration", 0.0)
            sum_duration += dur

            if e2e_score == 1:
                success_count += 1
            else:
                fail_count += 1

    valid_num = total_episode - crash_count
    if valid_num > 0:
        success_rate = round(success_count / valid_num, 4)
        avg_time = round(sum_duration / valid_num, 2)
    else:
        success_rate = 0.0
        avg_time = 0.0

    return {
        "task_name": task_name,
        "total_episode": total_episode,
        "crash_count": crash_count,
        "valid_num": valid_num,
        "success_count": success_count,
        "fail_count": fail_count,
        "success_rate": success_rate,
        "avg_time": avg_time
    }


def scan_all_json(input_folder: str, model_name: str, scene_mode: str):
    """
    递归遍历文件夹，批量解析所有 evaluate_ret*.json
    :param input_folder: 日志根目录
    :param model_name: 模型标记
    :param scene_mode: 场景标记 fixed/random
    :return: list[dict] 全部统计结果
    """
    result_list = []
    if not os.path.isdir(input_folder):
        return result_list

    for root, _, files in os.walk(input_folder):
        for filename in files:
            if filename.endswith(".json") and filename.startswith("evaluate_ret"):
                full_path = os.path.join(root, filename)
                stat_item = parse_json(full_path)
                stat_item["model"] = model_name
                stat_item["scene_mode"] = scene_mode
                stat_item["json_file"] = os.path.relpath(full_path, input_folder)
                result_list.append(stat_item)
    return result_list


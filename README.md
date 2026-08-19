# GenieSim Evaluation Tool

GenieSim仿真评测工具，支持全自动运行任务和解析结果。

## 重要说明

本评测脚本用于测试 **VLA（视觉语言动作）模型** 在 GenieSim 具身仿真环境下的任务表现。

GenieSim仿真中机械臂的动作输出，全部来自外部VLA推理服务；脚本本身不负责拉起VLA服务。

**在运行 `eval_auto_run.py` 脚本之前，必须预先启动VLA推理服务，并保证配置文件内 `infer_host` 地址端口和VLA服务监听地址完全一致，否则仿真任务会全部超时/无动作输出。**

## 项目结构

```
geniesim_eval_tool/
├── config/
│   └── exp_example.json      # 实验配置文件
├── scripts/
│   ├── eval_auto_run.py      # 全自动：运行任务+解析结果
│   ├── eval_parse_only.py    # 半自动：仅解析已有JSON
│   └── eval_compare.py       # 多模型对比分析
├── eval_tool/
│   ├── genie_runner.py       # 执行docker内geniesim命令
│   ├── parser.py             # 解析evaluate_ret*.json
│   └── utils.py              # 写CSV等工具
├── sample_output/            # 完整运行示例
│   └── 20260817_120000/
│       ├── 40000_g2op_manip_open_door_result.csv
│       ├── 40000_g2op_if_pick_billiards_color_result.csv
│       └── 40000_g2op_spatial_stack_bowls_result.csv
└── README.md
```

## 两种模式

### 模式一：全自动（推荐）

自动在docker容器内运行geniesim任务，解析结果输出CSV。

**启动命令：**
```bash
python3 scripts/eval_auto_run.py --config config/exp_example.json
```

**命令行参数（可覆盖配置文件）：**
```bash
python3 scripts/eval_auto_run.py --config config/exp_example.json \
  --docker-id <容器ID> \
  --model-name <模型名> \
  --infer-host <推理地址> \
  --timeout <超时秒数> \
  --output-dir <输出目录> \
  --geniesim-output <geniesim_json输出目录> \
  --task <任务1> <任务2> ...
```

**参数说明：**
| 参数 | 说明 |
|------|------|
| --config | 配置文件路径（必填） |
| --docker-id | 覆盖容器ID |
| --model-name | 覆盖模型名 |
| --infer-host | 覆盖推理地址 |
| --timeout | 覆盖超时秒数 |
| --output-dir | 覆盖输出目录 |
| --task | 指定任务列表（可多个） |

**运行示例：**
```bash
# 使用配置文件运行全部任务
python3 scripts/eval_auto_run.py --config config/exp_example.json

# 命令行指定单个任务
python3 scripts/eval_auto_run.py --config config/exp_example.json \
  --task g2op_manip_open_door

# 命令行指定多个任务
python3 scripts/eval_auto_run.py --config config/exp_example.json \
  --task g2op_manip_open_door g2op_if_pick_billiards_color

# 完整参数示例
python3 scripts/eval_auto_run.py --config config/exp_example.json \
  --docker-id <your_docker_container_id> \
  --model-name 40000 \
  --infer-host <infer_service_ip:port> \
  --timeout 120 \
  --output-dir /home/ubuntu/agibot_ws/eval_auto_result \
  --geniesim-output /home/ubuntu/agibot_ws/genie_sim/output \
  --task task g2op_robust_instructgen_pick_block_shape g2op_robust_posegen_pick_billiards_color
```

**配置文件说明 (`config/exp_example.json`)：**
```json
{
  "docker_id": "容器ID",
  "model_name": "模型名称标记",
  "task_list": ["任务1", "任务2"],
  "infer_host": "模型推理服务地址",
  "task_timeout_sec": 220,
  "geniesim_output_base": "geniesim输出JSON目录",
  "parse_output_dir": "CSV输出目录"
}
```

**工作流程：**
1. 检查docker容器是否存在
2. 清理docker内残留进程
3. 记录已有JSON文件
4. 执行 `geniesim51 benchmark run <task>`，日志保存到 `run_task.log`
5. 解析新增的JSON文件
6. 输出CSV到 `{parse_output_dir}/{timestamp}/`

示例：`eval_auto_result/20260817_120000/`

### 模式二：半自动

仅解析已有的JSON文件，不运行任务。

**启动命令：**
```bash
python3 scripts/eval_parse_only.py \
  --input-folder <JSON目录> \
  --model <模型名> \
  --output-dir <输出目录>
```

### 模式三：多模型对比

横向对比多个模型的评测结果，生成对比表格和可视化图表。

**启动命令：**
```bash
python3 scripts/eval_compare.py \
  --model "<模型名1>:<结果目录1>" \
  --model "<模型名2>:<结果目录2>" \
  [--task-filter <任务1> <任务2> ...]
```

**参数说明：**
| 参数 | 说明 |
|------|------|
| --model | 模型组，格式 `"模型名:结果目录"`，可多次传入 |
| --task-filter | 指定对比的任务列表，不填默认全部任务 |
| --out-root | 输出根目录，默认 `./compare_output` |

**运行示例：**
```bash
# 对比三个模型的所有任务
python3 scripts/eval_compare.py \
  --model "40000:/home/ubuntu/agibot_ws/eval_auto_result/40" \
  --model "45000:/home/ubuntu/agibot_ws/eval_auto_result/45" \
  --model "pi0.5:/home/ubuntu/agibot_ws/eval_auto_result/0.5"

# 仅对比指定任务
python3 scripts/eval_compare.py \
  --model "40000:/home/ubuntu/agibot_ws/eval_auto_result/40" \
  --model "45000:/home/ubuntu/agibot_ws/eval_auto_result/45" \
  --task-filter g2op_manip_open_door g2op_if_pick_billiards_color
```

**功能特点：**
- 自动递归扫描子文件夹中的CSV文件
- 显示所有任务（并集），缺失任务标记为 "-"
- 支持任务过滤，仅对比指定任务

**输出文件：**
- `{模型组合}_{时间戳}_compare.csv` - 对比表格
- `{模型组合}_{时间戳}_compare_line.png` - 折线图
- `{模型组合}_{时间戳}_compare_bar.png` - 柱形图

## 输出说明

**CSV字段：**

| 字段 | 说明 |
|------|------|
| model | 模型名称标记 |
| scene_mode | 场景模式 |
| task_name | 任务名称 |
| json_file | JSON文件名 |
| total_episode | 总episode数 |
| crash_count | 异常样本数 |
| valid_num | 有效样本数 |
| success_count | 成功数 |
| fail_count | 失败数 |
| success_rate | 成功率 |
| avg_time | 平均耗时(秒) |

**示例输出见 `sample_output/` 目录**

## 统计口径

- **crash_count**：episode执行异常（`code != 0`或缺失E2E评分）
- **valid_num**：总episode数减去异常数
- **success_rate**：成功数 / 有效样本数
- 任务目标未达成（如抓取失败）属正常失败，不计入crash

## 异常处理

| 场景 | 行为 |
|------|------|
| 容器不存在 | 打印错误，脚本退出 |
| 任务超时 | 强制kill进程，返回ret_code=-1，继续解析已产出的JSON |
| 任务启动失败 | 返回ret_code=-2，跳过解析，继续下一任务 |
| 无JSON产出 | CSV仅含表头 |
| Ctrl-C中断 | 提示手动清理容器残留进程 |

## 环境要求

**全自动模式：**
- Docker容器已安装geniesim51
- Docker卷挂载正确（`/workspace`映射到本地）
- 模型推理服务可访问

**半自动模式：**
- Python 3环境

## 部署说明

换电脑需修改配置文件：
- `docker_id`：新容器ID
- `geniesim_output_base`：geniesim输出路径（通常是 `/home/user/agibot_ws/genie_sim/output`）
- `parse_output_dir`：CSV输出路径
- `infer_host`：模型推理服务地址

**注意**：`geniesim_output_base` 必须对应Docker容器内 `/workspace/output` 映射到宿主机的路径。查看容器卷挂载：
```bash
docker inspect <容器ID> | grep -A 2 "/workspace"
```
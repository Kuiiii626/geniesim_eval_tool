# 项目限制说明

## 1. JSON日志不存储模型权重信息
GenieSim输出日志仅记录任务执行结果，不会保存当前加载的checkpoint。脚本无法通过日志自动区分模型版本，需在配置文件中手动标记。

## 2. 异常码说明
- `code = 0`：episode正常执行完成
- `code != 0`：episode执行过程中出现异常（推理失败、IK求解失败、任务初始化失败等）

## 3. 进程级崩溃无法检测
若仿真进程直接崩溃（如强杀、OOM），当前episode无日志落盘，脚本无法统计此类丢失样本。

## 4. 推理服务超时问题
若推理服务断开且客户端未配置超时，仿真会阻塞等待，episode无法结束，不会生成日志。

## 5. 输出路径依赖docker挂载
全自动模式依赖docker卷挂载：
- 容器内 `/workspace/output/benchmark/` 需正确映射到宿主机
- 若挂载配置错误，脚本无法找到生成的JSON文件

## 6. 任务名与输出目录不直接对应
geniesim的任务名（如`g2op_if_pick_billiards_color`）与实际输出目录（如`table_task_1_g2_op/pick_billiards_color/`）不直接对应，脚本通过解析JSON文件中的`task_name`字段识别任务。

## 7. 多任务并行不支持
脚本串行执行任务列表，不支持并行运行多个任务。

## 8. 历史数据过滤
脚本通过记录任务运行前后的JSON文件差异，仅解析新增文件，避免重复统计历史数据。若手动修改/删除JSON文件，可能导致统计遗漏。

## 9. Ctrl-C中断残留进程
脚本被Ctrl-C中断时，容器内geniesim51进程会残留，需手动清理：
```bash
docker exec <docker_id> pkill -9 -f geniesim51
```

## 10. 容器-宿主机权限
若容器内输出目录权限为root，宿主机读取时可能报PermissionError。需手动修改权限：
```bash
sudo chown -R <user>:<group> <output_dir>
```
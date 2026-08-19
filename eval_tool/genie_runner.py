import subprocess


def run_single_task(docker_id: str, geniesim_cmd: str, log_save_path: str, timeout_sec: int):
    """
    在docker容器内部运行geniesim benchmark
    :param docker_id: 容器id
    :param geniesim_cmd: 容器内要执行的geniesim完整指令
    :param log_save_path: 宿主机保存日志路径
    :param timeout_sec: 用户设定最大允许执行时间（秒）
    :return: int  0正常退出； -1超时终止； -2其他异常
    """
    full_cmd = f"docker exec -i {docker_id} {geniesim_cmd} > {log_save_path} 2>&1"
    proc = subprocess.Popen(full_cmd, shell=True)
    try:
        return_code = proc.wait(timeout=timeout_sec)
        if return_code == 0:
            return 0
        else:
            return -2
    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] 超过{timeout_sec}秒，强制终止容器内进程")
        subprocess.run(["docker", "exec", docker_id, "pkill", "-9", "-f", "geniesim"], capture_output=True)
        subprocess.run(["docker", "exec", docker_id, "pkill", "-9", "-f", "python.*app.py"], capture_output=True)
        subprocess.run(["docker", "exec", docker_id, "pkill", "-9", "-f", "kit/python"], capture_output=True)
        proc.kill()
        proc.wait()
        return -1
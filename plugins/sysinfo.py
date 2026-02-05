import platform
import psutil
import time
import os

__info__ = {
    "help": "系统监控：CPU/内存、全分区磁盘、网络流量及实时网速",
    "alias": ["sys", "info", "status"]
}

def get_size(bytes, suffix="B"):
    """容量单位自动转换"""
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor

def run_sysinfo(args, tools):
    Fore = tools.get("Fore")
    
    # 1. 采集数据
    uname = platform.uname()
    # 实时网速：记录初始流量
    io_start = psutil.net_io_counters()
    time.sleep(1) # 采样间隔 1 秒
    io_end = psutil.net_io_counters()
    
    # 计算网速
    up_speed = get_size(io_end.bytes_sent - io_start.bytes_sent)
    down_speed = get_size(io_end.bytes_recv - io_start.bytes_recv)
    
    print(f"\n{Fore.CYAN}🖥️  DevBox SysInfo - 系统全景状态报告")
    print("-" * 65)

    # 2. 基础系统信息
    print(f"{Fore.WHITE}主机节点 : {uname.node}")
    print(f"操作系统 : {uname.system} {uname.release} ({platform.architecture()[0]})")
    print(f"系统架构 : {uname.machine}")
    print(f"运行时间 : {get_size(time.time() - psutil.boot_time(), 'S')[:-1]} (自启动)")
    print("-" * 65)

    # 3. 进度条渲染函数
    def print_bar(label, percent, info_suffix="", color=Fore.GREEN):
        bar_len = 25
        filled = int(bar_len * percent / 100)
        # 根据负载自动变换颜色
        if percent > 85: color = Fore.RED
        elif percent > 60: color = Fore.YELLOW
        
        bar = "█" * filled + "░" * (bar_len - filled)
        print(f"{label:<8} : {color}[{bar}] {percent}% {Fore.WHITE}{info_suffix}")

    # 4. CPU & 内存状态
    cpu_freq = psutil.cpu_freq()
    cpu_info = f"({psutil.cpu_count(logical=False)}核/{psutil.cpu_count()}线程 @ {cpu_freq.current:.0f}MHz)" if cpu_freq else ""
    print_bar("CPU 负载", psutil.cpu_percent(), cpu_info)
    
    mem = psutil.virtual_memory()
    mem_info = f"({get_size(mem.used)} / {get_size(mem.total)})"
    print_bar("内存占用", mem.percent, mem_info)
    
    # 5. 网络流量 (实时)
    print(f"{Fore.WHITE}网络流量 : ⬆️ 上传 {up_speed}/s | ⬇️ 下载 {down_speed}/s")
    print("-" * 65)

    # 6. 多磁盘分区检测
    print(f"{Fore.CYAN}📁 存储设备详情:")
    partitions = psutil.disk_partitions()
    for partition in partitions:
        # 排除虚拟盘和空盘
        if os.name == 'nt':
            if 'cdrom' in partition.opts or partition.fstype == '': continue
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            p_label = f"分区 {partition.device}"
            p_info = f"{get_size(usage.used)} / {get_size(usage.total)} ({partition.fstype})"
            print_bar(p_label, usage.percent, p_info, Fore.BLUE)
        except PermissionError:
            continue
    
    print("-" * 65)
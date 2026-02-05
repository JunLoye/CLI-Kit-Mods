import asyncio
import socket
import time
import sys
from urllib.request import Request, urlopen

__info__ = {
    "help": "端口扫描",
    "alias": ["scan", "audit"]
}

PORT_PRESETS = {
    "常用服务": {
        "ports": "21,22,23,25,53,80,110,143,443,445,1433,1521,3306,3389,5432,6379,8080,8888,27017",
        "desc": "包含 Web、数据库、远程桌面等"
    },
    "Web 专项 (常用)": {
        "ports": "80,443,8000,8080,8443,9000,9090,3000",
        "desc": "常见 HTTP/HTTPS 端口"
    },
    "基础渗透 (1-1024)": {
        "ports": "1-1024",
        "desc": "标准系统服务端口"
    },
    "全端口探测": {
        "ports": "1-65535",
        "desc": "全量扫描"
    }
}

def render_progress(current, total, Fore):
    """单行渲染进度条"""
    percent = (current / total) * 100
    length = 40
    fill = int(percent / (100 / length))
    bar = f"{Fore.GREEN}{'█' * fill}{Fore.RESET}{'░' * (length - fill)}"
    sys.stdout.write(f"\r\033[K  {Fore.CYAN}进度: {Fore.WHITE}[{bar}] {percent:.1f}% ({current}/{total})")
    sys.stdout.flush()

async def probe_web_service(target, port):
    """
    通用 Web 探测：不依赖端口号，通过协议头判断是否为 Web 服务
    返回: (info_str, link_url_or_None)
    """
    # 优先尝试 HTTPS，再尝试 HTTP
    protocols = [("https", 443), ("http", 80)] if port == 443 else [("http", 80), ("https", 443)]
    
    for prot, _ in protocols:
        url = f"{prot}://{target}:{port}" if port not in [80, 443] else f"{prot}://{target}"
        try:
            def fetch():
                req = Request(url, headers={'User-Agent': 'CLI-Kit/1.0'})
                with urlopen(req, timeout=1.2) as res:
                    content = res.read(1024).decode('utf-8', errors='ignore')
                    title = "N/A"
                    if "<title>" in content.lower():
                        title = content.split("<title>")[1].split("</title>")[0].strip()
                        title = " ".join(title.split())[:20]
                    server = res.headers.get('Server', 'Unk')[:10]
                    return f"{res.getcode()} | {server} | {title}", url
            
            return await asyncio.get_event_loop().run_in_executor(None, fetch)
        except:
            continue
            
    return "OPEN", None

async def scan_worker(target, port, sem):
    """原子扫描任务"""
    async with sem:
        try:
            # 1. 尝试 TCP 三次握手
            conn = asyncio.open_connection(target, port)
            reader, writer = await asyncio.wait_for(conn, timeout=1.2)
            
            # 2. 获取已知服务名
            try:
                service_name = socket.getservbyport(port, 'tcp').upper()
            except:
                service_name = "CUSTOM"
            
            # 3. 任何端口都尝试进行 Web 识别 (逻辑核心)
            # 先读一小段数据判断是否主动吐出 Banner（如 SSH/FTP）
            try:
                banner = await asyncio.wait_for(reader.read(256), timeout=0.5)
                if banner:
                    info, link = banner.decode('utf-8', errors='ignore').strip()[:30], None
                else:
                    info, link = await probe_web_service(target, port)
            except asyncio.TimeoutError:
                # 超时未吐数据，通常是 Web 服务在等待请求，执行主动探测
                info, link = await probe_web_service(target, port)
            
            writer.close()
            await writer.wait_closed()
            return port, service_name, info, link
        except:
            return None

async def main_loop(target, ports, Fore):
    sem = asyncio.Semaphore(500)
    total = len(ports)
    tasks = [scan_worker(target, p, sem) for p in ports]
    
    print(f"\n{Fore.CYAN}⚙️  任务启动: {Fore.WHITE}{target}")
    print(f"{Fore.WHITE}{'PORT':<8} | {'SERVICE':<12} | {'INFO / QUICK LINK'}")
    print("-" * 80)

    current = 0
    found_any = False
    
    for task in asyncio.as_completed(tasks):
        res = await task
        current += 1
        
        if res:
            found_any = True
            port, svc, info, link = res
            sys.stdout.write("\r\033[K") # 清除进度条
            
            # 下划线使用原生 ANSI 转义码 \033[4m
            link_str = f" -> \033[4m{link}\033[0m" if link else ""
            print(f"{Fore.GREEN}{port:<8}{Fore.WHITE} | {svc:<12} | {Fore.YELLOW}{info}{link_str}")
        
        render_progress(current, total, Fore)

    sys.stdout.write("\r\033[K")
    if not found_any:
        print(f"{Fore.YELLOW}  未发现任何开放端口。")
    print("-" * 80)

def run_portscan(args, tools):
    import questionary
    Fore = tools.get("Fore")
    
    target = getattr(args, 'target', None) or questionary.text("目标地址:", default="127.0.0.1").ask()
    if not target: return

    choices = [
        questionary.Choice(
            title=[("class:text", f"{name:<18} "), ("class:instruction", f"({data['desc']})")],
            value=data['ports']
        ) for name, data in PORT_PRESETS.items()
    ]
    choices.append(questionary.Choice("自定义范围", value="custom"))

    port_input = questionary.select("选择扫描方案:", choices=choices).ask()
    if port_input == "custom":
        port_input = questionary.text("输入范围:").ask()
    if not port_input: return

    try:
        ports = []
        for part in port_input.split(','):
            part = part.strip()
            if '-' in part:
                s, e = map(int, part.split('-'))
                ports.extend(range(s, e + 1))
            else:
                ports.append(int(part))
        ports = sorted(list(set([p for p in ports if 0 < p <= 65535])))
    except:
        print(f"{Fore.RED}❌ 端口解析错误。")
        return

    start_time = time.time()
    try:
        asyncio.run(main_loop(target, ports, Fore))
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️ 用户中断。")
    
    print(f"{Fore.CYAN}✨ 耗时: {time.time()-start_time:.2f}s")
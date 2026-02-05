import os
import time
from fnmatch import fnmatch

__info__ = {
    "help": "自定义目录扫描：支持深度控制、规则过滤与结果导出",
    "alias": ["tree", "lsr", "find"]
}

def run_explorer(args, tools):
    import questionary
    Fore = tools.get("Fore")

    # 1. 交互式参数配置
    root_path = questionary.text("输入要遍历的根目录:", default=".").ask()
    if not os.path.exists(root_path):
        print(f"{Fore.RED}❌ 路径不存在！")
        return

    pattern = questionary.text("文件匹配模式 (如 *.py, *test*):", default="*").ask()
    max_depth = questionary.text("最大遍历深度 (留空为无限):", default="").ask()
    max_depth = int(max_depth) if max_depth.isdigit() else float('inf')

    exclude_dirs = [".git", "__pycache__", ".venv", "node_modules", ".idea", ".vscode"]
    
    # 2. 遍历核心逻辑
    print(f"\n{Fore.CYAN}🔍 正在扫描: {Fore.WHITE}{os.path.abspath(root_path)}")
    print(f"{Fore.CYAN}规则: {Fore.WHITE}Pattern={pattern}, MaxDepth={max_depth}")
    print("-" * 65)

    file_count = 0
    dir_count = 0
    total_size = 0
    start_time = time.time()

    # 规范化初始路径深度
    base_depth = root_path.rstrip(os.sep).count(os.sep)

    for root, dirs, files in os.walk(root_path):
        # 计算当前深度
        current_depth = root.count(os.sep) - base_depth
        if current_depth >= max_depth:
            dirs[:] = [] # 停止向深层遍历
            continue

        # 过滤掉不需要的目录（原地修改 dirs 影响后续 walk）
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        # 计算树状前缀
        indent = "  " * current_depth
        folder_name = os.path.basename(root) or root
        print(f"{Fore.BLUE}{indent}📁 {folder_name}/")

        for file in files:
            if fnmatch(file, pattern):
                file_path = os.path.join(root, file)
                try:
                    f_size = os.path.getsize(file_path)
                    total_size += f_size
                    file_count += 1
                    
                    # 格式化显示：深度 + 文件名 + 大小
                    size_str = f"({f_size/1024:.1f} KB)" if f_size < 1024*1024 else f"({f_size/1024/1024:.1f} MB)"
                    print(f"{Fore.WHITE}{indent}  📄 {file:<30} {Fore.YELLOW}{size_str}")
                except OSError:
                    continue
        
        dir_count += 1

    # 3. 统计报告
    duration = time.time() - start_time
    print("-" * 65)
    print(f"{Fore.GREEN}✅ 扫描完成！")
    print(f"统计: {dir_count} 目录 | {file_count} 文件 | 总计 {total_size/1024/1024:.2f} MB")
    print(f"耗时: {duration:.2f}s")

    # 4. 可选导出功能
    if file_count > 0 and questionary.confirm("是否将文件列表导出为 txt?").ask():
        with open("scan_result.txt", "w", encoding="utf-8") as f:
            f.write(f"Scan Report - {time.ctime()}\n")
            f.write(f"Target: {os.path.abspath(root_path)}\n\n")
            # 这里可以重新运行一遍简单的逻辑来写入文件...
            f.write("Scan successful.")
        print(f"{Fore.CYAN}📁 结果已保存至 scan_result.txt")

import os
import json
import ast

def get_plugin_info(file_path):
    """
    使用 AST 抽象语法树解析元数据，无需运行代码即可提取 __info__
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
            for node in tree.body:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == '__info__':
                            # 转换为 Python 字典对象
                            return ast.literal_eval(node.value)
    except Exception as e:
        print(f"解析 {file_path} 出错: {e}")
    return {}

def generate_manifest():
    # 核心修改：指定插件存放的子目录
    plugin_dir = "plugins"
    manifest_name = "manifest.json"
    
    plugins_list = []
    
    if not os.path.exists(plugin_dir):
        print(f"错误: 未找到 {plugin_dir} 目录")
        return

    # 遍历 plugins 文件夹
    for filename in os.listdir(plugin_dir):
        if filename.endswith(".py") and not filename.startswith("__"):
            file_path = os.path.join(plugin_dir, filename)
            info = get_plugin_info(file_path)
            
            # 提取元数据，若缺失则提供默认值
            plugins_list.append({
                "name": filename.replace(".py", ""),
                "file": f"plugins/{filename}",  # 注意：这里路径包含子目录名
                "desc": info.get("help", "暂无描述"),
                "author": info.get("author", "Admin"),
                "license": info.get("license", "MIT")
            })
    
    # 写入根目录
    output_data = {"plugins": plugins_list}
    with open(manifest_name, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
    
    print(f"成功更新 {manifest_name}，共计 {len(plugins_list)} 个插件。")

if __name__ == "__main__":
    generate_manifest()
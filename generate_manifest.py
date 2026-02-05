import os
import json
import importlib.util

def extract_mod_info(file_path, filename):
    """动态加载模块并提取 __info__"""
    module_name = filename[:-3]
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        
        if hasattr(mod, "__info__"):
            info = mod.__info__
            return {
                "name": module_name,
                "file": f"plugins/{filename}",
                "desc": info.get("help", "无描述"),
                "alias": info.get("alias", []),
                "author": info.get("author", "Community")
            }
    except Exception as e:
        print(f"⚠️  解析 {filename} 失败: {e}")
    return None

def main():
    plugins_dir = "plugins"
    manifest_path = "manifest.json"
    
    plugin_list = []
    if os.path.exists(plugins_dir):
        for filename in sorted(os.listdir(plugins_dir)):
            if filename.endswith(".py") and not filename.startswith("__"):
                info = extract_mod_info(os.path.join(plugins_dir, filename), filename)
                if info:
                    plugin_list.append(info)

    manifest_data = {
        "version": "1.0.0",
        "total": len(plugin_list),
        "plugins": plugin_list
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已成功更新 manifest.json，共 {len(plugin_list)} 个插件。")

if __name__ == "__main__":
    main()
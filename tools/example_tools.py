# tools/example_tools.py
import datetime
import os
import json

def get_current_time():
    """获取当前日期和时间"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"当前时间是: {now}"

# 设置工具元数据
get_current_time.tool_name = "get_current_time"
get_current_time.tool_description = "获取当前的日期和时间"
get_current_time.tool_parameters = {
    "type": "object",
    "properties": {},
    "required": []
}


def read_file(filename: str):
    """安全地读取本地文本文件内容（仅限当前目录及子目录）"""
    # 安全检查：禁止路径遍历（如 ../../etc/passwd）
    safe_path = os.path.abspath(os.path.join(".", filename))
    if not safe_path.startswith(os.path.abspath(".")):
        return "❌ 错误：不允许访问项目目录之外的文件。"
    
    try:
        with open(safe_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return f"文件 {filename} 的内容：\n{content}"
    except Exception as e:
        return f"❌ 读取文件失败: {str(e)}"

read_file.tool_name = "read_file"
read_file.tool_description = "读取指定文本文件的内容（仅限当前项目目录内）"
read_file.tool_parameters = {
    "type": "object",
    "properties": {
        "filename": {
            "type": "string",
            "description": "要读取的文件名，例如 'notes.txt'"
        }
    },
    "required": ["filename"]
}
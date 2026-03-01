# agent.py (更新版)
import os
import requests
import json
import re
from dotenv import load_dotenv
from typing import List, Callable, Any, Dict

# 自动加载 tools/ 下的所有工具
from tools.example_tools import get_current_time, read_file

load_dotenv()

class Agent:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        
        if not self.api_key:
            raise ValueError("❌ Missing LLM_API_KEY in .env file!")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 注册工具（手动注册，后续可自动扫描）
        self.tools: Dict[str, Callable] = {
            get_current_time.tool_name: get_current_time,
            read_file.tool_name: read_file,
        }

        # 构建工具描述（用于 prompt）
        self.tool_descriptions = self._build_tool_descriptions()

        self.messages = []

    def _build_tool_descriptions(self) -> str:
        """生成工具描述字符串，插入到 system prompt 中"""
        desc = "你可以使用以下工具来帮助用户：\n"
        for name, func in self.tools.items():
            params = func.tool_parameters.get("properties", {})
            param_str = ", ".join([f"{k}: {v.get('description', '')}" for k, v in params.items()])
            desc += f"- {name}({param_str}): {func.tool_description}\n"
        desc += (
            "\n当你需要使用工具时，请严格按以下 JSON 格式回复（不要包含其他文字）：\n"
            '{"tool": "工具名", "args": {参数键值对}}\n'
            "如果不需要工具，直接回答用户问题。"
        )
        return desc

    def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """安全执行工具"""
        if tool_name not in self.tools:
            return f"❌ 工具 '{tool_name}' 不存在。"
        try:
            func = self.tools[tool_name]
            # 调用函数（支持有参/无参）
            if args:
                result = func(**args)
            else:
                result = func()
            return str(result)
        except Exception as e:
            return f"❌ 执行工具 '{tool_name}' 时出错: {str(e)}"

    def chat(self, user_message: str) -> str:
        # 首次对话加入 system prompt
        if not self.messages:
            self.messages.append({
                "role": "system",
                "content": (
                    "你是一个运行在用户本地电脑上的智能助手。"
                    + self.tool_descriptions
                )
            })

        self.messages.append({"role": "user", "content": user_message})

        max_turns = 5  # 防止无限循环
        turn = 0

        while turn < max_turns:
            payload = {
                "model": self.model,
                "messages": self.messages,
                "temperature": 0.7
            }

            try:
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                reply = data["choices"][0]["message"]["content"].strip()

                # 尝试解析是否为工具调用
                tool_call = None
                try:
                    # 提取 JSON 块（兼容模型可能加 ```json ... ```）
                    json_match = re.search(r"```(?:json)?(.*?)```", reply, re.DOTALL)
                    json_str = json_match.group(1) if json_match else reply
                    parsed = json.loads(json_str.strip())
                    if "tool" in parsed and "args" in parsed:
                        tool_call = parsed
                except (json.JSONDecodeError, AttributeError):
                    pass

                if tool_call:
                    tool_name = tool_call["tool"]
                    args = tool_call.get("args", {})
                    observation = self._execute_tool(tool_name, args)
                    
                    # 将工具调用和结果加入上下文
                    self.messages.append({"role": "assistant", "content": reply})
                    self.messages.append({
                        "role": "user",
                        "content": f"[工具执行结果]: {observation}"
                    })
                    
                    # 继续让模型生成最终回答
                    turn += 1
                    continue
                else:
                    # 正常回答
                    self.messages.append({"role": "assistant", "content": reply})
                    return reply

            except Exception as e:
                error_msg = f"⚠️ 调用失败: {e}"
                print(error_msg)
                return error_msg

        return "❌ 对话轮次超限，请简化问题。"
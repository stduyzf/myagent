import os
from typing import Dict, Any, Callable
import requests
from dotenv import load_dotenv
from serpapi import SerpApiClient
load_dotenv()

class ToolExecutor:
    """
    一个工具执行器，负责管理和执行工具。
    """
    def __init__(self):
        self.tools: Dict[str, Dict[str,Any]] = {}

    def register_tool(self, name:str, description:str, func:Callable):
        """
        注册一个新工具
        """
        if name in self.tools:
            print(f"警告:工具 '{name}' 已存在，将被覆盖。")
        self.tools[name] = {"description": description, "func": func}
        print(f"工具{name}已注册")

    def get_tool(self, name:str) -> callable:
        """
        根据名称获得执行函数
        """
        return self.tools.get(name,{}).get("func")

    def getAvailableTools(self) -> str:
        """
        获取所有可用工具的格式化描述字符串。
        """
        res = "\n"
        for name, tool in self.tools.items():
            res.join(tool["description"])
        return res

def search(query:str) -> str:
    """
        一个基于SerpApi的实战网页搜索引擎工具。
        它会智能地解析搜索结果，优先返回直接答案或知识图谱信息。
    """
    try:
        api_key = os.getenv("SERPAPI_API_KEY")
        if api_key is None:
            return "错误:SERPAPI_API_KEY 未在 .env copy 文件中配置。"
        params = {
            "engine": "google",
            "q": query,  # <--- 使用 'query'
            "gl": "cn",  # 国家代码
            "hl": "zh-cn",  # 语言代码
            "api_key": api_key  # <--- api_key 放在这里
        }

        client = SerpApiClient(params_dict=params)
        results = client.get_dict()

        # 智能解析:优先寻找最直接的答案
        if "answer_box_list" in results:
            return "\n".join(results["answer_box_list"])
        if "answer_box" in results and "answer" in results["answer_box"]:
            return results["answer_box"]["answer"]
        if "knowledge_graph" in results and "description" in results["knowledge_graph"]:
            return results["knowledge_graph"]["description"]
        if "organic_results" in results and results["organic_results"]:
            # 如果没有直接答案，则返回前三个有机结果的摘要
            snippets = [
                f"[{i + 1}] {res.get('title', '')}\n{res.get('snippet', '')}"
                for i, res in enumerate(results["organic_results"][:3])
            ]
            return "\n\n".join(snippets)

        return f"对不起，没有找到关于 '{query}' 的信息。"

    except Exception as e:
        return f"搜索时发生错误: {e}"

def calculator(task:str)->str:
    """
    一个基于Wolfram Alpha实现的计算工具
    输出想要计算的文本即可
    """
    url = "http://api.wolframalpha.com/v2/query"
    params = {
        "input": task,
        "appid": "QPL79REY3K",
        "format": "plaintext",
        "output": "json",
        "podstate": "Result__Step-by-step solution",  # 可获取步骤
    }
    resp = requests.get(url, params=params).json()
    if not resp["queryresult"]["success"]:
        return "计算失败或无结果"
    result_text=""
    for pod in resp["queryresult"]["pods"]:
        if "Result" in pod["title"] or "Decimal" in pod["title"]:
            result_text = pod["subpods"][0]["plaintext"]
            break
    return result_text.strip() if result_text else "未找到结果"

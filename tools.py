import os
from typing import Dict, Any, Callable

from dotenv import load_dotenv
from serpapi import SerpApiClient


load_dotenv()
#第一个工具是 search 函数，它的作用是接收一个查询字符串，然后返回搜索结果。
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
class ToolExecutor:
    """
    一个工具执行类
    """
    def __init__(self):
        self.tools: Dict[str, Dict[str,Any]] = {}

    def register_tool(self, name: str, description:str,func: Callable):
        """
        注册新工具
        """
        if name in self.tools:
            print(f"警告：工具‘{name}’已存在，将被覆盖")
        self.tools[name] = {"description": description, "func": func}
        print(f"工具‘{name}'已注册")

    def get_tool(self, name:str) -> callable:
        return self.tools.get(name,{}).get("func")

    def getAvailableTools(self) -> str:
        """
        获得所有可用工具的格式化描述字符串
        :return:
        """
        return "\n".join([
            f"-{name}:{info['description']}" for name, info in self.tools.items()
        ])

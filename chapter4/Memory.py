from typing import Dict, List, Any, Optional



class Memory:
    """
    短期记忆模块
    这个 Memory 类的设计比较简洁，主体是这样的：

    使用一个列表 records 来按顺序存储每一次的行动和反思。
    add_record 方法负责向记忆中添加新的条目。
    get_trajectory 方法是核心，它将记忆轨迹“序列化”成一段文本，可以直接插入到后续的提示词中，为模型的反思和优化提供完整的上下文。
    get_last_execution 方便我们获取最新的“初稿”以供反思。
    """
    def __init__(self):
        self.records: List[Dict[str, Any]] = []

    def add_record(self,record_type:str, content:str):
        """
        向记忆中添加一条新记录。

        参数:
        - record_type (str): 记录的类型 ('execution' 或 'reflection')。
        - content (str): 记录的具体内容 (例如，生成的代码或反思的反馈)。
        """
        record = {"type":record_type, "content":content}
        self.records.append(record)
        print(f"📝 记忆已更新，新增一条 '{record_type}' 记录。")

    def get_trajectory(self)-> str:
        """
        将所有记忆记录格式化为一个连贯的字符串文本，用于构建提示词。
        """
        trajectory = []
        for record in self.records:
            if record["type"] == "execution":
                trajectory.append(f"--- 上一轮尝试 (代码) ---\n{record['content']}")
            elif record["type"] == "reflection":
                trajectory.append(f"--- 评审员反馈 ---\n{record['content']}")
        return "\n\n".join(trajectory)

    def get_last_execution(self) -> Optional[str]:
        """
        获取最近一次的执行结果 (例如，最新生成的代码)。
        如果不存在，则返回 None。
        """
        for record in reversed(self.records):
            if record["type"] == "execution":
                return record["content"]
        return None
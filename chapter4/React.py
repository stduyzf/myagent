import re
from chapter4.LLM_client import HelloAgentsLLM
from tools import ToolExecutor, search

# (此处省略 REACT_PROMPT_TEMPLATE 的定义)
REACT_PROMPT_TEMPLATE = """
请注意，你是一个有能力调用外部工具的智能助手。

可用工具如下：
{tools}

请严格按照以下格式进行回应：

Thought: 你的思考过程，用于分析问题、拆解任务和规划下一步行动。
Action: 你决定采取的行动，必须是以下格式之一：
- `{{tool_name}}[{{tool_input}}]`：调用一个可用工具。
- `Finish[最终答案]`：当你认为已经获得最终答案时。
- 当你收集到足够的信息，能够回答用户的最终问题时，你必须在`Action:`字段后使用 `finish(answer="...")` 来输出最终答案。


现在，请开始解决以下问题：
Question: {question}
History: {history}
"""


class ReActAgent:
    def __init__(self, llm_client: HelloAgentsLLM, tool_executor: ToolExecutor, max_steps: int = 10):
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.max_steps = max_steps
        self.history = []

    def run(self, question: str):
        self.history = []
        current_step = 0

        while current_step < self.max_steps:
            current_step += 1
            print(f"\n--- 第 {current_step} 步 ---")

            tools_desc = self.tool_executor.getAvailableTools()
            history_str = "\n".join(self.history)
            prompt = REACT_PROMPT_TEMPLATE.format(tools=tools_desc, question=question, history=history_str)

            messages = [{"role": "user", "content": prompt}]
            response_text = self.llm_client.think(messages=messages)
            if not response_text:
                print("错误：LLM未能返回有效响应。")
                break

            thought, action = self._parse_output(response_text)
            if thought: print(f"🤔 思考: {thought}")
            if not action: print("警告：未能解析出有效的Action，流程终止。"); break

            if action.startswith("Finish"):

                # --- 关键修正 V2 ---

                # 检查 Thought 是否是一个“计划”而不是“答案”
                # (这里我们用简单的关键词来判断)
                is_plan = False
                if thought:
                    planning_keywords = ["我需要", "我应该", "下一步", "提取"]
                    if any(keyword in thought for keyword in planning_keywords):
                        is_plan = True

                # 尝试从 Finish[] 括号中获取答案
                match = re.match(r"Finish\[(.*)\]", action, re.DOTALL)
                answer_in_bracket = match.group(1).strip() if match else ""

                # 逻辑判断：
                # 1. 如果括号里有答案，优先使用
                if answer_in_bracket:
                    print(f"✅ 最终答案 (来自 Finish[]): {answer_in_bracket}")
                    return answer_in_bracket

                # 2. 如果括号里没答案，但 Thought 看起来是答案 (不是计划)
                elif thought and not is_plan:
                    print(f"✅ 最终答案 (来自 Thought): {thought}")
                    return thought

                # 3. 如果括号里没答案，且 Thought 看起来是个计划 (LLM 矛盾了)
                else:
                    print("警告: LLM 尝试在未完成时 Finish，强制继续。")
                    # 无视 Finish，把这个错误的 Thought 当作 Observation
                    observation = f"错误: 你的 Thought 是一个计划 ({thought})，但你却调用了 Finish。你必须先完成计划。"

                    # (这部分代码与下面的 'else' 分支重复，但为了清晰起见，我们保留它)
                    print(f"👀 观察: {observation}")
                    self.history.append(f"Action: {action} (被否决)")
                    self.history.append(f"Observation: {observation}")
                    continue  # 继续下一次循环，而不是 break

            tool_name, tool_input = self._parse_action(action)
            if not tool_name or not tool_input:
                self.history.append("Observation: 无效的Action格式，请检查。")
                continue

            print(f"🎬 行动: {tool_name}[{tool_input}]")
            tool_function = self.tool_executor.get_tool(tool_name)
            observation = tool_function(tool_input) if tool_function else f"错误：未找到名为 '{tool_name}' 的工具。"

            print(f"👀 观察: {observation}")
            self.history.append(f"Action: {action}")
            self.history.append(f"Observation: {observation}")

        print("已达到最大步数，流程终止。")
        return None

    def _parse_output(self, text: str):
        thought_match = re.search(r"Thought: (.*)", text)
        action_match = re.search(r"Action: (.*)", text)
        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
        return thought, action

    def _parse_action(self, action_text: str):
        match = re.match(r"(\w+)\[(.*)\]", action_text)
        return (match.group(1), match.group(2)) if match else (None, None)

    def _parse_action_input(self, action_text: str):
        match = re.match(r"\w+\[(.*)\]", action_text)
        return match.group(1) if match else ""


if __name__ == '__main__':
    llm = HelloAgentsLLM()
    tool_executor = ToolExecutor()
    search_desc = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
    tool_executor.register_tool("Search", search_desc, search)
    agent = ReActAgent(llm_client=llm, tool_executor=tool_executor)
    question = "华为最新的手机是哪一款？它的主要卖点是什么？"
    agent.run(question)
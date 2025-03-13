"""
Agent模块，实现银行客服智能体
"""
from typing import Dict, Any, List, Tuple, Optional, TypedDict, Union
from langgraph.graph import StateGraph, END
from langsmith.run_helpers import traceable
from langsmith import Client
from loguru import logger

from src.tools import RAGTool, ModelTool, WebSearchTool
from src.config import LANGCHAIN_PROJECT

class AgentState(TypedDict):
    """智能体状态类型定义"""
    query: str
    chat_history: List[Dict[str, str]]  # 添加对话历史
    tool_choice: Optional[str]
    tool_result: Optional[str]
    response: Optional[str]

class BankServiceAgent:
    """银行客服智能体"""
    
    def __init__(self):
        self.rag_tool = RAGTool()
        self.model_tool = ModelTool()
        self.web_search_tool = WebSearchTool()
        self.workflow = self._create_workflow()
        self.client = Client()  # LangSmith 客户端
        self.chat_history = []  # 存储对话历史
    
    def _create_workflow(self) -> StateGraph:
        """创建工作流程图"""
        # 定义工作流
        workflow = StateGraph(AgentState)
        
        # 定义节点
        workflow.add_node("analyze_query", self._analyze_query)
        workflow.add_node("use_rag", self._use_rag)
        workflow.add_node("use_model", self._use_model)
        workflow.add_node("use_web_search", self._use_web_search)
        workflow.add_node("generate_response", self._generate_response)
        
        # 定义边
        workflow.add_edge("analyze_query", "use_rag")
        workflow.add_edge("analyze_query", "use_model")
        workflow.add_edge("analyze_query", "use_web_search")
        workflow.add_edge("use_rag", "generate_response")
        workflow.add_edge("use_model", "generate_response")
        workflow.add_edge("use_web_search", "generate_response")
        workflow.add_edge("generate_response", END)
        
        # 设置工作流的入口节点
        workflow.set_entry_point("analyze_query")
        
        # 编译工作流
        return workflow.compile()
    
    @traceable(name="analyze_query", run_type="chain", project_name=LANGCHAIN_PROJECT)
    def _analyze_query(self, state: AgentState) -> AgentState:
        """分析用户查询，决定使用哪个工具"""
        query = state["query"]
        
        # 构建包含历史上下文的提示词
        context = "之前的对话：\n"
        if self.chat_history:
            for msg in self.chat_history[-3:]:  # 只使用最近的3轮对话作为上下文
                context += f"{msg['role']}: {msg['content']}\n"
        
        # 调用模型来决定使用哪个工具
        prompt = f"""
        请分析以下用户查询，并决定使用哪个工具来回答。

        {context}
        当前查询: {query}

        可用工具及其使用场景:
        1. 知识库文档 (RAG)
           - 银行标准业务流程（开户、贷款等）
           - 固定政策信息（利率、费率等）
           - 产品详细说明（理财、信用卡等）
           - 内部规章制度
           适用问题示例：
           - "办理房贷需要什么材料？"
           - "你们银行有哪些理财产品？"

        2. 模型直接回答 (MODEL)
           - 需要推理或建议的问题
           - 个性化咨询
           - 简单的解释说明
           适用问题示例：
           - "我应该选择哪种理财产品？"
           - "如何提高信用卡额度？"

        3. 网络搜索 (SEARCH)
           - 需要最新市场信息
           - 实时金融数据
           - 最新政策变化
           适用问题示例：
           - "今天的美元汇率是多少？"
           - "最近的存款利率政策有什么变化？"

        请根据问题特点和对话上下文选择最合适的工具，只返回: RAG, MODEL, 或 SEARCH
        """
        
        tool_choice = self.model_tool.query(prompt).strip().upper()
        state["tool_choice"] = tool_choice
        state["chat_history"] = self.chat_history
        return state
    
    @traceable(name="use_rag", run_type="chain", project_name=LANGCHAIN_PROJECT)
    def _use_rag(self, state: AgentState) -> Optional[AgentState]:
        """使用RAG工具"""
        if state["tool_choice"] != "RAG":
            return None
        
        result = self.rag_tool.query(state["query"])
        state["tool_result"] = result
        return state
    
    @traceable(name="use_model", run_type="chain", project_name=LANGCHAIN_PROJECT)
    def _use_model(self, state: AgentState) -> Optional[AgentState]:
        """使用模型工具"""
        if state["tool_choice"] != "MODEL":
            return None
        
        result = self.model_tool.query(state["query"])
        state["tool_result"] = result
        return state
    
    @traceable(name="use_web_search", run_type="chain", project_name=LANGCHAIN_PROJECT)
    def _use_web_search(self, state: AgentState) -> Optional[AgentState]:
        """使用网络搜索工具"""
        if state["tool_choice"] != "SEARCH":
            return None
        
        result = self.web_search_tool.search(state["query"])
        state["tool_result"] = result
        return state
    
    @traceable(name="generate_response", run_type="chain", project_name=LANGCHAIN_PROJECT)
    def _generate_response(self, state: AgentState) -> AgentState:
        """生成最终响应"""
        # 构建包含历史上下文的提示词
        context = "之前的对话：\n"
        if self.chat_history:
            for msg in self.chat_history[-3:]:  # 只使用最近的3轮对话作为上下文
                context += f"{msg['role']}: {msg['content']}\n"
        
        prompt = f"""
        {context}
        基于以下信息生成专业、友好的银行客服回答：
        
        用户问题: {state['query']}
        工具结果: {state['tool_result']}
        
        请确保回答：
        1. 专业且准确
        2. 语气友好
        3. 结构清晰
        4. 考虑对话上下文
        5. 如有必要，提供后续建议
        """
        
        response = self.model_tool.query(prompt)
        state["response"] = response
        
        # 更新对话历史
        self.chat_history.append({"role": "user", "content": state["query"]})
        self.chat_history.append({"role": "assistant", "content": response})
        
        # 保持对话历史在合理长度
        if len(self.chat_history) > 10:  # 保留最近5轮对话
            self.chat_history = self.chat_history[-10:]
        
        return state
    
    @traceable(name="chat", run_type="chain", project_name=LANGCHAIN_PROJECT)
    def chat(self, query: str) -> str:
        """处理用户查询"""
        try:
            state: AgentState = {
                "query": query,
                "chat_history": self.chat_history,
                "tool_choice": None,
                "tool_result": None,
                "response": None
            }
            final_state = self.workflow.invoke(state)
            return final_state["response"]
        except Exception as e:
            logger.error(f"处理查询时出错: {str(e)}")
            return "抱歉，处理您的请求时出现了错误。请稍后再试或联系人工客服。" 
"""
Streamlit应用界面
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

import streamlit as st
from loguru import logger
from langsmith import Client

# 在导入其他模块之前设置环境变量
# os.environ["PYTORCH_JIT"] = "0"  # 禁用JIT以避免某些问题
# if "CUDA_VISIBLE_DEVICES" not in os.environ:
#     os.environ["CUDA_VISIBLE_DEVICES"] = ""  # 强制使用CPU

from src.agent import BankServiceAgent
from src.config import (
    validate_config,
    LANGCHAIN_API_KEY,
    LANGCHAIN_PROJECT,
    LANGCHAIN_ENDPOINT,
    GOOGLE_API_KEY,
    GOOGLE_CSE_ID,
    DEEPSEEK_API_KEY
)

def initialize_langsmith():
    """初始化 LangSmith"""
    try:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = LANGCHAIN_PROJECT
        os.environ["LANGCHAIN_ENDPOINT"] = LANGCHAIN_ENDPOINT
        
        client = Client()
        logger.info("成功初始化 LangSmith")
        return client
    except Exception as e:
        logger.error(f"初始化 LangSmith 失败: {str(e)}")
        return None

def initialize_agent():
    """初始化智能体"""
    if "agent" not in st.session_state:
        try:
            validate_config()
            # 初始化 LangSmith
            initialize_langsmith()
            st.session_state.agent = BankServiceAgent()
            logger.info("成功初始化智能体")
        except Exception as e:
            logger.error(f"初始化失败: {str(e)}")
            st.error(f"初始化失败: {str(e)}")
            st.stop()

# 页面配置
st.set_page_config(
    page_title="银行智能客服",
    page_icon="🏦",
    layout="wide"
)

# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []
    welcome_message = {
        "role": "assistant",
        "content": """👋 您好！我是您的智能银行客服助手。

我可以帮您：
- 📝 解答银行业务相关问题
- 💰 提供理财产品咨询
- 🏠 介绍贷款办理流程
- 💳 解答信用卡相关问题
- 🌐 查询最新金融资讯

请问有什么可以帮您？"""
    }
    st.session_state.messages.append(welcome_message)

# 确保在主线程中初始化智能体
initialize_agent()

# 页面标题
st.title("🏦 银行智能客服")

# 侧边栏
with st.sidebar:
    st.title("💡 使用说明")
    st.markdown("""
    ### 我可以帮您解答以下问题：
    1. 账户相关问题
    2. 理财产品咨询
    3. 贷款业务咨询
    4. 信用卡服务
    5. 网银操作指导
    
    ### 功能说明
    - 知识库问答：可回答已上传文档中的信息
    - 网络搜索：可查询最新的金融市场信息
    - 智能推理：可针对具体情况给出建议
    
    ### 温馨提示
    - 请勿透露个人敏感信息
    - 复杂业务建议前往柜台办理
    - 如需人工服务，请拨打95588
    """)
    
    # 文档上传部分
    st.title("📚 知识库管理")
    
    status_placeholder = st.empty()
    # 显示知识库状态
    if "agent" in st.session_state and st.session_state.agent.rag_tool.vector_store:
        status_placeholder.success("✅ 知识库已加载")
    else:
        status_placeholder.warning("⚠️ 知识库未加载，请上传文档")
    
    uploaded_files = st.file_uploader(
        "上传文档到知识库",
        accept_multiple_files=True,
        type=["txt", "md", "pdf"],
        help="支持txt、markdown和PDF格式的文档"
    )
    
    if uploaded_files:
        status_placeholder.success("✅ 知识库已加载")
        if st.button("处理上传的文档"):
            with st.spinner("正在处理文档..."):
                try:
                    result = st.session_state.agent.rag_tool.load_documents(uploaded_files)
                    st.success(result)
                except Exception as e:
                    st.error(f"处理文档失败: {str(e)}")
    
    # 显示功能状态
    st.title("🔧 功能状态")
    col1, col2 = st.columns(2)
    with col1:
        if GOOGLE_API_KEY and GOOGLE_CSE_ID:
            st.success("✅ 网络搜索")
        else:
            st.error("❌ 网络搜索未配置")
    with col2:
        if DEEPSEEK_API_KEY:
            st.success("✅ AI对话")
        else:
            st.error("❌ AI对话未配置")
    
    # 清除会话按钮
    if st.button("清除会话历史"):
        st.session_state.messages = []
        st.rerun()

# 显示聊天历史
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 用户输入
if prompt := st.chat_input("请输入您的问题"):
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 生成回答
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            try:
                response = st.session_state.agent.chat(prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                error_msg = f"处理请求时出错: {str(e)}"
                logger.error(error_msg)
                st.error(error_msg) 
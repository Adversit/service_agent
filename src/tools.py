"""
工具模块，包含所有可用的工具实现
"""
from typing import Dict, Any, List, Optional
import numpy as np
import requests
from pathlib import Path
import faiss
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.document import Document
from langchain.embeddings.base import Embeddings
from langsmith.run_helpers import traceable
from loguru import logger
import torch
import json
import time
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import httplib2
from openai import OpenAI

from src.config import (
    MODEL_NAME,
    MODEL_KWARGS,
    ENCODE_KWARGS,
    DEEPSEEK_API_KEY,
    DATA_DIR,
    GOOGLE_API_KEY,
    GOOGLE_CSE_ID,
    PROXY_HOST,
    PROXY_PORT,
    LANGCHAIN_PROJECT
)

class CustomEmbeddings(Embeddings):
    """自定义嵌入类，包装 SentenceTransformer"""
    
    def __init__(self, model: SentenceTransformer):
        self.model = model
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """生成文档嵌入"""
        with torch.no_grad():
            embeddings = self.model.encode(texts, **ENCODE_KWARGS)
        return embeddings.tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """生成查询嵌入"""
        with torch.no_grad():
            embedding = self.model.encode([text], **ENCODE_KWARGS)[0]
        return embedding.tolist()

class RAGTool:
    """基于RAG的知识库文档工具"""
    
    def __init__(self):
        try:
            logger.info(f"正在初始化模型，使用设备: {MODEL_KWARGS['device']}")
            self.model = SentenceTransformer(MODEL_NAME, **MODEL_KWARGS)
            self.embeddings = CustomEmbeddings(self.model)
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50
            )
            self.vector_store = None
            self.model_tool = ModelTool()  # 用于生成最终答案
        except Exception as e:
            logger.error(f"初始化模型失败: {str(e)}")
            raise
    
    @traceable(name="load_documents", run_type="chain", project_name=LANGCHAIN_PROJECT)
    def load_documents(self, files: List[Any]) -> str:
        """加载文档并创建向量存储
        
        Args:
            files: 上传的文件列表
            
        Returns:
            str: 处理结果信息
        """
        try:
            documents = []
            for file in files:
                try:
                    # 读取文件内容
                    text = file.getvalue().decode("utf-8")
                    # 分割文本
                    chunks = self.text_splitter.split_text(text)
                    documents.extend([Document(page_content=chunk) for chunk in chunks])
                    logger.info(f"成功处理文件: {file.name}")
                except Exception as e:
                    logger.error(f"处理文件 {file.name} 失败: {str(e)}")
                    continue
            
            if documents:
                logger.info(f"开始创建文档嵌入，共 {len(documents)} 个文档片段")
                
                # 使用自定义嵌入类创建向量存储
                self.vector_store = FAISS.from_documents(documents, self.embeddings)
                logger.info("成功创建向量存储")
                return f"成功加载 {len(documents)} 个文档片段"
            else:
                return "没有找到可处理的文档内容"
                
        except Exception as e:
            error_msg = f"处理文档时出错: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def _format_relevant_docs(self, docs: List[Document]) -> str:
        """格式化相关文档片段"""
        formatted_docs = []
        for i, doc in enumerate(docs, 1):
            formatted_docs.append(f"片段 {i}:\n{doc.page_content}\n")
        return "\n".join(formatted_docs)
    
    @traceable(name="query_rag", run_type="chain", project_name=LANGCHAIN_PROJECT)
    def query(self, question: str, k: int = 4) -> str:
        """查询知识库并生成答案
        
        Args:
            question: 用户问题
            k: 返回的相关文档数量
            
        Returns:
            str: 生成的答案
        """
        if not self.vector_store:
            return "知识库为空，请先上传并处理文档"
        
        try:
            # 第一阶段：使用 embedding 进行相似度搜索
            logger.info(f"正在搜索相关文档: {question}")
            relevant_docs = self.vector_store.similarity_search(question, k=k)
            
            if not relevant_docs:
                return "未找到相关文档"
            
            # 格式化相关文档
            context = self._format_relevant_docs(relevant_docs)
            logger.info(f"找到 {len(relevant_docs)} 个相关文档片段")
            
            # 第二阶段：使用 DeepSeek 模型生成答案
            prompt = f"""
            请基于以下文档片段回答用户的问题。
            如果文档片段中没有相关信息，请明确说明。
            如果信息不完整，请说明还需要什么信息。
            
            用户问题: {question}
            
            相关文档:
            {context}
            
            请生成准确、完整且专业的回答。回答应当：
            1. 直接回答用户问题
            2. 只使用文档中提供的信息
            3. 保持客观专业的语气
            4. 如有必要，可以组织多个片段的信息
            5. 清晰说明信息的局限性
            """
            
            logger.info("正在生成答案")
            answer = self.model_tool.query(prompt)
            logger.info("成功生成答案")
            
            return answer
            
        except Exception as e:
            error_msg = f"查询知识库时出错: {str(e)}"
            logger.error(error_msg)
            return error_msg

class ModelTool:
    """DeepSeek模型调用工具"""
    
    def __init__(self):
        """初始化 DeepSeek API 配置"""
        self.client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"
        )
    
    @traceable(name="query_model", run_type="llm", project_name=LANGCHAIN_PROJECT)
    def query(self, prompt: str) -> str:
        """调用模型API"""
        try:
            messages = [
                {"role": "system", "content": "你是一个专业的银行客服助手，请用专业、友好的语气回答用户的问题。"},
                {"role": "user", "content": prompt}
            ]
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"调用模型API失败: {str(e)}")
            return f"调用模型失败: {str(e)}"
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "deepseek-chat",
        stream: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Any:
        """
        调用 DeepSeek API 进行对话补全
        
        Args:
            messages: 对话消息列表
            model: 模型名称，默认为 "deepseek-chat"
            stream: 是否使用流式响应
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成token数
            
        Returns:
            API 响应对象
        """
        try:
            params = {
                "model": model,
                "messages": messages,
                "stream": stream
            }
            
            if temperature is not None:
                params["temperature"] = temperature
            if max_tokens is not None:
                params["max_tokens"] = max_tokens
                
            response = self.client.chat.completions.create(**params)
            return response
            
        except Exception as e:
            logger.error(f"调用模型API失败: {str(e)}")
            raise

    def get_completion_content(self, response: Any) -> str:
        """
        从API响应中提取生成的内容
        
        Args:
            response: API 响应对象
            
        Returns:
            生成的文本内容
        """
        return response.choices[0].message.content

class WebSearchTool:
    """网络搜索工具"""
    
    def __init__(self):
        """初始化Google Custom Search API服务"""
        try:
            # 创建支持代理的 HTTP 对象
            proxy_info = None
            if PROXY_HOST and PROXY_PORT:
                proxy_info = httplib2.ProxyInfo(
                    proxy_type=httplib2.socks.PROXY_TYPE_HTTP,
                    proxy_host=PROXY_HOST,
                    proxy_port=int(PROXY_PORT)
                )
                logger.info(f"使用代理设置: {PROXY_HOST}:{PROXY_PORT}")
            
            http = httplib2.Http(
                proxy_info=proxy_info,
                timeout=30
            )
            
            # 创建 Google API 客户端
            self.service = build(
                "customsearch", "v1",
                developerKey=GOOGLE_API_KEY,
                http=http
            )
            logger.info("成功初始化 Google 搜索服务")
        except Exception as e:
            logger.error(f"初始化 Google 搜索服务失败: {str(e)}")
            raise
    
    @traceable(name="web_search", run_type="tool", project_name=LANGCHAIN_PROJECT)
    def search(self, query: str, num_results: int = 5) -> str:
        """执行网络搜索
        
        Args:
            query: 搜索查询
            num_results: 返回结果数量
            
        Returns:
            str: 格式化的搜索结果
        """
        try:
            logger.info(f"开始执行搜索: {query}")
            
            # 执行搜索
            result = self.service.cse().list(
                q=query,
                cx=GOOGLE_CSE_ID,
                num=num_results
            ).execute()
            
            # 格式化结果
            if "items" not in result:
                logger.warning("未找到搜索结果")
                return "未找到相关搜索结果"
            
            formatted_results = []
            for item in result["items"]:
                title = item.get("title", "无标题")
                snippet = item.get("snippet", "无描述")
                link = item.get("link", "")
                formatted_results.append(f"标题: {title}\n描述: {snippet}\n链接: {link}\n")
            
            logger.info(f"搜索成功，找到 {len(formatted_results)} 条结果")
            return "\n".join(formatted_results)
            
        except HttpError as e:
            error_msg = f"Google搜索API调用失败: {str(e)}"
            logger.error(error_msg)
            return f"搜索失败: {str(e)}"
        except Exception as e:
            error_msg = f"执行搜索时出错: {str(e)}"
            logger.error(error_msg)
            return error_msg 
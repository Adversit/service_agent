"""
测试 Google API 的可用性
"""
import os
from pathlib import Path
import sys

# 添加项目根目录到 Python 路径
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from src.tools import WebSearchTool
from src.config import GOOGLE_API_KEY, GOOGLE_CSE_ID, PROXY_HOST, PROXY_PORT

def test_google_api():
    """测试 Google API 搜索功能"""
    print(f"\n正在测试 Google API...")
    print(f"API Key: {GOOGLE_API_KEY[:8]}..." if GOOGLE_API_KEY else "API Key 未设置")
    print(f"CSE ID: {GOOGLE_CSE_ID[:8]}..." if GOOGLE_CSE_ID else "CSE ID 未设置")
    print(f"代理设置: {PROXY_HOST}:{PROXY_PORT}" if PROXY_HOST and PROXY_PORT else "未使用代理")
    
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        print("错误：Google API 密钥或搜索引擎 ID 未配置")
        return
    
    try:
        # 创建搜索工具实例
        search_tool = WebSearchTool()
        
        # 测试搜索
        test_query = "中国工商银行最新存款利率"
        print(f"\n执行测试搜索：{test_query}")
        
        result = search_tool.search(test_query, num_results=2)
        print("\n搜索结果：")
        print(result)
        
        if "搜索失败" in result or "出错" in result:
            print("\n❌ Google API 测试失败！")
        else:
            print("\n✅ Google API 测试成功！")
        
    except Exception as e:
        print(f"\n❌ 测试失败：{str(e)}")

if __name__ == "__main__":
    test_google_api() 
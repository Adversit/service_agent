"""
测试代理连接的可用性
"""
import os
import sys
from pathlib import Path
import requests
import socket
import time
import json
from loguru import logger
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取代理配置
PROXY_HOST = os.getenv("PROXY_HOST", "127.0.0.1")
PROXY_PORT = os.getenv("PROXY_PORT", "7890")

def verify_response_content(response):
    """验证响应内容是否真的来自 Google"""
    try:
        # 检查响应头
        server = response.headers.get('Server', '').lower()
        content_type = response.headers.get('Content-Type', '').lower()
        
        # 检查响应内容
        content = response.text.lower()
        
        # Google 特征检查
        google_indicators = [
            'google' in server,
            'html' in content_type,
            'google' in content,
            'search' in content,
            len(content) > 1000  # Google 首页通常很大
        ]
        
        success_rate = sum(google_indicators) / len(google_indicators)
        return success_rate >= 0.6  # 至少满足60%的特征
    except Exception as e:
        print(f"验证响应内容时出错: {str(e)}")
        return False

def test_proxy_connection():
    """测试代理服务器连接"""
    if not PROXY_HOST or not PROXY_PORT:
        print("错误：代理配置未设置")
        print("请在 .env 文件中设置 PROXY_HOST 和 PROXY_PORT")
        return False
    
    print(f"\n正在测试代理连接: {PROXY_HOST}:{PROXY_PORT}")
    
    # 测试代理服务器端口是否开放
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((PROXY_HOST, int(PROXY_PORT)))
        sock.close()
        
        if result != 0:
            print(f"❌ 代理端口未开放: {PROXY_HOST}:{PROXY_PORT}")
            return False
        else:
            print(f"✅ 代理端口已开放: {PROXY_HOST}:{PROXY_PORT}")
    except Exception as e:
        print(f"❌ 测试代理端口时出错: {str(e)}")
        return False

    # 测试通过代理访问 Google
    try:
        proxies = {
            'http': f'http://{PROXY_HOST}:{PROXY_PORT}',
            'https': f'http://{PROXY_HOST}:{PROXY_PORT}'
        }
        
        print("\n正在通过代理访问 Google...")
        print(f"使用代理设置: {json.dumps(proxies, indent=2)}")
        
        start_time = time.time()
        response = requests.get(
            'https://www.google.com',
            proxies=proxies,
            timeout=10,
            verify=True  # 验证 SSL 证书
        )
        elapsed_time = time.time() - start_time
        
        print(f"\n响应信息:")
        print(f"状态码: {response.status_code}")
        print(f"响应时间: {elapsed_time:.2f}秒")
        print(f"响应大小: {len(response.content)} 字节")
        print(f"服务器: {response.headers.get('Server', 'Unknown')}")
        print(f"内容类型: {response.headers.get('Content-Type', 'Unknown')}")
        
        if response.status_code == 200 and verify_response_content(response):
            print(f"\n✅ 成功访问 Google！")
            return True
        else:
            print(f"\n❌ 访问 Google 失败或响应内容异常")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 通过代理访问 Google 时出错: {str(e)}")
        return False

def test_direct_connection():
    """测试直接连接（不使用代理）"""
    print("\n正在测试直接连接...")
    try:
        # 首先测试 DNS 解析
        try:
            print("正在解析 www.google.com...")
            ip = socket.gethostbyname('www.google.com')
            print(f"DNS 解析结果: {ip}")
        except socket.gaierror as e:
            print(f"❌ DNS 解析失败: {str(e)}")
            return False
            
        start_time = time.time()
        response = requests.get('https://www.google.com', timeout=5)
        elapsed_time = time.time() - start_time
        
        print(f"\n响应信息:")
        print(f"状态码: {response.status_code}")
        print(f"响应时间: {elapsed_time:.2f}秒")
        print(f"响应大小: {len(response.content)} 字节")
        print(f"服务器: {response.headers.get('Server', 'Unknown')}")
        print(f"内容类型: {response.headers.get('Content-Type', 'Unknown')}")
        
        if response.status_code == 200 and verify_response_content(response):
            print(f"\n✅ 直接连接成功！")
            return True
        else:
            print(f"\n❌ 直接连接失败或响应内容异常")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 直接连接失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("=== 代理连接测试 ===")
    print(f"Python 版本: {sys.version}")
    print(f"Requests 版本: {requests.__version__}")
    
    proxy_result = test_proxy_connection()
    
    print("\n=== 直接连接测试 ===")
    direct_result = test_direct_connection()
    
    print("\n=== 测试总结 ===")
    if proxy_result:
        print("✅ 代理连接正常工作")
    else:
        print("❌ 代理连接测试失败")
        
    if direct_result:
        print("✅ 直接连接正常工作")
    else:
        print("❌ 直接连接测试失败")
        
    if not proxy_result and not direct_result:
        print("\n⚠️ 建议：")
        print("1. 检查网络连接是否正常")
        print("2. 确认代理服务器是否正在运行")
        print("3. 验证代理配置是否正确")
        print("4. 尝试重启代理服务器")
        print("5. 检查防火墙设置")
        print("6. 尝试使用其他代理端口")
        print("7. 检查代理软件是否支持 HTTPS 代理")
        print("8. 验证代理服务器是否支持 Google 域名")

if __name__ == "__main__":
    main() 
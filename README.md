# Bank Service Agent

一个基于 DeepSeek API 的银行客服助手系统。

## 安装

```bash
# 克隆仓库后，在项目根目录下执行：
pip install -e .
```

## 运行示例

```bash
# 确保已经正确设置了 .env 文件中的配置
python examples/model_tool_example.py
```

## 环境变量配置

请确保在 `.env` 文件中设置了以下环境变量：

- DEEPSEEK_API_KEY：DeepSeek API 密钥
- LANGCHAIN_API_KEY：LangChain API 密钥（可选）
- GOOGLE_API_KEY：Google Custom Search API 密钥（可选）
- GOOGLE_CSE_ID：Google Custom Search Engine ID（可选）

## 目录结构

- src/：源代码目录
  - tools.py：工具类实现
  - config.py：配置文件
- examples/：示例代码
  - model_tool_example.py：ModelTool 使用示例

## 功能特点

- 使用LangGraph构建智能工作流
- 支持多种回答来源：
  - 基于RAG的知识库文档查询
  - DeepSeek模型直接回答
  - 网络搜索结果
- 使用Streamlit构建友好的用户界面
- 支持LangSmith监控
- 完整的日志记录和错误处理

## 安装

1. 克隆项目：
```bash
git clone [项目地址]
cd bank_service_agent
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
```bash
cp .env.example .env
# 编辑.env文件，填入必要的API密钥
```

## 使用方法

1. 启动应用：
```bash
streamlit run src/app.py
```

2. 在浏览器中访问应用（默认地址：http://localhost:8501）

## 项目结构

```
bank_service_agent/
├── data/               # 知识库文档
├── docs/               # 项目文档
├── logs/               # 日志文件
├── src/                # 源代码
│   ├── __init__.py
│   ├── agent.py       # 智能体实现
│   ├── app.py         # Streamlit应用
│   ├── config.py      # 配置管理
│   └── tools.py       # 工具实现
├── tests/             # 测试文件
├── .env.example       # 环境变量示例
├── README.md          # 项目说明
└── requirements.txt   # 项目依赖
```

## 配置说明

必要的环境变量：
- `DEEPSEEK_API_KEY`: DeepSeek API密钥
- `LANGCHAIN_API_KEY`: LangSmith API密钥
- `SECRET_KEY`: 应用安全密钥

## 开发说明

1. 添加新的知识库文档：
   - 将文档放入 `data/documents` 目录
   - 文档会在应用启动时自动加载

2. 修改模型配置：
   - 编辑 `src/config.py` 中的模型相关配置

3. 添加新的工具：
   - 在 `src/tools.py` 中实现新的工具类
   - 在 `src/agent.py` 中集成新工具

## 注意事项

- 请确保API密钥安全，不要提交到版本控制系统
- 建议在生产环境中使用HTTPS
- 定期备份知识库文档
- 监控日志文件大小

## 许可证

[选择合适的许可证] 
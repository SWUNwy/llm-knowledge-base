#!/bin/bash
set -e

echo "🚀 初始化 LLM Knowledge Base..."
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 未安装"
    echo "   请先安装 Python 3.11 或更高版本"
    echo "   推荐使用: brew install python@3.11"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(sys.version_info.major * 100 + sys.version_info.minor)')
if [ "$PYTHON_VERSION" -lt 311 ]; then
    echo "❌ Python 版本过低 (需要 3.11+)"
    python3 --version
    exit 1
fi

echo "✅ Python $(python3 --version)"

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装"
    echo "   请先安装 Node.js 18 或更高版本"
    echo "   推荐使用: brew install node"
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js 版本过低 (需要 18+)"
    node --version
    exit 1
fi

echo "✅ Node.js $(node --version)"
echo ""

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "📝 创建 .env 文件..."
    cp .env.example .env
    echo ""
    echo "⚠️  请编辑 .env 文件，配置以下必要项："
    echo "   - VAULT_PATH: 你的 Obsidian vault 路径"
    echo "   - 至少一个 LLM API Key (GEMINI_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY)"
    echo ""
    echo "编辑完成后，重新运行此脚本继续安装。"
    echo ""
    echo "  vim .env"
    echo ""
    exit 0
fi

echo "✅ .env 文件已存在"
echo ""

# 后端设置
echo "📦 设置后端环境..."
cd backend

if [ ! -d "venv" ]; then
    echo "   创建 Python 虚拟环境..."
    python3 -m venv venv
fi

echo "   安装依赖..."
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
pip install --quiet -r requirements-dev.txt

echo "✅ 后端依赖安装完成"
cd ..

# 前端设置
echo ""
echo "📦 设置前端环境..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "   安装 npm 依赖..."
    npm install --silent
fi

echo "✅ 前端依赖安装完成"
cd ..

echo ""
echo "================================"
echo "✅ 初始化完成！"
echo "================================"
echo ""
echo "下一步："
echo ""
echo "1. 启动开发服务器（需要两个终端）："
echo ""
echo "   终端 1 - 后端:"
echo "   cd backend && source venv/bin/activate"
echo "   uvicorn src.main:app --reload --port 8000"
echo ""
echo "   终端 2 - 前端:"
echo "   cd frontend && npm run dev"
echo ""
echo "2. 访问应用："
echo "   前端: http://localhost:5173"
echo "   API 文档: http://localhost:8000/docs"
echo ""

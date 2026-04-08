#!/bin/bash

echo "🚀 LLM Knowledge Base - 开发服务器"
echo ""

# 检查 .env
if [ ! -f .env ]; then
    echo "❌ .env 文件不存在"
    echo "   请先运行: ./scripts/setup.sh"
    exit 1
fi

# 加载环境变量
export $(grep -v '^#' .env | xargs)

PORT=${APP_PORT:-8000}

echo "请分别在两个终端运行以下命令："
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📦 终端 1 - 后端 API 服务:"
echo ""
echo "    cd backend && source venv/bin/activate"
echo "    uvicorn src.main:app --reload --port $PORT"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 终端 2 - 前端开发服务器:"
echo ""
echo "    cd frontend && npm run dev"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "访问地址："
echo "  • 前端应用:  http://localhost:5173"
echo "  • API 文档:  http://localhost:$PORT/docs"
echo "  • ReDoc:     http://localhost:$PORT/redoc"
echo ""

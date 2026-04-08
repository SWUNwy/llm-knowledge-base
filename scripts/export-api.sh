#!/bin/bash
set -e

echo "📄 导出 OpenAPI 规范..."
echo ""

# 检查后端是否存在
if [ ! -d "backend" ]; then
    echo "❌ backend 目录不存在"
    exit 1
fi

cd backend

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行 ./scripts/setup.sh"
    exit 1
fi

source venv/bin/activate

# 临时启动服务器并导出
echo "启动临时服务器..."
uvicorn src.main:app --port 8765 &
PID=$!

sleep 3

echo "导出 OpenAPI 规范..."
curl -s http://localhost:8765/openapi.json | python3 -c "
import sys, json
try:
    import yaml
    spec = json.load(sys.stdin)
    print(yaml.dump(spec, allow_unicode=True, sort_keys=False, default_flow_style=False))
except ImportError:
    print('警告: pyyaml 未安装，输出 JSON 格式')
    spec = json.load(sys.stdin)
    print(json.dumps(spec, indent=2, ensure_ascii=False))
" > ../docs/api.yaml

kill $PID 2>/dev/null

cd ..

echo ""
echo "✅ OpenAPI 规范已导出到 docs/api.yaml"
echo ""
echo "查看方式："
echo "  • 在线编辑器: https://editor.swagger.io (粘贴文件内容)"
echo "  • VS Code插件: OpenAPI (Preview)"
echo "  • 运行时访问: http://localhost:8000/docs"
echo ""

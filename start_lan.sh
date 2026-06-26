#!/usr/bin/env bash
# 一键启动 backend + frontend（局域网 production 模式）
# 用法：在项目根目录执行 ./start_lan.sh
#
# 注意：frontend 用 production build（next start），不用 dev mode。
# Next.js 16 Turbopack dev mode 有 RSC hydration bug，导致页面无交互。
# 改了前端代码后需要先 npm run build 再重新跑此脚本。
set -e
cd "$(dirname "$0")"

# 检查是否已 build
if [ ! -d "frontend/.next/standalone" ] && [ ! -f "frontend/.next/BUILD_ID" ]; then
  echo "→ 首次运行，先 build frontend..."
  (cd frontend && npm run build)
fi

# 后台启动 backend (0.0.0.0)
HOST=0.0.0.0 python3 start_backend.py &
BACKEND_PID=$!

# 后台启动 frontend production (0.0.0.0)
(cd frontend && npm run start:lan) &
FRONTEND_PID=$!

# 打印 LAN IP 方便手机访问
echo ""
echo "=== LAN IP ==="
ifconfig 2>/dev/null | grep "inet " | grep -v 127.0.0.1 | awk '{print "  http://"$2":3000"}'
ipconfig getifaddr en0 2>/dev/null | awk '{print "  http://"$1":3000 (en0)"}'
echo ""
echo "Backend PID: $BACKEND_PID | Frontend PID: $FRONTEND_PID"
echo "Ctrl+C 关闭"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait

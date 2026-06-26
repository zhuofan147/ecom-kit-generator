# 电商套图生成工具

ecom-kit-generator

Single product upload, `rembg` background removal, AI provider-based ecommerce kit generation, and multi-platform image sizing.

## Backend

```bash
cd backend
python -m venv .venv
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Frontend

```bash
cd frontend
npm install
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Open `http://127.0.0.1:3000`.

## Tests

```bash
cd backend && python -m pytest
cd frontend && npm test
cd frontend && npm run build
```

## 局域网访问

让手机等局域网设备访问本机的前后端（默认都只绑 127.0.0.1）。

**启动 backend**（监听 0.0.0.0:8000）：

```bash
HOST=0.0.0.0 python start_backend.py
```

**启动 frontend**（监听 0.0.0.0:3000，production build）：

```bash
cd frontend
npm run build          # 首次或改代码后需要 build
npm run start:lan      # production server，绑 0.0.0.0:3000
```

> ⚠️ **不要用 `npm run dev:lan`**。Next.js 16 Turbopack dev mode 有 RSC hydration bug，
> 页面能加载但所有按钮点击无响应（React 不 hydrate）。必须用 production build。

或者在项目根目录直接跑一键脚本：

```bash
python start_lan.py
```

macOS/Linux 也可以用 `./start_lan.sh`，Windows 可以双击或执行 `start_lan.bat`。脚本会同时拉起 backend + frontend 并打印 LAN IP。

**手机访问**：在手机浏览器输入 `http://<电脑的 LAN IP>:3000`，例如 `http://192.168.1.10:3000`。frontend 内部已根据 `window.location.hostname` 拼出 backend 地址，手机无需改任何配置。

**第一次启动会弹 macOS 防火墙提示**（"是否允许 python/Node 接受传入网络连接？"），点 **Allow** 即可。如果之前误点了拒绝，可以到 `系统设置 → 网络 → 防火墙` 里把对应程序删掉再重启。

**查看本机 LAN IP**：`start_lan.py` 会自动打印可访问地址。

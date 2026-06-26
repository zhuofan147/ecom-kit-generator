#!/usr/bin/env python3
"""启动 ecom-kit-generator 后端，从 .env 加载密钥

用法:
  python3 start_backend.py              # 本地模式 (127.0.0.1:8000)
  HOST=0.0.0.0 python3 start_backend.py # 局域网模式 (0.0.0.0:8000)
"""
import os, sys, subprocess
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

os.chdir(Path(__file__).resolve().parent)
load_dotenv(find_dotenv())

# 从 .env 加载密钥（不再硬要求 AGNES_API_KEY，因为现在支持 volcengine/fal/siliconflow）
# 只 warn，方便老豆用别的 provider 时不报错
ag_key = os.environ.get("AGNES_API_KEY", "")
if not ag_key:
    print("WARN: AGNES_API_KEY not set — agnes provider will fail (others OK)", file=sys.stderr)

# ── 启动时打印各 provider 可用状态 ──────────────────────────────
print()
sys.path.insert(0, str(Path("backend")))
from app.config.providers import PROVIDER_REGISTRY, detect_availability

print("━" * 48)
print(f"{'Provider':24s} {'ENV Variable':24s} {'Status'}")
print("━" * 48)
avail = detect_availability()
for meta in PROVIDER_REGISTRY:
    available = avail.get(meta.name, False)
    icon = "✅" if available else "❌"
    envs = ",".join(meta.env_vars) if meta.env_vars else "(none)"
    status = "AVAILABLE" if available else "NOT SET"
    print(f"{icon} {meta.label:22s} {envs:24s} {status}")
print("━" * 48)
print(f"  Placeholder 'mock' always available (solid-colour fallback)")
print()

# 透传所有 provider key 到子进程
forward_env = os.environ.copy()
for env_name in ("AGNES_API_KEY", "VOLCENGINE_ARK_API_KEY", "FAL_KEY", "SILICONFLOW_KEY", "VISION_API_KEY", "VISION_BASE_URL", "VISION_MODEL"):
    val = os.environ.get(env_name)
    if val:
        forward_env[env_name] = val

# 监听地址：HOST=0.0.0.0 走局域网，否则本地
host = os.environ.get("HOST", "127.0.0.1")

subprocess.run([
    ".venv/bin/python", "-m", "uvicorn", "app.main:app",
    "--host", host, "--port", "8000",
], cwd="backend", env=forward_env)

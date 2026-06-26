#!/usr/bin/env python3
"""Cross-platform LAN launcher for backend and frontend."""

from __future__ import annotations

import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT_DIR / "frontend"


def npm_cmd() -> str:
    return "npm.cmd" if os.name == "nt" else "npm"


def local_ip_addresses() -> list[str]:
    addresses: set[str] = set()
    hostname = socket.gethostname()
    try:
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if not ip.startswith("127."):
                addresses.add(ip)
    except socket.gaierror:
        pass

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        if not ip.startswith("127."):
            addresses.add(ip)
    except OSError:
        pass
    finally:
        sock.close()

    return sorted(addresses)


def ensure_frontend_build() -> None:
    standalone_dir = FRONTEND_DIR / ".next" / "standalone"
    build_id = FRONTEND_DIR / ".next" / "BUILD_ID"
    if standalone_dir.exists() or build_id.exists():
        return
    print("-> 首次运行，先 build frontend...")
    subprocess.run([npm_cmd(), "run", "build"], cwd=FRONTEND_DIR, check=True)


def start_processes() -> list[subprocess.Popen]:
    env = os.environ.copy()
    env["HOST"] = "0.0.0.0"

    backend = subprocess.Popen([sys.executable, str(ROOT_DIR / "start_backend.py")], cwd=ROOT_DIR, env=env)
    frontend = subprocess.Popen([npm_cmd(), "run", "start:lan"], cwd=FRONTEND_DIR)
    return [backend, frontend]


def stop_processes(processes: list[subprocess.Popen]) -> None:
    for proc in processes:
        if proc.poll() is not None:
            continue
        if os.name == "nt":
            proc.terminate()
        else:
            proc.send_signal(signal.SIGTERM)
    for proc in processes:
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def main() -> int:
    if shutil.which(npm_cmd()) is None:
        print("ERROR: npm not found in PATH", file=sys.stderr)
        return 1

    ensure_frontend_build()
    processes = start_processes()

    print()
    print("=== LAN URLs ===")
    urls = local_ip_addresses()
    if urls:
        for ip in urls:
            print(f"  http://{ip}:3000")
    else:
        print("  http://localhost:3000")
    print()
    print(f"Backend PID: {processes[0].pid} | Frontend PID: {processes[1].pid}")
    print("Ctrl+C 关闭")

    try:
        while True:
            for proc in processes:
                code = proc.poll()
                if code is not None:
                    stop_processes(processes)
                    return code
            time.sleep(1)
    except KeyboardInterrupt:
        stop_processes(processes)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SWIPLY -- ONE-CLICK LAUNCHER
Starts ALL services + Frontend with a single command.
Usage:  python START.py
"""

import subprocess
import sys
import os
import time
import threading
import signal
from pathlib import Path

# Force UTF-8 output so box chars work on Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

ROOT = Path(__file__).parent.resolve()
VENV_PYTHON  = ROOT / ".venv" / "Scripts" / "python.exe"
VENV_UVICORN = ROOT / ".venv" / "Scripts" / "uvicorn.exe"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

MICROSERVICES = [
    {"name": "auth",         "module": "services.auth.app.main:app",         "port": 8001},
    {"name": "profile",      "module": "services.profile.app.main:app",      "port": 8004},
    {"name": "job",          "module": "services.job.app.main:app",          "port": 8003},
    {"name": "credential",   "module": "services.credential.app.main:app",   "port": 8009},
    {"name": "email",        "module": "services.email.app.main:app",        "port": 8007},
    {"name": "automation",   "module": "services.automation.app.main:app",   "port": 8006},
    {"name": "ai",           "module": "services.ai.app.main:app",           "port": 8010},
    {"name": "wttj",         "module": "services.wttj.app.main:app",         "port": 8012},
    {"name": "wttj_scraper", "module": "services.wttj_scraper.app.main:app", "port": 8013},
]

GATEWAY  = {"name": "gateway",  "script": str(ROOT / "api_gateway.py"), "port": 8000}
FRONTEND = {"name": "frontend", "cwd":    str(ROOT / "frontend"),        "port": 5173}

all_processes = []

def make_env():
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["OPENAI_API_KEY"]   = OPENAI_API_KEY
    env["DATABASE_URL"]     = "postgresql://swiply:swiply123@localhost:5432/swiply"
    env["ENCRYPTION_KEY"]   = "your-32-byte-encryption-key-here"
    env["HEADLESS"]         = "true"
    return env

def kill_port(port):
    """Kill any process listening on a given port (Windows)."""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             f"(Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue "
             f"| Select-Object -First 1 OwningProcess).OwningProcess"],
            capture_output=True, text=True
        )
        owner = result.stdout.strip()
        if owner and owner.isdigit():
            subprocess.run(["taskkill", "/F", "/PID", owner], capture_output=True)
    except Exception:
        pass

COLORS = [32, 33, 34, 35, 36, 92, 93, 94, 95, 96, 91, 97]

def stream_logs(name, process, color_code):
    try:
        for line in iter(process.stdout.readline, ""):
            if line.strip():
                print(f"\033[{color_code}m[{name}]\033[0m {line.rstrip()}", flush=True)
    except Exception:
        pass

def start_microservice(svc, env):
    cmd = [str(VENV_UVICORN), svc["module"],
           "--host", "0.0.0.0", "--port", str(svc["port"])]
    return subprocess.Popen(cmd, cwd=str(ROOT), env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, bufsize=1, encoding="utf-8", errors="replace")

def start_gateway(env):
    cmd = [str(VENV_PYTHON), GATEWAY["script"]]
    return subprocess.Popen(cmd, cwd=str(ROOT), env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, bufsize=1, encoding="utf-8", errors="replace")

def start_frontend():
    return subprocess.Popen(
        ["npm", "run", "dev"], cwd=FRONTEND["cwd"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1, shell=True, encoding="utf-8", errors="replace"
    )

def shutdown(signum=None, frame=None):
    print("\n\nStopping all services...")
    for name, proc in all_processes:
        try:
            proc.terminate()
            print(f"  Stopped {name}")
        except Exception:
            pass
    print("All services stopped. Goodbye!\n")
    sys.exit(0)

signal.signal(signal.SIGINT,  shutdown)
signal.signal(signal.SIGTERM, shutdown)

def main():
    print("\n" + "=" * 50)
    print("  SWIPLY -- STARTING ALL SERVICES")
    print("=" * 50 + "\n")

    env = make_env()

    # Kill any stale processes on service ports
    all_ports = [svc["port"] for svc in MICROSERVICES] + [GATEWAY["port"], FRONTEND["port"]]
    print("  Clearing stale processes...")
    for port in all_ports:
        kill_port(port)
    time.sleep(1)

    # Start microservices
    for i, svc in enumerate(MICROSERVICES):
        color = COLORS[i % len(COLORS)]
        print(f"  [START] {svc['name']} on port {svc['port']}...")
        try:
            proc = start_microservice(svc, env)
            all_processes.append((svc["name"], proc))
            threading.Thread(target=stream_logs, args=(svc["name"], proc, color), daemon=True).start()
            time.sleep(1.5)
        except Exception as e:
            print(f"  [FAIL]  {svc['name']}: {e}")

    # Start API Gateway
    print(f"  [START] gateway on port {GATEWAY['port']}...")
    try:
        proc = start_gateway(env)
        all_processes.append(("gateway", proc))
        threading.Thread(target=stream_logs, args=("gateway", proc, 96), daemon=True).start()
        time.sleep(2)
    except Exception as e:
        print(f"  [FAIL]  gateway: {e}")

    # Start Frontend
    print(f"  [START] frontend on port {FRONTEND['port']}...")
    try:
        proc = start_frontend()
        all_processes.append(("frontend", proc))
        threading.Thread(target=stream_logs, args=("frontend", proc, 93), daemon=True).start()
    except Exception as e:
        print(f"  [FAIL]  frontend: {e}")

    time.sleep(5)

    # Status summary
    print("\n" + "-" * 50)
    print("SERVICE STATUS:")
    for name, proc in all_processes:
        status = "RUNNING" if proc.poll() is None else "STOPPED"
        print(f"  [{status}]  {name}")

    print("\nOPEN YOUR APP:")
    print("  Frontend  -->  http://localhost:5173")
    print("  API Docs  -->  http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop all services.\n")
    print("-" * 50 + "\n")

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        shutdown()

if __name__ == "__main__":
    main()

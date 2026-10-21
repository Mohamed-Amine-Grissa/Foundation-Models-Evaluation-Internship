"""Starts, stops and checks the local llama-servers; all paths and ports come from config.toml.

Server logs and the PID file go to .run/ (git-ignored).

Usage (from repo root):
    python scripts/llama_servers.py start chat [<gguf file>]   # default: chat_model
    python scripts/llama_servers.py start embed
    python scripts/llama_servers.py stop                       # stops servers started by this script
    python scripts/llama_servers.py status
"""
import json
import subprocess
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.config import REPO_ROOT, load_config, bin_path, model_path

RUN_DIR = REPO_ROOT / ".run"
PIDS = RUN_DIR / "server_pids.json"
STARTUP_TIMEOUT_S = 180

def _pids() -> dict:
    return json.loads(PIDS.read_text()) if PIDS.exists() else {}

def healthy(port: int) -> bool:
    try:
        return requests.get(f"http://localhost:{port}/health", timeout=2).status_code == 200
    except requests.RequestException:
        return False

def start(cfg: dict, kind: str, model_file: str | None = None) -> None:
    port = cfg["servers"][f"{kind}_port"]
    if healthy(port):
        sys.exit(f"something is already answering on port {port}; stop it first")
    model = (Path(cfg["llama_cpp"]["models_dir"]) / model_file) if model_file else model_path(cfg, f"{kind}_model")
    cmd = [str(bin_path(cfg, "llama-server.exe")), "-m", str(model), "--port", str(port), "-t", "8"]
    if kind == "embed":
        cmd.append("--embeddings")
    RUN_DIR.mkdir(exist_ok=True)
    log_path = RUN_DIR / f"server_{kind}.log"
    proc = subprocess.Popen(cmd, stdout=open(log_path, "w"), stderr=subprocess.STDOUT,
                            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
    pids = _pids()
    pids[kind] = proc.pid
    PIDS.write_text(json.dumps(pids))
    for _ in range(STARTUP_TIMEOUT_S):
        if healthy(port):
            print(f"{kind} server up on {port} with {model.name} (pid {proc.pid})")
            return
        if proc.poll() is not None:
            sys.exit(f"{kind} server exited with code {proc.returncode}; see {log_path}")
        time.sleep(1)
    sys.exit(f"{kind} server not healthy after {STARTUP_TIMEOUT_S} s; see {log_path}")

def stop() -> None:
    for kind, pid in _pids().items():
        r = subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, text=True)
        print(kind, pid, (r.stdout or r.stderr).strip())
    PIDS.unlink(missing_ok=True)

def status(cfg: dict) -> None:
    for kind in ("chat", "embed"):
        port = cfg["servers"][f"{kind}_port"]
        print(kind, port, "UP" if healthy(port) else "DOWN")

if __name__ == "__main__":
    cfg = load_config()
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    if action == "start":
        start(cfg, sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    elif action == "stop":
        stop()
    else:
        status(cfg)

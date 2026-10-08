"""Writes a small, consistent JSON log alongside every experiment run."""
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

def sha256_of_file(path: str, chunk_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()

def write_run_log(out_path: str, *, model_path: str, llama_build: str,
                   command: str, prompt_version: str | None = None,
                   seed: int | None = None, temperature: float | None = None,
                   extra: dict | None = None) -> None:
    # Only the model filename is logged (the repo is public); the hash still
    # identifies the exact file.
    log = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_file": Path(model_path).name,
        "model_sha256": sha256_of_file(model_path),
        "llama_build": llama_build,
        "command": command,
        "prompt_version": prompt_version,
        "seed": seed,
        "temperature": temperature,
    }
    if extra:
        log.update(extra)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

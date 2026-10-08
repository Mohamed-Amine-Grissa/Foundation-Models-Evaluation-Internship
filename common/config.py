"""Loads config.toml and exposes resolved paths for the local llama.cpp install."""
import re
import subprocess
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

def load_config() -> dict:
    with open(REPO_ROOT / "config.toml", "rb") as f:
        return tomllib.load(f)

def bin_path(cfg: dict, exe_name: str) -> Path:
    return Path(cfg["llama_cpp"]["bin_dir"]) / exe_name

def model_path(cfg: dict, key: str) -> Path:
    """key is 'chat_model' or 'embed_model'."""
    return Path(cfg["llama_cpp"]["models_dir"]) / cfg["llama_cpp"][key]

def generator_path(cfg: dict, model_file: str) -> Path:
    """Path of a generator model; model_file must be listed in llama_cpp.generators."""
    if model_file not in cfg["llama_cpp"]["generators"]:
        raise ValueError(f"{model_file} is not in llama_cpp.generators in config.toml")
    return Path(cfg["llama_cpp"]["models_dir"]) / model_file

def llama_build(cfg: dict, exe_name: str = "llama-perplexity.exe") -> str:
    """Asks a llama.cpp binary for its build string, e.g. '10358 (030ebb558)'."""
    out = subprocess.run([str(bin_path(cfg, exe_name)), "--version"],
                         capture_output=True, text=True, timeout=30)
    m = re.search(r"version:\s*(.+)", out.stdout + out.stderr)
    return m.group(1).strip() if m else "unknown"

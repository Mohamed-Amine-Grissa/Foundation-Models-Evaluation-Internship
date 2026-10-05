"""Thin client for a locally running llama-server (chat or embeddings)."""
import requests

class LlamaServerClient:
    def __init__(self, port: int, base_url: str = "http://localhost"):
        self.base = f"{base_url}:{port}"

    def chat(self, system: str, user: str, temperature: float = 0.7,
              max_tokens: int = 512, seed: int | None = None) -> dict:
        payload = {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if seed is not None:
            payload["seed"] = seed
        r = requests.post(f"{self.base}/v1/chat/completions", json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        return {
            "text": data["choices"][0]["message"]["content"],
            "raw": data,
        }

    def embed(self, text: str, prefix: str = "search_document: ") -> list[float]:
        r = requests.post(f"{self.base}/v1/embeddings",
                           json={"input": f"{prefix}{text}"}, timeout=60)
        r.raise_for_status()
        return r.json()["data"][0]["embedding"]

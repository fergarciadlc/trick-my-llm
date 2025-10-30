import os
import httpx
from typing import Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class LLMClient:
    """
    Minimal OpenAI-compatible chat completions client (e.g., Groq base_url).
    """
    def __init__(self, base_url: str, api_key_env: str, timeout_s: int = 60):
        self.base_url = base_url.rstrip("/")
        self.api_key = os.environ.get(api_key_env)
        if not self.api_key:
            raise RuntimeError(f"Missing API key in env var {api_key_env}")
        self.timeout_s = timeout_s
        self.headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    @retry(reraise=True, stop=stop_after_attempt(5),
           wait=wait_exponential(multiplier=1, min=1, max=10),
           retry=retry_if_exception_type((httpx.HTTPError,)))
    def chat_completions(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/chat/completions"
        with httpx.Client(timeout=self.timeout_s) as client:
            resp = client.post(url, headers=self.headers, json=payload)
            resp.raise_for_status()
            return resp.json()

def build_payload(model: str, system: str, user: str, model_params: Dict[str, Any]) -> Dict[str, Any]:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user})
    allowed = {"temperature", "top_p", "max_tokens", "presence_penalty", "frequency_penalty", "seed", "stop"}
    extras = {k: v for k, v in (model_params or {}).items() if k in allowed and v is not None}
    payload = {"model": model, "messages": messages, **extras}
    return payload

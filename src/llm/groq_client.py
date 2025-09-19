import requests
from typing import List, Dict
from ..config import GROQ_API_KEY, GROQ_BASE_URL, TIMEOUT_S

class GroqClient:
    def __init__(self, model: str, temperature: float = 0.0, max_tokens: int = 1000):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def chat(self, messages: List[Dict]) -> str:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False
        }
        url = f"{GROQ_BASE_URL}/chat/completions"
        resp = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT_S)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

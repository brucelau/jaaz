#!/usr/bin/env python3
"""
Selene LLM Client
Call remote Selene server from local machine
"""

import requests
from typing import List, Optional


class SeleneClient:
    def __init__(self, base_url: str = "http://100.75.202.111:8080"):
        self.base_url = base_url

    def completions(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> str:
        """Simple text completion"""
        resp = requests.post(
            f"{self.base_url}/v1/completions",
            json={
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature
            },
            timeout=120
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["text"]

    def chat(
        self,
        messages: List[dict],
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> str:
        """Chat completion"""
        resp = requests.post(
            f"{self.base_url}/v1/chat/completions",
            json={
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            },
            timeout=120
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def health(self) -> bool:
        """Check if server is alive"""
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=5)
            return resp.status_code == 200
        except:
            return False


if __name__ == "__main__":
    client = SeleneClient()

    # Check health
    print(f"Server health: {client.health()}")

    # Test completion
    prompt = "Explain what is an air-mold design in one sentence:"
    print(f"Prompt: {prompt}")
    result = client.completions(prompt)
    print(f"Result: {result}")

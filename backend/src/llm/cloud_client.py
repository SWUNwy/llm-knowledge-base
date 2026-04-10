"""Cloud LLM proxy client for SaaS mode."""

import httpx
from typing import AsyncGenerator
from src.config import get_settings

settings = get_settings()


class CloudLLMClient:
    """Client for LLM requests through cloud proxy."""

    def __init__(self, license_token: str):
        self.license_token = license_token
        self.base_url = settings.cloud_api_url.rstrip('/')
        self.timeout = 120.0  # LLM requests can take time

    async def compile_document(
        self,
        documents: list[dict],
        prompt_template: str = "wiki"
    ) -> AsyncGenerator[str, None]:
        """Compile document via cloud proxy."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "token": self.license_token,
                "action": "compile",
                "payload": {
                    "documents": documents,
                    "prompt_template": prompt_template
                }
            }

            async with client.stream(
                'POST',
                f"{self.base_url}/api/llm/proxy",
                json=payload
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith('data: '):
                        data_str = line[6:]  # Remove 'data: ' prefix
                        if data_str == '[DONE]':
                            break
                        try:
                            import json
                            data = json.loads(data_str)
                            if 'content' in data:
                                yield data['content']
                        except json.JSONDecodeError:
                            continue

    async def answer_question(
        self,
        question: str,
        context: list[dict]
    ) -> AsyncGenerator[str, None]:
        """Answer question via cloud proxy."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "token": self.license_token,
                "action": "qa",
                "payload": {
                    "question": question,
                    "context": context
                }
            }

            async with client.stream(
                'POST',
                f"{self.base_url}/api/llm/proxy",
                json=payload
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str == '[DONE]':
                            break
                        try:
                            import json
                            data = json.loads(data_str)
                            if 'content' in data:
                                yield data['content']
                        except json.JSONDecodeError:
                            continue

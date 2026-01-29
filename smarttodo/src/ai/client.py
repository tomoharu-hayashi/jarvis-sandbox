import os
from functools import lru_cache

from openai import AsyncOpenAI


@lru_cache(maxsize=1)
def get_openai_client() -> AsyncOpenAI:
    """OpenAI クライアントのシングルトンを取得"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY が設定されていません")
    return AsyncOpenAI(api_key=api_key)

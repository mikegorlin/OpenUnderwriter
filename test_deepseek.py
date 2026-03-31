#!/usr/bin/env python3
"""Test DeepSeek API integration."""

import os
from openai import OpenAI

# Load environment variables from .env if not already loaded
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("DEEPSEEK_API_KEY")
if not api_key:
    print("ERROR: DEEPSEEK_API_KEY not set")
    exit(1)

print(f"API key: {api_key[:10]}...")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com",
)

try:
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, what is 2+2?"},
        ],
        max_tokens=10,
    )
    print("API call successful!")
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"API call failed: {e}")
    import traceback

    traceback.print_exc()

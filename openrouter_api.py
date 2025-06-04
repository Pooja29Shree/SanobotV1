import os
import requests
from dotenv import load_dotenv

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

SYSTEM_PROMPT = {
    "role": "system",
    "content": "You are a helpful medical assistant. Never give diagnoses. Only provide general health information."
}

def call_openrouter_chat(messages, model="openai/gpt-4o-mini"):
    url = "https://openrouter.ai/api/v1/chat/completions"  # ✅ Correct endpoint

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://yourdomain.com",   # Optional but helps with OpenRouter analytics
        "X-Title": "Medical Chatbot"                # Optional
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 401:
        raise Exception("401 Unauthorized: Invalid or missing OpenRouter API key.")
    if response.status_code == 404:
        raise Exception("404 Not Found: Check the model name or endpoint URL.")

    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
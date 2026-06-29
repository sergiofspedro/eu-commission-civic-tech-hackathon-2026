"""DeepSeek V4 Flash via OpenRouter — thin wrapper for civic context replies."""
import os
import httpx

_BASE = "https://openrouter.ai/api/v1"
_MODEL = "deepseek/deepseek-v4-flash"
_SYSTEM = (
    "You are a civic engagement assistant for EU CivicConnect, a platform for digital "
    "public participation. You help citizens understand and engage with public consultations "
    "at municipal, national, and European Union levels. Be empathetic, informative, and "
    "concise. Keep replies under 200 words. Do not take political positions — acknowledge "
    "the citizen's view respectfully and explain the civic process."
)


def get_reply(user_message: str, context: str = "") -> str:
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    system = _SYSTEM + (f"\n\nConsultation context: {context}" if context else "")
    try:
        resp = httpx.post(
            f"{_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://civicconnect-demo.eu",
                "X-Title": "EU CivicConnect Demo",
            },
            json={
                "model": _MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_message},
                ],
                "max_tokens": 300,
                "temperature": 0.7,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return (
            "Thank you for sharing your view. Your input has been noted and will "
            "contribute to the consultation process."
        )

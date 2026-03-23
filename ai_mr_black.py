import requests
from config import OPENROUTER_API_KEY

def generate_line(context):

    prompt = f"""
You are Mr Black.

Style:
- dark
- mysterious
- short
- no explanation

Context:
{context}

Respond in 1–2 lines.
"""

    res = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}"
        },
        json={
            "model": "openai/gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are Mr Black"},
                {"role": "user", "content": prompt}
            ]
        }
    )

    return res.json()["choices"][0]["message"]["content"]

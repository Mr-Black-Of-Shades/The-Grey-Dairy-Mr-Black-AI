import requests
from config import OPENROUTER_API_KEY

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


# ================= BASE CALL =================

def _call_openrouter(messages):

    try:
        res = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-4o-mini",
                "messages": messages,
                "temperature": 0.8
            },
            timeout=10
        )

        data = res.json()

        return data["choices"][0]["message"]["content"]

    except Exception as e:
        print("AI ERROR:", e)
        return "Something feels... off."


# ================= MR BLACK =================

def generate_line(context):

    system_prompt = """
You are Mr Black.

Rules:
- Speak in short sentences
- Be mysterious, calm, controlled
- Never explain too much
- Never sound like an assistant
- Always create curiosity
"""

    user_prompt = f"""
Context:
{context}

Respond in 1–2 short lines.
"""

    return _call_openrouter([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ])


# ================= VOICE SYSTEM =================

def generate_voice_line(character_name, context):

    system_prompt = f"""
You are {character_name}.

Rules:
- Speak emotionally but controlled
- Short sentences
- Slightly different tone than Mr Black
- Feel like a real person in the story
"""

    user_prompt = f"""
Context:
{context}

Respond in 1–2 short lines.
"""

    return _call_openrouter([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ])


# ================= UPSELL / MONETIZATION =================

def generate_upsell_line():

    return generate_line("""
User reached locked content.
Make them curious without directly selling.
""")



# ================= RE-ENGAGEMENT =================

def generate_reengagement_line():

    return generate_line("""
User has been inactive and left mid-story.
Bring them back with tension.
""")

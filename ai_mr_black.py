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


        if "choices" in data:
            return data["choices"][0]["message"]["content"]
    
        return "Something feels... off."
        

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



# ================= STATE-BASED AI =================

def generate_state_line(state):

    if state == "CURIOUS":
        return generate_line("""
User just entered the story.
Make them feel like they are missing something deeper.
""")

    elif state == "HOOKED":
        return generate_line("""
User is already engaged in story.
Push them forward subtly. Make stopping feel incomplete.
""")

    elif state == "HESITANT":
        return generate_line("""
User stopped at payment.
Apply psychological pressure. Make them feel they stopped at the wrong moment.
""")

    elif state == "BUYER":
        return generate_line("""
User has already paid.
Make them feel special and continue deeper.
""")

    elif state == "DORMANT":
        return generate_line("""
User left the story midway.
Bring them back with tension and curiosity.
""")

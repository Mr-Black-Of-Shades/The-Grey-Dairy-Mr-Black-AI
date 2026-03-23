from supabase_client import supabase
from datetime import datetime

def get_or_create_user(telegram_id):

    res = supabase.table("users")\
        .select("*")\
        .eq("telegram_id", str(telegram_id))\
        .execute()

    if res.data:
        return res.data[0]

    user = supabase.table("users").insert({
        "telegram_id": str(telegram_id),
        "current_episode": 1
    }).execute()

    return user.data[0]


# ✅ Create or update behavior
def update_user_behavior(user_id, episode_id=None, drop_off=None):
    data = {
        "user_id": user_id,
        "updated_at": datetime.utcnow().isoformat()
    }

    if episode_id is not None:
        data["last_episode_seen"] = episode_id
    
    if drop_off is not None:
        data["drop_off_point"] = drop_off

    data["last_active"] = datetime.utcnow().isoformat()

    supabase.table("user_behavior").upsert(data).execute()


# ✅ Get behavior
def get_user_behavior(user_id):
    res = supabase.table("user_behavior") \
        .select("*") \
        .eq("user_id", user_id) \
        .execute()
    
    return res.data[0] if res.data else None


# ✅ USER STATE LOGIC
def get_user_state(user, behavior):
    if user["total_spent"] > 0:
        return "BUYER"
    
    if behavior and behavior.get("drop_off_point") == "payment":
        return "HESITANT"
    
    if user["current_episode"] >= 2:
        return "HOOKED"
    
    return "CURIOUS"

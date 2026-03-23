from supabase_client import supabase


# ================= GET EPISODE =================

def get_episode(episode_id):

    res = supabase.table("episodes")\
        .select("*")\
        .eq("id", episode_id)\
        .limit(1)\
        .execute()

    return res.data[0] if res.data else None


# ================= CHECK UNLOCK =================

def is_episode_unlocked(user_id, episode_id):

    res = supabase.table("user_progress")\
        .select("id")\
        .eq("user_id", user_id)\
        .eq("episode_id", episode_id)\
        .limit(1)\
        .execute()

    return bool(res.data)


# ================= UNLOCK EPISODE =================

def unlock_episode(user_id, episode_id):

    # prevent duplicate unlock
    if is_episode_unlocked(user_id, episode_id):
        return True

    res = supabase.table("user_progress").insert({
        "user_id": user_id,
        "episode_id": episode_id,
        "unlocked": True
    }).execute()

    return bool(res.data)


# ================= GET USER CURRENT EPISODE =================

def get_user_current_episode(telegram_id):

    res = supabase.table("users")\
        .select("current_episode")\
        .eq("telegram_id", str(telegram_id))\
        .limit(1)\
        .execute()

    if res.data:
        return res.data[0]["current_episode"]

    return 1


# ================= UPDATE USER EPISODE =================

def update_user_episode(telegram_id, episode_id):

    supabase.table("users")\
        .update({"current_episode": episode_id})\
        .eq("telegram_id", str(telegram_id))\
        .execute()

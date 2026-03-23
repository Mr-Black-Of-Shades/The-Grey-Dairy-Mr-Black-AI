from supabase_client import supabase

def get_episode(episode_id):

    res = supabase.table("episodes")\
        .select("*")\
        .eq("id", episode_id)\
        .execute()

    return res.data[0] if res.data else None


def is_episode_unlocked(user_id, episode_id):

    res = supabase.table("user_progress")\
        .select("*")\
        .eq("user_id", user_id)\
        .eq("episode_id", episode_id)\
        .execute()

    return bool(res.data)


def unlock_episode(user_id, episode_id):

    supabase.table("user_progress").insert({
        "user_id": user_id,
        "episode_id": episode_id,
        "unlocked": True
    }).execute()

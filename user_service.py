from supabase_client import supabase

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

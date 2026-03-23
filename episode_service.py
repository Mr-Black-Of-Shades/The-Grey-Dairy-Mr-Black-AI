from supabase_client import supabase

def get_episode_content(episode_id):

    res = supabase.table("episode_content")\
        .select("*")\
        .eq("episode_id", episode_id)\
        .order("sequence")\
        .execute()

    return res.data

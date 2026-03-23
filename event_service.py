from supabase_client import supabase


def track_event(user_id, event_type, data=None):

    try:
        supabase.table("events").insert({
            "user_id": user_id,
            "event_type": event_type,
            "event_data": data or {}
        }).execute()
    except Exception as e:
        print("EVENT ERROR:", e)

from db import get_cursor
import json


def track_event(user_id, event_type, data=None):

    try:
        cur = get_cursor()

        cur.execute(
            """
            INSERT INTO events (user_id, event_type, event_data)
            VALUES (%s, %s, %s)
            """,
            (user_id, event_type, json.dumps(data or {}))
        )

    except Exception as e:
        print("EVENT ERROR:", e)

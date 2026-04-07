from db import get_cursor
from datetime import datetime


# ================= GET OR CREATE USER =================

def get_or_create_user(telegram_id):

    cur = get_cursor()

    # check user
    cur.execute(
        "SELECT * FROM users WHERE telegram_id = %s",
        (str(telegram_id),)
    )
    user = cur.fetchone()

    if user:
        return user

    # create user
    cur.execute(
        """
        INSERT INTO users (telegram_id, current_episode)
        VALUES (%s, 1)
        RETURNING *
        """,
        (str(telegram_id),)
    )

    return cur.fetchone()


# ================= UPDATE USER BEHAVIOR =================

def update_user_behavior(user_id, episode_id=None, drop_off=None):

    cur = get_cursor()

    cur.execute(
        """
        INSERT INTO user_behavior 
        (user_id, last_active, updated_at, last_episode_seen, drop_off_point)
        VALUES (%s, NOW(), NOW(), %s, %s)
        ON CONFLICT (user_id)
        DO UPDATE SET
            last_active = NOW(),
            updated_at = NOW(),
            last_episode_seen = COALESCE(EXCLUDED.last_episode_seen, user_behavior.last_episode_seen),
            drop_off_point = COALESCE(EXCLUDED.drop_off_point, user_behavior.drop_off_point)
        """,
        (user_id, episode_id, drop_off)
    )


# ================= GET USER BEHAVIOR =================

def get_user_behavior(user_id):

    cur = get_cursor()

    cur.execute(
        "SELECT * FROM user_behavior WHERE user_id = %s",
        (user_id,)
    )

    return cur.fetchone()


# ================= USER STATE LOGIC =================

def get_user_state(user, behavior):

    if user.get("total_spent", 0) > 0:
        return "BUYER"
    
    if behavior and behavior.get("drop_off_point") == "payment":
        return "HESITANT"
    
    if user["current_episode"] >= 2:
        return "HOOKED"
    
    return "CURIOUS"


# ================= USER SUBSCRIPTION LOGIC =================

def has_active_subscription(user):

    # no subscription
    if not user.get("subscription_status"):
        return False

    if user["subscription_status"] != "active":
        return False

    expiry = user.get("subscription_expiry")

    if not expiry:
        return False

    # expired
    if expiry < datetime.utcnow():
        return False

    return True

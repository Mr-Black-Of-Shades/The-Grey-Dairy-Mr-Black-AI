from db import get_cursor


# ================= GET EPISODE =================

def get_episode(episode_id):

    cur = get_cursor()

    cur.execute(
        "SELECT * FROM episodes WHERE id = %s",
        (episode_id,)
    )

    return cur.fetchone()


# ================= CHECK UNLOCK =================

def is_episode_unlocked(user_id, episode_id):

    cur = get_cursor()

    cur.execute(
        """
        SELECT id 
        FROM user_progress 
        WHERE user_id = %s AND episode_id = %s
        """,
        (user_id, episode_id)
    )

    return bool(cur.fetchone())


# ================= UNLOCK EPISODE =================

def unlock_episode(user_id, episode_id):

    # prevent duplicate unlock
    if is_episode_unlocked(user_id, episode_id):
        return True

    cur = get_cursor()

    cur.execute(
        """
        INSERT INTO user_progress (user_id, episode_id, unlocked)
        VALUES (%s, %s, true)
        ON CONFLICT DO NOTHING
        """,
        (user_id, episode_id)
    )

    return True


# ================= GET USER CURRENT EPISODE =================

def get_user_current_episode(telegram_id):

    cur = get_cursor()

    cur.execute(
        "SELECT current_episode FROM users WHERE telegram_id = %s",
        (str(telegram_id),)
    )

    res = cur.fetchone()

    if res:
        return res["current_episode"]

    return 1


# ================= UPDATE USER EPISODE =================

def update_user_episode(telegram_id, episode_id):

    cur = get_cursor()

    cur.execute(
        """
        UPDATE users 
        SET current_episode = %s 
        WHERE telegram_id = %s
        """,
        (episode_id, str(telegram_id))
    )


# ================= GET EPISODE CONTENT =================

def get_episode_content(episode_id):

    cur = get_cursor()

    cur.execute(
        """
        SELECT * 
        FROM episode_content 
        WHERE episode_id = %s 
        ORDER BY sequence
        """,
        (episode_id,)
    )

    return cur.fetchall()


# ================= GET SIDE STORIES =================

def get_side_stories(parent_episode_id):

    cur = get_cursor()

    cur.execute(
        """
        SELECT * 
        FROM episodes 
        WHERE parent_episode_id = %s AND type = 'side'
        """,
        (parent_episode_id,)
    )

    return cur.fetchall()
    

# ================= GET FAN EPISODES =================

def get_fan_episodes(character_id):

    cur = get_cursor()

    cur.execute(
        """
        SELECT *
        FROM episodes
        WHERE character_id = %s AND type = 'fan'
        """,
        (character_id,)
    )

    return cur.fetchall()

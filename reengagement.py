from datetime import datetime, timedelta
from db import get_cursor
from ai_mr_black import generate_state_line


async def reengage_users(bot):

    cur = get_cursor()

    # get all user behaviors
    cur.execute("SELECT * FROM user_behavior")
    users = cur.fetchall()

    for u in users:

        last_active = u["last_active"]

        if datetime.utcnow() - last_active > timedelta(hours=24):

            user_id = u["user_id"]

            # get telegram_id
            cur.execute(
                "SELECT telegram_id FROM users WHERE id = %s",
                (user_id,)
            )

            res = cur.fetchone()

            if not res:
                continue

            chat_id = res["telegram_id"]

            msg = generate_state_line("DORMANT")

            try:
                await bot.send_message(chat_id, msg)
            except:
                pass

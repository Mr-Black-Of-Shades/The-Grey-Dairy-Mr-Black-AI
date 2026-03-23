from datetime import datetime, timedelta
from supabase_client import supabase
from ai_mr_black import generate_state_line

async def reengage_users(bot):

    users = supabase.table("user_behavior").select("*").execute().data

    for u in users:

        last_active = datetime.fromisoformat(u["last_active"])

        if datetime.utcnow() - last_active > timedelta(hours=24):

            user_id = u["user_id"]

            # get telegram_id
            res = supabase.table("users") \
                .select("telegram_id") \
                .eq("id", user_id) \
                .limit(1) \
                .execute()

            if not res.data:
                continue

            chat_id = res.data[0]["telegram_id"]

            msg = generate_state_line("DORMANT")

            try:
                await bot.send_message(chat_id, msg)
            except:
                pass

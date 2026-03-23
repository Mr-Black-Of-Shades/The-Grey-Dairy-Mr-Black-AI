from telegram import Update
from telegram.ext import ContextTypes

from supabase_client import supabase
from episode_service import get_episode_content
from sender import send_episode
from ai_mr_black import generate_line


async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id

    user = supabase.table("users")\
        .select("*")\
        .eq("telegram_id", str(chat_id))\
        .execute().data[0]

    next_episode = user["current_episode"] + 1

    supabase.table("users")\
        .update({"current_episode": next_episode})\
        .eq("telegram_id", str(chat_id))\
        .execute()

    # AI transition
    line = generate_line("User is going deeper into story")
    await context.bot.send_message(chat_id, line)

    content = get_episode_content(next_episode)

    if not content:
        await context.bot.send_message(chat_id, "Nothing more… yet.")
        return

    await send_episode(context.bot, chat_id, content)

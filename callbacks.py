from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from supabase_client import supabase
from episode_service import get_episode_content, get_episode
from sender import send_episode
from ai_mr_black import (
    generate_line,
    generate_voice_line,
    generate_upsell_line
)


async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    data = query.data

    # ================= GET USER =================
    user = supabase.table("users")\
        .select("*")\
        .eq("telegram_id", str(chat_id))\
        .execute().data[0]

    user_id = user["id"]

    # ================= SIDE STORY =================
    if data == "side_story":

        voice_line = generate_voice_line(
            "She",
            "Reveal her version of the same night, emotional and mysterious."
        )

        await context.bot.send_message(chat_id, voice_line)

        return

    # ================= SKIP =================
    if data == "skip":
        await context.bot.send_message(chat_id, "Some truths don’t wait forever.")
        return

    # ================= NEXT EPISODE =================
    next_episode = user["current_episode"] + 1

    episode = get_episode(next_episode)

    if not episode:
        await context.bot.send_message(chat_id, "Nothing more… yet.")
        return

    price = episode.get("price", 0)

    # ================= CHECK UNLOCK =================
    progress = supabase.table("user_progress")\
        .select("*")\
        .eq("user_id", user_id)\
        .eq("episode_id", next_episode)\
        .execute()

    is_unlocked = bool(progress.data)

    # ================= LOCKED FLOW =================
    if price > 0 and not is_unlocked:

        # AI upsell
        upsell_line = generate_upsell_line()
        await context.bot.send_message(chat_id, upsell_line)

        payment_link = f"https://your-payment-link.com/pay?episode={next_episode}"

        keyboard = [
            [InlineKeyboardButton(f"Unlock ₹{price}", url=payment_link)],
            [InlineKeyboardButton("Maybe later", callback_data="skip")]
        ]

        await context.bot.send_message(
            chat_id,
            "This part isn’t free.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    # ================= UNLOCKED FLOW =================

    # update episode pointer
    supabase.table("users")\
        .update({"current_episode": next_episode})\
        .eq("telegram_id", str(chat_id))\
        .execute()

    # AI transition
    line = generate_line("User is going deeper into the story.")
    await context.bot.send_message(chat_id, line)

    # send content
    content = get_episode_content(next_episode)
    await send_episode(context.bot, chat_id, content)

    # ================= MULTI-VOICE TRIGGER =================
    if next_episode == 2:

        voice_line = generate_voice_line(
            "Unknown Voice",
            "Reveal that someone else experienced the same moment differently."
        )

        keyboard = [
            [InlineKeyboardButton("See her side", callback_data="side_story")]
        ]

        await context.bot.send_message(
            chat_id,
            voice_line,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

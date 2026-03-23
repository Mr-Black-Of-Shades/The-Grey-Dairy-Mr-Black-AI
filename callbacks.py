from telegram import Update
from telegram.ext import ContextTypes

from ai_mr_black import generate_voice_line


async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    data = query.data

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
        await context.bot.send_message(
            chat_id,
            "Some truths don’t wait forever."
        )
        return

    # ================= PAYMENT (PLACEHOLDER) =================
    if data.startswith("pay_"):
        await context.bot.send_message(
            chat_id,
            "Payment system coming next..."
        )
        return

    # ================= MICRO (PLACEHOLDER) =================
    if data.startswith("micro_"):
        await context.bot.send_message(
            chat_id,
            "This part isn’t fully visible yet..."
        )
        return

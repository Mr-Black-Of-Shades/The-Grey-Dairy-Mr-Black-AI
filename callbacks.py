from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ai_mr_black import generate_voice_line, generate_upsell_line


async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    data = query.data

    # ================= SIDE STORY (UPGRADED) =================
    if data == "side_story":

        text = """She remembers it very differently.

You’re only hearing one version.

Unlock her side: ₹49
"""

        keyboard = [
            [InlineKeyboardButton("Unlock her side (₹49)", callback_data="pay_side")],
            [InlineKeyboardButton("Ignore", callback_data="skip")]
        ]

        await context.bot.send_message(
            chat_id,
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # ================= SKIP =================
    if data == "skip":
        await context.bot.send_message(
            chat_id,
            "Some truths don’t wait forever."
        )
        return

    # ================= PAYMENT =================
    if data.startswith("pay_"):

        # 🔥 AI upsell before payment
        upsell = generate_upsell_line()
        await context.bot.send_message(chat_id, upsell)

        await context.bot.send_message(
            chat_id,
            "Payment system coming next..."
        )
        return

    # ================= MICRO =================
    if data.startswith("micro_"):

        upsell = generate_upsell_line()
        await context.bot.send_message(chat_id, upsell)

        await context.bot.send_message(
            chat_id,
            "This part isn’t fully visible yet..."
        )
        return

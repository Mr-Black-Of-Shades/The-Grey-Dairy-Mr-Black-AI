from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from user_service import get_or_create_user
from episode_service import get_episode_content
from sender import send_episode
from ai_mr_black import generate_line


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id

    user = get_or_create_user(chat_id)

    # AI intro
    intro = generate_line("User entered for first time")
    await context.bot.send_message(chat_id, intro)

    hook = generate_line("Make user curious")
    await context.bot.send_message(chat_id, hook)

    episode_id = user["current_episode"]

    content = get_episode_content(episode_id)

    await send_episode(context.bot, chat_id, content)

    keyboard = [[InlineKeyboardButton("Continue", callback_data="next")]]

    await context.bot.send_message(
        chat_id,
        "Continue?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

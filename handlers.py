from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import asyncio

from user_service import (
    get_or_create_user,
    get_user_behavior,
    get_user_state,
    update_user_behavior
)

from episode_service import get_episode_content, get_side_stories
from episode_service import get_episode, is_episode_unlocked, update_user_episode
from sender import send_episode
from event_service import track_event

from ai_mr_black import generate_line, generate_state_line



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id

    user = get_or_create_user(chat_id)
    track_event(user["id"], "session_start")

    # ✅ behavior fetch
    behavior = get_user_behavior(user["id"])

    # 👇 NEW USER FIX
    if not behavior:
        update_user_behavior(user["id"])
        behavior = get_user_behavior(user["id"])

    # ✅ state detect
    state = get_user_state(user, behavior)

    # ✅ AI state line (NEW)
    await context.bot.send_chat_action(chat_id, "typing")
    intro = generate_state_line(state)

    await context.bot.send_message(chat_id, intro)
    
    await asyncio.sleep(1.2)

    await context.bot.send_chat_action(chat_id, "typing")  # 👈 ADD THIS
    
    hook = generate_line("Make user curious")
    await context.bot.send_message(chat_id, hook)

    episode_id = user["current_episode"]

    content = get_episode_content(episode_id)

    await send_episode(context.bot, chat_id, content)

    track_event(user["id"], "episode_view", {
        "episode_id": episode_id
    })

    # ✅ track behavior
    update_user_behavior(
        user_id=user["id"],
        episode_id=episode_id,
        drop_off="story"
    )

    keyboard = [[InlineKeyboardButton("Continue", callback_data="next")]]

    await context.bot.send_message(
        chat_id,
        "You can stop here… or continue.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )



async def handle_next(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id

    user = get_or_create_user(chat_id)

    current_episode = user["current_episode"]
    next_episode_id = current_episode + 1

    # ✅ check episode
    episode = get_episode(next_episode_id)

    if not episode:
        await context.bot.send_message(chat_id, "No more story...")
        return

    # ================= LOCK CHECK =================

    if episode["price"] > 0 and not is_episode_unlocked(user["id"], next_episode_id):

        # 🔥 mark hesitation
        update_user_behavior(
            user_id=user["id"],
            drop_off="payment"
        )

        # 🧠 AI pressure
        await context.bot.send_chat_action(chat_id, "typing")
        state_line = generate_state_line("HESITANT")
        await context.bot.send_message(chat_id, state_line)
        await asyncio.sleep(0.8)  # 👈 ADD THIS

        track_event(user["id"], "hit_paywall", {
            "episode_id": next_episode_id
        })

        # 🔥 first payment optimization
        if next_episode_id == 2:
            episode["price"] = 49

        price = episode["price"]

        text = f"""Some truths were never meant for everyone.

You’ve reached the part most people avoid.

Unlock this episode: ₹{price}
"""

        keyboard = [
            [InlineKeyboardButton(f"🔓 Continue (₹{price})", callback_data=f"pay_{next_episode_id}")],
            [InlineKeyboardButton("👁 See what you missed (₹49)", callback_data=f"micro_{next_episode_id}")]
        ]

        await context.bot.send_message(
            chat_id,
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    # ================= SEND EPISODE =================

    content = get_episode_content(next_episode_id)

    await send_episode(context.bot, chat_id, content)

    track_event(user["id"], "episode_view", {
        "episode_id": next_episode_id
    })
    
    await asyncio.sleep(1)  # 👈 feels like thinking

    # ✅ update episode in DB
    update_user_episode(chat_id, next_episode_id)

    # ✅ track behavior
    update_user_behavior(
        user_id=user["id"],
        episode_id=next_episode_id,
        drop_off="story"
    )

    # ✅ refresh user (IMPORTANT)
    user = get_or_create_user(chat_id)

    # ================= STATE MESSAGE =================

    behavior = get_user_behavior(user["id"])
    state = get_user_state(user, behavior)

    await context.bot.send_chat_action(chat_id, "typing")

    state_line = generate_state_line(state)
    await context.bot.send_message(chat_id, state_line)

    await asyncio.sleep(0.5)
    await context.bot.send_chat_action(chat_id, "typing")


    # ================= SIDE STORIES =================

    side_stories = get_side_stories(next_episode_id)
    
    buttons = []
    
    # continue button always
    buttons.append([InlineKeyboardButton("Continue", callback_data="next")])
    
    # add side stories if exist
    for side in side_stories:
        buttons.append([
            InlineKeyboardButton(
                f"👁️ {side['title']} (₹{side['price']})",
                callback_data=f"side_{side['id']}"
            )
        ])
    
    await context.bot.send_message(
        chat_id,
        "You can stop here… or explore more.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

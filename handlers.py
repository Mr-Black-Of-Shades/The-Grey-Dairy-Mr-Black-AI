from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import asyncio

from user_service import (
    get_or_create_user,
    get_user_behavior,
    get_user_state,
    update_user_behavior
)

from episode_service import (
    get_episode_content,
    get_side_stories,
    get_episode,
    is_episode_unlocked,
    update_user_episode
)

from sender import send_episode
from event_service import track_event
from ai_mr_black import generate_line, generate_state_line


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id

    user = get_or_create_user(chat_id)
    track_event(user["id"], "session_start")

    behavior = get_user_behavior(user["id"])

    if not behavior:
        update_user_behavior(user["id"])
        behavior = get_user_behavior(user["id"])

    state = get_user_state(user, behavior)

    await context.bot.send_chat_action(chat_id, "typing")
    intro = generate_state_line(state)
    await context.bot.send_message(chat_id, intro)

    await asyncio.sleep(1.2)

    hook = generate_line("Make user curious")
    await context.bot.send_message(chat_id, hook)

    episode_id = user["current_episode"]
    content = get_episode_content(episode_id)

    await send_episode(context.bot, chat_id, content)

    track_event(user["id"], "episode_view", {"episode_id": episode_id})

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

    next_episode_id = user["current_episode"] + 1
    episode = get_episode(next_episode_id)

    if not episode:
        await context.bot.send_message(chat_id, "No more story...")
        return

    # ================= LOCK =================

    if episode["price"] > 0 and not is_episode_unlocked(user["id"], next_episode_id):

        update_user_behavior(user_id=user["id"], drop_off="payment")

        await context.bot.send_chat_action(chat_id, "typing")
        await context.bot.send_message(chat_id, generate_state_line("HESITANT"))

        track_event(user["id"], "hit_paywall", {
            "episode_id": next_episode_id
        })

        price = 49 if next_episode_id == 2 else episode["price"]

        keyboard = [
            [InlineKeyboardButton(f"🔓 Continue (₹{price})", callback_data=f"pay_{next_episode_id}")],
            [InlineKeyboardButton("👁 See what you missed (₹49)", callback_data=f"micro_{next_episode_id}")]
        ]

        await context.bot.send_message(
            chat_id,
            f"Unlock this episode: ₹{price}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # ================= PLAY =================

    content = get_episode_content(next_episode_id)
    await send_episode(context.bot, chat_id, content)

    track_event(user["id"], "episode_view", {"episode_id": next_episode_id})

    update_user_episode(chat_id, next_episode_id)

    update_user_behavior(
        user_id=user["id"],
        episode_id=next_episode_id,
        drop_off="story"
    )

    await asyncio.sleep(1)

    # ================= SIDE STORIES =================

    side_stories = get_side_stories(next_episode_id)

    if side_stories:

        track_event(user["id"], "side_story_shown", {
            "episode_id": next_episode_id,
            "count": len(side_stories)
        })

        await context.bot.send_message(
            chat_id,
            generate_line("Something feels off…")
        )

        await asyncio.sleep(0.5)

        buttons = []

        # 🔥 side first (money first)
        for side in side_stories:
            buttons.append([
                InlineKeyboardButton(
                    f"👁️ {side['title']} (₹{side['price']})",
                    callback_data=f"side_{side['id']}"
                )
            ])

        buttons.append([InlineKeyboardButton("Continue", callback_data="next")])

        await context.bot.send_message(
            chat_id,
            "But that’s not the full story...\n\nSomeone else saw it differently.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    else:
        keyboard = [[InlineKeyboardButton("Continue", callback_data="next")]]

        await context.bot.send_message(
            chat_id,
            "You can stop here… or continue.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


    # ================= FAN ZONE TRIGGER =================
    
    if next_episode_id >= 3:
    
        await context.bot.send_message(
            chat_id,
            generate_line("There’s something else… something hidden.")
        )
    
        await context.bot.send_message(
            chat_id,
            "Not everyone tells the same story.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "Enter Fan Zone",
                    callback_data=f"fan_{episode['character_id']}"
                )]
            ])
        )

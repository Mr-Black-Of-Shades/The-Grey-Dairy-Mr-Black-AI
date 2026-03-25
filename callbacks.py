from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ai_mr_black import generate_voice_line, generate_upsell_line
from event_service import track_event
from db import get_cursor

from episode_service import get_episode, unlock_episode, get_episode_content
from sender import send_episode
from user_service import update_user_behavior


async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id

    # ================= GET USER =================
    try:
        cur = get_cursor()
        cur.execute(
            "SELECT id FROM users WHERE telegram_id = %s",
            (str(chat_id),)
        )
        user_res = cur.fetchone()
    except:
        return
    
    if not user_res:
        return
    
    user_id = user_res["id"]
    
    data = query.data

   
    # ================= SKIP =================
    if data == "skip":
        await context.bot.send_message(
            chat_id,
            "Some truths don’t wait forever."
        )
        return


    # ================= SIDE STORY CLICK =================
    if data.startswith("side_"):
    
        side_episode_id = int(data.split("_")[1])
    
        episode = get_episode(side_episode_id)
    
        # track click
        track_event(user_id, "side_story_click", {
            "episode_id": side_episode_id,
            "character_id": episode["character_id"]
        })
    
        # if paid
        if episode["price"] > 0:
            await context.bot.send_message(
                chat_id,
                f"Unlock this story: ₹{episode['price']}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        f"🔓 Unlock (₹{episode['price']})",
                        callback_data=f"pay_{side_episode_id}"
                    )]
                ])
            )
            return
    
        # free story
        unlock_episode(user_id, side_episode_id)

        update_user_behavior(
            user_id=user_id,
            episode_id=side_episode_id,
            drop_off="side_story"
        )
    
        track_event(user_id, "side_story_unlock", {
            "episode_id": side_episode_id,
            "character_id": episode["character_id"]
        })
    

        content = get_episode_content(side_episode_id)
        
        await send_episode(context.bot, chat_id, content)

        await context.bot.send_message(
            chat_id,
            "Now… back to where we were.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Continue", callback_data="next")]
            ])
        )
    
        return


    # ================= PAYMENT =================
    if data.startswith("pay_"):

        episode_id = int(data.replace("pay_", ""))

        track_event(user_id, "click_pay", {
            "episode_id": episode_id,
            "button": data
        })
        
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

        track_event(user_id, "click_micro")
        
        upsell = generate_upsell_line()
        await context.bot.send_message(chat_id, upsell)

        await context.bot.send_message(
            chat_id,
            "This part isn’t fully visible yet..."
        )
        return

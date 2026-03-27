from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ai_mr_black import generate_voice_line, generate_upsell_line
from event_service import track_event
from db import get_cursor

from episode_service import get_episode, unlock_episode, get_episode_content
from sender import send_episode
from user_service import update_user_behavior

from config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET

import razorpay


# ================= RAZORPAY CLIENT =================

razorpay_client = razorpay.Client(auth=(
    RAZORPAY_KEY_ID,
    RAZORPAY_KEY_SECRET
))


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
    
        track_event(user_id, "side_story_click", {
            "episode_id": side_episode_id,
            "character_id": episode["character_id"]
        })
    
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


    # ================= FAN ZONE =================
    if data.startswith("fan_"):
    
        character_id = data.split("_")[1]
    
        from episode_service import get_fan_episodes
    
        fan_episodes = get_fan_episodes(character_id)
    
        if not fan_episodes:
            await context.bot.send_message(
                chat_id,
                "Nothing here... yet."
            )
            return
    
        buttons = []
    
        for ep in fan_episodes:
            buttons.append([
                InlineKeyboardButton(
                    f"{ep['title']} (₹{ep['price']})",
                    callback_data=f"side_{ep['id']}"
                )
            ])
    
        buttons.append([InlineKeyboardButton("Back", callback_data="next")])
    
        await context.bot.send_message(
            chat_id,
            "This is where their story changes…",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
        return

    
    # ================= PAYMENT (UPGRADED) =================
    if data.startswith("pay_"):

        episode_id = int(data.replace("pay_", ""))

        episode = get_episode(episode_id)
        amount = episode["price"]

        track_event(user_id, "click_pay", {
            "episode_id": episode_id,
            "amount": amount
        })

        # 🔥 AI upsell
        upsell = generate_upsell_line()
        await context.bot.send_message(chat_id, upsell)

        try:
            # ================= CREATE PAYMENT LINK =================
            payment = razorpay_client.payment_link.create({
                "amount": amount * 100,
                "currency": "INR",
                "description": f"Unlock Episode {episode_id}",
                "customer": {
                    "name": f"user_{user_id}",
                    "email": "user@example.com"
                },
                "notify": {
                    "sms": False,
                    "email": False
                },
                "reminder_enable": True
            })

            payment_link_id = payment["id"]
            payment_link_url = payment["short_url"]

            # ================= SAVE TO DB =================
            cur = get_cursor()
            cur.execute(
                """
                INSERT INTO payments (user_id, episode_id, amount, status, razorpay_order_id, character_id)
                VALUES (%s, %s, %s, 'pending', %s, %s)
                """,
                (user_id, episode_id, amount, payment_link_id, episode["character_id"])
            )

            # ================= SEND LINK =================
            await context.bot.send_message(
                chat_id,
                f"🔓 Complete your payment:\n{payment_link_url}"
            )

        except Exception as e:
            print("PAYMENT LINK ERROR:", e)

            await context.bot.send_message(
                chat_id,
                "Something went wrong while creating payment. Try again."
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

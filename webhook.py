from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from config import BOT_TOKEN, WEBHOOK_URL, ADMIN_SECRET
from handlers import start, handle_next
from callbacks import handle_buttons

from payments import router as payment_router

from pydantic import BaseModel
from typing import Literal
from db import get_cursor


app = FastAPI()

# 💰 include payment routes
app.include_router(payment_router)

telegram_app = Application.builder().token(BOT_TOKEN).build()


# ================= REGISTER HANDLERS =================

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CallbackQueryHandler(handle_next, pattern="^next$"))
telegram_app.add_handler(CallbackQueryHandler(handle_buttons))


# 🖤 MEDIA CAPTURE HANDLER (NEW)
async def capture_media(update: Update, context):

    # 🔒 CHECK USER
    user_id = str(update.effective_user.id)

    # ❌ BLOCK NON-ADMIN
    if user_id not in ADMIN_SECRET:
        return

    # 🔒 ONLY PRIVATE CHAT
    if update.effective_chat.type != "private":
        return

    cur = get_cursor()

    # 🎬 VIDEO
    if update.message.video:
        file_id = update.message.video.file_id

        cur.execute(
            "INSERT INTO media_files (file_id, type) VALUES (%s, %s)",
            (file_id, "video")
        )

        await update.message.reply_text("✅ Video saved")

    # 🖼️ IMAGE
    elif update.message.photo:
        file_id = update.message.photo[-1].file_id

        cur.execute(
            "INSERT INTO media_files (file_id, type) VALUES (%s, %s)",
            (file_id, "photo")
        )

        await update.message.reply_text("✅ Image saved")


# 🔥 REGISTER MEDIA HANDLER
telegram_app.add_handler(
    MessageHandler(filters.VIDEO | filters.PHOTO, capture_media)
)


# ================= STARTUP =================

@app.on_event("startup")
async def startup():
    await telegram_app.initialize()

    await telegram_app.bot.set_webhook(
        url=f"{WEBHOOK_URL}/webhook"
    )

    print("Webhook set successfully")


# ================= WEBHOOK =================

@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, telegram_app.bot)

    await telegram_app.process_update(update)

    return {"ok": True}


# ================= STUDIO APIs =================


# ---------- MODELS ----------

class EpisodeCreate(BaseModel):
    title: str
    type: Literal["main", "side", "fan"]
    price: int = 0
    character_id: str
    parent_episode_id: int | None = None


class ContentSave(BaseModel):
    episode_id: int
    blocks: list


# ---------- CREATE EPISODE ----------

@app.post("/studio/episode/create")
async def create_episode(data: EpisodeCreate):

    try:
        cur = get_cursor()

        cur.execute(
            """
            INSERT INTO episodes (title, type, price, character_id, parent_episode_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                data.title,
                data.type,
                data.price,
                data.character_id,
                data.parent_episode_id
            )
        )

        res = cur.fetchone()

        return {
            "success": True,
            "episode_id": res["id"]
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# ---------- SAVE FULL CONTENT (NEW CORE API) ----------

@app.post("/studio/content/save")
async def save_content(data: ContentSave):

    try:
        cur = get_cursor()

        # DELETE old
        cur.execute(
            "DELETE FROM episode_content WHERE episode_id = %s",
            (data.episode_id,)
        )

        # INSERT new
        for i, block in enumerate(data.blocks, start=1):
            cur.execute(
                """
                INSERT INTO episode_content (episode_id, type, content, sequence)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    data.episode_id,
                    block["type"],
                    block.get("content"),
                    i
                )
            )

        return {"success": True}

    except Exception as e:
        return {"success": False, "error": str(e)}


# ---------- GET CONTENT ----------

@app.get("/studio/content/{episode_id}")
async def get_content(episode_id: int):

    try:
        cur = get_cursor()

        cur.execute(
            """
            SELECT id, type, content, sequence
            FROM episode_content
            WHERE episode_id = %s
            ORDER BY sequence
            """,
            (episode_id,)
        )

        return cur.fetchall()

    except Exception as e:
        return {"success": False, "error": str(e)}


# ---------- MEDIA LIST ----------

@app.get("/studio/media")
async def get_media():

    try:
        cur = get_cursor()

        cur.execute(
            """
            SELECT id, file_id, type
            FROM media_files
            ORDER BY id DESC
            """
        )

        return cur.fetchall()

    except Exception as e:
        return {"success": False, "error": str(e)}


# ---------- GET EPISODES ----------

@app.get("/studio/episode/list")
async def get_episodes():

    try:
        cur = get_cursor()

        cur.execute(
            """
            SELECT id, title, type, price
            FROM episodes
            ORDER BY id DESC
            """
        )

        return cur.fetchall()

    except Exception as e:
        return {"success": False, "error": str(e)}

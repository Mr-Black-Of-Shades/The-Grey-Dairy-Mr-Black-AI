from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from config import BOT_TOKEN, WEBHOOK_URL
from handlers import start, handle_next
from callbacks import handle_buttons

from payments import router as payment_router  # 💰 NEW

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


# ================= STARTUP =================

@app.on_event("startup")
async def startup():
    await telegram_app.initialize()

    await telegram_app.bot.set_webhook(
        url=f"{WEBHOOK_URL}/webhook"
    )

    print("Webhook set successfully")


# ================= WEBHOOK ENDPOINT =================

@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, telegram_app.bot)

    await telegram_app.process_update(update)

    return {"ok": True}


# ================= STUDIO APIs =================


# ---------- REQUEST MODELS ----------

class EpisodeCreate(BaseModel):
    title: str
    type: Literal["main", "side", "fan"]
    price: int = 0
    character_id: str
    parent_episode_id: int | None = None


class ContentCreate(BaseModel):
    episode_id: int
    type: Literal["text", "photo", "video"]
    content: str
    sequence: int | None = None


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


# ---------- ADD CONTENT ----------

@app.post("/studio/content/add")
async def add_content(data: ContentCreate):

    try:
        cur = get_cursor()

        # AUTO SEQUENCE
        if data.sequence is None:
            cur.execute(
                """
                SELECT COALESCE(MAX(sequence), 0) + 1 AS next_seq
                FROM episode_content
                WHERE episode_id = %s
                """,
                (data.episode_id,)
            )
            seq = cur.fetchone()["next_seq"]
        else:
            seq = data.sequence

        cur.execute(
            """
            INSERT INTO episode_content (episode_id, type, content, sequence)
            VALUES (%s, %s, %s, %s)
            """,
            (
                data.episode_id,
                data.type,
                data.content,
                seq
            )
        )

        return {"success": True}

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

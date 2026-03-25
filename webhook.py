from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from config import BOT_TOKEN
from handlers import start, handle_next
from callbacks import handle_buttons

import os

app = FastAPI()

telegram_app = Application.builder().token(BOT_TOKEN).build()


# ================= REGISTER HANDLERS =================

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CallbackQueryHandler(handle_next, pattern="^next$"))
telegram_app.add_handler(CallbackQueryHandler(handle_buttons))


# ================= STARTUP =================

@app.on_event("startup")
async def startup():
    await telegram_app.initialize()

    WEBHOOK_URL = os.getenv("WEBHOOK_URL")

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

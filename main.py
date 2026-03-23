from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler

from config import BOT_TOKEN
from handlers import start, handle_next
from callbacks import handle_buttons


def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    # ✅ NEXT button handler
    app.add_handler(CallbackQueryHandler(handle_next, pattern="^next$"))

    # ✅ other buttons (pay, micro etc.)
    app.add_handler(CallbackQueryHandler(handle_buttons))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()

async def send_episode(bot, chat_id, content):

    for item in content:

        if item["type"] == "text":
            await bot.send_message(chat_id, item["content"])

        elif item["type"] == "photo":
            await bot.send_photo(chat_id, item["content"])

        elif item["type"] == "video":
            await bot.send_video(chat_id, item["content"])

# set_webhook.py
import asyncio
import os
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing. Set it in environment before running set_webhook.py")

RENDER_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
WEBHOOK_URL = os.getenv("WEBHOOK_URL") or (f"https://{RENDER_HOSTNAME}/webhook/{BOT_TOKEN}" if RENDER_HOSTNAME else None)

if not WEBHOOK_URL:
    raise RuntimeError("WEBHOOK_URL not available. Set RENDER_EXTERNAL_HOSTNAME or WEBHOOK_URL env var.")

async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.set_webhook(WEBHOOK_URL)
        print("✅ Webhook set:", WEBHOOK_URL)
    finally:
        # close session cleanly
        try:
            await bot.session.close()
        except Exception:
            pass

if __name__ == "__main__":
    asyncio.run(main())

import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# --- CONFIG (Isko waise hi rehne dein) ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE_WEBHOOK_URL = os.getenv("BASE_WEBHOOK_URL")

# Yeh check karega ki environment variables set hain ya nahi
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable not set!")
if not BASE_WEBHOOK_URL:
    raise RuntimeError("BASE_WEBHOOK_URL environment variable not set!")

# Webhook settings
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}"

# Server settings
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.getenv("PORT", 8080))

# Bot aur Dispatcher setup
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


# --- BOT HANDLER (Sirf ek command) ---
@dp.message(Command("start"))
async def cmd_start(message: Message):
    """/start command par yeh function chalega"""
    await message.answer("Hello! Bot bilkul theek se kaam kar raha hai.")


# --- APP LIFECYCLE (Webhook set karne ke liye) ---
async def on_startup(bot: Bot) -> None:
    """Server start hone par webhook set karega"""
    await bot.set_webhook(url=WEBHOOK_URL)
    print(f"Webhook set to: {WEBHOOK_URL}")

async def on_shutdown(bot: Bot) -> None:
    """Server band hone par webhook delete karega"""
    await bot.delete_webhook()
    print("Webhook deleted.")


# --- MAIN FUNCTION (Bot ko start karne ke liye) ---
def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    setup_application(app, dp, bot=bot)
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)


if __name__ == "__main__":
    main()

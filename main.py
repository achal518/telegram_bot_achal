import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from flask import Flask

# logging setup
logging.basicConfig(level=logging.INFO)

# bot token from environment variable (safe way)
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN provided. Please set it in Render secrets.")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ====== BOT HANDLERS ======

# start command
@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("👋 Hello", callback_data="hello"),
        types.InlineKeyboardButton("📚 Help", callback_data="help"),
        types.InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
        types.InlineKeyboardButton("🎲 Random", callback_data="random"),
        types.InlineKeyboardButton("📢 Updates", callback_data="updates"),
        types.InlineKeyboardButton("📝 Notes", callback_data="notes"),
        types.InlineKeyboardButton("💡 Tips", callback_data="tips"),
        types.InlineKeyboardButton("🔗 Links", callback_data="links"),
        types.InlineKeyboardButton("❓ About", callback_data="about"),
        types.InlineKeyboardButton("🚀 Extra", callback_data="extra"),
    )
    await message.answer("👋 Welcome! Choose an option below:", reply_markup=keyboard)

# handle button callbacks
@dp.callback_query_handler(lambda c: True)
async def process_callback(callback_query: types.CallbackQuery):
    data = callback_query.data
    responses = {
        "hello": "Hello! 👋",
        "help": "Here’s some help 📚",
        "settings": "Settings panel ⚙️",
        "random": "Random number 🎲: " + str(os.urandom(1)[0]),
        "updates": "Latest updates 📢",
        "notes": "Write your notes 📝",
        "tips": "Here are some tips 💡",
        "links": "Some useful links 🔗",
        "about": "This is a demo bot ❓",
        "extra": "Extra feature 🚀",
    }
    response = responses.get(data, "Unknown option ❌")
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, response)

# ====== FLASK APP for Render ======
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running ✅"

# ====== START BOT ======
if __name__ == "__main__":
    import threading

    # run flask server in separate thread
    def run_flask():
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

    threading.Thread(target=run_flask).start()

    # run aiogram bot
    executor.start_polling(dp, skip_updates=True)

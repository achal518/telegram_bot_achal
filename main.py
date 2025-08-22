
from flask import Flask
from pyrogram import Client, filters
import os
import random
import datetime

# Flask app for keep-alive
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running fine!"

# Pyrogram bot
API_ID = int(os.getenv("API_ID"))       # Secret me dalna
API_HASH = os.getenv("API_HASH")        # Secret me dalna
BOT_TOKEN = os.getenv("BOT_TOKEN")      # Secret me dalna

bot = Client(
    "my_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Jokes & Quotes
jokes = [
    "😂 Why did the computer go to the doctor? Because it caught a virus!",
    "🤣 I asked my laptop for a joke… it said '404 Joke Not Found!'",
    "😜 Why was the math book sad? Because it had too many problems."
]

quotes = [
    "🌟 Believe in yourself!",
    "🚀 Dreams don’t work unless you do.",
    "🔥 Stay positive, work hard, make it happen."
]

# /start command with inline keyboard
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@bot.on_message(filters.command("start"))
async def start(client, message):
    keyboard = [
        [InlineKeyboardButton("📌 About Bot", callback_data="about")],
        [InlineKeyboardButton("👤 My Profile", callback_data="profile")],
        [InlineKeyboardButton("⏰ Time & Date", callback_data="time")],
        [InlineKeyboardButton("😂 Random Joke", callback_data="joke")],
        [InlineKeyboardButton("💡 Quote", callback_data="quote")],
        [InlineKeyboardButton("❌ Exit", callback_data="exit")]
    ]
    await message.reply("Welcome! Choose an option 👇", reply_markup=InlineKeyboardMarkup(keyboard))

# Button handler
@bot.on_callback_query()
async def callback(client, query):
    if query.data == "about":
        text = "🤖 This is a simple Pyrogram bot with inline buttons."
    elif query.data == "profile":
        user = query.from_user
        text = f"👤 Profile:\nName: {user.first_name}\nUsername: @{user.username}\nID: {user.id}"
    elif query.data == "time":
        text = f"⏰ Current Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    elif query.data == "joke":
        text = random.choice(jokes)
    elif query.data == "quote":
        text = random.choice(quotes)
    elif query.data == "exit":
        text = "❌ Bot stopped. Type /start to begin again."
    else:
        text = "⚠️ Unknown option!"
    
    await query.message.edit_text(text)

# Run Flask + Bot
if __name__ == "__main__":
    import threading

    # Run Flask server in background
    def run_flask():
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

    t = threading.Thread(target=run_flask)
    t.start()

    # Run Telegram bot
    bot.run()

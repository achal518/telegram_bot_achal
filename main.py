# -*- coding: utf-8 -*-
import asyncio
import os
import random
import string
import time
from datetime import datetime, timedelta

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
)
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# ========== CONFIG ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing. Set it in Environment.")

# Yeh Render.com environment variable se aayega. Example: https://your-app-name.onrender.com
BASE_WEBHOOK_URL = os.getenv("BASE_WEBHOOK_URL")

OWNER_NAME = os.getenv("OWNER_NAME", "Achal")
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "your_username_here")

# Webhook settings
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_SECRET = "my_super_secret_string_12345" # aap isko badal sakte hain
WEBHOOK_URL = f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}"

# Web server settings
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.getenv("PORT", 8080)) # Render PORT variable use karega

# Bot and Dispatcher
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
START_TIME = time.time()
user_state = {}  # in-memory session state

# ---------- helpers (SAME AS BEFORE) ----------
def ensure_user(uid: int):
    if uid not in user_state:
        user_state[uid] = {"echo": False, "mode": None, "design_style": None, "guess_target": None}

def format_uptime(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def now_ist_str() -> str:
    ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    return ist.strftime("%Y-%m-%d %H:%M:%S")

def to_fullwidth(text: str) -> str:
    out = []
    for ch in text:
        if ch == " ":
            out.append(" ")
        elif 33 <= ord(ch) <= 126:
            out.append(chr(ord(ch) + 0xFEE0))
        else:
            out.append(ch)
    return "".join(out)

def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🙋‍♂️ Greet Me", callback_data="greet")],
        [InlineKeyboardButton(text="🎮 Dice Game", callback_data="game_dice"),
         InlineKeyboardButton(text="🔢 Guess Game", callback_data="game_guess")],
        [InlineKeyboardButton(text="🔁 Echo Mode", callback_data="toggle_echo"),
         InlineKeyboardButton(text="🖌 Design Msg", callback_data="design_menu")],
        [InlineKeyboardButton(text="🎨 Image Magic", callback_data="image_gen"),
         InlineKeyboardButton(text="⏱ Bot Status", callback_data="bot_status")],
        [InlineKeyboardButton(text="👑 Owner", callback_data="owner"),
         InlineKeyboardButton(text="ℹ️ About", callback_data="about")],
        [InlineKeyboardButton(text="📚 Help", callback_data="help"),
         InlineKeyboardButton(text="🔗 Links", callback_data="links")],
        [InlineKeyboardButton(text="❌ Close", callback_data="close")]
    ])

def design_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🅱️ Bold", callback_data="design_bold"),
         InlineKeyboardButton(text="𝑰 Italic", callback_data="design_italic"),
         InlineKeyboardButton(text="</> Mono", callback_data="design_mono")],
        [InlineKeyboardButton(text="✨ Fancy", callback_data="design_fancy")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_menu")]
    ])

# ========== BOT HANDLERS (SAME AS BEFORE) ==========
# Yahan par aapke saare purane bot handlers (cmd_start, cb_greet, etc.) aayenge.
# Maine neeche sab paste kar diya hai, koi change nahi karna hai.

@dp.message(Command("start"))
async def cmd_start(message: Message):
    ensure_user(message.from_user.id)
    greet = f"👋 <b>Welcome, {message.from_user.first_name or 'buddy'}!</b>\nMain tumhara personal bot hoon — niche se feature choose karo 👇"
    await message.answer(greet, reply_markup=main_menu())

@dp.message(Command("help"))
async def cmd_help(message: Message):
    text = ("📚 <b>Help</b>\n"
            "/start — Main menu\n"
            "/help — This help\n"
            "/menu — Show menu\n"
            "/cancel — Cancel current mode\n")
    await message.answer(text, reply_markup=main_menu())

@dp.message(Command("menu"))
async def cmd_menu(message: Message):
    await message.answer("📋 <b>Main Menu</b>", reply_markup=main_menu())

@dp.message(Command("cancel"))
async def cmd_cancel(message: Message):
    uid = message.from_user.id
    ensure_user(uid)
    user_state[uid]["mode"] = None
    user_state[uid]["design_style"] = None
    user_state[uid]["guess_target"] = None
    await message.answer("✅ Mode cancelled. Back to menu.", reply_markup=main_menu())

# CALLBACKS
@dp.callback_query(F.data == "greet")
async def cb_greet(cb: CallbackQuery):
    u = cb.from_user
    await cb.message.answer(f"🙏 Namaste {u.first_name or 'dost'}! Aaj kya explore karna chahoge? 😊", reply_markup=main_menu())
    await cb.answer()

@dp.callback_query(F.data == "owner")
async def cb_owner(cb: CallbackQuery):
    text = f"👑 <b>Owner</b>\nName: <b>{OWNER_NAME}</b>\nUsername: @{OWNER_USERNAME}\nContact: Telegram DM"
    await cb.message.answer(text, reply_markup=main_menu())
    await cb.answer()

@dp.callback_query(F.data == "bot_status")
async def cb_status(cb: CallbackQuery):
    up = int(time.time() - START_TIME)
    try:
        import aiogram
        ver = aiogram.__version__
    except Exception:
        ver = "unknown"
    text = (f"⏱ <b>Bot Status</b>\nUptime: <code>{format_uptime(up)}</code>\nServer (IST): <code>{now_ist_str()}</code>\nAiogram: <code>{ver}</code>\nMode: Webhook ✅")
    await cb.message.answer(text, reply_markup=main_menu())
    await cb.answer()

@dp.callback_query(F.data == "about")
async def cb_about(cb: CallbackQuery):
    text = "ℹ️ <b>About</b>\nYe bot inline buttons, games, echo, design text, fake image-gen, status—all-in-one."
    await cb.message.answer(text, reply_markup=main_menu())
    await cb.answer()

@dp.callback_query(F.data == "links")
async def cb_links(cb: CallbackQuery):
    await cb.message.answer("🔗 Useful Links\n• Telegram: https://telegram.org\n• BotFather: https://t.me/BotFather", reply_markup=main_menu())
    await cb.answer()

@dp.callback_query(F.data == "game_dice")
async def cb_dice(cb: CallbackQuery):
    await cb.answer()
    msg = await bot.send_dice(chat_id=cb.message.chat.id, emoji="🎲")
    await bot.send_message(cb.message.chat.id, f"🎯 Dice rolled: <b>{msg.dice.value}</b>", reply_markup=main_menu())

@dp.callback_query(F.data == "game_guess")
async def cb_guess_start(cb: CallbackQuery):
    uid = cb.from_user.id
    ensure_user(uid)
    target = random.randint(1, 10)
    user_state[uid]["mode"] = "guess"
    user_state[uid]["guess_target"] = target
    await cb.message.answer("🔢 Guess Game: 1 se 10 ke beech koi number bhejo. (/cancel to stop)")
    await cb.answer()

@dp.callback_query(F.data == "toggle_echo")
async def cb_toggle_echo(cb: CallbackQuery):
    uid = cb.from_user.id
    ensure_user(uid)
    user_state[uid]["echo"] = not user_state[uid]["echo"]
    status = "ON" if user_state[uid]["echo"] else "OFF"
    await cb.message.answer(f"🔁 Echo mode: <b>{status}</b>\nAb jo text bhejoge, bot usko repeat karega.", reply_markup=main_menu())
    await cb.answer()

@dp.callback_query(F.data == "design_menu")
async def cb_design_menu(cb: CallbackQuery):
    uid = cb.from_user.id
    ensure_user(uid)
    user_state[uid]["mode"] = None
    user_state[uid]["design_style"] = None
    await cb.message.answer("🖌 <b>Design Message</b>\nStyle choose karo, phir apna text bhejo:", reply_markup=design_menu_kb())
    await cb.answer()

@dp.callback_query(F.data.in_(["design_bold", "design_italic", "design_mono", "design_fancy"]))
async def cb_design_pick(cb: CallbackQuery):
    uid = cb.from_user.id
    ensure_user(uid)
    mapping = {"design_bold": "bold", "design_italic": "italic", "design_mono": "mono", "design_fancy": "fancy"}
    sel = mapping.get(cb.data, "bold")
    user_state[uid]["mode"] = "design"
    user_state[uid]["design_style"] = sel
    pretty = {"bold": "🅱️ Bold", "italic": "𝑰 Italic", "mono": "</> Mono", "fancy": "✨ Fancy"}[sel]
    await cb.message.answer(f"{pretty} selected.\nAb apna text bhejo. (/cancel to stop)")
    await cb.answer()

@dp.callback_query(F.data == "image_gen")
async def cb_image(cb: CallbackQuery):
    seed = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    url = f"https://picsum.photos/seed/{seed}/700/400"
    caption = "🎨 Image Magic (placeholder). For real AI images use external API."
    try:
        await bot.send_photo(cb.message.chat.id, url, caption=caption)
    except Exception:
        await cb.message.answer("⚠️ Image fetch issue. Try again.")
    await cb.answer()

@dp.callback_query(F.data == "close")
async def cb_close(cb: CallbackQuery):
    try:
        await cb.message.delete()
    except Exception:
        try:
            await cb.message.answer("Window closed.")
        except Exception:
            pass
    await cb.answer()

# Message handler (modes)
@dp.message(F.text)
async def all_text(message: Message):
    uid = message.from_user.id
    ensure_user(uid)

    if user_state[uid]["mode"] == "guess":
        txt = message.text.strip()
        if txt.isdigit():
            n = int(txt)
            target = user_state[uid]["guess_target"]
            if n == target:
                user_state[uid]["mode"] = None
                user_state[uid]["guess_target"] = None
                await message.answer(f"🎉 Correct! Number was <b>{n}</b>.", reply_markup=main_menu())
            else:
                hint = "⬆️ bigger" if n < target else "⬇️ smaller"
                await message.answer(f"❌ Nope, try {hint}. (/cancel to stop)")
        else:
            await message.answer("Send a number between 1–10.")
        return

    if user_state[uid]["mode"] == "design":
        style = user_state[uid]["design_style"] or "bold"
        text = message.text
        if style == "bold":
            out = f"<b>{text}</b>"
        elif style == "italic":
            out = f"<i>{text}</i>"
        elif style == "mono":
            out = f"<code>{text}</code>"
        else:
            out = to_fullwidth(text)
        user_state[uid]["mode"] = None
        user_state[uid]["design_style"] = None
        await message.answer(out, reply_markup=main_menu())
        return

    if user_state[uid]["echo"]:
        await message.answer(message.text)
        return

    await message.answer("🙂 Use /menu or press buttons.", reply_markup=main_menu())

# ========== APP LIFECYCLE ==========
async def on_startup(bot: Bot) -> None:
    # Set bot commands
    cmds = [BotCommand(command="start", description="Open menu"),
            BotCommand(command="help", description="How to use"),
            BotCommand(command="menu", description="Show menu"),
            BotCommand(command="cancel", description="Cancel mode")]
    await bot.set_my_commands(cmds)

    # Set webhook
    await bot.set_webhook(url=WEBHOOK_URL, secret_token=WEBHOOK_SECRET)
    print(f"✅ Webhook set to: {WEBHOOK_URL}")


async def on_shutdown(bot: Bot) -> None:
    # Delete webhook
    await bot.delete_webhook()
    print("✅ Webhook deleted.")


def main():
    # Register lifecycle events
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Create aiohttp app and register handlers
    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    # Mount dispatcher on app and start web server
    setup_application(app, dp, bot=bot)
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)


if __name__ == "__main__":
    main()


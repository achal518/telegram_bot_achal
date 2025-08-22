# -*- coding: utf-8 -*-
import asyncio
import os
import random
import string
import threading
import time
from datetime import datetime, timedelta

from flask import Flask
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
)
from aiogram.filters import Command

# =========================
# CONFIG & GLOBAL STATE
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing. Set it in Render → Environment.")

# Optional owner details (safe defaults if not set)
OWNER_NAME = os.getenv("OWNER_NAME", "Achal")
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "your_username_here")  # without @

# Bot & Dispatcher (use DefaultBotProperties for parse_mode to be compatible with aiogram v3.22)
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Keep-alive Flask for Render
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Bot is alive. (aiogram v3 + Flask on Render)"

# Uptime calc
START_TIME = time.time()

# In-memory user/session state (no DB)
user_state = {}  # user_id -> dict like {"echo": bool, "mode": None/"design"/"guess", "design_style": "bold"/"italic"/"mono"/"fancy", "guess_target": int}

# =========================
# HELPERS
# =========================
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

def format_uptime(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def now_ist_str() -> str:
    # Server time (UTC) + 5:30 for IST
    ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    return ist.strftime("%Y-%m-%d %H:%M:%S")

def ensure_user(uid: int):
    if uid not in user_state:
        user_state[uid] = {"echo": False, "mode": None, "design_style": None, "guess_target": None}

def to_fullwidth(text: str) -> str:
    # simple fancy transform using fullwidth unicode
    out = []
    for ch in text:
        if ch == " ":
            out.append(" ")
        elif 33 <= ord(ch) <= 126:
            out.append(chr(ord(ch) + 0xFEE0))
        else:
            out.append(ch)
    return "".join(out)

# =========================
# COMMANDS
# =========================
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user = message.from_user
    ensure_user(user.id)
    greet = f"👋 <b>Welcome, {user.first_name or 'buddy'}!</b>\n"
    greet += "Main tumhara personal bot hoon — niche se feature choose karo 👇"
    await message.answer(greet, reply_markup=main_menu())

@dp.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "📚 <b>Help</b>\n"
        "/start — Main menu dikhaye\n"
        "/help — Ye help\n"
        "/menu — Main menu\n"
        "/cancel — Current mode cancel\n\n"
        "Inline buttons se games, echo, design, image, owner info, status sab mil jayega."
    )
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

# =========================
# CALLBACKS (BUTTONS)
# =========================
@dp.callback_query(F.data == "greet")
async def cb_greet(cb: CallbackQuery):
    user = cb.from_user
    await cb.message.answer(f"🙏 Namaste {user.first_name or 'dost'}! Aaj kya explore karna chahoge? 😊", reply_markup=main_menu())
    await cb.answer()

@dp.callback_query(F.data == "owner")
async def cb_owner(cb: CallbackQuery):
    text = (
        f"👑 <b>Owner</b>\n"
        f"Name: <b>{OWNER_NAME}</b>\n"
        f"Username: @{OWNER_USERNAME}\n"
        f"Contact: Telegram DM\n\n"
        "Agar koi bug/idea ho to yahin batana!"
    )
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
    text = (
        "⏱ <b>Bot Status</b>\n"
        f"Uptime: <code>{format_uptime(up)}</code>\n"
        f"Server (IST): <code>{now_ist_str()}</code>\n"
        f"Aiogram: <code>{ver}</code>\n"
        "Mode: Polling ✅"
    )
    await cb.message.answer(text, reply_markup=main_menu())
    await cb.answer()

@dp.callback_query(F.data == "about")
async def cb_about(cb: CallbackQuery):
    text = (
        "ℹ️ <b>About</b>\n"
        "Ye bot inline buttons, games, echo, design text, fake image-gen, status—all-in-one feature set ke sath bana hai.\n"
        "Data DB me store nahi hota; sab in-memory session hai."
    )
    await cb.message.answer(text, reply_markup=main_menu())
    await cb.answer()

@dp.callback_query(F.data == "help")
async def cb_h(cb: CallbackQuery):
    await cb.message.answer("❓ Button dabao aur maza lo. Kuch bhi atke to /cancel ya /help use karo.", reply_markup=main_menu())
    await cb.answer()

@dp.callback_query(F.data == "links")
async def cb_links(cb: CallbackQuery):
    text = (
        "🔗 <b>Useful Links</b>\n"
        "• Telegram: https://telegram.org\n"
        "• BotFather: https://t.me/BotFather\n"
        "• Privacy: apni secret info kabhi public mat karo."
    )
    await cb.message.answer(text, reply_markup=main_menu())
    await cb.answer()

# ---------- GAMES ----------
@dp.callback_query(F.data == "game_dice")
async def cb_dice(cb: CallbackQuery):
    await cb.answer()
    # send dice to chat
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

# ---------- ECHO ----------
@dp.callback_query(F.data == "toggle_echo")
async def cb_toggle_echo(cb: CallbackQuery):
    uid = cb.from_user.id
    ensure_user(uid)
    user_state[uid]["echo"] = not user_state[uid]["echo"]
    status = "ON" if user_state[uid]["echo"] else "OFF"
    await cb.message.answer(f"🔁 Echo mode: <b>{status}</b>\nAb jo text bhejoge, bot usko repeat karega (jab tak OFF na karo).", reply_markup=main_menu())
    await cb.answer()

# ---------- DESIGN MESSAGE ----------
@dp.callback_query(F.data == "design_menu")
async def cb_design_menu(cb: CallbackQuery):
    uid = cb.from_user.id
    ensure_user(uid)
    user_state[uid]["mode"] = None  # reset any pending
    user_state[uid]["design_style"] = None
    await cb.message.answer("🖌 <b>Design Message</b>\nStyle choose karo, phir apna text bhejo:", reply_markup=design_menu_kb())
    await cb.answer()

@dp.callback_query(F.data.in_(["design_bold", "design_italic", "design_mono", "design_fancy"]))
async def cb_design_pick(cb: CallbackQuery):
    uid = cb.from_user.id
    ensure_user(uid)
    mapping = {
        "design_bold": "bold",
        "design_italic": "italic",
        "design_mono": "mono",
        "design_fancy": "fancy",
    }
    # cb.data is the callback_data string (like "design_bold")
    sel = mapping.get(cb.data, "bold")
    user_state[uid]["mode"] = "design"
    user_state[uid]["design_style"] = sel
    pretty = {"bold": "🅱️ Bold", "italic": "𝑰 Italic", "mono": "</> Mono", "fancy": "✨ Fancy"}[sel]
    await cb.message.answer(f"{pretty} selected.\nAb apna text bhejo. (/cancel to stop)")
    await cb.answer()

@dp.callback_query(F.data == "back_to_menu")
async def cb_back_menu(cb: CallbackQuery):
    await cb.message.answer("📋 Back to main menu.", reply_markup=main_menu())
    await cb.answer()

# ---------- IMAGE MAGIC (placeholder without extra libs) ----------
@dp.callback_query(F.data == "image_gen")
async def cb_image(cb: CallbackQuery):
    # Generate a deterministic random image URL (no external libs; Telegram fetches URL)
    seed = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    url = f"https://picsum.photos/seed/{seed}/700/400"
    caption = (
        "🎨 <b>Image Magic</b>\n"
        "Ye demo image-gen style output hai (placeholder). Real AI image ke liye external API chahiye hota, "
        "lekin hum abhi bina extra dependency ke chal rahe hain."
    )
    try:
        await bot.send_photo(cb.message.chat.id, url, caption=caption)
    except Exception:
        await cb.message.answer("⚠️ Image fetch issue. Phir se try karo.")
    await cb.answer()

# ---------- CLOSE ----------
@dp.callback_query(F.data == "close")
async def cb_close(cb: CallbackQuery):
    try:
        await cb.message.delete()
    except Exception:
        await cb.message.answer("Window closed.", reply_markup=None)
    await cb.answer()

# =========================
# MESSAGE HANDLER (MODES)
# =========================
@dp.message(F.text)
async def all_text(message: Message):
    uid = message.from_user.id
    ensure_user(uid)

    # 1) Guess game mode
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

    # 2) Design mode
    if user_state[uid]["mode"] == "design":
        style = user_state[uid]["design_style"] or "bold"
        text = message.text
        if style == "bold":
            out = f"<b>{text}</b>"
        elif style == "italic":
            out = f"<i>{text}</i>"
        elif style == "mono":
            out = f"<code>{text}</code>"
        else:  # fancy
            out = to_fullwidth(text)
        user_state[uid]["mode"] = None
        user_state[uid]["design_style"] = None
        await message.answer(out, reply_markup=main_menu())
        return

    # 3) Echo mode (if ON)
    if user_state[uid]["echo"]:
        await message.answer(message.text)
        return

    # Default fallback
    await message.answer("🙂 Command ya button use karo. /menu se options khol lo.", reply_markup=main_menu())

# =========================
# SET BOT COMMANDS (nice UX)
# =========================
async def set_commands():
    cmds = [
        BotCommand(command="start", description="Open menu"),
        BotCommand(command="help", description="How to use"),
        BotCommand(command="menu", description="Show main menu"),
        BotCommand(command="cancel", description="Cancel current mode"),
    ]
    try:
        await bot.set_my_commands(cmds)
    except Exception:
        # ignore if fails (e.g. network)
        pass

# =========================
# RUN APP
# =========================
async def main():
    await set_commands()
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Flask in separate thread (Render health)
    port = int(os.environ.get("PORT", "10000"))
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=port), daemon=True).start()

    # Run bot (aiogram v3; use asyncio)
    asyncio.run(main())

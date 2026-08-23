#!/usr/bin/env python3
"""
Premium Telegram Group management Bot
Full-featured group management with all commands.
Requirements: pip install python-telegram-bot==20.7
"""

import logging
import json
import os
import asyncio
from datetime import datetime, timedelta
import random
import platform
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo
from collections import defaultdict
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ChatMemberHandler,
    CallbackQueryHandler, filters, ContextTypes
)
from telegram.constants import ParseMode, ChatMemberStatus

# ─── Configuration ───────────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "USER_ID"))  # Your Telegram user ID

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── In-Memory Storage (replace with DB for production) ─────────────────────
warnings_db: dict[int, dict[int, int]] = defaultdict(lambda: defaultdict(int))
MAX_WARNINGS = 3
welcome_messages: dict[int, str] = {}
goodbye_messages: dict[int, str] = {}
antiflood_settings: dict[int, dict] = {}
flood_tracker: dict[int, dict[int, list]] = defaultdict(lambda: defaultdict(list))
banned_words: dict[int, list[str]] = defaultdict(list)
anti_link: dict[int, bool] = defaultdict(bool)
locked_permissions: dict[int, dict] = {}
notes_db: dict[int, dict[str, str]] = defaultdict(dict)
disabled_commands: dict[int, set] = defaultdict(set)
log_channel: dict[int, int] = {}
active_groups: set[int] = set()  # Track all groups bot is in


# ═══════════════════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def mention(user) -> str:
    """Create a clickable mention for the user."""
    return f'<a href="tg://user?id={user.id}">{user.first_name}</a>'


def small(text: str) -> str:
    """Convert text to small caps Unicode."""
    normal = "abcdefghijklmnopqrstuvwxyz"
    smcaps = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"
    table = str.maketrans(normal, smcaps)
    return text.lower().translate(table)



def box(title: str, body: str, heart1="💖", heart2="💗") -> str:
    """Create a beautiful box-style response."""
    top =    f"╔═══════════════════════╗"
    bottom = f"╚═══════════════════════╝"
    return (
        f"<code>{top}</code>\n"
        f"  {heart1} <b>{title}</b> {heart2}\n"
        f"<code>╠═══════════════════════╣</code>\n"
        f"{body}\n"
        f"<code>{bottom}</code>"
    )

# Bot start time for uptime tracking
BOT_START_TIME = datetime.now()

# Funny responses lists
ROASTS = [
    "ᴛᴜ ɪᴛɴᴀ ꜱʟᴏᴡ ʜᴀɪ, ᴛᴇʀᴀ ɪɴᴛᴇʀɴᴇᴛ ʙʜɪ ᴛᴜᴊʜꜱᴇ ᴛᴇᴢ ʜᴀɪ",
    "ᴛᴜ ɢᴏᴏɢʟᴇ ᴘᴇ ꜱᴇᴀʀᴄʜ ᴋᴀʀ 'ᴍᴀɪɴ ᴋʏᴜ ᴀɪꜱᴀ ʜᴜ'",
    "ᴛᴇʀᴇ ᴊᴏᴋᴇꜱ ꜱᴜɴ ᴋᴇ ᴡɪꜰɪ ʙʜɪ ᴅɪꜱᴄᴏɴɴᴇᴄᴛ ʜᴏ ᴊᴀᴛᴀ ʜᴀɪ",
    "ᴛᴜ ᴡᴏ ʙᴀɴᴅᴀ ʜᴀɪ ᴊᴏ ʟɪꜰᴛ ᴍᴇɪɴ ʙʜɪ ᴀᴋᴇʟᴀ ᴊᴀᴛᴀ ʜᴀɪ",
    "ᴛᴇʀɪ ᴅᴘ ᴅᴇᴋʜ ᴋᴇ ꜰᴏɴᴇ ᴋɪ ʙᴀᴛᴛᴇʀʏ ɢɪʀ ᴊᴀᴛɪ ʜᴀɪ",
    "ᴛᴜ ɪᴛɴᴀ ʙᴏʀɪɴɢ ʜᴀɪ, ᴛᴇʀᴀ ᴀʟᴀʀᴍ ʙʜɪ ɴᴀʜɪ ʙᴀᴊᴛᴀ",
    "ᴛᴇʀᴇ ꜱᴀᴀᴛʜ ɢʀᴏᴜᴘ ᴍᴇɪɴ ꜱᴀɴɴᴀᴛᴀ ᴄʜʜᴀ ᴊᴀᴛᴀ ʜᴀɪ",
]

LOVE_QUOTES = [
    "ᴘʏᴀᴀʀ ᴡᴏ ᴄʜᴇᴇᴢ ʜᴀɪ ᴊᴏ ᴡɪꜰɪ ꜱᴇ ʙʜɪ ᴢʏᴀᴅᴀ ᴢᴀʀᴜʀɪ ʜᴀɪ",
    "ᴛᴜᴍ ᴍᴇʀᴇ ʟɪʏᴇ ᴡᴏ ʜᴏ ᴊᴏ ᴄʜᴀʀɢᴇʀ ᴘʜᴏɴᴇ ᴋᴇ ʟɪʏᴇ ʜᴀɪ",
    "ᴅɪʟ ᴛᴏᴅɴᴀ ᴍᴀᴛ, ᴍᴇʀᴇ ᴘᴀᴀꜱ ᴡᴀʀʀᴀɴᴛʏ ɴᴀʜɪ ʜᴀɪ",
    "ᴛᴜᴍꜱᴇ ᴍɪʟᴋᴀʀ ᴅɪʟ ᴋᴀ ꜱᴛᴏʀᴀɢᴇ ꜰᴜʟʟ ʜᴏ ɢᴀʏᴀ",
    "ᴍᴏʜᴀʙʙᴀᴛ ᴍᴇɪɴ ᴀᴄᴄʜᴀ ᴡᴏ ᴊᴏ ʀᴇᴀᴅ ᴋᴀʀᴋᴇ ʀᴇᴘʟʏ ᴋᴀʀᴇ",
]

TRUTH_QUESTIONS = [
    "ᴛᴜɴᴇ ᴀᴀᴊ ᴛᴀᴋ ᴋɪꜱꜱᴇ ꜱᴀʙꜱᴇ ʙᴀᴅᴀ ᴊʜᴏᴏᴛ ʙᴏʟᴀ?",
    "ᴛᴇʀᴀ ꜱᴀʙꜱᴇ ᴇᴍʙᴀʀᴀꜱꜱɪɴɢ ᴍᴏᴍᴇɴᴛ ᴋʏᴀ ᴛʜᴀ?",
    "ᴛᴜ ᴋɪꜱᴋᴏ ꜱᴇᴄʀᴇᴛʟʏ ꜱᴛᴀʟᴋ ᴋᴀʀᴛᴀ ʜᴀɪ?",
    "ᴛᴇʀᴀ ᴘʜᴏɴᴇ ᴄʜᴇᴄᴋ ᴋᴀʀᴇɪɴ ᴛᴏʜ ᴋʏᴀ ᴍɪʟᴇɢᴀ?",
    "ᴛᴜɴᴇ ᴋᴀʙʜɪ ᴄʟᴀꜱꜱ ʙᴜɴᴋ ᴋᴀʀᴋᴇ ᴋʏᴀ ᴋɪʏᴀ?",
]

DARE_CHALLENGES = [
    "ᴀᴘɴɪ ʟᴀꜱᴛ ꜱᴇʟꜰɪᴇ ɢʀᴏᴜᴘ ᴍᴇɪɴ ʙʜᴇᴊᴏ",
    "ᴀɢʟᴇ 5 ᴍɪɴᴜᴛᴇ ꜱɪʀꜰ ᴇᴍᴏᴊɪ ᴍᴇɪɴ ʙᴀᴀᴛ ᴋᴀʀᴏ",
    "ᴀᴘɴᴇ ᴄʀᴜꜱʜ ᴋᴀ ꜰɪʀꜱᴛ ɴᴀᴍᴇ ʙᴀᴛᴀᴏ",
    "10 ᴘᴜꜱʜᴜᴘꜱ ᴋᴀʀᴏ ᴀᴜʀ ᴠɪᴅᴇᴏ ʙʜᴇᴊᴏ",
    "ᴀᴘɴᴀ ꜱᴄʀᴇᴇɴ ᴛɪᴍᴇ ꜱᴄʀᴇᴇɴꜱʜᴏᴛ ʙʜᴇᴊᴏ",
]

FLIRT_LINES = [
    "ᴛᴜᴍ ʜᴏ ᴛᴏʜ ᴅᴜɴɪʏᴀ ʜᴀꜱɪɴ ʜᴀɪ, ᴠᴀʀɴᴀ ᴋʏᴀ ʜᴀɪ",
    "ᴛᴇʀɪ ᴀᴀɴᴋʜᴏɴ ᴍᴇɪɴ ᴡɪꜰɪ ᴋᴀ ᴘᴀꜱꜱᴡᴏʀᴅ ᴍɪʟ ɢᴀʏᴀ",
    "ᴛᴜ ᴘᴀꜱꜱᴡᴏʀᴅ ᴍᴀᴛ ʙᴀᴅʟ, ᴍᴀɪɴ ᴛᴇʀᴇ ᴅɪʟ ᴍᴇɪɴ ᴀᴀ ᴄʜᴜᴋᴀ",
    "ɢᴏᴏɢʟᴇ ᴘᴇ ꜱᴇᴀʀᴄʜ ᴋɪʏᴀ 'ᴘᴇʀꜰᴇᴄᴛ', ᴛᴇʀᴀ ɴᴀᴍᴇ ᴀᴀʏᴀ",
    "ᴛᴇʀᴇ ʙɪɴᴀ ᴢɪɴᴅᴀɢɪ ʟᴏᴡ ʙᴀᴛᴛᴇʀʏ ᴊᴀɪꜱɪ ʜᴀɪ",
]


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int = None) -> bool:
    """Check if a user is an admin in the chat."""
    uid = user_id or update.effective_user.id
    member = await context.bot.get_chat_member(update.effective_chat.id, uid)
    return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)


async def get_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get target user from reply or args."""
    if update.message.reply_to_message:
        return update.message.reply_to_message.from_user
    if context.args:
        try:
            user_id = int(context.args[0])
            member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
            return member.user
        except (ValueError, Exception):
            pass
    return None


async def log_action(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str):
    """Send action log to the configured log channel."""
    if chat_id in log_channel:
        try:
            await context.bot.send_message(log_channel[chat_id], text, parse_mode=ParseMode.HTML)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════════════
#  COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

# ─── Start & Help ────────────────────────────────────────────────────────────

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command with inline buttons."""
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("❤️ ᴄᴏᴍᴍᴀɴᴅꜱ", callback_data="help_menu"),
         InlineKeyboardButton("🩷 ᴀᴅᴅ ᴛᴏ ɢʀᴏᴜᴘ", url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("🧡 ᴏᴡɴᴇʀ", url="https://t.me/InfinityMovieWorld")]
    ]
    await update.message.reply_text(
        f"💛 <b>ᴘʀᴇᴍɪᴜᴍ ɢʀᴏᴜᴘ ᴍᴀɴᴀɢᴇʀ ʙᴏᴛ</b>\n\n"
        f"ʜᴇʏ {mention(user)} 💚\n"
        f"<i>\"ᴍᴀɪɴ ʜᴏᴏɴ ᴛᴇʀᴀ ᴘᴏᴡᴇʀꜰᴜʟ ɢʀᴏᴜᴘ ᴍᴀɴᴀɢᴇʀ\"</i>\n"
        f"ᴍᴜᴊʜᴇ ɢʀᴏᴜᴘ ᴍᴇɪɴ ᴀᴅᴅ ᴋᴀʀᴏ ᴀᴜʀ ᴀᴅᴍɪɴ ʙᴀɴᴀᴏ 💙\n\n"
        f"<b>💜 ꜰᴇᴀᴛᴜʀᴇꜱ:</b>\n"
        f"  🤍 ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅꜱ (ʙᴀɴ, ᴍᴜᴛᴇ, ᴋɪᴄᴋ, ᴡᴀʀɴ)\n"
        f"  🖤 ᴡᴇʟᴄᴏᴍᴇ & ɢᴏᴏᴅʙʏᴇ ᴍᴇꜱꜱᴀɢᴇꜱ\n"
        f"  🩵 ᴀɴᴛɪ-ꜱᴘᴀᴍ & ᴀɴᴛɪ-ꜰʟᴏᴏᴅ\n"
        f"  💖 ᴀɴᴛɪ-ʟɪɴᴋ ᴘʀᴏᴛᴇᴄᴛɪᴏɴ\n"
        f"  💗 ɴᴏᴛᴇꜱ ꜱʏꜱᴛᴇᴍ\n"
        f"  💕 ʟᴏᴄᴋ/ᴜɴʟᴏᴄᴋ ᴘᴇʀᴍɪꜱꜱɪᴏɴꜱ\n"
        f"  💝 ɢʀᴏᴜᴘ ꜱᴛᴀᴛꜱ\n\n"
        f"<i>\"ᴜꜱᴇ /help ꜰᴏʀ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅꜱ\"</i> 💘\n\n"
        f"💞 <b>ᴏᴡɴᴇʀ:</b> @INFINITYxPRIME",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help menu with categories."""
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("💓 ᴀᴅᴍɪɴ", callback_data="help_admin"),
         InlineKeyboardButton("❣️ ᴡᴇʟᴄᴏᴍᴇ", callback_data="help_welcome")],
        [InlineKeyboardButton("❤️ ᴀɴᴛɪ-ꜱᴘᴀᴍ", callback_data="help_antispam"),
         InlineKeyboardButton("🩷 ɴᴏᴛᴇꜱ", callback_data="help_notes")],
        [InlineKeyboardButton("🧡 ʟᴏᴄᴋꜱ", callback_data="help_locks"),
         InlineKeyboardButton("💛 ꜱᴇᴛᴛɪɴɢꜱ", callback_data="help_settings")],
    ]
    await update.message.reply_text(
        f"💚 <b>ʜᴇʟᴘ ᴍᴇɴᴜ</b>\n\n"
        f"ʜᴇʏ {mention(user)} 💙\n"
        f"<i>\"ɴᴇᴇᴄʜᴇ ꜱᴇ ᴄᴀᴛᴇɢᴏʀʏ ᴄʜᴜɴᴏ\"</i>\n\n"
        f"💜 ʙᴏᴛ ᴏᴡɴᴇʀ: ",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


HELP_TEXTS = {
    "help_admin": (
        "🤍 <b>ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅꜱ</b>\n\n"
        "/ban ─ 🖤 ᴜꜱᴇʀ ᴋᴏ ʙᴀɴ ᴋᴀʀᴏ\n"
        "/unban ─ 🩵 ᴜꜱᴇʀ ᴋᴏ ᴜɴʙᴀɴ ᴋᴀʀᴏ\n"
        "/mute ─ 💖 ᴜꜱᴇʀ ᴋᴏ ᴍᴜᴛᴇ ᴋᴀʀᴏ\n"
        "/unmute ─ 💗 ᴜꜱᴇʀ ᴋᴏ ᴜɴᴍᴜᴛᴇ ᴋᴀʀᴏ\n"
        "/tmute [time] ─ 💕 ᴛᴇᴍᴘ ᴍᴜᴛᴇ\n"
        "/tban [time] ─ 💝 ᴛᴇᴍᴘ ʙᴀɴ\n"
        "/kick ─ 💘 ᴜꜱᴇʀ ᴋᴏ ᴋɪᴄᴋ ᴋᴀʀᴏ\n"
        "/warn ─ 💞 ᴜꜱᴇʀ ᴋᴏ ᴡᴀʀɴ ᴋᴀʀᴏ\n"
        "/unwarn ─ 💓 ᴡᴀʀɴɪɴɢ ʜᴀᴛᴀᴏ\n"
        "/warns ─ ❣️ ᴡᴀʀɴɪɴɢꜱ ᴄʜᴇᴄᴋ ᴋᴀʀᴏ\n"
        "/resetwarns ─ ❤️ ꜱᴀᴀʀɪ ᴡᴀʀɴɪɴɢꜱ ʀᴇꜱᴇᴛ\n"
        "/promote ─ 🩷 ᴀᴅᴍɪɴ ʙᴀɴᴀᴏ\n"
        "/demote ─ 🧡 ᴅᴇᴍᴏᴛᴇ ᴋᴀʀᴏ\n"
        "/pin ─ 💛 ᴍᴇꜱꜱᴀɢᴇ ᴘɪɴ ᴋᴀʀᴏ\n"
        "/unpin ─ 💚 ᴍᴇꜱꜱᴀɢᴇ ᴜɴᴘɪɴ ᴋᴀʀᴏ\n"
        "/unpinall ─ 💙 ꜱᴀʙ ᴜɴᴘɪɴ ᴋᴀʀᴏ\n"
        "/purge ─ 💜 ᴍᴇꜱꜱᴀɢᴇꜱ ᴅᴇʟᴇᴛᴇ ᴋᴀʀᴏ\n"
        "/del ─ 🤍 ʀᴇᴘʟɪᴇᴅ ᴍᴇꜱꜱᴀɢᴇ ᴅᴇʟᴇᴛᴇ ᴋᴀʀᴏ\n"
    ),
    "help_welcome": (
        "🖤 <b>ᴡᴇʟᴄᴏᴍᴇ & ɢᴏᴏᴅʙʏᴇ</b>\n\n"
        "/setwelcome [text] ─ 🩵 ᴡᴇʟᴄᴏᴍᴇ ꜱᴇᴛ ᴋᴀʀᴏ\n"
        "/setgoodbye [text] ─ 💖 ɢᴏᴏᴅʙʏᴇ ꜱᴇᴛ ᴋᴀʀᴏ\n"
        "/resetwelcome ─ 💗 ᴡᴇʟᴄᴏᴍᴇ ʀᴇꜱᴇᴛ\n"
        "/resetgoodbye ─ 💕 ɢᴏᴏᴅʙʏᴇ ʀᴇꜱᴇᴛ\n\n"
        "<b>💝 ᴠᴀʀɪᴀʙʟᴇꜱ:</b>\n"
        "{first} ─ ꜰɪʀꜱᴛ ɴᴀᴍᴇ\n"
        "{last} ─ ʟᴀꜱᴛ ɴᴀᴍᴇ\n"
        "{fullname} ─ ꜰᴜʟʟ ɴᴀᴍᴇ\n"
        "{username} ─ ᴜꜱᴇʀɴᴀᴍᴇ\n"
        "{id} ─ ᴜꜱᴇʀ ɪᴅ\n"
        "{chatname} ─ ɢʀᴏᴜᴘ ɴᴀᴍᴇ\n"
        "{count} ─ ᴍᴇᴍʙᴇʀ ᴄᴏᴜɴᴛ\n"
    ),
    "help_antispam": (
        "💘 <b>ᴀɴᴛɪ-ꜱᴘᴀᴍ & ꜰɪʟᴛᴇʀꜱ</b>\n\n"
        "/antiflood [count] ─ 💞 ꜰʟᴏᴏᴅ ʟɪᴍɪᴛ ꜱᴇᴛ ᴋᴀʀᴏ\n"
        "/antifloodoff ─ 💓 ᴀɴᴛɪ-ꜰʟᴏᴏᴅ ᴏꜰꜰ\n"
        "/antilink on/off ─ ❣️ ᴀɴᴛɪ-ʟɪɴᴋ ᴛᴏɢɢʟᴇ\n"
        "/addword [word] ─ ❤️ ʙᴀɴɴᴇᴅ ᴡᴏʀᴅ ᴀᴅᴅ\n"
        "/rmword [word] ─ 🩷 ʙᴀɴɴᴇᴅ ᴡᴏʀᴅ ʜᴀᴛᴀᴏ\n"
        "/wordlist ─ 🧡 ʙᴀɴɴᴇᴅ ᴡᴏʀᴅꜱ ᴅᴇᴋʜᴏ\n"
    ),
    "help_notes": (
        "💛 <b>ɴᴏᴛᴇꜱ ꜱʏꜱᴛᴇᴍ</b>\n\n"
        "/save [name] [text] ─ 💚 ɴᴏᴛᴇ ꜱᴀᴠᴇ ᴋᴀʀᴏ\n"
        "/get [name] ─ 💙 ɴᴏᴛᴇ ᴅᴇᴋʜᴏ\n"
        "#notename ─ 💜 ɴᴏᴛᴇ ᴅᴇᴋʜᴏ\n"
        "/notes ─ 🤍 ꜱᴀᴀʀᴇ ɴᴏᴛᴇꜱ\n"
        "/clear [name] ─ 🖤 ɴᴏᴛᴇ ᴅᴇʟᴇᴛᴇ ᴋᴀʀᴏ\n"
        "/clearall ─ 🩵 ꜱᴀᴀʀᴇ ɴᴏᴛᴇꜱ ᴅᴇʟᴇᴛᴇ\n"
    ),
    "help_locks": (
        "💖 <b>ʟᴏᴄᴋ / ᴜɴʟᴏᴄᴋ</b>\n\n"
        "/lock [type] ─ 💗 ᴘᴇʀᴍɪꜱꜱɪᴏɴ ʟᴏᴄᴋ ᴋᴀʀᴏ\n"
        "/unlock [type] ─ 💕 ᴘᴇʀᴍɪꜱꜱɪᴏɴ ᴜɴʟᴏᴄᴋ\n"
        "/locks ─ 💝 ᴄᴜʀʀᴇɴᴛ ʟᴏᴄᴋꜱ ᴅᴇᴋʜᴏ\n\n"
        "<b>💘 ᴛʏᴘᴇꜱ:</b> messages, media, stickers, gifs, "
        "games, inline, url, polls, info, invite\n"
    ),
    "help_settings": (
        "💞 <b>ꜱᴇᴛᴛɪɴɢꜱ</b>\n\n"
        "/setlog [channel_id] ─ 💓 ʟᴏɢ ᴄʜᴀɴɴᴇʟ ꜱᴇᴛ\n"
        "/unsetlog ─ ❣️ ʟᴏɢ ᴄʜᴀɴɴᴇʟ ʜᴀᴛᴀᴏ\n"
        "/settings ─ ❤️ ꜱᴇᴛᴛɪɴɢꜱ ᴅᴇᴋʜᴏ\n"
        "/id ─ 🩷 ᴄʜᴀᴛ/ᴜꜱᴇʀ ɪᴅ\n"
        "/info ─ 🧡 ᴜꜱᴇʀ ɪɴꜰᴏ\n"
        "/admins ─ 💛 ᴀᴅᴍɪɴꜱ ʟɪꜱᴛ\n"
        "/rules ─ 💚 ɢʀᴏᴜᴘ ʀᴜʟᴇꜱ\n"
        "/setrules [text] ─ 💙 ʀᴜʟᴇꜱ ꜱᴇᴛ ᴋᴀʀᴏ\n"
    ),
}


async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle help menu button clicks."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "help_menu":
        keyboard = [
            [InlineKeyboardButton("💜 ᴀᴅᴍɪɴ", callback_data="help_admin"),
             InlineKeyboardButton("🤍 ᴡᴇʟᴄᴏᴍᴇ", callback_data="help_welcome")],
            [InlineKeyboardButton("🖤 ᴀɴᴛɪ-ꜱᴘᴀᴍ", callback_data="help_antispam"),
             InlineKeyboardButton("🩵 ɴᴏᴛᴇꜱ", callback_data="help_notes")],
            [InlineKeyboardButton("💖 ʟᴏᴄᴋꜱ", callback_data="help_locks"),
             InlineKeyboardButton("💗 ꜱᴇᴛᴛɪɴɢꜱ", callback_data="help_settings")],
        ]
        await query.edit_message_text(
            f"💕 <b>ʜᴇʟᴘ ᴍᴇɴᴜ</b>\n\n"
            f"<i>\"ɴᴇᴇᴄʜᴇ ꜱᴇ ᴄᴀᴛᴇɢᴏʀʏ ᴄʜᴜɴᴏ\"</i> 💝\n\n"
            f"💘 ʙᴏᴛ ᴏᴡɴᴇʀ: @INFINITYxPRIME",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif data in HELP_TEXTS:
        keyboard = [[InlineKeyboardButton("💞 ʙᴀᴄᴋ", callback_data="help_menu")]]
        await query.edit_message_text(
            HELP_TEXTS[data],
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# ─── Admin Commands ─────────────────────────────────────────────────────────

async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"💓 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    target = await get_target_user(update, context)
    if not target:
        return await update.message.reply_text(f"❣️ {mention(update.effective_user)}\n<i>\"ʀᴇᴘʟʏ ᴋᴀʀᴏ ʏᴀ ᴜꜱᴇʀ ɪᴅ ᴅᴏ\"</i>", parse_mode=ParseMode.HTML)
    if await is_admin(update, context, target.id):
        return await update.message.reply_text(f"❤️ {mention(update.effective_user)}\n<i>\"ᴀᴅᴍɪɴ ᴋᴏ ʙᴀɴ ɴᴀʜɪ ᴋᴀʀ ꜱᴀᴋᴛᴇ\"</i>", parse_mode=ParseMode.HTML)
    reason = " ".join(context.args[1:]) if context.args and len(context.args) > 1 else "No reason"
    await context.bot.ban_chat_member(update.effective_chat.id, target.id)
    await update.message.reply_text(
        f"🩷 {mention(target)} ᴋᴏ ʙᴀɴ ᴋᴀʀ ᴅɪʏᴀ 🧡\n"
        f"<i>\"ʀᴇᴀꜱᴏɴ: {reason}\"</i>\n"
        f"💛 ʙʏ: {mention(update.effective_user)}",
        parse_mode=ParseMode.HTML
    )
    await log_action(context, update.effective_chat.id,
                     f"💚 #BAN\nUser: {target.full_name} ({target.id})\nBy: {update.effective_user.full_name}\nReason: {reason}")


async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"💙 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    target = await get_target_user(update, context)
    if not target:
        return await update.message.reply_text(f"💜 {mention(update.effective_user)}\n<i>\"ʀᴇᴘʟʏ ᴋᴀʀᴏ ʏᴀ ᴜꜱᴇʀ ɪᴅ ᴅᴏ\"</i>", parse_mode=ParseMode.HTML)
    await context.bot.unban_chat_member(update.effective_chat.id, target.id, only_if_banned=True)
    await update.message.reply_text(
        f"🤍 {mention(target)} ᴋᴏ ᴜɴʙᴀɴ ᴋᴀʀ ᴅɪʏᴀ 🖤\n"
        f"🩵 ʙʏ: {mention(update.effective_user)}",
        parse_mode=ParseMode.HTML
    )


async def kick_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"💖 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    target = await get_target_user(update, context)
    if not target:
        return await update.message.reply_text(f"💗 {mention(update.effective_user)}\n<i>\"ʀᴇᴘʟʏ ᴋᴀʀᴏ ʏᴀ ᴜꜱᴇʀ ɪᴅ ᴅᴏ\"</i>", parse_mode=ParseMode.HTML)
    if await is_admin(update, context, target.id):
        return await update.message.reply_text(f"💕 {mention(update.effective_user)}\n<i>\"ᴀᴅᴍɪɴ ᴋᴏ ᴋɪᴄᴋ ɴᴀʜɪ ᴋᴀʀ ꜱᴀᴋᴛᴇ\"</i>", parse_mode=ParseMode.HTML)
    await context.bot.ban_chat_member(update.effective_chat.id, target.id)
    await context.bot.unban_chat_member(update.effective_chat.id, target.id)
    await update.message.reply_text(
        f"💝 {mention(target)} ᴋᴏ ᴋɪᴄᴋ ᴋᴀʀ ᴅɪʏᴀ 💘\n"
        f"💞 ʙʏ: {mention(update.effective_user)}",
        parse_mode=ParseMode.HTML
    )


async def mute_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"💓 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    target = await get_target_user(update, context)
    if not target:
        return await update.message.reply_text(f"❣️ {mention(update.effective_user)}\n<i>\"ʀᴇᴘʟʏ ᴋᴀʀᴏ ʏᴀ ᴜꜱᴇʀ ɪᴅ ᴅᴏ\"</i>", parse_mode=ParseMode.HTML)
    if await is_admin(update, context, target.id):
        return await update.message.reply_text(f"❤️ {mention(update.effective_user)}\n<i>\"ᴀᴅᴍɪɴ ᴋᴏ ᴍᴜᴛᴇ ɴᴀʜɪ ᴋᴀʀ ꜱᴀᴋᴛᴇ\"</i>", parse_mode=ParseMode.HTML)
    await context.bot.restrict_chat_member(
        update.effective_chat.id, target.id,
        permissions=ChatPermissions(can_send_messages=False)
    )
    await update.message.reply_text(
        f"🩷 {mention(target)} ᴋᴏ ᴍᴜᴛᴇ ᴋᴀʀ ᴅɪʏᴀ 🧡\n"
        f"💛 ʙʏ: {mention(update.effective_user)}",
        parse_mode=ParseMode.HTML
    )


async def unmute_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"💚 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    target = await get_target_user(update, context)
    if not target:
        return await update.message.reply_text(f"💙 {mention(update.effective_user)}\n<i>\"ʀᴇᴘʟʏ ᴋᴀʀᴏ ʏᴀ ᴜꜱᴇʀ ɪᴅ ᴅᴏ\"</i>", parse_mode=ParseMode.HTML)
    await context.bot.restrict_chat_member(
        update.effective_chat.id, target.id,
        permissions=ChatPermissions(
            can_send_messages=True, can_send_media_messages=True,
            can_send_polls=True, can_send_other_messages=True,
            can_add_web_page_previews=True, can_invite_users=True
        )
    )
    await update.message.reply_text(
        f"💜 {mention(target)} ᴋᴏ ᴜɴᴍᴜᴛᴇ ᴋᴀʀ ᴅɪʏᴀ 🤍\n"
        f"🖤 ʙʏ: {mention(update.effective_user)}",
        parse_mode=ParseMode.HTML
    )


def parse_time(time_str: str) -> timedelta | None:
    """Parse time string like 1h, 30m, 1d."""
    units = {"m": "minutes", "h": "hours", "d": "days", "w": "weeks"}
    if not time_str or len(time_str) < 2:
        return None
    unit = time_str[-1].lower()
    if unit not in units:
        return None
    try:
        amount = int(time_str[:-1])
        return timedelta(**{units[unit]: amount})
    except ValueError:
        return None


async def tmute_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"🩵 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    target = await get_target_user(update, context)
    if not target or not context.args:
        return await update.message.reply_text(f"💖 {mention(update.effective_user)}\n<i>\"ᴜꜱᴀɢᴇ: /tmute [time] (ʀᴇᴘʟʏ ᴛᴏ ᴜꜱᴇʀ)\"</i>\n<i>\"ᴇxᴀᴍᴘʟᴇ: /tmute 1h\"</i>", parse_mode=ParseMode.HTML)
    time_arg = context.args[0]
    duration = parse_time(time_arg)
    if not duration:
        return await update.message.reply_text(f"💗 {mention(update.effective_user)}\n<i>\"ɪɴᴠᴀʟɪᴅ ᴛɪᴍᴇ! ᴜꜱᴇ: 30ᴍ, 1ʜ, 1ᴅ, 1ᴡ\"</i>", parse_mode=ParseMode.HTML)
    until = datetime.now() + duration
    await context.bot.restrict_chat_member(
        update.effective_chat.id, target.id,
        permissions=ChatPermissions(can_send_messages=False),
        until_date=until
    )
    await update.message.reply_text(
        f"💕 {mention(target)} ᴋᴏ {time_arg} ᴋᴇ ʟɪʏᴇ ᴍᴜᴛᴇ ᴋᴀʀ ᴅɪʏᴀ 💝\n"
        f"💘 ʙʏ: {mention(update.effective_user)}",
        parse_mode=ParseMode.HTML
    )


async def tban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"💞 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    target = await get_target_user(update, context)
    if not target or not context.args:
        return await update.message.reply_text(f"💓 {mention(update.effective_user)}\n<i>\"ᴜꜱᴀɢᴇ: /tban [time] (ʀᴇᴘʟʏ ᴛᴏ ᴜꜱᴇʀ)\"</i>\n<i>\"ᴇxᴀᴍᴘʟᴇ: /tban 1d\"</i>", parse_mode=ParseMode.HTML)
    duration = parse_time(context.args[0])
    if not duration:
        return await update.message.reply_text(f"❣️ {mention(update.effective_user)}\n<i>\"ɪɴᴠᴀʟɪᴅ ᴛɪᴍᴇ! ᴜꜱᴇ: 30ᴍ, 1ʜ, 1ᴅ, 1ᴡ\"</i>", parse_mode=ParseMode.HTML)
    until = datetime.now() + duration
    await context.bot.ban_chat_member(update.effective_chat.id, target.id, until_date=until)
    await update.message.reply_text(
        f"❤️ {mention(target)} ᴋᴏ {context.args[0]} ᴋᴇ ʟɪʏᴇ ʙᴀɴ ᴋᴀʀ ᴅɪʏᴀ 🩷\n"
        f"🧡 ʙʏ: {mention(update.effective_user)}",
        parse_mode=ParseMode.HTML
    )


# ─── Warn System ─────────────────────────────────────────────────────────────

async def warn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"💛 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    target = await get_target_user(update, context)
    if not target:
        return await update.message.reply_text(f"💚 {mention(update.effective_user)}\n<i>\"ʀᴇᴘʟʏ ᴋᴀʀᴏ ʏᴀ ᴜꜱᴇʀ ɪᴅ ᴅᴏ\"</i>", parse_mode=ParseMode.HTML)
    if await is_admin(update, context, target.id):
        return await update.message.reply_text(f"💙 {mention(update.effective_user)}\n<i>\"ᴀᴅᴍɪɴ ᴋᴏ ᴡᴀʀɴ ɴᴀʜɪ ᴋᴀʀ ꜱᴀᴋᴛᴇ\"</i>", parse_mode=ParseMode.HTML)
    chat_id = update.effective_chat.id
    reason = " ".join(context.args[1:]) if context.args and len(context.args) > 1 else "No reason"
    warnings_db[chat_id][target.id] += 1
    count = warnings_db[chat_id][target.id]
    if count >= MAX_WARNINGS:
        await context.bot.ban_chat_member(chat_id, target.id)
        warnings_db[chat_id][target.id] = 0
        await update.message.reply_text(
            f"💜 {mention(target)} ᴋᴏ {MAX_WARNINGS} ᴡᴀʀɴɪɴɢꜱ ᴍɪʟɴᴇ ᴘᴀʀ ʙᴀɴ ᴋᴀʀ ᴅɪʏᴀ 🤍\n"
            f"🖤 ʙʏ: {mention(update.effective_user)}",
            parse_mode=ParseMode.HTML
        )
    else:
        await update.message.reply_text(
            f"🩵 {mention(target)} ᴋᴏ ᴡᴀʀɴ ᴋɪʏᴀ ({count}/{MAX_WARNINGS}) 💖\n"
            f"<i>\"ʀᴇᴀꜱᴏɴ: {reason}\"</i>\n"
            f"💗 ʙʏ: {mention(update.effective_user)}",
            parse_mode=ParseMode.HTML
        )


async def unwarn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"💕 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    target = await get_target_user(update, context)
    if not target:
        return await update.message.reply_text(f"💝 {mention(update.effective_user)}\n<i>\"ʀᴇᴘʟʏ ᴋᴀʀᴏ ʏᴀ ᴜꜱᴇʀ ɪᴅ ᴅᴏ\"</i>", parse_mode=ParseMode.HTML)
    chat_id = update.effective_chat.id
    if warnings_db[chat_id][target.id] > 0:
        warnings_db[chat_id][target.id] -= 1
    await update.message.reply_text(
        f"💘 {mention(target)} ᴋɪ ᴇᴋ ᴡᴀʀɴɪɴɢ ʜᴀᴛᴀ ᴅɪ ({warnings_db[chat_id][target.id]}/{MAX_WARNINGS}) 💞\n"
        f"💓 ʙʏ: {mention(update.effective_user)}",
        parse_mode=ParseMode.HTML
    )


async def warns_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await get_target_user(update, context)
    if not target:
        target = update.effective_user
    count = warnings_db[update.effective_chat.id][target.id]
    await update.message.reply_text(
        f"❣️ {mention(target)} ᴋɪ ᴡᴀʀɴɪɴɢꜱ: {count}/{MAX_WARNINGS} ❤️",
        parse_mode=ParseMode.HTML
    )


async def resetwarns_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"🩷 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    target = await get_target_user(update, context)
    if not target:
        return await update.message.reply_text(f"🧡 {mention(update.effective_user)}\n<i>\"ʀᴇᴘʟʏ ᴋᴀʀᴏ ʏᴀ ᴜꜱᴇʀ ɪᴅ ᴅᴏ\"</i>", parse_mode=ParseMode.HTML)
    warnings_db[update.effective_chat.id][target.id] = 0
    await update.message.reply_text(
        f"💛 {mention(target)} ᴋɪ ꜱᴀᴀʀɪ ᴡᴀʀɴɪɴɢꜱ ʀᴇꜱᴇᴛ 💚\n"
        f"💙 ʙʏ: {mention(update.effective_user)}",
        parse_mode=ParseMode.HTML
    )


# ─── Promote / Demote ────────────────────────────────────────────────────────

async def promote_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"💜 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    target = await get_target_user(update, context)
    if not target:
        return await update.message.reply_text(f"🤍 {mention(update.effective_user)}\n<i>\"ʀᴇᴘʟʏ ᴋᴀʀᴏ ʏᴀ ᴜꜱᴇʀ ɪᴅ ᴅᴏ\"</i>", parse_mode=ParseMode.HTML)
    title = " ".join(context.args[1:]) if context.args and len(context.args) > 1 else "Admin"
    await context.bot.promote_chat_member(
        update.effective_chat.id, target.id,
        can_delete_messages=True, can_restrict_members=True,
        can_invite_users=True, can_pin_messages=True,
        can_manage_video_chats=True
    )
    try:
        await context.bot.set_chat_administrator_custom_title(update.effective_chat.id, target.id, title)
    except Exception:
        pass
    await update.message.reply_text(
        f"🖤 {mention(target)} ᴋᴏ ᴀᴅᴍɪɴ ʙᴀɴᴀ ᴅɪʏᴀ 🩵\n"
        f"<i>\"ᴛɪᴛʟᴇ: {title}\"</i>\n"
        f"💖 ʙʏ: {mention(update.effective_user)}",
        parse_mode=ParseMode.HTML
    )


async def demote_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"💗 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    target = await get_target_user(update, context)
    if not target:
        return await update.message.reply_text(f"💕 {mention(update.effective_user)}\n<i>\"ʀᴇᴘʟʏ ᴋᴀʀᴏ ʏᴀ ᴜꜱᴇʀ ɪᴅ ᴅᴏ\"</i>", parse_mode=ParseMode.HTML)
    await context.bot.promote_chat_member(
        update.effective_chat.id, target.id,
        can_delete_messages=False, can_restrict_members=False,
        can_invite_users=False, can_pin_messages=False
    )
    await update.message.reply_text(
        f"💝 {mention(target)} ᴋᴏ ᴅᴇᴍᴏᴛᴇ ᴋᴀʀ ᴅɪʏᴀ 💘\n"
        f"💞 ʙʏ: {mention(update.effective_user)}",
        parse_mode=ParseMode.HTML
    )


# ─── Pin / Purge / Del ───────────────────────────────────────────────────────

async def pin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"💓 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    if not update.message.reply_to_message:
        return await update.message.reply_text(f"❣️ {mention(update.effective_user)}\n<i>\"ᴋɪꜱɪ ᴍᴇꜱꜱᴀɢᴇ ᴘᴇ ʀᴇᴘʟʏ ᴋᴀʀᴏ\"</i>", parse_mode=ParseMode.HTML)
    silent = "loud" not in (context.args or [])
    await update.message.reply_to_message.pin(disable_notification=silent)
    await update.message.reply_text(f"❤️ {mention(update.effective_user)}\n<i>\"ᴍᴇꜱꜱᴀɢᴇ ᴘɪɴ ᴋᴀʀ ᴅɪʏᴀ\"</i> 🩷", parse_mode=ParseMode.HTML)


async def unpin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"🧡 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    if update.message.reply_to_message:
        await update.message.reply_to_message.unpin()
    else:
        await context.bot.unpin_chat_message(update.effective_chat.id)
    await update.message.reply_text(f"💛 {mention(update.effective_user)}\n<i>\"ᴍᴇꜱꜱᴀɢᴇ ᴜɴᴘɪɴ ᴋᴀʀ ᴅɪʏᴀ\"</i> 💚", parse_mode=ParseMode.HTML)


async def unpinall_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"💙 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    await context.bot.unpin_all_chat_messages(update.effective_chat.id)
    await update.message.reply_text(f"💜 {mention(update.effective_user)}\n<i>\"ꜱᴀᴀʀᴇ ᴍᴇꜱꜱᴀɢᴇꜱ ᴜɴᴘɪɴ ᴋᴀʀ ᴅɪʏᴇ\"</i> 🤍", parse_mode=ParseMode.HTML)


async def purge_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"🖤 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    if not update.message.reply_to_message:
        return await update.message.reply_text(f"🩵 {mention(update.effective_user)}\n<i>\"ᴊɪꜱ ᴍᴇꜱꜱᴀɢᴇ ꜱᴇ ᴅᴇʟᴇᴛᴇ ᴋᴀʀɴᴀ ʜᴀɪ ᴜꜱᴘᴇ ʀᴇᴘʟʏ ᴋᴀʀᴏ\"</i>", parse_mode=ParseMode.HTML)
    start_id = update.message.reply_to_message.message_id
    end_id = update.message.message_id
    deleted = 0
    for msg_id in range(start_id, end_id + 1):
        try:
            await context.bot.delete_message(update.effective_chat.id, msg_id)
            deleted += 1
        except Exception:
            pass
    msg = await update.effective_chat.send_message(
        f"💖 {mention(update.effective_user)}\n<i>\"{deleted} ᴍᴇꜱꜱᴀɢᴇꜱ ᴅᴇʟᴇᴛᴇ ᴋɪʏᴇ\"</i> 💗",
        parse_mode=ParseMode.HTML
    )
    await asyncio.sleep(3)
    try:
        await msg.delete()
    except Exception:
        pass


async def del_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if update.message.reply_to_message:
        try:
            await update.message.reply_to_message.delete()
            await update.message.delete()
        except Exception:
            pass


# ─── Welcome & Goodbye ───────────────────────────────────────────────────────

async def set_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"💕 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    if not context.args:
        return await update.message.reply_text(f"💝 {mention(update.effective_user)}\n<i>\"ᴜꜱᴀɢᴇ: /setwelcome [message]\"</i>", parse_mode=ParseMode.HTML)
    welcome_messages[update.effective_chat.id] = " ".join(context.args)
    await update.message.reply_text(f"💘 {mention(update.effective_user)}\n<i>\"ᴡᴇʟᴄᴏᴍᴇ ᴍᴇꜱꜱᴀɢᴇ ꜱᴇᴛ ᴋᴀʀ ᴅɪʏᴀ\"</i> 💞", parse_mode=ParseMode.HTML)


async def set_goodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"💓 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    if not context.args:
        return await update.message.reply_text(f"❣️ {mention(update.effective_user)}\n<i>\"ᴜꜱᴀɢᴇ: /setgoodbye [message]\"</i>", parse_mode=ParseMode.HTML)
    goodbye_messages[update.effective_chat.id] = " ".join(context.args)
    await update.message.reply_text(f"❤️ {mention(update.effective_user)}\n<i>\"ɢᴏᴏᴅʙʏᴇ ᴍᴇꜱꜱᴀɢᴇ ꜱᴇᴛ ᴋᴀʀ ᴅɪʏᴀ\"</i> 🩷", parse_mode=ParseMode.HTML)


async def reset_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"🧡 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    welcome_messages.pop(update.effective_chat.id, None)
    await update.message.reply_text(f"💛 {mention(update.effective_user)}\n<i>\"ᴡᴇʟᴄᴏᴍᴇ ᴍᴇꜱꜱᴀɢᴇ ʀᴇꜱᴇᴛ ᴋᴀʀ ᴅɪʏᴀ\"</i> 💚", parse_mode=ParseMode.HTML)


async def reset_goodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"💙 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    goodbye_messages.pop(update.effective_chat.id, None)
    await update.message.reply_text(f"💜 {mention(update.effective_user)}\n<i>\"ɢᴏᴏᴅʙʏᴇ ᴍᴇꜱꜱᴀɢᴇ ʀᴇꜱᴇᴛ ᴋᴀʀ ᴅɪʏᴀ\"</i> 🤍", parse_mode=ParseMode.HTML)


def format_welcome(text: str, user, chat) -> str:
    """Format welcome/goodbye message with variables."""
    return text.format(
        first=user.first_name or "",
        last=user.last_name or "",
        fullname=user.full_name or "",
        username=f"@{user.username}" if user.username else user.full_name,
        id=user.id,
        chatname=chat.title or "",
        count="N/A"
    )


async def greet_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new member join."""
    result = update.chat_member
    if update.effective_chat:
        active_groups.add(update.effective_chat.id)
    if result.new_chat_member.status == ChatMemberStatus.MEMBER:
        chat_id = update.effective_chat.id
        user = result.new_chat_member.user
        if chat_id in welcome_messages:
            text = format_welcome(welcome_messages[chat_id], user, update.effective_chat)
        else:
            text = (
                f"🖤 ᴡᴇʟᴄᴏᴍᴇ {mention(user)} 🩵\n"
                f"<i>\"ᴛᴜᴍ <b>{update.effective_chat.title}</b> ᴍᴇɪɴ ᴀᴀ ɢᴀʏᴇ\"</i> 💖"
            )
        await context.bot.send_message(chat_id, text, parse_mode=ParseMode.HTML)
    elif result.new_chat_member.status in (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED):
        chat_id = update.effective_chat.id
        user = result.old_chat_member.user
        if chat_id in goodbye_messages:
            text = format_welcome(goodbye_messages[chat_id], user, update.effective_chat)
        else:
            text = f"💗 {mention(user)} ɢʀᴏᴜᴘ ᴄʜʜᴏᴅ ᴋᴇ ᴄʜᴀʟᴀ ɢᴀʏᴀ 💕"
        await context.bot.send_message(chat_id, text, parse_mode=ParseMode.HTML)


# ─── Anti-Flood ──────────────────────────────────────────────────────────────

async def antiflood_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"💝 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    if not context.args:
        return await update.message.reply_text(f"💘 {mention(update.effective_user)}\n<i>\"ᴜꜱᴀɢᴇ: /antiflood [count]\"</i>", parse_mode=ParseMode.HTML)
    try:
        count = int(context.args[0])
        if count < 3:
            return await update.message.reply_text(f"💞 {mention(update.effective_user)}\n<i>\"ᴍɪɴɪᴍᴜᴍ 3 ʜᴏɴᴀ ᴄʜᴀʜɪʏᴇ\"</i>", parse_mode=ParseMode.HTML)
        antiflood_settings[update.effective_chat.id] = {"max_msgs": count, "time_window": 5}
        await update.message.reply_text(
            f"💓 {mention(update.effective_user)}\n"
            f"<i>\"ᴀɴᴛɪ-ꜰʟᴏᴏᴅ ᴏɴ! {count} ᴍᴇꜱꜱᴀɢᴇꜱ / 5ꜱ ꜱᴇ ᴢʏᴀᴅᴀ ᴘᴇ ᴍᴜᴛᴇ\"</i> ❣️",
            parse_mode=ParseMode.HTML
        )
    except ValueError:
        await update.message.reply_text(f"❤️ {mention(update.effective_user)}\n<i>\"ɴᴜᴍʙᴇʀ ᴅᴏ\"</i>", parse_mode=ParseMode.HTML)


async def antiflood_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"🩷 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    antiflood_settings.pop(update.effective_chat.id, None)
    await update.message.reply_text(f"🧡 {mention(update.effective_user)}\n<i>\"ᴀɴᴛɪ-ꜰʟᴏᴏᴅ ᴏꜰꜰ ᴋᴀʀ ᴅɪʏᴀ\"</i> 💛", parse_mode=ParseMode.HTML)


async def check_flood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check for flooding."""
    if not update.message or not update.effective_chat:
        return
    chat_id = update.effective_chat.id
    if chat_id not in antiflood_settings:
        return
    user_id = update.effective_user.id
    if await is_admin(update, context, user_id):
        return
    settings = antiflood_settings[chat_id]
    now = datetime.now().timestamp()
    flood_tracker[chat_id][user_id].append(now)
    flood_tracker[chat_id][user_id] = [
        t for t in flood_tracker[chat_id][user_id]
        if now - t < settings["time_window"]
    ]
    if len(flood_tracker[chat_id][user_id]) > settings["max_msgs"]:
        await context.bot.restrict_chat_member(
            chat_id, user_id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=datetime.now() + timedelta(hours=1)
        )
        flood_tracker[chat_id][user_id] = []
        await update.message.reply_text(
            f"💚 {mention(update.effective_user)} ᴋᴏ ꜰʟᴏᴏᴅɪɴɢ ᴋᴇ ʟɪʏᴇ 1 ʜᴏᴜʀ ᴍᴜᴛᴇ ᴋᴀʀ ᴅɪʏᴀ 💙",
            parse_mode=ParseMode.HTML
        )


# ─── Anti-Link ───────────────────────────────────────────────────────────────

async def antilink_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"💜 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    if not context.args or context.args[0].lower() not in ("on", "off"):
        return await update.message.reply_text(f"🤍 {mention(update.effective_user)}\n<i>\"ᴜꜱᴀɢᴇ: /antilink on/off\"</i>", parse_mode=ParseMode.HTML)
    anti_link[update.effective_chat.id] = context.args[0].lower() == "on"
    status = "ᴏɴ 🖤" if anti_link[update.effective_chat.id] else "ᴏꜰꜰ 🩵"
    await update.message.reply_text(
        f"💖 {mention(update.effective_user)}\n<i>\"ᴀɴᴛɪ-ʟɪɴᴋ: {status}\"</i>",
        parse_mode=ParseMode.HTML
    )


async def check_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete messages with links from non-admins."""
    if not update.message or not update.effective_chat:
        return
    chat_id = update.effective_chat.id
    if not anti_link.get(chat_id):
        return
    if await is_admin(update, context):
        return
    if update.message.entities:
        for entity in update.message.entities:
            if entity.type in ("url", "text_link"):
                await update.message.delete()
                await update.effective_chat.send_message(
                    f"💗 {mention(update.effective_user)}\n<i>\"ʟɪɴᴋꜱ ʙʜᴇᴊɴᴇ ᴋɪ ᴘᴇʀᴍɪꜱꜱɪᴏɴ ɴᴀʜɪ ʜᴀɪ\"</i> 💕",
                    parse_mode=ParseMode.HTML
                )
                return


# ─── Banned Words ────────────────────────────────────────────────────────────

async def addword_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"💝 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    if not context.args:
        return await update.message.reply_text(f"💘 {mention(update.effective_user)}\n<i>\"ᴜꜱᴀɢᴇ: /addword [word]\"</i>", parse_mode=ParseMode.HTML)
    word = " ".join(context.args).lower()
    banned_words[update.effective_chat.id].append(word)
    await update.message.reply_text(
        f"💞 {mention(update.effective_user)}\n<i>\"'{word}' ʙᴀɴɴᴇᴅ ᴡᴏʀᴅꜱ ᴍᴇɪɴ ᴀᴅᴅ ᴋᴀʀ ᴅɪʏᴀ\"</i> 💓",
        parse_mode=ParseMode.HTML
    )


async def rmword_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"❣️ {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    if not context.args:
        return await update.message.reply_text(f"❤️ {mention(update.effective_user)}\n<i>\"ᴜꜱᴀɢᴇ: /rmword [word]\"</i>", parse_mode=ParseMode.HTML)
    word = " ".join(context.args).lower()
    chat_id = update.effective_chat.id
    if word in banned_words[chat_id]:
        banned_words[chat_id].remove(word)
        await update.message.reply_text(f"🩷 {mention(update.effective_user)}\n<i>\"'{word}' ʜᴀᴛᴀ ᴅɪʏᴀ\"</i> 🧡", parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(f"💛 {mention(update.effective_user)}\n<i>\"'{word}' ʟɪꜱᴛ ᴍᴇɪɴ ɴᴀʜɪ ʜᴀɪ\"</i>", parse_mode=ParseMode.HTML)


async def wordlist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    words = banned_words.get(update.effective_chat.id, [])
    if not words:
        return await update.message.reply_text(f"💚 {mention(update.effective_user)}\n<i>\"ᴋᴏɪ ʙᴀɴɴᴇᴅ ᴡᴏʀᴅ ɴᴀʜɪ ʜᴀɪ\"</i>", parse_mode=ParseMode.HTML)
    await update.message.reply_text(
        f"💙 <b>ʙᴀɴɴᴇᴅ ᴡᴏʀᴅꜱ:</b>\n" + "\n".join(f"  💜 {w}" for w in words),
        parse_mode=ParseMode.HTML
    )


async def check_banned_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete messages containing banned words."""
    if not update.message or not update.message.text or not update.effective_chat:
        return
    chat_id = update.effective_chat.id
    if not banned_words.get(chat_id):
        return
    if await is_admin(update, context):
        return
    text = update.message.text.lower()
    for word in banned_words[chat_id]:
        if word in text:
            await update.message.delete()
            await update.effective_chat.send_message(
                f"🤍 {mention(update.effective_user)}\n<i>\"ʏᴇ ᴡᴏʀᴅ ᴀʟʟᴏᴡᴇᴅ ɴᴀʜɪ ʜᴀɪ\"</i> 🖤",
                parse_mode=ParseMode.HTML
            )
            return


# ─── Notes System ────────────────────────────────────────────────────────────

async def save_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"🩵 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    if len(context.args) < 2:
        return await update.message.reply_text(f"💖 {mention(update.effective_user)}\n<i>\"ᴜꜱᴀɢᴇ: /save [name] [text]\"</i>", parse_mode=ParseMode.HTML)
    name = context.args[0].lower()
    text = " ".join(context.args[1:])
    notes_db[update.effective_chat.id][name] = text
    await update.message.reply_text(f"💗 {mention(update.effective_user)}\n<i>\"ɴᴏᴛᴇ '{name}' ꜱᴀᴠᴇ ᴋᴀʀ ᴅɪʏᴀ\"</i> 💕", parse_mode=ParseMode.HTML)


async def get_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text(f"💝 {mention(update.effective_user)}\n<i>\"ᴜꜱᴀɢᴇ: /get [name]\"</i>", parse_mode=ParseMode.HTML)
    name = context.args[0].lower()
    note = notes_db.get(update.effective_chat.id, {}).get(name)
    if note:
        await update.message.reply_text(note, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(f"💘 {mention(update.effective_user)}\n<i>\"ɴᴏᴛᴇ '{name}' ɴᴀʜɪ ᴍɪʟᴀ\"</i>", parse_mode=ParseMode.HTML)


async def notes_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    notes = notes_db.get(update.effective_chat.id, {})
    if not notes:
        return await update.message.reply_text(f"💞 {mention(update.effective_user)}\n<i>\"ᴋᴏɪ ɴᴏᴛᴇ ɴᴀʜɪ ʜᴀɪ\"</i>", parse_mode=ParseMode.HTML)
    text = f"💓 <b>ɴᴏᴛᴇꜱ:</b>\n" + "\n".join(f"  ❣️ <code>{n}</code>" for n in notes.keys())
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def clear_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"❤️ {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    if not context.args:
        return await update.message.reply_text(f"🩷 {mention(update.effective_user)}\n<i>\"ᴜꜱᴀɢᴇ: /clear [name]\"</i>", parse_mode=ParseMode.HTML)
    name = context.args[0].lower()
    if name in notes_db.get(update.effective_chat.id, {}):
        del notes_db[update.effective_chat.id][name]
        await update.message.reply_text(f"🧡 {mention(update.effective_user)}\n<i>\"ɴᴏᴛᴇ '{name}' ᴅᴇʟᴇᴛᴇ ᴋᴀʀ ᴅɪʏᴀ\"</i> 💛", parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(f"💚 {mention(update.effective_user)}\n<i>\"ɴᴏᴛᴇ '{name}' ɴᴀʜɪ ᴍɪʟᴀ\"</i>", parse_mode=ParseMode.HTML)


async def clearall_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"💙 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    notes_db[update.effective_chat.id] = {}
    await update.message.reply_text(f"💜 {mention(update.effective_user)}\n<i>\"ꜱᴀᴀʀᴇ ɴᴏᴛᴇꜱ ᴅᴇʟᴇᴛᴇ ᴋᴀʀ ᴅɪʏᴇ\"</i> 🤍", parse_mode=ParseMode.HTML)


async def hashtag_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle #notename messages."""
    if not update.message or not update.message.text:
        return
    text = update.message.text
    if text.startswith("#"):
        name = text[1:].lower().split()[0]
        note = notes_db.get(update.effective_chat.id, {}).get(name)
        if note:
            await update.message.reply_text(note, parse_mode=ParseMode.HTML)


# ─── Lock / Unlock ───────────────────────────────────────────────────────────

LOCK_TYPES = {
    "messages": {"can_send_messages": False},
    "media": {"can_send_media_messages": False},
    "stickers": {"can_send_other_messages": False},
    "gifs": {"can_send_other_messages": False},
    "games": {"can_send_other_messages": False},
    "inline": {"can_send_other_messages": False},
    "url": {"can_add_web_page_previews": False},
    "polls": {"can_send_polls": False},
    "info": {"can_change_info": False},
    "invite": {"can_invite_users": False},
}


async def lock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"🖤 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    if not context.args or context.args[0].lower() not in LOCK_TYPES:
        types = ", ".join(LOCK_TYPES.keys())
        return await update.message.reply_text(f"🩵 {mention(update.effective_user)}\n<i>\"ᴜꜱᴀɢᴇ: /lock [type]\"</i>\nTypes: {types}", parse_mode=ParseMode.HTML)
    lock_type = context.args[0].lower()
    perms = await context.bot.get_chat(update.effective_chat.id)
    current = perms.permissions.to_dict() if perms.permissions else {}
    current.update(LOCK_TYPES[lock_type])
    await context.bot.set_chat_permissions(update.effective_chat.id, ChatPermissions(**current))
    await update.message.reply_text(
        f"💖 {mention(update.effective_user)}\n<i>\"{lock_type} ʟᴏᴄᴋ ᴋᴀʀ ᴅɪʏᴀ\"</i> 💗",
        parse_mode=ParseMode.HTML
    )


async def unlock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"💕 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    if not context.args:
        return await update.message.reply_text(f"💝 {mention(update.effective_user)}\n<i>\"ᴜꜱᴀɢᴇ: /unlock [type]\"</i>", parse_mode=ParseMode.HTML)
    lock_type = context.args[0].lower()
    unlock_map = {k: {kk: True for kk in v} for k, v in LOCK_TYPES.items()}
    if lock_type not in unlock_map:
        return await update.message.reply_text(f"💘 {mention(update.effective_user)}\n<i>\"ɪɴᴠᴀʟɪᴅ ʟᴏᴄᴋ ᴛʏᴘᴇ\"</i>", parse_mode=ParseMode.HTML)
    perms = await context.bot.get_chat(update.effective_chat.id)
    current = perms.permissions.to_dict() if perms.permissions else {}
    current.update(unlock_map[lock_type])
    await context.bot.set_chat_permissions(update.effective_chat.id, ChatPermissions(**current))
    await update.message.reply_text(
        f"💞 {mention(update.effective_user)}\n<i>\"{lock_type} ᴜɴʟᴏᴄᴋ ᴋᴀʀ ᴅɪʏᴀ\"</i> 💓",
        parse_mode=ParseMode.HTML
    )


# ─── Info Commands ───────────────────────────────────────────────────────────

async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"❣️ {mention(update.effective_user)}\n❤️ ᴛᴇʀᴀ ɪᴅ: <code>{update.effective_user.id}</code>\n"
    if update.effective_chat.type != "private":
        text += f"🩷 ᴄʜᴀᴛ ɪᴅ: <code>{update.effective_chat.id}</code>"
    if update.message.reply_to_message:
        text += f"\n🧡 ʀᴇᴘʟɪᴇᴅ ᴜꜱᴇʀ ɪᴅ: <code>{update.message.reply_to_message.from_user.id}</code>"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await get_target_user(update, context)
    if not target:
        target = update.effective_user
    text = (
        f"💛 <b>ᴜꜱᴇʀ ɪɴꜰᴏ</b>\n\n"
        f"💚 ɪᴅ: <code>{target.id}</code>\n"
        f"💙 ɴᴀᴍᴇ: {target.full_name}\n"
        f"💜 ᴜꜱᴇʀɴᴀᴍᴇ: @{target.username or 'N/A'}\n"
        f"🤍 ʙᴏᴛ: {'ʏᴇꜱ' if target.is_bot else 'ɴᴏ'}\n"
    )
    if update.effective_chat.type != "private":
        member = await context.bot.get_chat_member(update.effective_chat.id, target.id)
        text += f"🖤 ꜱᴛᴀᴛᴜꜱ: {member.status}\n"
        warns = warnings_db[update.effective_chat.id][target.id]
        text += f"🩵 ᴡᴀʀɴɪɴɢꜱ: {warns}/{MAX_WARNINGS}\n"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def admins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admins = await context.bot.get_chat_administrators(update.effective_chat.id)
    text = f"💖 <b>{update.effective_chat.title} ᴋᴇ ᴀᴅᴍɪɴꜱ</b>\n\n"
    for admin in admins:
        emoji = "💗" if admin.status == ChatMemberStatus.OWNER else "💕"
        text += f"{emoji} {admin.user.full_name}"
        if admin.custom_title:
            text += f" ─ {admin.custom_title}"
        text += "\n"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


# ─── Rules ───────────────────────────────────────────────────────────────────

rules_db: dict[int, str] = {}

async def setrules_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"💝 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    if not context.args:
        return await update.message.reply_text(f"💘 {mention(update.effective_user)}\n<i>\"ᴜꜱᴀɢᴇ: /setrules [text]\"</i>", parse_mode=ParseMode.HTML)
    rules_db[update.effective_chat.id] = " ".join(context.args)
    await update.message.reply_text(f"💞 {mention(update.effective_user)}\n<i>\"ʀᴜʟᴇꜱ ꜱᴇᴛ ᴋᴀʀ ᴅɪʏᴇ\"</i> 💓", parse_mode=ParseMode.HTML)


async def rules_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rules = rules_db.get(update.effective_chat.id, "ᴋᴏɪ ʀᴜʟᴇꜱ ꜱᴇᴛ ɴᴀʜɪ ʜᴀɪɴ. ᴀᴅᴍɪɴ /setrules ᴜꜱᴇ ᴋᴀʀᴇ.")
    await update.message.reply_text(
        f"❣️ <b>ɢʀᴏᴜᴘ ʀᴜʟᴇꜱ:</b>\n\n{rules} ❤️",
        parse_mode=ParseMode.HTML
    )


# ─── Log Channel ─────────────────────────────────────────────────────────────

async def setlog_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"🩷 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    if not context.args:
        return await update.message.reply_text(f"🧡 {mention(update.effective_user)}\n<i>\"ᴜꜱᴀɢᴇ: /setlog [channel_id]\"</i>", parse_mode=ParseMode.HTML)
    try:
        channel_id = int(context.args[0])
        log_channel[update.effective_chat.id] = channel_id
        await update.message.reply_text(f"💛 {mention(update.effective_user)}\n<i>\"ʟᴏɢ ᴄʜᴀɴɴᴇʟ ꜱᴇᴛ ᴋᴀʀ ᴅɪʏᴀ\"</i> 💚", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text(f"💙 {mention(update.effective_user)}\n<i>\"ᴠᴀʟɪᴅ ᴄʜᴀɴɴᴇʟ ɪᴅ ᴅᴏ\"</i>", parse_mode=ParseMode.HTML)


async def unsetlog_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text(f"💜 {mention(update.effective_user)}\n<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>", parse_mode=ParseMode.HTML)
    log_channel.pop(update.effective_chat.id, None)
    await update.message.reply_text(f"🤍 {mention(update.effective_user)}\n<i>\"ʟᴏɢ ᴄʜᴀɴɴᴇʟ ʀᴇᴍᴏᴠᴇ ᴋᴀʀ ᴅɪʏᴀ\"</i> 🖤", parse_mode=ParseMode.HTML)


# ─── Settings ────────────────────────────────────────────────────────────────

async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    flood = antiflood_settings.get(chat_id)
    flood_text = f"{flood['max_msgs']} ᴍꜱɢꜱ / {flood['time_window']}ꜱ" if flood else "ᴏꜰꜰ"
    link_text = "ᴏɴ 🩵" if anti_link.get(chat_id) else "ᴏꜰꜰ"
    words_count = len(banned_words.get(chat_id, []))
    notes_count = len(notes_db.get(chat_id, {}))
    log_text = str(log_channel.get(chat_id, "ɴᴏᴛ ꜱᴇᴛ"))
    welcome_text = "ᴄᴜꜱᴛᴏᴍ 💖" if chat_id in welcome_messages else "ᴅᴇꜰᴀᴜʟᴛ"
    goodbye_text = "ᴄᴜꜱᴛᴏᴍ 💗" if chat_id in goodbye_messages else "ᴅᴇꜰᴀᴜʟᴛ"

    text = (
        f"💕 <b>ɢʀᴏᴜᴘ ꜱᴇᴛᴛɪɴɢꜱ</b>\n\n"
        f"💝 ᴀɴᴛɪ-ꜰʟᴏᴏᴅ: {flood_text}\n"
        f"💘 ᴀɴᴛɪ-ʟɪɴᴋ: {link_text}\n"
        f"💞 ʙᴀɴɴᴇᴅ ᴡᴏʀᴅꜱ: {words_count}\n"
        f"💓 ɴᴏᴛᴇꜱ: {notes_count}\n"
        f"❣️ ʟᴏɢ ᴄʜᴀɴɴᴇʟ: {log_text}\n"
        f"❤️ ᴡᴇʟᴄᴏᴍᴇ: {welcome_text}\n"
        f"🩷 ɢᴏᴏᴅʙʏᴇ: {goodbye_text}\n"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════


async def track_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Track groups the bot is added to."""
    if update.message and update.effective_chat and update.effective_chat.type in ("group", "supergroup"):
        active_groups.add(update.effective_chat.id)


async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner-only broadcast to all groups."""
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text(
            f"🧡 {mention(update.effective_user)}\n<i>\"ꜱɪʀꜰ ʙᴏᴛ ᴏᴡɴᴇʀ ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴋᴀʀ ꜱᴀᴋᴛᴀ ʜᴀɪ\"</i> 💛",
            parse_mode=ParseMode.HTML
        )
    if not context.args:
        return await update.message.reply_text(
            f"💚 {mention(update.effective_user)}\n<i>\"ᴜꜱᴀɢᴇ: /broadcast [message]\"</i>",
            parse_mode=ParseMode.HTML
        )
    msg = " ".join(context.args)
    broadcast_text = (
        f"💙 <b>ʙʀᴏᴀᴅᴄᴀꜱᴛ ꜰʀᴏᴍ ᴏᴡɴᴇʀ</b> 💜\n\n"
        f"<i>\"{msg}\"</i>\n\n"
        f"🤍 @INFINITYxPRIME"
    )
    success = 0
    fail = 0
    for gid in list(active_groups):
        try:
            await context.bot.send_message(gid, broadcast_text, parse_mode=ParseMode.HTML)
            success += 1
        except Exception:
            active_groups.discard(gid)
            fail += 1
    await update.message.reply_text(
        f"🖤 {mention(update.effective_user)}\n"
        f"<i>\"ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴅᴏɴᴇ\"</i> 🩵\n\n"
        f"💖 ꜱᴜᴄᴄᴇꜱꜱ: {success}\n"
        f"💗 ꜰᴀɪʟᴇᴅ: {fail}",
        parse_mode=ParseMode.HTML
    )




# ─── Time Command ────────────────────────────────────────────────────────────

async def time_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current India time."""
    india_tz = ZoneInfo("Asia/Kolkata")
    now = datetime.now(india_tz)
    
    time_str = now.strftime("%I:%M:%S %p")
    date_str = now.strftime("%d %B %Y")
    day_str = now.strftime("%A")
    
    body = (
        f"  🩷 ᴛɪᴍᴇ: <code>{time_str}</code>\n"
        f"  🧡 ᴅᴀᴛᴇ: <code>{date_str}</code>\n"
        f"  💛 ᴅᴀʏ: <code>{day_str}</code>\n"
        f"  💚 ᴢᴏɴᴇ: <code>IST (UTC+5:30)</code>\n"
        f"  💙 ᴜꜱᴇʀ: {mention(update.effective_user)}"
    )
    await update.message.reply_text(
        box("🇮🇳 ɪɴᴅɪᴀ ᴛɪᴍᴇ", body, "💜", "🩵"),
        parse_mode=ParseMode.HTML
    )


# ─── Stats Command ──────────────────────────────────────────────────────────

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show full bot stats with DP."""
    bot = context.bot
    bot_info = await bot.get_me()
    
    uptime = datetime.now() - BOT_START_TIME
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    days = hours // 24
    hours = hours % 24
    
    total_groups = len(active_groups)
    total_warns = sum(sum(v.values()) for v in warnings_db.values())
    total_notes = sum(len(v) for v in notes_db.values())
    total_banned_words = sum(len(v) for v in banned_words.values())
    
    body = (
        f"  💖 ɴᴀᴍᴇ: <b>{bot_info.full_name}</b>\n"
        f"  💗 ᴜꜱᴇʀɴᴀᴍᴇ: @{bot_info.username}\n"
        f"  💕 ɪᴅ: <code>{bot_info.id}</code>\n"
        f"  💝 ᴘʏᴛʜᴏɴ: <code>{platform.python_version()}</code>\n"
        f"  💘 ᴜᴘᴛɪᴍᴇ: <code>{days}ᴅ {hours}ʜ {minutes}ᴍ {seconds}ꜱ</code>\n"
        f"  💞 ɢʀᴏᴜᴘꜱ: <code>{total_groups}</code>\n"
        f"  💓 ᴡᴀʀɴɪɴɢꜱ: <code>{total_warns}</code>\n"
        f"  ❣️ ɴᴏᴛᴇꜱ: <code>{total_notes}</code>\n"
        f"  ❤️ ʙᴀɴɴᴇᴅ ᴡᴏʀᴅꜱ: <code>{total_banned_words}</code>\n"
        f"  🩷 ᴏᴡɴᴇʀ: @INFINITYxPRIME"
    )
    
    # Try to send with bot DP
    try:
        photos = await bot.get_user_profile_photos(bot_info.id, limit=1)
        if photos.total_count > 0:
            photo = photos.photos[0][-1]
            await update.message.reply_photo(
                photo=photo.file_id,
                caption=box("ʙᴏᴛ ꜱᴛᴀᴛꜱ", body, "🧡", "💛"),
                parse_mode=ParseMode.HTML
            )
            return
    except Exception:
        pass
    
    await update.message.reply_text(
        box("ʙᴏᴛ ꜱᴛᴀᴛꜱ", body, "🧡", "💛"),
        parse_mode=ParseMode.HTML
    )


# ─── Funny Commands ─────────────────────────────────────────────────────────

async def roast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Roast a user."""
    target = await get_target_user(update, context)
    if not target:
        target = update.effective_user
    roast = random.choice(ROASTS)
    body = (
        f"  🔥 ᴛᴀʀɢᴇᴛ: {mention(target)}\n"
        f"  💀 <i>\"{roast}\"</i>"
    )
    await update.message.reply_text(
        box("ʀᴏᴀꜱᴛ 🔥", body, "🖤", "💜"),
        parse_mode=ParseMode.HTML
    )


async def love_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Love percentage between two users."""
    target = await get_target_user(update, context)
    if not target:
        return await update.message.reply_text(
            f"💖 {mention(update.effective_user)}\n<i>\"ᴋɪꜱɪ ᴘᴇ ʀᴇᴘʟʏ ᴋᴀʀᴏ ʏᴀ ᴜꜱᴇʀ ɪᴅ ᴅᴏ\"</i>",
            parse_mode=ParseMode.HTML
        )
    percentage = random.randint(1, 100)
    hearts_bar = "❤️" * (percentage // 10) + "🤍" * (10 - percentage // 10)
    body = (
        f"  💘 {mention(update.effective_user)} & {mention(target)}\n"
        f"  💕 ʟᴏᴠᴇ: <b>{percentage}%</b>\n"
        f"  {hearts_bar}"
    )
    await update.message.reply_text(
        box("ʟᴏᴠᴇ ᴍᴇᴛᴇʀ 💕", body, "💖", "💗"),
        parse_mode=ParseMode.HTML
    )


async def quote_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a random love quote."""
    q = random.choice(LOVE_QUOTES)
    body = (
        f"  💌 {mention(update.effective_user)}\n"
        f"  💝 <i>\"{q}\"</i>"
    )
    await update.message.reply_text(
        box("ʟᴏᴠᴇ ǫᴜᴏᴛᴇ 💌", body, "💖", "💗"),
        parse_mode=ParseMode.HTML
    )


async def truth_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a random truth question."""
    target = await get_target_user(update, context)
    if not target:
        target = update.effective_user
    q = random.choice(TRUTH_QUESTIONS)
    body = (
        f"  🎯 ᴛᴀʀɢᴇᴛ: {mention(target)}\n"
        f"  💬 <i>\"{q}\"</i>"
    )
    await update.message.reply_text(
        box("ᴛʀᴜᴛʜ 🎯", body, "💚", "💙"),
        parse_mode=ParseMode.HTML
    )


async def dare_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a random dare challenge."""
    target = await get_target_user(update, context)
    if not target:
        target = update.effective_user
    d = random.choice(DARE_CHALLENGES)
    body = (
        f"  ⚡ ᴛᴀʀɢᴇᴛ: {mention(target)}\n"
        f"  🎲 <i>\"{d}\"</i>"
    )
    await update.message.reply_text(
        box("ᴅᴀʀᴇ ⚡", body, "🧡", "💛"),
        parse_mode=ParseMode.HTML
    )


async def flirt_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a flirty line to someone."""
    target = await get_target_user(update, context)
    if not target:
        target = update.effective_user
    line = random.choice(FLIRT_LINES)
    body = (
        f"  😏 ᴛᴏ: {mention(target)}\n"
        f"  💋 ꜰʀᴏᴍ: {mention(update.effective_user)}\n"
        f"  💕 <i>\"{line}\"</i>"
    )
    await update.message.reply_text(
        box("ꜰʟɪʀᴛ 😏", body, "💖", "💘"),
        parse_mode=ParseMode.HTML
    )


async def decide_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Random yes/no decision maker."""
    answers = [
        ("ʜᴀᴀɴ ʙɪʟᴋᴜʟ! 💚", "✅"),
        ("ɴᴀ ʙʜᴀɪ ɴᴀ! 🖤", "❌"),
        ("ꜱʜᴀᴀʏᴀᴅ... 💛", "🤔"),
        ("1000% ʜᴀᴀɴ! 💖", "💯"),
        ("ʙɪʟᴋᴜʟ ɴᴀʜɪ! 💜", "🚫"),
        ("ᴘᴜᴄʜ ᴍᴀᴛ ʏᴀᴀʀ! 🩷", "😅"),
        ("ᴋʏᴜ ɴᴀʜɪ! 💙", "👍"),
        ("ꜱᴏᴄʜ ʟᴇ ᴘʜɪʀ ꜱᴇ! 🧡", "🔄"),
    ]
    ans, emoji = random.choice(answers)
    question = " ".join(context.args) if context.args else "ᴋᴏɪ ꜱᴀᴡᴀᴀʟ ɴᴀʜɪ ᴘᴜᴄʜᴀ"
    body = (
        f"  ❓ ꜱᴀᴡᴀᴀʟ: <i>\"{question}\"</i>\n"
        f"  {emoji} ᴊᴀᴡᴀᴀʙ: <b>{ans}</b>\n"
        f"  💕 ᴘᴜᴄʜɴᴇ ᴡᴀʟᴀ: {mention(update.effective_user)}"
    )
    await update.message.reply_text(
        box("ꜰᴀɪꜱʟᴀ 🎱", body, "💝", "💞"),
        parse_mode=ParseMode.HTML
    )



async def owner_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot owner info."""
    await update.message.reply_text(
        f"💕 {mention(update.effective_user)}\n"
        f"💝 <b>ʙᴏᴛ ᴏᴡɴᴇʀ:</b>@INFINITYxPRIME\n"
        f"<i>\"ᴋᴏɪ ᴘʀᴏʙʟᴇᴍ ʜᴏ ᴛᴏʜ ᴏᴡɴᴇʀ ꜱᴇ ᴄᴏɴᴛᴀᴄᴛ ᴋᴀʀᴏ\"</i> 💘",
        parse_mode=ParseMode.HTML
    )

def main():
    """Start the bot."""
    app = Application.builder().token(BOT_TOKEN).build()

    # Basic commands
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("owner", owner_cmd))
    app.add_handler(CallbackQueryHandler(help_callback, pattern="^help_"))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("time", time_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))

    # Funny commands
    app.add_handler(CommandHandler("roast", roast_cmd))
    app.add_handler(CommandHandler("love", love_cmd))
    app.add_handler(CommandHandler("quote", quote_cmd))
    app.add_handler(CommandHandler("truth", truth_cmd))
    app.add_handler(CommandHandler("dare", dare_cmd))
    app.add_handler(CommandHandler("flirt", flirt_cmd))
    app.add_handler(CommandHandler("decide", decide_cmd))

    # Admin commands
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))
    app.add_handler(CommandHandler("kick", kick_cmd))
    app.add_handler(CommandHandler("mute", mute_cmd))
    app.add_handler(CommandHandler("unmute", unmute_cmd))
    app.add_handler(CommandHandler("tmute", tmute_cmd))
    app.add_handler(CommandHandler("tban", tban_cmd))

    # Warn system
    app.add_handler(CommandHandler("warn", warn_cmd))
    app.add_handler(CommandHandler("unwarn", unwarn_cmd))
    app.add_handler(CommandHandler("warns", warns_cmd))
    app.add_handler(CommandHandler("resetwarns", resetwarns_cmd))

    # Promote/Demote
    app.add_handler(CommandHandler("promote", promote_cmd))
    app.add_handler(CommandHandler("demote", demote_cmd))

    # Pin/Purge
    app.add_handler(CommandHandler("pin", pin_cmd))
    app.add_handler(CommandHandler("unpin", unpin_cmd))
    app.add_handler(CommandHandler("unpinall", unpinall_cmd))
    app.add_handler(CommandHandler("purge", purge_cmd))
    app.add_handler(CommandHandler("del", del_cmd))

    # Welcome/Goodbye
    app.add_handler(CommandHandler("setwelcome", set_welcome))
    app.add_handler(CommandHandler("setgoodbye", set_goodbye))
    app.add_handler(CommandHandler("resetwelcome", reset_welcome))
    app.add_handler(CommandHandler("resetgoodbye", reset_goodbye))
    app.add_handler(ChatMemberHandler(greet_member, ChatMemberHandler.CHAT_MEMBER))

    # Anti-flood
    app.add_handler(CommandHandler("antiflood", antiflood_cmd))
    app.add_handler(CommandHandler("antifloodoff", antiflood_off))

    # Anti-link
    app.add_handler(CommandHandler("antilink", antilink_cmd))

    # Banned words
    app.add_handler(CommandHandler("addword", addword_cmd))
    app.add_handler(CommandHandler("rmword", rmword_cmd))
    app.add_handler(CommandHandler("wordlist", wordlist_cmd))

    # Notes
    app.add_handler(CommandHandler("save", save_note))
    app.add_handler(CommandHandler("get", get_note))
    app.add_handler(CommandHandler("notes", notes_list))
    app.add_handler(CommandHandler("clear", clear_note))
    app.add_handler(CommandHandler("clearall", clearall_notes))

    # Lock/Unlock
    app.add_handler(CommandHandler("lock", lock_cmd))
    app.add_handler(CommandHandler("unlock", unlock_cmd))

    # Info
    app.add_handler(CommandHandler("id", id_cmd))
    app.add_handler(CommandHandler("info", info_cmd))
    app.add_handler(CommandHandler("admins", admins_cmd))

    # Rules
    app.add_handler(CommandHandler("setrules", setrules_cmd))
    app.add_handler(CommandHandler("rules", rules_cmd))

    # Log channel
    app.add_handler(CommandHandler("setlog", setlog_cmd))
    app.add_handler(CommandHandler("unsetlog", unsetlog_cmd))

    # Settings
    app.add_handler(CommandHandler("settings", settings_cmd))

    # Message handlers (filters) - ORDER MATTERS
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r"^#"), hashtag_notes))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, check_flood), group=1)
    app.add_handler(MessageHandler(filters.Entity("url") | filters.Entity("text_link"), check_links), group=2)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_banned_words), group=3)
    app.add_handler(MessageHandler(filters.ALL, track_groups), group=4)

    print("💞 Bot started! Press Ctrl+C to stop.")
    print("💓 Owner ID:", OWNER_ID)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

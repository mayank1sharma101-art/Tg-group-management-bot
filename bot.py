#!/usr/bin/env python3
"""
✨ Premium Telegram Group Manager Bot ✨
Full-featured group management bot.
Requirements: pip install -r requirements.txt
"""

import logging
import os
import asyncio
from datetime import datetime, timedelta
import random
import platform
from collections import defaultdict
from functools import wraps
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, ChatMemberHandler,
    CallbackQueryHandler, MessageHandler, filters, ContextTypes
)
from telegram.constants import ParseMode, ChatMemberStatus

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set!")

OWNER_ID = int(os.getenv("OWNER_ID", "0"))
if OWNER_ID == 0:
    raise ValueError("OWNER_ID environment variable not set!")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

warnings_db = defaultdict(lambda: defaultdict(int))
MAX_WARNINGS = 3
welcome_messages = {}
goodbye_messages = {}
antiflood_settings = {}
flood_tracker = defaultdict(lambda: defaultdict(list))
banned_words = defaultdict(list)
anti_link = defaultdict(bool)
notes_db = defaultdict(dict)
rules_db = {}
log_channel = {}
active_groups = set()
BOT_START_TIME = datetime.now()


def mention(user):
    return f'<a href="tg://user?id={user.id}">{user.first_name}</a>'


def box(title, body, heart1="💎", heart2="💠"):
    top = "╔═══════════════════════╗"
    bottom = "╚═══════════════════════╝"
    return (
        f"<code>{top}</code>\n"
        f"  {heart1} <b>{title}</b> {heart2}\n"
        f"<code>╠═══════════════════════╣</code>\n"
        f"{body}\n"
        f"<code>{bottom}</code>"
    )


async def safe_get_member(chat_id, user_id, bot):
    try:
        return await bot.get_chat_member(chat_id, user_id)
    except Exception:
        return None


async def is_admin(update, context, user_id=None):
    uid = user_id or update.effective_user.id
    member = await safe_get_member(update.effective_chat.id, uid, context.bot)
    if member is None:
        return False
    return member.status in (
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER,
    )


async def get_target_user(update, context):
    if update.message.reply_to_message:
        return update.message.reply_to_message.from_user

    if context.args:
        try:
            user_id = int(context.args[0])
            member = await safe_get_member(
                update.effective_chat.id, user_id, context.bot
            )
            if member:
                return member.user
        except (ValueError, TypeError):
            pass
    return None


async def log_action(context, chat_id, text):
    if chat_id in log_channel:
        try:
            await context.bot.send_message(
                log_channel[chat_id], text, parse_mode=ParseMode.HTML
            )
        except Exception:
            pass


def admin_only(func):
    @wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        if not await is_admin(update, context):
            await update.message.reply_text(
                f"🚫 {mention(update.effective_user)}\n"
                f"<i>\"ᴛᴜᴍ ᴀᴅᴍɪɴ ɴᴀʜɪ ʜᴏ\"</i>",
                parse_mode=ParseMode.HTML,
            )
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


def parse_time(time_str):
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


async def start_cmd(update, context):
    user = update.effective_user
    username = context.bot.username or "your_bot"
    keyboard = [
        [
            InlineKeyboardButton("❤️ ᴄᴏᴍᴍᴀɴᴅꜱ", callback_data="help_menu"),
            InlineKeyboardButton(
                "🩷 ᴀᴅᴅ ᴛᴏ ɢʀᴏᴜᴘ",
                url=f"https://t.me/{username}?startgroup=true",
            ),
        ],
        [InlineKeyboardButton("🧡 ᴏᴡɴᴇʀ", url="https://t.me/Teamapst")],
    ]
    await update.message.reply_text(
        f"💎 <b>ᴘʀᴇᴍɪᴜᴍ ɢʀᴏᴜᴘ ᴍᴀɴᴀɢᴇʀ ʙᴏᴛ</b> 💎\n\n"
        f"ʜᴇʏ {mention(user)} 💚\n"
        f"ᴍᴜᴊʜᴇ ɢʀᴏᴜᴘ ᴍᴇɪɴ ᴀᴅᴅ ᴋᴀʀᴏ ᴀᴜʀ ᴀᴅᴍɪɴ ʙᴀɴᴀᴏ 💙\n\n"
        f"<b>💜 ꜰᴇᴀᴛᴜʀᴇꜱ:</b>\n"
        f"  🤍 ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅꜱ\n"
        f"  🖤 ᴡᴇʟᴄᴏᴍᴇ & ɢᴏᴏᴅʙʏᴇ\n"
        f"  🩵 ᴀɴᴛɪ-ꜱᴘᴀᴍ & ᴀɴᴛɪ-ꜰʟᴏᴏᴅ\n"
        f"  💖 ᴀɴᴛɪ-ʟɪɴᴋ\n"
        f"  💗 ɴᴏᴛᴇꜱ\n"
        f"  💕 ʟᴏᴄᴋ/ᴜɴʟᴏᴄᴋ\n\n"
        f"<i>\"ᴜꜱᴇ /help ꜰᴏʀ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅꜱ\"</i> 💘\n\n"
        f"💞 <b>ᴏᴡɴᴇʀ:</b> @Teamapst",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


HELP_TEXTS = {
    "help_admin": (
        "🤍 <b>ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅꜱ</b>\n\n"
        "/ban /unban /mute /unmute /tmute /tban\n"
        "/kick /warn /unwarn /warns /resetwarns\n"
        "/promote /demote /pin /unpin /unpinall /purge /del"
    ),
    "help_welcome": (
        "🖤 <b>ᴡᴇʟᴄᴏᴍᴇ & ɢᴏᴏᴅʙʏᴇ</b>\n\n"
        "/setwelcome [text]\n/setgoodbye [text]\n"
        "/resetwelcome\n/resetgoodbye\n\n"
        "{first} {last} {fullname} {username} {id} {chatname} {count}"
    ),
    "help_antispam": (
        "💘 <b>ᴀɴᴛɪ-ꜱᴘᴀᴍ & ꜰɪʟᴛᴇʀꜱ</b>\n\n"
        "/antiflood [count]\n/antifloodoff\n"
        "/antilink on/off\n/addword [word]\n/rmword [word]\n/wordlist"
    ),
    "help_notes": (
        "💛 <b>ɴᴏᴛᴇꜱ ꜱʏꜱᴛᴇᴍ</b>\n\n"
        "/save [name] [text]\n/get [name]\n#notename\n"
        "/notes\n/clear [name]\n/clearall"
    ),
    "help_locks": (
        "💖 <b>ʟᴏᴄᴋ / ᴜɴʟᴏᴄᴋ</b>\n\n"
        "/lock [type]\n/unlock [type]\n/locks\n\n"
        "Types: messages, media, stickers, gifs, games, inline, "
        "url, polls, info, invite"
    ),
    "help_settings": (
        "💞 <b>ꜱᴇᴛᴛɪɴɢꜱ</b>\n\n"
        "/setlog [channel_id]\n/unsetlog\n/settings\n/id\n"
        "/info\n/admins\n/rules\n/setrules [text]"
    ),
}


async def help_cmd(update, context):
    keyboard = [
        [
            InlineKeyboardButton("💓 ᴀᴅᴍɪɴ", callback_data="help_admin"),
            InlineKeyboardButton("❣️ ᴡᴇʟᴄᴏᴍᴇ", callback_data="help_welcome"),
        ],
        [
            InlineKeyboardButton("❤️ ᴀɴᴛɪ-ꜱᴘᴀᴍ", callback_data="help_antispam"),
            InlineKeyboardButton("🩷 ɴᴏᴛᴇꜱ", callback_data="help_notes"),
        ],
        [
            InlineKeyboardButton("🧡 ʟᴏᴄᴋꜱ", callback_data="help_locks"),
            InlineKeyboardButton("💛 ꜱᴇᴛᴛɪɴɢꜱ", callback_data="help_settings"),
        ],
    ]
    await update.message.reply_text(
        f"💚 <b>ʜᴇʟᴘ ᴍᴇɴᴜ</b>\n\n"
        f"ʜᴇʏ {mention(update.effective_user)} 💙\n"
        f"💜 ʙᴏᴛ ᴏᴡɴᴇʀ: @Teamapst",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def help_callback(update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "help_menu":
        await query.edit_message_text(
            "💕 <b>ʜᴇʟᴘ ᴍᴇɴᴜ</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("💞 ʙᴀᴄᴋ", callback_data="help_menu")]]
            ),
        )
        return

    text = HELP_TEXTS.get(query.data)
    if text:
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("💞 ʙᴀᴄᴋ", callback_data="help_menu")]]
            ),
        )


async def require_target(update, context):
    target = await get_target_user(update, context)
    if not target:
        await update.message.reply_text(
            f"❣️ {mention(update.effective_user)}\n"
            f"<i>Reply to a user or provide a numeric user ID.</i>",
            parse_mode=ParseMode.HTML,
        )
    return target


@admin_only
async def ban_cmd(update, context):
    target = await require_target(update, context)
    if not target:
        return
    if await is_admin(update, context, target.id):
        await update.message.reply_text("🚫 Admins cannot be banned by this command.")
        return
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason"
    await context.bot.ban_chat_member(update.effective_chat.id, target.id)
    await update.message.reply_text(
        f"🩷 {mention(target)} ᴋᴏ ʙᴀɴ ᴋᴀʀ ᴅɪʏᴀ\n"
        f"<i>Reason: {reason}</i>",
        parse_mode=ParseMode.HTML,
    )
    await log_action(
        context,
        update.effective_chat.id,
        f"💚 #BAN\nUser: {target.full_name} ({target.id})\n"
        f"By: {update.effective_user.full_name}\nReason: {reason}",
    )


@admin_only
async def unban_cmd(update, context):
    target = await require_target(update, context)
    if not target:
        return
    await context.bot.unban_chat_member(
        update.effective_chat.id, target.id, only_if_banned=True
    )
    await update.message.reply_text(
        f"🤍 {mention(target)} ᴋᴏ ᴜɴʙᴀɴ ᴋᴀʀ ᴅɪʏᴀ",
        parse_mode=ParseMode.HTML,
    )


@admin_only
async def kick_cmd(update, context):
    target = await require_target(update, context)
    if not target:
        return
    if await is_admin(update, context, target.id):
        await update.message.reply_text("🚫 Admins cannot be kicked by this command.")
        return
    await context.bot.ban_chat_member(update.effective_chat.id, target.id)
    await context.bot.unban_chat_member(update.effective_chat.id, target.id)
    await update.message.reply_text(
        f"💝 {mention(target)} ᴋᴏ ᴋɪᴄᴋ ᴋᴀʀ ᴅɪʏᴀ",
        parse_mode=ParseMode.HTML,
    )


@admin_only
async def mute_cmd(update, context):
    target = await require_target(update, context)
    if not target:
        return
    if await is_admin(update, context, target.id):
        await update.message.reply_text("🚫 Admins cannot be muted by this command.")
        return
    await context.bot.restrict_chat_member(
        update.effective_chat.id,
        target.id,
        permissions=ChatPermissions(can_send_messages=False),
    )
    await update.message.reply_text(
        f"🩷 {mention(target)} ᴋᴏ ᴍᴜᴛᴇ ᴋᴀʀ ᴅɪʏᴀ",
        parse_mode=ParseMode.HTML,
    )


@admin_only
async def unmute_cmd(update, context):
    target = await require_target(update, context)
    if not target:
        return
    await context.bot.restrict_chat_member(
        update.effective_chat.id,
        target.id,
        permissions=ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_invite_users=True,
        ),
    )
    await update.message.reply_text(
        f"💜 {mention(target)} ᴋᴏ ᴜɴᴍᴜᴛᴇ ᴋᴀʀ ᴅɪʏᴀ",
        parse_mode=ParseMode.HTML,
    )


@admin_only
async def tmute_cmd(update, context):
    target = await require_target(update, context)
    if not target or not context.args:
        return
    duration = parse_time(context.args[0])
    if not duration:
        await update.message.reply_text("Invalid time. Use 30m, 1h, 1d or 1w.")
        return
    await context.bot.restrict_chat_member(
        update.effective_chat.id,
        target.id,
        permissions=ChatPermissions(can_send_messages=False),
        until_date=datetime.now() + duration,
    )
    await update.message.reply_text(
        f"💕 {mention(target)} ᴋᴏ {context.args[0]} ᴋᴇ ʟɪʏᴇ ᴍᴜᴛᴇ",
        parse_mode=ParseMode.HTML,
    )


@admin_only
async def tban_cmd(update, context):
    target = await require_target(update, context)
    if not target or not context.args:
        return
    duration = parse_time(context.args[0])
    if not duration:
        await update.message.reply_text("Invalid time. Use 30m, 1h, 1d or 1w.")
        return
    await context.bot.ban_chat_member(
        update.effective_chat.id,
        target.id,
        until_date=datetime.now() + duration,
    )
    await update.message.reply_text(
        f"❤️ {mention(target)} ᴋᴏ {context.args[0]} ᴋᴇ ʟɪʏᴇ ʙᴀɴ",
        parse_mode=ParseMode.HTML,
    )


@admin_only
async def warn_cmd(update, context):
    target = await require_target(update, context)
    if not target:
        return
    if await is_admin(update, context, target.id):
        await update.message.reply_text("🚫 Admins cannot be warned.")
        return
    chat_id = update.effective_chat.id
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason"
    warnings_db[chat_id][target.id] += 1
    count = warnings_db[chat_id][target.id]

    if count >= MAX_WARNINGS:
        await context.bot.ban_chat_member(chat_id, target.id)
        warnings_db[chat_id][target.id] = 0
        await update.message.reply_text(
            f"💜 {mention(target)} ᴋᴏ {MAX_WARNINGS} ᴡᴀʀɴɪɴɢꜱ ᴘᴀʀ ʙᴀɴ",
            parse_mode=ParseMode.HTML,
        )
    else:
        await update.message.reply_text(
            f"🩵 {mention(target)} ᴋᴏ ᴡᴀʀɴ ({count}/{MAX_WARNINGS})\n"
            f"<i>Reason: {reason}</i>",
            parse_mode=ParseMode.HTML,
        )


@admin_only
async def unwarn_cmd(update, context):
    target = await require_target(update, context)
    if not target:
        return
    chat_id = update.effective_chat.id
    warnings_db[chat_id][target.id] = max(
        0, warnings_db[chat_id][target.id] - 1
    )
    await update.message.reply_text(
        f"💘 {mention(target)} ᴋɪ ᴇᴋ ᴡᴀʀɴɪɴɢ ʜᴀᴛᴀ ᴅɪ",
        parse_mode=ParseMode.HTML,
    )


async def warns_cmd(update, context):
    target = await get_target_user(update, context) or update.effective_user
    count = warnings_db[update.effective_chat.id][target.id]
    await update.message.reply_text(
        f"❣️ {mention(target)} ᴋɪ ᴡᴀʀɴɪɴɢꜱ: {count}/{MAX_WARNINGS}",
        parse_mode=ParseMode.HTML,
    )


@admin_only
async def resetwarns_cmd(update, context):
    target = await require_target(update, context)
    if not target:
        return
    warnings_db[update.effective_chat.id][target.id] = 0
    await update.message.reply_text(
        f"💛 {mention(target)} ᴋɪ ᴡᴀʀɴɪɴɢꜱ ʀᴇꜱᴇᴛ",
        parse_mode=ParseMode.HTML,
    )


@admin_only
async def promote_cmd(update, context):
    target = await require_target(update, context)
    if not target:
        return
    title = " ".join(context.args[1:]) if len(context.args) > 1 else "Admin"
    await context.bot.promote_chat_member(
        update.effective_chat.id,
        target.id,
        can_delete_messages=True,
        can_restrict_members=True,
        can_invite_users=True,
        can_pin_messages=True,
        can_manage_video_chats=True,
    )
    try:
        await context.bot.set_chat_administrator_custom_title(
            update.effective_chat.id, target.id, title
        )
    except Exception:
        pass
    await update.message.reply_text(
        f"🖤 {mention(target)} ᴋᴏ ᴀᴅᴍɪɴ ʙᴀɴᴀ ᴅɪʏᴀ",
        parse_mode=ParseMode.HTML,
    )


@admin_only
async def demote_cmd(update, context):
    target = await require_target(update, context)
    if not target:
        return
    await context.bot.promote_chat_member(
        update.effective_chat.id,
        target.id,
        can_delete_messages=False,
        can_restrict_members=False,
        can_invite_users=False,
        can_pin_messages=False,
        can_manage_video_chats=False,
    )
    await update.message.reply_text(
        f"💝 {mention(target)} ᴋᴏ ᴅᴇᴍᴏᴛᴇ ᴋᴀʀ ᴅɪʏᴀ",
        parse_mode=ParseMode.HTML,
    )


@admin_only
async def pin_cmd(update, context):
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message to pin it.")
        return
    await update.message.reply_to_message.pin(
        disable_notification="loud" not in (context.args or [])
    )
    await update.message.reply_text("📌 Message pinned.")


@admin_only
async def unpin_cmd(update, context):
    if update.message.reply_to_message:
        await update.message.reply_to_message.unpin()
    else:
        await context.bot.unpin_chat_message(update.effective_chat.id)
    await update.message.reply_text("📌 Message unpinned.")


@admin_only
async def unpinall_cmd(update, context):
    await context.bot.unpin_all_chat_messages(update.effective_chat.id)
    await update.message.reply_text("📌 All messages unpinned.")


@admin_only
async def purge_cmd(update, context):
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to the first message to purge from.")
        return
    start_id = update.message.reply_to_message.message_id
    end_id = update.message.message_id
    deleted = 0
    for msg_id in range(start_id, end_id + 1):
        try:
            await context.bot.delete_message(update.effective_chat.id, msg_id)
            deleted += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
    msg = await update.effective_chat.send_message(f"🧹 Deleted {deleted} messages.")
    await asyncio.sleep(3)
    try:
        await msg.delete()
    except Exception:
        pass


@admin_only
async def del_cmd(update, context):
    if update.message.reply_to_message:
        try:
            await update.message.reply_to_message.delete()
            await update.message.delete()
        except Exception:
            pass


@admin_only
async def set_welcome(update, context):
    if not context.args:
        await update.message.reply_text("Usage: /setwelcome [message]")
        return
    welcome_messages[update.effective_chat.id] = " ".join(context.args)
    await update.message.reply_text("💝 Welcome message saved.")


@admin_only
async def set_goodbye(update, context):
    if not context.args:
        await update.message.reply_text("Usage: /setgoodbye [message]")
        return
    goodbye_messages[update.effective_chat.id] = " ".join(context.args)
    await update.message.reply_text("💝 Goodbye message saved.")


@admin_only
async def reset_welcome(update, context):
    welcome_messages.pop(update.effective_chat.id, None)
    await update.message.reply_text("Welcome message reset.")


@admin_only
async def reset_goodbye(update, context):
    goodbye_messages.pop(update.effective_chat.id, None)
    await update.message.reply_text("Goodbye message reset.")


def format_welcome(text, user, chat):
    return text.format(
        first=user.first_name or "",
        last=user.last_name or "",
        fullname=user.full_name or "",
        username=f"@{user.username}" if user.username else user.full_name,
        id=user.id,
        chatname=chat.title or "",
        count="N/A",
    )


async def greet_member(update, context):
    result = update.chat_member
    if not update.effective_chat or not result:
        return

    active_groups.add(update.effective_chat.id)

    if result.new_chat_member.status == ChatMemberStatus.MEMBER:
        chat_id = update.effective_chat.id
        user = result.new_chat_member.user
        text = format_welcome(
            welcome_messages[chat_id], user, update.effective_chat
        ) if chat_id in welcome_messages else (
            f"🖤 ᴡᴇʟᴄᴏᴍᴇ {mention(user)} 🩵\n"
            f"ᴛᴜᴍ <b>{update.effective_chat.title}</b> ᴍᴇɪɴ ᴀᴀ ɢᴀʏᴇ"
        )
        await context.bot.send_message(
            chat_id, text, parse_mode=ParseMode.HTML
        )

    elif result.new_chat_member.status in (
        ChatMemberStatus.LEFT, ChatMemberStatus.BANNED
    ):
        chat_id = update.effective_chat.id
        user = result.old_chat_member.user
        text = format_welcome(
            goodbye_messages[chat_id], user, update.effective_chat
        ) if chat_id in goodbye_messages else (
            f"💗 {mention(user)} ɢʀᴏᴜᴘ ᴄʜʜᴏᴅ ᴋᴇ ᴄʜᴀʟᴀ ɢᴀʏᴀ"
        )
        await context.bot.send_message(
            chat_id, text, parse_mode=ParseMode.HTML
        )


@admin_only
async def antiflood_cmd(update, context):
    if not context.args:
        await update.message.reply_text("Usage: /antiflood [count]")
        return
    try:
        count = int(context.args[0])
        if count < 3:
            await update.message.reply_text("Minimum count is 3.")
            return
        antiflood_settings[update.effective_chat.id] = {
            "max_msgs": count, "time_window": 5
        }
        await update.message.reply_text(
            f"💓 Anti-flood enabled: {count} messages / 5s."
        )
    except ValueError:
        await update.message.reply_text("Give a valid number.")


@admin_only
async def antiflood_off(update, context):
    antiflood_settings.pop(update.effective_chat.id, None)
    await update.message.reply_text("Anti-flood disabled.")


async def check_flood(update, context):
    if not update.message or not update.effective_chat:
        return
    chat_id = update.effective_chat.id
    if chat_id not in antiflood_settings:
        return
    if await is_admin(update, context, update.effective_user.id):
        return

    user_id = update.effective_user.id
    settings = antiflood_settings[chat_id]
    now = datetime.now().timestamp()
    flood_tracker[chat_id][user_id] = [
        t for t in flood_tracker[chat_id][user_id]
        if now - t < settings["time_window"]
    ]
    flood_tracker[chat_id][user_id].append(now)

    if len(flood_tracker[chat_id][user_id]) > settings["max_msgs"]:
        await context.bot.restrict_chat_member(
            chat_id,
            user_id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=datetime.now() + timedelta(hours=1),
        )
        flood_tracker[chat_id][user_id] = []
        await update.message.reply_text(
            f"💚 {mention(update.effective_user)} ᴋᴏ ꜰʟᴏᴏᴅɪɴɢ ᴋᴇ ʟɪʏᴇ 1 ʜᴏᴜʀ ᴍᴜᴛᴇ",
            parse_mode=ParseMode.HTML,
        )


@admin_only
async def antilink_cmd(update, context):
    if not context.args or context.args[0].lower() not in ("on", "off"):
        await update.message.reply_text("Usage: /antilink on/off")
        return
    anti_link[update.effective_chat.id] = context.args[0].lower() == "on"
    await update.message.reply_text(
        f"💖 Anti-link: {'ON' if anti_link[update.effective_chat.id] else 'OFF'}"
    )


async def check_links(update, context):
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
                try:
                    await update.message.delete()
                except Exception:
                    pass
                await update.effective_chat.send_message(
                    f"💗 {mention(update.effective_user)}\n"
                    f"ʟɪɴᴋꜱ ʙʜᴇᴊɴᴇ ᴋɪ ᴘᴇʀᴍɪꜱꜱɪᴏɴ ɴᴀʜɪ ʜᴀɪ",
                    parse_mode=ParseMode.HTML,
                )
                return


@admin_only
async def addword_cmd(update, context):
    if not context.args:
        await update.message.reply_text("Usage: /addword [word]")
        return
    word = " ".join(context.args).lower()
    if word not in banned_words[update.effective_chat.id]:
        banned_words[update.effective_chat.id].append(word)
    await update.message.reply_text(f"Added banned word: {word}")


@admin_only
async def rmword_cmd(update, context):
    if not context.args:
        await update.message.reply_text("Usage: /rmword [word]")
        return
    word = " ".join(context.args).lower()
    chat_id = update.effective_chat.id
    if word in banned_words[chat_id]:
        banned_words[chat_id].remove(word)
        await update.message.reply_text(f"Removed banned word: {word}")
    else:
        await update.message.reply_text("Word not found.")


async def wordlist_cmd(update, context):
    words = banned_words.get(update.effective_chat.id, [])
    await update.message.reply_text(
        "💙 <b>ʙᴀɴɴᴇᴅ ᴡᴏʀᴅꜱ:</b>\n" +
        ("\n".join(f"• {w}" for w in words) if words else "None"),
        parse_mode=ParseMode.HTML,
    )


async def check_banned_words(update, context):
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
            try:
                await update.message.delete()
            except Exception:
                pass
            return


@admin_only
async def save_note(update, context):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /save [name] [text]")
        return
    name = context.args[0].lower()
    notes_db[update.effective_chat.id][name] = " ".join(context.args[1:])
    await update.message.reply_text(f"Note '{name}' saved.")


async def get_note(update, context):
    if not context.args:
        await update.message.reply_text("Usage: /get [name]")
        return
    name = context.args[0].lower()
    note = notes_db.get(update.effective_chat.id, {}).get(name)
    await update.message.reply_text(
        note if note else f"Note '{name}' not found.",
        parse_mode=ParseMode.HTML,
    )


async def notes_list(update, context):
    notes = notes_db.get(update.effective_chat.id, {})
    await update.message.reply_text(
        "💓 <b>Notes:</b>\n" +
        ("\n".join(f"• <code>{n}</code>" for n in notes) if notes else "None"),
        parse_mode=ParseMode.HTML,
    )


@admin_only
async def clear_note(update, context):
    if not context.args:
        await update.message.reply_text("Usage: /clear [name]")
        return
    name = context.args[0].lower()
    if name in notes_db.get(update.effective_chat.id, {}):
        del notes_db[update.effective_chat.id][name]
        await update.message.reply_text(f"Note '{name}' deleted.")
    else:
        await update.message.reply_text("Note not found.")


@admin_only
async def clearall_notes(update, context):
    notes_db[update.effective_chat.id] = {}
    await update.message.reply_text("All notes deleted.")


async def hashtag_notes(update, context):
    if not update.message or not update.message.text:
        return
    text = update.message.text
    if text.startswith("#"):
        name = text[1:].lower().split()[0]
        note = notes_db.get(update.effective_chat.id, {}).get(name)
        if note:
            await update.message.reply_text(note, parse_mode=ParseMode.HTML)


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


@admin_only
async def lock_cmd(update, context):
    if not context.args or context.args[0].lower() not in LOCK_TYPES:
        await update.message.reply_text(
            "Usage: /lock [type]\nTypes: " + ", ".join(LOCK_TYPES)
        )
        return
    lock_type = context.args[0].lower()
    chat = await context.bot.get_chat(update.effective_chat.id)
    current = chat.permissions.to_dict() if chat.permissions else {}
    current.update(LOCK_TYPES[lock_type])
    await context.bot.set_chat_permissions(
        update.effective_chat.id, ChatPermissions(**current)
    )
    await update.message.reply_text(f"🔒 {lock_type} locked.")


@admin_only
async def unlock_cmd(update, context):
    if not context.args:
        await update.message.reply_text("Usage: /unlock [type]")
        return
    lock_type = context.args[0].lower()
    if lock_type not in LOCK_TYPES:
        await update.message.reply_text("Invalid lock type.")
        return
    chat = await context.bot.get_chat(update.effective_chat.id)
    current = chat.permissions.to_dict() if chat.permissions else {}
    current.update({key: True for key in LOCK_TYPES[lock_type]})
    await context.bot.set_chat_permissions(
        update.effective_chat.id, ChatPermissions(**current)
    )
    await update.message.reply_text(f"🔓 {lock_type} unlocked.")


async def id_cmd(update, context):
    text = (
        f"❣️ {mention(update.effective_user)}\n"
        f"❤️ ᴛᴇʀᴀ ɪᴅ: <code>{update.effective_user.id}</code>\n"
    )
    if update.effective_chat.type != "private":
        text += f"🩷 ᴄʜᴀᴛ ɪᴅ: <code>{update.effective_chat.id}</code>"
    if update.message.reply_to_message:
        text += (
            f"\n🧡 ʀᴇᴘʟɪᴇᴅ ᴜꜱᴇʀ ɪᴅ: "
            f"<code>{update.message.reply_to_message.from_user.id}</code>"
        )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def info_cmd(update, context):
    target = await get_target_user(update, context) or update.effective_user
    text = (
        f"💛 <b>ᴜꜱᴇʀ ɪɴꜰᴏ</b>\n\n"
        f"💚 ɪᴅ: <code>{target.id}</code>\n"
        f"💙 ɴᴀᴍᴇ: {target.full_name}\n"
        f"💜 ᴜꜱᴇʀɴᴀᴍᴇ: @{target.username or 'N/A'}\n"
        f"🤍 ʙᴏᴛ: {'ʏᴇꜱ' if target.is_bot else 'ɴᴏ'}\n"
    )
    if update.effective_chat.type != "private":
        member = await safe_get_member(
            update.effective_chat.id, target.id, context.bot
        )
        if member:
            text += f"🖤 ꜱᴛᴀᴛᴜꜱ: {member.status}\n"
        warns = warnings_db[update.effective_chat.id][target.id]
        text += f"🩵 ᴡᴀʀɴɪɴɢꜱ: {warns}/{MAX_WARNINGS}\n"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def admins_cmd(update, context):
    admins = await context.bot.get_chat_administrators(update.effective_chat.id)
    text = f"💖 <b>{update.effective_chat.title} ᴋᴇ ᴀᴅᴍɪɴꜱ</b>\n\n"
    for admin in admins:
        emoji = "💗" if admin.status == ChatMemberStatus.OWNER else "💕"
        text += f"{emoji} {admin.user.full_name}"
        if admin.custom_title:
            text += f" ─ {admin.custom_title}"
        text += "\n"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


@admin_only
async def setrules_cmd(update, context):
    if not context.args:
        await update.message.reply_text("Usage: /setrules [text]")
        return
    rules_db[update.effective_chat.id] = " ".join(context.args)
    await update.message.reply_text("Rules saved.")


async def rules_cmd(update, context):
    rules = rules_db.get(
        update.effective_chat.id,
        "ᴋᴏɪ ʀᴜʟᴇꜱ ꜱᴇᴛ ɴᴀʜɪ ʜᴀɪɴ. ᴀᴅᴍɪɴ /setrules ᴜꜱᴇ ᴋᴀʀᴇ."
    )
    await update.message.reply_text(
        f"❣️ <b>ɢʀᴏᴜᴘ ʀᴜʟᴇꜱ:</b>\n\n{rules}",
        parse_mode=ParseMode.HTML,
    )


@admin_only
async def setlog_cmd(update, context):
    if not context.args:
        await update.message.reply_text("Usage: /setlog [channel_id]")
        return
    try:
        log_channel[update.effective_chat.id] = int(context.args[0])
        await update.message.reply_text("Log channel saved.")
    except ValueError:
        await update.message.reply_text("Invalid channel ID.")


@admin_only
async def unsetlog_cmd(update, context):
    log_channel.pop(update.effective_chat.id, None)
    await update.message.reply_text("Log channel removed.")


async def settings_cmd(update, context):
    chat_id = update.effective_chat.id
    flood = antiflood_settings.get(chat_id)
    flood_text = (
        f"{flood['max_msgs']} msgs / {flood['time_window']}s"
        if flood else "OFF"
    )
    text = (
        "💕 <b>GROUP SETTINGS</b>\n\n"
        f"💝 Anti-flood: {flood_text}\n"
        f"💘 Anti-link: {'ON' if anti_link.get(chat_id) else 'OFF'}\n"
        f"💞 Banned words: {len(banned_words.get(chat_id, []))}\n"
        f"💓 Notes: {len(notes_db.get(chat_id, {}))}\n"
        f"❣️ Log channel: {log_channel.get(chat_id, 'NOT SET')}\n"
        f"❤️ Welcome: {'CUSTOM' if chat_id in welcome_messages else 'DEFAULT'}\n"
        f"🩷 Goodbye: {'CUSTOM' if chat_id in goodbye_messages else 'DEFAULT'}"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def track_groups(update, context):
    if (
        update.message
        and update.effective_chat
        and update.effective_chat.type in ("group", "supergroup")
    ):
        active_groups.add(update.effective_chat.id)


async def broadcast_cmd(update, context):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 Owner only.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast [message]")
        return
    msg = " ".join(context.args)
    broadcast_text = (
        f"💙 <b>ʙʀᴏᴀᴅᴄᴀꜱᴛ ꜰʀᴏᴍ ᴏᴡɴᴇʀ</b> 💜\n\n"
        f"<i>{msg}</i>\n\n"
        f"🤍 @Teamapst"
    )
    success, fail = 0, 0
    for gid in list(active_groups):
        try:
            await context.bot.send_message(
                gid, broadcast_text, parse_mode=ParseMode.HTML
            )
            success += 1
        except Exception:
            active_groups.discard(gid)
            fail += 1
    await update.message.reply_text(
        f"🖤 Broadcast done.\n\n💖 Success: {success}\n💗 Failed: {fail}"
    )


async def time_cmd(update, context):
    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    body = (
        f"  🩷 ᴛɪᴍᴇ: <code>{now.strftime('%I:%M:%S %p')}</code>\n"
        f"  🧡 ᴅᴀᴛᴇ: <code>{now.strftime('%d %B %Y')}</code>\n"
        f"  💛 ᴅᴀʏ: <code>{now.strftime('%A')}</code>\n"
        f"  💚 ᴢᴏɴᴇ: <code>IST (UTC+5:30)</code>"
    )
    await update.message.reply_text(
        box("🇮🇳 ɪɴᴅɪᴀ ᴛɪᴍᴇ", body, "💜", "🩵"),
        parse_mode=ParseMode.HTML,
    )


async def stats_cmd(update, context):
    bot_info = await context.bot.get_me()
    uptime = datetime.now() - BOT_START_TIME
    total_seconds = int(uptime.total_seconds())
    days, rem = divmod(total_seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    body = (
        f"  💖 ɴᴀᴍᴇ: <b>{bot_info.full_name}</b>\n"
        f"  💗 ᴜꜱᴇʀɴᴀᴍᴇ: @{bot_info.username}\n"
        f"  💕 ɪᴅ: <code>{bot_info.id}</code>\n"
        f"  💝 ᴘʏᴛʜᴏɴ: <code>{platform.python_version()}</code>\n"
        f"  💘 ᴜᴘᴛɪᴍᴇ: <code>{days}d {hours}h {minutes}m {seconds}s</code>\n"
        f"  💞 ɢʀᴏᴜᴘꜱ: <code>{len(active_groups)}</code>\n"
        f"  💓 ᴡᴀʀɴɪɴɢꜱ: <code>{sum(sum(v.values()) for v in warnings_db.values())}</code>\n"
        f"  ❣️ ɴᴏᴛᴇꜱ: <code>{sum(len(v) for v in notes_db.values())}</code>\n"
        f"  ❤️ ʙᴀɴɴᴇᴅ ᴡᴏʀᴅꜱ: <code>{sum(len(v) for v in banned_words.values())}</code>"
    )
    await update.message.reply_text(
        box("ʙᴏᴛ ꜱᴛᴀᴛꜱ", body, "🧡", "💛"),
        parse_mode=ParseMode.HTML,
    )


async def roast_cmd(update, context):
    target = await get_target_user(update, context) or update.effective_user
    roast = random.choice([
        "ᴛᴜ ɪᴛɴᴀ ꜱʟᴏᴡ ʜᴀɪ, ᴛᴇʀᴀ ɪɴᴛᴇʀɴᴇᴛ ʙʜɪ ᴛᴜᴊʜꜱᴇ ᴛᴇᴢ ʜᴀɪ",
        "ᴛᴜ ɢᴏᴏɢʟᴇ ᴘᴇ ꜱᴇᴀʀᴄʜ ᴋᴀʀ 'ᴍᴀɪɴ ᴋʏᴜ ᴀɪꜱᴀ ʜᴜ'",
        "ᴛᴜ ɪᴛɴᴀ ʙᴏʀɪɴɢ ʜᴀɪ, ᴛᴇʀᴀ ᴀʟᴀʀᴍ ʙʜɪ ɴᴀʜɪ ʙᴀᴊᴛᴀ",
    ])
    await update.message.reply_text(
        box(
            "ʀᴏᴀꜱᴛ 🔥",
            f"  🔥 ᴛᴀʀɢᴇᴛ: {mention(target)}\n"
            f"  💀 <i>\"{roast}\"</i>",
            "🖤", "💜",
        ),
        parse_mode=ParseMode.HTML,
    )


async def love_cmd(update, context):
    target = await get_target_user(update, context)
    if not target:
        await update.message.reply_text("Reply to a user or provide a user ID.")
        return
    percentage = random.randint(1, 100)
    hearts = "❤️" * (percentage // 10) + "🤍" * (10 - percentage // 10)
    await update.message.reply_text(
        box(
            "ʟᴏᴠᴇ ᴍᴇᴛᴇʀ 💕",
            f"  💘 {mention(update.effective_user)} & {mention(target)}\n"
            f"  💕 ʟᴏᴠᴇ: <b>{percentage}%</b>\n  {hearts}",
            "💖", "💗",
        ),
        parse_mode=ParseMode.HTML,
    )


async def quote_cmd(update, context):
    q = random.choice([
        "ᴘʏᴀᴀʀ ᴡᴏ ᴄʜᴇᴇᴢ ʜᴀɪ ᴊᴏ ᴡɪꜰɪ ꜱᴇ ʙʜɪ ᴢᴀʀᴜʀɪ ʜᴀɪ",
        "ᴅɪʟ ᴛᴏᴅɴᴀ ᴍᴀᴛ, ᴍᴇʀᴇ ᴘᴀᴀꜱ ᴡᴀʀʀᴀɴᴛʏ ɴᴀʜɪ ʜᴀɪ",
        "ᴛᴜᴍꜱᴇ ᴍɪʟᴋᴀʀ ᴅɪʟ ᴋᴀ ꜱᴛᴏʀᴀɢᴇ ꜰᴜʟʟ ʜᴏ ɢᴀʏᴀ",
    ])
    await update.message.reply_text(
        box(
            "ʟᴏᴠᴇ ǫᴜᴏᴛᴇ 💌",
            f"  💌 {mention(update.effective_user)}\n  💝 <i>\"{q}\"</i>",
            "💖", "💗",
        ),
        parse_mode=ParseMode.HTML,
    )


async def truth_cmd(update, context):
    target = await get_target_user(update, context) or update.effective_user
    q = random.choice([
        "ᴛᴜɴᴇ ᴀᴀᴊ ᴛᴀᴋ ᴋɪꜱᴋᴏ ꜱᴀʙꜱᴇ ʙᴀᴅᴀ ᴊʜᴏᴏᴛ ʙᴏʟᴀ?",
        "ᴛᴇʀᴀ ꜱᴀʙꜱᴇ ᴇᴍʙᴀʀᴀꜱꜱɪɴɢ ᴍᴏᴍᴇɴᴛ ᴋʏᴀ ᴛʜᴀ?",
        "ᴛᴜ ᴋɪꜱᴋᴏ ꜱᴇᴄʀᴇᴛʟʏ ꜱᴛᴀʟᴋ ᴋᴀʀᴛᴀ ʜᴀɪ?",
    ])
    await update.message.reply_text(
        box(
            "ᴛʀᴜᴛʜ 🎯",
            f"  🎯 ᴛᴀʀɢᴇᴛ: {mention(target)}\n  💬 <i>\"{q}\"</i>",
            "💚", "💙",
        ),
        parse_mode=ParseMode.HTML,
    )


async def dare_cmd(update, context):
    target = await get_target_user(update, context) or update.effective_user
    d = random.choice([
        "ᴀᴘɴɪ ʟᴀꜱᴛ ꜱᴇʟꜰɪᴇ ɢʀᴏᴜᴘ ᴍᴇɪɴ ʙʜᴇᴊᴏ",
        "ᴀɢʟᴇ 5 ᴍɪɴᴜᴛᴇ ꜱɪʀꜰ ᴇᴍᴏᴊɪ ᴍᴇɪɴ ʙᴀᴀᴛ ᴋᴀʀᴏ",
        "ᴀᴘɴᴇ ᴄʀᴜꜱʜ ᴋᴀ ꜰɪʀꜱᴛ ɴᴀᴍᴇ ʙᴀᴛᴀᴏ",
        "10 ᴘᴜꜱʜᴜᴘꜱ ᴋᴀʀᴏ",
    ])
    await update.message.reply_text(
        box(
            "ᴅᴀʀᴇ ⚡",
            f"  ⚡ ᴛᴀʀɢᴇᴛ: {mention(target)}\n  🎲 <i>\"{d}\"</i>",
            "🧡", "💛",
        ),
        parse_mode=ParseMode.HTML,
    )


async def decide_cmd(update, context):
    answers = [
        ("ʜᴀᴀɴ ʙɪʟᴋᴜʟ! 💚", "✅"),
        ("ɴᴀ ʙʜᴀɪ ɴᴀ! 🖤", "❌"),
        ("ꜱʜᴀᴀʏᴀᴅ... 💛", "🤔"),
        ("1000% ʜᴀᴀɴ! 💖", "💯"),
        ("ʙɪʟᴋᴜʟ ɴᴀʜɪ! 💜", "🚫"),
    ]
    ans, emoji = random.choice(answers)
    question = " ".join(context.args) if context.args else "ᴋᴏɪ ꜱᴀᴡᴀᴀʟ ɴᴀʜɪ"
    await update.message.reply_text(
        box(
            "ꜰᴀɪꜱʟᴀ 🎱",
            f"  ❓ ꜱᴀᴡᴀᴀʟ: <i>\"{question}\"</i>\n"
            f"  {emoji} ᴊᴀᴡᴀᴀʙ: <b>{ans}</b>\n"
            f"  💕 ᴘᴜᴄʜɴᴇ ᴡᴀʟᴀ: {mention(update.effective_user)}",
            "💝", "💞",
        ),
        parse_mode=ParseMode.HTML,
    )


async def owner_cmd(update, context):
    await update.message.reply_text(
        f"💕 {mention(update.effective_user)}\n"
        f"💝 <b>ʙᴏᴛ ᴏᴡɴᴇʀ:</b> @Teamapst",
        parse_mode=ParseMode.HTML,
    )


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    commands = {
        "start": start_cmd, "help": help_cmd, "owner": owner_cmd,
        "broadcast": broadcast_cmd, "time": time_cmd, "stats": stats_cmd,
        "roast": roast_cmd, "love": love_cmd, "quote": quote_cmd,
        "truth": truth_cmd, "dare": dare_cmd, "decide": decide_cmd,
        "ban": ban_cmd, "unban": unban_cmd, "kick": kick_cmd,
        "mute": mute_cmd, "unmute": unmute_cmd, "tmute": tmute_cmd,
        "tban": tban_cmd, "warn": warn_cmd, "unwarn": unwarn_cmd,
        "warns": warns_cmd, "resetwarns": resetwarns_cmd,
        "promote": promote_cmd, "demote": demote_cmd, "pin": pin_cmd,
        "unpin": unpin_cmd, "unpinall": unpinall_cmd, "purge": purge_cmd,
        "del": del_cmd, "setwelcome": set_welcome, "setgoodbye": set_goodbye,
        "resetwelcome": reset_welcome, "resetgoodbye": reset_goodbye,
        "antiflood": antiflood_cmd, "antifloodoff": antiflood_off,
        "antilink": antilink_cmd, "addword": addword_cmd, "rmword": rmword_cmd,
        "wordlist": wordlist_cmd, "save": save_note, "get": get_note,
        "notes": notes_list, "clear": clear_note, "clearall": clearall_notes,
        "lock": lock_cmd, "unlock": unlock_cmd, "id": id_cmd, "info": info_cmd,
        "admins": admins_cmd, "setrules": setrules_cmd, "rules": rules_cmd,
        "setlog": setlog_cmd, "unsetlog": unsetlog_cmd, "settings": settings_cmd,
    }

    for name, handler in commands.items():
        app.add_handler(CommandHandler(name, handler))

    app.add_handler(CallbackQueryHandler(help_callback, pattern=r"^help_"))
    app.add_handler(ChatMemberHandler(greet_member, ChatMemberHandler.CHAT_MEMBER))

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r"^#"), hashtag_notes)
    )
    app.add_handler(
        MessageHandler(filters.ALL & ~filters.COMMAND, check_flood), group=1
    )
    app.add_handler(
        MessageHandler(
            filters.Entity("url") | filters.Entity("text_link"),
            check_links,
        ),
        group=2,
    )
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, check_banned_words),
        group=3,
    )
    app.add_handler(
        MessageHandler(filters.ALL, track_groups),
        group=4,
    )

    print("💎 Bot started! Press Ctrl+C to stop.")
    print("💠 Owner ID:", OWNER_ID)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

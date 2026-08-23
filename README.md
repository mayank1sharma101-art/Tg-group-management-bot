# 💎 Infinity Premium Group Manager Bot

A feature-rich Telegram group management bot built with Python and `python-telegram-bot`.

## ✨ Features

- Ban / unban / kick
- Mute / unmute / temporary mute
- Temporary bans
- Warning system
- Promote / demote
- Pin / unpin / purge
- Welcome & goodbye messages
- Anti-flood protection
- Anti-link protection
- Banned-word filter
- Notes system
- Group permission locks
- Rules and group settings
- Log channel support
- Owner broadcast
- Bot statistics
- Utility and fun commands

## ⚙️ Requirements

- Python 3.9+
- Telegram bot token
- Bot must be an administrator in the target group
- Appropriate Telegram admin permissions

## 🚀 Installation

```bash
git clone https://github.com/mayank1sharma101-art/Tg-group-management-bot.git
cd Tg-group-management-bot

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

On Windows:

```bash
venv\Scripts\activate
```

## 🔐 Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Set:

```text
BOT_TOKEN=your_bot_token
OWNER_ID=your_numeric_telegram_id
```

For Linux/macOS:

```bash
export BOT_TOKEN="your_bot_token"
export OWNER_ID="123456789"
python bot.py
```

For production, configure environment variables through your hosting provider rather than committing `.env`.

## 🤖 Main Commands

### Administration

`/ban` `/unban` `/kick` `/mute` `/unmute`

`/tmute 1h` `/tban 1d`

`/warn` `/unwarn` `/warns` `/resetwarns`

`/promote` `/demote`

`/pin` `/unpin` `/unpinall` `/purge` `/del`

### Protection

`/antiflood 5`

`/antifloodoff`

`/antilink on`

`/antilink off`

`/addword word`

`/rmword word`

`/wordlist`

### Welcome

`/setwelcome [message]`

`/setgoodbye [message]`

`/resetwelcome`

`/resetgoodbye`

Supported variables:

```text
{first}
{last}
{fullname}
{username}
{id}
{chatname}
{count}
```

### Notes

`/save name text`

`/get name`

`#name`

`/notes`

`/clear name`

`/clearall`

### Settings

`/lock type`

`/unlock type`

`/id`

`/info`

`/admins`

`/setrules text`

`/rules`

`/setlog channel_id`

`/unsetlog`

`/settings`

### Utility

`/start`

`/help`

`/owner`

`/stats`

`/time`

`/broadcast message`

## ⚠️ Important

This project currently uses **in-memory storage**. Settings, warnings, notes, filters and tracked groups are lost when the bot restarts.

For a serious production deployment, replace the in-memory dictionaries with persistent storage such as SQLite or another database.

The bot also requires suitable Telegram administrator permissions to perform moderation actions.

## 👤 Credits

**Developed by Mayank Sharma**

Original developer credit must remain in the repository and source code.

You may fork and modify this project, but do not present the original work as your own or remove the original attribution.

## 📜 License

See [`LICENSE`](LICENSE).

## 🐛 Bug Reports

Open a GitHub Issue and include:

- Command that caused the issue
- Error message
- Python version
- Deployment platform
- Relevant logs
- Steps to reproduce

## ⭐ Support

If the project is useful to you, consider starring the repository.

---

© 2026 Mayank Sharma. All Rights Reserved.

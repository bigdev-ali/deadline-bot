# Deadline Bot

A Discord bot that tracks your deadlines and DMs you before they're due. Add a deadline with a slash command, and the bot reminds you automatically at 24 hours, 3 hours and 1 hour before it's due.

Built as a one-week project to practice async Python, SQL and scheduled background tasks.

## Features

- **Slash commands** to add, list, finish and delete deadlines
- **Automatic reminders** by DM at 24h, 3h and 1h before the due time, color-coded by urgency (green, orange, red)
- **Persistent storage** with SQLite, so deadlines survive restarts
- **Per-user data**: you can only see and change your own deadlines
- **Input validation**: bad date formats and dates in the past are rejected with a friendly message
- **Central error handling and logging**, so users never see raw errors and failures are easy to debug

## Commands

| Command | What it does |
|---|---|
| `/add title due` | Save a deadline. `due` format: `YYYY-MM-DD HH:MM` (Pakistan time) |
| `/list` | Show your unfinished deadlines, soonest first |
| `/done id` | Mark a deadline as finished |
| `/delete id` | Delete a deadline |
| `/ping` | Check that the bot is alive |

## Tech stack

- **Python** with [discord.py](https://discordpy.readthedocs.io/) (slash commands, embeds, background tasks)
- **SQLite** via `aiosqlite` for async database access
- **python-dotenv** for keeping the bot token out of the code
- **zoneinfo / tzdata** for timezone handling

## How it works

- **Commands** are event-driven. The bot runs code when someone uses a slash command.
- **Reminders** are schedule-driven. A background task wakes up every minute, finds unfinished deadlines inside a reminder window, sends a DM, and records it in the database so the same reminder is never sent twice.
- **Time handling:** deadlines are typed in local time, converted to UTC for storage, and shown with Discord's timestamp format, so each viewer sees them in their own timezone.
- **Safety:** all SQL uses placeholders (no string-built queries), and every update or delete is scoped to the user who owns the row.

## Project structure

```
deadline-bot/
├── bot.py            # startup, logging, error handler, /ping, /add, /list, /done, /delete, reminder loop
├── database.py       # all SQL lives here
├── requirements.txt  # dependencies
├── .env.example      # template for the bot token
└── docs/             # screenshots
```

## Setup

1. **Create a bot** in the [Discord Developer Portal](https://discord.com/developers/applications). Copy its token from the Bot tab.
2. **Invite it** to a server using OAuth2 → URL Generator, with the scopes `bot` and `applications.commands` and the **Send Messages** permission.
3. **Clone the repo and create a virtual environment:**
   ```bash
   git clone https://github.com/bigdev-ali/deadline-bot.git
   cd deadline-bot
   python -m venv venv
   ```
   Activate it: `source venv/bin/activate` on macOS/Linux, or `venv\Scripts\activate` on Windows.
4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
5. **Add your token.** Copy `.env.example` to `.env` and replace the placeholder with your real token.
6. **Run it:**
   ```bash
   python bot.py
   ```

Reminders are sent by DM, so you need to share a server with the bot and allow DMs from server members.

## What went wrong along the way

- **Windows activation path:** the virtual environment's activate script wasn't where the usual instructions say, so I had to find the real path in the `venv` folder.
- **A function name typo** (`get_deadline` vs `get_deadlines`) crashed `/list`. The traceback's last line pointed straight at it.
- **A malformed SQL query** raised an `OperationalError`. Reading the failing query closely, line by line, found it.
- **`requirements.txt` saved as UTF-16** by PowerShell's `>` redirect, which `pip` can't read. Re-saving as UTF-8 fixed it.
- **The first `/ping` timed out** with "application did not respond" and worked on the next try, since Discord only allows 3 seconds for the first reply.

## Limitations

- **Runs locally.** The bot only sends reminders while `bot.py` is running. It isn't hosted yet.
- **One timezone.** Input is assumed to be Pakistan time. A per-user timezone setting would fix this.
- **Reminders are DMs only,** and users with DMs closed won't receive them.

## Future improvements

- Deploy to a hosting platform so reminders run 24/7
- Containerize with Docker
- Split commands and the reminder loop into separate cogs
- Per-user timezone setting
- Snooze and edit commands

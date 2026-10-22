import asyncio
import logging
import os

from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

# ============================================================
# Sukuna X Music Radio
# Environment variables required:
# API_ID, API_HASH, BOT_TOKEN (or STRING_SESSION), OWNER_ID
# STREAM_URL is required for /radio
# CHANNEL_USERNAME is required for /channelpost
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("sukuna-x-music")


def env_int(name: str, default: int = 0) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


API_ID = 31862898
API_HASH = "c0e5fa94ba15a7d8fd4a883c21db2afe"
BOT_TOKEN = "8781475628:AAFhetyDEYXHod7RVnalPN8SCVhCjKEp9gg"
STRING_SESSION = "BQHmMHIAV8Htpyl8gXYIMbE8o0TGdvRaEEfBNLaCUfNPkpE_8b5xonEjOr2XEUNVWjEjCZvjBkgA6vkpR8ONrEt8BH33N6Ukz3uGcEo1YLEmnrUZ6_7elxNeQ3t5R2UPO4VZ1nBEMoIinKMcnWwv04UTvWmSS3DZhqStLzCmt-4IFb1JSELXm9HqdR8V2X6iUnLfThF4ZWhGLyOq7HdALSu3BEji-l5tSZhzhCWyC49pHSaN4d4WuYMWff4ktjXin7NuVdL9fXBrYGFHA9DdpzgGAFsWQn9yg5VlB3dyf1trfqS75ckwXLqPWQ2jow85ynpEVJyOI0M-UOzB1vQ4c5zA_GoCZgAAAAILnKT9AA"
OWNER_ID = 8734813395
STREAM_URL = "https://eu8.fastcast4u.com/proxy/clyedupq/stream"
CHANNEL_USERNAME = "Sukuna X Music"
CHANNEL_LINK = "https://t.me/youcanplaymusicbyurchoice"
PORT = env_int("PORT", 10000)

if not API_ID or not API_HASH:
    raise RuntimeError("Please set API_ID and API_HASH in your hosting environment.")

if STRING_SESSION:
    app = Client(
        "sukuna_radio",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=STRING_SESSION,
    )
elif BOT_TOKEN:
    app = Client(
        "sukuna_radio_bot",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
    )
else:
    raise RuntimeError("Set BOT_TOKEN or STRING_SESSION in your hosting environment.")

calls = PyTgCalls(app)


async def health_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """Tiny HTTP endpoint so Render Web Services detect an open port."""
    try:
        # Read the request line and headers; the endpoint only reports health.
        await asyncio.wait_for(reader.readline(), timeout=5)
        while True:
            line = await asyncio.wait_for(reader.readline(), timeout=5)
            if line in (b"\r\n", b"\n", b""):
                break
        body = b"Sukuna X Music Radio is running"
        response = (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: text/plain; charset=utf-8\r\n"
            + f"Content-Length: {len(body)}\r\n".encode()
            + b"Connection: close\r\n\r\n"
            + body
        )
        writer.write(response)
        await writer.drain()
    except (asyncio.TimeoutError, ConnectionError):
        pass
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except ConnectionError:
            pass



@app.on_message(filters.command(["start", "help"]) & filters.private)
async def start_command(_, message: Message):
    await message.reply_text(
        "🎧 **Sukuna X Music Radio**\n\n"
        "Add the account to your group and start a voice chat first.\n\n"
        "🎵 `/radio` — start the configured audio stream in a group\n"
        "⏹️ `/stopradio` — stop the stream\n"
        "📘 `/radiohelp` — show radio help\n"
        "📢 `/channelpost Your message` — post a message to your configured channel "
        "(owner only)\n\n"
        "Configure STREAM_URL and CHANNEL_USERNAME in your hosting environment."
    )


@app.on_message(filters.command(["radiohelp", "help_radio"]))
async def radio_help(_, message: Message):
    await message.reply_text(
        "🎵 **Radio commands**\n"
        "`/radio` — start the stream in this group\n"
        "`/stopradio` — stop the stream\n\n"
        "Start a voice chat in the group before using `/radio`. "
        "STREAM_URL must be a direct, reachable audio-stream URL that you have "
        "permission to rebroadcast."
    )


@app.on_message(filters.command("radio") & filters.group)
async def radio_command(_, message: Message):
    if not STREAM_URL:
        await message.reply_text("⚠️ Set the STREAM_URL environment variable first.")
        return

    try:
        await calls.play(message.chat.id, MediaStream(STREAM_URL))
        await message.reply_text("📻 Radio stream started.")
    except Exception as exc:
        log.exception("Could not start radio stream")
        await message.reply_text(
            "❌ Couldn't start the radio. Check that a voice chat is active, "
            "the stream URL is directly playable, and the account has permission "
            "to join.\n"
            f"Error: `{type(exc).__name__}: {exc}`"
        )


@app.on_message(filters.command("stopradio") & filters.group)
async def stop_radio(_, message: Message):
    try:
        await calls.leave_call(message.chat.id)
        await message.reply_text("⏹️ Radio stopped.")
    except Exception as exc:
        log.exception("Could not stop radio")
        await message.reply_text(
            f"⚠️ No active stream was found, or stopping failed: "
            f"`{type(exc).__name__}: {exc}`"
        )


@app.on_message(filters.command("channelpost") & filters.private)
async def channel_post(_, message: Message):
    # Only the configured owner can post through this command.
    if not OWNER_ID or not message.from_user or message.from_user.id != OWNER_ID:
        await message.reply_text("⛔ You are not authorized to use this command.")
        return

    if not CHANNEL_USERNAME:
        await message.reply_text(
            "⚠️ Set CHANNEL_USERNAME in your hosting environment, for example @MyChannel."
        )
        return

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.reply_text(
            "Usage:\n/channelpost Your message here"
        )
        return

    try:
        await app.send_message(CHANNEL_USERNAME, parts[1].strip())
        await message.reply_text("✅ Message posted to your channel.")
    except Exception as exc:
        log.exception("Channel post failed")
        await message.reply_text(
            "❌ Could not post. Make sure the bot is an admin in the channel "
            "with permission to post messages.\n"
            f"Error: `{type(exc).__name__}: {exc}`"
        )


async def main():
    # Render Web Services require an HTTP port bound to 0.0.0.0.
    # Start this before Telegram so Render can detect the port promptly.
    http_server = await asyncio.start_server(health_handler, "0.0.0.0", PORT)
    log.info("Health server listening on 0.0.0.0:%s", PORT)

    try:
        await app.start()
        await calls.start()
        log.info("Sukuna X Music is online.")
        # Keep the process running for Render/Railway.
        await asyncio.Event().wait()
    finally:
        http_server.close()
        await http_server.wait_closed()
        try:
            await calls.stop()
        except Exception:
            log.exception("Error while stopping PyTgCalls")
        try:
            await app.stop()
        except Exception:
            log.exception("Error while stopping Pyrogram")


if __name__ == "__main__":
    asyncio.run(main())

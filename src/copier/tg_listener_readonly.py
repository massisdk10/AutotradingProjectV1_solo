import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from telethon import TelegramClient, events

# --- Hard safety rules (project-critical) ---
# This script MUST NEVER send messages, forward, react, or join anything.
# It only listens and writes local logs.

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_ROOT / "logs" / "copier"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "tg_readonly.log"

def log_line(text: str) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"{ts} {text}\n")

def must_get_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v

def main() -> int:
    # IMPORTANT: We intentionally do NOT auto-load .env here.
    # You will export env vars manually in terminal (next micro-step) to avoid leaks.
    api_id = int(must_get_env("TG_API_ID"))
    api_hash = must_get_env("TG_API_HASH")

    # Session file will be created locally; gitignore already covers *.session*
    session_path = str(PROJECT_ROOT / "config" / "keystore" / "tg_readonly")

    client = TelegramClient(session_path, api_id, api_hash)

    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        try:
            chat = await event.get_chat()
            chat_title = getattr(chat, "title", None) or getattr(chat, "username", None) or str(getattr(chat, "id", "unknown"))
            sender = await event.get_sender()
            sender_name = getattr(sender, "username", None) or getattr(sender, "first_name", None) or str(getattr(sender, "id", "unknown"))

            msg_id = event.message.id
            text = event.message.message or ""

            # Log raw receipt (no transformation)
            log_line(f"[CHAT={chat_title}] [SENDER={sender_name}] [MSG_ID={msg_id}] {text.replace(chr(10), ' / ')}")

        except Exception as e:
            log_line(f"[ERROR] {type(e).__name__}: {e}")

    log_line("[START] tg_listener_readonly starting (no send/forward/reply).")
    client.start()  # login may be required on first run
    log_line("[RUNNING] waiting for new messages...")
    client.run_until_disconnected()
    log_line("[STOP] disconnected.")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        log_line("[STOP] KeyboardInterrupt")
        raise
    except Exception as e:
        # print to stderr WITHOUT secrets
        print(f"Fatal: {type(e).__name__}: {e}", file=sys.stderr)
        raise


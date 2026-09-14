import os
from datetime import datetime
from telethon import TelegramClient
from telethon.sessions import StringSession

LOG_PATH = "logs/copier/tg_chat_scan.log"

def log_line(s: str) -> None:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(s + "\n")

def main() -> None:
    # Read-only scan: no sending, no joining, no manual "mark read"
    api_id = os.getenv("TG_API_ID", "").strip()
    api_hash = os.getenv("TG_API_HASH", "").strip()
    session_str = os.getenv("TG_SESSION", "").strip()

    if not api_id.isdigit():
        raise SystemExit("ERROR: TG_API_ID missing or not digits.")
    if len(api_hash) < 20:
        raise SystemExit("ERROR: TG_API_HASH missing or too short.")
    if len(session_str) < 20:
        raise SystemExit("ERROR: TG_SESSION missing or too short.")

    ts = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    log_line(f"\n===== TG CHAT SCAN START {ts} =====")

    client = TelegramClient(StringSession(session_str), int(api_id), api_hash)

    async def runner():
        await client.connect()
        if not await client.is_user_authorized():
            raise SystemExit("ERROR: Session not authorized. Stop here (no re-auth in this step).")

        count = 0
        async for dialog in client.iter_dialogs():
            ent = dialog.entity

            chat_id = getattr(ent, "id", None)
            title = getattr(ent, "title", None) or getattr(ent, "first_name", None) or "UNKNOWN"
            username = getattr(ent, "username", None)
            access_hash = getattr(ent, "access_hash", None)

            cls = ent.__class__.__name__
            broadcast = getattr(ent, "broadcast", None)
            megagroup = getattr(ent, "megagroup", None)

            log_line("[CHAT]")
            log_line(f"  id: {chat_id}")
            log_line(f"  title: {title}")
            log_line(f"  username: {username}")
            log_line(f"  entity_class: {cls}")
            log_line(f"  broadcast: {broadcast}")
            log_line(f"  megagroup: {megagroup}")
            log_line(f"  access_hash: {access_hash}")
            log_line("")

            count += 1

        ts2 = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        log_line(f"===== TG CHAT SCAN END {ts2} (dialogs={count}) =====\n")

    client.loop.run_until_complete(runner())
    client.disconnect()

if __name__ == "__main__":
    main()

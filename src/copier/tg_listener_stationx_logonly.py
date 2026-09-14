import os
import json
from datetime import datetime, timezone

from telethon import TelegramClient, events
from telethon.sessions import StringSession

CFG_PATH = "config/source_channel.json"
LOG_PATH = "logs/copier/stationx_listener.log"


def log_line(s: str) -> None:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(s + "\n")


def load_peer_id() -> int:
    with open(CFG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)["source_channel"]
    peer_id = int(cfg["peer_id"])
    return peer_id


def main() -> None:
    api_id = os.getenv("TG_API_ID", "").strip()
    api_hash = os.getenv("TG_API_HASH", "").strip()
    session_str = os.getenv("TG_SESSION", "").strip()

    if not api_id.isdigit():
        raise SystemExit("ERROR: TG_API_ID missing or not digits.")
    if len(api_hash) < 20:
        raise SystemExit("ERROR: TG_API_HASH missing or too short.")
    if len(session_str) < 20:
        raise SystemExit("ERROR: TG_SESSION missing or too short.")

    peer_id = load_peer_id()

    # Start banner
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    log_line(f"\n===== STATIONX LISTENER START {ts} peer_id={peer_id} =====")

    client = TelegramClient(StringSession(session_str), int(api_id), api_hash)

    @client.on(events.NewMessage)
    async def handler(event: events.NewMessage.Event) -> None:
        # Filter strictly by peer_id
        try:
            ev_peer = event.chat_id
        except Exception:
            return

        if ev_peer != peer_id:
            return

        msg = event.message
        msg_id = getattr(msg, "id", None)
        reply_to = getattr(getattr(msg, "reply_to", None), "reply_to_msg_id", None)
        date_utc = msg.date.replace(tzinfo=timezone.utc).isoformat(timespec="seconds") if getattr(msg, "date", None) else None
        text = msg.message if getattr(msg, "message", None) else ""

        # Minimal, robust log format
        log_line("[MSG]")
        log_line(f"  date_utc: {date_utc}")
        log_line(f"  peer_id: {ev_peer}")
        log_line(f"  message_id: {msg_id}")
        log_line(f"  reply_to_msg_id: {reply_to}")
        log_line("  text: " + (text.replace("\n", "\\n")))
        log_line("")

    async def runner():
        await client.connect()
        if not await client.is_user_authorized():
            raise SystemExit("ERROR: Session not authorized (stop).")

        # Hard gate: resolve entity and verify it's a broadcast Channel
        ent = await client.get_entity(peer_id)
        cls = ent.__class__.__name__
        broadcast = getattr(ent, "broadcast", None)
        megagroup = getattr(ent, "megagroup", None)
        title = getattr(ent, "title", None)

        log_line("[CHECK]")
        log_line(f"  resolved_title: {title}")
        log_line(f"  class: {cls}")
        log_line(f"  broadcast: {broadcast}")
        log_line(f"  megagroup: {megagroup}")
        log_line("")

        if not (cls == "Channel" and broadcast is True and megagroup is False):
            raise SystemExit("FAIL-STOP: peer_id is not a broadcast Channel. Do NOT proceed.")

        # Idle listening loop
        await client.run_until_disconnected()

    client.loop.run_until_complete(runner())


if __name__ == "__main__":
    main()


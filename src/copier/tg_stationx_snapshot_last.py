import os, json
from datetime import timezone
from telethon import TelegramClient
from telethon.sessions import StringSession

CFG_PATH = "config/source_channel.json"
LOG_PATH = "logs/copier/stationx_snapshot.log"

def log(s: str):
    os.makedirs("logs/copier", exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(s + "\n")

def main():
    api_id = os.getenv("TG_API_ID","").strip()
    api_hash = os.getenv("TG_API_HASH","").strip()
    session_str = os.getenv("TG_SESSION","").strip()
    if not api_id.isdigit() or len(api_hash) < 20 or len(session_str) < 20:
        raise SystemExit("ERROR: missing TG_* env")

    peer_id = int(json.load(open(CFG_PATH,"r",encoding="utf-8"))["source_channel"]["peer_id"])

    client = TelegramClient(StringSession(session_str), int(api_id), api_hash)

    async def runner():
        await client.connect()
        if not await client.is_user_authorized():
            raise SystemExit("ERROR: Session not authorized")

        ent = await client.get_entity(peer_id)
        log(f"\n===== SNAPSHOT START peer_id={peer_id} title={getattr(ent,'title',None)} =====")

        # last 30 messages
        async for m in client.iter_messages(ent, limit=100):
            dt = m.date.replace(tzinfo=timezone.utc).isoformat(timespec="seconds") if m.date else None
            reply_to = getattr(getattr(m, "reply_to", None), "reply_to_msg_id", None)
            text = m.message or ""
            log("[MSG]")
            log(f"  date_utc: {dt}")
            log(f"  message_id: {m.id}")
            log(f"  reply_to_msg_id: {reply_to}")
            log("  text: " + text.replace("\n", "\\n"))
            log("")

        log("===== SNAPSHOT END =====\n")

    client.loop.run_until_complete(runner())
    client.disconnect()

if __name__ == "__main__":
    main()

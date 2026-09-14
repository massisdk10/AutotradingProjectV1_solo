import os
import json
from telethon import TelegramClient
from telethon.sessions import StringSession

CFG = "config/source_channel.json"

def main():
    api_id = os.getenv("TG_API_ID","").strip()
    api_hash = os.getenv("TG_API_HASH","").strip()
    session_str = os.getenv("TG_SESSION","").strip()

    if not api_id.isdigit():
        raise SystemExit("ERROR: TG_API_ID missing or not digits.")
    if len(api_hash) < 20:
        raise SystemExit("ERROR: TG_API_HASH missing or too short.")
    if len(session_str) < 20:
        raise SystemExit("ERROR: TG_SESSION missing or too short.")

    with open(CFG, "r", encoding="utf-8") as f:
        cfg = json.load(f)["source_channel"]

    chan_id = int(cfg["peer_id"])  # IMPORTANT: use peer_id (-100...)

    client = TelegramClient(StringSession(session_str), int(api_id), api_hash)

    async def runner():
        await client.connect()
        if not await client.is_user_authorized():
            raise SystemExit("ERROR: Session not authorized (stop).")

        ent = await client.get_entity(chan_id)

        cls = ent.__class__.__name__
        broadcast = getattr(ent, "broadcast", None)
        megagroup = getattr(ent, "megagroup", None)
        username = getattr(ent, "username", None)
        title = getattr(ent, "title", None)

        print("RESOLVED")
        print("  id:", chan_id)
        print("  class:", cls)
        print("  title:", title)
        print("  username:", username)
        print("  broadcast:", broadcast)
        print("  megagroup:", megagroup)

        # Hard safety gate
        if not (cls == "Channel" and broadcast is True and megagroup is False):
            raise SystemExit("FAIL-STOP: ID is not a broadcast Channel. Do NOT proceed.")

    client.loop.run_until_complete(runner())
    client.disconnect()

if __name__ == "__main__":
    main()


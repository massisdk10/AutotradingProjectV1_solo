import os
from telethon import TelegramClient

api_id = int(os.environ["TG_API_ID"])
api_hash = os.environ["TG_API_HASH"]
session = os.environ.get("TG_SESSION", "scan_chats_mac_001")

async def main(client):
    async for d in client.iter_dialogs():
        name = (d.name or "").strip()
        if not name:
            continue
        print(f"{name} | id={d.entity.id} | type={type(d.entity).__name__}")

with TelegramClient(session, api_id, api_hash) as client:
    client.loop.run_until_complete(main(client))

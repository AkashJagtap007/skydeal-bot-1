from telethon.sync import TelegramClient, events
import asyncio
import re
import threading
from ping_server import app  # Flask server for Railway

# === Telegram API Credentials ===
api_id = 26429542
api_hash = '6caf396bf1f8898478ce1d8bdb1b5a88'
session_name = 'skydeal'

# === Channels ===
source_channels = ['realearnkaro', 'dealdost', 'skydeal_frostfibre']
converter_bot = 'ekconverter20bot'
destination_channel = 'SkyDeal247'

# === Extract all valid URLs ===
def extract_all_valid_links(text):
    return re.findall(r'(https?://[^\s<>]+)', text)

# === Telegram Client ===
client = TelegramClient(session_name, api_id, api_hash)

@client.on(events.NewMessage(chats=source_channels))
async def convert_and_forward(event):
    text = event.raw_text or ""
    links = extract_all_valid_links(text)

    if not links:
        print("⛔ No links found.")
        return

    print(f"📥 Message from @{event.chat.username or 'source'} with {len(links)} link(s)")

    converted_links = {}
    final_text = text

    try:
        for link in links:
            print(f"🔁 Converting: {link}")
            async with client.conversation(converter_bot, timeout=30) as conv:
                await conv.send_message(link)
                reply = await conv.get_response()
                converted_link = reply.text.strip()
                converted_links[link] = converted_link
                print(f"✅ Converted: {link} → {converted_link}")

        for original, converted in converted_links.items():
            final_text = final_text.replace(original, converted)

        if event.photo or event.document:
            await client.send_file(
                destination_channel,
                file=event.media,
                caption=final_text,
                link_preview=False
            )
            print("🖼️ Media forwarded with converted links.")
        else:
            await client.send_message(
                destination_channel,
                final_text,
                link_preview=False
            )
            print("📤 Text forwarded with converted links.")

    except Exception as e:
        print(f"❌ Error: {e}")

# === Flask + Telegram start ===
async def start_bot():
    await client.start()
    print("🚀 Bot is running and watching source channels...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 8080}).start()
    asyncio.run(start_bot())

import asyncio
import re
import threading
from telethon.sync import TelegramClient, events, Button
from ping_server import app  # Flask app to keep Railway/Replit alive

# === Telegram API Credentials (yours) ===
api_id = 26429542
api_hash = '6caf396bf1f8898478ce1d8bdb1b5a88'
session_name = 'skydeal'

# === Telegram Usernames ===
source_channels = ['realearnkaro', 'dealdost', 'skydeal_frostfibre']
converter_bot = 'ekconverter20bot'
destination_channel = 'SkyDeal247'

# === Blocked Domains
blocked_domains = ['myntra.com']

# === Extract all links from a message ===
def extract_all_valid_links(text):
    return re.findall(r'(https?://[^\s<>]+)', text)

# === Setup Telegram client ===
client = TelegramClient(session_name, api_id, api_hash)

@client.on(events.NewMessage(chats=source_channels))
async def convert_and_repost(event):
    text = event.raw_text or ""

    if '🛒 Buy now ✅' in text:
        print("⛔ Already processed. Skipping.")
        return

    links = extract_all_valid_links(text)
    if not links:
        print("⛔ No links found in message. Skipping.")
        return

    # ✅ Block messages containing Myntra links
    for link in links:
        if any(blocked in link for blocked in blocked_domains):
            print(f"🚫 Blocked domain found ({link}). Skipping message.")
            return

    print(f"📥 Message from {event.chat.username or 'source'} with {len(links)} link(s)")

    converted_links = {}
    final_text = text

    try:
        # Convert each link using the converter bot
        for link in links:
            print(f"🤖 Sending to @{converter_bot}: {link}")
            async with client.conversation(converter_bot, timeout=30) as conv:
                await conv.send_message(link)
                reply = await conv.get_response()
                converted_link = reply.text.strip()
                converted_links[link] = converted_link
                print(f"✅ Converted: {link} → {converted_link}")

        # Replace original links with converted ones
        for original, converted in converted_links.items():
            final_text = final_text.replace(original, converted)

        # Mark message to avoid reprocessing
        final_text += "\n\n🛒 Buy now ✅"

        # Create Buy Now button using first converted link
        button_link = list(converted_links.values())[0]
        button = [[Button.url("🔗 Buy Now", button_link)]]

        # Post to destination channel (with or without media)
        if event.photo or event.document:
            await client.send_file(
                destination_channel,
                file=event.media,
                caption=final_text,
                buttons=button,
                link_preview=False
            )
            print("🖼️ Media + converted text posted to destination.")
        else:
            await client.send_message(
                destination_channel,
                final_text,
                buttons=button,
                link_preview=False
            )
            print("📝 Text-only message posted to destination.")

    except Exception as e:
        print(f"❌ Error during processing: {e}")

# === Run Flask + Telegram Bot ===
async def start_bot():
    await client.start()
    print("🚀 SkyDeal Bot is running...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 8080}).start()
    asyncio.run(start_bot())

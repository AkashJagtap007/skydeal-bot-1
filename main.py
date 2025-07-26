from telethon.sync import TelegramClient, events, Button
import asyncio
import re
import threading
from ping_server import app  # Flask server to keep Railway alive

# === Telegram API Credentials ===
api_id = 26429542
api_hash = '6caf396bf1f8898478ce1d8bdb1b5a88'
session_name = 'skydeal'

# === Telegram Channels ===
source_channels = ['realearnkaro', 'dealdost', 'skydeal_frostfibre']
converter_bot = 'ekconverter20bot'
destination_channel = 'SkyDeal247'

# === Extract all links from text ===
def extract_all_valid_links(text):
    return re.findall(r'(https?://[^\s<>]+)', text)

# === Telegram client ===
client = TelegramClient(session_name, api_id, api_hash)

@client.on(events.NewMessage(chats=source_channels))
async def convert_and_repost(event):
    text = event.raw_text or ""

    # Skip already processed messages
    if '🛒 Buy now ✅' in text:
        print("⛔ Already processed.")
        return

    links = extract_all_valid_links(text)
    if not links:
        print("⛔ No links found.")
        return

    print(f"📥 Message from {event.chat.username or 'source'} with {len(links)} link(s)")

    converted_links = {}
    final_text = text

    try:
        # Convert links using the bot
        for link in links:
            print(f"🤖 Sending to @{converter_bot}: {link}")
            async with client.conversation(converter_bot, timeout=30) as conv:
                await conv.send_message(link)
                reply = await conv.get_response()
                converted_reply_text = reply.text.strip()

                converted_links[link] = converted_reply_text
                print(f"✅ Converted: {link} → {converted_reply_text}")

        # Replace original links in the message with full bot reply texts
        for original, converted_reply in converted_links.items():
            final_text = final_text.replace(original, converted_reply)

        final_text += "\n\n🛒 Buy now ✅"

        # Create button with first link inside converted reply (if available)
        button_link_candidates = extract_all_valid_links(list(converted_links.values())[0])
        button_url = button_link_candidates[0] if button_link_candidates else None
        buttons = [[Button.url("🔗 Buy Now", button_url)]] if button_url else None

        # Send media + caption if photo exists
        if event.photo or event.document:
            await client.send_file(
                destination_channel,
                file=event.media,
                caption=final_text,
                buttons=buttons,
                link_preview=False
            )
            print("🖼️ Sent media with converted links.")
        else:
            await client.send_message(
                destination_channel,
                final_text,
                buttons=buttons,
                link_preview=False
            )
            print("📤 Sent text message with converted links.")

    except Exception as e:
        print(f"❌ Error: {e}")

# === Start Flask and Telegram ===
async def start_bot():
    await client.start()
    print("🚀 Bot is running...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 8080}).start()
    asyncio.run(start_bot())

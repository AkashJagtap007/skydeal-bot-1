import asyncio
import re
import threading
from telethon.sync import TelegramClient, events, Button
from ping_server import app

# === Telegram API Credentials ===
api_id = 26429542
api_hash = '6caf396bf1f8898478ce1d8bdb1b5a88'
session_name = 'skydeal'

# === Channels and Bot ===
source_channels = ['skydeal_frostfibre', 'dealdost', 'realearnkaro']
destination_channel = 'SkyDeal247'
converter_bot = 'ekconverter20bot'

# === Blocked Domains ===
blocked_domains = ['myntra.com']

# === Extract all links ===
def extract_all_valid_links(text):
    return re.findall(r'(https?://[^\s<>]+)', text)

# === Telegram client ===
client = TelegramClient(session_name, api_id, api_hash)

@client.on(events.NewMessage(chats=source_channels))
async def convert_and_repost(event):
    original_text = event.raw_text or ""
    print(f"\n🔔 New message from: {event.chat.username or event.chat_id}")

    if '🛒 Buy now ✅' in original_text:
        print("⏩ Already converted. Skipping.")
        return

    links = extract_all_valid_links(original_text)
    if not links:
        print("⏩ No links found. Skipping.")
        return

    if any(blocked in link for link in links for blocked in blocked_domains):
        print("🚫 Blocked domain (e.g. myntra) found. Skipping.")
        return

    converted_links = {}
    try:
        for link in links:
            print(f"🤖 Converting via @{converter_bot}: {link}")
            async with client.conversation(converter_bot, timeout=30) as conv:
                await conv.send_message(link)

                while True:
                    reply = await conv.get_response()
                    reply_text = reply.text.strip()

                    # Skip raw short link-only replies
                    if re.fullmatch(r'https?://[^\s<>]+', reply_text):
                        print("⚠️ Ignoring short reply.")
                        continue

                    # Get converted URL from a rich reply
                    match = re.search(r'(https?://[^\s<>]+)', reply_text)
                    if match:
                        converted_link = match.group(1)
                        converted_links[link] = converted_link
                        print(f"✅ Converted: {link} → {converted_link}")
                        break

            await asyncio.sleep(1.5)

        if not converted_links:
            print("⛔ No valid converted links found.")
            return

        # Replace all original links in original message
        final_text = original_text
        for original, converted in converted_links.items():
            final_text = final_text.replace(original, converted)

        # Add Buy now tag
        final_text += "\n\n🛒 Buy now ✅"

        # Create button with first converted link
        button_link = list(converted_links.values())[0]
        button = [[Button.url("🔗 Buy Now", button_link)]]

        # Check if media exists
        if event.media:
            await client.send_file(
                destination_channel,
                file=event.media,
                caption=final_text,
                buttons=button,
                link_preview=False
            )
            print("📤 Media + caption posted.")
        else:
            await client.send_message(
                destination_channel,
                final_text,
                buttons=button,
                link_preview=False
            )
            print("📤 Text-only message posted.")

    except Exception as e:
        print(f"❌ Error during processing: {e}")

# === Start Bot ===
async def start_bot():
    await client.start()
    print("🚀 Bot is live. Watching:", ", ".join(source_channels))
    await client.run_until_disconnected()

if __name__ == "__main__":
    threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 8080}).start()
    asyncio.run(start_bot())

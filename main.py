import asyncio
import re
from telethon.sync import TelegramClient, events, Button

# === Telegram API Credentials ===
api_id = 26429542
api_hash = '6caf396bf1f8898478ce1d8bdb1b5a88'
session_name = 'skydeal'

# === Telegram usernames ===
source_channels = ['realearnkaro', 'dealdost', 'skydeal_frostfibre']
converter_bot = 'ekconverter20bot'
destination_channel = 'SkyDeal247'

# === Supported domains ===
supported_domains = [
    'flipkart.com', 'dl.flipkart.com', 'fkrt.cc',
    'amazon.in', 'amzn.to', 'ajio.com',
    'ekaro.in', 'bit.ly', 'ekart.shop'
]

# === Blocked domains (like Myntra) ===
blocked_domains = ['myntra.com']

# === Extract all supported links ===
def extract_supported_links(text):
    matches = re.findall(r'(https?://[^\s<>]+)', text)
    links = []
    for url in matches:
        if any(bad in url for bad in blocked_domains):
            return []  # Skip entire message if it contains a blocked domain
        if any(domain in url for domain in supported_domains):
            links.append(url.strip().split('?')[0])
    return links

# === Setup Telegram client ===
client = TelegramClient(session_name, api_id, api_hash)

@client.on(events.NewMessage(chats=source_channels))
async def convert_and_repost(event):
    if event.out or event.sender_id == (await client.get_me()).id:
        return

    text = event.raw_text or ""
    print(f"📥 Message received in {event.chat.username or 'source'}")
    print(f"🔍 Text: {text[:300]}")

    if '🛒 Buy Now' in text or '#converted' in text:
        print("⛔ Already processed. Skipping.")
        return

    links = extract_supported_links(text)
    if not links:
        print("❌ No valid (or blocked) links found. Skipping.")
        return

    converted_links = {}
    try:
        for link in links:
            print(f"🤖 Sending to @{converter_bot}: {link}")
            async with client.conversation(converter_bot, timeout=30) as conv:
                await conv.send_message(link)
                while True:
                    reply = await conv.get_response()
                    reply_text = reply.text.strip()
                    if len(reply_text) > 30 and 'http' in reply_text:
                        break
                converted_links[link] = reply_text
                print(f"✅ Converted: {link} → {reply_text}")

        # Replace original links with converted replies
        final_text = text
        for original, converted in converted_links.items():
            final_text = final_text.replace(original, converted)

        final_text += "\n\n#converted"

        # Extract first converted link for the button
        button_url = None
        if converted_links:
            first_reply = list(converted_links.values())[0]
            found_links = re.findall(r'(https?://[^\s<>]+)', first_reply)
            button_url = found_links[0] if found_links else None

        buttons = [[Button.url("🛒 Buy Now", button_url)]] if button_url else None

        await event.delete()
        print("🗑️ Original message deleted.")

        await client.send_message(
            destination_channel,
            final_text,
            buttons=buttons,
            link_preview=False
        )
        print(f"📤 Sent converted message to {destination_channel}")

    except Exception as e:
        print(f"❌ Error: {e}")

# === Run the bot ===
async def main():
    await client.start()
    print("🚀 Bot is running and converting all supported links...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())

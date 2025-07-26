import asyncio
import re
from telethon.sync import TelegramClient, events, Button

# === Telegram API Credentials ===
api_id = 26429542
api_hash = '6caf396bf1f8898478ce1d8bdb1b5a88'
session_name = 'skydeal'

# === Telegram usernames ===
source_channels = ['realearnkaro', 'dealdost', 'skydeal_frostfibre', 'SkyDeal247']
converter_bot = 'ekconverter20bot'
destination_channel = 'SkyDeal247'

# === Supported and Blocked Domains ===
supported_domains = [
    'flipkart.com', 'dl.flipkart.com', 'fkrt.cc',
    'amazon.in', 'amzn.to',
    'ajio.com',
    'meesho.com', 'meesho.link',
    'nykaa.com',
    'firstcry.com',
    'mamaearth.in',
    'croma.com',
    'tatacliq.com',
    'snapdeal.com',
    'bigbasket.com',
    'reliancedigital.in',
    'pharmeasy.in',
    'bit.ly', 'ekaro.in', 'ekart.shop'
]

blocked_domains = ['myntra.com']

# === Extract supported links ===
def extract_supported_links(text):
    matches = re.findall(r'(https?://[^\s<>]+)', text)
    links = []
    for url in matches:
        if any(bad in url for bad in blocked_domains):
            print(f"🚫 Blocked domain detected: {url}")
            return []  # Block entire message
        if any(domain in url for domain in supported_domains):
            links.append(url.strip())
    return links

client = TelegramClient(session_name, api_id, api_hash)

@client.on(events.NewMessage(chats=source_channels))
async def convert_and_repost(event):
    try:
        print("🔔 New message received.")

        if event.out or '🛒 Buy Now' in (event.raw_text or ''):
            print("⏩ Skipped (self message or already converted).")
            return

        text = event.message.message or ""
        print("📝 Message text:", text)

        links = extract_supported_links(text)
        print("🔗 Extracted links:", links)

        if not links:
            print("⚠️ No supported links found. Skipping.")
            return

        converted_links = {}

        for link in links:
            print(f"➡️ Converting: {link}")
            async with client.conversation(converter_bot, timeout=30) as conv:
                await conv.send_message(link)

                while True:
                    reply = await conv.get_response()
                    reply_text = reply.text.strip()

                    match = re.search(r'(https?://[^\s<>]+)', reply_text)
                    if match:
                        converted_url = match.group(1)
                        converted_links[link] = converted_url
                        print(f"✅ Converted: {converted_url}")
                        break
                await asyncio.sleep(1.5)

        if not converted_links:
            print("⚠️ No valid converted links found.")
            return

        # Replace original links with converted links
        final_text = text
        for original, converted in converted_links.items():
            final_text = final_text.replace(original, converted)

        # Add "Buy Now" button
        button_url = list(converted_links.values())[0]
        buttons = [[Button.url("🛒 Buy Now", button_url)]]

        # Delete original message
        await event.delete()
        print("🗑️ Original message deleted.")

        # Send new message to destination
        await client.send_message(
            destination_channel,
            final_text,
            buttons=buttons,
            link_preview=False
        )
        print("✅ Message sent to destination.")

    except Exception as e:
        print(f"❌ Error occurred: {e}")

# === Start Bot ===
async def main():
    await client.start()
    print("🚀 SkyDeal Bot is running...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())

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

# === Supported and Blocked Domains ===
supported_domains = [
    'flipkart.com', 'dl.flipkart.com', 'fkrt.cc',
    'amazon.in', 'amzn.to', 'ajio.com',
    'ekaro.in', 'bit.ly', 'ekart.shop'
]
blocked_domains = ['myntra.com']

# === Extract supported links ===
def extract_supported_links(text):
    matches = re.findall(r'(https?://[^\s<>]+)', text)
    links = []
    for url in matches:
        if any(bad in url for bad in blocked_domains):
            return []  # Skip entire message if blocked domain is found
        if any(domain in url for domain in supported_domains):
            links.append(url.strip().split('?')[0])
    return links

client = TelegramClient(session_name, api_id, api_hash)

@client.on(events.NewMessage(chats=source_channels))
async def convert_and_repost(event):
    if event.out or event.sender_id == (await client.get_me()).id:
        return

    text = event.raw_text or ""
    if '🛒 Buy Now' in text or '#converted' in text:
        return

    links = extract_supported_links(text)
    if not links:
        return

    converted_links = {}

    try:
        for link in links:
            async with client.conversation(converter_bot, timeout=30) as conv:
                await conv.send_message(link)

                while True:
                    reply = await conv.get_response()
                    reply_text = reply.text.strip()
                    if 'http' in reply_text and len(reply_text) > 20:
                        break

            # ✅ Extract only converted URL
            converted_url_match = re.search(r'(https?://[^\s<>]+)', reply_text)
            if not converted_url_match:
                continue
            converted_url = converted_url_match.group(1)
            converted_links[link] = converted_url

        # ✅ Replace original links with converted links in text
        final_text = text
        for original, converted in converted_links.items():
            final_text = final_text.replace(original, converted)

        final_text += "\n\n#converted"

        # ✅ Button using first converted link
        button_url = list(converted_links.values())[0]
        buttons = [[Button.url("🛒 Buy Now", button_url)]]

        # ✅ Delete the original message
        await event.delete()

        # ✅ Send only the final text+converted links (not raw bot reply)
        await client.send_message(
            destination_channel,
            final_text,
            buttons=buttons,
            link_preview=False
        )

    except Exception as e:
        print(f"❌ Error: {e}")

# === Run bot ===
async def main():
    await client.start()
    print("🚀 Bot is running...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import re
from telethon.sync import TelegramClient, events, Button

# === Telegram API Credentials ===
api_id = 26429542
api_hash = '6caf396bf1f8898478ce1d8bdb1b5a88'
session_name = 'skydeal'

# === Telegram usernames ===
source_channels = ['realearnkaro', 'dealdost', 'skydeal_frostfibre']
converter_bot = 'ekconverter15bot'
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
            return []  # Block entire message if any blocked domain is present
        if any(domain in url for domain in supported_domains):
            links.append(url.strip())
    return links

client = TelegramClient(session_name, api_id, api_hash)

@client.on(events.NewMessage(chats=source_channels))
async def convert_and_repost(event):
    try:
        if event.out or '🛒 Buy Now' in (event.raw_text or ''):
            return

        text = event.message.message or ""
        links = extract_supported_links(text)
        if not links:
            return

        converted_links = {}

        for link in links:
            async with client.conversation(converter_bot, timeout=30) as conv:
                await conv.send_message(link)

                # Keep getting responses until valid one with a link is found
                while True:
                    reply = await conv.get_response()
                    reply_text = reply.text.strip()

                    # Extract valid URL from the response
                    match = re.search(r'(https?://[^\s<>]+)', reply_text)
                    if match:
                        converted_url = match.group(1)
                        converted_links[link] = converted_url
                        break  # stop reading more replies after valid one

                await asyncio.sleep(1.5)  # prevent rate limiting

        if not converted_links:
            return

        # Replace original links with converted links
        final_text = text
        for original, converted in converted_links.items():
            final_text = final_text.replace(original, converted)

        # Add "Buy Now" button using the first converted link
        button_url = list(converted_links.values())[0]
        buttons = [[Button.url("🛒 Buy Now", button_url)]]

        # Delete original message
        await event.delete()

        # Send final message to destination channel
        await client.send_message(
            destination_channel,
            final_text,
            buttons=buttons,
            link_preview=False
        )

    except Exception as e:
        print(f"❌ Error: {e}")

# === Run the bot ===
async def main():
    await client.start()
    print("🚀 SkyDeal Bot is running...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())

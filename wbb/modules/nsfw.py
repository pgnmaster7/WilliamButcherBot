from wbb import app, arq, IMGBB_API_KEY, MESSAGE_DUMP_CHAT
from wbb.utils.filter_groups import nsfw_detect_group
from wbb.utils.dbfunctions import is_nsfw_on, nsfw_on, nsfw_off
from wbb.modules.admin import member_permissions
from pyrogram import filters
from random import randint
import aiohttp
import aiofiles
import os


@app.on_message((filters.document | filters.photo | filters.sticker) & ~filters.private, group=nsfw_detect_group)
async def detect_nsfw(_, message):
    if message.document:
        if int(message.document.file_size) > 3145728:
            return
        mime_type = message.document.mime_type
        if mime_type != "image/png" and mime_type != "image/jpeg":
            return
    if not await is_nsfw_on(message.chat.id):
        return
    image = await message.download(f"{randint(6666, 9999)}.jpg")
    async with aiofiles.open(image, mode='rb') as f:
        payload = {
            "key": IMGBB_API_KEY,
            "image": await f.read(),
            "expiration": "60"
        }
    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.imgbb.com/1/upload", data=payload) as resp:
            data = await resp.json()
        url = data['data']['url']
    os.remove(image)
    try:
        results = await arq.nsfw_scan(url)
    except Exception as e:
        print(e)
        return
    hentai = results.data.hentai
    sexy = results.data.sexy
    porn = results.data.porn
    neutral = results.data.neutral
    if hentai < 80 and porn < 70 and sexy < 95:
        return
    if neutral > 30:
        return
    user_mention = message.from_user.mention
    user_id = message.from_user.id
    m = await message.forward(MESSAGE_DUMP_CHAT)
    try:
        await message.delete()
    except Exception:
        pass
    await message.reply_text(f"""
**NSFW [Image]({m.link}) Detected & Deleted Successfully!
————————————————————————**

**User:** {user_mention} [`{user_id}`]
**Safe:** `{neutral}` %
**Porn:** `{porn}` %
**Adult:** `{sexy}` %
**Hentai:** `{hentai}` %
""")


@app.on_message(filters.command("nsfw_scan"))
async def nsfw_scan_command(_, message):
    if not message.reply_to_message:
        await message.reply_text("Reply to an image or document to scan it.")
        return
    reply = message.reply_to_message
    if not reply.document and not reply.photo and not reply.sticker:
        await message.reply_text("Reply to an image/document/sticker to scan it.")
        return
    if message.reply_to_message.document:
        if int(message.reply_to_message.document.file_size) > 3145728:
            return
        mime_type = message.reply_to_message.document.mime_type
        if mime_type != "image/png" and mime_type != "image/jpeg":
            return
    image = await message.reply_to_message.download(f"{randint(6666, 9999)}.jpg")
    async with aiofiles.open(image, mode='rb') as f:
        payload = {
            "key": IMGBB_API_KEY,
            "image": await f.read(),
            "expiration": "60"
        }
    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.imgbb.com/1/upload", data=payload) as resp:
            data = await resp.json()
        url = data['data']['url']
    os.remove(image)
    try:
        results = await arq.nsfw_scan(url)
    except Exception as e:
        print(e)
        await message.reply_text(str(e))
        return
    hentai = results.data.hentai
    sexy = results.data.sexy
    porn = results.data.porn
    neutral = results.data.neutral
    await message.reply_text(f"""
**Neutral:** `{neutral}`
**Porn:** `{porn}`
**Hentai:** `{hentai}`
**sexy:** `{sexy}`
""")


@app.on_message(filters.command("anti_nsfw") & ~filters.private)
async def nsfw_enable_disable(_, message):
    if len(message.command) != 2:
        await message.reply_text("Usage: /anti_nsfw [enable | disable]")
        return
    status = message.text.split(None, 1)[1].strip()
    status = status.lower()
    chat_id = message.chat.id
    user_id = message.from_user.id
    permissions = await member_permissions(chat_id, user_id)
    if "can_change_info" not in permissions:
        await message.reply_text("You don't have enough permissions.")
        return
    if status == "enable":
        await nsfw_on(chat_id)
        await message.reply_text("Enabled AntiNSFW System. I will Delete Messages Containing Inappropriate Content.")
    elif status == "disable":
        await nsfw_off(chat_id)
        await message.reply_text("Disabled AntiNSFW System.")
    else:
        await message.reply_text("Unknown Suffix, Use /anti_nsfw [enable|disable]")

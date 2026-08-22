import os
import re
import json
import asyncio
import httpx
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Update
from aiogram.enums import ParseMode

BOT_TOKEN = os.getenv("BOT_TOKEN")

app = FastAPI()
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

API_1_URL = "http://apis.rootx.run/key=LAKSHIT-RAMDI&term={}"
API_2_URL = "https://nmdllpezcocquamhgpmb.supabase.co/functions/v1/lookup?number={}"
DEV_TAG = "@lakshitpatidar"

# Data Normalizer & Tag Stripper
def sanitize_record(raw: dict) -> dict:
    if not isinstance(raw, dict):
        return {}
    
    # Capitalize names and clean whitespace
    name = str(raw.get("name") or "N/A").strip().title()
    fname = str(raw.get("fname") or raw.get("father_name") or "N/A").strip().title()
    address = str(raw.get("address") or "N/A").strip()
    
    # Remove unwanted trailing tags or extra symbols
    address = re.sub(r'!!|!NA!', ' ', address)
    address = re.sub(r'\s+', ' ', address).strip()

    return {
        "mobile": str(raw.get("mobile") or "N/A"),
        "name": name,
        "father_name": fname,
        "id_number": str(raw.get("id") or "N/A"),
        "circle": str(raw.get("circle") or "N/A"),
        "address": address,
        "email": raw.get("email") if raw.get("email") else "N/A",
        "alt_mobile": str(raw.get("alt") or "N/A"),
        "dev": DEV_TAG
    }

async def fetch_api_1(number: str) -> dict:
    async with httpx.AsyncClient(timeout=8.0) as client:
        try:
            resp = await client.get(API_1_URL.format(number))
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success" and data.get("results"):
                    return sanitize_record(data["results"][0])
        except Exception:
            pass
    return None

async def fetch_api_2(number: str) -> dict:
    async with httpx.AsyncClient(timeout=8.0) as client:
        try:
            resp = await client.get(API_2_URL.format(number))
            if resp.status_code == 200:
                data = resp.json()
                # Unpack nested structures safely
                res = data.get("result", {})
                if isinstance(res, dict) and "result" in res:
                    res = res.get("result", {})
                
                results_list = res.get("results", [])
                if results_list and len(results_list) > 0:
                    return sanitize_record(results_list[0])
        except Exception:
            pass
    return None

# Long Message Splitter
def send_smart_json(data: dict, title: str = "SEARCH RESULT") -> list[str]:
    if not data:
        return [f"❌ <b>{title}</b>\n<i>No record found in database.</i>"]

    formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
    header = f"<b><u>✦ {title} ✦</u></b>\n"
    
    # If JSON fits inside one message (Telegram limit ~4096 chars)
    full_text = f"{header}```Info\n{formatted_json}\n```"
    if len(full_text) <= 4000:
        return [full_text]

    # Split logic for unusually large responses
    chunks = []
    lines = formatted_json.split("\n")
    current_chunk = ""
    
    for line in lines:
        if len(current_chunk) + len(line) + 20 > 3800:
            chunks.append(f"{header}```Info\n{current_chunk}\n```")
            current_chunk = ""
        current_chunk += line + "\n"
        
    if current_chunk:
        chunks.append(f"```Info\n{current_chunk}\n```")
        
    return chunks

def extract_number(text: str) -> str:
    if not text:
        return None
    match = re.search(r'\b[6-9]\d{9}\b', text)
    return match.group(0) if match else None

# --- BOT COMMAND HANDLERS ---

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.reply(
        "✨ <b><u>INTELLIGENCE SEARCH BOT</u></b> ✨\n\n"
        "<b>Available Commands:</b>\n"
        "▫️ <code>/num 98765XXXXX</code> — <i>Smart Auto-Fetch (Fastest)</i>\n"
        "▫️ <code>/num1 98765XXXXX</code> — <i>Query Server 1</i>\n"
        "▫️ <code>/num2 98765XXXXX</code> — <i>Query Server 2</i>\n"
        "▫️ <code>/bnum 98765XXXXX</code> — <i>Dual Fetch (Both Servers)</i>\n\n"
        "💡 <i>Tip: Number waale kisi bhi message par reply karke info fetch kar sakte ho.</i>",
        reply_to_message_id=message.message_id
    )

@dp.message(Command("num1"))
async def num1_cmd(message: types.Message):
    num = extract_number(message.text)
    if not num:
        return await message.reply("⚠️ <b>Invalid Input:</b> Please provide a valid 10-digit phone number.", reply_to_message_id=message.message_id)
    
    status_msg = await message.reply("🔄 <i>Querying Server 1...</i>", reply_to_message_id=message.message_id)
    data = await fetch_api_1(num)
    chunks = send_smart_json(data, "SERVER 1 RECORD")
    
    await status_msg.edit_text(chunks[0])
    for chunk in chunks[1:]:
        await message.reply(chunk, reply_to_message_id=message.message_id)

@dp.message(Command("num2"))
async def num2_cmd(message: types.Message):
    num = extract_number(message.text)
    if not num:
        return await message.reply("⚠️ <b>Invalid Input:</b> Please provide a valid 10-digit phone number.", reply_to_message_id=message.message_id)
    
    status_msg = await message.reply("🔄 <i>Querying Server 2...</i>", reply_to_message_id=message.message_id)
    data = await fetch_api_2(num)
    chunks = send_smart_json(data, "SERVER 2 RECORD")
    
    await status_msg.edit_text(chunks[0])
    for chunk in chunks[1:]:
        await message.reply(chunk, reply_to_message_id=message.message_id)

@dp.message(Command("num"))
async def num_cmd(message: types.Message):
    num = extract_number(message.text)
    if not num:
        return await message.reply("⚠️ <b>Invalid Input:</b> Please provide a valid 10-digit phone number.", reply_to_message_id=message.message_id)
    
    status_msg = await message.reply("⚡ <i>Executing hybrid search...</i>", reply_to_message_id=message.message_id)
    
    # Priority search: Try Server 1, fallback to Server 2
    data = await fetch_api_1(num)
    server_used = "HYBRID SEARCH (SERVER 1)"
    if not data:
        data = await fetch_api_2(num)
        server_used = "HYBRID SEARCH (SERVER 2)"
        
    chunks = send_smart_json(data, server_used)
    await status_msg.edit_text(chunks[0])
    for chunk in chunks[1:]:
        await message.reply(chunk, reply_to_message_id=message.message_id)

@dp.message(Command("bnum"))
async def bnum_cmd(message: types.Message):
    num = extract_number(message.text)
    if not num:
        return await message.reply("⚠️ <b>Invalid Input:</b> Please provide a valid 10-digit phone number.", reply_to_message_id=message.message_id)
    
    status_msg = await message.reply("🚀 <i>Fetching records from BOTH servers concurrently...</i>", reply_to_message_id=message.message_id)
    
    # Concurrent Async Calls for maximum speed
    data1, data2 = await asyncio.gather(fetch_api_1(num), fetch_api_2(num))
    
    chunks1 = send_smart_json(data1, "SERVER 1 RESULT")
    chunks2 = send_smart_json(data2, "SERVER 2 RESULT")
    
    await status_msg.edit_text(chunks1[0])
    for chunk in chunks1[1:]:
        await message.reply(chunk, reply_to_message_id=message.message_id)
        
    for chunk in chunks2:
        await message.reply(chunk, reply_to_message_id=message.message_id)

@dp.message(F.reply_to_message)
async def handle_reply_auto(message: types.Message):
    # Skip if message starts with a command slash
    if message.text and message.text.startswith('/'):
        return

    num = extract_number(message.reply_to_message.text)
    if num:
        status_msg = await message.reply("⚡ <i>Auto-detected number from reply. Fetching details...</i>", reply_to_message_id=message.message_id)
        
        data = await fetch_api_1(num)
        server_used = "AUTO SEARCH (SERVER 1)"
        if not data:
            data = await fetch_api_2(num)
            server_used = "AUTO SEARCH (SERVER 2)"
            
        chunks = send_smart_json(data, server_used)
        await status_msg.edit_text(chunks[0])
        for chunk in chunks[1:]:
            await message.reply(chunk, reply_to_message_id=message.message_id)

# --- VERCEL WEBHOOK ROUTE ---
@app.post("/api/webhook")
async def webhook_handler(request: Request):
    try:
        update_data = await request.json()
        update = Update.model_validate(update_data, context={"bot": bot})
        await dp.feed_update(bot, update)
    except Exception as e:
        pass
    return {"status": "ok"}


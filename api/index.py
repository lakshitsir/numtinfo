import os
import re
import json
import asyncio
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Update
from aiogram.enums import ParseMode

# === CONFIGURATION ===
BOT_TOKEN = os.getenv("BOT_TOKEN", "8891963980:AAFBbrs5pOsPIAZmWJkJ59CAxFP8EvwygNc")
DEV_TAG = "@lakshitpatidar"

app = FastAPI()
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Headers to prevent API blocks
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# === DATA FILTER & CLEANER ===
def sanitize_record(raw: dict) -> dict:
    if not isinstance(raw, dict): 
        return {}
        
    clean_data = {}
    ignore_keys = {"success", "status", "count", "limit", "tag", "credit", "query", "meta", "search_time"}
    
    for key, value in raw.items():
        if key.lower() in ignore_keys:
            continue
            
        val = str(value).strip() if value else "N/A"
        
        # Format Address professionally
        if key.lower() == "address":
            val = re.sub(r'!!|!NA!', ', ', val)
            val = re.sub(r'\s+', ' ', val).strip(', ')
        
        # Capitalize headers (e.g., father_name -> Father_Name)
        clean_key = str(key).replace("_", " ").title().replace(" ", "_")
        
        # Proper case for names
        if key.lower() in ["name", "fname", "father_name"]:
            clean_data[clean_key] = val.title()
        else:
            clean_data[clean_key] = val
            
    # Add developer signature at the very end
    clean_data["Dev"] = DEV_TAG
    return clean_data

def extract_target_data(data: dict) -> dict:
    """Recursively finds the 'results' array no matter how deep the API hides it."""
    if isinstance(data, dict):
        if "results" in data and isinstance(data["results"], list) and len(data["results"]) > 0:
            return sanitize_record(data["results"][0])
        for key, value in data.items():
            result = extract_target_data(value)
            if result:
                return result
    return None

# === API FETCHERS ===
async def fetch_api_1(num: str) -> dict:
    async with httpx.AsyncClient(timeout=12.0) as client:
        try:
            resp = await client.get(f"http://apis.rootx.run/key=LAKSHIT-RAMDI&term={num}", headers=HEADERS)
            if resp.status_code == 200:
                return extract_target_data(resp.json())
        except Exception:
            return None
    return None

async def fetch_api_2(num: str) -> dict:
    async with httpx.AsyncClient(timeout=12.0) as client:
        try:
            resp = await client.get(f"https://nmdllpezcocquamhgpmb.supabase.co/functions/v1/lookup?number={num}", headers=HEADERS)
            if resp.status_code == 200:
                return extract_target_data(resp.json())
        except Exception:
            return None
    return None

# === AESTHETIC UI FORMATTER ===
def format_json_response(data: dict, title: str) -> list:
    if not data: 
        return [f"<b>{title}</b>\n\n<i>No records found in the database.</i> ⚠️"]
    
    json_str = json.dumps(data, indent=4, ensure_ascii=False)
    header = f"<b>{title}</b>\n\n"
    
    # Native Telegram HTML Code Block for perfect copy-paste formatting
    code_block_start = "<pre><code class=\"language-Info\">\n"
    code_block_end = "\n</code></pre>"
    
    full_msg = f"{header}{code_block_start}{json_str}{code_block_end}"
    
    if len(full_msg) < 4000: 
        return [full_msg]
    
    # Split gracefully if data exceeds Telegram limits
    return [
        f"{header}{code_block_start}{json_str[:3800]}{code_block_end}", 
        "<i>Output truncated due to length limits.</i> ⚠️"
    ]

def get_num(text: str):
    match = re.search(r'\b\d{10}\b', str(text))
    return match.group(0) if match else None

# === BOT COMMANDS ===
@dp.message(Command("start"))
async def start_cmd(m: types.Message):
    welcome_text = (
        "<b>Intelligence Terminal Online</b> 🛡️\n\n"
        "<b>Available Commands:</b>\n"
        "▫️ <code>/num 98765XXXXX</code> — <i>Hybrid Auto-Fetch</i>\n"
        "▫️ <code>/num1 98765XXXXX</code> — <i>Query Server 1</i>\n"
        "▫️ <code>/num2 98765XXXXX</code> — <i>Query Server 2</i>\n"
        "▫️ <code>/bnum 98765XXXXX</code> — <i>Query Both Servers</i>\n\n"
        "<i>💡 Tip: You can directly reply to any number in chat to fetch details.</i>"
    )
    await m.answer(welcome_text)

@dp.message(Command("num1"))
async def num1_cmd(m: types.Message):
    num = get_num(m.text)
    if not num: 
        return await m.reply("<i>Please provide a valid 10-digit number.</i> ⚠️")
    
    msg = await m.reply("<i>Querying Server 1...</i> ⏳")
    data = await fetch_api_1(num)
    
    for chunk in format_json_response(data, "SERVER 1 EXTRACT"):
        await msg.edit_text(chunk) if chunk == format_json_response(data, "SERVER 1 EXTRACT")[0] else await m.reply(chunk)

@dp.message(Command("num2"))
async def num2_cmd(m: types.Message):
    num = get_num(m.text)
    if not num: 
        return await m.reply("<i>Please provide a valid 10-digit number.</i> ⚠️")
    
    msg = await m.reply("<i>Querying Server 2...</i> ⏳")
    data = await fetch_api_2(num)
    
    for chunk in format_json_response(data, "SERVER 2 EXTRACT"):
        await msg.edit_text(chunk) if chunk == format_json_response(data, "SERVER 2 EXTRACT")[0] else await m.reply(chunk)

@dp.message(Command("num"))
async def num_cmd(m: types.Message):
    num = get_num(m.text)
    if not num: 
        return await m.reply("<i>Please provide a valid 10-digit number.</i> ⚠️")
    
    msg = await m.reply("<i>Executing hybrid search...</i> ⏳")
    
    data = await fetch_api_1(num)
    title = "HYBRID EXTRACT (SERVER 1)"
    if not data:
        data = await fetch_api_2(num)
        title = "HYBRID EXTRACT (SERVER 2)"
        
    for chunk in format_json_response(data, title):
        await msg.edit_text(chunk) if chunk == format_json_response(data, title)[0] else await m.reply(chunk)

@dp.message(Command("bnum"))
async def bnum_cmd(m: types.Message):
    num = get_num(m.text)
    if not num: 
        return await m.reply("<i>Please provide a valid 10-digit number.</i> ⚠️")
    
    msg = await m.reply("<i>Processing concurrent requests...</i> ⏳")
    
    data1, data2 = await asyncio.gather(fetch_api_1(num), fetch_api_2(num))
    
    chunks1 = format_json_response(data1, "SERVER 1 RESULT")
    chunks2 = format_json_response(data2, "SERVER 2 RESULT")
    
    await msg.edit_text(chunks1[0])
    for c in chunks1[1:]: await m.reply(c)
    for c in chunks2: await m.reply(c)

@dp.message(F.reply_to_message)
async def auto_reply(m: types.Message):
    if m.text and m.text.startswith('/'): 
        return
    
    num = get_num(m.reply_to_message.text)
    if num:
        msg = await m.reply("<i>Target identified. Fetching records...</i> ⏳")
        data = await fetch_api_1(num)
        title = "AUTO EXTRACT (SERVER 1)"
        if not data:
            data = await fetch_api_2(num)
            title = "AUTO EXTRACT (SERVER 2)"
            
        for chunk in format_json_response(data, title):
            await msg.edit_text(chunk) if chunk == format_json_response(data, title)[0] else await m.reply(chunk)

# === VERCEL WEBHOOK ROUTES ===
@app.get("/")
async def root_path():
    html = (
        "<html><body style='background:#121212; color:#ffffff; font-family:sans-serif; text-align:center; margin-top:15%;'>"
        "<h2>Server Operational ✅</h2>"
        "<p style='color:#aaaaaa;'>Developed by @lakshitpatidar</p></body></html>"
    )
    return HTMLResponse(html)

@app.post("/api/webhook")
async def webhook_handler(request: Request):
    try:
        update = Update.model_validate(await request.json(), context={"bot": bot})
        await dp.feed_update(bot, update)
    except Exception:
        pass
    return {"status": "ok"}
    

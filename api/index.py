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

# === DYNAMIC DATA FILTER & CLEANER ☠️ ===
def sanitize_record(raw: dict) -> dict:
    if not isinstance(raw, dict): return {}
    clean_data = {}
    
    # API se jo bhi aayega, automatically pakad lega (Zero Data Mismatch)
    for key, value in raw.items():
        # Faltu tags remove karna
        if key.lower() in ["success", "status", "count", "limit", "tag", "credit", "query", "meta"]:
            continue
            
        val = str(value).strip() if value else "N/A"
        
        # Address Cleaning
        if key.lower() == "address":
            val = re.sub(r'!!|!NA!', ' ', val)
            val = re.sub(r'\s+', ' ', val).strip()
        
        # Heading ko capitalize aur professional banana (e.g., father_name -> Father_Name)
        clean_key = str(key).replace("_", " ").title().replace(" ", "_")
        clean_data[clean_key] = val.title() if key.lower() in ["name", "fname", "father_name"] else val
        
    # Signature End Me
    clean_data["Dev"] = DEV_TAG
    return clean_data

# === API CALLERS 👀 ===
async def fetch_api_1(num: str) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"http://apis.rootx.run/key=LAKSHIT-RAMDI&term={num}")
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success" and data.get("results"):
                    return sanitize_record(data["results"][0])
        except Exception:
            pass
    return None

async def fetch_api_2(num: str) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"https://nmdllpezcocquamhgpmb.supabase.co/functions/v1/lookup?number={num}")
            if resp.status_code == 200:
                data = resp.json()
                res = data.get("result", {})
                if isinstance(res, dict) and "result" in res:
                    res = res.get("result", {})
                
                results_list = res.get("results", [])
                if results_list and len(results_list) > 0:
                    return sanitize_record(results_list[0])
        except Exception:
            pass
    return None

# === PREMIUM UI FORMATTER 👾 ===
def format_json_response(data: dict, title: str) -> list:
    if not data: 
        return [f"💀 <b>{title}</b>\n<i>No details found for this target. 😾</i>"]
    
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    header = f"👺 <b><u>✦ {title} ✦</u></b>\n"
    
    full_msg = f"{header}```Info\n{json_str}\n```"
    if len(full_msg) < 4000: 
        return [full_msg]
    
    # Message break handler for large data
    return [f"{header}```Info\n{json_str[:3800]}\n```", "<i>...Output truncated due to Telegram limit. ☠️</i>"]

def get_num(text: str):
    match = re.search(r'\b\d{10}\b', str(text))
    return match.group(0) if match else None

# === BOT COMMANDS 🏴‍☠️ ===
@dp.message(Command("start"))
async def start_cmd(m: types.Message):
    await m.answer(
        "👾 <b><u>INTELLIGENCE TERMINAL ONLINE</u></b> 🏴‍☠️\n\n"
        "<b>Commands:</b>\n"
        "▫️ <code>/num 98765XXXXX</code> — <i>Hybrid Auto-Fetch 😸</i>\n"
        "▫️ <code>/num1 98765XXXXX</code> — <i>Server 1 Only 🙂</i>\n"
        "▫️ <code>/num2 98765XXXXX</code> — <i>Server 2 Only 🙃</i>\n"
        "▫️ <code>/bnum 98765XXXXX</code> — <i>Both Servers 👀</i>\n\n"
        "<i>💡 Reply to a number message to auto-trace.</i>"
    )

@dp.message(Command("num1"))
async def num1_cmd(m: types.Message):
    num = get_num(m.text)
    if not num: return await m.reply("⚠️ <i>Ek valid 10-digit number de. 😾</i>")
    
    msg = await m.reply("👀 <i>Tracing API-1...</i>")
    data = await fetch_api_1(num)
    for chunk in format_json_response(data, "API-1 EXTRACT"):
        await msg.edit_text(chunk) if chunk == format_json_response(data, "API-1 EXTRACT")[0] else await m.reply(chunk)

@dp.message(Command("num2"))
async def num2_cmd(m: types.Message):
    num = get_num(m.text)
    if not num: return await m.reply("⚠️ <i>Ek valid 10-digit number de. 😾</i>")
    
    msg = await m.reply("👀 <i>Tracing API-2...</i>")
    data = await fetch_api_2(num)
    for chunk in format_json_response(data, "API-2 EXTRACT"):
        await msg.edit_text(chunk) if chunk == format_json_response(data, "API-2 EXTRACT")[0] else await m.reply(chunk)

@dp.message(Command("num"))
async def num_cmd(m: types.Message):
    num = get_num(m.text)
    if not num: return await m.reply("⚠️ <i>Ek valid 10-digit number de. 😾</i>")
    
    msg = await m.reply("⚡ <i>Executing hybrid search... 👀</i>")
    
    data = await fetch_api_1(num)
    title = "HYBRID EXTRACT (API-1)"
    if not data:
        data = await fetch_api_2(num)
        title = "HYBRID EXTRACT (API-2)"
        
    for chunk in format_json_response(data, title):
        await msg.edit_text(chunk) if chunk == format_json_response(data, title)[0] else await m.reply(chunk)

@dp.message(Command("bnum"))
async def bnum_cmd(m: types.Message):
    num = get_num(m.text)
    if not num: return await m.reply("⚠️ <i>Ek valid 10-digit number do. 😾</i>")
    
    msg = await m.reply("🚀 <i>Brute-forcing both servers concurrently... ☠️</i>")
    
    data1, data2 = await asyncio.gather(fetch_api_1(num), fetch_api_2(num))
    
    chunks1 = format_json_response(data1, "API-1 RESULT")
    chunks2 = format_json_response(data2, "API-2 RESULT")
    
    await msg.edit_text(chunks1[0])
    for c in chunks1[1:]: await m.reply(c)
    for c in chunks2: await m.reply(c)

@dp.message(F.reply_to_message)
async def auto_reply(m: types.Message):
    if m.text and m.text.startswith('/'): return
    
    num = get_num(m.reply_to_message.text)
    if num:
        msg = await m.reply("👀 <i>Target locked from reply. Fetching... 👾</i>")
        data = await fetch_api_1(num)
        title = "AUTO EXTRACT (API-1)"
        if not data:
            data = await fetch_api_2(num)
            title = "AUTO EXTRACT (API-2)"
            
        for chunk in format_json_response(data, title):
            await msg.edit_text(chunk) if chunk == format_json_response(data, title)[0] else await m.reply(chunk)

# === VERCEL ROUTES ===
@app.get("/")
async def root_path():
    return HTMLResponse(
        "<html><body style='background:#0a0a0a; color:#00ff00; font-family:monospace; text-align:center; margin-top:20%;'>"
        "<h1>👾 Server Active & Bot is Running Flawlessly 🏴‍☠️</h1>"
        "<p>Developed by @lakshitpatidar</p></body></html>"
    )

@app.post("/api/webhook")
async def webhook_handler(request: Request):
    try:
        update = Update.model_validate(await request.json(), context={"bot": bot})
        await dp.feed_update(bot, update)
    except Exception:
        pass
    return {"status": "ok"}
            

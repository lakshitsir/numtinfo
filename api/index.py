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

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# === DATA SANITIZER ===
def sanitize_record(raw: dict) -> dict:
    if not isinstance(raw, dict): 
        return {}
        
    clean_data = {}
    ignore_keys = {"success", "status", "count", "limit", "tag", "credit", "query", "meta", "search_time"}
    ordered_keys = ["mobile", "name", "fname", "father_name", "id", "circle", "address", "email", "alt"]
    
    processed_keys = set()
    for k in ordered_keys:
        for raw_k, val in raw.items():
            if raw_k.lower() == k and raw_k.lower() not in ignore_keys:
                clean_val = str(val).strip() if val else "N/A"
                if raw_k.lower() == "address":
                    clean_val = re.sub(r'!!|!NA!', ', ', clean_val)
                    clean_val = re.sub(r'\s+', ' ', clean_val).strip(', ')
                elif raw_k.lower() in ["name", "fname", "father_name"]:
                    clean_val = clean_val.title()
                
                key_name = str(raw_k).replace("_", " ").title().replace(" ", "_")
                clean_data[key_name] = clean_val
                processed_keys.add(raw_k)

    for key, value in raw.items():
        if key.lower() in ignore_keys or key in processed_keys:
            continue
        val = str(value).strip() if value else "N/A"
        key_name = str(key).replace("_", " ").title().replace(" ", "_")
        clean_data[key_name] = val.title() if key.lower() in ["name", "fname"] else val

    clean_data["Dev"] = DEV_TAG
    return clean_data

# === API EXTRACTORS ===
async def fetch_api_1(num: str) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"http://apis.rootx.run/key=LAKSHIT-RAMDI&term={num}", headers=HEADERS)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict) and "results" in data and isinstance(data["results"], list) and len(data["results"]) > 0:
                    return sanitize_record(data["results"][0])
        except Exception:
            pass
    return None

async def fetch_api_2(num: str) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"https://nmdllpezcocquamhgpmb.supabase.co/functions/v1/lookup?number={num}", headers=HEADERS)
            if resp.status_code == 200:
                data = resp.json()
                def deep_search(d):
                    if isinstance(d, dict):
                        if "results" in d and isinstance(d["results"], list) and len(d["results"]) > 0:
                            return sanitize_record(d["results"][0])
                        for k, v in d.items():
                            res = deep_search(v)
                            if res: return res
                    return None
                return deep_search(data)
        except Exception:
            pass
    return None

# === CLEAN MINIMAL AESTHETIC FORMATTER ===
def format_single_response(data: dict, title: str) -> str:
    if not data: 
        return f"<b>✦ {title} </b>\n\n<i>No records found in database.</i> ⚠️"
    
    json_str = json.dumps(data, indent=4, ensure_ascii=False)
    header = f"<b>{title} </b>\n\n"
    code_block = f"<pre><code class=\"language-Info\">\n{json_str}\n</code></pre>"
    
    return f"{header}{code_block}"

def format_dual_response(data1: dict, data2: dict) -> str:
    combined = {
        "Server_1_Result": data1 if data1 else "No record found",
        "Server_2_Result": data2 if data2 else "No record found"
    }
    json_str = json.dumps(combined, indent=4, ensure_ascii=False)
    header = "<b>✦ DUAL SERVER RECORD (COMBINED)</b>\n\n"
    code_block = f"<pre><code class=\"language-Info\">\n{json_str}\n</code></pre>"
    return f"{header}{code_block}"

def get_num(text: str):
    match = re.search(r'\b\d{10}\b', str(text))
    return match.group(0) if match else None

# === BOT COMMANDS ===
@dp.message(Command("start"))
async def start_cmd(m: types.Message):
    await m.answer(
        "<b>✨ Intelligence Terminal Online</b>\n\n"
        "<b>Commands:</b>\n"
        "▫️ <code>/num 98765XXXXX</code> — <i>Hybrid Auto-Fetch</i> ⚡\n"
        "▫️ <code>/num1 98765XXXXX</code> — <i>Server 1 Only</i> 🔍\n"
        "▫️ <code>/num2 98765XXXXX</code> — <i>Server 2 Only</i> 🔍\n"
        "▫️ <code>/bnum 98765XXXXX</code> — <i>Both Servers (Single Msg)</i> 🚀\n\n"
        "<i>💡 Tip: Reply to any number message to auto-trace instantly.</i>"
    )

@dp.message(Command("num1"))
async def num1_cmd(m: types.Message):
    num = get_num(m.text)
    if not num: return await m.reply("<i>Please provide a valid 10-digit number.</i> ⚠️")
    
    msg = await m.reply("<i>Querying Server 1...</i> ⏳")
    data = await fetch_api_1(num)
    await msg.edit_text(format_single_response(data, "SERVER 1 RECORD"))

@dp.message(Command("num2"))
async def num2_cmd(m: types.Message):
    num = get_num(m.text)
    if not num: return await m.reply("<i>Please provide a valid 10-digit number.</i> ⚠️")
    
    msg = await m.reply("<i>Querying Server 2...</i> ⏳")
    data = await fetch_api_2(num)
    await msg.edit_text(format_single_response(data, "SERVER 2 RECORD"))

@dp.message(Command("num"))
async def num_cmd(m: types.Message):
    num = get_num(m.text)
    if not num: return await m.reply("<i>Please provide a valid 10-digit number.</i> ⚠️")
    
    msg = await m.reply("<i>Executing hybrid search...</i> ⚡")
    data = await fetch_api_1(num)
    title = "HYBRID RECORD (SERVER 1)"
    if not data:
        data = await fetch_api_2(num)
        title = "HYBRID RECORD (SERVER 2)"
        
    await msg.edit_text(format_single_response(data, title))

@dp.message(Command("bnum"))
async def bnum_cmd(m: types.Message):
    num = get_num(m.text)
    if not num: return await m.reply("<i>Please provide a valid 10-digit number.</i> ⚠️")
    
    msg = await m.reply("<i>Fetching from both servers simultaneously...</i> 🚀")
    data1, data2 = await asyncio.gather(fetch_api_1(num), fetch_api_2(num))
    
    # Send both in ONE single combined message block
    await msg.edit_text(format_dual_response(data1, data2))

@dp.message(F.reply_to_message)
async def auto_reply(m: types.Message):
    if m.text and m.text.startswith('/'): return
    
    num = get_num(m.reply_to_message.text)
    if num:
        msg = await m.reply("<i>Target identified. Extracting data...</i> ⚡")
        data = await fetch_api_1(num)
        title = "AUTO TRACE (SERVER 1)"
        if not data:
            data = await fetch_api_2(num)
            title = "AUTO TRACE (SERVER 2)"
            
        await msg.edit_text(format_single_response(data, title))

# === VERCEL ROUTES ===
@app.get("/")
async def root_path():
    return HTMLResponse(
        "<html><body style='background:#0f0f0f; color:#00ff88; font-family:monospace; text-align:center; margin-top:15%;'>"
        "<h2>[ ✓ ] SECURE BOT ONLINE</h2>"
        "<p style='color:#777777;'>Maintained by @lakshitpatidar</p></body></html>"
    )

@app.post("/api/webhook")
async def webhook_handler(request: Request):
    try:
        update = Update.model_validate(await request.json(), context={"bot": bot})
        await dp.feed_update(bot, update)
    except Exception:
        pass
    return {"status": "ok"}
                    

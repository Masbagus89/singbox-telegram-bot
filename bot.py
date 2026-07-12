import os
import logging
import asyncio
import json
import base64
import urllib.parse
from aiohttp import web
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = '8026920485:AAHBe399WAYCpXvtvy_MY8ecsHmzxbIxze4'

def parse_vless_to_singbox(vless_link):
    """Mengubah link Vless menjadi format JSON Sing-box secara internal tanpa API luar"""
    try:
        parsed = urllib.parse.urlparse(vless_link)
        userinfo, host_port = parsed.netloc.split('@')
        uuid = userinfo
        address, port = host_port.split(':')
        
        query = urllib.parse.parse_qs(parsed.query)
        path = query.get('path', [''])[0]
        host = query.get('host', [''])[0]
        sni = query.get('sni', [''])[0]
        security = query.get('security', ['none'])[0]
        
        # Struktur dasar outbound Sing-box
        singbox_config = {
            "outbounds": [
                {
                    "type": "vless",
                    "tag": parsed.fragment if parsed.fragment else "Vless-Outbound",
                    "server": address,
                    "server_port": int(port),
                    "uuid": uuid,
                    "flow": "",
                    "tls": {
                        "enabled": True if security in ['tls', 'reality'] else False,
                        "server_name": sni if sni else host,
                        "insecure": True
                    },
                    "transport": {
                        "type": "ws" if path or host else "tcp",
                        "path": path,
                        "headers": {
                            "Host": host
                        } if host else {}
                    }
                }
            ]
        }
        return json.dumps(singbox_config, indent=2)
    except Exception as e:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! Kirimkan link Vless Anda.\n"
        "Saya akan langsung mengubahnya menjadi format Sing-box secara instan dan aman!"
    )

async def convert_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    if not user_text.startswith('vless://'):
        await update.message.reply_text("❌ Untuk saat ini, kirimkan format link vless:// terlebih dahulu.")
        return

    await update.message.reply_text("⏳ Sedang memproses konversi internal ke Sing-box...")
    
    # Konversi langsung di dalam memori tanpa request internet
    result_text = parse_vless_to_singbox(user_text)

    if result_text:
        if len(result_text) > 4000:
            file_name = "singbox.json"
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(result_text)
            with open(file_name, "rb") as f:
                await update.message.reply_document(document=f, filename="singbox.json", caption="✅ Berhasil Konversi!")
        else:
            await update.message.reply_text(f"✅ **Hasil Sing-box:**\n\n```json\n{result_text}\n```", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Gagal memproses format link tersebut secara internal.")

async def handle_dummy(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_dummy)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    asyncio.create_task(start_web_server())
    
    # Jalankan Bot Telegram dengan Proxy PythonAnywhere
    application = (
        Application.builder()
        .token(TOKEN)
        .proxy_url("http://proxy.server:3128")
        .get_updates_proxy_url("http://proxy.server:3128")
        .build()
    )
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, convert_link))
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main())

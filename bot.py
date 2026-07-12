import os
import logging
import asyncio
import requests
import urllib.parse
from aiohttp import web
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = '8026920485:AAHBe399WAYCpXvtvy_MY8ecsHmzxbIxze4'
SUBCONVERTER_API = 'https://sub-converter-dyeq.onrender.com/sub'

# Proxy khusus PythonAnywhere untuk requests biasa
PROXIES = {
    "http": "http://proxy.server:3128",
    "https": "http://proxy.server:3128"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! Kirimkan link Vless, Trojan, atau Vmess Anda.\n"
        "Saya akan mengubahnya menjadi format Sing-box menggunakan API pribadi Anda."
    )

async def convert_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    if not any(user_text.startswith(proto) for proto in ['vless://', 'vmess://', 'trojan://', 'ss://', 'http']):
        await update.message.reply_text("❌ Format link tidak valid.")
        return

    await update.message.reply_text("⏳ Sedang memproses konversi ke Sing-box...")
    encoded_url = urllib.parse.quote_plus(user_text)
    api_url = f"{SUBCONVERTER_API}?target=singbox&url={encoded_url}"

    try:
        # Menambahkan proxies agar bisa menembus batas free tier PythonAnywhere saat menembak API luar
        response = requests.get(api_url, proxies=PROXIES, timeout=20)
        if response.status_code == 200:
            result_text = response.text
            if len(result_text) > 4000:
                file_name = "singbox.json"
                with open(file_name, "w", encoding="utf-8") as f:
                    f.write(result_text)
                with open(file_name, "rb") as f:
                    await update.message.reply_document(document=f, filename="singbox.json", caption="✅ Berhasil!")
            else:
                await update.message.reply_text(f"✅ **Hasil:**\n\n```json\n{result_text}\n```", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ Server API merespon error ({response.status_code}).")
    except Exception as e:
        logging.error(f"Error saat konversi: {e}")
        await update.message.reply_text("❌ Gagal menghubungi server sub-converter.")

# Server dummy (tetap dipertahankan agar tidak bentrok dengan sisa kode bawaan)
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
    logging.info(f"Dummy web server started on port {port}")

async def main():
    # Jalankan web server dummy secara asinkron
    asyncio.create_task(start_web_server())
    
    # Jalankan Bot Telegram dengan integrasi proxy PythonAnywhere
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
    
    # Jaga agar loop tetap berjalan nonstop
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main())

import os
import logging
import requests
import urllib.parse
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Token akan ditarik otomatis dari pengaturan Render nanti
TOKEN = os.getenv('TELEGRAM_TOKEN')

# API Server Render Anda yang sudah aktif
SUBCONVERTER_API = 'https://sub-converter-dyeq.onrender.com/sub' 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! Kirimkan link Vless, Trojan, atau Vmess Anda.\n"
        "Saya akan mengubahnya menjadi format Sing-box menggunakan API pribadi Anda."
    )

async def convert_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    
    if not any(user_text.startswith(proto) for proto in ['vless://', 'vmess://', 'trojan://', 'ss://', 'http']):
        await update.message.reply_text("❌ Format link tidak valid. Kirim link vless/vmess/trojan.")
        return

    await update.message.reply_text("⏳ Sedang memproses konversi ke Sing-box...")
    encoded_url = urllib.parse.quote_plus(user_text)
    api_url = f"{SUBCONVERTER_API}?target=singbox&url={encoded_url}"

    try:
        response = requests.get(api_url, timeout=20)
        if response.status_code == 200:
            result_text = response.text
            if len(result_text) > 4000:
                file_name = "singbox.json"
                with open(file_name, "w", encoding="utf-8") as f:
                    f.write(result_text)
                with open(file_name, "rb") as f:
                    await update.message.reply_document(document=f, filename="singbox.json", caption="✅ Berhasil dikonversi!")
            else:
                await update.message.reply_text(f"✅ **Hasil:**\n\n```json\n{result_text}\n```", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ Server API merespon error ({response.status_code}).")
    except Exception as e:
        await update.message.reply_text("❌ Gagal menghubungi server sub-converter.")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, convert_link))
    application.run_polling()

if __name__ == '__main__':
    main()

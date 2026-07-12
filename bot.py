import logging
import json
import urllib.parse
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Setup Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = '8026920485:AAHBe399WAYCpXvtvy_MY8ecsHmzxbIxze4'

def parse_vless_to_singbox(vless_link):
    """Mengubah link Vless menjadi format JSON Sing-box yang valid & siap konek"""
    try:
        # Decode url terlebih dahulu untuk membersihkan karakter seperti %2F dan %3F
        decoded_link = urllib.parse.unquote(vless_link)
        parsed = urllib.parse.urlparse(decoded_link)
        
        userinfo, host_port = parsed.netloc.split('@')
        uuid = userinfo
        address, port = host_port.split(':')
        
        query = urllib.parse.parse_qs(parsed.query)
        
        # Mengambil nilai mentah dari query string untuk mengamankan path utuh
        raw_path = "/"
        if parsed.query:
            # Mencari parameter path jika ada, atau mengambil seluruh query jika itu bagian dari path worker
            if 'path' in query:
                raw_path = query['path'][0]
            elif 'mode' in query:
                raw_path = f"/?{parsed.query}"

        host = query.get('host', [''])[0]
        sni = query.get('sni', [''])[0]
        security = query.get('security', ['none'])[0]
        
        # Formatter standar Sing-box Outbound yang valid
        singbox_config = {
            "outbounds": [
                {
                    "type": "vless",
                    "tag": parsed.fragment if parsed.fragment else "Vless-Outbound",
                    "server": host if host else address,
                    "server_port": int(port),
                    "uuid": uuid,
                    "flow": "",
                    "tls": {
                        "enabled": True if security in ['tls', 'reality'] else False,
                        "server_name": sni if sni else host,
                        "insecure": True
                    },
                    "transport": {
                        "type": "ws",
                        "path": raw_path,
                        "headers": {
                            "Host": host if host else address
                        }
                    }
                }
            ]
        }
        return json.dumps(singbox_config, indent=2)
    except Exception as e:
        logging.error(f"Error parsing Vless: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! Kirimkan link Vless Anda.\n"
        "Saya akan langsung mengubahnya menjadi format Sing-box secara instan!"
    )

async def convert_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    if not user_text.startswith('vless://'):
        await update.message.reply_text("❌ Mohon kirimkan format link yang diawali dengan vless://")
        return

    await update.message.reply_text("⏳ Sedang memproses konversi...")
    result_text = parse_vless_to_singbox(user_text)

    if result_text:
        await update.message.reply_text(f"✅ **Hasil Sing-box:**\n\n```json\n{result_text}\n```", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Gagal memproses format link tersebut.")

def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, convert_link))
    
    application.run_polling()

if __name__ == '__main__':
    main()

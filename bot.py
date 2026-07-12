import os
import logging
import json
import urllib.parse
import io
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Setup Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = '8026920485:AAHBe399WAYCpXvtvy_MY8ecsHmzxbIxze4'

def generate_singbox_from_template(vless_link):
    """Menghasilkan file konfigurasi sing-box yang kompatibel dengan versi terbaru"""
    try:
        decoded_link = urllib.parse.unquote(vless_link)
        parsed = urllib.parse.urlparse(decoded_link)
        
        userinfo = parsed.netloc.split('@')[0]
        address = parsed.netloc.split('@')[1].split(':')[0]
        
        query = urllib.parse.parse_qs(parsed.query)
        host = query.get('host', [''])[0]
        proxyip = query.get('proxyip', [''])[0]
        
        full_path = f"/?mode=proxy&proxyip={proxyip}"
        vless_tag = "🇺🇸 US_GoogleLLC"
        
        vless_outbound = {
            "type": "vless",
            "tag": vless_tag,
            "server": address,
            "server_port": 443,
            "uuid": userinfo,
            "packet_encoding": "xudp",
            "tls": {
                "enabled": True,
                "server_name": host,
                "insecure": True
            },
            "transport": {
                "type": "ws",
                "path": full_path,
                "headers": {"Host": host}
            }
        }
        
        template = {
            "log": {"level": "info", "timestamp": True},
            "dns": {
                "servers": [
                    {"tag": "local", "type": "local"},
                    {"tag": "ggdns", "type": "https", "server": "dns.google", "detour": "Proxy"}
                ],
                "rules": [{"outbound": "any", "server": "local"}],
                "final": "ggdns"
            },
            "inbounds": [
                {
                    "tag": "tun-in", "type": "tun", "address": ["172.19.0.0/30"], 
                    "auto_route": True, "strict_route": True, 
                    "platform": {"http_proxy": {"enabled": True, "server": "127.0.0.1", "server_port": 7890}}
                },
                {"tag": "mixed-in", "type": "mixed", "listen": "127.0.0.1", "listen_port": 7890}
            ],
            "outbounds": [
                {"tag": "Proxy", "type": "selector", "outbounds": ["auto", vless_tag, "direct"]},
                {"tag": "auto", "type": "urltest", "outbounds": [vless_tag], "url": "http://www.gstatic.com/generate_204", "interval": "10m", "tolerance": 50},
                {"type": "direct", "tag": "direct"},
                vless_outbound
            ],
            "route": {
                "final": "Proxy",
                "rules": [{"inbound": ["tun-in", "mixed-in"], "action": "sniff"}]
            }
        }

        return json.dumps(template, indent=2)
    except Exception as e:
        logging.error(f"Error compiling config: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Kirim link Vless Anda untuk mendapatkan config yang sudah diperbaiki.")

async def convert_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    if not user_text.startswith('vless://'):
        await update.message.reply_text("Format link harus diawali vless://")
        return

    result_text = generate_singbox_from_template(user_text)

    if result_text:
        file_stream = io.BytesIO(result_text.encode('utf-8'))
        await update.message.reply_document(
            document=file_stream,
            filename='singbox_1.13.json',
            caption="✅ Konfigurasi diperbarui (Tanpa deprecated warning)."
        )

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, convert_link))
    application.run_polling()

if __name__ == '__main__':
    main()

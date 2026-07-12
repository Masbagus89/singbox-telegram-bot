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
        
        # Parse UUID dan address
        userinfo = parsed.netloc.split('@')[0]
        address = parsed.netloc.split('@')[1].split(':')[0]
        
        # Parse query parameters
        query = urllib.parse.parse_qs(parsed.query)
        host = query.get('host', [''])[0]
        proxyip = query.get('proxyip', [''])[0]
        
        # Buat path untuk WebSocket
        if proxyip:
            full_path = f"/?mode=proxy&proxyip={proxyip}"
        else:
            full_path = "/"
        
        # Tag untuk outbound
        vless_tag = "🇺🇸 US_GoogleLLC"
        
        # Konfigurasi outbound VLESS
        vless_outbound = {
            "type": "vless",
            "tag": vless_tag,
            "server": address,
            "server_port": 443,
            "uuid": userinfo,
            "flow": "xtls-rprx-vision",
            "packet_encoding": "xudp",
            "tls": {
                "enabled": True,
                "server_name": host,
                "insecure": True,
                "utls": {
                    "enabled": True,
                    "fingerprint": "chrome"
                }
            },
            "transport": {
                "type": "ws",
                "path": full_path,
                "headers": {
                    "Host": host
                }
            }
        }
        
        # Template lengkap dengan HTTP clients yang benar
        template = {
            "log": {
                "level": "info",
                "timestamp": True
            },
            "experimental": {
                "clash_api": {
                    "external_controller": "127.0.0.1:9090",
                    "external_ui": "ui",
                    "secret": "",
                    "external_ui_download_url": "https://gh-proxy.com/https://github.com/MetaCubeX/metacubexd/archive/refs/heads/gh-pages.zip",
                    "external_ui_download_detour": "direct",
                    "default_mode": "rule"
                },
                "cache_file": {
                    "enabled": True,
                    "store_fakeip": True,
                    "store_dns": True
                }
            },
            "dns": {
                "servers": [
                    {
                        "tag": "local",
                        "type": "local"
                    },
                    {
                        "tag": "hosts",
                        "type": "hosts",
                        "predefined": {
                            "dns.alidns.com": [
                                "223.5.5.5",
                                "223.6.6.6"
                            ],
                            "dns.google": [
                                "8.8.8.8",
                                "8.8.4.4"
                            ]
                        }
                    },
                    {
                        "tag": "alidns",
                        "type": "https",
                        "server": "dns.alidns.com",
                        "domain_resolver": "hosts"
                    },
                    {
                        "tag": "ggdns",
                        "type": "https",
                        "server": "dns.google",
                        "domain_resolver": "hosts",
                        "detour": "Proxy"
                    },
                    {
                        "tag": "fakeip",
                        "type": "fakeip",
                        "inet4_range": "198.18.0.0/15",
                        "inet6_range": "fc00::/18"
                    }
                ],
                "rules": [
                    {
                        "clash_mode": "direct",
                        "server": "local"
                    },
                    {
                        "clash_mode": "global",
                        "server": "ggdns"
                    },
                    {
                        "query_type": [
                            "A",
                            "AAAA"
                        ],
                        "server": "fakeip"
                    },
                    {
                        "rule_set": "geosite-cn",
                        "server": "local"
                    },
                    {
                        "action": "evaluate",
                        "server": "alidns"
                    },
                    {
                        "match_response": True,
                        "rule_set": "geoip-cn",
                        "action": "respond"
                    }
                ],
                "final": "ggdns",
                "strategy": "prefer_ipv4"
            },
            "inbounds": [
                {
                    "tag": "tun-in",
                    "type": "tun",
                    "address": [
                        "172.19.0.0/30",
                        "fdfe:dcba:9876::0/126"
                    ],
                    "stack": "system",
                    "auto_route": True,
                    "strict_route": True,
                    "platform": {
                        "http_proxy": {
                            "enabled": True,
                            "server": "127.0.0.1",
                            "server_port": 7890
                        }
                    }
                },
                {
                    "tag": "mixed-in",
                    "type": "mixed",
                    "listen": "127.0.0.1",
                    "listen_port": 7890
                }
            ],
            "http_clients": [
                {
                    "tag": "default",
                    "detour": "Proxy"
                },
                {
                    "tag": "direct",
                    "detour": "direct"
                }
            ],
            "outbounds": [
                {
                    "tag": "Proxy",
                    "type": "selector",
                    "outbounds": [
                        "auto",
                        vless_tag,
                        "direct"
                    ]
                },
                {
                    "tag": "auto",
                    "type": "urltest",
                    "outbounds": [
                        vless_tag
                    ],
                    "url": "http://www.gstatic.com/generate_204",
                    "interval": "10m",
                    "tolerance": 50
                },
                {
                    "type": "direct",
                    "tag": "direct"
                },
                vless_outbound
            ],
            "route": {
                "default_domain_resolver": {
                    "server": "local"
                },
                "auto_detect_interface": True,
                "final": "Proxy",
                "rules": [
                    {
                        "inbound": [
                            "tun-in",
                            "mixed-in"
                        ],
                        "action": "sniff"
                    },
                    {
                        "type": "logical",
                        "mode": "or",
                        "rules": [
                            {
                                "port": 53
                            },
                            {
                                "protocol": "dns"
                            }
                        ],
                        "action": "hijack-dns"
                    },
                    {
                        "ip_is_private": True,
                        "outbound": "direct"
                    },
                    {
                        "rule_set": "geosite-cn",
                        "outbound": "direct"
                    },
                    {
                        "rule_set": "geoip-cn",
                        "outbound": "direct"
                    }
                ],
                "rule_set": [
                    {
                        "tag": "geoip-cn",
                        "type": "remote",
                        "format": "binary",
                        "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geoip/cn.srs",
                        "http_client": "default"
                    },
                    {
                        "tag": "geosite-cn",
                        "type": "remote",
                        "format": "binary",
                        "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/cn.srs",
                        "http_client": "default"
                    }
                ]
            }
        }

        return json.dumps(template, indent=2)
    except Exception as e:
        logging.error(f"Error compiling config: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📡 Kirim link Vless Anda untuk mendapatkan config sing-box yang sudah diperbaiki.\n\n"
        "Contoh: vless://uuid@server.com:443?host=server.com&proxyip=proxyip\n\n"
        "✨ Fitur:\n"
        "• TUN & Mixed inbound\n"
        "• DNS dengan FakeIP\n"
        "• Clash API support\n"
        "• Auto route & strict route"
    )

async def convert_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    if not user_text.startswith('vless://'):
        await update.message.reply_text("❌ Format link harus diawali vless://")
        return

    await update.message.reply_text("⏳ Sedang memproses konfigurasi...")
    
    result_text = generate_singbox_from_template(user_text)

    if result_text:
        file_stream = io.BytesIO(result_text.encode('utf-8'))
        await update.message.reply_document(
            document=file_stream,
            filename='singbox_config.json',
            caption="✅ Konfigurasi berhasil dibuat!\n\n"
                   "📌 Cara penggunaan:\n"
                   "1. Buka aplikasi sing-box\n"
                   "2. Import file config\n"
                   "3. Start service\n\n"
                   "⚠️ Pastikan rule-set sudah terdownload sebelum start"
        )
    else:
        await update.message.reply_text("❌ Gagal membuat konfigurasi. Periksa format link Anda.")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, convert_link))
    application.run_polling()

if __name__ == '__main__':
    main()

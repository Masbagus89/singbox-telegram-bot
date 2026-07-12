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
    """Mengekstrak Vless dan menggabungkannya ke dalam template Sing-box lengkap"""
    try:
        # 1. Parsing Link Vless
        decoded_link = urllib.parse.unquote(vless_link)
        parsed = urllib.parse.urlparse(decoded_link)
        
        userinfo, host_port = parsed.netloc.split('@')
        uuid = userinfo
        address, port = host_port.split(':')
        
        query = urllib.parse.parse_qs(parsed.query)
        
        raw_path = "/"
        if parsed.query:
            if 'path' in query:
                raw_path = query['path'][0]
            elif 'mode' in query:
                raw_path = f"/?{parsed.query}"

        host = query.get('host', [''])[0]
        sni = query.get('sni', [''])[0]
        security = query.get('security', ['none'])[0]
        
        vless_tag = parsed.fragment if parsed.fragment else "Vless-Converted"
        
        # 2. Struktur Objek Outbound Vless
        vless_outbound = {
            "type": "vless",
            "tag": vless_tag,
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
        
        # 3. Base Template Lengkap Anda
        template = {
            "log": {"level": "info", "timestamp": True},
            "experimental": {
                "clash_api": {
                    "external_controller": "127.0.0.1:9090",
                    "external_ui": "ui",
                    "secret": "",
                    "external_ui_download_url": "https://gh-proxy.com/https://github.com/MetaCubeX/metacubexd/archive/refs/heads/gh-pages.zip",
                    "external_ui_download_detour": "direct",
                    "default_mode": "rule"
                },
                "cache_file": {"enabled": True, "store_fakeip": True, "store_dns": True}
            },
            "dns": {
                "servers": [
                    {"tag": "local", "type": "local"},
                    {"tag": "hosts", "type": "hosts", "predefined": {"dns.alidns.com": ["223.5.5.5", "223.6.6.6"], "dns.google": ["8.8.8.8", "8.8.4.4"]}},
                    {"tag": "alidns", "type": "https", "server": "dns.alidns.com", "domain_resolver": "hosts"},
                    {"tag": "ggdns", "type": "https", "server": "dns.google", "domain_resolver": "hosts", "detour": "Proxy"},
                    {"tag": "fakeip", "type": "fakeip", "inet4_range": "198.18.0.0/15", "inet6_range": "fc00::/18"}
                ],
                "rules": [
                    {"clash_mode": "direct", "server": "local"},
                    {"clash_mode": "global", "server": "ggdns"},
                    {"query_type": ["A", "AAAA"], "server": "fakeip"},
                    {"rule_set": "geosite-cn", "server": "local"},
                    {"action": "evaluate", "server": "alidns"},
                    {"match_response": True, "rule_set": "geoip-cn", "action": "respond"}
                ],
                "final": "ggdns",
                "strategy": "prefer_ipv4"
            },
            "inbounds": [
                {"tag": "tun-in", "type": "tun", "address": ["172.19.0.0/30", "fdfe:dcba:9876::0/126"], "stack": "system", "auto_route": True, "strict_route": True, "platform": {"http_proxy": {"enabled": True, "server": "127.0.0.1", "server_port": 7890}}},
                {"tag": "mixed-in", "type": "mixed", "listen": "127.0.0.1", "listen_port": 7890}
            ],
            "outbounds": [],
            "http_clients": [
                {"tag": "default", "detour": "Proxy"},
                {"tag": "direct", "detour": "direct"}
            ],
            "route": {
                "default_domain_resolver": {"server": "local"},
                "auto_detect_interface": True,
                "final": "Proxy",
                "rules": [
                    {"inbound": ["tun-in", "mixed-in"], "action": "sniff"},
                    {"type": "logical", "mode": "or", "rules": [{"port": 53}, {"protocol": "dns"}], "action": "hijack-dns"},
                    {"rule_set": "geosite-category-ads-all", "clash_mode": "rule", "action": "reject"},
                    {"rule_set": "geosite-category-ads-all", "clash_mode": "global", "outbound": "Proxy"},
                    {"clash_mode": "direct", "outbound": "direct"},
                    {"clash_mode": "global", "outbound": "Proxy"},
                    {"domain": ["clash.razord.top", "yacd.metacubex.one", "yacd.haishan.me", "d.metacubex.one"], "outbound": "direct"},
                    {"ip_is_private": True, "outbound": "direct"},
                    {"rule_set": "geosite-openai", "outbound": "OpenAI"},
                    {"rule_set": ["geosite-youtube", "geoip-google", "geosite-google", "geosite-github"], "outbound": "Google"},
                    {"rule_set": ["geoip-telegram", "geosite-telegram"], "outbound": "Telegram"},
                    {"rule_set": ["geoip-twitter", "geosite-twitter"], "outbound": "Twitter"},
                    {"rule_set": ["geoip-facebook", "geosite-facebook"], "outbound": "Facebook"},
                    {"rule_set": "geosite-bilibili", "outbound": "BiliBili"},
                    {"rule_set": "geosite-bahamut", "outbound": "Bahamut"},
                    {"rule_set": "geosite-spotify", "outbound": "Spotify"},
                    {"rule_set": "geosite-tiktok", "outbound": "TikTok"},
                    {"rule_set": ["geoip-netflix", "geosite-netflix"], "outbound": "Netflix"},
                    {"rule_set": "geosite-disney", "outbound": "Disney+"},
                    {"rule_set": ["geoip-apple", "geosite-apple", "geosite-amazon"], "outbound": "Apple"},
                    {"rule_set": "geosite-microsoft", "outbound": "Microsoft"},
                    {"rule_set": ["geosite-category-games", "geosite-dmm"], "outbound": "Games"},
                    {"rule_set": ["geosite-hbo", "geosite-primevideo"], "outbound": "Streaming"},
                    {"rule_set": "geosite-geolocation-!cn", "outbound": "Global"},
                    {"rule_set": ["geoip-cn", "geosite-cn"], "outbound": "China"}
                ],
                "rule_set": [
                    {"tag": "geosite-category-ads-all", "type": "remote", "format": "binary", "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/category-ads-all.srs", "http_client": "default"},
                    {"tag": "geosite-openai", "type": "remote", "format": "binary", "url": "https://gh-proxy.com/raw.githubusercontent.com/Toperlock/sing-box-geosite/main/rule/OpenAI.srs", "http_client": "default"},
                    {"tag": "geosite-youtube", "type": "remote", "format": "binary", "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/youtube.srs", "http_client": "default"},
                    {"tag": "geoip-google", "type": "remote", "format": "binary", "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geoip/google.srs", "http_client": "default"},
                    {"tag": "geosite-google", "type": "remote", "format": "binary", "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/google.srs", "http_client": "default"},
                    {"tag": "geosite-github", "type": "remote", "format": "binary", "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/github.srs", "http_client": "default"},
                    {"tag": "geoip-telegram", "type": "remote", "format": "binary", "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geoip/telegram.srs", "http_client": "default"},
                    {"tag": "geosite-telegram", "type": "remote", "format": "binary", "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/telegram.srs", "http_client": "default"},
                    {"tag": "geoip-twitter", "type": "remote", "format": "binary", "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geoip/twitter.srs", "http_client": "default"},
                    {"tag": "geosite-twitter", "type": "remote", "format": "binary", "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/twitter.srs", "http_client": "default"},
                    {"tag": "geoip-facebook", "type": "remote", "format": "binary", "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geoip/facebook.srs", "http_client": "default"},
                    {"tag": "geosite-facebook", "type": "remote", "format": "binary", "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/facebook.srs", "http_client": "default"},
                    {"tag": "geosite-bilibili", "type": "remote", "format": "binary", "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/bilibili.srs", "http_client": "default"},
                    {"tag": "geosite-bahamut", "type": "remote", "format": "binary", "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/bahamut.srs", "http_client": "default"},
                    {"tag": "geosite-spotify", "type": "remote", "format": "binary", "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/spotify.srs", "http_client": "default"},
                    {"tag": "geosite-tiktok", "type": "remote", "format": "binary", "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/tiktok.srs", "http_client": "default"},
                    {"tag": "geoip-netflix", "type": "remote", "format": "binary", "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geoip/netflix.srs", "http_client": "default"},
                    {"tag": "geosite-netflix", "type": "remote", "format": "binary", "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/netflix.srs", "http_client": "default"},
                    {"tag": "geosite-disney", "type": "remote", "format": "binary", "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/disney.srs", "http_client": "default"},
                    {"tag": "geoip-apple", "type": "remote", "format": "binary", "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo-lite/geoip/apple.srs", "http_client": "default"},
                    {"tag": "geosite-apple", "type": "remote", "format": "binary", "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/apple.srs", "http_client": "default"},
                    {"tag": "geosite-amazon", "type": "remote", "format": "binary", "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/amazon.srs", "http_client": "default"},
                    {"tag": "geosite-microsoft", "type": "remote", "format": "binary", "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/microsoft.srs", "http_client": "default"},
                    {"tag": "geosite-category-games", "type": "remote", "format": "binary", "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/category-games.srs", "http_client": "default"},
                    {"tag": "geosite-dmm", "type": "remote", "format": "binary", "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/dmm.srs", "http_client": "default"},
                    {"tag": "geosite-hbo", "type": "remote", "format": "binary", "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/hbo.srs", "http_client": "default"},
                    {"tag": "geosite-primevideo", "type": "remote", "format": "binary", "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/primevideo.srs", "http_client": "default"},
                    {"tag": "geosite-geolocation-!cn", "type": "remote", "format": "binary", "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/geolocation-!cn.srs", "http_client": "default"},
                    {"tag": "geoip-cn", "type": "remote", "format": "binary", "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geoip/cn.srs", "http_client": "default"},
                    {"tag": "geosite-cn", "type": "remote", "format": "binary", "url": "https://gh-proxy.com/raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/cn.srs", "http_client": "default"}
                ]
            }
        }

        # 4. Injeksi Akun Dinamis ke Selector Group
        static_outbounds = [
            {"tag": "Proxy", "type": "selector", "outbounds": [vless_tag, "auto", "direct"]},
            {"tag": "OpenAI", "type": "selector", "outbounds": [vless_tag, "TaiWan", "Singapore", "Japan", "America", "Others"], "default": "America"},
            {"tag": "Google", "type": "selector", "outbounds": [vless_tag, "HongKong", "TaiWan", "Singapore", "Japan", "America", "Others"]},
            {"tag": "Telegram", "type": "selector", "outbounds": [vless_tag, "HongKong", "TaiWan", "Singapore", "Japan", "America", "Others"]},
            {"tag": "Twitter", "type": "selector", "outbounds": [vless_tag, "HongKong", "TaiWan", "Singapore", "Japan", "America", "Others"]},
            {"tag": "Facebook", "type": "selector", "outbounds": [vless_tag, "HongKong", "TaiWan", "Singapore", "Japan", "America", "Others"]},
            {"tag": "BiliBili", "type": "selector", "outbounds": ["direct", vless_tag, "HongKong", "TaiWan"]},
            {"tag": "Bahamut", "type": "selector", "outbounds": ["TaiWan", "Proxy"]},
            {"tag": "Spotify", "type": "selector", "outbounds": [vless_tag, "HongKong", "TaiWan", "Singapore", "Japan", "America", "Others"], "default": "America"},
            {"tag": "TikTok", "type": "selector", "outbounds": [vless_tag, "HongKong", "TaiWan", "Singapore", "Japan", "America"], "default": "America"},
            {"tag": "Netflix", "type": "selector", "outbounds": [vless_tag, "HongKong", "TaiWan", "Singapore", "Japan", "America", "Others"]},
            {"tag": "Disney+", "type": "selector", "outbounds": [vless_tag, "HongKong", "TaiWan", "Singapore", "Japan", "America", "Others"]},
            {"tag": "Apple", "type": "selector", "outbounds": ["direct", vless_tag, "HongKong", "TaiWan", "Singapore", "Japan", "America", "Others"]},
            {"tag": "Microsoft", "type": "selector", "outbounds": ["direct", vless_tag, "HongKong", "TaiWan", "Singapore", "Japan", "America", "Others"]},
            {"tag": "Games", "type": "selector", "outbounds": ["direct", vless_tag, "HongKong", "TaiWan", "Singapore", "Japan", "America", "Others"], "default": "Japan"},
            {"tag": "Streaming", "type": "selector", "outbounds": [vless_tag, "HongKong", "TaiWan", "Singapore", "Japan", "America", "Others"]},
            {"tag": "Global", "type": "selector", "outbounds": [vless_tag, "HongKong", "TaiWan", "Singapore", "Japan", "America", "Others", "direct"]},
            {"tag": "China", "type": "selector", "outbounds": ["direct", "Proxy"]},
            {"tag": "HongKong", "type": "selector", "outbounds": [vless_tag, "direct"]},
            {"tag": "TaiWan", "type": "selector", "outbounds": [vless_tag, "direct"]},
            {"tag": "Singapore", "type": "selector", "outbounds": [vless_tag, "direct"]},
            {"tag": "Japan", "type": "selector", "outbounds": [vless_tag, "direct"]},
            {"tag": "America", "type": "selector", "outbounds": [vless_tag, "direct"]},
            {"tag": "Others", "type": "selector", "outbounds": [vless_tag, "direct"]},
            {"tag": "auto", "type": "urltest", "outbounds": [vless_tag, "direct"], "url": "http://www.gstatic.com/generate_204", "interval": "10m", "tolerance": 50},
            {"type": "direct", "tag": "direct"},
            vless_outbound
        ]

        template["outbounds"] = static_outbounds
        return json.dumps(template, indent=2)
    except Exception as e:
        logging.error(f"Error compiling config: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! Kirimkan link Vless Anda.\n"
        "Saya akan buatkan file konfigurasi singbox_1.13.json lengkap yang siap diunduh dan dipakai!"
    )

async def convert_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    if not user_text.startswith('vless://'):
        await update.message.reply_text("❌ Mohon kirimkan format link yang diawali dengan vless://")
        return

    await update.message.reply_text("⏳ Sedang memproses dan membuat file Sing-box...")
    
    result_text = generate_singbox_from_template(user_text)

    if result_text:
        # Mengubah string JSON menjadi file biner di dalam memori RAM (tanpa mengotori penyimpanan server)
        file_stream = io.BytesIO(result_text.encode('utf-8'))
        file_stream.name = 'singbox_1.13.json'
        
        # Kirim hasil konversi langsung berupa file dokumen yang bisa diunduh
        await update.message.reply_document(
            document=file_stream,
            filename='singbox_1.13.json',
            caption="✅ **Konversi Berhasil!**\nSilakan unduh file konfigurasi di atas untuk langsung di-import ke aplikasi Sing-box Anda.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ Gagal menyusun file konfigurasi.")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, convert_link))
    application.run_polling()

if __name__ == '__main__':
    main()

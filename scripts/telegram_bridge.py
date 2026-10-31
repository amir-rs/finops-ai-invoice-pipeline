#!/usr/bin/env python3
"""
Telegram Bot Live Bridge for n8n Autonomous FinOps Pipeline
Listens for live messages, invoice photos, and /report commands
"""
from Telegram users and forwards them straight to the n8n pipeline.
"""

import sys
import io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import builtins
orig_print = builtins.print
def print(*args, **kwargs):
    kwargs.setdefault('flush', True)
    orig_print(*args, **kwargs)

import time
import json
import urllib.request
import urllib.error
import os
import re
from datetime import datetime

import socket

def setup_global_proxy():
    proxies = {}
    if os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy"):
        p = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
        proxies = {"http": p, "https": p}
    else:
        candidates = ["http://127.0.0.1:10808", "http://127.0.0.1:10809", "http://127.0.0.1:7890", "http://127.0.0.1:2081"]
        for c in candidates:
            try:
                host, port = c.replace("http://", "").split(":")
                with socket.create_connection((host, int(port)), timeout=0.3):
                    proxies = {"http": c, "https": c}
                    break
            except Exception:
                pass
    if proxies:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler(proxies))
        urllib.request.install_opener(opener)
        return list(proxies.values())[0]
    return None

detected_proxy = setup_global_proxy()

try:
    from ai_vision_service import download_telegram_file, analyze_invoice_with_ai, evaluate_and_format_response
except ImportError:
    from scripts.ai_vision_service import download_telegram_file, analyze_invoice_with_ai, evaluate_and_format_response

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
def load_env():
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()

load_env()

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
N8N_WEBHOOK = os.environ.get("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/process-invoice")

print("=" * 60)
print("🤖 Telegram Bot Polling Bridge for n8n FinOps Pipeline")
print(f"📌 Bot Token: {BOT_TOKEN[:10]}...{BOT_TOKEN[-5:]}")
print(f"🎯 Target Webhook: {N8N_WEBHOOK}")
print("=" * 60)

def tg_request(method, params=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    data = None
    headers = {"User-Agent": "n8n-Telegram-Bridge/1.0"}
    if params:
        data = json.dumps(params).encode('utf-8')
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return {"ok": False, "error": str(e)}

def forward_to_n8n(payload):
    # Try both Production webhook and Test webhook dynamically
    candidates = [
        N8N_WEBHOOK,
        "http://localhost:5678/webhook-test/process-invoice" if "webhook-test" not in N8N_WEBHOOK else "http://localhost:5678/webhook/process-invoice"
    ]
    
    last_code = None
    last_body = ""
    for target_url in candidates:
        req = urllib.request.Request(
            target_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                code = resp.getcode()
                body = resp.read().decode('utf-8')
                return code, body, target_url
        except urllib.error.HTTPError as e:
            last_code = e.code
            last_body = e.read().decode('utf-8')
            # If 404, try candidate (test webhook vs production webhook)
            if e.code == 404:
                continue
            return e.code, last_body, target_url
        except Exception as e:
            return None, str(e), target_url

    return last_code, last_body, candidates[0]
LOCAL_INVOICE_DB = [
    {
        "id": 101,
        "invoice_number": "INV-2026-98214",
        "vendor_name": "Amazon Web Services Inc.",
        "total_amount": 440.00,
        "status": "auto_approved",
        "created_at": "2026-10-31T05:00:00.000Z"
    }
]

def save_gemini_key(new_key):
    os.environ["GEMINI_API_KEY"] = new_key
    lines = []
    found = False
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for l in f:
                if l.strip().startswith("GEMINI_API_KEY="):
                    lines.append(f"GEMINI_API_KEY={new_key}\n")
                    found = True
                else:
                    lines.append(l)
    if not found:
        lines.append(f"GEMINI_API_KEY={new_key}\n")
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"Saved new GEMINI_API_KEY to {ENV_PATH}")


def main():
    # Test Bot connection
    me = tg_request("getMe")
    if not me.get("ok"):
        print(f"❌ Failed to connect to Telegram API: {me.get('error')}")
        print("💡 Hint: If api.telegram.org is restricted in your region, enable your VPN or set HTTPS_PROXY.")
        return

    bot_info = me["result"]
    print(f"✅ Connected to Telegram as @{bot_info.get('username')} ({bot_info.get('first_name')})")
    print("🚀 Listening for incoming invoices and /report commands... (Press Ctrl+C to stop)\n")

    offset = 0
    while True:
        try:
            updates = tg_request("getUpdates", {"offset": offset, "timeout": 10})
            if not updates.get("ok"):
                time.sleep(3)
                continue

            for u in updates.get("result", []):
                offset = u["update_id"] + 1
                msg = u.get("message")
                if not msg:
                    continue

                chat_id = msg.get("chat", {}).get("id")
                user_name = msg.get("from", {}).get("first_name", "User")
                text = msg.get("text") or msg.get("caption") or ""
                has_photo = bool(msg.get("photo") or msg.get("document"))
                photo_id = None
                if msg.get("photo"):
                    photo_id = msg["photo"][-1].get("file_id")
                elif msg.get("document"):
                    photo_id = msg["document"].get("file_id")

                # Check if user sent Gemini API key
                new_key = None
                key_match = re.search(r'(?:AIza[0-9A-Za-z-_]{35}|AQ\.[0-9A-Za-z-_]{30,70})', text)
                if key_match:
                    new_key = key_match.group(0)
                elif not has_photo:
                    candidate = text.strip()
                    if 35 <= len(candidate) <= 80 and ' ' not in candidate and all(c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_." for c in candidate):
                        new_key = candidate

                if new_key:
                    save_gemini_key(new_key)
                    tg_request("sendMessage", {
                        "chat_id": chat_id,
                        "text": (
                            "✅ *کلید هوش مصنوعی Google Gemini با موفقیت ثبت و فعال شد!*\n"
                            "━━━━━━━━━━━━━━━━━━━━━\n"
                            "🚀 از این لحظه هر تصویر فاکتوری ارسال نمایید، مستقیماً توسط مدل قدرتمند Google Gemini Vision AI "
                            "تحلیل، اقلام و مبالغ استخراج و اعتبارسنجی محاسباتی می‌گردد.\n\n"
                            "⚡ لطفاً تصویر یا فایل یک فاکتور را ارسال کنید تا آزمایش کنیم!"
                        ),
                        "parse_mode": "Markdown"
                    })
                    continue

                print(f"📩 [{time.strftime('%X')}] Message from {user_name} (Chat {chat_id}): '{text}' (Photo: {has_photo})")

                payload = {
                    "source": "telegram_bot",
                    "chat_id": chat_id,
                    "user_name": user_name,
                    "message_text": text,
                    "has_photo": has_photo,
                    "photo_file_id": photo_id,
                    "telegram_raw_update": u
                }

                # Forward to n8n
                print(f"   ↳ Forwarding to n8n...")
                code, resp, used_url = forward_to_n8n(payload)
                print(f"   ↳ n8n Response: HTTP {code} (via {used_url})")

                if code in (200, 202, 409):
                    print("   ↳ Successfully handled by n8n!")
                elif chat_id:
                    low = (text or '').strip().lower()
                    if low.startswith('/start') or low.startswith('/help') or 'راهنما' in low or (not has_photo and not low.startswith('/report') and not 'inv' in low and not 'فاکتور' in low):
                        tg_request("sendMessage", {
                            "chat_id": chat_id,
                            "text": f"👋 درود {user_name} گرامی!\nبه سامانه پردازش هوشمند اسناد مالی خوش آمدید.\n━━━━━━━━━━━━━━━━━━━━━\n📌 راهنما:\n1️⃣ ارسال فاکتور: عکس یا فایل فاکتور را بفرستید تا توسط هوش مصنوعی Google Gemini تحلیل و اعتبارسنجی گردد.\n2️⃣ فعال‌سازی کلید: کلید رایگان خود را از aistudio.google.com ارسال فرمایید.\n3️⃣ دریافت گزارش: دستور /report را ارسال نمایید."
                        })
                    elif low.startswith('/report') or low.startswith('/stats') or 'گزارش' in low:
                        total_spent = sum(inv["total_amount"] for inv in LOCAL_INVOICE_DB)
                        app_count = sum(1 for inv in LOCAL_INVOICE_DB if inv["status"] == "auto_approved")
                        tg_request("sendMessage", {
                            "chat_id": chat_id,
                            "text": f"📊 *گزارش پایگاه داده مالی:*\n• کل اسناد: {len(LOCAL_INVOICE_DB)} فقره\n• تایید قطعی: {app_count} فقره\n• گردش مالی کل: ${total_spent:,.2f} USD",
                            "parse_mode": "Markdown"
                        })
                    elif has_photo and photo_id:
                        gemini_key = os.environ.get("GEMINI_API_KEY")
                        if not gemini_key:
                            tg_request("sendMessage", {
                                "chat_id": chat_id,
                                "text": (
                                    "🔑 *کلید هوش مصنوعی Google Gemini هنوز فعال نشده است!*\n"
                                    "━━━━━━━━━━━━━━━━━━━━━\n"
                                    "برای اینکه فاکتور شما مستقیماً توسط هوش مصنوعی واقعی تحلیل، اقلام استخراج و اعتبارسنجی ریاضی شود:\n\n"
                                    "۱. وارد لینک زیر در سایت Google شوید:\n"
                                    "👉 https://aistudio.google.com/app/apikey\n"
                                    "۲. دکمه **Create API Key** را بزنید.\n"
                                    "۳. کلید ایجاد شده (که با `AIza...` شروع می‌شود) را کپی کرده و در همین چت تلگرام ارسال فرمایید.\n\n"
                                    "⚡ به محض ارسال کلید، سامانه به صورت خودکار فعال شده و فاکتورها را تحلیل خواهد کرد!"
                                ),
                                "parse_mode": "Markdown"
                            })
                        else:
                            tg_request("sendMessage", {
                                "chat_id": chat_id,
                                "text": "⏳ در حال دانلود تصویر و تحلیل هوشمند سند توسط Google Gemini Vision AI..."
                            })
                            img_bytes, mime = download_telegram_file(photo_id)
                            if not img_bytes:
                                tg_request("sendMessage", {"chat_id": chat_id, "text": "❌ خطا در دانلود تصویر از تلگرام."})
                            else:
                                extracted, err = analyze_invoice_with_ai(img_bytes, mime, api_key=gemini_key, provider="gemini")
                                if err or not extracted:
                                    tg_request("sendMessage", {"chat_id": chat_id, "text": f"⚠️ خطا در تحلیل هوش مصنوعی: {err}"})
                                else:
                                    eval_res = evaluate_and_format_response(extracted, LOCAL_INVOICE_DB)
                                    if eval_res["status"] == "AUTO_APPROVED":
                                        LOCAL_INVOICE_DB.append({
                                            "id": len(LOCAL_INVOICE_DB) + 101,
                                            "invoice_number": extracted.get("invoice_number", "INV-UNKNOWN"),
                                            "vendor_name": extracted.get("vendor_name", "Unknown"),
                                            "total_amount": float(extracted.get("total_amount", 0.0)),
                                            "status": "auto_approved",
                                            "created_at": datetime.utcnow().isoformat()
                                        })
                                    tg_request("sendMessage", {
                                        "chat_id": chat_id,
                                        "text": eval_res["message"],
                                        "parse_mode": "Markdown"
                                    })
                    else:
                        tg_request("sendMessage", {
                            "chat_id": chat_id,
                            "text": "👋 پیام شما دریافت شد. لطفاً تصویر یا فایل یک فاکتور را ارسال فرمایید تا توسط هوش مصنوعی بررسی گردد."
                        })

            time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Bridge stopped by user.")
            break
        except Exception as e:
            print(f"⚠️ Polling loop error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()

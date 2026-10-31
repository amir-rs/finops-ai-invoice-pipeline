import os
import json
import base64
import urllib.request
import urllib.error

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

setup_global_proxy()

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

def download_telegram_file(file_id):
    """Downloads an image file from Telegram servers and returns raw bytes and mime type."""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        
        if not data.get("ok"):
            return None, None
            
        file_path = data["result"]["file_path"]
        download_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        
        down_req = urllib.request.Request(download_url)
        with urllib.request.urlopen(down_req, timeout=30) as resp:
            content = resp.read()
            
        mime = "image/jpeg"
        if file_path.lower().endswith(".png"):
            mime = "image/png"
        elif file_path.lower().endswith(".webp"):
            mime = "image/webp"
            
        return content, mime
    except Exception as e:
        print(f"Error downloading file {file_id}: {e}")
        return None, None

def analyze_invoice_with_ai(image_bytes, mime_type="image/jpeg", api_key=None, provider="openai"):
    """
    Analyzes an invoice image using Vision AI API (OpenAI GPT-4o, Google Gemini, OpenRouter, or Groq).
    Returns parsed dictionary of invoice fields and audit evaluation.
    """
    b64_img = base64.b64encode(image_bytes).decode('utf-8')
    
    system_prompt = (
        "You are an expert AI FinOps Auditor. Analyze this invoice image carefully and extract all financial details in strict JSON format.\n"
        "Return ONLY a JSON object with this exact schema:\n"
        "{\n"
        '  "vendor_name": "Exact vendor/company name",\n'
        '  "vendor_vat_id": "Tax ID or null",\n'
        '  "invoice_number": "Exact invoice number",\n'
        '  "invoice_date": "YYYY-MM-DD",\n'
        '  "due_date": "YYYY-MM-DD",\n'
        '  "currency": "USD / EUR / ...",\n'
        '  "line_items": [\n'
        '    {"description": "...", "quantity": 1, "unit_price": 0.0, "total_price": 0.0}\n'
        "  ],\n"
        '  "subtotal": 0.0,\n'
        '  "tax_amount": 0.0,\n'
        '  "total_amount": 0.0,\n'
        '  "confidence_score": 0.98,\n'
        '  "notes": "Any observation or discrepancy"\n'
        "}"
    )

    # 1. Google Gemini Provider
    if provider == "gemini":
        gemini_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not gemini_key:
            return None, "کلید API برای مدل Gemini تنظیم نشده است."

        models_to_try = [
            "gemini-flash-lite-latest",
            "gemini-flash-latest",
            "gemini-3.5-flash",
            "gemini-3.8-flash"
        ]

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": system_prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": b64_img
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "response_mime_type": "application/json"
            }
        }

        last_err = None
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json"}
            )
            try:
                with urllib.request.urlopen(req, timeout=35) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if text.startswith("```json"):
                        text = text[7:]
                    if text.startswith("```"):
                        text = text[3:]
                    if text.endswith("```"):
                        text = text[:-3]
                    text = text.strip()
                    return json.loads(text), None
            except urllib.error.HTTPError as e:
                err_body = e.read().decode('utf-8', errors='ignore')
                last_err = f"Model {model} HTTP {e.code}: {err_body}"
                continue
            except Exception as e:
                last_err = f"Model {model} error: {e}"
                continue

        return None, last_err or "خطا در اتصال به سرویس هوش مصنوعی Gemini."

    # 2. OpenAI / OpenRouter / Groq Provider (OpenAI Compatible)
    base_url = "https://api.openai.com/v1"
    model = "gpt-4o-mini"
    
    if provider == "openrouter":
        base_url = "https://openrouter.ai/api/v1"
        model = "google/gemini-2.0-flash-exp:free"
        api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
    elif provider == "groq":
        base_url = "https://api.groq.com/openai/v1"
        model = "llama-3.2-11b-vision-preview"
        api_key = api_key or os.environ.get("GROQ_API_KEY")
    else:
        api_key = api_key or os.environ.get("OPENAI_API_KEY")

    if not api_key:
        return None, "کلید API هوش مصنوعی (API Key) تعریف نشده است."

    url = f"{base_url}/chat/completions"
    payload = {
        "model": model,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": system_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{b64_img}"
                        }
                    }
                ]
            }
        ]
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    if provider == "openrouter":
        headers["HTTP-Referer"] = "https://github.com/n8n-io/n8n"
        headers["X-Title"] = "n8n FinOps Pipeline"

    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
    with urllib.request.urlopen(req, timeout=35) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        raw_content = data["choices"][0]["message"]["content"]
        # extract json if markdown fenced
        if "```json" in raw_content:
            raw_content = raw_content.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_content:
            raw_content = raw_content.split("```")[1].split("```")[0].strip()
        return json.loads(raw_content), None

def evaluate_and_format_response(inv_data, existing_invoices):
    """
    Applies business logic & math validation to the AI-extracted invoice
    and generates a detailed, dynamic Persian report.
    """
    vendor = inv_data.get("vendor_name", "ناشناس")
    inv_num = inv_data.get("invoice_number", "نامشخص")
    inv_date = inv_data.get("invoice_date", "نامشخص")
    currency = inv_data.get("currency", "USD")
    total = float(inv_data.get("total_amount", 0.0))
    subtotal = float(inv_data.get("subtotal", total))
    tax = float(inv_data.get("tax_amount", 0.0))
    items = inv_data.get("line_items", [])

    # 1. Math Integrity Check
    calc_subtotal = sum(float(i.get("total_price", 0.0)) for i in items) if items else subtotal
    math_diff = abs(calc_subtotal - subtotal)
    math_valid = math_diff < 0.05
    total_valid = abs((subtotal + tax) - total) < 0.05

    # 2. Duplicate Check
    is_duplicate = any(ex.get("invoice_number") == inv_num for ex in existing_invoices)

    # 3. Decision Matrix
    status = "AUTO_APPROVED"
    reason = "تایید خودکار بر اساس تمامی شروط و قوانین مالی"
    status_icon = "✅"
    status_title = "تایید خودکار و ثبت قطعی در سیستم (Auto-Approved)"

    if is_duplicate:
        status = "REJECTED_DUPLICATE"
        status_icon = "❌"
        status_title = "خطای فاکتور تکراری (Duplicate Invoice)"
        reason = f"فاکتور شماره {inv_num} قبلاً در پایگاه داده ثبت گردیده است."
    elif not math_valid or not total_valid:
        status = "FLAGGED_MATH_ERROR"
        status_icon = "⚠️"
        status_title = "مغایرت حسابی و خطای محاسباتی (Math Mismatch)"
        reason = f"مجموع اقلام (${calc_subtotal:,.2f}) با جمع جزء فاکتور (${subtotal:,.2f}) همخوانی ندارد."
    elif total > 2000.0:
        status = "FLAGGED_HIGH_VALUE"
        status_icon = "⚠️"
        status_title = "نیازمند تایید دستی مدیر مالی (Threshold Exceeded)"
        reason = f"مبلغ فاکتور (${total:,.2f}) از سقف مجاز ثبت خودکار ($2,000.00) فراتر است."

    # Format items table
    items_text = ""
    for idx, item in enumerate(items, 1):
        desc = item.get("description", "کالا/خدمت")
        qty = item.get("quantity", 1)
        u_price = float(item.get("unit_price", 0.0))
        l_tot = float(item.get("total_price", u_price * qty))
        items_text += f"  {idx}. {desc} | تعداد: {qty} | واحد: ${u_price:,.2f} | کل: ${l_tot:,.2f}\n"

    msg = (
        f"{status_icon} *{status_title}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 *استخراج بلادرنگ توسط هوش مصنوعی Vision AI:*\n"
        f"🏢 صادرکننده: *{vendor}*\n"
        f"📄 شماره فاکتور: `{inv_num}`\n"
        f"📅 تاریخ سند: `{inv_date}`\n"
        f"💵 واحد پولی: *{currency}*\n\n"
        f"📦 *اقلام استخراج‌شده از تصویر:*\n"
        f"{items_text if items_text else '  (بدون جزئیات اقلام)\n'}\n"
        f"💰 *خلاصه مالی و محاسباتی:*\n"
        f"• جمع جزء (Subtotal): *${subtotal:,.2f}*\n"
        f"• مالیات/ارزش‌افزوده (Tax): *${tax:,.2f}*\n"
        f"• مبلغ کل قابل پرداخت: *${total:,.2f} {currency}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔍 *نتیجه ممیزی و قوانین سامانه:*\n"
        f"• وضعیت نهایی: *{reason}*\n"
    )

    if status == "AUTO_APPROVED":
        msg += f"🏦 سند مالی در دیتابیس ثبت و به دفتر کل ERP اضافه شد."
    elif status == "REJECTED_DUPLICATE":
        msg += f"🛡️ جهت جلوگیری از پرداخت مضاعف، فرآیند فوراً متوقف گردید."
    else:
        msg += f"📨 پیام بازبینی به همراه تصویر به کارتابل مدیر مالی ارسال شد."

    return {
        "status": status,
        "is_duplicate": is_duplicate,
        "math_valid": math_valid,
        "message": msg
    }

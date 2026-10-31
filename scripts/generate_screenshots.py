import os
from PIL import Image, ImageDraw

os.makedirs("docs/images", exist_ok=True)

def create_chat_mockup(output_path, title_text, user_img_path, bot_messages):
    width, height = 920, 880
    bg_color = (14, 22, 33)
    header_color = (23, 33, 43)
    bot_bubble = (24, 37, 51)
    user_bubble = (43, 82, 120)
    text_color = (245, 245, 245)
    muted_color = (130, 145, 160)
    accent_green = (46, 204, 113)
    accent_red = (231, 76, 60)
    accent_yellow = (241, 196, 15)
    accent_blue = (52, 152, 219)

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Header
    draw.rectangle([0, 0, width, 68], fill=header_color)
    draw.line([0, 68, width, 68], fill=(35, 48, 62), width=1)
    draw.ellipse([20, 12, 64, 56], fill=accent_blue)
    draw.text((34, 22), "AI", fill=(255, 255, 255))
    draw.text((78, 15), "FinOps AI Manager Bot", fill=text_color)
    draw.text((78, 38), "@tets_manager111_bot • bot • Google Gemini Vision 2026", fill=muted_color)

    y = 88
    # User photo bubble
    if user_img_path and os.path.exists(user_img_path):
        inv_thumb = Image.open(user_img_path)
        inv_thumb.thumbnail((250, 180))
        tw, th = inv_thumb.size
        bx = width - tw - 45
        draw.rounded_rectangle([bx - 10, y - 8, bx + tw + 10, y + th + 26], radius=12, fill=user_bubble)
        img.paste(inv_thumb, (bx, y))
        draw.text((bx + 5, y + th + 6), "Invoice Document (PNG)", fill=(210, 230, 250))
        draw.text((bx + tw - 35, y + th + 6), "12:15", fill=muted_color)
        y += th + 48

    # Bot messages
    for b_msg in bot_messages:
        lines = b_msg["text"]
        badge = b_msg.get("badge", "")
        b_color = accent_green if "APPROVED" in badge else (accent_red if "ERROR" in badge or "DUPLICATE" in badge else accent_yellow)
        msg_h = len(lines) * 22 + 54
        bw, bx, by = 670, 25, y

        draw.rounded_rectangle([bx, by, bx + bw, by + msg_h], radius=14, fill=bot_bubble)
        if badge:
            draw.rounded_rectangle([bx + 14, by + 12, bx + 165, by + 34], radius=6, fill=b_color)
            draw.text((bx + 22, by + 16), badge, fill=(255, 255, 255))
            draw.text((bx + 180, by + 16), b_msg.get("title", ""), fill=text_color)
        else:
            draw.text((bx + 14, by + 14), b_msg.get("title", ""), fill=text_color)

        draw.line([bx + 14, by + 42, bx + bw - 14, by + 42], fill=(35, 48, 62), width=1)
        ly = by + 50
        for l in lines:
            col = text_color
            if l.startswith("•") or l.startswith("  -"):
                col = (200, 215, 230)
            elif "Auto-Approved" in l or "Passed" in l or "100%" in l:
                col = accent_green
            elif "Mismatch" in l or "Discrepancy" in l or "Gap" in l or "FLAGGED" in l:
                col = accent_red
            draw.text((bx + 18, ly), l, fill=col)
            ly += 22

        draw.text((bx + bw - 55, by + msg_h - 20), "12:15 ✓", fill=muted_color)
        y += msg_h + 18
    img.save(output_path, "PNG")
    print(f"Generated: {output_path}")


# 1. Approved Mockup
create_chat_mockup(
    "docs/images/telegram_demo_approved.png",
    "Auto-Approved Invoice",
    "sample_invoices/invoice_1_approved.png",
    [{
        "badge": "AUTO-APPROVED",
        "title": "Amazon Web Services Inc. (AWS)",
        "text": [
            "AI Vision Model: Google Gemini Flash Vision AI (Live Dynamic)",
            "Invoice Number: INV-2026-9011 | Date: 2026-10-31",
            "Total Extracted: $350.00 USD",
            "----------------------------------------------------------------------",
            "Line Items Extracted:",
            "  1. AWS EC2 Cloud Compute (c6i.2xlarge)  | Qty: 2  | Total: $240.00",
            "  2. AWS RDS Postgres Database Multi-AZ   | Qty: 1  | Total: $80.00",
            "  3. AWS CloudWatch Monitoring & Metrics  | Qty: 1  | Total: $30.00",
            "----------------------------------------------------------------------",
            "Financial Audit & Integrity Rules:",
            "  • Subtotal Verification: $350.00 (Exact Match 100%)",
            "  • Threshold Policy: Under $2,000 Cap (Passed)",
            "  • Deduplication Audit: Unique record in DB (Passed)",
            "Status: Auto-Approved and Recorded in PostgreSQL & ERP Ledger."
        ]
    }]
)

# 2. Math Mismatch Mockup
create_chat_mockup(
    "docs/images/telegram_demo_math_error.png",
    "Math Mismatch Flagged",
    "sample_invoices/invoice_3_math_mismatch_flagged.png",
    [{
        "badge": "MATH-MISMATCH",
        "title": "TechLogix Supplies • Arithmetic Discrepancy",
        "text": [
            "AI Vision Model: Google Gemini Flash Vision AI (Live Dynamic)",
            "Invoice Number: INV-2026-7731 | Date: 2026-10-31",
            "Reported Total: $1,250.00 USD",
            "----------------------------------------------------------------------",
            "Line Items Extracted:",
            "  1. 27-inch 4K Developer Monitor         | Qty: 2  | Total: $500.00",
            "  2. Ergonomic Mechanical Keyboard        | Qty: 4  | Total: $400.00",
            "----------------------------------------------------------------------",
            "Financial Audit & Integrity Rules:",
            "  • Sum of Line Items: $900.00",
            "  • Subtotal Claimed on Invoice: $1,250.00",
            "  • Discrepancy: +$350.00 Unaccounted Math Error!",
            "Status: FLAGGED - Escalated to Finance Manager Review Queue."
        ]
    }]
)

# 3. Report Mockup
create_chat_mockup(
    "docs/images/telegram_demo_stats_report.png",
    "Dataset Statistics",
    None,
    [{
        "badge": "DATASET-REPORT",
        "title": "FinOps Database Executive Summary",
        "text": [
            "User Command: /report",
            "----------------------------------------------------------------------",
            "Aggregated Pipeline Statistics:",
            "  • Total Processed Invoices: 4 Records",
            "  • Auto-Approved & Settled: 3 Invoices (75.0%)",
            "  • Pending Review / Flagged: 1 Invoice (25.0%)",
            "  • Gross Processed Volume: $10,920.00 USD",
            "----------------------------------------------------------------------",
            "Recent Ledger Activity:",
            "  1. INV-2026-9011 (Amazon Web Services) -> $350.00 [APPROVED]",
            "  2. INV-2026-8802 (Enterprise Cloud Co.) -> $1,450.00 [APPROVED]",
            "  3. INV-2026-7731 (TechLogix Supplies)  -> $1,250.00 [FLAGGED]",
            "  4. INV-2026-6640 (Global Data Systems) -> $7,870.00 [APPROVED]"
        ]
    }]
)
# 4. High-Value Flagged Mockup (> $2,000)
create_chat_mockup(
    "docs/images/telegram_demo_high_value.png",
    "High-Value Policy Threshold Flagged",
    "sample_invoices/invoice_2_high_value_flagged.png",
    [{
        "badge": "FLAGGED_HIGH_VALUE",
        "title": "Enterprise Cloud Solutions • Policy Review Gate",
        "text": [
            "AI Vision Model: Google Gemini Flash Vision AI (Live Dynamic)",
            "Invoice Number: INV-2026-8802 | Date: 2026-10-31",
            "Currency: USD | Total Amount: $3,500.00",
            "----------------------------------------------------------------------",
            "Line Items Extracted:",
            "  1. Annual Enterprise Kubernetes Cluster | Qty: 1  | Total: $2,500.00",
            "  2. Premium 24/7 SLA Engineering Support | Qty: 1  | Total: $1,000.00",
            "----------------------------------------------------------------------",
            "Financial Audit & Integrity Rules:",
            "  • Subtotal Verification: $3,500.00 (Math Verified 100%)",
            "  • Policy Threshold: Exceeds $2,000 Cap ($3,500.00 > $2,000.00)",
            "  • Compliance Routing: High-Value Human-in-the-Loop Gate",
            "Status: FLAGGED - Dispatched to CFO / Senior Finance Manager Worklist."
        ]
    }]
)



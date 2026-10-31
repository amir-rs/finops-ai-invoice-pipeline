import os
from PIL import Image, ImageDraw

def create_architecture_diagram(output_path):
    w, h = 1100, 560
    bg_color = (13, 17, 23)      # GitHub Dark
    card_bg = (22, 27, 34)
    card_border = (48, 54, 61)
    text_color = (230, 237, 243)
    subtext_color = (139, 148, 158)
    line_color = (88, 166, 255)
    
    img = Image.new("RGB", (w, h), bg_color)
    draw = ImageDraw.Draw(img)

    # Title
    draw.text((30, 25), "Autonomous FinOps & Vision AI Invoice Pipeline Architecture", fill=text_color)
    draw.text((30, 48), "Enterprise Architecture • Google Gemini Vision • n8n Workflow • PostgreSQL 16", fill=subtext_color)
    draw.line([30, 75, w - 30, 75], fill=card_border, width=1)

    nodes = [
        {"x": 40, "y": 110, "w": 200, "h": 140, "title": "1. Inbound Ingestion", "sub": "• Telegram Bot\n• REST Webhook API\n• Invoice Photos (PNG/PDF)"},
        {"x": 280, "y": 110, "w": 220, "h": 140, "title": "2. Router & Normalizer", "sub": "• Action Classification\n• Bot /report Commands\n• Telegram File Downloader"},
        {"x": 540, "y": 110, "w": 250, "h": 140, "title": "3. Gemini Vision AI", "sub": "• Google Gemini 2026 Model\n• Zero-shot Schema Extraction\n• Line-items, VAT, Totals"},
        {"x": 830, "y": 110, "w": 230, "h": 140, "title": "4. Financial Rules Engine", "sub": "• Qty x Price Arithmetic\n• Line Items vs Subtotal Sum\n• Duplicate Detection in DB"},
        {"x": 160, "y": 330, "w": 260, "h": 150, "title": "5. Human-in-the-Loop", "sub": "• >$2,000 Threshold Gate\n• Math Discrepancy Escalation\n• Flagged Telegram Card Alert"},
        {"x": 460, "y": 330, "w": 270, "h": 150, "title": "6. PostgreSQL Ledger", "sub": "• Invoices Relational DB\n• Complete Audit Log Trail\n• Unique Indices (Deduplication)"},
        {"x": 770, "y": 330, "w": 260, "h": 150, "title": "7. Auto-Approval / ERP", "sub": "• 100% Verified Invoices\n• Instant Settlement Sync\n• Telegram Live Confirmation"}
    ]

    for n in nodes:
        draw.rounded_rectangle([n["x"], n["y"], n["x"] + n["w"], n["y"] + n["h"]], radius=10, fill=card_bg, outline=card_border, width=2)
        draw.text((n["x"] + 15, n["y"] + 15), n["title"], fill=text_color)
        draw.line([n["x"] + 15, n["y"] + 38, n["x"] + n["w"] - 15, n["y"] + 38], fill=card_border, width=1)
        draw.text((n["x"] + 15, n["y"] + 48), n["sub"], fill=subtext_color)

    # Connecting arrows
    draw.line([240, 180, 280, 180], fill=line_color, width=3)
    draw.line([500, 180, 540, 180], fill=line_color, width=3)
    draw.line([790, 180, 830, 180], fill=line_color, width=3)

    # Downward connectors
    draw.line([945, 250, 945, 290], fill=line_color, width=3)
    draw.line([945, 290, 290, 290], fill=line_color, width=3)
    draw.line([290, 290, 290, 330], fill=line_color, width=3)
    draw.line([595, 290, 595, 330], fill=line_color, width=3)
    draw.line([900, 290, 900, 330], fill=line_color, width=3)

    img.save(output_path, "PNG")
    print(f"Generated diagram: {output_path}")

create_architecture_diagram("docs/images/system_architecture_diagram.png")

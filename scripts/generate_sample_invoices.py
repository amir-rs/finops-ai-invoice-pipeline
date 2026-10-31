import os
from PIL import Image, ImageDraw, ImageFont

os.makedirs("sample_invoices", exist_ok=True)

def make_invoice(filename, vendor, inv_num, date, items, tax_rate, total_override=None, stamp=None, color=(30, 60, 120)):
    w, h = 900, 1200
    img = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(img)

    try:
        f_xl = ImageFont.truetype("arialbd.ttf", 30)
        f_lg = ImageFont.truetype("arialbd.ttf", 22)
        f_md = ImageFont.truetype("arial.ttf", 16)
        f_b = ImageFont.truetype("arialbd.ttf", 16)
        f_sm = ImageFont.truetype("arial.ttf", 13)
        f_stamp = ImageFont.truetype("arialbd.ttf", 26)
    except:
        f_xl = f_lg = f_md = f_b = f_sm = f_stamp = ImageFont.load_default()

    # Header Banner
    d.rectangle([(0, 0), (w, 120)], fill=color)
    d.text((40, 30), "COMMERCIAL INVOICE", fill="white", font=f_xl)
    d.text((40, 75), "Autonomous FinOps Document Validation", fill=(210, 230, 255), font=f_sm)
    d.text((w - 280, 35), f"INVOICE #: {inv_num}", fill="white", font=f_lg)
    d.text((w - 280, 75), f"DATE: {date}", fill=(210, 230, 255), font=f_md)

    # Vendor & Customer
    d.text((40, 150), "ISSUED BY (صادرکننده):", fill=(110, 110, 110), font=f_b)
    d.text((40, 175), vendor, fill=(20, 20, 20), font=f_lg)
    d.text((40, 205), "Global Cloud Infrastructure & SaaS Services LLC", fill=(80, 80, 80), font=f_md)
    d.text((40, 225), "Tax ID: US-9918237 | Billing Dept", fill=(100, 100, 100), font=f_sm)

    d.text((w - 360, 150), "BILLED TO (خریدار):", fill=(110, 110, 110), font=f_b)
    d.text((w - 360, 175), "FinOps Automation Corp.", fill=(20, 20, 20), font=f_lg)
    d.text((w - 360, 205), "Attn: Amir R. S. / Finance Operations", fill=(80, 80, 80), font=f_md)

    # Table Header
    y = 280
    d.rectangle([(40, y), (w - 40, y + 36)], fill=color)
    d.text((55, y + 8), "Description / کالا یا خدمات", fill="white", font=f_b)
    d.text((500, y + 8), "Qty", fill="white", font=f_b)
    d.text((610, y + 8), "Unit Price", fill="white", font=f_b)
    d.text((750, y + 8), "Total ($)", fill="white", font=f_b)

    # Table Rows
    y += 42
    subtotal = 0.0
    for i, (desc, qty, price, line_tot) in enumerate(items):
        bg = (248, 250, 253) if i % 2 == 1 else (255, 255, 255)
        d.rectangle([(40, y), (w - 40, y + 40)], fill=bg)
        d.line([(40, y + 40), (w - 40, y + 40)], fill=(230, 230, 235))
        d.text((55, y + 10), desc, fill=(30, 30, 30), font=f_md)
        d.text((510, y + 10), str(qty), fill=(50, 50, 50), font=f_md)
        d.text((615, y + 10), f"${price:,.2f}", fill=(50, 50, 50), font=f_md)
        d.text((755, y + 10), f"${line_tot:,.2f}", fill=(20, 20, 20), font=f_b)
        subtotal += line_tot
        y += 42

    # Totals Box
    tax = subtotal * tax_rate
    total = total_override if total_override is not None else (subtotal + tax)
    box_y = max(y + 30, 680)
    bx = w - 380

    d.rounded_rectangle([(bx, box_y), (w - 40, box_y + 140)], radius=8, fill=(247, 248, 251), outline=(210, 215, 225))
    d.text((bx + 20, box_y + 15), "Subtotal:", fill=(90, 90, 90), font=f_md)
    d.text((w - 170, box_y + 15), f"${subtotal:,.2f}", fill=(30, 30, 30), font=f_b)
    d.text((bx + 20, box_y + 45), f"Tax / VAT ({int(tax_rate*100)}%):", fill=(90, 90, 90), font=f_md)
    d.text((w - 170, box_y + 45), f"${tax:,.2f}", fill=(30, 30, 30), font=f_b)
    d.line([(bx + 15, box_y + 75), (w - 55, box_y + 75)], fill=(200, 205, 215), width=2)
    d.text((bx + 20, box_y + 90), "TOTAL DUE:", fill=color, font=f_lg)
    d.text((w - 180, box_y + 90), f"${total:,.2f}", fill=color, font=f_lg)

    # Stamp
    if stamp:
        txt, sc = stamp
        d.rounded_rectangle([(60, box_y + 20), (380, box_y + 90)], radius=8, outline=sc, width=3)
        d.text((80, box_y + 35), txt, fill=sc, font=f_stamp)

    # Footer
    d.line([(40, h - 60), (w - 40, h - 60)], fill=(220, 220, 225))
    d.text((40, h - 45), "Generated for Telegram Bot & n8n FinOps Pipeline End-to-End Test", fill=(140, 140, 140), font=f_sm)

    out = os.path.join("sample_invoices", filename)
    img.save(out, quality=95)
    print("Saved:", out)

# 1. Standard Approved (< $2000, correct math)
make_invoice(
    "invoice_1_approved.png",
    "Amazon Web Services Inc.",
    "INV-2026-9011",
    "2026-10-31",
    [
        ("AWS EC2 Cloud Compute (c6i.2xlarge)", 2, 120.00, 240.00),
        ("AWS RDS Postgres Database Multi-AZ", 1, 80.00, 80.00),
        ("AWS CloudWatch Monitoring & Metrics", 1, 30.00, 30.00)
    ],
    0.0,
    stamp=("AUTO-APPROVED", (40, 150, 60)),
    color=(25, 75, 140)
)

# 2. High Value (> $2000, requires manager approval)
make_invoice(
    "invoice_2_high_value_flagged.png",
    "Dell Technologies Enterprise Sales",
    "INV-2026-4482",
    "2026-10-31",
    [
        ("Dell PowerEdge R760 Rack Server 128GB", 1, 3800.00, 3800.00),
        ("Broadcom 25Gb Dual-Port SFP28 NIC", 2, 350.00, 700.00),
        ("Dell ProSupport Plus SLA 24x7 (1 Year)", 1, 350.00, 350.00)
    ],
    0.0,
    stamp=("FLAGGED: > $2,000", (210, 90, 20)),
    color=(170, 95, 25)
)

# 3. Calculation Error (Math Mismatch)
make_invoice(
    "invoice_3_math_mismatch_flagged.png",
    "TechLogix Hardware Supplies",
    "INV-2026-7731",
    "2026-10-31",
    [
        ("27-inch 4K Developer Monitor", 2, 250.00, 500.00),
        ("Ergonomic Mechanical Office Keyboard", 4, 100.00, 400.00)
    ],
    0.0,
    total_override=1250.00, # Actual is 900, listed as 1250
    stamp=("MATH ERROR", (200, 40, 40)),
    color=(160, 40, 40)
)

# 4. Duplicate Test (INV-2026-98214 is already in DB)
make_invoice(
    "invoice_4_duplicate_test.png",
    "Amazon Web Services Inc.",
    "INV-2026-98214",
    "2026-10-25",
    [
        ("AWS Elastic Kubernetes Cluster (EKS)", 1, 250.00, 250.00),
        ("AWS Application Load Balancer (ALB)", 2, 95.00, 190.00)
    ],
    0.0,
    stamp=("DUPLICATE RECORD", (140, 30, 140)),
    color=(110, 40, 110)
)

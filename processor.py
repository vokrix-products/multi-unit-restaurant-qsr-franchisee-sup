import os
import io
import json
from openai import OpenAI

PRICE_CHANGE_THRESHOLD_PERCENT = 5.0

def extract_text(file_bytes: bytes) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            text = ""
            for page in pdf.pages:
                t = page.extract_text()
                if t: text += t + "
"
            if text.strip(): return text
    except Exception:
        pass
    try:
        return file_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return ""

def process_file(file_bytes: bytes) -> list[dict]:
    text = extract_text(file_bytes)
    if not text.strip():
        return []

    client = OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")

    system_prompt = (
        "You are a data extraction assistant. Output only valid JSON. "
        "Example: if text contains 'Supplier: Acme, Product: Rice, Old Price: $4.00, New Price: $5.00, Effective Date: 2024-01-01', "
        "return [{\"supplier\": \"Acme\", \"product\": \"Rice\", \"old_price\": 4.00, \"new_price\": 5.00, \"effective_date\": \"2024-01-01\"}]."
    )

    prompt = (
        "Extract supplier price change information from the following text. "
        "Return a JSON array of objects, each with keys: supplier, product, old_price, new_price, effective_date. "
        "old_price and new_price should be numeric values (in dollars). effective_date in YYYY-MM-DD format. "
        "If no price change found, return empty array. Output only valid JSON, no extra text.\n\n"
        f"Text:\n{text}"
    )

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": prompt}],
        temperature=0
    )

    content = response.choices[0].message.content.strip()
    try:
        extracted = json.loads(content)
    except json.JSONDecodeError:
        if content.startswith("```"):
            lines = content.split("\n")
            json_lines = []
            in_block = False
            for line in lines:
                if line.startswith("```"):
                    if in_block:
                        break
                    else:
                        in_block = True
                        continue
                if in_block:
                    json_lines.append(line)
            cleaned = "\n".join(json_lines)
            extracted = json.loads(cleaned)
        else:
            extracted = []

    records = []
    for item in extracted:
        old_price = float(item.get("old_price", 0))
        new_price = float(item.get("new_price", 0))
        if old_price != 0:
            change_percent = ((new_price - old_price) / old_price) * 100
        else:
            change_percent = 0
        abs_change = abs(change_percent)
        status = "price_change_above_threshold:critical" if abs_change >= PRICE_CHANGE_THRESHOLD_PERCENT else "price_change_within_threshold:good"
        due_date = item.get("effective_date")
        records.append({
            "title": item.get("product", "Unknown"),
            "status": status,
            "details": {
                "supplier": item.get("supplier"),
                "product": item.get("product"),
                "old_price": old_price,
                "new_price": new_price,
                "change_percent": round(change_percent, 2),
                "effective_date": due_date
            },
            "due_date": due_date
        })

    return records

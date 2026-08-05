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
                if t:
                    text += t + "\n"
            if text.strip():
                return text
    except Exception:
        pass
    return file_bytes.decode("utf-8", errors="ignore")

def process_file(file_bytes: bytes) -> list:
    text = extract_text(file_bytes)
    if not text.strip():
        return []
    client = OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")
    prompt = (
        "Extract supplier price change information from the following text. "
        "Return a JSON array of objects, each with keys: supplier, product, old_price, new_price, effective_date. "
        "old_price and new_price should be numeric values. effective_date in YYYY-MM-DD format. "
        "If no price change found, return empty array. Output only valid JSON, no extra text.\n\n"
        f"Text:\n{text}"
    )
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000
    )
    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        items = json.loads(raw)
    except Exception:
        return []
    records = []
    for item in items:
        old_p = float(item.get("old_price", 0) or 0)
        new_p = float(item.get("new_price", 0) or 0)
        pct = abs(new_p - old_p) / old_p * 100 if old_p else 0
        status = "above_threshold" if pct >= PRICE_CHANGE_THRESHOLD_PERCENT else "within_threshold"
        records.append({
            "title": str(item.get("supplier", "Unknown")),
            "status": status,
            "details": {"product": item.get("product"), "old_price": old_p, "new_price": new_p, "change_pct": round(pct, 2)},
            "due_date": item.get("effective_date")
        })
    return records

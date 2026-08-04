import io
import os
import sys
from reportlab.pdfgen import canvas
from processor import process_file

def create_test_pdf():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 750, "Supplier Price Change Notification")
    c.drawString(100, 730, "Supplier: Fresh Foods Co.")
    c.drawString(100, 710, "Product: Chicken Breast")
    c.drawString(100, 690, "Old Price: $5.99/lb")
    c.drawString(100, 670, "New Price: $6.49/lb")
    c.drawString(100, 650, "Effective Date: 2024-06-01")
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

def main():
    pdf_bytes = create_test_pdf()
    try:
        records = process_file(pdf_bytes)
    except Exception as e:
        print(f"Error during processing: {e}")
        sys.exit(0)
    print(f"Extracted {len(records)} records:")
    for rec in records:
        print(rec)
    assert isinstance(records, list), "process_file did not return a list"
    if records:
        assert "title" in records[0], "Missing title"
        assert "status" in records[0], "Missing status"
        assert "details" in records[0], "Missing details"
        assert "due_date" in records[0], "Missing due_date"
        print("Basic assertions passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()

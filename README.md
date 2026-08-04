# Supplier Price Change Alert and Menu Margin Impact Dashboard

Backend extraction pipeline for multi-unit restaurant / QSR franchisees that processes PDF notifications of supplier price changes, extracts structured records, and classifies each change by margin impact severity.

## Product

This service ingests supplier price change PDF notifications and returns normalized records containing:

- supplier
- product
- old_price
- new_price
- change_percent
- effective_date

Each record is classified as:

- **price_change_above_threshold:critical** when the absolute change is >= 5%
- **price_change_within_threshold:good** when the absolute change is below 5%

## Archetype

**Multi-Unit Restaurant / QSR Franchisee** — operators running several locations who need a single consolidated view of supplier price movements so they can protect menu margins across all units before price increases hit.

## Pipeline

1. `processor.py` — extracts text from PDF bytes with pdfplumber, sends it to DeepSeek for structured extraction, and applies the threshold classification.
2. `run_demo.py` — generates a sample PDF and demonstrates the full flow.
3. `run_tests.py` — imports and structure test that requires no API key.

## Poller Input Expectations

The poller must pass in the raw **PDF file bytes** to `process_file(file_bytes)`. The PDF should contain supplier price change notification text such as product name, supplier name, old price, new price, and effective date. A valid `DEEPSEEK_API_KEY` must be present in the environment for real extractions; empty input returns an empty list without calling the API.

## Dependencies

- Python 3.8+
- openai
- requests
- pdfplumber
- reportlab

## Usage

`python3 run_demo.py` — generates a sample PDF and displays extracted records.
`python3 run_tests.py` — basic import and structure test (no key needed).

Dashboard: https://multi-unit-restaurant-qsr-franchisee-sup.vokrix.co
Vercel: multi-unit-restaurant-qsr-franchisee-sup
Railway: 55c14326-497e-4d71-9d21-1a732e7ed0cb
Railway: multi-unit-restaurant-qsr-franchisee-sup

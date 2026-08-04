import os
import time
import json
from datetime import datetime, timezone

import requests

import processor

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
PRODUCT_ID = os.environ["PRODUCT_ID"]

JOBS_URL = f"{SUPABASE_URL}/rest/v1/jobs"
RECORDS_URL = f"{SUPABASE_URL}/rest/v1/records"
NOTIFICATIONS_URL = f"{SUPABASE_URL}/rest/v1/notifications"

HEADERS = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    "Content-Type": "application/json",
}

UPLOADS_BUCKET = "uploads"
RESULTS_BUCKET = "results"


def poll_once():
    params = {
        "status": "eq.pending",
        "job_type": "eq.process_upload",
        "product_id": f"eq.{PRODUCT_ID}",
        "select": "*",
    }
    resp = requests.get(JOBS_URL, headers=HEADERS, params=params)
    resp.raise_for_status()
    for job in resp.json():
        process_job(job)


def download_file(bucket, file_path):
    if file_path.startswith(bucket + "/"):
        file_path = file_path[len(bucket) + 1:]
    url = f"{SUPABASE_URL}/storage/v1/object/{bucket}/{file_path}"
    resp = requests.get(url, headers={"Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"})
    resp.raise_for_status()
    return resp.content


def upload_result(job_id, records):
    result_bytes = json.dumps(records, default=str).encode("utf-8")
    file_name = f"{job_id}.json"
    url = f"{SUPABASE_URL}/storage/v1/object/{RESULTS_BUCKET}/{file_name}"
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"},
        data=result_bytes,
    )
    resp.raise_for_status()
    return f"{RESULTS_BUCKET}/{file_name}"


def insert_records(job, records, source_file_path):
    rows = []
    for rec in records:
        rows.append({
            "product_id": PRODUCT_ID,
            "customer_id": job.get("customer_id"),
            "title": rec["title"],
            "status": rec["status"],
            "details": rec["details"],
            "source_file_path": source_file_path,
            "due_date": rec.get("due_date"),
        })
    if rows:
        resp = requests.post(RECORDS_URL, headers=HEADERS, json=rows)
        resp.raise_for_status()


def update_job(job_id, status, output_file_path, result_summary):
    payload = {
        "status": status,
        "output_file_path": output_file_path,
        "result_summary": result_summary,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    resp = requests.patch(f"{JOBS_URL}?id=eq.{job_id}", headers=HEADERS, json=payload)
    resp.raise_for_status()


def notify(job, type_, title, body):
    try:
        payload = {
            "product_id": PRODUCT_ID,
            "customer_id": job.get("customer_id"),
            "title": title,
            "body": body,
            "type": type_,
            "read": False,
        }
        requests.post(NOTIFICATIONS_URL, headers=HEADERS, json=payload)
    except Exception as exc:
        print("Notification failed:", exc)


def process_job(job):
    job_id = job.get("id")
    input_file_path = job.get("input_file_path")
    try:
        file_bytes = download_file(UPLOADS_BUCKET, input_file_path)
        records = processor.process_file(file_bytes)
        output_file_path = upload_result(job_id, records)
        insert_records(job, records, input_file_path)
        update_job(job_id, "completed", output_file_path, {"record_count": len(records)})
        notify(job, "success", "Processing complete", "Your upload has been processed successfully.")
    except Exception as exc:
        print("Job failed:", job_id, exc)
        try:
            update_job(job_id, "failed", None, {"error": str(exc)})
        except Exception as update_exc:
            print("Failed to update job:", job_id, update_exc)
        notify(job, "error", "Processing failed", "There was an error processing your upload.")


def main():
    while True:
        try:
            poll_once()
        except Exception as exc:
            print("Poll error:", exc)
        time.sleep(60)


if __name__ == "__main__":
    main()

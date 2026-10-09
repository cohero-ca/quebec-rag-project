import os
from datetime import datetime, timezone
from google.cloud import storage
from dotenv import load_dotenv

load_dotenv()

GCP_PROJECT = os.getenv("GCP_PROJECT", "gen-lang-client-0426110783")
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "hr-chatbot-tenant-vault")

# Ensure service account path is set consistently
KEY_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "gcp-key.json"))
if os.path.exists(KEY_PATH):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_PATH

def get_storage_client() -> storage.Client:
    """Returns an authenticated GCS client using explicit key or environment credentials."""
    if os.path.exists(KEY_PATH):
        return storage.Client.from_service_account_json(KEY_PATH, project=GCP_PROJECT)
    return storage.Client(project=GCP_PROJECT)

def get_or_create_tenant_folder(tenant_id: str) -> str:
    return f"{tenant_id}/"

def upload_file_to_drive(file_stream, filename: str, folder_id: str) -> str:
    client = get_storage_client()
    bucket = client.bucket(BUCKET_NAME)
    blob_path = f"{folder_id}{filename}"
    blob = bucket.blob(blob_path)
    file_stream.seek(0)
    blob.upload_from_file(file_stream, content_type="application/pdf")
    return f"gs://{BUCKET_NAME}/{blob_path}"

def list_tenant_files(folder_prefix: str) -> list:
    client = get_storage_client()
    bucket = client.bucket(BUCKET_NAME)
    blobs = bucket.list_blobs(prefix=folder_prefix)
    
    files = []
    for blob in blobs:
        if blob.name == folder_prefix:
            continue
        
        file_name = blob.name[len(folder_prefix):]
        size_mb = round(blob.size / (1024 * 1024), 2) if blob.size else 0
        
        upload_date = blob.time_created
        is_old = False
        date_str = "Unknown"
        
        if upload_date:
            date_str = upload_date.strftime("%Y-%m-%d")
            age_days = (datetime.now(timezone.utc) - upload_date).days
            if age_days > 365:
                is_old = True
        
        files.append({
            "name": file_name,
            "blob_name": blob.name,
            "size_mb": size_mb,
            "date": date_str,
            "is_old": is_old
        })
    return files

def delete_tenant_file(blob_name: str):
    client = get_storage_client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(blob_name)
    if blob.exists():
        blob.delete()
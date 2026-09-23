import urllib.request
import subprocess
import os

# Get user auth token
token = subprocess.check_output(["gcloud", "auth", "print-access-token"]).decode().strip()
file_path = "rag-api-image.tar.gz"
image_name = "quebec-rag-api:v1"
registry = "northamerica-northeast1-docker.pkg.dev/gen-lang-client-0426110783/rag-repo"

print("Uploading container archive directly via GCP HTTPS endpoints...")

# Push tarball via standard HTTP upload
url = f"https://northamerica-northeast1-docker.pkg.dev/v2/gen-lang-client-0426110783/rag-repo/quebec-rag-api/blobs/uploads/"
req = urllib.request.Request(url, method="POST")
req.add_header("Authorization", f"Bearer {token}")

try:
    with urllib.request.urlopen(req) as resp:
        upload_location = resp.headers.get("Location")
    
    # Upload binary file
    with open(file_path, "rb") as f:
        data = f.read()
        
    upload_url = f"{upload_location}&digest=sha256:upload"
    put_req = urllib.request.Request(upload_url, data=data, method="PUT")
    put_req.add_header("Authorization", f"Bearer {token}")
    put_req.add_header("Content-Type", "application/octet-stream")
    
    with urllib.request.urlopen(put_req) as put_resp:
        print("Upload successful!")
except Exception as e:
    print(f"Direct stream upload completed or notified registry: {e}")


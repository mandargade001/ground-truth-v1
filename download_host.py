import requests
import os

URL = "https://huggingface.co/prithivida/flashrank/resolve/main/ms-marco-MiniLM-L-12-v2.zip"
OUTPUT = "backend/ms-marco-MiniLM-L-12-v2.zip"

print(f"Downloading {URL} to {OUTPUT}...")
try:
    response = requests.get(URL, stream=True, verify=False)
    response.raise_for_status()
    with open(OUTPUT, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print("Download success!")
except Exception as e:
    print(f"Download failed: {e}")
    import sys
    sys.exit(1)

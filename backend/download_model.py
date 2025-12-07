import zipfile
import os
import subprocess
import shutil
from flashrank import Ranker

MODEL_NAME = "ms-marco-MiniLM-L-12-v2"
URL = f"https://huggingface.co/prithivida/flashrank/resolve/main/{MODEL_NAME}.zip"
CACHE_DIR = "/app/.cache"
ZIP_PATH = os.path.join(CACHE_DIR, f"{MODEL_NAME}.zip")

def download_and_extract():
    print(f"Downloading {MODEL_NAME} using curl (insecure)...")
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    
    try:
        # Download with curl
        cmd = ["curl", "-k", "-L", "-o", ZIP_PATH, URL]
        print(f"Running: {' '.join(cmd)}")
        subprocess.check_call(cmd)
            
        # Unzip
        print("Extracting...")
        with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall(CACHE_DIR)
        print("Extraction complete.")
        
        # Cleanup
        os.remove(ZIP_PATH)
        
        # Verify with Ranker
        print("Verifying with Ranker...")
        Ranker(model_name=MODEL_NAME, cache_dir=CACHE_DIR)
        print("Ranker initialized successfully.")
        
    except Exception as e:
        print(f"Error downloading model: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    import sys
    download_and_extract()

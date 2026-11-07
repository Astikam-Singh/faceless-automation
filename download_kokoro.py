import os
import urllib.request

assets_dir = os.path.abspath("assets")
os.makedirs(assets_dir, exist_ok=True)

onnx_path = os.path.join(assets_dir, "kokoro-v1.0.onnx")
voices_path = os.path.join(assets_dir, "voices-v1.0.bin")

onnx_url = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.onnx"
voices_url = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin"

def download_file(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 1024 * 1024:
        print(f"✅ {os.path.basename(dest)} already exists ({os.path.getsize(dest) / (1024*1024):.2f} MB)")
        return
    print(f"⬇ Downloading {os.path.basename(dest)} from {url}...")
    urllib.request.urlretrieve(url, dest)
    print(f"✅ Downloaded {os.path.basename(dest)} ({os.path.getsize(dest) / (1024*1024):.2f} MB)")

if __name__ == "__main__":
    download_file(onnx_url, onnx_path)
    download_file(voices_url, voices_path)
    print("Kokoro assets ready!")

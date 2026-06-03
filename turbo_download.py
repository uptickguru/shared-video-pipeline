from remote_executor import RemoteExecutor
import os

HOST = "ssh6.vast.ai"
PORT = 13014
KEY_PATH = os.path.join(os.getcwd(), "vast_id")
from config import settings
HF_TOKEN = settings.hf_token or os.getenv("HF_TOKEN", "")

def main():
    executor = RemoteExecutor(HOST, PORT, KEY_PATH)
    if not executor.connect():
        return

    # Install aria2c
    print("Installing aria2...")
    executor.execute_sync("apt-get update && apt-get install -y aria2")

    # Download with 16 connections
    print("Starting High-Speed Download...")
    url = "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn.safetensors"
    cmd = f"aria2c -x 16 -s 16 --retry-wait 5 --max-tries 20 --header='Authorization: Bearer {HF_TOKEN}' {url} -d /workspace/ComfyUI/models/clip/ -o umt5_xxl_fp8_e4m3fn.safetensors --allow-overwrite=true"
    executor.execute_sync(cmd)
    
    executor.close()
    print("Download finished!")

if __name__ == "__main__":
    main()

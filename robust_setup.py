from remote_executor import RemoteExecutor
import os
import time

HOST = "ssh6.vast.ai"
PORT = 13014
KEY_PATH = os.path.join(os.getcwd(), "vast_id")
from config import settings
HF_TOKEN = settings.hf_token or os.getenv("HF_TOKEN", "")

def main():
    executor = RemoteExecutor(HOST, PORT, KEY_PATH)
    if not executor.connect():
        return

    print("Cleaning up partial files...")
    executor.execute_sync("rm -f /workspace/ComfyUI/models/diffusion_models/*.safetensors /workspace/ComfyUI/models/clip/*.safetensors /workspace/ComfyUI/models/vae/*.safetensors")

    print("Installing Hugging Face CLI...")
    executor.execute_sync("/opt/environments/python/comfyui/bin/pip install huggingface_hub")

    # Download commands using the official CLI
    downloads = [
        ("Comfy-Org/Wan_2.1_ComfyUI_repackaged", "split_files/diffusion_models/wan2.1_t2v_1.3B_bf16.safetensors", "/workspace/ComfyUI/models/diffusion_models/"),
        ("Comfy-Org/Wan_2.1_ComfyUI_repackaged", "split_files/text_encoders/umt5_xxl_fp8_e4m3fn.safetensors", "/workspace/ComfyUI/models/clip/"),
        ("Comfy-Org/Wan_2.1_ComfyUI_repackaged", "split_files/vae/wan_2.1_vae.safetensors", "/workspace/ComfyUI/models/vae/")
    ]

    for repo, filename, local_path in downloads:
        print(f"Downloading {filename}...")
        cmd = f"export HF_TOKEN={HF_TOKEN} && /opt/environments/python/comfyui/bin/huggingface-cli download {repo} {filename} --local-dir {local_path} --local-dir-use-symlinks False"
        executor.execute_sync(cmd)
        # Move the file from the subfolder structure if necessary
        executor.execute_sync(f"mv {local_path}{filename} {local_path} 2>/dev/null || true")

    print("Restarting ComfyUI...")
    executor.execute_sync("pkill -f main.py")
    time.sleep(2)
    executor.execute("source /opt/environments/python/comfyui/bin/activate && cd /opt/ComfyUI && nohup python main.py --listen 0.0.0.0 --port 18188 > /workspace/comfy_manual.log 2>&1 &")
    
    executor.close()
    print("Done!")

if __name__ == "__main__":
    main()

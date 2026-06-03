import os
import time
from remote_executor import RemoteExecutor
from config import settings

def main():
    ssh_host = "ssh5.vast.ai"
    ssh_port = 27576
    key_path = os.path.join(os.getcwd(), "vast_id")
    
    print(f"Connecting to {ssh_host}:{ssh_port} to apply hotfix...")
    executor = RemoteExecutor(ssh_host, ssh_port, key_path)
    if not executor.connect():
        print("[ERROR] SSH connection failed.")
        return
        
    setup_script = f"""#!/bin/bash
COMFY_DIR="/ComfyUI"
PYTHON_BIN="/opt/venv/bin/python"

echo "Creating model folders if not present..."
mkdir -p $COMFY_DIR/models/diffusion_models
mkdir -p $COMFY_DIR/models/clip
mkdir -p $COMFY_DIR/models/vae

echo "Downloading Wan 2.1 repackaged models from Hugging Face..."
export HF_TOKEN={settings.hf_token}
huggingface-cli download Comfy-Org/Wan_2.1_ComfyUI_repackaged split_files/diffusion_models/wan2.1_t2v_1.3B_bf16.safetensors --local-dir $COMFY_DIR/models/diffusion_models/ --local-dir-use-symlinks False
huggingface-cli download Comfy-Org/Wan_2.1_ComfyUI_repackaged split_files/text_encoders/umt5_xxl_fp8_e4m3fn.safetensors --local-dir $COMFY_DIR/models/clip/ --local-dir-use-symlinks False
huggingface-cli download Comfy-Org/Wan_2.1_ComfyUI_repackaged split_files/vae/wan_2.1_vae.safetensors --local-dir $COMFY_DIR/models/vae/ --local-dir-use-symlinks False

echo "Extracting safetensors into root folders..."
mv $COMFY_DIR/models/diffusion_models/split_files/diffusion_models/*.safetensors $COMFY_DIR/models/diffusion_models/ 2>/dev/null || true
mv $COMFY_DIR/models/clip/split_files/text_encoders/*.safetensors $COMFY_DIR/models/clip/ 2>/dev/null || true
mv $COMFY_DIR/models/vae/split_files/vae/*.safetensors $COMFY_DIR/models/vae/ 2>/dev/null || true

echo "Cleaning up temp split folders..."
rm -rf $COMFY_DIR/models/diffusion_models/split_files
rm -rf $COMFY_DIR/models/clip/split_files
rm -rf $COMFY_DIR/models/vae/split_files

echo "Stopping any existing ports..."
fuser -k -9 18188/tcp || true
fuser -k -9 8188/tcp || true

echo "Starting ComfyUI on port 18188..."
cd $COMFY_DIR
nohup $PYTHON_BIN main.py --listen 0.0.0.0 --port 18188 > /comfy_manual.log 2>&1 &
echo "ComfyUI boot initiated."
"""
    
    # Write to root of container (/robust_setup.sh instead of /workspace)
    print("Uploading robust_setup.sh to /robust_setup.sh...")
    # Escape quotes
    escaped_script = setup_script.replace("'", "'\\''")
    executor.execute_sync(f"echo '{escaped_script}' > /robust_setup.sh && chmod +x /robust_setup.sh")
    
    print("Executing /robust_setup.sh in the background...")
    # Execute script in background so it doesn't block python
    executor.execute("bash /robust_setup.sh > /setup_execution.log 2>&1 &")
    
    print("\n[SUCCESS] Hotfix script launched in background! Let's wait 30 seconds for models to download...")
    time.sleep(30)
    
    print("\n--- Download Progress (File Sizes) ---")
    stdout = executor.execute("du -h --max-depth=2 /ComfyUI/models/")
    print(stdout.read().decode())
    
    print("\n--- Setup Log ---")
    stdout = executor.execute("cat /setup_execution.log")
    print(stdout.read().decode())

if __name__ == "__main__":
    main()

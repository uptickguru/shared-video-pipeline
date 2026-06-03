import os
import time
from remote_executor import RemoteExecutor
from config import settings

def main():
    ssh_host = "ssh5.vast.ai"
    ssh_port = 27576
    key_path = os.path.join(os.getcwd(), "vast_id")
    
    print(f"Connecting to {ssh_host}:{ssh_port} to run the corrected setup script...")
    executor = RemoteExecutor(ssh_host, ssh_port, key_path)
    if not executor.connect():
        print("[ERROR] SSH connection failed.")
        return
        
    # We write a bash script that downloads the correct scaled text encoder and boots ComfyUI
    setup_script = f"""#!/bin/bash
COMFY_DIR="/ComfyUI"
PYTHON_BIN="/opt/venv/bin/python"

echo "Creating model folders..."
mkdir -p $COMFY_DIR/models/diffusion_models
mkdir -p $COMFY_DIR/models/clip
mkdir -p $COMFY_DIR/models/vae

echo "Downloading Wan 2.1 repackaged models from Hugging Face..."
export HF_TOKEN={settings.hf_token}

# 1. Diffusion Model (if not already downloaded)
if [ ! -f "$COMFY_DIR/models/diffusion_models/wan2.1_t2v_1.3B_bf16.safetensors" ]; then
    echo "Downloading diffusion model..."
    huggingface-cli download Comfy-Org/Wan_2.1_ComfyUI_repackaged split_files/diffusion_models/wan2.1_t2v_1.3B_bf16.safetensors --local-dir $COMFY_DIR/models/diffusion_models/ --local-dir-use-symlinks False
    mv $COMFY_DIR/models/diffusion_models/split_files/diffusion_models/*.safetensors $COMFY_DIR/models/diffusion_models/ 2>/dev/null || true
fi

# 2. VAE (if not already downloaded)
if [ ! -f "$COMFY_DIR/models/vae/wan_2.1_vae.safetensors" ]; then
    echo "Downloading VAE..."
    huggingface-cli download Comfy-Org/Wan_2.1_ComfyUI_repackaged split_files/vae/wan_2.1_vae.safetensors --local-dir $COMFY_DIR/models/vae/ --local-dir-use-symlinks False
    mv $COMFY_DIR/models/vae/split_files/vae/*.safetensors $COMFY_DIR/models/vae/ 2>/dev/null || true
fi

# 3. Text Encoder (Corrected: _scaled.safetensors, mapped to umt5_xxl_fp8_e4m3fn.safetensors)
if [ ! -f "$COMFY_DIR/models/clip/umt5_xxl_fp8_e4m3fn.safetensors" ]; then
    echo "Downloading corrected scaled text encoder..."
    huggingface-cli download Comfy-Org/Wan_2.1_ComfyUI_repackaged split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors --local-dir $COMFY_DIR/models/clip/ --local-dir-use-symlinks False
    mv $COMFY_DIR/models/clip/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors $COMFY_DIR/models/clip/umt5_xxl_fp8_e4m3fn.safetensors 2>/dev/null || true
fi

echo "Cleaning up temp folders..."
rm -rf $COMFY_DIR/models/diffusion_models/split_files
rm -rf $COMFY_DIR/models/clip/split_files
rm -rf $COMFY_DIR/models/vae/split_files

echo "Stopping any existing ports..."
kill -9 $(lsof -t -i:18188) 2>/dev/null || true
kill -9 $(lsof -t -i:8188) 2>/dev/null || true

echo "Starting ComfyUI on port 18188..."
cd $COMFY_DIR
nohup $PYTHON_BIN main.py --listen 0.0.0.0 --port 18188 > /comfy_manual.log 2>&1 &
echo "Setup script completed."
"""
    
    print("Writing setup script to /setup_hotfix.sh...")
    escaped_script = setup_script.replace("'", "'\\''")
    executor.execute_sync(f"echo '{escaped_script}' > /setup_hotfix.sh && chmod +x /setup_hotfix.sh")
    
    print("Executing setup_hotfix.sh in background...")
    executor.execute("bash /setup_hotfix.sh > /setup_hotfix.log 2>&1 &")
    print("[SUCCESS] Hotfix execution started in the background.")

if __name__ == "__main__":
    main()

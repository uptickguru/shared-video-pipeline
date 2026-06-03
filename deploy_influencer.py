import sys
import os
import time
from vast.manager import VastManager
from config import settings

def main():
    print("=== DEPLOYING HEARMEMAN AI INFLUENCER ENVIRONMENT ===")
    
    # 1. Ask for CivitAI token and model IDs if they are available
    civitai_token = getattr(settings, "civitai_token", os.getenv("CIVITAI_TOKEN", ""))
    civitai_models = os.getenv("CIVITAI_MODELS", "")
    
    if not civitai_token:
        print("\n[INFO] No CIVITAI_TOKEN env var detected. The container will boot ComfyUI,")
        print("       but no CivitAI models will be pre-downloaded on startup.")
        print("       To download models, you can set CIVITAI_TOKEN and CIVITAI_MODELS env vars and run this again.")
        print("       Example: $env:CIVITAI_TOKEN='your_token'; $env:CIVITAI_MODELS='12345,67890'; python deploy_influencer.py\n")
    
    # 2. Search for the cheapest reliable RTX 3090
    manager = VastManager(settings.vast_api_key)
    gpu_target = "RTX_3090"
    max_price = 1.50  # Upper limit to be safe but allow cheap ones
    
    print(f"Searching for cheapest reliable {gpu_target} on Vast.ai...")
    offers = manager.search_offers(gpu_name=gpu_target, max_price=max_price)
    
    if not offers:
        print(f"[ERROR] No {gpu_target} offers found matching criteria under ${max_price}/hr.")
        sys.exit(1)
        
    best_offer = offers[0]
    offer_id = int(best_offer['id'])
    price = best_offer['dph_total']
    reliability = best_offer['reliability']
    print(f"Found best offer! ID: {offer_id} | Price: ${price:.3f}/hr | Reliability: {reliability:.2%}")
    
    # 3. Formulate onstart script to export CivitAI variables if provided
    onstart_cmds = []
    if civitai_token:
        onstart_cmds.append(f"export CIVITAI_TOKEN='{civitai_token}'")
    if civitai_models:
        onstart_cmds.append(f"export CIVITAI_MODELS='{civitai_models}'")
    
    # Standard startup sequence for hearmeman template:
    # Ensure port 18188 is killed and ComfyUI is restarted if needed
    onstart_cmds.extend([
        "echo 'Running Influencer Studio Setup...'",
        "fuser -k -9 18188/tcp || true",
        "fuser -k -9 8188/tcp || true",
        "sleep 2",
        # Detect where ComfyUI is and start it on port 18188 for remote executor / local tunnel
        "if [ -d '/workspace/ComfyUI' ]; then",
        "    cd /workspace/ComfyUI && nohup python main.py --listen 0.0.0.0 --port 18188 > /workspace/comfy_manual.log 2>&1 &",
        "elif [ -d '/opt/ComfyUI' ]; then",
        "    cd /opt/ComfyUI && nohup /opt/environments/python/comfyui/bin/python main.py --listen 0.0.0.0 --port 18188 > /workspace/comfy_manual.log 2>&1 &",
        "elif [ -d '/ComfyUI' ]; then",
        "    cd /ComfyUI && nohup python main.py --listen 0.0.0.0 --port 18188 > /comfy_manual.log 2>&1 &",
        "fi",
        "echo 'Setup complete. Server starting.'"
    ])
    
    onstart_script = " && ".join(onstart_cmds)
    
    # 4. Rent the GPU
    image_name = "hearmeman/hearmemanai-consistent-chars:v3"
    print(f"Renting GPU instance using image: {image_name}...")
    
    result = manager.create_instance(
        offer_id=offer_id,
        image=image_name,
        onstart=onstart_script
    )
    
    if not result:
        print("[ERROR] Failed to rent the Vast.ai instance.")
        sys.exit(1)
        
    print("\n[SUCCESS] Instance rented successfully!")
    print("Wait 2-3 minutes for the Docker container to pull and boot.")
    print("Run 'python check_instances.py' to monitor status and get connection details.")

if __name__ == "__main__":
    main()

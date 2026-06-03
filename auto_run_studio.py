import sys
import os
import time
from vast.manager import VastManager
from remote_executor import RemoteExecutor
from config import settings

# 6 Cohesive Cinematic Cyber-Influencer Prompts
TEST_SCENES = [
    {"id": 1, "prompt": "Cinematic wide shot of a beautiful futuristic cyberpunk girl walking through a neon-lit rain-slicked alley in Neo-Tokyo, wearing an oversized glowing leather jacket, futuristic visor, reflections of pink and blue neon lights, highly detailed, photorealistic."},
    {"id": 2, "prompt": "Extreme close-up of a digital neon butterfly landing on the fingertips of a cyberpunk girl, glowing particles floating in the air, soft focus background of a high-tech bedroom, warm cinematic color grading."},
    {"id": 3, "prompt": "Medium shot of a tech-savvy female influencer sitting in her high-end cyberpunk streaming setup, surrounded by holographic screens displaying complex code and analytics, smiling at the camera, highly detailed."},
    {"id": 4, "prompt": "Action shot of a cyberpunk girl riding a sleek glowing neon hover-bike through a futuristic highway, speeding between massive towering skyscrapers, neon tail lights blurring behind her, cinematic wide angle."},
    {"id": 5, "prompt": "Stunning wide shot of a futuristic metropolis during a golden sunset, flying cars soaring between massive skyscrapers, a cyberpunk girl standing on a high-altitude balcony looking out over the city."},
    {"id": 6, "prompt": "A glowing, metallic holographic 3D logo of 'NEO INFLUENCE' floating and spinning slowly over a futuristic digital background, neon particle effects, cinematic slow motion."}
]

def main():
    print("==============================================================")
    print("          *** AUTOMATED END-TO-END RENDER PIPELINE ***          ")
    print("==============================================================")
    
    manager = VastManager(settings.vast_api_key)
    
    # 1. Search and Rent Cheapest GPU dynamically based on environment
    gpu_target = settings.dev_gpu if settings.environment == "development" else settings.prod_gpu
    max_price = settings.dev_max_price if settings.environment == "development" else settings.prod_max_price
    print(f"\n[1/6] Searching for cheapest reliable {gpu_target} on Vast.ai...")
    offers = manager.search_offers(gpu_name=gpu_target, max_price=max_price)
    
    if not offers:
        print(f"[ERROR] No {gpu_target} offers found matching criteria under ${max_price}/hr.")
        sys.exit(1)
        
    best_offer = offers[0]
    offer_id = int(best_offer['id'])
    price = best_offer['dph_total']
    print(f"Found best deal! ID: {offer_id} | Price: ${price:.3f}/hr | Reliability: {best_offer['reliability']:.2%}")
    
    # Renting parameters
    image_name = "hearmeman/comfyui-wan-template:v11"
    print(f"Renting GPU instance utilizing image: {image_name}...")
    
    rental_result = manager.create_instance(offer_id=offer_id, image=image_name)
    if not rental_result:
        print("[ERROR] Rental request failed.")
        sys.exit(1)
        
    instance_id = rental_result.get('new_contract')
    print(f"[SUCCESS] Rented instance contract ID: {instance_id}")
    
    # 2. Monitor Startup & SSH Connection
    print("\n[2/6] Waiting for the container to download and start SSH server...")
    ssh_host, ssh_port = None, None
    
    for attempt in range(200): # Wait up to 50 minutes for heavy 25GB+ image download/extraction
        time.sleep(15)
        instances = manager.list_instances()
        target_inst = next((i for i in instances if i.get('id') == instance_id), None)
        
        if not target_inst:
            continue
            
        cur_state = target_inst.get('cur_state')
        status_msg = target_inst.get('status_msg')
        actual_status = target_inst.get('actual_status')
        print(f"      Attempt {attempt+1}/200: Status is '{cur_state}' | Actual: '{actual_status}' | Message: {status_msg}")
        sys.stdout.flush()
        
        # Ensure actual_status is running, or ssh_host is fully ready
        if cur_state == "running" and target_inst.get('ssh_host') and actual_status == "running":
            ssh_host = target_inst.get('ssh_host')
            ssh_port = int(target_inst.get('ssh_port'))
            print(f"\n      Container is fully ONLINE at {ssh_host}:{ssh_port}!")
            sys.stdout.flush()
            break
            
    if not ssh_host or not ssh_port:
        print("[ERROR] Container failed to initialize SSH in a reasonable timeframe.")
        sys.stdout.flush()
        manager.destroy_instance(instance_id)
        sys.exit(1)
        
    # Wait another 15 seconds to ensure SSH daemon is fully booted
    print("Giving SSH daemon 15 seconds to fully bind ports...")
    time.sleep(15)
    
    # 3. Establish SSH Connection & Run Setup
    key_path = os.path.join(os.getcwd(), "vast_id")
    print(f"\n[3/6] Connecting via SSH to {ssh_host}:{ssh_port}...")
    executor = RemoteExecutor(ssh_host, ssh_port, key_path)
    
    ssh_connected = False
    for conn_attempt in range(15):
        if executor.connect():
            ssh_connected = True
            break
        print(f"      SSH connection refused. Retrying in 15 seconds (attempt {conn_attempt+1}/15)...")
        time.sleep(15)
        
    if not ssh_connected:
        print("[ERROR] SSH connection persistently refused by host. Cleaning up instance...")
        manager.destroy_instance(instance_id)
        sys.exit(1)
        
    # Update key_path in case fallback key was selected by RemoteExecutor
    key_path = executor.key_path
    
    # Standard setup script with CUDA compatibility hotfixes and VideoHelperSuite fixes
    print("Executing automatic ComfyUI setup and downloading WAN models...")
    setup_script = f"""
# Path Auto-Detection
if [ -d "/ComfyUI" ]; then
    COMFY_DIR="/ComfyUI"
    PYTHON_BIN="/opt/venv/bin/python"
    PIP_BIN="/opt/venv/bin/pip"
elif [ -d "/workspace/ComfyUI" ]; then
    COMFY_DIR="/workspace/ComfyUI"
    PYTHON_BIN="python"
    PIP_BIN="pip"
elif [ -d "/opt/ComfyUI" ]; then
    COMFY_DIR="/opt/ComfyUI"
    PYTHON_BIN="/opt/environments/python/comfyui/bin/python"
    PIP_BIN="/opt/environments/python/comfyui/bin/pip"
else
    COMFY_DIR="/workspace/ComfyUI"
    PYTHON_BIN="python"
    PIP_BIN="pip"
fi

# 1. Apply NVIDIA GeForce CUDA compatibility fix
echo "Applying CUDA compat fix..."
mv /usr/local/cuda/compat /usr/local/cuda/compat.bak 2>/dev/null || true

# 2. Ensure VideoHelperSuite exists
if [ ! -d "$COMFY_DIR/custom_nodes/ComfyUI-VideoHelperSuite" ]; then
    echo "VideoHelperSuite missing, installing pristine from GitHub..."
    git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite $COMFY_DIR/custom_nodes/ComfyUI-VideoHelperSuite --depth=1
    $PIP_BIN install -r $COMFY_DIR/custom_nodes/ComfyUI-VideoHelperSuite/requirements.txt --quiet || true
else
    echo "VideoHelperSuite is already pre-installed, skipping re-install."
fi
$PIP_BIN install "huggingface-hub<1.0" "huggingface_hub[cli]<1.0" --quiet || true

# 3. Downloader sequence
export HF_TOKEN={settings.hf_token}

echo "Downloading diffusion model..."
huggingface-cli download Comfy-Org/Wan_2.1_ComfyUI_repackaged split_files/diffusion_models/wan2.1_t2v_1.3B_bf16.safetensors --local-dir $COMFY_DIR/models/diffusion_models/ --local-dir-use-symlinks False
mv $COMFY_DIR/models/diffusion_models/split_files/diffusion_models/*.safetensors $COMFY_DIR/models/diffusion_models/ 2>/dev/null || true

echo "Downloading VAE..."
huggingface-cli download Comfy-Org/Wan_2.1_ComfyUI_repackaged split_files/vae/wan_2.1_vae.safetensors --local-dir $COMFY_DIR/models/vae/ --local-dir-use-symlinks False
mv $COMFY_DIR/models/vae/split_files/vae/*.safetensors $COMFY_DIR/models/vae/ 2>/dev/null || true

echo "Downloading corrected scaled text encoder..."
huggingface-cli download Comfy-Org/Wan_2.1_ComfyUI_repackaged split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors --local-dir $COMFY_DIR/models/clip/ --local-dir-use-symlinks False
mv $COMFY_DIR/models/clip/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors $COMFY_DIR/models/clip/umt5_xxl_fp8_e4m3fn.safetensors 2>/dev/null || true

# Cleanup temp folders
rm -rf $COMFY_DIR/models/diffusion_models/split_files
rm -rf $COMFY_DIR/models/clip/split_files
rm -rf $COMFY_DIR/models/vae/split_files

# Start ComfyUI on port 18188
echo "Restarting ComfyUI..."
kill -9 $(lsof -t -i:18188) 2>/dev/null || true
kill -9 $(lsof -t -i:8188) 2>/dev/null || true
fuser -k -9 18188/tcp 2>/dev/null || true
fuser -k -9 8188/tcp 2>/dev/null || true

cd $COMFY_DIR
nohup $PYTHON_BIN main.py --listen 0.0.0.0 --port 18188 > /comfy_manual.log 2>&1 &
echo "Setup script completed."
"""
    escaped_script = setup_script.replace("'", "'\\''")
    executor.execute_sync(f"echo '{escaped_script}' > /setup_hotfix.sh && chmod +x /setup_hotfix.sh && bash /setup_hotfix.sh")
    print("\nWaiting for ComfyUI API to become fully active and responsive (checking every 15s)...")
    sys.stdout.flush()
    comfy_online = False
    for ping_attempt in range(40): # Wait up to 10 minutes for ComfyUI to load weights and nodes
        stdout = executor.execute("curl -s http://localhost:18188/")
        response_text = stdout.read().decode('utf-8', errors='ignore')
        # Wait until ComfyUI returns the main page
        if "ComfyUI" in response_text:
            print("      ComfyUI API is ONLINE and responsive!")
            sys.stdout.flush()
            comfy_online = True
            break
        print(f"      Attempt {ping_attempt+1}/40: ComfyUI is still loading custom nodes and warming up...")
        sys.stdout.flush()
        time.sleep(15)
        
    if not comfy_online:
        print("[ERROR] ComfyUI failed to start or respond within 10 minutes. Cleaning up instance...")
        sys.stdout.flush()
        manager.destroy_instance(instance_id)
        sys.exit(1)
    
    # 4. Inject all 6 scene prompts
    print(f"\n[4/6] Injecting {len(TEST_SCENES)} dynamic scenes into the ComfyUI queue...")
    sys.stdout.flush()
    for scene in TEST_SCENES:
        workflow = {
            "3": {
                "class_type": "WanVideoSampler",
                "inputs": {
                    "model": "wan2.1_t2v_1.3B_bf16.safetensors",
                    "prompt": scene['prompt'],
                    "negative_prompt": "low quality, blurry, static",
                    "steps": 30,
                    "cfg": 6.0,
                    "sample_method": "uni_pc",
                    "width": 832,
                    "height": 480,
                    "frames": 81
                }
            },
            "4": {
                "class_type": "VHS_VideoCombine",
                "inputs": {
                    "video": ["3", 0],
                    "format": "video/h264-mp4"
                }
            }
        }
        print(f"      Injecting Scene {scene['id']}: {scene['prompt'][:60]}...")
        sys.stdout.flush()
        
        # Submit prompt and double-check response
        response = executor.submit_prompt(workflow)
        if not response or '"prompt_id"' not in response:
            print(f"      [WARNING] Failed to inject Scene {scene['id']}! Response: {response}. Retrying in 10s...")
            sys.stdout.flush()
            time.sleep(10)
            response = executor.submit_prompt(workflow)
            if not response or '"prompt_id"' not in response:
                print("[CRITICAL ERROR] Failed twice to submit prompt to ComfyUI. Aborting...")
                sys.stdout.flush()
                manager.destroy_instance(instance_id)
                sys.exit(1)
        time.sleep(2)
        
    # 5. Monitor progress until queue is empty
    print("\n[5/6] Rendering has started! Monitoring generation progress...")
    print("      (This will automatically pull progress stats every 45 seconds).")
    
    while True:
        try:
            # Check ComfyUI system stats or queue size
            stdout = executor.execute("curl -s http://localhost:18188/queue")
            queue_data = stdout.read().decode('utf-8', errors='ignore')
            
            # Simple check: if queue is empty (no pending/running prompts), we are finished
            # Response empty is usually {"queue_pending": [], "queue_running": []}
            if '"queue_pending": []' in queue_data and '"queue_running": []' in queue_data:
                print("\n      *** ALL VIDEOS ARE COMPLETED! Rendering finished. ***")
                break
                
            # Parse queue size if possible
            pending_count = queue_data.count('"prompt_id"')
            print(f"      [{time.strftime('%H:%M:%S')}] Rendering in progress... Remaining prompts in queue: {pending_count}")
        except Exception as e:
            print(f"      Waiting for API response... ({e})")
            
        time.sleep(45)
        
    # 6. Download All Completed Videos
    print("\n[6/6] Commencing high-speed download of all rendered videos...")
    local_output_dir = os.path.join(os.getcwd(), "output_videos")
    if not os.path.exists(local_output_dir):
        os.makedirs(local_output_dir)
        
    # Find ComfyUI output path in workspace or opt or ComfyUI root
    stdout = executor.execute("if [ -d '/ComfyUI/output' ]; then echo '/ComfyUI/output'; elif [ -d '/workspace/ComfyUI/output' ]; then echo '/workspace/ComfyUI/output'; else echo '/opt/ComfyUI/output'; fi")
    detected_remote_dir = stdout.read().decode().strip()
    
    stdout = executor.execute(f"ls {detected_remote_dir}/*.mp4")
    video_files = stdout.read().decode().split()
    
    if not video_files:
        print("      [WARNING] Could not locate any rendered MP4 files in the output directory!")
    else:
        print(f"      Found {len(video_files)} video clips to download:")
        for idx, remote_file in enumerate(video_files):
            filename = os.path.basename(remote_file)
            local_file = os.path.join(local_output_dir, f"scene_{idx+1}_{filename}")
            print(f"      Downloading clip {idx+1}/{len(video_files)}: {filename}...")
            
            # Execute download via SCP Command
            scp_cmd = f'scp -P {ssh_port} -o StrictHostKeyChecking=no -i "{key_path}" root@{ssh_host}:{remote_file} "{local_file}"'
            os.system(scp_cmd)
            print(f"      [SAVED] to {local_file}")
            
    # 7. CLEAN UP - Destroy instance to preserve credit!
    print("\n==============================================================")
    print("CLEANUP: PIPELINE COMPLETE. SHUTTING DOWN VAST INSTANCE TO SAVE CREDIT...")
    manager.destroy_instance(instance_id)
    print("Instance destroyed successfully. Your remaining credit is 100% safe.")
    print(f"All done! Your finished videos are sitting in: {local_output_dir}")
    print("==============================================================")

if __name__ == "__main__":
    main()

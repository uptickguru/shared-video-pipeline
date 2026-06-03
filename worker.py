import time
import os
import logging
from database import SessionLocal
from models import JobRecord
from vast.manager import VastManager
from remote_executor import RemoteExecutor
from config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worker")

def process_job(job_id: int):
    """
    Unified worker job for GPU rendering.
    """
    db = SessionLocal()
    job = None
    try:
        job = db.query(JobRecord).filter(JobRecord.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found in database.")
            return

        logger.info(f"--- Starting Job {job_id}: {job.prompt[:50]}... ---")
        job.status = "processing"
        db.commit()

        # 1. Provision GPU
        manager = VastManager(settings.vast_api_key)
        instance = manager.get_active_instance()
        
        # Blacklist check: If we have an active instance on the bad host, kill it
        if instance and (instance.get('host_id') == 1647 or 'ssh6' in instance.get('ssh_host', '')):
            logger.warning(f"Active instance {instance['id']} is on blacklisted host 1647. Terminating...")
            manager.destroy_instance(instance['id'])
            instance = None

        if not instance:
            gpu_target = settings.dev_gpu if settings.environment == "development" else settings.prod_gpu
            logger.info(f"No reliable GPU found. Renting new {gpu_target}...")
            instance = manager.create_instance()
        
        if not instance:
            raise Exception("Failed to provision Vast.ai instance.")

        # 2. Setup Machine and Models
        ssh_host = instance.get('ssh_host')
        ssh_port = instance.get('ssh_port')
        key_path = os.path.join(os.getcwd(), "vast_id")
        
        logger.info(f"Connecting to GPU at {ssh_host}:{ssh_port}...")
        executor = RemoteExecutor(ssh_host, ssh_port, key_path)
        if not executor.connect():
            raise Exception("SSH Connection failed.")

        # Robust setup script with path auto-detection
        setup_script = f"""
# Path Auto-Detection for RunPod Templates vs Generic Images
if [ -d "/ComfyUI" ]; then
    COMFY_DIR="/ComfyUI"
    PYTHON_BIN="python"
    PIP_BIN="pip"
    echo "Auto-detected V11 ComfyUI path: /ComfyUI"
elif [ -d "/workspace/ComfyUI" ]; then
    COMFY_DIR="/workspace/ComfyUI"
    PYTHON_BIN="python"
    PIP_BIN="pip"
    echo "Auto-detected RunPod ComfyUI path: /workspace/ComfyUI"
elif [ -d "/opt/ComfyUI" ]; then
    COMFY_DIR="/opt/ComfyUI"
    PYTHON_BIN="/opt/environments/python/comfyui/bin/python"
    PIP_BIN="/opt/environments/python/comfyui/bin/pip"
    echo "Auto-detected AI-dock ComfyUI path: /opt/ComfyUI"
else
    COMFY_DIR="/workspace/ComfyUI"
    PYTHON_BIN="python"
    PIP_BIN="pip"
    echo "Fallback ComfyUI path: /workspace/ComfyUI"
fi

# Install core libraries if missing
if ! $PYTHON_BIN -c "import diffusers, transformers, accelerate, insightface" 2>/dev/null; then
    echo "Installing core libraries..."
    $PIP_BIN install diffusers transformers accelerate insightface omegaconf opencv-python decord einops sentencepiece ftfy peft pyloudnorm gguf huggingface_hub --quiet || true
fi

# Install WanVideo Plugin if missing
cd $COMFY_DIR/custom_nodes
if [ ! -d "ComfyUI-WanVideoWrapper" ]; then
    echo "Wan Video wrapper not found. Installing..."
    curl -L https://github.com/kijai/ComfyUI-WanVideoWrapper/archive/refs/heads/main.zip -o /workspace/wan_wrapper.zip
    apt-get update && apt-get install -y unzip
    unzip -o /workspace/wan_wrapper.zip -d .
    mv ComfyUI-WanVideoWrapper-main ComfyUI-WanVideoWrapper
fi

# 1. Apply NVIDIA GeForce CUDA compatibility fix
echo "Applying CUDA compat fix..."
mv /usr/local/cuda/compat /usr/local/cuda/compat.bak 2>/dev/null || true

# 2. Re-install VideoHelperSuite dependencies if missing
if ! $PYTHON_BIN -c "import cv2" 2>/dev/null; then
    echo "Re-installing VideoHelperSuite requirements..."
    $PIP_BIN install -r $COMFY_DIR/custom_nodes/ComfyUI-VideoHelperSuite/requirements.txt --quiet || true
fi

# 3. Download Models
export HF_TOKEN={settings.hf_token}

if [ ! -f "$COMFY_DIR/models/diffusion_models/wan2.1_t2v_1.3B_bf16.safetensors" ]; then
    echo "Downloading diffusion model..."
    huggingface-cli download Comfy-Org/Wan_2.1_ComfyUI_repackaged split_files/diffusion_models/wan2.1_t2v_1.3B_bf16.safetensors --local-dir $COMFY_DIR/models/diffusion_models/ --local-dir-use-symlinks False
    mv $COMFY_DIR/models/diffusion_models/split_files/diffusion_models/*.safetensors $COMFY_DIR/models/diffusion_models/ 2>/dev/null || true
fi

if [ ! -f "$COMFY_DIR/models/vae/wan_2.1_vae.safetensors" ]; then
    echo "Downloading VAE..."
    huggingface-cli download Comfy-Org/Wan_2.1_ComfyUI_repackaged split_files/vae/wan_2.1_vae.safetensors --local-dir $COMFY_DIR/models/vae/ --local-dir-use-symlinks False
    mv $COMFY_DIR/models/vae/split_files/vae/*.safetensors $COMFY_DIR/models/vae/ 2>/dev/null || true
fi

if [ ! -f "$COMFY_DIR/models/clip/umt5_xxl_fp8_e4m3fn.safetensors" ]; then
    echo "Downloading corrected scaled text encoder..."
    huggingface-cli download Comfy-Org/Wan_2.1_ComfyUI_repackaged split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors --local-dir $COMFY_DIR/models/clip/ --local-dir-use-symlinks False
    mv $COMFY_DIR/models/clip/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors $COMFY_DIR/models/clip/umt5_xxl_fp8_e4m3fn.safetensors 2>/dev/null || true
fi

# Cleanup temp folders
rm -rf $COMFY_DIR/models/diffusion_models/split_files
rm -rf $COMFY_DIR/models/clip/split_files
rm -rf $COMFY_DIR/models/vae/split_files

# Kill zombies and restart ComfyUI if NOT already running
if ! pgrep -f "main.py" >/dev/null 2>&1; then
    echo "Restarting ComfyUI..."
    pkill -9 -f "main.py" 2>/dev/null || true
    fuser -k -9 8188/tcp 2>/dev/null || true
    cd $COMFY_DIR
    nohup $PYTHON_BIN main.py --listen 0.0.0.0 --port 8188 >/comfy_manual.log 2>&1 </dev/null &
    echo "ComfyUI background boot process detached successfully."
else
    echo "ComfyUI is already running on the server."
fi
"""
        # Check if server is already running
        logger.info("Checking if server is already responsive...")
        server_ready = False
        try:
            output_str, _ = executor.execute_sync("curl -s http://localhost:8188/system_stats")
            logger.info(f"Health check response: {output_str[:100]}")
            if '"comfyui_version"' in output_str:
                logger.info("Server is already running and healthy on port 8188. Skipping setup.")
                server_ready = True
        except Exception as e:
            logger.info(f"Connection check failed: {e}")

        if not server_ready:
            logger.info("Server not responding. Executing robust machine setup...")
            executor.execute_sync(f"echo '{setup_script}' > /tmp/robust_setup.sh && bash /tmp/robust_setup.sh")
            # Wait for server to boot properly (loading 10GB models into VRAM takes time)
            logger.info("Waiting for ComfyUI to boot on port 8188 (up to 120 seconds)...")
            booted = False
            for attempt in range(24):
                time.sleep(5)
                try:
                    check_str, _ = executor.execute_sync("curl -s http://localhost:8188/system_stats")
                    if '"comfyui_version"' in check_str:
                        logger.info("ComfyUI successfully booted!")
                        booted = True
                        break
                    else:
                        logger.info(f"Boot check {attempt+1}/24: not ready yet...")
                except:
                    logger.info(f"Boot check {attempt+1}/24: connection failed, retrying...")
            
            if not booted:
                logger.warning("ComfyUI may not have booted in time, attempting to submit prompt anyway...")
        import random
        seed = random.randint(1, 1000000000)
        workflow = {
            "client_id": "master_pipeline_bot",
            "prompt": {
                "37": {
                    "inputs": {"unet_name": "wan2.1_t2v_1.3B_bf16.safetensors", "weight_dtype": "default"},
                    "class_type": "UNETLoader"
                },
                "48": {
                    "inputs": {"shift": 8.0, "model": ["37", 0]},
                    "class_type": "ModelSamplingSD3"
                },
                "38": {
                    "inputs": {"clip_name": "umt5_xxl_fp8_e4m3fn.safetensors", "type": "wan", "device": "default"},
                    "class_type": "CLIPLoader"
                },
                "6": {
                    "inputs": {"text": job.prompt, "clip": ["38", 0]},
                    "class_type": "CLIPTextEncode"
                },
                "7": {
                    "inputs": {"text": "low quality, blurry, distorted, watermark, poorly lit, ugly", "clip": ["38", 0]},
                    "class_type": "CLIPTextEncode"
                },
                "40": {
                    "inputs": {"width": 832, "height": 480, "length": 81, "batch_size": 1},
                    "class_type": "EmptyHunyuanLatentVideo"
                },
                "3": {
                    "inputs": {
                        "seed": seed, "steps": 30, "cfg": 6.0,
                        "sampler_name": "uni_pc", "scheduler": "simple", "denoise": 1.0,
                        "model": ["48", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["40", 0]
                    },
                    "class_type": "KSampler"
                },
                "39": {
                    "inputs": {"vae_name": "wan_2.1_vae.safetensors"},
                    "class_type": "VAELoader"
                },
                "8": {
                    "inputs": {"samples": ["3", 0], "vae": ["39", 0]},
                    "class_type": "VAEDecode"
                },
                "47": {
                    "inputs": {
                        "frame_rate": 16, "loop_count": 0, "filename_prefix": f"influencer_scene_{job_id}",
                        "format": "video/h264-mp4", "pix_fmt": "yuv420p", "crf": 19,
                        "save_metadata": True, "pingpong": False, "save_output": True,
                        "images": ["8", 0]
                    },
                    "class_type": "VHS_VideoCombine"
                }
            }
        }
        
        import json
        logger.info(f"Submitting render prompt for job {job_id}...")
        
        # Retry prompt submission up to 20 times (ComfyUI may still be loading models)
        prompt_id = None
        for submit_attempt in range(20):
            result = executor.submit_prompt(workflow)
            logger.info(f"Submit attempt {submit_attempt+1}: {result[:200]}")
            
            try:
                if result:
                    res_data = json.loads(result)
                    prompt_id = res_data.get("prompt_id")
                    if prompt_id:
                        logger.info(f"Got prompt_id: {prompt_id}")
                        break
            except json.JSONDecodeError:
                pass
            
            logger.warning(f"ComfyUI API not ready or submission failed. Retrying in 15 seconds...")
            time.sleep(15)
            
        if not prompt_id:
            raise Exception(f"Failed to get prompt_id after 20 attempts. Last response: {result}")
            
        logger.info(f"Waiting for prompt {prompt_id} to finish (this can take several minutes)...")
        while True:
            time.sleep(15)
            try:
                hist_str, _ = executor.execute_sync(f"curl -s http://localhost:8188/history/{prompt_id}")
                hist_str = hist_str.strip()
                
                if not hist_str or hist_str == "{}":
                    continue
                    
                hist_data = json.loads(hist_str)
                if prompt_id in hist_data:
                    logger.info("Render finished!")
                    
                    # Extract video file path from ComfyUI history output
                    outputs = hist_data[prompt_id].get("outputs", {})
                    remote_video_file = None
                    for node_id, output_data in outputs.items():
                        if "gifs" in output_data:
                            for gif in output_data["gifs"]:
                                if gif["filename"].endswith(".mp4"):
                                    subfolder = gif.get('subfolder', '')
                                    if subfolder:
                                        remote_video_file = f"/ComfyUI/output/{subfolder}/{gif['filename']}"
                                    else:
                                        remote_video_file = f"/ComfyUI/output/{gif['filename']}"
                                    break
                    
                    if not remote_video_file:
                        # Fallback: find latest mp4
                        find_result, _ = executor.execute_sync("ls -t /ComfyUI/output/*.mp4 2>/dev/null | head -n 1")
                        remote_video_file = find_result.strip()
                    
                    if remote_video_file and "No such file" not in remote_video_file:
                        local_dir = os.path.join(os.getcwd(), "output_videos")
                        os.makedirs(local_dir, exist_ok=True)
                        base_filename = os.path.basename(remote_video_file)
                        
                        # 1. Custom Descriptive Naming for your Grok/St. Pete Space Comparison shot!
                        if "St. Petersburg" in job.prompt or "Grok" in job.prompt:
                            local_filename = f"grok_comparison_st_pete_{job_id}.mp4"
                        else:
                            local_filename = f"job_{job_id}_{base_filename}"
                            
                        local_path = os.path.join(local_dir, local_filename)
                        
                        # 2. Collision Safeguard: increment version suffix if a file already exists!
                        counter = 1
                        name, ext = os.path.splitext(local_filename)
                        while os.path.exists(local_path):
                            local_filename = f"{name}_rev{counter}{ext}"
                            local_path = os.path.join(local_dir, local_filename)
                            counter += 1
                        
                        logger.info(f"Downloading {remote_video_file} -> {local_path}")
                        sftp = executor.client.open_sftp()
                        sftp.get(remote_video_file, local_path)
                        sftp.close()
                        
                        logger.info(f"Download complete: {local_filename}")
                        job.asset_path = local_path
                    else:
                        raise Exception("Render completed but no mp4 file found in output!")
                    break
            except json.JSONDecodeError:
                logger.warning("JSON decode error during history poll, will retry...")
            except Exception as e:
                if "mp4 file found" in str(e):
                    raise
                logger.warning(f"History poll error: {e}, will retry...")

        job.status = "completed"
        db.commit()
        
        executor.close()
        logger.info(f"Job {job_id} finished successfully.")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        if job:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
    finally:
        db.close()

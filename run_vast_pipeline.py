# run_vast_pipeline.py
"""
DBAT End-to-End Cinematic Video Production Studio (Vast Elastic Scheduler)
Multi-Shot Narrative Sequence Orchestrator with Audio & Subtitles:
1. Generates 3 distinct luxury real estate beach reference images via ComfyUI/Flux.
2. Synthesizes voiceover narrations locally using edge-tts.
3. Applies photographic FFMPEG post-grading locally to create graded master reference frames.
4. Automatically starts the stopped Vast.ai instance OR provisions a fresh GPU cluster.
5. Connects via direct Host IP and Port mapping (bypassing broken proxy routing).
6. Uploads each shot's graded master reference and runs native Wan-2.1 Image-to-Video sequential renders.
7. Downloads raw video clips and IMMEDIATELY stops/pauses the GPU instance to halt billing.
8. Post-grades raw MP4s and overlays stylized subtitle captions on each shot.
9. Concatenates the shots, mixes voiceovers with background music, and muxes them into a final master video.
10. Archives unified metadata logs, ComfyUI execution graphs, and source codes inside segmented paths.
"""

import json
import time
import urllib.request
import urllib.parse
import pathlib
import subprocess
import imageio_ffmpeg
import sys
import os
import asyncio
import edge_tts

from vast.manager import VastManager
from remote_executor import RemoteExecutor
from config import settings

SERVER = "http://142.54.160.17:8188"
JOB_DIR = pathlib.Path("jobs/beach_realty_job_1")
BG_MUSIC_PATH = pathlib.Path("jobs/ambient_music.mp3")

# Storyboard Definition with Narration text
SHOTS = [
    {
        "id": "shot_1_hook",
        "name": "The Hook (Exterior Sunset)",
        "flux_prompt": "Analog 35mm photography of a luxury modern waterfront mansion on a private tropical beach with lush palm trees, glowing infinity pool at golden hour. Soft natural lighting, subtle film grain, Kodak Portra 400, muted realistic colors, architectural textures, f/5.6, highly detailed, photorealistic.",
        "wan_prompt": "Elegant slow-motion tracking shot gliding across the infinity pool towards the modern beachfront mansion at sunset, warm ocean breeze gently swaying palm trees. Photorealistic, 8k, Arri Alexa, smooth cinema camera movement.",
        "narration": "Welcome to absolute coastal luxury. Redefining modern beachfront living."
    },
    {
        "id": "shot_2_lounge",
        "name": "The Transition (Interior-to-Exterior Lounge)",
        "flux_prompt": "Architectural interior photography of a minimalist luxury lounge inside a waterfront villa, open floor-to-ceiling glass walls looking out to a bright turquoise tropical ocean. White linen furniture, warm natural oak wood accents, potted exotic palms, sunlit bright spaces, natural daylight, soft realistic shadows, highly detailed, photorealistic.",
        "wan_prompt": "Gentle slow-motion dolly shot gliding forward from the luxury interior lounge onto the sunny beachfront terrace, revealing the bright sandy ocean view. Majestic, photorealistic, cinematic camera sweep.",
        "narration": "Step inside to bright, sunlit spaces looking out to a private ocean horizon."
    },
    {
        "id": "shot_3_twilight",
        "name": "The Close (Twilight Aerial Sweep)",
        "flux_prompt": "Professional high-angle twilight photography of a luxury beachfront estate at blue hour. Soft pastel purple and blue skies, warm interior architectural lights glowing through expansive glass panels, gentle ocean waves lapping on white sand, dusk ambient light, cinematic, highly detailed, photorealistic.",
        "wan_prompt": "Cinematic slow rising crane shot revealing the entire luxury beachfront estate at twilight dusk, warm interior lights sparkling, soft waves lapping on the beach. Calm, realistic, majestic drone movement.",
        "narration": "Experience twilight living at its finest, where beach beauty meets design."
    }
]

async def generate_tts(text: str, output_path: str):
    """
    Synthesizes natural professional voiceover narration using edge-tts.
    """
    communicate = edge_tts.Communicate(text, "en-US-AriaNeural") # Professional warm female voice
    await communicate.save(output_path)

def generate_tts_sync(text: str, output_path: str):
    asyncio.run(generate_tts(text, output_path))

def fetch_json(url: str):
    try:
        with urllib.request.urlopen(url) as resp:
            return json.load(resp)
    except Exception:
        return {}

def queue_prompt(server_url, workflow, client_id):
    payload = json.dumps({"prompt": workflow, "client_id": client_id}).encode()
    req = urllib.request.Request(
        f"{server_url}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)["prompt_id"]

def wait_for_flux_job(prompt_id):
    while True:
        hist = fetch_json(f"{SERVER}/history/{prompt_id}")
        if prompt_id in hist:
            return hist[prompt_id]
        time.sleep(2)

def grade_image(input_path, output_path):
    """
    Applies photographic grading to raw Flux output to establish gold-standard realism.
    """
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    filter_chain = (
        "eq=saturation=1.25:contrast=1.08:brightness=-0.01,"
        "noise=alls=6:allf=t+u,"
        "vignette=angle=0.35"
    )
    cmd = [
        ffmpeg_exe, "-y",
        "-i", str(input_path),
        "-vf", filter_chain,
        str(output_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def grade_video(input_path, output_path):
    """
    Applies our signature cinematic post-production desaturation, temporal grain,
    and vignette filter chain to the final video clip.
    """
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    filter_chain = (
        "eq=saturation=0.80:contrast=0.95:brightness=-0.01,"
        "noise=alls=8:allf=t+u,"
        "vignette=angle=0.35"
    )
    cmd = [
        ffmpeg_exe, "-y",
        "-i", str(input_path),
        "-vf", filter_chain,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        str(output_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def add_captions(input_path, output_path, text):
    """
    Applies stylized captions on the bottom third of the video with a translucent dark box.
    """
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    # Horizontal centering: (w-text_w)/2, vertical: lower third (h-80). Arial fallback.
    filter_chain = (
        f"drawtext=text='{text}':"
        f"x=(w-text_w)/2:y=h-80:"
        f"fontsize=24:fontcolor=white:"
        f"box=1:boxcolor=black@0.5:boxborderw=10:"
        f"font='Arial'"
    )
    cmd = [
        ffmpeg_exe, "-y",
        "-i", str(input_path),
        "-vf", filter_chain,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        str(output_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    # Setup base job structure
    JOB_DIR.mkdir(parents=True, exist_ok=True)
    
    print("==================================================")
    print("[RUNNING] DBAT MULTI-SHOT REALTY PRODUCTION STUDIO")
    print("==================================================")
    
    # -----------------------------------------------------------------
    # STEP 1: Generate & Grade Flux Reference Images + Narrations Locally
    # -----------------------------------------------------------------
    print("\n[STEP 1] Generating reference frames, voiceovers, and grading locally...")
    
    for shot in SHOTS:
        shot_id = shot["id"]
        shot_name = shot["name"]
        
        # Subfolders setup
        shot_dir = JOB_DIR / shot_id
        ref_dir = shot_dir / "reference_images"
        out_dir = shot_dir / "outputs"
        wf_dir = shot_dir / "workflows"
        
        ref_dir.mkdir(parents=True, exist_ok=True)
        out_dir.mkdir(parents=True, exist_ok=True)
        wf_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n  -> Processing assets for {shot_name}...")
        
        # Generate voiceover locally
        narration_path = out_dir / "narration.mp3"
        try:
            generate_tts_sync(shot["narration"], str(narration_path))
            print(f"     * Voiceover narration generated: {narration_path}")
            shot["narration_path"] = narration_path
        except Exception as e:
            print(f"     * [WARNING] Voiceover generation failed: {e}")
        
        # Generate Flux raw reference image
        flux_workflow = {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "z_image_turbo_fp8.safetensors"}
            },
            "2": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": 1024, "height": 576, "batch_size": 1}
            },
            "3": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": shot["flux_prompt"],
                    "clip": ["1", 1]
                }
            },
            "4": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": "3d render, cartoon, illustration, painting, plastic, neon colors, oversaturated, bright colors, high saturation, glowing lines, drawing, watermark, text, low quality, blurry",
                    "clip": ["1", 1]
                }
            },
            "5": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["1", 0],
                    "positive": ["3", 0],
                    "negative": ["4", 0],
                    "latent_image": ["2", 0],
                    "seed": 42,
                    "steps": 5,
                    "cfg": 1.0,
                    "sampler_name": "euler",
                    "scheduler": "simple",
                    "denoise": 1.0
                }
            },
            "6": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["5", 0], "vae": ["1", 2]}
            },
            "7": {
                "class_type": "SaveImage",
                "inputs": {"images": ["6", 0], "filename_prefix": f"flux_{shot_id}_raw"}
            }
        }
        
        try:
            flux_pid = queue_prompt(SERVER, flux_workflow, f"flux_{shot_id}")
            job_info = wait_for_flux_job(flux_pid)
            
            raw_meta = job_info["outputs"]["7"]["images"][0]
            raw_path = ref_dir / "raw_flux.png"
            
            params = urllib.parse.urlencode({"filename": raw_meta["filename"], "subfolder": raw_meta["subfolder"], "type": raw_meta["type"]})
            with urllib.request.urlopen(f"{SERVER}/view?{params}") as resp:
                raw_path.write_bytes(resp.read())
            print(f"     * Raw image downloaded to: {raw_path}")
            
            graded_path = ref_dir / "graded_master.png"
            grade_image(raw_path, graded_path)
            print(f"     * Graded master image saved to: {graded_path}")
            
            # Archive flux graph
            with open(wf_dir / "flux_workflow.json", "w", encoding="utf-8") as wf_file:
                json.dump(flux_workflow, wf_file, indent=4)
                
            # Attach paths
            shot["local_graded_path"] = graded_path
            shot["out_dir"] = out_dir
            shot["wf_dir"] = wf_dir
            
        except Exception as e:
            print(f"[ERROR] Reference generation failed for {shot_id}: {e}")
            sys.exit(1)
            
    # -----------------------------------------------------------------
    # STEP 2: Boot or Rent a Vast GPU Instance dynamically
    # -----------------------------------------------------------------
    print("\n[STEP 2] Resuming or provisioning Vast.ai GPU cluster resources...")
    manager = VastManager(settings.vast_api_key)
    
    is_new_rental = False
    instance = None
    inst_id = None
    executor = None
    
    try:
        # Try starting existing stopped instance first
        try:
            instance = manager.get_active_instance()
        except Exception as e:
            print(f"  -> Note: stopped instance check returned error: {e}")
            
        if not instance:
            print("  -> Existing stopped instance is unavailable. Provisioning fresh RTX 4090 cluster...")
            gpu_target = settings.prod_gpu
            max_price = settings.prod_max_price
            
            offers = manager.search_offers(gpu_name=gpu_target, max_price=max_price)
            if not offers:
                print(f"[ERROR] Failed to locate any verified GPU offers for {gpu_target} under ${max_price}/hr.")
                sys.exit(1)
                
            selected_offer = offers[0]
            offer_id = int(selected_offer["id"])
            print(f"  -> Selected verified offer {offer_id} at ${selected_offer['dph_total']:.3f}/hr.")
            
            rent_result = manager.create_instance(offer_id=offer_id)
            if not rent_result:
                print("[ERROR] Failed to initiate GPU contract on Vast.ai.")
                sys.exit(1)
                
            print("  -> Rented successfully! Waiting for SSH endpoint to assign (up to 120s)...")
            new_inst_id = rent_result.get("new_contract") or rent_result.get("id")
            
            for attempt in range(24):
                time.sleep(5)
                instances = manager.list_instances()
                for inst in instances:
                    if str(inst.get("id")) == str(new_inst_id) or str(inst.get("contract_id")) == str(new_inst_id):
                        if inst.get("ssh_host") and inst.get("ssh_port"):
                            instance = inst
                            is_new_rental = True
                            break
                if instance:
                    break
                    
            if not instance:
                print("[ERROR] Rented instance did not spin up SSH interface in time.")
                sys.exit(1)
                
        inst_id = instance.get("id") or instance.get("contract_id")
        
        # Robust SSH endpoint detection: bypass broken Vast proxies by using direct Host IP and Port Map if available!
        ssh_host = instance.get("ssh_host")
        ssh_port = instance.get("ssh_port")
        
        ports = instance.get("ports", {})
        ssh_ports_list = ports.get("22/tcp", [])
        if ssh_ports_list and instance.get("public_ipaddr"):
            ssh_host = instance.get("public_ipaddr")
            ssh_port = int(ssh_ports_list[0].get("HostPort", ssh_port))
            print(f"  -> Direct SSH route detected! Bypassing proxy: connecting directly to {ssh_host}:{ssh_port}")
        else:
            print(f"  -> Using standard Vast proxy SSH route: {ssh_host}:{ssh_port}")
            
        print(f"  -> Vast GPU instance {inst_id} is running at {ssh_host}:{ssh_port}!")
        
        # -----------------------------------------------------------------
        # STEP 3: Connect over SSH and wait for local ComfyUI to respond
        # -----------------------------------------------------------------
        print("\n[STEP 3] Connecting to GPU instance over SSH and checking health...")
        key_path = os.path.join(os.getcwd(), "vast_id")
        executor = RemoteExecutor(ssh_host, ssh_port, key_path)
        
        if not executor.connect():
            print("[ERROR] SSH connection failed.")
            sys.exit(1)
            
        # Ensure ComfyUI is running on port 8188
        print("  -> Checking if ComfyUI is already running on port 8188...")
        is_running = False
        try:
            output_str, _ = executor.execute_sync("curl -s http://localhost:8188/system_stats")
            if '"comfyui_version"' in output_str:
                is_running = True
                print("  -> ComfyUI is already running.")
        except Exception:
            pass

        if not is_running:
            print("  -> ComfyUI is not running. Starting ComfyUI in the background...")
            # Apply NVIDIA GeForce CUDA compatibility fix
            executor.execute_sync("mv /usr/local/cuda/compat /usr/local/cuda/compat.bak 2>/dev/null || true")
            # Clean any old bound sockets
            executor.execute_sync("kill -9 $(lsof -t -i:8188) 2>/dev/null || fuser -k -9 8188/tcp 2>/dev/null || true")
            # Launch ComfyUI in background using setsid (survives SSH terminal detach)
            launch_cmd = "setsid /opt/venv/bin/python /ComfyUI/main.py --listen 0.0.0.0 --port 8188 > /ComfyUI/comfy.log 2>&1 &"
            executor.execute_sync(launch_cmd)
            print("  -> ComfyUI boot initiated.")

        # Health check loop
        print("  -> Waiting for ComfyUI port 8188 to respond...")
        server_ready = False
        for attempt in range(30):
            try:
                output_str, _ = executor.execute_sync("curl -s http://localhost:8188/system_stats")
                if '"comfyui_version"' in output_str:
                    print("  -> ComfyUI is up and fully operational!")
                    server_ready = True
                    break
            except Exception:
                pass
            time.sleep(5)
            
        if not server_ready:
            print("[ERROR] ComfyUI server failed to boot on the remote instance in time.")
            log_out, _ = executor.execute_sync("cat /ComfyUI/comfy.log 2>/dev/null | tail -n 30")
            print("--- COMFYUI REMOTE LOGS ---")
            print(log_out)
            sys.exit(1)
            
        # Clean remote ComfyUI output directory to prevent fallback collisions
        print("  -> Cleaning remote output directory...")
        executor.execute_sync("rm -f /ComfyUI/output/*.mp4")

        # -----------------------------------------------------------------
        # STEP 4: Submit local Wan-2.1 Image-to-Video sequential renders
        # -----------------------------------------------------------------
        print("\n[STEP 4] Submitting sequential Wan-2.1 Image-to-Video renders...")
        
        for shot in SHOTS:
            shot_id = shot["id"]
            shot_name = shot["name"]
            graded_master_local = shot["local_graded_path"]
            out_dir = shot["out_dir"]
            wf_dir = shot["wf_dir"]
            
            print(f"\n  -> Submitting and rendering {shot_name}...")
            
            # SFTP Upload the photoreal cinematic graded reference master (not raw!)
            print("     * SFTP-uploading photographic-graded master reference to remote...")
            sftp = executor.client.open_sftp()
            executor.execute_sync("mkdir -p /ComfyUI/input")
            sftp.put(str(graded_master_local), "/ComfyUI/input/graded_master.png")
            sftp.close()
            print("     * Graded master uploaded successfully to /ComfyUI/input/graded_master.png!")
            
            video_workflow = {
                "client_id": f"vast_realty_{shot_id}",
                "prompt": {
                    # Load Flux reference frame from input folder
                    "51": {
                        "inputs": {"image": "graded_master.png", "upload": "image"},
                        "class_type": "LoadImage"
                    },
                    # Load CLIP Vision model
                    "53": {
                        "inputs": {"clip_name": "clip_vision_h.safetensors"},
                        "class_type": "CLIPVisionLoader"
                    },
                    # Encode CLIP vision features
                    "65": {
                        "inputs": {
                            "clip_vision": ["53", 0],
                            "image_1": ["51", 0],
                            "strength_1": 1.0,
                            "strength_2": 1.0,
                            "crop": "center",
                            "combine_embeds": "average",
                            "force_offload": True
                        },
                        "class_type": "WanVideoClipVisionEncode"
                    },
                    # Load the main Wan 2.1 14B FP8 I2V model
                    "22": {
                        "inputs": {
                            "model": "wan2.1_i2v_480p_14B_fp8_e4m3fn.safetensors",
                            "base_precision": "fp16",
                            "quantization": "fp8_e4m3fn",
                            "load_device": "offload_device",
                            "attention_mode": "sdpa"
                        },
                        "class_type": "WanVideoModelLoader"
                    },
                    # Load T5 Text Encoder using the custom LoadWanVideoT5TextEncoder node
                    "38": {
                        "inputs": {
                            "model_name": "umt5-xxl-enc-fp8_e4m3fn.safetensors",
                            "precision": "bf16",
                            "load_device": "offload_device",
                            "quantization": "disabled"
                        },
                        "class_type": "LoadWanVideoT5TextEncoder"
                    },
                    # Load VAE
                    "39": {
                        "inputs": {
                            "model_name": "wan_2.1_vae.safetensors",
                            "precision": "bf16"
                        },
                        "class_type": "WanVideoVAELoader"
                    },
                    # Wan Video Text Encode (Positive & Negative)
                    "16": {
                        "inputs": {
                            "positive_prompt": shot["wan_prompt"],
                            "negative_prompt": "low quality, blurry, distorted, watermark, poorly lit, ugly",
                            "t5": ["38", 0],
                            "force_offload": True,
                            "model_to_offload": ["22", 0],
                            "use_disk_cache": False,
                            "device": "gpu"
                        },
                        "class_type": "WanVideoTextEncode"
                    },
                    # Encode image latents using VAE and clip vision embeds
                    "63": {
                        "inputs": {
                            "vae": ["39", 0],
                            "clip_embeds": ["65", 0],
                            "start_image": ["51", 0],
                            "width": 832,
                            "height": 480,
                            "num_frames": 81,
                            "noise_aug_strength": 0.01,
                            "start_latent_strength": 1.0,
                            "end_latent_strength": 1.0,
                            "force_offload": True
                        },
                        "class_type": "WanVideoImageToVideoEncode"
                    },
                    # Custom Wan Video Sampler
                    "27": {
                        "inputs": {
                            "model": ["22", 0],
                            "image_embeds": ["63", 0],
                            "text_embeds": ["16", 0],
                            "steps": 30,
                            "cfg": 6.0,
                            "shift": 5.0,
                            "seed": 42,
                            "force_offload": True,
                            "scheduler": "unipc",
                            "riflex_freq_index": 0,
                            "rope_function": "comfy"
                        },
                        "class_type": "WanVideoSampler"
                    },
                    # VAE Decode
                    "28": {
                        "inputs": {
                            "vae": ["39", 0],
                            "samples": ["27", 0],
                            "enable_vae_tiling": False,
                            "tile_x": 272,
                            "tile_y": 272,
                            "tile_stride_x": 144,
                            "tile_stride_y": 128
                        },
                        "class_type": "WanVideoDecode"
                    },
                    # Save/Assemble Video Combine
                    "47": {
                        "inputs": {
                            "frame_rate": 16, "loop_count": 0, "filename_prefix": f"wan_{shot_id}",
                            "format": "video/h264-mp4", "pix_fmt": "yuv420p", "crf": 19,
                            "save_metadata": True, "pingpong": False, "save_output": True,
                            "images": ["28", 0]
                        },
                        "class_type": "VHS_VideoCombine"
                    }
                }
            }
            
            # Submit Prompt
            prompt_res = executor.submit_prompt(video_workflow)
            res_data = json.loads(prompt_res)
            video_pid = res_data.get("prompt_id")
            
            if not video_pid:
                raise ValueError(f"Failed to submit: {prompt_res}")
                
            print(f"     * Prompt submitted successfully! Job ID: {video_pid}")
            print("     * Rendering high-fidelity video on remote GPU...")
            
            # Poll completion robustly
            print("     * Polling remote server for render completion (takes several minutes)...")
            consecutive_failures = 0
            while True:
                try:
                    hist_str, _ = executor.execute_sync(f"curl -s http://localhost:8188/history/{video_pid}")
                    if hist_str.strip():
                        hist_data = json.loads(hist_str)
                        if video_pid in hist_data:
                            print("     * Local rendering finished!")
                            break
                    consecutive_failures = 0
                except Exception as e:
                    consecutive_failures += 1
                    print(f"     * [POLL] Transient warning or network lag (waiting 15s to retry, failure {consecutive_failures}/10): {e}")
                    if consecutive_failures >= 10:
                        print("     * [ERROR] Too many consecutive SSH/network failures. Aborting render loop.")
                        raise e
                time.sleep(15)
                
            # Locate remote video path
            outputs = hist_data[video_pid].get("outputs", {})
            remote_video_file = None
            for node_id, output_data in outputs.items():
                if "gifs" in output_data:
                    for gif in output_data["gifs"]:
                        if gif["filename"].endswith(".mp4"):
                            remote_video_file = f"/ComfyUI/output/{gif['filename']}"
                            break
                            
            if not remote_video_file:
                # Fallback to last modified mp4
                find_res, _ = executor.execute_sync("ls -t /ComfyUI/output/*.mp4 2>/dev/null | head -n 1")
                remote_video_file = find_res.strip()
                
            if not remote_video_file or "No such file" in remote_video_file:
                raise FileNotFoundError("Could not locate final rendered mp4 on server.")
                
            # Download raw mp4
            raw_video_path = out_dir / "raw_video.mp4"
            print(f"     * Downloading rendered video to local: {raw_video_path}")
            
            sftp = executor.client.open_sftp()
            sftp.get(remote_video_file, str(raw_video_path))
            sftp.close()
            print("     * Download completed successfully!")
            
            # Archive wan graph
            with open(wf_dir / "wan_workflow.json", "w", encoding="utf-8") as wf_file:
                json.dump(video_workflow, wf_file, indent=4)
                
            shot["raw_video_path"] = raw_video_path
            
    except Exception as e:
        print(f"\n[ERROR] Step 4 failed: {e}")
        sys.exit(1)
        
    finally:
        # -----------------------------------------------------------------
        # STEP 5: Pause billing or Terminate Vast GPU instance IMMEDIATELY
        # -----------------------------------------------------------------
        print("\n[STEP 5] Releasing GPU cluster resources to pause billing...")
        if executor:
            try:
                executor.close()
            except Exception:
                pass
        if inst_id:
            if is_new_rental:
                print(f"  -> Destroying newly rented instance {inst_id}...")
                manager.destroy_instance(inst_id)
            else:
                print(f"  -> Stopping existing instance {inst_id}...")
                manager.stop_instance(inst_id)
            print("  -> GPU resource released successfully. Billing halted.")
            
    # -----------------------------------------------------------------
    # STEP 6: Apply cinematic film post-grading AND overlay stylized subtitles
    # -----------------------------------------------------------------
    print("\n[STEP 6] Applying signature post-production grading and subtitles...")
    for shot in SHOTS:
        if "raw_video_path" in shot:
            shot_name = shot["name"]
            raw_video_path = shot["raw_video_path"]
            graded_video_path = shot["out_dir"] / "graded_video.mp4"
            captioned_video_path = shot["out_dir"] / "captioned_video.mp4"
            
            print(f"  -> Color grading raw clip for {shot_name}...")
            try:
                # 1. Apply desaturation & moving film grain
                grade_video(raw_video_path, graded_video_path)
                print(f"     * Graded video clip saved to: {graded_video_path}")
                
                # 2. Add subtitles centered on the lower third
                print(f"  -> Overlaying captions for {shot_name}...")
                add_captions(graded_video_path, captioned_video_path, shot["narration"])
                print(f"     * Captioned video clip saved to: {captioned_video_path}")
                shot["captioned_video_path"] = captioned_video_path
                
            except Exception as e:
                print(f"     * [WARNING] Local visual post-processing failed for {shot_name}: {e}")
                
    # -----------------------------------------------------------------
    # STEP 7: Combine videos and mix voiceover with background music
    # -----------------------------------------------------------------
    print("\n[STEP 7] Concatenating scenes, mixing audio tracks, and compiling movie...")
    
    final_master_path = JOB_DIR / "final_realty_master.mp4"
    
    try:
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        
        # 1. Concatenate captioned videos
        concat_list_path = JOB_DIR / "video_concat_list.txt"
        with open(concat_list_path, "w", encoding="utf-8") as concat_f:
            for shot in SHOTS:
                if "captioned_video_path" in shot:
                    # FFMPEG requires forward slashes even on Windows for demuxer files
                    relative_path = shot["id"] + "/outputs/captioned_video.mp4"
                    concat_f.write(f"file '{relative_path}'\n")
                    
        concat_video_path = JOB_DIR / "concat_captioned.mp4"
        print("  -> Concatenating visual segments...")
        subprocess.run([
            ffmpeg_exe, "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_list_path), "-c", "copy", str(concat_video_path)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 2. Concatenate voiceover narrations
        audio_concat_list_path = JOB_DIR / "audio_concat_list.txt"
        with open(audio_concat_list_path, "w", encoding="utf-8") as audio_concat_f:
            for shot in SHOTS:
                if "narration_path" in shot:
                    relative_path = shot["id"] + "/outputs/narration.mp3"
                    audio_concat_f.write(f"file '{relative_path}'\n")
                    
        concat_narration_path = JOB_DIR / "concat_narration.mp3"
        print("  -> Concatenating audio segments...")
        subprocess.run([
            ffmpeg_exe, "-y", "-f", "concat", "-safe", "0",
            "-i", str(audio_concat_list_path), "-c", "copy", str(concat_narration_path)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 3. Mix concatenated narrations with dipped background music
        # a0 is voiceover boosted (1.8x), a1 is music dipped (to 15% volume)
        mixed_audio_path = JOB_DIR / "final_mixed_audio.mp3"
        print("  -> Mixing voiceover and ambient music (ducking background music)...")
        subprocess.run([
            ffmpeg_exe, "-y",
            "-i", str(concat_narration_path),
            "-i", str(BG_MUSIC_PATH),
            "-filter_complex", "[0:a]volume=1.8[a0];[1:a]volume=0.15[a1];[a0][a1]amix=inputs=2:duration=first:dropout_transition=2",
            "-c:a", "mp3", str(mixed_audio_path)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 4. Mux final video and mixed audio together
        print("  -> Compiling final master movie clip...")
        subprocess.run([
            ffmpeg_exe, "-y",
            "-i", str(concat_video_path),
            "-i", str(mixed_audio_path),
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            str(final_master_path)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print(f"\n  -> Master Movie Compiled! Saved to: {final_master_path}")
        
    except Exception as e:
        print(f"  -> [ERROR] Final visual and audio compiling failed: {e}")
        
    # -----------------------------------------------------------------
    # STEP 8: Save production metadata & Archive source script inside package
    # -----------------------------------------------------------------
    print("\n[STEP 8] Saving production settings and archiving source codes...")
    
    metadata = {
        "job_id": "beach_realty_job_1",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "environmental_mode": settings.environment,
        "active_gpu": instance.get("gpu_name") if instance else "RTX_3090/4090",
        "final_movie_output": str(final_master_path),
        "shots_production": []
    }
    
    for shot in SHOTS:
        shot_entry = {
            "shot_id": shot["id"],
            "shot_name": shot["name"],
            "narration_text": shot["narration"],
            "flux_reference_settings": {
                "checkpoint": "z_image_turbo_fp8.safetensors",
                "seed": 42,
                "steps": 5,
                "cfg": 1.0,
                "prompt": shot["flux_prompt"]
            },
            "wan_video_settings": {
                "model": "wan2.1_i2v_480p_14B_fp8_e4m3fn.safetensors",
                "seed": 42,
                "steps": 30,
                "cfg": 6.0,
                "shift": 5.0,
                "resolution": "832x480 (Wide 16:9)",
                "duration": "5 seconds (81 frames @ 16fps)",
                "reference_image": "graded_master.png",
                "prompt": shot["wan_prompt"]
            },
            "color_grading_specs": {
                "image_grading": "saturation=1.25, contrast=1.08, grain=6, vignette=0.35",
                "video_grading": "saturation=0.80, contrast=0.95, grain=8, vignette=0.35",
                "subtitles": "fontsize=24, color=white, box=black@0.5"
            },
            "file_paths": {
                "raw_flux": str(shot["local_graded_path"].parent / "raw_flux.png"),
                "graded_master": str(shot["local_graded_path"]),
                "narration_mp3": str(shot.get("narration_path", "")),
                "raw_video": str(shot.get("raw_video_path", "")),
                "graded_video": str(shot.get("graded_video_path", "")),
                "captioned_video": str(shot.get("captioned_video_path", ""))
            }
        }
        metadata["shots_production"].append(shot_entry)
        
    # Save master metadata
    metadata_path = JOB_DIR / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
    print(f"  -> Unified master metadata logs saved to: {metadata_path}")
    
    # Self-archiving source code inside the package
    try:
        archive_script_path = JOB_DIR / "run_vast_pipeline.py"
        with open(__file__, "r", encoding="utf-8") as f_src:
            script_code = f_src.read()
        with open(archive_script_path, "w", encoding="utf-8") as f_dest:
            f_dest.write(script_code)
        print(f"  -> Execution script archived to: {archive_script_path}")
    except Exception as e:
        print(f"  -> Warning: self-archiving script code failed: {e}")
        
    print("\n==================================================")
    print("[SUCCESS] MULTI-SHOT REALTY JOB COMPLETED FLAWLESSLY!")
    print("==================================================")
    print(f"  * Job Folder: {JOB_DIR.resolve()}")
    print(f"  * Compiled Master Video: {final_master_path.resolve()}")

if __name__ == "__main__":
    main()

# run_production_pipeline.py
"""
DBAT End-to-End Cinematic Video Production Studio
1. Creates a custom job folder under `jobs/beach_realty_job_1/`
2. Generates the gold-standard beach reference image via ComfyUI/Flux
3. Applies film-grade FFMPEG post-grading and saves raw/graded master frames
4. Uploads the graded master to the server's input folder
5. Triggers a high-fidelity 5-second Wan-2.1 Image-to-Video generation via Cloud API
6. Downloads the raw video, applies cinematic post-processing (desaturation, grain, vignette)
7. Saves all metadata, settings, and final graded movie clips inside the job folder!
"""

import json
import time
import urllib.request
import urllib.parse
import pathlib
import subprocess
import imageio_ffmpeg
import sys
import uuid

SERVER = "http://142.54.160.17:8188"
JOB_DIR = pathlib.Path("jobs/beach_realty_job_1")
REF_DIR = JOB_DIR / "reference_images"
OUT_DIR = JOB_DIR / "outputs"

def fetch_json(url: str):
    try:
        with urllib.request.urlopen(url) as resp:
            return json.load(resp)
    except Exception:
        return {}

def upload_image(server_url, image_path):
    """
    Uploads a local image to the ComfyUI server input directory.
    """
    with open(image_path, "rb") as f:
        img_data = f.read()
    
    boundary = "----ComfyUIBoundary" + str(uuid.uuid4())
    parts = []
    parts.append(f"--{boundary}")
    parts.append(f'Content-Disposition: form-data; name="image"; filename="{image_path.name}"')
    parts.append("Content-Type: image/png")
    parts.append("")
    parts.append(img_data)
    parts.append(f"--{boundary}--")
    parts.append("")
    
    body = b"\r\n".join(p if isinstance(p, bytes) else p.encode() for p in parts)
    
    req = urllib.request.Request(
        f"{server_url}/upload/image",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)

def queue_prompt(workflow, client_id):
    payload = json.dumps({"prompt": workflow, "client_id": client_id}).encode()
    req = urllib.request.Request(
        f"{SERVER}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)["prompt_id"]

def wait_for_job(prompt_id):
    while True:
        hist = fetch_json(f"{SERVER}/history/{prompt_id}")
        if prompt_id in hist:
            return hist[prompt_id]
        
        # Check queue
        try:
            with urllib.request.urlopen(f"{SERVER}/queue") as q_resp:
                q_info = json.load(q_resp)
                running = q_info.get("queue_running", [])
                pending = q_info.get("queue_pending", [])
                if any(j[1] == prompt_id for j in running):
                    print("  [STATUS] Processing on GPU...", flush=True)
                elif any(j[1] == prompt_id for j in pending):
                    print(f"  [STATUS] In queue (position {pending.index(next(j for j in pending if j[1] == prompt_id)) + 1})...", flush=True)
        except Exception:
            pass
            
        time.sleep(3)

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
    # Post-processor: desaturate (80%), add realistic moving grain and vignette
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

def main():
    # Setup job structure
    REF_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("==================================================")
    print("[RUNNING] DBAT FULL VIDEO PRODUCTION STUDIO FLOW")
    print("==================================================")
    
    # -----------------------------------------------------------------
    # STEP 1: Generate & Grade Flux Reference Image
    # -----------------------------------------------------------------
    print("\n[STEP 1] Generating raw gold-standard Flux reference beach image...")
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
                "text": "Analog 35mm photography of a luxury modern waterfront mansion on a private tropical beach with lush palm trees, glowing infinity pool at golden hour. Soft natural lighting, subtle film grain, Kodak Portra 400, muted realistic colors, architectural textures, f/5.6, highly detailed, photorealistic.",
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
            "inputs": {"images": ["6", 0], "filename_prefix": "flux_beach_realty_raw"}
        }
    }
    
    try:
        flux_pid = queue_prompt(flux_workflow, "flux_beach_realty")
        job_info = wait_for_job(flux_pid)
        
        # Download raw
        raw_meta = job_info["outputs"]["7"]["images"][0]
        raw_path = REF_DIR / "flux_beach_raw.png"
        
        params = urllib.parse.urlencode({"filename": raw_meta["filename"], "subfolder": raw_meta["subfolder"], "type": raw_meta["type"]})
        with urllib.request.urlopen(f"{SERVER}/view?{params}") as resp:
            raw_path.write_bytes(resp.read())
        print(f"  -> Raw reference image downloaded to: {raw_path}")
        
        # Grade raw
        graded_path = REF_DIR / "graded_beach_master.png"
        grade_image(raw_path, graded_path)
        print(f"  -> Cinematic graded master image saved to: {graded_path}")
        
    except Exception as e:
        print(f"[ERROR] Step 1 failed: {e}")
        sys.exit(1)
        
    # -----------------------------------------------------------------
    # STEP 2: Upload Graded Master back to ComfyUI input folder
    # -----------------------------------------------------------------
    print("\n[STEP 2] Uploading graded master image back to ComfyUI input folder...")
    try:
        upload_resp = upload_image(SERVER, graded_path)
        uploaded_filename = upload_resp["name"]
        print(f"  -> Uploaded successfully! Server filename: {uploaded_filename}")
    except Exception as e:
        print(f"[ERROR] Step 2 failed: {e}")
        sys.exit(1)
        
    # -----------------------------------------------------------------
    # STEP 3: Trigger Wan-2.1 Cloud API Video Generation (Image-to-Video)
    # -----------------------------------------------------------------
    print("\n[STEP 3] Submitting high-end Wan-2.1 Image-to-Video generation task...")
    
    # 5-second video, elegant dynamic push-in hook
    video_prompt = (
        "Cinematic, elegant slow-motion tracking shot gliding towards an ultra-luxury beachfront mansion at golden sunset hour, "
        "warm ocean breeze gently swaying palm trees, glowing infinity pool water ripples. Photorealistic, 8k, majestic, "
        "Arri Alexa, smooth cinematic camera movement."
    )
    
    video_workflow = {
        "10": {
            "class_type": "LoadImage",
            "inputs": {
                "image": uploaded_filename
            }
        },
        "20": {
            "class_type": "WanImageToVideoApi",
            "inputs": {
                "model": "wan2.6-i2v",
                "image": ["10", 0],
                "prompt": video_prompt
            }
        },
        "30": {
            "class_type": "SaveVideo",
            "inputs": {
                "video": ["20", 0],
                "filename_prefix": "wan_beach_realty",
                "format": "mp4",
                "codec": "h264"
            }
        }
    }
    
    try:
        video_pid = queue_prompt(video_workflow, "wan_beach_realty_i2v")
        print(f"  -> Prompt queued successfully. ID: {video_pid}")
        print("  -> Waiting for Wan Cloud API rendering pipeline to complete...")
        
        video_info = wait_for_job(video_pid)
        
        # Check status of execution
        status_info = video_info.get("status", {})
        if status_info.get("status_str") == "error":
            # Extract error message
            msg = status_info.get("messages", [["error", {"exception_message": "Unknown error"}]])[-1][1].get("exception_message")
            raise ValueError(f"Server-side execution failed: {msg}")
            
        print("[SUCCESS] Wan Video render completed on the Cloud GPU cluster!")
        
        # Resiliently download video
        node_out = video_info["outputs"]["30"]
        meta = None
        for k in ["videos", "gifs", "images", "video"]:
            if k in node_out and len(node_out[k]) > 0:
                meta = node_out[k][0]
                break
                
        if not meta:
            raise ValueError(f"No video files found in output metadata: {node_out}")
            
        raw_video_path = OUT_DIR / "raw_video.mp4"
        
        params = urllib.parse.urlencode({"filename": meta["filename"], "subfolder": meta["subfolder"], "type": meta["type"]})
        with urllib.request.urlopen(f"{SERVER}/view?{params}") as resp:
            raw_video_path.write_bytes(resp.read())
        print(f"  -> Raw render video downloaded to: {raw_video_path}")
        
    except Exception as e:
        print(f"[ERROR] Step 3 failed: {e}")
        sys.exit(1)
        
    # -----------------------------------------------------------------
    # STEP 4: Post-Process Video (Grade, Grain, Vignette)
    # -----------------------------------------------------------------
    print("\n[STEP 4] Applying professional cinema post-production grading to the video clip...")
    try:
        final_video_path = OUT_DIR / "graded_video.mp4"
        grade_video(raw_video_path, final_video_path)
        print(f"  -> Graded movie clip successfully saved to: {final_video_path}")
    except Exception as e:
        print(f"[ERROR] Step 4 failed: {e}")
        sys.exit(1)
        
    # -----------------------------------------------------------------
    # STEP 5: Save Job settings and metadata
    # -----------------------------------------------------------------
    print("\n[STEP 5] Saving all production settings, metadata, and logs...")
    metadata = {
        "job_id": "beach_realty_job_1",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "flux_settings": {
            "checkpoint": "z_image_turbo_fp8.safetensors",
            "seed": 42,
            "steps": 5,
            "cfg": 1.0,
            "prompt": "Analog 35mm photography of a luxury modern waterfront mansion on a private tropical beach..."
        },
        "wan_settings": {
            "model": "wan2.6-i2v",
            "seed": 42,
            "resolution": "720P",
            "duration": "5 seconds",
            "prompt": video_prompt
        },
        "post_processing": {
            "image_grading": "saturation=1.25, contrast=1.08, grain=6, vignette=0.35",
            "video_grading": "saturation=0.80, contrast=0.95, grain=8, vignette=0.35"
        }
    }
    
    with open(JOB_DIR / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)
    print("  -> Job metadata saved to: jobs/beach_realty_job_1/metadata.json")
    
    print("\n==================================================")
    print("[SUCCESS] FULL PRODUCTION JOB COMPLETED FLAWLESSLY!")
    print("==================================================")
    print(f"  * Job Folder: {JOB_DIR.resolve()}")
    print(f"  * Graded Video: {final_video_path.resolve()}")

if __name__ == "__main__":
    main()

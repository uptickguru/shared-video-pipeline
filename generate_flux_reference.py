# generate_flux_reference.py
"""
Create a single reference image of a luxury yacht interior on the remote ComfyUI server
(142.54.160.17:8188) using the pre-baked 'z_image_turbo_fp8.safetensors' checkpoint.
Applies professional cinematic color-grading and saves the master reference inside `reference_images/`.
"""

import json
import time
import urllib.request
import urllib.parse
import pathlib
import subprocess
import imageio_ffmpeg
import sys
from PIL import Image

SERVER = "http://142.54.160.17:8188"
SEED = 42

def fetch_json(url: str):
    try:
        with urllib.request.urlopen(url) as resp:
            return json.load(resp)
    except Exception:
        return {}

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
        time.sleep(2)

def download_image(filename, subfolder, img_type, local_path):
    params = urllib.parse.urlencode({
        "filename": filename,
        "subfolder": subfolder,
        "type": img_type
    })
    view_url = f"{SERVER}/view?{params}"
    with urllib.request.urlopen(view_url) as view_resp:
        local_path.write_bytes(view_resp.read())

def grade_image(input_path, output_path):
    """
    Applies high-end cinematic color correction, contrast calibration,
    organic film grain, and lens vignettes to the yacht interior image.
    """
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    # Cinematic color grade:
    # 1. eq = slight saturation and contrast boost
    # 2. noise = temporal film grain
    # 3. vignette = focused anamorphic lens shader
    filter_chain = (
        "eq=saturation=1.20:contrast=1.05:brightness=-0.01,"
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

def main():
    out_dir = pathlib.Path("reference_images")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print("==================================================")
    print("[STARTING] GENERATING CINEMATIC YACHT SCENE")
    print("==================================================")
    
    # Yacht interior workflow
    workflow = {
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
                "text": "Medium close-up shot of a luxury modern yacht interior, a crystal decanter on a teak wood table, 50mm lens at f/2.0. Shot on Arri Alexa with Kodak Portra 400. Soft diffused morning ocean light streaming through large glass windows, subtle temporal film grain, highly detailed, photorealistic.",
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
                "seed": SEED,
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
            "inputs": {"images": ["6", 0], "filename_prefix": "flux_yacht_reference"}
        }
    }
    
    try:
        # 1. Submit
        prompt_id = queue_prompt(workflow, "cinematic_yacht_interior")
        print(f"[INFO] Prompt queued. ID: {prompt_id}")
        
        # 2. Wait
        job_info = wait_for_job(prompt_id)
        print("[SUCCESS] Yacht interior rendered successfully on GPU.")
        
        # 3. Download
        raw_meta = job_info["outputs"]["7"]["images"][0]
        raw_path = out_dir / "flux_reference_image.png"
        download_image(raw_meta["filename"], raw_meta["subfolder"], raw_meta["type"], raw_path)
        print("[SUCCESS] Raw yacht reference image downloaded.")
        
        # 4. Color Grade
        graded_path = out_dir / "graded_reference_image.png"
        grade_image(raw_path, graded_path)
        print(f"[SUCCESS] Cinematic color grading completed.")
        print(f"[PATH] Saved graded master to: {graded_path.resolve()}")
        
    except Exception as e:
        print(f"[ERROR] Yacht generation failed: {e}")
        sys.exit(1)
        
    print("==================================================")
    print("[FINISHED] LUXURY YACHT MASTER IMAGE COMPLETED!")
    print("==================================================")

if __name__ == "__main__":
    main()

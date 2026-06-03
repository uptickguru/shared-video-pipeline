import requests
import json
import time
import os

COMFY_URL = "http://localhost:8188"

SCENES = [
    {"id": 1, "prompt": "A futuristic digital city with flowing neon gold rivers representing crypto liquidity."},
    {"id": 2, "prompt": "Close up of digital coins dropping into a glowing blue pool, creating ripples of code."},
    {"id": 3, "prompt": "A 3D bar chart rising out of a digital ocean, glowing with green energy."},
    {"id": 4, "prompt": "An abstract 3D representation of a decentralized exchange, gears made of light turning."},
    {"id": 5, "prompt": "A network of interconnected glowing nodes representing global traders providing liquidity."},
    {"id": 6, "prompt": "Final logo reveal: 'The Future of Liquidity' appears in shimmering silver over a calm digital sea."}
]

def submit_job(prompt_text):
    # Basic Wan-2.1 Workflow for ComfyUI
    # This is a simplified version - in a real scenario we'd load the full JSON workflow
    workflow = {
        "3": {
            "class_type": "WanVideoSampler",
            "inputs": {
                "model": "wan2.1_t2v_1.3B_bf16.safetensors",
                "prompt": prompt_text,
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
    
    try:
        response = requests.post(f"{COMFY_URL}/prompt", json={"prompt": workflow})
        return response.json().get("prompt_id")
    except Exception as e:
        print(f"Error submitting to ComfyUI: {e}")
        return None

def main():
    print("Starting Master Render for 'Liquidity Pools'...")
    
    for scene in SCENES:
        print(f"Submitting Scene {scene['id']}: {scene['prompt'][:50]}...")
        prompt_id = submit_job(scene['prompt'])
        if prompt_id:
            print(f"  [SUCCESS] Prompt ID: {prompt_id}")
        else:
            print("  [FAILED] Is the SSH tunnel open and ComfyUI running?")
        time.sleep(2) # Brief pause between submissions

    print("\nAll scenes submitted to the GPU machine!")
    print("The machine is now rendering. I will notify you when the first clip is ready for download.")

if __name__ == "__main__":
    main()

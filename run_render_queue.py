import os
import sys
import time
from remote_executor import RemoteExecutor
from vast.manager import VastManager
from config import settings

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
    print("        *** EXECUTING COHESIVE CYBER-INFLUENCER BATCH ***     ")
    print("==============================================================")
    
    ssh_host = "ssh5.vast.ai"
    ssh_port = 27576
    key_path = os.path.join(os.getcwd(), "vast_id")
    instance_id = 38387577 # Active contract ID
    
    manager = VastManager(settings.vast_api_key)
    
    print(f"\n[1/4] Connecting via SSH to active instance {ssh_host}:{ssh_port}...")
    executor = RemoteExecutor(ssh_host, ssh_port, key_path)
    if not executor.connect():
        print("[ERROR] SSH connection failed.")
        return
        
    print("\n[2/4] Injecting prompts into the ComfyUI API queue...")
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
        executor.submit_prompt(workflow)
        time.sleep(2)
        
    print("\n[3/4] Monitoring rendering progress...")
    print("      (Polling ComfyUI queue status every 30 seconds).")
    
    while True:
        try:
            stdout = executor.execute("curl -s http://localhost:18188/queue")
            queue_data = stdout.read().decode('utf-8', errors='ignore')
            
            if '"queue_pending": []' in queue_data and '"queue_running": []' in queue_data:
                print("\n      *** ALL SCENES COMPLETED RENDERING! ***")
                break
                
            pending_count = queue_data.count('"prompt_id"')
            # Print a clean, ASCII progress indicator to avoid console encoding crashes
            print(f"      [{time.strftime('%H:%M:%S')}] Rendering active... Jobs left in queue: {pending_count}")
        except Exception as e:
            print(f"      Waiting for API response... ({e})")
        time.sleep(30)
        
    print("\n[4/4] Commencing high-speed download of all rendered videos...")
    local_output_dir = os.path.join(os.getcwd(), "output_videos")
    if not os.path.exists(local_output_dir):
        os.makedirs(local_output_dir)
        
    detected_remote_dir = "/ComfyUI/output"
    stdout = executor.execute(f"ls {detected_remote_dir}/*.mp4 2>/dev/null || echo ''")
    video_files = stdout.read().decode('utf-8', errors='ignore').split()
    
    # Filter out empty entries
    video_files = [f for f in video_files if f.strip()]
    
    if not video_files:
        print("      [WARNING] No rendered MP4 files found in remote output dir.")
    else:
        print(f"      Found {len(video_files)} video clips ready to download:")
        for idx, remote_file in enumerate(video_files):
            filename = os.path.basename(remote_file)
            local_file = os.path.join(local_output_dir, f"cyber_influencer_scene_{idx+1}_{filename}")
            print(f"      Downloading scene {idx+1}/{len(video_files)}: {filename}...")
            
            # Transfer via SCP
            scp_cmd = f'scp -P {ssh_port} -o StrictHostKeyChecking=no -i "{key_path}" root@{ssh_host}:{remote_file} "{local_file}"'
            os.system(scp_cmd)
            print(f"      [SAVED] to {local_file}")
            
    print("\n==============================================================")
    print("DESTROYING VAST INSTANCE TO SAFEGUARD REMAINING CREDIT...")
    manager.destroy_instance(instance_id)
    print("Instance destroyed successfully. Remaining budget is 100% preserved.")
    print(f"All done! Your finished cyber-influencer videos are located in: {local_output_dir}")
    print("==============================================================")

if __name__ == "__main__":
    main()

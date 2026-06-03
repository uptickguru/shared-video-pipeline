import os
import sys
import json
import time
import argparse
import asyncio
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.append(os.getcwd())

import edge_tts
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips
from config import settings
from remote_executor import RemoteExecutor

from content import ALL_PROJECTS
import asyncio

async def generate_audio(text, filename):
    communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
    await communicate.save(filename)

def build_advanced_wan_payload(prompt, lora_name="influencer_lora.safetensors"):
    import random
    seed = random.randint(1, 1000000000)
    return {
        "client_id": "master_pipeline_bot",
        "prompt": {
            "37": {
                "inputs": {"unet_name": "Wan2_1-T2V-1_3B_bf16.safetensors", "weight_dtype": "default"},
                "class_type": "UNETLoader"
            },
            "48": {
                "inputs": {"shift": 8.0, "model": ["37", 0]},
                "class_type": "ModelSamplingSD3"
            },
            "38": {
                "inputs": {"clip_name": "umt5-xxl-enc-fp8_e4m3fn.safetensors", "type": "wan", "device": "default"},
                "class_type": "CLIPLoader"
            },
            "6": {
                "inputs": {"text": prompt, "clip": ["38", 0]},
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
                "inputs": {"vae_name": "Wan2_1_VAE_bf16.safetensors"},
                "class_type": "VAELoader"
            },
            "8": {
                "inputs": {"samples": ["3", 0], "vae": ["39", 0]},
                "class_type": "VAEDecode"
            },
            "47": {
                "inputs": {
                    "frame_rate": 16, "loop_count": 0, "filename_prefix": "Influencer_Pipeline_Wan",
                    "format": "video/h264-mp4", "pix_fmt": "yuv420p", "crf": 19,
                    "save_metadata": True, "pingpong": False, "save_output": True,
                    "images": ["8", 0]
                },
                "class_type": "VHS_VideoCombine"
            }
        }
    }

class JobDispatcher:
    def __init__(self, num_instances, max_price, use_ultra=False):
        self.num_instances = num_instances
        self.max_price = max_price
        self.use_ultra = use_ultra
        self.instances = []
        self.executors = []
        
    def provision_instances(self):
        print(f"Searching for {self.num_instances} instances...")
        
        # 1. Gather running and stopped instances
        res = subprocess.run(["vastai", "show", "instances", "--raw", "--api-key", settings.vast_api_key], capture_output=True, text=True)
        try:
            instances = json.loads(res.stdout)
        except:
            instances = []
            
        running_insts = [i for i in instances if "comfyui-wan" in i.get("image_uuid", "") and i.get("actual_status") == "running"]
        stopped_insts = [i for i in instances if "comfyui-wan" in i.get("image_uuid", "") and i.get("actual_status") in ["exited", "stopped"]]
        
        self.instances.extend(running_insts[:self.num_instances])
        needed = self.num_instances - len(self.instances)
        
        # 2. Start stopped instances if needed
        if needed > 0 and stopped_insts:
            print(f"Found {len(stopped_insts)} stopped instances. Resuming them to save setup time...")
            for i in range(min(needed, len(stopped_insts))):
                inst_id = stopped_insts[i]['id']
                print(f"Starting instance {inst_id}...")
                subprocess.run(["vastai", "start", "instance", str(inst_id), "--api-key", settings.vast_api_key])
                self.instances.append(stopped_insts[i])
                needed -= 1
                
            if needed == 0:
                print("Waiting 15 seconds for instances to transition state...")
                time.sleep(15)
        
        # 3. Spin up new needed instances
        if needed > 0:
            print(f"Need {needed} more instances. Searching market...")
            if self.use_ultra:
                query = "gpu_ram>=80000 cuda_max_good>=12.1 num_gpus=1 rented=False"
            else:
                query = "gpu_name=RTX_3090 cuda_max_good>=12.1 num_gpus=1 rented=False"
                
            res = subprocess.run(["vastai", "search", "offers", query, "--raw", "--api-key", settings.vast_api_key], capture_output=True, text=True)
            offers = json.loads(res.stdout)
            
            # Sort by reliability and price
            offers = sorted(offers, key=lambda x: (x.get('reliability2', 0), -x['dph_base']), reverse=True)
            
            for i in range(min(needed, len(offers))):
                offer_id = offers[i]['id']
                print(f"Deploying Instance on Offer {offer_id}...")
                subprocess.run(["vastai", "create", "instance", str(offer_id), "--image", "hearmeman/comfyui-wan-template:v11", "--env", "-p 8188:8188 -p 16306:22", "--disk", "120", "--api-key", settings.vast_api_key, "--onstart-cmd", "sleep infinity"])
                
        # 4. Wait for all to be running
        if self.num_instances > len(running_insts):
            print("Polling Vast.ai until instances finish downloading/booting and enter 'running' state (can take 5-15 mins)...")
            for attempt in range(60):
                time.sleep(30)
                res = subprocess.run(["vastai", "show", "instances", "--raw", "--api-key", settings.vast_api_key], capture_output=True, text=True)
                try:
                    instances = json.loads(res.stdout)
                    running_insts = [i for i in instances if "comfyui-wan" in i.get("image_uuid", "") and i.get("actual_status") == "running"]
                    if len(running_insts) >= self.num_instances:
                        self.instances = running_insts[:self.num_instances]
                        break
                except: pass
                print(f"Waiting for instances to boot... (Attempt {attempt+1}/60)")
            
        print(f"Successfully provisioned {len(self.instances)} instances.")
        
    def connect_and_init(self):
        key_path = os.path.join(os.getcwd(), 'vast_id')
        for inst in self.instances:
            ssh_host = inst['ssh_host']
            ssh_port = int(inst['ssh_port'])
            e = RemoteExecutor(ssh_host, ssh_port, key_path)
            if e.connect():
                print(f"[{ssh_host}] Connected!")
                
                # Upload and run init_studio.sh (Provider Agnostic setup)
                print(f"[{ssh_host}] Uploading init_studio.sh...")
                sftp = e.client.open_sftp()
                sftp.put("init_studio.sh", "/tmp/init_studio.sh")
                sftp.close()
                
                print(f"[{ssh_host}] Executing initialization script (Downloads models if missing)...")
                e.execute_sync("chmod +x /tmp/init_studio.sh && bash /tmp/init_studio.sh")
                
                print(f"[{ssh_host}] Updating ComfyUI Core to support latest Wan nodes...")
                e.execute_sync("cd /ComfyUI && git pull && /opt/venv/bin/pip install -r requirements.txt")
                
                print(f"[{ssh_host}] Booting AI-Dock native ComfyUI services...")
                e.execute_sync("/opt/ai-dock/bin/init.sh > /dev/null 2>&1 &")
                time.sleep(25) # Wait for supervisor and python to bind to 8188
                
                self.executors.append(e)
            else:
                print(f"[{ssh_host}] Failed to connect.")

    def run_job(self, executor, project_name, scene_idx, scene_data, proj_dir):
        """Dispatches a single job to the given executor (instance)."""
        vid_file = os.path.join(proj_dir, f"scene_{scene_idx:02d}.mp4")
        audio_file = os.path.join(proj_dir, f"scene_{scene_idx:02d}.mp3")
        os.makedirs(proj_dir, exist_ok=True)
        
        if os.path.exists(vid_file):
            return vid_file
            
        print(f"[{executor.host}] Queuing {project_name} Scene {scene_idx}...")
        
        # 1. Generate local audio first if needed for lip sync
        if not os.path.exists(audio_file) and 'text' in scene_data:
            print(f"[{executor.host}] Generating TTS for {project_name} Scene {scene_idx}...")
            # We use an event loop to run the async generate_audio in a synchronous thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(generate_audio(scene_data['text'], audio_file))
            loop.close()
            
        # 2. Build Advanced Workflow Payload
        payload = build_advanced_wan_payload(scene_data['prompt'])
            
        payload_json = json.dumps(payload).replace("'", "\\'")
        
        # 3. Submit via ComfyUI Prompt API (Port 8188 for v11) with retry logic
        executor.execute_sync(f"echo '{payload_json}' > /tmp/payload_{scene_idx}.json")
        
        prompt_id = None
        for submit_attempt in range(20):
            stdout = executor.execute_sync(f"curl -s -X POST http://localhost:8188/prompt -H 'Content-Type: application/json' -d @/tmp/payload_{scene_idx}.json")[0]
            response = stdout.read().decode().strip()
            print(f"[{executor.host}] Submit Response: {response}")
            
            try:
                if response:
                    resp_data = json.loads(response)
                    prompt_id = resp_data.get("prompt_id")
                    if prompt_id:
                        break
            except:
                pass
                
            print(f"[{executor.host}] ComfyUI API not ready or submission failed. Retrying in 15 seconds...")
            time.sleep(15)
            
        if not prompt_id:
            print(f"[{executor.host}] Prompt ID not returned after 20 attempts. Failing job.")
            return None
            
        # 4. Robust Polling using ComfyUI History API (Port 8188 for v11)
        print(f"[{executor.host}] Polling history for prompt {prompt_id}...")
        while True:
            stdout = executor.execute_sync(f"curl -s http://localhost:8188/history/{prompt_id}")[0]
            history_data = stdout.read().decode().strip()
            
            if not history_data or history_data == "{}":
                time.sleep(15)
                continue
                
            try:
                hist_json = json.loads(history_data)
                if prompt_id in hist_json:
                    print(f"[{executor.host}] Job {prompt_id} COMPLETED in ComfyUI!")
                    
                    # Extract outputs
                    outputs = hist_json[prompt_id].get("outputs", {})
                    remote_video_file = None
                    for node_id, output_data in outputs.items():
                        if "gifs" in output_data:
                            for gif in output_data["gifs"]:
                                if gif["filename"].endswith(".mp4"):
                                    remote_video_file = f"/workspace/ComfyUI/output/{gif['subfolder']}/{gif['filename']}" if gif.get('subfolder') else f"/workspace/ComfyUI/output/{gif['filename']}"
                                    break
                                    
                    if not remote_video_file:
                        # Fallback try finding latest mp4
                        remote_video_file = executor.execute_sync("ls -t /workspace/ComfyUI/output/*.mp4 2>/dev/null | head -n 1")[0].read().decode().strip()
                    
                    if remote_video_file and "No such file" not in remote_video_file:
                        print(f"[{executor.host}] Downloading {remote_video_file} -> {vid_file}")
                        sftp = executor.client.open_sftp()
                        sftp.get(remote_video_file, vid_file)
                        sftp.close()
                        executor.execute_sync(f"rm {remote_video_file}")
                        return vid_file
                    else:
                        print(f"[{executor.host}] History completed but video file not found!")
                        return None
            except json.JSONDecodeError:
                print(f"[{executor.host}] JSON Decode Error during history polling.")
                pass
                
            time.sleep(15)

    def dispatch(self):
        # Flatten all jobs
        all_jobs = []
        for project in ALL_PROJECTS:
            proj_dir = os.path.join('production_assets', project['name'])
            for i, scene in enumerate(project['scenes']):
                all_jobs.append({
                    "project_name": project['name'],
                    "scene_idx": i,
                    "scene_data": scene,
                    "proj_dir": proj_dir
                })
                
        # Dispatch using ThreadPoolExecutor across our instances
        if not self.executors:
            print("[FATAL] No executors successfully connected. Exiting dispatcher to prevent crash.")
            return
            
        print(f"Dispatching {len(all_jobs)} jobs across {len(self.executors)} instances in parallel...")
        
        # Use workers equal to the number of jobs to push everything to the ComfyUI queues instantly
        num_workers = max(1, len(self.executors) * 3)
        with ThreadPoolExecutor(max_workers=num_workers) as pool:
            futures = []
            for idx, job in enumerate(all_jobs):
                # Round-robin assign jobs to executors
                exec_target = self.executors[idx % len(self.executors)]
                futures.append(pool.submit(self.run_job, exec_target, job['project_name'], job['scene_idx'], job['scene_data'], job['proj_dir']))
                
            for future in as_completed(futures):
                try:
                    result = future.result()
                    print(f"Job completed: {result}")
                except Exception as e:
                    print(f"Job failed: {e}")
                    
    def stitch_movies(self):
        for project in ALL_PROJECTS:
            proj_dir = os.path.join('production_assets', project['name'])
            clips = []
            print(f"Stitching {project['name']}...")
            for i in range(len(project['scenes'])):
                v_path = os.path.join(proj_dir, f"scene_{i:02d}.mp4")
                a_path = os.path.join(proj_dir, f"scene_{i:02d}.mp3")
                if os.path.exists(v_path) and os.path.exists(a_path):
                    try:
                        vid = VideoFileClip(v_path)
                        aud = AudioFileClip(a_path)
                        if aud.duration > vid.duration:
                            vid = vid.loop(duration=aud.duration)
                        vid = vid.set_audio(aud)
                        clips.append(vid)
                    except Exception as e: pass
                    
            if clips:
                final_name = f"FINAL_PARALLEL_{project['name']}.mp4"
                final_video = concatenate_videoclips(clips)
                final_video.write_videofile(final_name, fps=24, codec="libx264", audio_codec="aac")
                print(f"Finished {final_name}!")
                
    def shutdown(self):
        for e in self.executors:
            e.close()
        for inst in self.instances:
            inst_id = inst['id']
            print(f"Stopping instance {inst_id} to save state and preserve credits...")
            subprocess.run(["vastai", "stop", "instance", str(inst_id), "--api-key", settings.vast_api_key])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-Instance Parallel Render Dispatcher")
    parser.add_argument("-n", "--instances", type=int, default=1, help="Number of Vast AI instances to distribute jobs across")
    parser.add_argument("-u", "--ultra", action="store_true", help="Use 80GB VRAM (H100/A100) instances")
    args = parser.parse_args()
    
    dispatcher = JobDispatcher(num_instances=args.instances, max_price=5.0, use_ultra=args.ultra)
    dispatcher.provision_instances()
    dispatcher.connect_and_init()
    dispatcher.dispatch()
    dispatcher.stitch_movies()
    dispatcher.shutdown()

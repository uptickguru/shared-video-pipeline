"""
Pre-flight diagnostic: verify the remote instance is healthy and ready for rendering.
Checks SSH, model files, ComfyUI boot, and UNETLoader model paths.
"""
import paramiko
import json
import time
import sys

HOST = 'ssh8.vast.ai'
PORT = 14476
KEY = 'vast_id'

def ssh_connect(retries=12):
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    for i in range(retries):
        try:
            print(f"SSH attempt {i+1}/{retries}...")
            c.connect(HOST, port=PORT, username='root', key_filename=KEY, timeout=15)
            print("SSH connected!")
            return c
        except Exception as e:
            print(f"  Failed: {e}")
            time.sleep(10)
    return None

def run(c, cmd):
    stdin, stdout, stderr = c.exec_command(cmd)
    stdout.channel.recv_exit_status()
    return stdout.read().decode('utf-8', errors='ignore').strip()

def main():
    c = ssh_connect()
    if not c:
        print("FATAL: Cannot SSH into instance")
        sys.exit(1)
    
    # 1. Check model files
    print("\n=== MODEL FILES ===")
    for path in [
        '/ComfyUI/models/diffusion_models',
        '/ComfyUI/models/unet',
        '/ComfyUI/models/text_encoders',
        '/ComfyUI/models/clip',
        '/ComfyUI/models/vae',
    ]:
        result = run(c, f'ls {path} 2>/dev/null')
        print(f"{path}: {result if result else '(empty or missing)'}")
    
    # 2. Check if ComfyUI is running
    print("\n=== COMFYUI STATUS ===")
    ps = run(c, 'pgrep -af main.py')
    print(f"ComfyUI process: {ps if ps else 'NOT RUNNING'}")
    
    # 3. If not running, start it
    if not ps:
        print("Starting ComfyUI...")
        run(c, 'cd /ComfyUI && nohup python main.py --listen 0.0.0.0 --port 8188 >/comfy_manual.log 2>&1 </dev/null &')
        print("Waiting 30s for ComfyUI to boot...")
        time.sleep(30)
    
    # 4. Check API
    print("\n=== API CHECK ===")
    stats = run(c, 'curl -s http://localhost:8188/system_stats')
    if '"uptime"' in stats:
        print("ComfyUI API is HEALTHY")
    else:
        print(f"ComfyUI API response: {stats[:200]}")
        print("Waiting 15 more seconds...")
        time.sleep(15)
        stats = run(c, 'curl -s http://localhost:8188/system_stats')
        if '"uptime"' in stats:
            print("ComfyUI API is HEALTHY (after extra wait)")
        else:
            print("ComfyUI API still not ready")
            print("Last 20 lines of /comfy_manual.log:")
            print(run(c, 'tail -20 /comfy_manual.log'))
            c.close()
            sys.exit(1)
    
    # 5. Check UNETLoader available models
    print("\n=== UNET LOADER MODELS ===")
    info = json.loads(run(c, 'curl -s http://localhost:8188/object_info'))
    unet_models = info.get('UNETLoader', {}).get('input', {}).get('required', {}).get('unet_name', [[]])[0]
    print(f"Available: {unet_models}")
    
    # 6. Check CLIPLoader models
    print("\n=== CLIP LOADER MODELS ===")
    clip_models = info.get('CLIPLoader', {}).get('input', {}).get('required', {}).get('clip_name', [[]])[0]
    print(f"Available: {clip_models}")
    
    # 7. Check VAELoader models
    print("\n=== VAE LOADER MODELS ===")
    vae_models = info.get('VAELoader', {}).get('input', {}).get('required', {}).get('vae_name', [[]])[0]
    print(f"Available: {vae_models}")
    
    print("\n=== DIAGNOSTIC COMPLETE ===")
    c.close()

if __name__ == '__main__':
    main()

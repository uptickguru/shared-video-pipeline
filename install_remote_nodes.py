from remote_executor import RemoteExecutor
import os

HOST = "ssh6.vast.ai"
PORT = 13014
KEY_PATH = os.path.join(os.getcwd(), "vast_id")

def main():
    executor = RemoteExecutor(HOST, PORT, KEY_PATH)
    if not executor.connect():
        return

    # Using a multi-line string for the remote script to avoid shell escaping issues
    remote_script = """
cd /opt/ComfyUI/custom_nodes
rm -rf ComfyUI-WanVideoWrapper
curl -L https://github.com/kijai/ComfyUI-WanVideoWrapper/archive/refs/heads/main.zip -o /workspace/wan.zip
apt-get update && apt-get install -y unzip
unzip /workspace/wan.zip -d /opt/ComfyUI/custom_nodes
mv /opt/ComfyUI/custom_nodes/ComfyUI-WanVideoWrapper-main /opt/ComfyUI/custom_nodes/ComfyUI-WanVideoWrapper
cd /opt/ComfyUI/custom_nodes/ComfyUI-WanVideoWrapper
/opt/environments/python/comfyui/bin/pip install -r requirements.txt
"""
    
    print("Installing Wan-2.1 Custom Nodes on remote...")
    # Write the script on the remote machine
    executor.execute_sync(f"echo '{remote_script}' > /workspace/install_wan.sh")
    # Run the script
    stdout, stderr = executor.execute_sync("bash /workspace/install_wan.sh")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    print("Restarting ComfyUI...")
    executor.execute("pkill -f main.py")
    time.sleep(2)
    executor.execute("source /opt/environments/python/comfyui/bin/activate && cd /opt/ComfyUI && nohup python main.py --listen 0.0.0.0 --port 18188 > /workspace/comfy_manual.log 2>&1 &")
    
    executor.close()
    print("Done!")

if __name__ == "__main__":
    import time
    main()

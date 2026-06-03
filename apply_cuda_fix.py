import os
from remote_executor import RemoteExecutor

def main():
    ssh_host = "ssh5.vast.ai"
    ssh_port = 27576
    key_path = os.path.join(os.getcwd(), "vast_id")
    
    executor = RemoteExecutor(ssh_host, ssh_port, key_path)
    if not executor.connect():
        print("Failed to connect.")
        return
        
    print("\n--- Renaming CUDA Compat Folder ---")
    stdout = executor.execute("mv /usr/local/cuda/compat /usr/local/cuda/compat.bak 2>/dev/null || echo 'Already renamed or not found'")
    print(stdout.read().decode())
    
    print("\n--- Verifying PyTorch CUDA Access ---")
    stdout = executor.execute("/opt/venv/bin/python -c 'import torch; print(\"CUDA Available:\", torch.cuda.is_available()); print(\"Device Name:\", torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\")'")
    print(stdout.read().decode())
    
    print("\n--- Restarting ComfyUI ---")
    # Kill any ComfyUI processes
    executor.execute("kill -9 $(lsof -t -i:18188) 2>/dev/null || true")
    # Start in background
    executor.execute("cd /ComfyUI && nohup /opt/venv/bin/python main.py --listen 0.0.0.0 --port 18188 > /comfy_manual.log 2>&1 &")
    print("ComfyUI restarted.")

if __name__ == "__main__":
    main()

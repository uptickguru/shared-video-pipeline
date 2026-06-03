import os
from remote_executor import RemoteExecutor

def main():
    ssh_host = "ssh5.vast.ai"
    ssh_port = 27576
    key_path = os.path.join(os.getcwd(), "vast_id")
    
    print(f"Connecting to {ssh_host}:{ssh_port} to check progress...")
    executor = RemoteExecutor(ssh_host, ssh_port, key_path)
    if not executor.connect():
        print("Failed to connect via SSH.")
        return
        
    print("\n--- Python Executable Info ---")
    stdout = executor.execute("which python && python -c 'import sys; print(sys.executable)'")
    print(stdout.read().decode())
    
    print("\n--- ComfyUI Directory Listing ---")
    stdout = executor.execute("ls -la /ComfyUI")
    print(stdout.read().decode())

if __name__ == "__main__":
    main()

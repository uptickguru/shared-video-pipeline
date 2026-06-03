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
        
    print("\n--- ComfyUI Log (Grep VideoHelperSuite) ---")
    stdout = executor.execute("grep -i -C 5 'VideoHelperSuite' /comfy_manual.log 2>/dev/null || echo 'No matches'")
    decoded = stdout.read().decode('utf-8', errors='ignore')
    sanitized = "".join([c for c in decoded if ord(c) < 128])
    print(sanitized)
    
    print("\n--- Folder Sizes ---")
    stdout = executor.execute("du -h --max-depth=2 /ComfyUI/models/")
    decoded = stdout.read().decode('utf-8', errors='ignore')
    sanitized = "".join([c for c in decoded if ord(c) < 128])
    print(sanitized)

if __name__ == "__main__":
    main()

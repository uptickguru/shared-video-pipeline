import os
from remote_executor import RemoteExecutor

def main():
    ssh_host = "ssh3.vast.ai"
    ssh_port = 32114
    key_path = os.path.join(os.getcwd(), "vast_id")
    
    executor = RemoteExecutor(ssh_host, ssh_port, key_path)
    if not executor.connect():
        print("Failed to connect.")
        return
        
    print("\n--- ComfyUI Registered Nodes matching 'video' or 'combine' ---")
    stdout = executor.execute("python -c \"import urllib.request, json; data = json.loads(urllib.request.urlopen('http://localhost:18188/object_info').read()); print([k for k in data.keys() if 'video' in k.lower() or 'combine' in k.lower()])\"")
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

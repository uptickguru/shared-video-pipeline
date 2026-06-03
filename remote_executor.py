import paramiko
import time
import os
import json

class RemoteExecutor:
    def __init__(self, host, port, key_path):
        self.host = host
        self.port = int(port)
        self.key_path = key_path
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self, retries=30):
        # Determine fallback key if available
        user_fallback_key = os.path.expanduser("~/.ssh/id_ed25519")
        keys_to_try = [self.key_path]
        if os.path.exists(user_fallback_key) and user_fallback_key not in keys_to_try:
            keys_to_try.append(user_fallback_key)
            
        for i in range(retries):
            for kpath in keys_to_try:
                try:
                    print(f"[SSH] Connecting to {self.host}:{self.port} using key: {os.path.basename(kpath)} (Attempt {i+1})...")
                    self.client.connect(
                        hostname=self.host,
                        port=self.port,
                        username="root",
                        key_filename=kpath,
                        timeout=15
                    )
                    print(f"[SSH] Connection successful using key: {os.path.basename(kpath)}!")
                    self.key_path = kpath
                    return True
                except Exception as e:
                    print(f"[SSH] Key {os.path.basename(kpath)} failed: {e}")
            time.sleep(10)
        return False

    def execute(self, command):
        print(f"[SSH] Executing: {command}")
        stdin, stdout, stderr = self.client.exec_command(command)
        return stdout

    def execute_sync(self, command):
        print(f"[SSH] Executing (Sync): {command}")
        stdin, stdout, stderr = self.client.exec_command(command)
        # Read all output BEFORE checking exit status (Paramiko can lose data otherwise)
        out_data = stdout.read().decode('utf-8', errors='ignore')
        err_data = stderr.read().decode('utf-8', errors='ignore')
        exit_status = stdout.channel.recv_exit_status()
        print(f"[SSH] Command finished with exit status: {exit_status}")
        return out_data, err_data

    def submit_prompt(self, workflow_json):
        """Submit a prompt to ComfyUI using the proven temp-file approach.
        Writes JSON to /tmp/comfy_prompt.json via SFTP, then curls from that file.
        This avoids all shell escaping issues with complex nested JSON."""
        import io
        payload = json.dumps(workflow_json)
        
        # Write payload to remote temp file via SFTP (zero escaping issues)
        sftp = self.client.open_sftp()
        with sftp.file("/tmp/comfy_prompt.json", "w") as f:
            f.write(payload)
        sftp.close()
        
        # Submit using curl with -d @file (proven method from last night's successful run)
        stdout, stderr = self.execute_sync(
            "curl -s -X POST http://localhost:8188/prompt "
            "-H 'Content-Type: application/json' "
            "-d @/tmp/comfy_prompt.json"
        )
        response = stdout.strip()
        print(f"[COMFY] Server Response: {response}")
        return response

    def close(self):
        self.client.close()

def setup_machine(host, port, key_path, hf_token):
    executor = RemoteExecutor(host, port, key_path)
    if not executor.connect():
        return False
    
    # Run the setup commands
    commands = [
        "mkdir -p /workspace/ComfyUI/models/diffusion_models /workspace/ComfyUI/models/vae /workspace/ComfyUI/models/clip",
        f"wget --header='Authorization: Bearer {hf_token}' -O /workspace/ComfyUI/models/diffusion_models/wan2.1_t2v_1.3B_bf16.safetensors https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_t2v_1.3B_bf16.safetensors",
        f"wget --header='Authorization: Bearer {hf_token}' -O /workspace/ComfyUI/models/clip/umt5_xxl_fp8_e4m3fn.safetensors https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn.safetensors",
        f"wget --header='Authorization: Bearer {hf_token}' -O /workspace/ComfyUI/models/vae/wan_2.1_vae.safetensors https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors",
        "/opt/ai-dock/bin/init.sh &" # Start services in background
    ]
    
    for cmd in commands:
        executor.execute(cmd)
        time.sleep(2)
        
    executor.close()
    return True

from remote_executor import RemoteExecutor
import os
import time

HOST = "ssh6.vast.ai"
PORT = 13014
KEY_PATH = os.path.join(os.getcwd(), "vast_id")
REMOTE_DIR = "/workspace/ComfyUI/output"
LOCAL_DIR = os.path.join(os.getcwd(), "output_videos")

def main():
    if not os.path.exists(LOCAL_DIR):
        os.makedirs(LOCAL_DIR)

    executor = RemoteExecutor(HOST, PORT, KEY_PATH)
    if not executor.connect():
        return

    print(f"Checking for finished videos in {REMOTE_DIR}...")
    
    # List files in remote output directory
    stdout = executor.execute(f"ls {REMOTE_DIR}/*.mp4")
    files = stdout.read().decode().split()
    
    if not files:
        print("No videos ready yet. Still cooking!")
    else:
        print(f"Found {len(files)} video(s). Downloading...")
        # Note: In a real paramiko implementation we'd use sftp.get()
        # For now we'll use a simple scp-like command via the shell
        for remote_file in files:
            filename = os.path.basename(remote_file)
            local_file = os.path.join(LOCAL_DIR, filename)
            print(f"Downloading {filename}...")
            # Using scp directly for the transfer
            scp_cmd = f'scp -P {PORT} -i "{KEY_PATH}" root@{HOST}:{remote_file} "{local_file}"'
            os.system(scp_cmd)
    
    executor.close()

if __name__ == "__main__":
    main()

from remote_executor import RemoteExecutor
import os

HOST = "ssh6.vast.ai"
PORT = 13014
KEY_PATH = os.path.join(os.getcwd(), "vast_id")

def main():
    executor = RemoteExecutor(HOST, PORT, KEY_PATH)
    if not executor.connect():
        return

    # Look for failed imports in the log
    cmd = "grep -C 10 -i 'failed' /opt/ComfyUI/comfyui_18188.log | tail -n 20"
    stdout = executor.execute(cmd)
    print("Failed Imports with Context:")
    print(stdout.read().decode())
    
    cmd = "grep -i 'skip' /opt/ComfyUI/comfyui_18188.log | head -n 50"
    stdout = executor.execute(cmd)
    print("Skipped Nodes in Log:")
    print(stdout.read().decode())
    
    executor.close()

if __name__ == "__main__":
    main()

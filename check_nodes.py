from remote_executor import RemoteExecutor
import os

HOST = "ssh6.vast.ai"
PORT = 13014
KEY_PATH = os.path.join(os.getcwd(), "vast_id")

def main():
    executor = RemoteExecutor(HOST, PORT, KEY_PATH)
    if not executor.connect():
        return

    # Check for node names in the wrapper
    cmd = "grep -h 'class ' /opt/ComfyUI/custom_nodes/ComfyUI-WanVideoWrapper/*.py"
    stdout = executor.execute(cmd)
    print("Potential Node Classes:")
    print(stdout.read().decode())
    
    executor.close()

if __name__ == "__main__":
    main()

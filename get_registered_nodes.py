from remote_executor import RemoteExecutor
import os

HOST = "ssh6.vast.ai"
PORT = 13014
KEY_PATH = os.path.join(os.getcwd(), "vast_id")

def main():
    executor = RemoteExecutor(HOST, PORT, KEY_PATH)
    if not executor.connect():
        return

    # Check for node names via API
    cmd = "curl -s http://localhost:18188/object_info | grep -o 'WanVideo[^\\\"]*' | sort | uniq"
    stdout = executor.execute(cmd)
    print("Actual Registered Nodes on Server:")
    print(stdout.read().decode())
    
    executor.close()

if __name__ == "__main__":
    main()

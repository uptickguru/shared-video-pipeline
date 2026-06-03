from remote_executor import RemoteExecutor
import os

HOST = "ssh6.vast.ai"
PORT = 13014
KEY_PATH = os.path.join(os.getcwd(), "vast_id")

def main():
    executor = RemoteExecutor(HOST, PORT, KEY_PATH)
    if not executor.connect():
        return

    # Use a clean method to write the test script
    test_code = """
import sys
import os
plugin_path = '/workspace/ComfyUI/custom_nodes/ComfyUI-WanVideoWrapper'
sys.path.append(plugin_path)
sys.path.append('/workspace/ComfyUI')

try:
    print('Attempting to import nodes...')
    import nodes
    print('SUCCESS: nodes imported')
except Exception as e:
    print(f'FAILURE: {e}')
    import traceback
    traceback.print_exc()
"""
    
    # Write test script to remote
    executor.execute_sync(f"echo \"{test_code}\" > /workspace/debug_import.py")
    
    # Run it
    stdout, stderr = executor.execute_sync("/opt/environments/python/comfyui/bin/python /workspace/debug_import.py")
    print("STDOUT:")
    print(stdout.read().decode())
    print("STDERR:")
    print(stderr.read().decode())
    
    executor.close()

if __name__ == "__main__":
    main()

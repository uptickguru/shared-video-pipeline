import sys
import os
import time
from vast.manager import VastManager
from remote_executor import RemoteExecutor
from config import settings

def main():
    print("=== EXTRACTING INFLUENCER WORKFLOW FROM INSTANCE 38625547 ===")
    manager = VastManager(settings.vast_api_key)
    instance_id = 38625547
    
    ssh_host, ssh_port = None, None
    for _ in range(120): # Wait up to 30 mins
        time.sleep(15)
        instances = manager.list_instances()
        target_inst = next((i for i in instances if i.get('id') == instance_id), None)
        if not target_inst:
            print("Instance lost.")
            return
            
        cur_state = target_inst.get('cur_state')
        actual_status = target_inst.get('actual_status')
        print(f"Status: {cur_state} | {actual_status}")
        
        if cur_state == "running" and target_inst.get('ssh_host') and actual_status == "running":
            ssh_host = target_inst.get('ssh_host')
            ssh_port = int(target_inst.get('ssh_port'))
            break
            
    if not ssh_host:
        print("Failed to boot.")
        return
        
    time.sleep(15)
    key_path = os.path.join(os.getcwd(), "vast_id")
    executor = RemoteExecutor(ssh_host, ssh_port, key_path)
    
    connected = False
    for _ in range(10):
        if executor.connect():
            connected = True
            break
        time.sleep(10)
        
    if not connected:
        print("SSH failed.")
        return
        
    key_path = executor.key_path
    
    print("Connected! Searching for workflow JSONs...")
    search_cmd = "find /workspace -type f -name '*.json' 2>/dev/null | grep -iE 'comfyui.*workflow' > /tmp/found_workflows.txt"
    executor.execute_sync(search_cmd)
    
    executor.execute_sync("find /workspace -type f -path '*/user/default/workflows/*.json' 2>/dev/null >> /tmp/found_workflows.txt")
    
    stdout, _ = executor.execute_sync("cat /tmp/found_workflows.txt")
    found_files = stdout.read().decode().strip()
    
    if found_files:
        print(f"Found files:\n{found_files}")
        executor.execute_sync("tar -czvf /tmp/workflows.tar.gz -T /tmp/found_workflows.txt")
        
        local_tar = os.path.join(os.getcwd(), "workflows_heist.tar.gz")
        scp_cmd = f'scp -P {ssh_port} -o StrictHostKeyChecking=no -i "{key_path}" root@{ssh_host}:/tmp/workflows.tar.gz "{local_tar}"'
        os.system(scp_cmd)
        print("Downloaded workflows to workflows_heist.tar.gz")
    else:
        print("No workflows found using find.")
        
    print("Stopping instance to save state (instead of destroying)...")
    # manager.destroy_instance(instance_id) # Commented out to preserve!
    os.system(f"vastai stop instance {instance_id} --api-key {settings.vast_api_key}")
    executor.close()
    print("Done!")

if __name__ == "__main__":
    main()

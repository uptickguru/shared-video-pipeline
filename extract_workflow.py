import sys
import os
import time
from vast.manager import VastManager
from remote_executor import RemoteExecutor
from config import settings

def main():
    print("=== EXTRACTING INFLUENCER WORKFLOW FROM V3 IMAGE ===")
    manager = VastManager(settings.vast_api_key)
    
    offers = manager.search_offers(gpu_name="RTX_3090", max_price=1.50)
    if not offers:
        print("[ERROR] No RTX_3090 offers found.")
        return
        
    offer_id = int(offers[0]['id'])
    image_name = "hearmeman/hearmemanai-consistent-chars:v3"
    print(f"Renting GPU with offer {offer_id} and image {image_name}...")
    
    rental_result = manager.create_instance(
        offer_id=offer_id,
        image=image_name,
        onstart="sleep infinity" # Just keep it alive
    )
    
    if not rental_result:
        print("[ERROR] Failed to rent instance.")
        return
        
    instance_id = rental_result.get('new_contract')
    print(f"Instance ID: {instance_id}")
    
    ssh_host, ssh_port = None, None
    for _ in range(120): # Wait up to 30 mins
        time.sleep(15)
        instances = manager.list_instances()
        target_inst = next((i for i in instances if i.get('id') == instance_id), None)
        if not target_inst:
            continue
            
        cur_state = target_inst.get('cur_state')
        actual_status = target_inst.get('actual_status')
        print(f"Status: {cur_state} | {actual_status}")
        
        if cur_state == "running" and target_inst.get('ssh_host') and actual_status == "running":
            ssh_host = target_inst.get('ssh_host')
            ssh_port = int(target_inst.get('ssh_port'))
            break
            
    if not ssh_host:
        print("Failed to boot.")
        manager.destroy_instance(instance_id)
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
        manager.destroy_instance(instance_id)
        return
        
    key_path = executor.key_path
    
    print("Connected! Searching for workflow JSONs...")
    # Find all json files in ComfyUI folders that contain 'workflow' or are in 'workflows' dir
    search_cmd = "find / -type f -name '*.json' 2>/dev/null | grep -iE 'comfyui.*workflow' > /tmp/found_workflows.txt"
    executor.execute_sync(search_cmd)
    
    # Also find files in user/default/workflows
    executor.execute_sync("find / -type f -path '*/user/default/workflows/*.json' 2>/dev/null >> /tmp/found_workflows.txt")
    
    # Check if we found anything
    stdout, _ = executor.execute_sync("cat /tmp/found_workflows.txt")
    found_files = stdout.read().decode().strip()
    
    if found_files:
        print(f"Found files:\n{found_files}")
        executor.execute_sync("tar -czvf /tmp/workflows.tar.gz -T /tmp/workflows.txt || tar -czvf /tmp/workflows.tar.gz -T /tmp/found_workflows.txt")
        
        local_tar = os.path.join(os.getcwd(), "workflows_heist.tar.gz")
        scp_cmd = f'scp -P {ssh_port} -o StrictHostKeyChecking=no -i "{key_path}" root@{ssh_host}:/tmp/workflows.tar.gz "{local_tar}"'
        os.system(scp_cmd)
        
        print("Downloaded workflows to workflows_heist.tar.gz")
    else:
        print("No workflows found using find.")
        
    print("Destroying instance...")
    manager.destroy_instance(instance_id)
    executor.close()
    print("Done!")

if __name__ == "__main__":
    main()

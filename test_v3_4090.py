import sys
import os
import time
from vast.manager import VastManager
from remote_executor import RemoteExecutor
from config import settings

def main():
    print("=== RTX 4090 V3 IMAGE BOOT TEST ===")
    manager = VastManager(settings.vast_api_key)
    
    # Search for an RTX 4090, max price $1.00 (plenty for a single 4090)
    offers = manager.search_offers(gpu_name="RTX_4090", max_price=1.00)
    if not offers:
        print("[ERROR] No high-tier RTX_4090 offers found matching our strict disk/inet criteria.")
        return
        
    offer_id = int(offers[0]['id'])
    image_name = "hearmeman/hearmemanai-consistent-chars:v3"
    print(f"Renting RTX 4090 (Offer {offer_id}) with image {image_name}...")
    
    rental_result = manager.create_instance(
        offer_id=offer_id,
        image=image_name,
        onstart="sleep infinity" 
    )
    
    if not rental_result:
        print("[ERROR] Failed to rent instance.")
        return
        
    instance_id = rental_result.get('new_contract')
    print(f"Instance ID: {instance_id}")
    
    ssh_host, ssh_port = None, None
    
    # Wait up to 35 minutes for extraction
    for attempt in range(140):
        time.sleep(15)
        instances = manager.list_instances()
        target_inst = next((i for i in instances if i.get('id') == instance_id), None)
        if not target_inst:
            print("[ERROR] Instance disappeared from Vast!")
            return
            
        cur_state = target_inst.get('cur_state')
        actual_status = target_inst.get('actual_status')
        status_msg = target_inst.get('status_msg', '')
        print(f"[{attempt}/140] Status: {cur_state} | Actual: {actual_status} | Msg: {status_msg}")
        
        if cur_state == "running" and target_inst.get('ssh_host') and actual_status == "running":
            ssh_host = target_inst.get('ssh_host')
            ssh_port = int(target_inst.get('ssh_port'))
            print("SUCCESS! RTX 4090 SUCCESSFULLY BOOTED THE V3 IMAGE!")
            break
            
    if not ssh_host:
        print("FAILED TO BOOT AFTER 35 MINUTES. Destroying instance to save credits.")
        manager.destroy_instance(instance_id)
        return
        
    print("Giving SSH daemon 15 seconds to fully bind ports...")
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
        print("SSH failed. Destroying instance.")
        manager.destroy_instance(instance_id)
        return
        
    key_path = executor.key_path
    
    print("Connected! Executing the Heist (Extracting JSON Workflows)...")
    search_cmd = "find /workspace -type f -name '*.json' 2>/dev/null | grep -iE 'comfyui.*workflow' > /tmp/found_workflows.txt"
    executor.execute_sync(search_cmd)
    executor.execute_sync("find /workspace -type f -path '*/user/default/workflows/*.json' 2>/dev/null >> /tmp/found_workflows.txt")
    
    stdout, _ = executor.execute_sync("cat /tmp/found_workflows.txt")
    found_files = stdout.read().decode().strip()
    
    if found_files:
        print(f"Found workflow files:\n{found_files}")
        executor.execute_sync("tar -czvf /tmp/workflows.tar.gz -T /tmp/found_workflows.txt")
        
        local_tar = os.path.join(os.getcwd(), "workflows_heist_4090.tar.gz")
        scp_cmd = f'scp -P {ssh_port} -o StrictHostKeyChecking=no -i "{key_path}" root@{ssh_host}:/tmp/workflows.tar.gz "{local_tar}"'
        os.system(scp_cmd)
        print("Heist Successful! Downloaded workflows to workflows_heist_4090.tar.gz")
    else:
        print("No ComfyUI workflows found inside the container.")
        
    print("Stopping instance to save state (instead of destroying)...")
    os.system(f"vastai stop instance {instance_id} --api-key {settings.vast_api_key}")
    executor.close()
    print("Test complete.")

if __name__ == "__main__":
    main()

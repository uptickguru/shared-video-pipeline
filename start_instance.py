from vast.manager import VastManager
from config import settings

# Start the stopped instance
m = VastManager(settings.vast_api_key)
inst = m.get_active_instance()
if inst:
    print(f"Instance {inst['id']} is now {inst.get('actual_status')} at {inst.get('ssh_host')}:{inst.get('ssh_port')}")
else:
    print("No instance available")

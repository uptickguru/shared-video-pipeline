from vast.manager import VastManager
from config import settings
import json

m = VastManager(settings.vast_api_key)
instances = m.list_instances()
print(f"Total instances: {len(instances)}")
for i in instances:
    print(f"  ID={i.get('id')} actual_status={i.get('actual_status')} intended_status={i.get('intended_status')} ssh_host={i.get('ssh_host')} ssh_port={i.get('ssh_port')} gpu={i.get('gpu_name')} dph=${i.get('dph_total',0):.3f}")

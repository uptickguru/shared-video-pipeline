from vast.manager import VastManager
from config import settings

def check_instances():
    v = VastManager(settings.vast_api_key)
    inst = v.list_instances()
    for i in inst:
        print(f"ID: {i.get('id')}")
        print(f"  Cur State: {i.get('cur_state')}")
        print(f"  Next State: {i.get('next_state')}")
        print(f"  SSH: {i.get('ssh_host')}:{i.get('ssh_port')}")
        print(f"  Web: {i.get('public_ipaddr')}")
        print(f"  Status: {i.get('status_msg')}")

if __name__ == "__main__":
    check_instances()

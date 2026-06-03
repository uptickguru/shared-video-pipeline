from vast.manager import VastManager
from config import settings

def kill_all():
    v = VastManager(settings.vast_api_key)
    inst = v.list_instances()
    print(f"Destroying {len(inst)} instances...")
    for i in inst:
        v.destroy_instance(i['id'])
        print(f"Destroyed {i['id']}")

if __name__ == "__main__":
    kill_all()

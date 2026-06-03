from vast.manager import VastManager
from config import settings

def cleanup():
    v = VastManager(settings.vast_api_key)
    inst = v.list_instances()
    print(f"Total Active Instances: {len(inst)}")
    
    if len(inst) > 1:
        print("Detected redundant instances. Keeping the first one and destroying the rest...")
        # Keep the first one (usually the oldest/best setup)
        for i in inst[1:]:
            v.destroy_instance(i['id'])
            print(f"Destroyed redundant instance {i['id']}")
    else:
        print("No redundancy detected.")

if __name__ == "__main__":
    cleanup()

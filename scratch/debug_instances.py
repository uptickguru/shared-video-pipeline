import os
from vast.manager import VastManager
from config import settings

m = VastManager(settings.vast_api_key)
instances = m.list_instances()
print("INSTANCES:")
for inst in instances:
    print(inst)

print("\nSTARTING INSTANCE 38654477:")
res = m.sdk.start_instance(38654477)
print("Result of start_instance:", res)

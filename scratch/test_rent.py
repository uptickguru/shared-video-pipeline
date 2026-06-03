import os
import sys
from vast.manager import VastManager
from config import settings

m = VastManager(settings.vast_api_key)
print("Searching for RTX_3090 / RTX_4090 offers...")
offers = m.search_offers(gpu_name="RTX_4090", max_price=2.50)
if not offers:
    offers = m.search_offers(gpu_name="RTX_3090", max_price=1.80)

if not offers:
    print("No offers found!")
    sys.exit(0)

print(f"Found {len(offers)} offers. Attempting to rent the first offer:")
offer = offers[0]
print(offer)

offer_id = int(offer['id'])
print(f"Renting offer {offer_id}...")
try:
    res = m.sdk.create_instance(
        offer_id,
        image=settings.vast_image,
        onstart_cmd=settings.vast_onstart_script,
        disk=250
    )
    print("Rental result:", res)
except Exception as e:
    print("Rental failed with exception:", e)
    if hasattr(e, 'response') and e.response is not None:
        print("Response body:", e.response.text)
    import traceback
    traceback.print_exc()

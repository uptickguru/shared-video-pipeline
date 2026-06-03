from vast.manager import VastManager
from config import settings

m = VastManager(settings.vast_api_key)

print("Querying RTX 4090 offers:")
offers = m.sdk.search_offers(query='gpu_name=RTX_4090 rentable=True verified=True disk_space>=120', order='dph')
print(f"Found {len(offers)} offers")
for o in offers[:10]:
    print(o['id'], o.get('gpu_name'), o['dph_total'], o.get('country_code'), o.get('geolocation'))

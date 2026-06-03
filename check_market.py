from vast.manager import VastManager
from config import settings

def check_market():
    vast = VastManager(settings.vast_api_key)
    # Search for all 4090s to see prices
    print("Checking current RTX_4090 market...")
    query = "gpu_name=RTX_4090 verified=True rentable=True"
    offers = vast.sdk.search_offers(query=query, order="dph")
    if not offers:
        print("No RTX_4090s found at all!")
    else:
        print(f"Found {len(offers)} RTX_4090s.")
        for i, offer in enumerate(offers[:10]):
            print(f"{i+1}. ID: {offer['id']} | Price: ${offer['dph_total']:.3f}/hr | Reliability: {offer['reliability']:.2%}")

if __name__ == "__main__":
    check_market()

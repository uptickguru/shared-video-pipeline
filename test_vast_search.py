from vast.manager import VastManager
from config import settings

def test_search_for_gpu(gpu_name: str, max_price: float):
    print(f"\nSearching for {gpu_name} offers under ${max_price}/hr...")
    vast = VastManager(settings.vast_api_key)
    try:
        offers = vast.search_offers(gpu_name=gpu_name, max_price=max_price)
        if not offers:
            print(f"No {gpu_name} offers found matching criteria.")
        else:
            print(f"Found {len(offers)} {gpu_name} offers!")
            for offer in offers[:5]: # Show top 5
                print(f"- ID: {offer['id']} | Machine: {offer['machine_id']} | Price: ${offer['dph_total']:.3f}/hr | Reliability: {offer['reliability']:.2%}")
    except Exception as e:
        print(f"Error connecting to Vast.ai for {gpu_name}: {e}")

def main():
    print(f"--- RUNNING VAST GPU OFFER SEARCH TESTS ---")
    print(f"Active Environment: {settings.environment}")
    
    # 1. Test Development target (RTX 3090)
    test_search_for_gpu(settings.dev_gpu, settings.dev_max_price)
    
    # 2. Test Production target (RTX 4090)
    test_search_for_gpu(settings.prod_gpu, settings.prod_max_price)

if __name__ == "__main__":
    main()

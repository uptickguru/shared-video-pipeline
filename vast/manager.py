from vastai import VastAI
import json
import time

class VastManager:
    def __init__(self, api_key: str):
        self.api_key = api_key
        # The official SDK handles the headers and authentication
        self.sdk = VastAI(api_key=api_key)

    def search_offers(self, gpu_name: str = "RTX_4090", max_price: float = 2.20):
        """
        Search for available GPU offers using the official SDK query format.
        """
        # Ensure the GPU name doesn't contain spaces which break the query parser
        gpu_clean = gpu_name.replace(" ", "_")
        # Removed hardcoded dph>0.35 limit to support cheap RTX 3090s
        query_str = f"gpu_name={gpu_clean} dph<{max_price} verified=True rentable=True reliability>0.95 disk_space>=250 host_id!=1647 inet_down>=600"
        print(f"[VAST] Searching with query: {query_str}")
        
        try:
            offers = self.sdk.search_offers(query=query_str, order="dph")
            # Programmatically filter out China-based hosts to avoid Great Firewall throttling on Docker/Hugging Face
            filtered_offers = []
            for offer in offers:
                country = str(offer.get('country_code', '')).upper()
                geo = str(offer.get('geolocation', '')).lower()
                if country == 'CN' or 'china' in geo:
                    continue
                filtered_offers.append(offer)
            return filtered_offers
        except Exception as e:
            print(f"[VAST] Search failed: {e}")
            return []

    def create_instance(self, offer_id: int = None, image: str = None, onstart: str = None):
        """
        Rents a GPU. If offer_id is not specified, automatically finds the best cheap offer
        matching the active environment in config.py.
        """
        from config import settings
        image = image or settings.vast_image
        onstart = onstart or settings.vast_onstart_script
        
        if offer_id is None:
            # Auto-find best offer based on environment
            gpu_name = settings.dev_gpu if settings.environment == "development" else settings.prod_gpu
            max_price = settings.dev_max_price if settings.environment == "development" else settings.prod_max_price
            print(f"[VAST] No offer_id specified. Auto-searching for {gpu_name} (Environment: {settings.environment})...")
            
            offers = self.search_offers(gpu_name=gpu_name, max_price=max_price)
            if not offers:
                print(f"[VAST] Failed to find any suitable offers for {gpu_name} under ${max_price}/hr.")
                return None
            offer_id = int(offers[0]['id'])
            print(f"[VAST] Selected best offer {offer_id} at ${offers[0]['dph_total']:.3f}/hr.")

        print(f"[VAST] Renting offer {offer_id} with image {image}...")
        
        try:
            # create_instance in SDK takes parameters for the rental
            result = self.sdk.create_instance(
                offer_id, # Positional ID
                image=image, 
                onstart_cmd=onstart,
                disk=250,
                label="video-pipeline-node"
            )
            print(f"[VAST] Rental success: {result}")
            return result
        except Exception as e:
            print(f"[VAST] Rental failed: {e}")
            return None

    def list_instances(self):
        try:
            return self.sdk.show_instances()
        except Exception as e:
            print(f"[VAST] Failed to list instances: {e}")
            return []

    def destroy_instance(self, instance_id: int):
        print(f"[VAST] Destroying instance {instance_id}...")
        try:
            return self.sdk.destroy_instance(instance_id) # Positional
        except Exception as e:
            print(f"[VAST] Destroy failed: {e}")
            return None

    def stop_instance(self, instance_id: int):
        """
        Stops/pauses the active instance to halt hourly execution fees while preserving data.
        """
        print(f"[VAST] Stopping instance {instance_id} to pause billing...")
        try:
            return self.sdk.stop_instance(instance_id)
        except Exception as e:
            print(f"[VAST] Stop failed: {e}")
            return None

    def get_active_instance(self):
        """
        Returns the first running instance found. If none are running but a stopped one exists,
        starts it, waits for it to become running, and returns it. Otherwise returns None.
        """
        instances = self.list_instances()
        
        # 1. Check for already running instance
        for i in instances:
            if i.get('actual_status') == 'running' or i.get('cur_state') == 'running' or i.get('status_msg') == 'running':
                return i
                
        # 2. Check for stopped instance to resume
        for i in instances:
            if i.get('actual_status') in ['exited', 'stopped'] or i.get('intended_status') == 'stopped':
                inst_id = i['id']
                print(f"[VAST] Found stopped instance {inst_id}. Resuming/Starting it...")
                try:
                    self.sdk.start_instance(inst_id)
                    # Poll until running (up to 300 seconds)
                    for attempt in range(60):
                        time.sleep(5)
                        updated_instances = self.list_instances()
                        for u in updated_instances:
                            if u['id'] == inst_id:
                                if u.get('actual_status') == 'running' or u.get('cur_state') == 'running' or u.get('status_msg') == 'running':
                                    print(f"[VAST] Instance {inst_id} is now running.")
                                    # Give it an extra couple seconds for port forwarding to stabilize
                                    time.sleep(2)
                                    return u
                    print(f"[VAST] Instance {inst_id} failed to start in 300 seconds.")
                except Exception as e:
                    print(f"[VAST] Failed to start stopped instance {inst_id}: {e}")
                    
        return None

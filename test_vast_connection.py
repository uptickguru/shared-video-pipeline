from vast.manager import VastManager
from config import settings

def test_connection():
    print(f"Testing Vast.ai connection...")
    vast = VastManager(settings.vast_api_key)
    try:
        # Simple list of instances (should be empty but return 200)
        result = vast.list_instances()
        print("Connection successful! API Key is valid.")
        print(f"Current instances: {len(result.get('instances', []))}")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_connection()

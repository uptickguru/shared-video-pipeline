import os
import sys
import time
import json
import subprocess
sys.path.append(os.getcwd())
from config import settings

CREDIT_LIMIT = 1.00

def get_credit():
    try:
        res = subprocess.run(['vastai', 'show', 'user', '--api-key', settings.vast_api_key, '--raw'], capture_output=True, text=True)
        data = json.loads(res.stdout)
        return float(data.get('credit', 0))
    except Exception as e:
        print(f"Error fetching credit: {e}")
        return None

def stop_all_instances():
    print("Initiating emergency shutdown of all Vast.ai instances...")
    try:
        res = subprocess.run(['vastai', 'show', 'instances', '--api-key', settings.vast_api_key, '--raw'], capture_output=True, text=True)
        instances = json.loads(res.stdout)
        for inst in instances:
            inst_id = inst.get('id')
            print(f"Stopping instance {inst_id} to preserve credits and disk state...")
            subprocess.run(['vastai', 'stop', 'instance', str(inst_id), '--api-key', settings.vast_api_key])
    except Exception as e:
        print(f"Error stopping instances: {e}")
        
    print("Emergency shutdown complete.")

def main():
    print(f"Starting Credit Monitor. Target threshold: ${CREDIT_LIMIT:.2f}")
    while True:
        current_credit = get_credit()
        if current_credit is not None:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Current Credit: ${current_credit:.2f}")
            if current_credit <= CREDIT_LIMIT:
                print(f"WARNING: Credit (${current_credit:.2f}) has dropped below the threshold (${CREDIT_LIMIT:.2f})!")
                stop_all_instances()
                print("Killing all python dispatcher scripts...")
                # Kill dispatcher process to stop new API calls
                if os.name == 'nt':
                    os.system("taskkill /F /IM python.exe")
                else:
                    os.system("pkill -f parallel_dispatcher")
                break
        time.sleep(300) # Check every 5 minutes

if __name__ == "__main__":
    main()

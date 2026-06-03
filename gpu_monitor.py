from remote_executor import RemoteExecutor
import os
import time

HOST = "ssh6.vast.ai"
PORT = 13014
KEY_PATH = os.path.join(os.getcwd(), "vast_id")

def main():
    executor = RemoteExecutor(HOST, PORT, KEY_PATH)
    if not executor.connect():
        return

    print("--- GPU Monitoring Started ---")
    try:
        while True:
            # Check nvidia-smi
            stdout = executor.execute("nvidia-smi --query-gpu=utilization.gpu,memory.used,temperature.gpu --format=csv,noheader,nounits")
            output = stdout.read().decode().strip()
            if output:
                util, mem, temp = output.split(",")
                print(f"GPU Load: {util}% | VRAM: {mem}MB | Temp: {temp}C")
            else:
                print("GPU data not available yet...")
            time.sleep(10)
    except KeyboardInterrupt:
        print("Monitoring stopped.")
    finally:
        executor.close()

if __name__ == "__main__":
    main()

from remote_executor import RemoteExecutor
import time
import os

# Configuration from previous successful rental
HOST = "ssh6.vast.ai"
PORT = 13014
KEY_PATH = os.path.join(os.getcwd(), "vast_id")

SCENES = [
    {"id": 1, "prompt": "A futuristic digital city with flowing neon gold rivers representing crypto liquidity."},
    {"id": 2, "prompt": "Close up of digital coins dropping into a glowing blue pool, creating ripples of code."},
    {"id": 3, "prompt": "A 3D bar chart rising out of a digital ocean, glowing with green energy."},
    {"id": 4, "prompt": "An abstract 3D representation of a decentralized exchange, gears made of light turning."},
    {"id": 5, "prompt": "A network of interconnected glowing nodes representing global traders providing liquidity."},
    {"id": 6, "prompt": "Final logo reveal: 'The Future of Liquidity' appears in shimmering silver over a calm digital sea."}
]

def main():
    executor = RemoteExecutor(HOST, PORT, KEY_PATH)
    if not executor.connect():
        print("Failed to connect to the machine.")
        return

    print(f"Connected to {HOST}:{PORT}. Injecting scenes...")

    for scene in SCENES:
        workflow = {
            "3": {
                "class_type": "WanVideoSampler",
                "inputs": {
                    "model": "wan2.1_t2v_1.3B_bf16.safetensors",
                    "prompt": scene['prompt'],
                    "negative_prompt": "low quality, blurry, static",
                    "steps": 30,
                    "cfg": 6.0,
                    "sample_method": "uni_pc",
                    "width": 832,
                    "height": 480,
                    "frames": 81
                }
            },
            "4": {
                "class_type": "VHS_VideoCombine",
                "inputs": {
                    "video": ["3", 0],
                    "format": "video/h264-mp4"
                }
            }
        }
        
        print(f"Submitting Scene {scene['id']}...")
        executor.submit_prompt(workflow)
        time.sleep(1)

    print("All scenes injected into the GPU's internal queue!")
    executor.close()

if __name__ == "__main__":
    main()

import requests
import time
import random
import metrics

API_BASE = "http://localhost:8000"

SAMPLE_PROMPTS = [
    "A futuristic cityscape at night with flying cars",
    "A close-up of a cybernetic eye reflecting a digital world",
    "A serene forest with neon-glowing mushrooms",
    "A space station orbiting a ringed planet",
    "A robot painting a classical landscape"
]

def submit_random_job():
    job_type = random.choice(["video", "text"])
    provider = random.choice(["wan", "kling", "openai", "gemini"])
    prompt = random.choice(SAMPLE_PROMPTS)
    priority = random.choice(["normal", "high"])
    emergency = random.choice([True, False]) if priority == "high" else False
    direct_to_vast = random.choice([True, False]) if job_type == "video" else False

    payload = {
        "job_type": job_type,
        "provider": provider,
        "engine": "test-engine",
        "prompt": prompt,
        "priority": priority,
        "emergency": emergency,
        "direct_to_vast": direct_to_vast
    }

    try:
        response = requests.post(f"{API_BASE}/jobs/", json=payload)
        response.raise_for_status()
        print(f"[SUBMIT] {job_type} ({provider}) | Priority: {priority} | Emergency: {emergency} | Status: {response.json()['status']}")
    except Exception as e:
        print(f"[ERROR] Failed to submit job: {e}")

def report_stats():
    try:
        response = requests.get(f"{API_BASE}/stats")
        response.raise_for_status()
        stats = response.json()
        print(f"\n--- Queue Stats ---")
        print(f"High Priority: {stats['high']}")
        print(f"Standard:      {stats['standard']}")
        print(f"Vast Video:    {stats['vast_video']}")
        
        # Performance Predictions
        v_size = stats['vast_video']
        if v_size > 0:
            print(f"\n--- Throughput Predictions ---")
            jph_4090 = metrics.predict_throughput("RTX_4090", "video")
            jph_a100 = metrics.predict_throughput("A100_80GB", "video")
            
            print(f"RTX 4090: ~{jph_4090:.1f} video jobs/hr")
            print(f"A100:     ~{jph_a100:.1f} video jobs/hr")
            
            est_4090 = metrics.get_full_load_estimate(v_size, "RTX_4090")
            est_a100 = metrics.get_full_load_estimate(v_size, "A100_80GB")
            print(f"Time to clear Vast queue on 4090: {est_4090:.2f} hours")
            print(f"Time to clear Vast queue on A100: {est_a100:.2f} hours")
        print("-------------------\n")
    except Exception as e:
        print(f"[ERROR] Failed to get stats: {e}")

if __name__ == "__main__":
    print("Starting Test Client...")
    for i in range(10): # Submit 10 random jobs
        submit_random_job()
        time.sleep(0.5)
    
    report_stats()

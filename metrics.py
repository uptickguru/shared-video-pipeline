# Estimates for jobs per hour based on GPU type
# These are heuristic values and should be tuned based on real-world testing.

HARDWARE_PROFILES = {
    "RTX_4090": {
        "video_generation_time_sec": 120, # 2 minutes per video
        "text_generation_time_sec": 5,
        "concurrent_jobs": 1
    },
    "A100_80GB": {
        "video_generation_time_sec": 90, # 1.5 minutes per video
        "text_generation_time_sec": 2,
        "concurrent_jobs": 4 # A100 can handle more parallel inference
    }
}

def predict_throughput(hardware: str, job_type: str = "video"):
    profile = HARDWARE_PROFILES.get(hardware)
    if not profile:
        return 0
    
    time_per_job = profile.get(f"{job_type}_generation_time_sec", 60)
    concurrent = profile.get("concurrent_jobs", 1)
    
    # Jobs per hour = (3600 / time_per_job) * concurrent
    jph = (3600 / time_per_job) * concurrent
    return jph

def get_full_load_estimate(queue_size: int, hardware: str):
    jph = predict_throughput(hardware, "video")
    if jph == 0:
        return 0
    
    hours_needed = queue_size / jph
    return hours_needed

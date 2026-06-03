import redis
from rq import Queue
from config import settings

# Initialize Redis connection
try:
    redis_conn = redis.from_url(settings.redis_url)
    redis_conn.ping() # Check if real redis is alive
except Exception:
    print("Real Redis not found. Falling back to fakeredis for local testing.")
    from fakeredis import FakeStrictRedis
    redis_conn = FakeStrictRedis()

# Create Queues
# We might have different queues based on job types or priorities
high_priority_queue = Queue("high", connection=redis_conn)
standard_queue = Queue("standard", connection=redis_conn)
video_vast_queue = Queue("vast_video", connection=redis_conn) # Holds standard video jobs until full load

def enqueue_job(job_record_id: int, job_type: str, priority: str, emergency: bool, direct_to_vast: bool):
    """
    Logic for queueing jobs based on the rules.
    """
    # Emergency bypasses holding queues and goes straight to high priority execution
    if emergency:
        # TODO: trigger vast instance spin up if not already running
        high_priority_queue.enqueue("worker.process_job", job_record_id, job_timeout=1800)
        return "enqueued_high"

    if job_type == "video":
        if direct_to_vast:
            # Goes straight to a processing queue (maybe standard or a specific direct queue)
            standard_queue.enqueue("worker.process_job", job_record_id, job_timeout=1800)
            return "enqueued_standard"
        else:
            # Hold in the vast_video queue until we get a full load
            # The worker or a cron job will monitor the size of this queue
            video_vast_queue.enqueue("worker.process_job", job_record_id, job_timeout=1800)
            
            # Check if we reached a full load
            if len(video_vast_queue) >= settings.vast_gpu_hour_threshold:
                # TODO: Trigger Vast instance spin-up
                pass
            return "held_in_vast_queue"
    else:
        # Text or other jobs
        if priority == "high":
            high_priority_queue.enqueue("worker.process_job", job_record_id, job_timeout=1800)
            return "enqueued_high"
        else:
            standard_queue.enqueue("worker.process_job", job_record_id, job_timeout=1800)
            return "enqueued_standard"

def get_queue_stats():
    """
    Returns current sizes of all queues.
    """
    return {
        "high": len(high_priority_queue),
        "standard": len(standard_queue),
        "vast_video": len(video_vast_queue)
    }

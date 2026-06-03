import time
import requests
from main import app
import uvicorn
from multiprocessing import Process
from database import init_db

def run_api():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

def submit_project():
    print("\n[START] INITIALIZING LIQUIDITY POOL PROJECT...")
    from database import SessionLocal
    from queue_manager import enqueue_job
    from models import JobRecord
    
    db = SessionLocal()
    
    scenes = [
        "A digital pool of glowing blue liquid with floating symbols for ETH and BTC, cinematic wide shot.",
        "Close-up of a robotic hand dropping a golden coin into a blue digital pool, causing golden ripples.",
        "High-tech futuristic dashboard with abstract charts and growing 'Yield' percentages.",
        "Golden translucent pipes carrying glowing blue liquid through a digital motherboard city.",
        "A network of interconnected glowing nodes representing liquidity providers across the globe.",
        "Final logo reveal: 'The Future of Liquidity' appearing over a golden sunrise background."
    ]

    for i, scene in enumerate(scenes):
        db_job = JobRecord(
            job_type="video",
            provider="wan",
            engine="Wan-2.1-14B",
            prompt=scene,
            priority="high",
            emergency=True if i == 0 else False,
            direct_to_vast=True,
            status="pending"
        )
        db.add(db_job)
        db.commit()
        db.refresh(db_job)

        queue_status = enqueue_job(
            job_record_id=db_job.id,
            job_type=db_job.job_type,
            priority=db_job.priority,
            emergency=db_job.emergency,
            direct_to_vast=db_job.direct_to_vast
        )
        print(f"[SUCCESS] Scene {i+1} Enqueued ({queue_status}): {scene[:50]}...")

    db.close()
    print("\n[FINISHED] All scenes are now in the queue.")

def run_worker():
    print("\n[WORKER] Starting local worker for fakeredis (Windows compatible)...")
    from queue_manager import redis_conn
    from rq import SimpleWorker, Queue
    q1 = Queue('high', connection=redis_conn)
    q2 = Queue('standard', connection=redis_conn)
    q3 = Queue('vast_video', connection=redis_conn)
    worker = SimpleWorker([q1, q2, q3], connection=redis_conn)
    # Burst mode processes everything currently in the queue and then exits
    worker.work(burst=True)

if __name__ == "__main__":
    init_db()
    
    # Submit the project and run worker
    try:
        submit_project()
        run_worker()
        print("\n[SUCCESS] Project processing complete.")
    except KeyboardInterrupt:
        pass
    finally:
        print("\nPipeline stopped.")

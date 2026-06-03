import redis
from rq import Queue, Worker
from queue_manager import redis_conn

print("=== Redis Connection ===")
print(f"Using connection: {redis_conn.__class__.__name__}")

# List all queues
for qname in ["high", "standard", "vast_video"]:
    q = Queue(qname, connection=redis_conn)
    print(f"Queue '{qname}': {len(q)} jobs pending")
    jobs = q.get_jobs()
    for j in jobs:
        print(f"  - Job {j.id}: status={j.get_status()} func={j.func_name}")

# List workers and active jobs
workers = Worker.all(connection=redis_conn)
print(f"\nActive workers: {len(workers)}")
for w in workers:
    job = w.get_current_job()
    print(f"  - Worker {w.name}: status={w.get_state()} active_job={job.id if job else None}")
    if job:
        print(f"    Active Job details: status={job.get_status()} func={job.func_name}")

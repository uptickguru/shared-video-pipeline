import os
from database import SessionLocal
from models import JobRecord

def inject_comparison():
    db = SessionLocal()
    
    # The badass space-to-earth St. Pete golden hour Golden Gate style macro descent prompt
    comparison_prompt = (
        "A cinematic, hyper-realistic drone shot starting from space showing Earth at night with glowing city lights, "
        "then rapidly descending through clouds into St. Petersburg, Florida at golden hour. "
        "We fly smoothly along the sparkling waterfront, passing luxury homes and boats, "
        "then circle around a modern waterfront mansion with palm trees and a glowing infinity pool. "
        "Dramatic lighting, rich colors, volumetric god rays, subtle film grain, 8K quality, "
        "shot on Arri Alexa 65 + anamorphic lenses, dynamic camera movement, masterpiece, photorealistic, breathtaking atmosphere."
    )
    
    # We will inject this into Job 361 (which is the next pending Realty scene in line!)
    target_job_id = 361
    
    job = db.query(JobRecord).filter(JobRecord.id == target_job_id).first()
    if job:
        print(f"[COMPARISON INJECTION] Found Job {target_job_id} currently in queue.")
        print(f"Old Prompt: {job.prompt[:80]}...")
        
        job.prompt = comparison_prompt
        db.commit()
        
        print(f"\n[SUCCESS] Injected Grok comparison prompt into Job {target_job_id} successfully!")
        print("The worker will fetch and render this space-to-waterfront descent next!")
    else:
        # Fallback: Find the first pending job that is not already a comparison or custom one
        pending_job = db.query(JobRecord).filter(JobRecord.status == "pending").first()
        if pending_job:
            print(f"[COMPARISON INJECTION] Target job {target_job_id} not found. Injecting into first available pending Job {pending_job.id} instead.")
            pending_job.prompt = comparison_prompt
            db.commit()
            print(f"[SUCCESS] Injected comparison prompt into Job {pending_job.id} successfully!")
        else:
            print("[ERROR] No pending jobs found in database to inject into!")
            
    db.close()

if __name__ == "__main__":
    inject_comparison()

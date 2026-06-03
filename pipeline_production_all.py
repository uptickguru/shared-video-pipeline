import time
import requests
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from database import init_db, SessionLocal
from models import JobRecord
from queue_manager import enqueue_job, redis_conn
from vast.manager import VastManager
from config import settings
from rq import SimpleWorker, Queue
import content

def submit_all_production_scenes():
    print("\n==============================================")
    print("  ENQUEUING ALL 4 PRODUCTION VIDEO PROJECTS   ")
    print("==============================================")
    
    db = SessionLocal()
    
    # 1. Gather all scenes from our core production databases + our badass challenge!
    projects = [
        {"name": "Florida_Realty", "scenes": content.REALTY_SCENES},
        {"name": "Food_Safety", "scenes": content.FOOD_SAFETY_SCENES},
        {"name": "Insurance_Crisis", "scenes": content.INSURANCE_SCENES},
        {"name": "DBAT_Agency", "scenes": content.DBAT_SCENES},
        {"name": "Badass_Challenge", "scenes": content.BADASS_SCENES}
    ]
    
    total_enqueued = 0
    import os
    
    for proj in projects:
        proj_name = proj["name"]
        scenes = proj["scenes"]
        print(f"\n📁 Processing Project: {proj_name} ({len(scenes)} scenes)")
        
        for i, scene_data in enumerate(scenes):
            prompt_text = scene_data["prompt"]
            voice_script = scene_data.get("text", "")
            
            # Idempotency Check: Check if this exact prompt was already completed and downloaded
            existing_completed = db.query(JobRecord).filter(
                JobRecord.prompt == prompt_text,
                JobRecord.status == "completed"
            ).first()
            
            if existing_completed and existing_completed.asset_path and os.path.exists(existing_completed.asset_path):
                print(f"  [-] Scene {i+1}/{len(scenes)} already successfully completed and downloaded as {os.path.basename(existing_completed.asset_path)}. Skipping!")
                continue
                
            # If not completed, we maps/enqueues it cleanly
            db_job = JobRecord(
                job_type="video",
                provider="wan",
                engine="Wan-2.1-14B",
                prompt=prompt_text,
                priority="standard",
                emergency=False,
                direct_to_vast=True,
                status="pending"
            )
            
            db.add(db_job)
            db.commit()
            db.refresh(db_job)
            
            # Enqueue the job inside our in-memory fakeredis queue
            queue_status = enqueue_job(
                job_record_id=db_job.id,
                job_type=db_job.job_type,
                priority=db_job.priority,
                emergency=db_job.emergency,
                direct_to_vast=db_job.direct_to_vast
            )
            
            total_enqueued += 1
            print(f"  [+] Scene {i+1}/{len(scenes)} enqueued as Job {db_job.id}: {prompt_text[:60]}...")
            
    db.close()
    print(f"\n Successfully enqueued {total_enqueued} total remaining scenes for tonight!")
    print("==============================================")

def run_worker_and_auto_sleep():
    print("\n Starting autonomous rendering worker loop...")
    
    q1 = Queue('high', connection=redis_conn)
    q2 = Queue('standard', connection=redis_conn)
    q3 = Queue('vast_video', connection=redis_conn)
    
    worker_instance = SimpleWorker([q1, q2, q3], connection=redis_conn)
    
    active_instance_id = None
    try:
        # Resolve active instance ID before starting work so we know what to stop later
        manager = VastManager(settings.vast_api_key)
        active_inst = manager.get_active_instance()
        if active_inst:
            active_instance_id = active_inst['id']
            print(f"[ORCHESTRATOR] Confirmed active Vast.ai instance: {active_instance_id}")
        else:
            print("[ORCHESTRATOR] Warning: No active Vast.ai instance found at boot. Worker will spin one up automatically.")
        
        # Burst mode will render and download every enqueued scene sequentially
        print("[ORCHESTRATOR] Worker rendering starts. This will run until all enqueued videos are completed.")
        worker_instance.work(burst=True)
        print("\n [SUCCESS] All enqueued videos have finished rendering and downloaded successfully!")
        
    except KeyboardInterrupt:
        print("\n Execution interrupted by user.")
    except Exception as e:
        print(f"\n Error during rendering queue execution: {e}")
    finally:
        # Put the Vast instance to sleep as soon as the queue is empty!
        print("\n Draining queue complete. Initiating auto-sleep protocol to preserve credits...")
        try:
            manager = VastManager(settings.vast_api_key)
            if not active_instance_id:
                active_inst = manager.get_active_instance()
                if active_inst:
                    active_instance_id = active_inst['id']
            
            if active_instance_id:
                print(f"[AUTO-SLEEP] Pausing active Vast instance {active_instance_id}...")
                manager.stop_instance(active_instance_id)
                print("[AUTO-SLEEP] Success! Instance is now stopped. Storage costs are capped at ~$0.015/hr.")
            else:
                print("[AUTO-SLEEP] No active Vast instance was found to stop.")
        except Exception as stop_error:
            print(f"[AUTO-SLEEP] Error occurred during auto-sleep command: {stop_error}")
            
        print("\n All processes complete. Pipeline shut down cleanly.")

if __name__ == "__main__":
    init_db()
    
    # 1. Enqueue all 40 scenes
    submit_all_production_scenes()
    
    # 2. Run them all night and auto-sleep
    run_worker_and_auto_sleep()

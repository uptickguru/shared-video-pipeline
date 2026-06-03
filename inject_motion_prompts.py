import os
from database import SessionLocal
from models import JobRecord

def inject_motion():
    db = SessionLocal()
    
    # Let's map out the dynamic, high-motion prompts for the pending Realty scenes
    realty_motion_mapping = {
        # Scene 3: Living room
        "An expansive, sun-drenched living room with minimalist white marble floors and panoramic ocean views. Soft sheer curtains blow gently in the sea breeze. 8k, architectural digest style.":
        "A slow, cinematic camera glide through an expansive living room. Volumetric sunlight streams through high glass walls, soft sheer curtains wave dynamically in a coastal sea breeze, revealing ocean waves crashing outside. 4k resolution, smooth motion.",
        
        # Scene 4: Kitchen
        "A state-of-the-art chef's kitchen featuring sleek black granite countertops, matte brass fixtures, and a massive wine cellar wall. ultra high definition, architectural photography.":
        "A slow, elegant camera sweep across a state-of-the-art chef's kitchen. Warm light reflects off polished black granite countertops, and champagne bubbles rise in tall crystal glasses in the foreground. Highly dynamic, cinematic.",
        
        # Scene 5: Master suite
        "A sprawling master bedroom suite with sliding glass doors fully open to the ocean. A massive plush white bed sits in the center. volumetric sunlight, hyper-realistic.":
        "A smooth cinematic tracking shot gliding through a luxurious master bedroom suite. Sliding glass doors are fully open to the coast, sheer white linens blow dynamically in the wind, and ocean waves crash in the background. High movement.",
        
        # Scene 6: Spa bath
        "A luxurious spa bathroom featuring a massive freestanding soaking tub positioned directly next to a window overlooking the beach. marble walls, warm golden lighting.":
        "A slow cinematic pan across a marble spa bathroom. Steam rises gently from a massive soaking tub, and water ripples slowly while warm golden light reflects off polished brass fixtures. Volumetric atmosphere.",
        
        # Scene 7: Boat dock
        "A high-end private boat dock extending into calm blue waters. A sleek white luxury yacht is tied to the wooden pier. bright sunny day, cinematic.":
        "A dynamic, low-angle tracking shot along a wooden boat dock. Crystal clear turquoise water splashes gently against the pillars, and a sleek white luxury yacht sways slowly in the foreground under bright volumetric sunlight.",
        
        # Scene 8: Twilight glow
        "A stunning aerial view of the property at twilight. The house glows warmly with strategically placed exterior lights, contrasting with the deep blue evening sky. 4k, cinematic.":
        "A breathtaking sweeping drone shot flying over a modern coastal mansion at twilight. Ocean waves roll onto the shore in the foreground, and glowing exterior pool lights pulse warmly as palm trees sway in the wind.",
        
        # Scene 9: Patio fire pit
        "A cinematic shot of a modern outdoor kitchen and massive fire pit lounge area on a beachfront patio. Luxurious outdoor furniture. warm fire glow, sunset.":
        "A cinematic low-angle tracking shot sweeping past a blazing outdoor fire pit. Intense fire sparks rise into the sunset air, and ocean waves crash nearby on the sand. Rich movement, dynamic flames.",
        
        # Scene 10: Footprints in sand
        "A beautiful cinematic tracking shot following footprints in pristine white sand leading directly up to the modern mansion's glowing glass doors. 4k, hyper-detailed.":
        "A smooth, low-angle camera sweep following footprints in pristine white sand. The wind gently blows sand particles across the dunes, leading up to a modern beachfront mansion's glowing glass doors. Rich kinetic physics."
    }
    
    # We will also polish the twilight ocean view of the Insurance Crisis scenes
    insurance_motion_mapping = {
        "A cinematic wide shot of a beautiful beach house with a massive 'FOR SALE' sign in the front yard. The sky is a beautiful but ominous orange sunset.":
        "A slow cinematic camera sweep across a beautiful beachfront house with a massive 'FOR SALE' sign in the front yard. Dark palm trees sway aggressively in the wind against an ominous, fiery red sunset sky. High movement."
    }
    
    # Merge mappings
    master_mapping = {**realty_motion_mapping, **insurance_motion_mapping}
    
    updated_count = 0
    
    # Retrieve all pending or processing jobs in the database
    jobs = db.query(JobRecord).filter(JobRecord.status == "pending").all()
    
    for job in jobs:
        if job.prompt in master_mapping:
            old_prompt = job.prompt
            new_prompt = master_mapping[old_prompt]
            job.prompt = new_prompt
            db.commit()
            updated_count += 1
            print(f"[MOTION INJECTION] Updated Job {job.id} -> Added dynamic movement to prompt!")
            
    db.close()
    print(f"\n[FINISHED] Injected cinematic kinetic motion into {updated_count} pending jobs successfully.")

if __name__ == "__main__":
    inject_motion()

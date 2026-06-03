import os
import sys
import json
from database import SessionLocal
from models import JobRecord

def load_api_keys():
    """
    Attempts to load API keys from environment, .env, or social_config.json
    """
    keys = {
        "gemini": os.environ.get("GEMINI_API_KEY"),
        "anthropic": os.environ.get("ANTHROPIC_API_KEY")
    }
    
    # Try social_config.json
    if os.path.exists("social_config.json"):
        try:
            with open("social_config.json", "r") as f:
                cfg = json.load(f)
                if cfg.get("GEMINI_API_KEY") and cfg.get("GEMINI_API_KEY") != "YOUR_GEMINI_API_KEY":
                    keys["gemini"] = cfg.get("GEMINI_API_KEY")
                if cfg.get("ANTHROPIC_API_KEY"):
                    keys["anthropic"] = cfg.get("ANTHROPIC_API_KEY")
        except Exception:
            pass
            
    # Try .env file
    if os.path.exists(".env"):
        try:
            with open(".env", "r") as f:
                for line in f:
                    if "=" in line:
                        k, v = line.strip().split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k == "GEMINI_API_KEY" and v != "YOUR_GEMINI_API_KEY":
                            keys["gemini"] = v
                        elif k == "ANTHROPIC_API_KEY":
                            keys["anthropic"] = v
        except Exception:
            pass
            
    return keys

def expand_prompt_gemini(api_key: str, simple_prompt: str) -> str:
    """
    Calls Google Gemini 1.5 Pro to creatively expand the prompt.
    """
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    system_instruction = (
        "You are an elite AI Film Director and Cinematographer. "
        "Expand the given simple video prompt into a hyper-kinetic, cinematic masterpiece prompt "
        "for the Wan-2.1 Text-to-Video model. "
        "Focus heavily on physical movement, lighting, lens details, and dynamic action: "
        "1. Active Physical Motion: splashing, swirling, shattering, exploding, or morphing. "
        "2. Dynamic Camera: FPV drone dives, rapid 360-degree orbits, or dramatic dolly sweeps. "
        "3. Cinematic Lighting: Volumetric god rays, anamorphic lens flares, rich color contrast. "
        "4. Lens keywords: Arri Alexa 65, anamorphic lenses, 8k quality, cinematic realism. "
        "Do NOT write any preamble, intro, or conversation. Output ONLY the raw expanded prompt, max 65 words."
    )
    
    prompt = f"{system_instruction}\n\nSimple prompt to expand: {simple_prompt}"
    response = model.generate_content(prompt)
    return response.text.strip()

def expand_prompt_anthropic(api_key: str, simple_prompt: str) -> str:
    """
    Calls Anthropic Claude 3.5 Sonnet to creatively expand the prompt.
    """
    # Import here to avoid crash if not installed
    import requests
    
    system_instruction = (
        "You are an elite AI Film Director and Cinematographer. "
        "Expand the given simple video prompt into a hyper-kinetic, cinematic masterpiece prompt "
        "for the Wan-2.1 Text-to-Video model. "
        "Focus heavily on physical movement, lighting, lens details, and dynamic action: "
        "1. Active Physical Motion: splashing, swirling, shattering, exploding, or morphing. "
        "2. Dynamic Camera: FPV drone dives, rapid 360-degree orbits, or dramatic dolly sweeps. "
        "3. Cinematic Lighting: Volumetric god rays, anamorphic lens flares, rich color contrast. "
        "4. Lens keywords: Arri Alexa 65, anamorphic lenses, 8k quality, cinematic realism. "
        "Do NOT write any preamble, intro, or conversation. Output ONLY the raw expanded prompt, max 65 words."
    )
    
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    payload = {
        "model": "claude-3-5-sonnet-latest",
        "max_tokens": 150,
        "temperature": 0.7,
        "system": system_instruction,
        "messages": [
            {"role": "user", "content": f"Expand this: {simple_prompt}"}
        ]
    }
    
    response = requests.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()["content"][0]["text"].strip()
    else:
        raise Exception(f"Anthropic API error: {response.text}")

def get_cinematic_prompt(simple_prompt: str) -> str:
    """
    Loads keys and routes prompt to the best available LLM. Falls back to pre-defined rules if offline.
    """
    keys = load_api_keys()
    
    # 1. Prefer Claude for maximum artistic soul
    if keys.get("anthropic"):
        try:
            print("[PROMPT DIRECTOR] Invoking Claude 3.5 Sonnet for creative burst...")
            return expand_prompt_anthropic(keys["anthropic"], simple_prompt)
        except Exception as e:
            print(f"[WARNING] Claude call failed, trying Gemini fallback: {e}")
            
    # 2. Fall back to Gemini 1.5 Pro
    if keys.get("gemini"):
        try:
            print("[PROMPT DIRECTOR] Invoking Gemini 1.5 Pro for creative burst...")
            return expand_prompt_gemini(keys["gemini"], simple_prompt)
        except Exception as e:
            print(f"[WARNING] Gemini call failed: {e}")
            
    # 3. Offline/Local Rule-based expansion fallback
    print("[PROMPT DIRECTOR] No API keys configured. Using local cinematic rule injector.")
    cinematic_suffix = (
        "Volumetric lighting, rich color contrast, anamorphic lens flare, "
        "Arri Alexa 65 camera, dynamic motion, photorealistic masterpiece, 8K quality, cinematic atmosphere."
    )
    return f"{simple_prompt}. {cinematic_suffix}"

def juice_database_job(job_id: int):
    """
    Queries a specific database job by ID, expands its prompt using AI, and saves it.
    """
    db = SessionLocal()
    job = db.query(JobRecord).filter(JobRecord.id == job_id).first()
    if not job:
        print(f"[ERROR] Job {job_id} not found in database.")
        db.close()
        return
        
    print(f"\n[PROMPT DIRECTOR] Juicing Job {job_id}")
    print(f"   Original: {job.prompt}")
    
    try:
        expanded = get_cinematic_prompt(job.prompt)
        job.prompt = expanded
        db.commit()
        print(f"[SUCCESS] Injected juiced prompt: {expanded}")
    except Exception as e:
        print(f"[ERROR] Failed to juice prompt: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # If passed an integer, juice that database job ID
        try:
            job_id = int(sys.argv[1])
            juice_database_job(job_id)
        except ValueError:
            # Otherwise, just expand the text passed in
            expanded = get_cinematic_prompt(" ".join(sys.argv[1:]))
            print(f"\nExpanded Prompt:\n{expanded}")
    else:
        print("\nUsage:")
        print("  1. Test expansion on simple text:")
        print('     python prompt_director.py "A modern mansion on the beach"')
        print("  2. Expand and update a live database job by ID:")
        print("     python prompt_director.py [job_id]")

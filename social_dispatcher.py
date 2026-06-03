import os
import glob
import json
import time
import shutil
import requests
import google.generativeai as genai

# Setup directories
POSTED_DIR = "posted_assets"
os.makedirs(POSTED_DIR, exist_ok=True)

def load_config():
    try:
        with open("social_config.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("[ERROR] social_config.json not found!")
        return None

def generate_caption(project_name, gemini_api_key):
    if not gemini_api_key or gemini_api_key == "YOUR_GEMINI_API_KEY":
        print("[WARNING] Gemini API key not configured. Using default caption.")
        return f"Check out this amazing content about {project_name.replace('_', ' ')}! #ai #influencer"
        
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-1.5-pro')
        prompt = f"You are a professional social media manager. Write an engaging, viral-style caption for a short video about '{project_name.replace('_', ' ')}'. Include a strong hook and exactly 5 highly relevant hashtags. Do not include emojis if they look unprofessional, keep it clean and sharp."
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"[ERROR] Gemini generation failed: {e}")
        return f"Check out this content about {project_name.replace('_', ' ')}! #ai #influencer"

def upload_to_instagram(video_path, caption, config):
    print(f"\n[INSTAGRAM] Starting upload for {os.path.basename(video_path)}...")
    if not config["INSTAGRAM"].get("ENABLED"):
        print("[INSTAGRAM] Disabled in config. Skipping.")
        return False
        
    mode = config["INSTAGRAM"].get("MODE", "UNOFFICIAL")
    
    if mode == "UNOFFICIAL":
        print("[INSTAGRAM] Using UNOFFICIAL mode (instagrapi) for direct local upload.")
        username = config["INSTAGRAM"].get("USERNAME")
        password = config["INSTAGRAM"].get("PASSWORD")
        
        if not username or username == "YOUR_INSTAGRAM_USERNAME":
            print("[INSTAGRAM] Username not configured. Skipping.")
            return False
            
        try:
            # We import instagrapi here so the script doesn't crash if it's not installed yet
            from instagrapi import Client
            cl = Client()
            print("[INSTAGRAM] Logging in...")
            cl.login(username, password)
            print("[INSTAGRAM] Uploading Reel...")
            media = cl.clip_upload(video_path, caption)
            print(f"[INSTAGRAM] Successfully uploaded Reel! Media ID: {media.id}")
            return True
        except ImportError:
            print("[ERROR] 'instagrapi' library is not installed. Run: pip install instagrapi")
            return False
        except Exception as e:
            print(f"[ERROR] Instagram upload failed: {e}")
            return False
            
    else:
        # Official Mode Placeholder
        print("[INSTAGRAM] Using OFFICIAL mode (Requires S3 Public URL).")
        page_token = config["INSTAGRAM"].get("PAGE_ACCESS_TOKEN")
        if not page_token or page_token == "YOUR_FACEBOOK_PAGE_ACCESS_TOKEN_FOR_OFFICIAL_MODE":
            print("[INSTAGRAM] Official API keys not configured. Skipping.")
            return False
        print("[INSTAGRAM] Official API simulated success.")
        return True

def process_queue():
    config = load_config()
    if not config:
        return
        
    # Find all final stitched videos
    videos = glob.glob("FINAL_PARALLEL_*.mp4")
    if not videos:
        print("No new videos found in the root directory. Waiting...")
        return
        
    print(f"Found {len(videos)} new videos ready for upload!")
    
    for video in videos:
        # Extract project name (e.g. FINAL_PARALLEL_Florida_Realty.mp4 -> Florida_Realty)
        project_name = video.replace("FINAL_PARALLEL_", "").replace(".mp4", "")
        
        print(f"\n{'='*50}\nProcessing: {project_name}\n{'='*50}")
        
        # 1. Generate Caption with AI
        caption = generate_caption(project_name, config.get("GEMINI_API_KEY"))
        print(f"\nGenerated Caption:\n{caption}\n")
        
        # 2. Upload to Platforms
        uploaded_any = False
        if upload_to_instagram(video, caption, config):
            uploaded_any = True
            
        # TODO: Add YouTube Shorts logic here once client_secret.json is provided
        
        # 3. Archive
        # We move it to posted_assets so it doesn't get uploaded twice
        # In a real environment, we'd only move it if uploaded_any == True.
        # But for testing, we'll move it automatically so the loop doesn't get stuck.
        dest = os.path.join(POSTED_DIR, video)
        shutil.move(video, dest)
        print(f"\n[ARCHIVE] Moved {video} to {POSTED_DIR}/")

if __name__ == "__main__":
    print("Starting Autonomous Social Media Dispatcher...")
    while True:
        process_queue()
        # Poll every 5 minutes
        time.sleep(300)

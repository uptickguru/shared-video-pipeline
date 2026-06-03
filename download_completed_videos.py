import paramiko
import os
import re

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print("Connecting to GPU server to fetch completed videos...")
c.connect('ssh8.vast.ai', port=14476, username='root', key_filename='vast_id', timeout=15)

sftp = c.open_sftp()
remote_dir = "/ComfyUI/output"
local_dir = "output_videos"

os.makedirs(local_dir, exist_ok=True)

try:
    files = sftp.listdir(remote_dir)
    print(f"Files found in remote output directory: {len(files)}")
    
    # Download any mp4 file
    for filename in files:
        if filename.endswith(".mp4"):
            # Extract the scene/job number if present
            match = re.search(r'influencer_scene_(\d+)', filename)
            if match:
                job_num = match.group(1)
                # Map to corresponding job folder name pattern
                local_name = f"job_{job_num}_{filename}"
            else:
                local_name = filename
                
            local_path = os.path.join(local_dir, local_name)
            remote_path = remote_dir + '/' + filename
            
            if not os.path.exists(local_path) or os.path.getsize(local_path) == 0:
                print(f"Downloading {filename} -> {local_name}...")
                sftp.get(remote_path, local_path)
                print(f"Successfully downloaded {local_name}!")
            else:
                print(f"Skipping {filename} (already exists locally).")
finally:
    sftp.close()
    c.close()
print("Done checking and downloading completed videos!")

import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh8.vast.ai', port=14476, username='root', key_filename='vast_id')

print("Killing old ComfyUI...")
client.exec_command('pkill -f "python /ComfyUI/main.py"')
import time
time.sleep(2)

print("Restarting ComfyUI...")
client.exec_command('nohup /opt/venv/bin/python /ComfyUI/main.py --listen 0.0.0.0 --port 8188 > /ComfyUI/comfy.log 2>&1 &')
print("Done!")

import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh8.vast.ai', port=14476, username='root', key_filename='vast_id')

print("Cloning Official Wan nodes...")
stdin, stdout, stderr = client.exec_command('git clone https://github.com/Comfy-Org/Wan_2.1_ComfyUI_Node /ComfyUI/custom_nodes/Wan_2.1_ComfyUI_Node')
print(stdout.read().decode())
print(stderr.read().decode())

print("Killing old ComfyUI...")
stdin, stdout, stderr = client.exec_command('pkill -f "python /ComfyUI/main.py"')
print(stdout.read().decode())

print("Restarting ComfyUI...")
client.exec_command('nohup /opt/venv/bin/python /ComfyUI/main.py --listen 0.0.0.0 --port 8188 > /ComfyUI/comfy.log 2>&1 &')
print("Done!")

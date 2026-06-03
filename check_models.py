import paramiko
import json

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('ssh8.vast.ai', port=14476, username='root', key_filename='vast_id', timeout=15)

stdin, stdout, stderr = c.exec_command("curl -s http://localhost:8188/object_info")
data = json.loads(stdout.read().decode())

print("UNET models:", data['UNETLoader']['input']['required']['unet_name'][0])
print("CLIP models:", data['CLIPLoader']['input']['required']['clip_name'][0][:5])
print("VAE models:", data['VAELoader']['input']['required']['vae_name'][0][:5])

c.close()

import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh8.vast.ai', port=14476, username='root', key_filename='vast_id')

stdin, stdout, stderr = client.exec_command('grep -rn "WanEmptyLatentImage" /ComfyUI')
print(stdout.read().decode())

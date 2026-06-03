import paramiko
import json

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh8.vast.ai', port=14476, username='root', key_filename='vast_id')

stdin, stdout, stderr = client.exec_command('curl -s http://localhost:8188/object_info')
data = stdout.read().decode()
try:
    obj = json.loads(data)
    for node_name in obj.keys():
        if "wan" in node_name.lower():
            print(node_name)
except Exception as e:
    print("Error parsing json:", e)
    print(data[:500])

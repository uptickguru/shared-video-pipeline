import paramiko
import sys
import io

# Force utf-8 stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh8.vast.ai', port=14476, username='root', key_filename='vast_id')

stdin, stdout, stderr = client.exec_command('cat /tmp/dl1.log')
print("DL1:", stdout.read().decode('utf-8', errors='ignore'))

stdin, stdout, stderr = client.exec_command('cat /tmp/dl2.log')
print("DL2:", stdout.read().decode('utf-8', errors='ignore'))

stdin, stdout, stderr = client.exec_command('cat /tmp/dl3.log')
print("DL3:", stdout.read().decode('utf-8', errors='ignore'))

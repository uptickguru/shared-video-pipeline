import paramiko
import json

def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect('ssh8.vast.ai', port=14476, username='root', key_filename='vast_id')
    
    stdin, stdout, stderr = c.exec_command("curl -s http://localhost:8188/object_info")
    data = json.loads(stdout.read().decode('utf-8'))
    
    node = 'WanVideoEmptyEmbeds'
    if node in data:
        print(f"=== {node} ===")
        print("REQUIRED:")
        print(json.dumps(data[node]['input'].get('required', {}), indent=2))
        print("OPTIONAL:")
        print(json.dumps(data[node]['input'].get('optional', {}), indent=2))
        print("RETURN_TYPES:")
        print(data[node]['output'])
    else:
        print(f"{node} not found")
        
    c.close()

if __name__ == '__main__':
    main()

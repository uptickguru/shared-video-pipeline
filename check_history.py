import paramiko, json, sys

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('ssh8.vast.ai', port=14476, username='root', key_filename='vast_id', timeout=15)

# Get ALL history
stdin, stdout, stderr = c.exec_command("curl -s http://localhost:8188/history")
data = json.loads(stdout.read().decode())

for pid, entry in data.items():
    status = entry.get("status", {})
    status_str = status.get("status_str", "unknown")
    outputs = entry.get("outputs", {})
    if status_str == "success":
        print(f"\nSUCCESS: {pid}")
        for nid, out in outputs.items():
            print(f"  Node {nid}: {json.dumps(out, indent=2)[:500]}")
    else:
        print(f"ERROR: {pid}")

c.close()

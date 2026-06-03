import paramiko
import time

def main():
    print("Connecting to ssh8.vast.ai:14476...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('ssh8.vast.ai', port=14476, username='root', key_filename='vast_id')

    print("Cleaning up stale processes...")
    # Kill robust_setup, huggingface-cli, and any running comfyui instances
    commands = [
        "pkill -9 -f robust_setup",
        "pkill -9 -f huggingface-cli",
        "pkill -9 -f main.py",
        "fuser -k -9 8188/tcp 2>/dev/null || true",
        "kill -9 $(lsof -t -i:8188) 2>/dev/null || true"
    ]
    for cmd in commands:
        stdin, stdout, stderr = client.exec_command(cmd)
        stdout.channel.recv_exit_status() # Wait for completion

    print("Checking process list after cleanup:")
    stdin, stdout, stderr = client.exec_command("ps aux")
    print(stdout.read().decode())

    print("Clean up finished successfully!")
    client.close()

if __name__ == "__main__":
    main()

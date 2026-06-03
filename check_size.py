import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('ssh8.vast.ai', port=14476, username='root', key_filename='vast_id')

stdin, stdout, stderr = client.exec_command('ls -lah /ComfyUI/models/diffusion_models/wan2.1-t2v-1.3B-bf16.safetensors /ComfyUI/models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors /ComfyUI/models/vae/wan_2.1_vae.safetensors 2>/dev/null || echo "Still downloading"')
print("STDOUT:", stdout.read().decode())

stdin, stdout, stderr = client.exec_command('du -sh /ComfyUI/models/diffusion_models/.cache /ComfyUI/models/text_encoders/.cache 2>/dev/null')
print("CACHE SIZES:\n", stdout.read().decode())

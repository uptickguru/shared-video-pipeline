#!/bin/bash
# init_studio.sh
# Provider-agnostic initialization script for the AI Influencer / Video Pipeline Studio
# This script downloads all required multi-gigabyte models to the standard ComfyUI directories.

echo "========================================="
echo "Initializing Production Studio Node"
echo "========================================="

# Ensure directories exist
mkdir -p /ComfyUI/models/unet
mkdir -p /ComfyUI/models/clip
mkdir -p /ComfyUI/models/vae
mkdir -p /ComfyUI/models/checkpoints
mkdir -p /ComfyUI/models/ipadapter
mkdir -p /ComfyUI/models/clip_vision
mkdir -p /ComfyUI/models/loras
mkdir -p /ComfyUI/models/insightface/models/buffalo_l

echo "1. Downloading Wan-2.1 Video Models..."
huggingface-cli download Kijai/WanVideo_comfy Wan2_1-T2V-1_3B_bf16.safetensors --local-dir /ComfyUI/models/diffusion_models
huggingface-cli download Kijai/WanVideo_comfy umt5-xxl-enc-fp8_e4m3fn.safetensors --local-dir /ComfyUI/models/text_encoders
huggingface-cli download Kijai/WanVideo_comfy Wan2_1_VAE_bf16.safetensors --local-dir /ComfyUI/models/vae

echo "2. Downloading Consistent Character (SDXL/FaceID) Models..."
python3 -c "
from huggingface_hub import hf_hub_download
hf_hub_download(repo_id='RunDiffusion/Juggernaut-XL-v9', filename='Juggernaut-XL_v9_RunDiffusion.safetensors', local_dir='/ComfyUI/models/checkpoints')
hf_hub_download(repo_id='h94/IP-Adapter-FaceID', filename='ip-adapter-faceid-plusv2_sdxl.bin', local_dir='/ComfyUI/models/ipadapter')
hf_hub_download(repo_id='h94/IP-Adapter', filename='models/image_encoder/model.safetensors', local_dir='/ComfyUI/models/clip_vision')
hf_hub_download(repo_id='h94/IP-Adapter-FaceID', filename='ip-adapter-faceid-plusv2_sdxl_lora.safetensors', local_dir='/ComfyUI/models/loras')
"

echo "3. Downloading InsightFace Dependencies..."
wget -nc 'https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip' -O /tmp/buffalo_l.zip 
unzip -n /tmp/buffalo_l.zip -d /ComfyUI/models/insightface/models/buffalo_l/

echo "========================================="
echo "Studio Initialization Complete!"
echo "========================================="

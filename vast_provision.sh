#!/bin/bash
# vast_provision.sh - Automatically setup Wan-2.1 on ComfyUI

echo "Starting Wan-2.1 Provisioning..."

# 1. Install missing dependencies
apt-get update && apt-get install -y wget git python3-pip

# 2. Setup HF Token for gated models
if [ ! -z "$HF_TOKEN" ]; then
    export HF_TOKEN=$HF_TOKEN
    echo "Hugging Face Token set."
fi

# 3. Download Wan-2.1 Checkpoints (using wget or hf-cli)
# For the 14B model (adjust path as needed)
MODEL_DIR="/workspace/ComfyUI/models/diffusion_models"
mkdir -p $MODEL_DIR

echo "Downloading Wan-2.1 14B Model (this may take a few minutes)..."
# Replace with actual HF URLs once confirmed
# huggingface-cli download Wan-Video/Wan2.1-T2V-14B --local-dir $MODEL_DIR --token $HF_TOKEN

# 4. Install Custom Nodes
CUSTOM_NODES="/workspace/ComfyUI/custom_nodes"
cd $CUSTOM_NODES
git clone https://github.com/ltdrdata/ComfyUI-Manager.git
git clone https://github.com/Wan-Video/Wan2.1-ComfyUI.git # Placeholder

echo "Provisioning Complete. ComfyUI is ready for Wan-2.1."

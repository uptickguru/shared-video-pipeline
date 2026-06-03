import os
import subprocess
import sys
import imageio_ffmpeg

def get_ffmpeg_path():
    try:
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        if os.path.exists(ffmpeg_path):
            return ffmpeg_path
    except Exception as e:
        print(f"[WARNING] Could not locate imageio-ffmpeg executable: {e}")
    
    # Fallback to system ffmpeg
    return "ffmpeg"

def process_video(input_path: str, output_path: str, saturation: float = 0.80, contrast: float = 0.95, brightness: float = -0.01, grain_strength: int = 8, vignette_angle: float = 0.35):
    """
    Applies high-end cinematic color correction, contrast calibration, organic film grain, and lens vignettes to a video.
    """
    ffmpeg_exe = get_ffmpeg_path()
    
    # Ensure directories exist
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    
    # FFMPEG Filter Chain:
    # 1. eq = saturation, contrast, brightness calibration
    # 2. noise = alls (strength), allf=t (temporal moving noise) + u (uniform distribution) for realistic film grain
    # 3. vignette = lens shader
    filter_chain = (
        f"eq=saturation={saturation}:contrast={contrast}:brightness={brightness},"
        f"noise=alls={grain_strength}:allf=t+u,"
        f"vignette=angle={vignette_angle}"
    )
    
    cmd = [
        ffmpeg_exe,
        "-y",               # Overwrite output if exists
        "-i", input_path,   # Input file
        "-vf", filter_chain,# Video filters
        "-c:v", "libx264",  # High-compatibility H.264 video codec
        "-preset", "medium",# Good balance between encoding speed and quality
        "-crf", "18",       # Visual lossless quality level (18 is standard cinema master CRF)
        "-c:a", "copy",     # Direct audio copy (no re-encoding needed)
        output_path
    ]
    
    print(f"\n[POST-PROCESSOR] Processing: {os.path.basename(input_path)}")
    print(f"   [Filters] Saturation: {saturation} | Contrast: {contrast} | Grain: {grain_strength} | Vignette: {vignette_angle}")
    
    try:
        # Run subprocess and capture output
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            print(f"[SUCCESS] Saved cinematic master to: {output_path}")
            return True
        else:
            print(f"[FFMPEG ERROR] Process failed with exit code {result.returncode}")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"[ERROR] Failed to run FFMPEG: {e}")
        return False

def process_directory(input_dir: str, output_dir: str):
    """
    Processes all MP4 videos in a directory.
    """
    if not os.path.exists(input_dir):
        print(f"[ERROR] Input directory '{input_dir}' does not exist.")
        return
        
    os.makedirs(output_dir, exist_ok=True)
    files = [f for f in os.listdir(input_dir) if f.endswith(".mp4") and not f.startswith("cinematic_")]
    
    if not files:
        print(f"[INFO] No mp4 files found in '{input_dir}' to process.")
        return
        
    print(f"[POST-PROCESSOR] Starting batch process of {len(files)} videos...")
    success_count = 0
    
    for filename in files:
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, f"cinematic_{filename}")
        if process_video(input_path, output_path):
            success_count += 1
            
    print(f"\n[BATCH COMPLETE] Successfully processed {success_count}/{len(files)} videos!")

if __name__ == "__main__":
    # If a specific file is passed, process it, otherwise process the output directory
    if len(sys.argv) > 2:
        process_video(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 2:
        # Single file to same directory
        infile = sys.argv[1]
        name, ext = os.path.splitext(infile)
        outfile = f"{name}_cinematic{ext}"
        process_video(infile, outfile)
    else:
        # Default: batch process the completed output_videos directory
        default_in = os.path.join(os.getcwd(), "output_videos")
        default_out = os.path.join(os.getcwd(), "output_videos_cinematic")
        process_directory(default_in, default_out)

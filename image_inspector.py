# image_inspector.py
"""
DBAT Programmatic Image Quality Inspector
Combines FFMPEG's perceptual blur detection and Pillow's HSV/Luminance analysis
to grade image quality, contrast, and realistic saturation levels.
"""

import subprocess
import os
import sys
import imageio_ffmpeg
from PIL import Image

def analyze_blur(image_path: str) -> float:
    """
    Runs FFMPEG blurdetect to calculate the no-reference perceptual blur score.
    Higher values mean more blur (less sharp). Sharp photo assets typically average <12.0.
    """
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg_exe,
        "-i", image_path,
        "-vf", "blurdetect",
        "-f", "null",
        "-"
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # Parse the blur mean from stderr (e.g. "[Parsed_blurdetect_0...] blur mean: 11.166")
        for line in res.stderr.splitlines():
            if "blur mean:" in line:
                parts = line.split("blur mean:")
                return float(parts[1].strip())
    except Exception as e:
        print(f"[WARNING] Could not calculate blur via FFMPEG: {e}")
    return 0.0

def inspect_image(image_path: str):
    """
    Performs rich pixel-level color, exposure, and sharpness checks.
    """
    if not os.path.exists(image_path):
        print(f"[ERROR] Image path does not exist: {image_path}")
        return

    print(f"\n==================================================")
    print(f"[GRADERS REPORT] {os.path.basename(image_path)}")
    print(f"==================================================")

    # 1. Open and load image
    img = Image.open(image_path)
    if img.mode != "RGB":
        img = img.convert("RGB")
    
    width, height = img.size
    total_pixels = width * height
    print(f"Dimensions: {width}x{height} pixels ({total_pixels:,} total)")

    # 2. HSV Color Analysis
    hsv_img = img.convert("HSV")
    h, s, v = hsv_img.split()
    
    # Saturation Statistics (0-255)
    s_data = list(s.getdata())
    avg_sat = sum(s_data) / total_pixels / 255.0 * 100.0  # converted to %
    max_sat = max(s_data) / 255.0 * 100.0
    min_sat = min(s_data) / 255.0 * 100.0
    
    # Brightness/Value Statistics (0-255)
    v_data = list(v.getdata())
    avg_val = sum(v_data) / total_pixels / 255.0 * 100.0  # converted to %
    max_val = max(v_data) / 255.0 * 100.0
    min_val = min(v_data) / 255.0 * 100.0

    # Clipped pixel checks
    pure_blacks = sum(1 for px in v_data if px == 0)
    pure_whites = sum(1 for px in v_data if px == 255)
    black_clip_pct = (pure_blacks / total_pixels) * 100.0
    white_clip_pct = (pure_whites / total_pixels) * 100.0

    # 3. Sharpness/Blur from FFMPEG
    blur_score = analyze_blur(image_path)

    # 4. Grading logic
    saturation_status = "PASS (Cinematic/Realistic)"
    if avg_sat > 70.0:
        saturation_status = "FAILED (Over-saturated Neon CGI)"
    elif avg_sat < 20.0:
        saturation_status = "FAILED (Under-saturated/Washy)"
    elif avg_sat > 55.0:
        saturation_status = "WARNING (Slightly High Saturation)"

    exposure_status = "PASS (Optimal Exposure)"
    if avg_val < 25.0:
        exposure_status = "WARNING (Very Dark/Underexposed)"
    elif avg_val > 80.0:
        exposure_status = "WARNING (Very Bright/Overexposed)"
    
    if white_clip_pct > 5.0:
        exposure_status = "FAILED (Blown Out Highlights/Clipped)"

    blur_status = "PASS (Sharp / High-Detail)"
    if blur_score > 18.0:
        blur_status = "FAILED (Extremely Blurry/Out-of-focus)"
    elif blur_score > 12.0:
        blur_status = "WARNING (Soft / Moderate Detail)"

    # Print statistical grades
    print(f"\n[RAW METRICS]:")
    print(f"  * Avg Saturation:    {avg_sat:.2f}% (Range: {min_sat:.1f}% to {max_sat:.1f}%)")
    print(f"  * Avg Brightness:    {avg_val:.2f}% (Range: {min_val:.1f}% to {max_val:.1f}%)")
    print(f"  * Clipped Shadows:   {black_clip_pct:.2f}% (Pure Black pixels)")
    print(f"  * Clipped Highlights:  {white_clip_pct:.2f}% (Pure White pixels)")
    print(f"  * Perceptual Blur:   {blur_score:.3f}")

    print(f"\n[QUALITY DECISIONS]:")
    print(f"  * Saturation Grade:  {saturation_status}")
    print(f"  * Exposure Grade:    {exposure_status}")
    print(f"  * Sharpness Grade:   {blur_status}")

    # Overall Verdict
    if "FAILED" in [saturation_status, exposure_status, blur_status]:
        print(f"\n[OVERALL VERDICT] REJECT (Aesthetic quality is sub-standard!)")
        return False
    else:
        print(f"\n[OVERALL VERDICT] ACCEPT (Realism calibration looks excellent!)")
        return True

if __name__ == "__main__":
    target = "reference_images/flux_reference_image.png"
    if len(sys.argv) > 1:
        target = sys.argv[1]
    inspect_image(target)

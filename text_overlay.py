import os
import subprocess
import sys
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

def get_ffmpeg_path():
    try:
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        if os.path.exists(ffmpeg_path):
            return ffmpeg_path
    except Exception as e:
        print(f"[WARNING] Could not locate imageio-ffmpeg executable: {e}")
    return "ffmpeg"

def get_system_font(size: int):
    """
    Attempts to load a clean premium Windows font, falling back to basic font.
    """
    font_paths = [
        "C:\\Windows\\Fonts\\Georgia.ttf",
        "C:\\Windows\\Fonts\\Arial.ttf",
        "C:\\Windows\\Fonts\\Trebuc.ttf",
        "C:\\Windows\\Fonts\\Calibri.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

def create_text_graphic(title_text: str, subtitle_text: str = "", width: int = 1280, height: int = 720, out_path: str = "_temp_overlay.png"):
    """
    Programmatically designs a gorgeous, transparent corporate title graphic with drop shadows.
    """
    # Create transparent RGBA canvas
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    title_font = get_system_font(int(height * 0.075)) # 7.5% of height
    sub_font = get_system_font(int(height * 0.038))   # 3.8% of height
    
    # Calculate positions
    # 1. Main Title
    title_w = draw.textlength(title_text, font=title_font)
    title_x = (width - title_w) // 2
    title_y = int(height * 0.40) # Position in upper half
    
    # Draw drop shadow for readability against light backgrounds
    shadow_offset = 3
    draw.text((title_x + shadow_offset, title_y + shadow_offset), title_text, fill=(0, 0, 0, 180), font=title_font)
    # Draw pristine white title
    draw.text((title_x, title_y), title_text, fill=(255, 255, 255, 255), font=title_font)
    
    # 2. Subtitle
    if subtitle_text:
        sub_w = draw.textlength(subtitle_text, font=sub_font)
        sub_x = (width - sub_w) // 2
        sub_y = int(height * 0.52) # Below main title
        
        # Subtitle drop shadow
        draw.text((sub_x + 2, sub_y + 2), subtitle_text, fill=(0, 0, 0, 160), font=sub_font)
        # Pristine white/silver subtitle
        draw.text((sub_x, sub_y), subtitle_text, fill=(230, 230, 230, 255), font=sub_font)
        
    img.save(out_path)
    return out_path

def burn_overlay(video_path: str, overlay_img_path: str, output_path: str, fade_in_start: float = 0.5, fade_in_duration: float = 0.5, fade_out_start: float = 4.0, fade_out_duration: float = 0.5):
    """
    Blends the transparent overlay PNG onto the video with elegant, hardware-accelerated fade transitions.
    """
    ffmpeg_exe = get_ffmpeg_path()
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    
    # FFMPEG Complex Filter:
    # 1. Take the overlay image input [1:v]
    # 2. Apply a temporal fade-in on alpha channel
    # 3. Apply a temporal fade-out on alpha channel
    # 4. Blend centered over [0:v] (main video input)
    filter_complex = (
        f"[1:v]fade=in:st={fade_in_start}:d={fade_in_duration}:alpha=1,"
        f"fade=out:st={fade_out_start}:d={fade_out_duration}:alpha=1[logo];"
        f"[0:v][logo]overlay=x=(W-w)/2:y=(H-h)/2"
    )
    
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", video_path,
        "-i", overlay_img_path,
        "-filter_complex", filter_complex,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-c:a", "copy",
        output_path
    ]
    
    print(f"\n[OVERLAY ENGINE] Burning logo/graphic onto: {os.path.basename(video_path)}")
    print(f"   [Transitions] Fade In: {fade_in_start}s | Fade Out: {fade_out_start}s")
    
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            print(f"[SUCCESS] Graphics burned successfully! Saved to: {output_path}")
            return True
        else:
            print(f"[FFMPEG ERROR] Overlay failed with exit code {result.returncode}")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"[ERROR] Failed to run FFMPEG overlay: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("\nUsage:")
        print("  1. Custom text burn-in:")
        print('     python text_overlay.py [video_in] [video_out] "Title Text" ["Subtitle Text"]')
        print("  2. Existing PNG logo overlay:")
        print('     python text_overlay.py [video_in] [video_out] [logo_path.png]')
        sys.exit(1)
        
    infile = sys.argv[1]
    outfile = sys.argv[2]
    
    # Scenario A: User provided a direct PNG file path
    if sys.argv[3].lower().endswith(".png"):
        logo_path = sys.argv[3]
        if not os.path.exists(logo_path):
            print(f"[ERROR] Logo file '{logo_path}' not found.")
            sys.exit(1)
        burn_overlay(infile, logo_path, outfile)
    else:
        # Scenario B: Programmatically design a beautiful title card
        title = sys.argv[3]
        subtitle = sys.argv[4] if len(sys.argv) > 4 else ""
        
        # Auto-generate temporary transparent text image
        temp_png = create_text_graphic(title, subtitle)
        
        try:
            # Burn it
            burn_overlay(infile, temp_png, outfile)
        finally:
            # Clean up temp file
            if os.path.exists(temp_png):
                os.remove(temp_png)

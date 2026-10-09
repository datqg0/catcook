"""
Generates polished 8-frame Bartender animation sequence:
1. Rock-solid anchor lock (zero jitter across all 8 frames)
2. 8 distinct frames showing full Japanese hard shake cycle
3. Updates individual sheet, master spritesheet, JSON atlas, and animated GIF
"""
import os
import json
from collections import deque
from PIL import Image
import numpy as np

BRAIN_DIR = r"C:\Users\cp\.gemini\antigravity-ide\brain\8a339ccb-11f3-4a78-8cfc-ebd42468c328"

FRAME_SOURCES = [
    # Frame 0: Ready pose at chest, calm focused expression •‿•, frost mist
    os.path.join(BRAIN_DIR, "cat_bartender_return_prep_1791529738042.jpg"),
    # Frame 1: First diagonal pump, focused eyes, ice water beads
    os.path.join(BRAIN_DIR, "cat_bartender_shaker_1791527271368.jpg"),
    # Frame 2: Mid-motion diagonal thrust upward, wide speed arcs, mouth open
    os.path.join(BRAIN_DIR, "cat_bartender_thrust_up_1791529651244.jpg"),
    # Frame 3: Apex Climax! High right-up, open smiling cheer \(=^o^=)/, ice crystals & golden stars
    os.path.join(BRAIN_DIR, "cat_bartender_tilt_happy_1791527298601.jpg"),
    # Frame 4: Descending from apex, happy curved eyes ^‿^, drifting stars and blushing cheeks
    os.path.join(BRAIN_DIR, "cat_bartender_descend_apex_1791529682495.jpg"),
    # Frame 5: Hard snap-down impact at chest, vertical speed blur, determined eyes >‿<
    os.path.join(BRAIN_DIR, "cat_bartender_shake_center_1791527320196.jpg"),
    # Frame 6: Barista flair level, charming gentle smile, beginning of wink, aroma heart
    os.path.join(BRAIN_DIR, "cat_bartender_level_flair_1791529710386.jpg"),
    # Frame 7: Full barista wink ^_~, floating coffee beans, boba pearl & pink heart
    os.path.join(BRAIN_DIR, "cat_bartender_tilt_left_1791527344173.jpg"),
]

OUT_DIR = os.path.join("assets", "animations", "bartender")
os.makedirs(OUT_DIR, exist_ok=True)
SHEETS_DIR = os.path.join("assets", "animations", "sheets")
os.makedirs(SHEETS_DIR, exist_ok=True)

def segment_white_bg(img_path):
    im = Image.open(img_path).convert("RGB")
    arr = np.array(im)
    h_a, w_a, _ = arr.shape
    is_bg = (arr[..., 0] > 240) & (arr[..., 1] > 240) & (arr[..., 2] > 240)
    visited = np.zeros((h_a, w_a), dtype=bool)
    bg_mask = np.zeros((h_a, w_a), dtype=bool)
    q = deque()
    for x in range(w_a):
        if is_bg[0, x]: q.append((0, x)); visited[0, x] = True
        if is_bg[h_a-1, x]: q.append((h_a-1, x)); visited[h_a-1, x] = True
    for y in range(h_a):
        if is_bg[y, 0]: q.append((y, 0)); visited[y, 0] = True
        if is_bg[y, w_a-1]: q.append((y, w_a-1)); visited[y, w_a-1] = True
    while q:
        y, x = q.popleft()
        bg_mask[y, x] = True
        for ny, nx in [(y-1, x), (y+1, x), (y, x-1), (y, x+1)]:
            if 0 <= ny < h_a and 0 <= nx < w_a:
                if not visited[ny, nx] and is_bg[ny, nx]:
                    visited[ny, nx] = True
                    q.append((ny, nx))
    alpha = np.where(bg_mask, 0, 255).astype(np.uint8)
    rgba = np.dstack([arr, alpha])
    return Image.fromarray(rgba, "RGBA")

def main():
    target_canvas_w, target_canvas_h = 344, 768
    scale = 546.0 / 1029.0
    raw_nx, raw_ny = 461, 524
    target_nx, target_ny = 222, 302
    paste_x = int(target_nx - raw_nx * scale)
    paste_y = int(target_ny - raw_ny * scale)

    processed_frames = []

    for idx, path in enumerate(FRAME_SOURCES):
        print(f"Processing Frame {idx}: {os.path.basename(path)}")
        seg = segment_white_bg(path)
        sw = int(seg.size[0] * scale)
        sh = int(seg.size[1] * scale)
        seg_scaled = seg.resize((sw, sh), Image.Resampling.LANCZOS)

        canvas = Image.new("RGBA", (target_canvas_w, target_canvas_h), (0, 0, 0, 0))
        canvas.paste(seg_scaled, (paste_x, paste_y), seg_scaled)

        out_path = os.path.join(OUT_DIR, f"frame_{idx}.png")
        canvas.save(out_path)
        print(f"  -> Saved {out_path}: {canvas.size}, bbox={canvas.getbbox()}")
        processed_frames.append(canvas)

    # 1. Save 8-frame individual sheet (2752 x 768)
    sheet_w = target_canvas_w * len(processed_frames)
    sheet_h = target_canvas_h
    sheet = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))
    for i, f in enumerate(processed_frames):
        sheet.paste(f, (i * target_canvas_w, 0), f)
    
    sheet_path = os.path.join(SHEETS_DIR, "chef_bartender_sheet.png")
    sheet.save(sheet_path)
    print(f"Saved {sheet_path}: {sheet.size}")

    # 2. Update Master Spritesheet (2752 x 7680)
    master_img_path = os.path.join(SHEETS_DIR, "chef_master_spritesheet.png")
    master_json_path = os.path.join(SHEETS_DIR, "chef_master_spritesheet.json")
    
    master_img = Image.open(master_img_path)
    # Bartender is row 9 (starting at y=6912)
    new_master = Image.new("RGBA", (2752, 7680), (0, 0, 0, 0))
    # Keep rows 0-8 from existing master
    row_0_8 = master_img.crop((0, 0, 2752, 6912))
    new_master.paste(row_0_8, (0, 0))
    # Paste updated 8-frame bartender sheet at row 9
    new_master.paste(sheet, (0, 6912))
    new_master.save(master_img_path)
    print(f"Saved {master_img_path}: {new_master.size}")

    # 3. Update master JSON atlas
    with open(master_json_path, "r") as f:
        atlas = json.load(f)

    # Clear old bartender frames
    old_keys = [k for k in atlas["frames"].keys() if "bartender" in k]
    for k in old_keys:
        del atlas["frames"][k]

    # Add 8 bartender frames
    for i in range(len(processed_frames)):
        k = f"chef_bartender_{i}"
        atlas["frames"][k] = {
            "frame": {"x": i * 344, "y": 6912, "w": 344, "h": 768},
            "rotated": False,
            "trimmed": False,
            "spriteSourceSize": {"x": 0, "y": 0, "w": 344, "h": 768},
            "sourceSize": {"w": 344, "h": 768}
        }

    atlas["meta"]["size"]["w"] = 2752
    atlas["meta"]["size"]["h"] = 7680
    with open(master_json_path, "w") as f:
        json.dump(atlas, f, indent=2)
    print(f"Updated {master_json_path}: Total {len(atlas['frames'])} frames")

    # 4. Generate Slower, Polished Animated GIF (200ms per frame = 1.6s loop)
    gif_path = os.path.join("assets", "animations", "preview_bartender.gif")
    processed_frames[0].save(
        gif_path,
        save_all=True,
        append_images=processed_frames[1:],
        duration=200, # 200ms per frame = 5.0 fps, smooth and chill
        loop=0,
        disposal=2
    )
    print(f"Saved {gif_path}: 8 frames @ 200ms")

if __name__ == "__main__":
    main()

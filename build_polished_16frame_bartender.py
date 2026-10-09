"""
Generates polished 16-frame Bartender animation sequence:
1. Rock-solid anchor lock (zero jitter across all 16 frames)
2. 16 distinct, fluid frames showing full Japanese hard shake cycle & barista flair
3. Slower, relaxing lofi rhythm (~4.0s full cycle)
4. Updates individual sheet (5504x768), master spritesheet (2752x9984), JSON atlas (61 frames), and animated GIF
"""
import os
import json
from collections import deque
from PIL import Image
import numpy as np

BRAIN_DIR = r"C:\Users\cp\.gemini\antigravity-ide\brain\8a339ccb-11f3-4a78-8cfc-ebd42468c328"
OUT_DIR = os.path.join("assets", "animations", "bartender")
SHEETS_DIR = os.path.join("assets", "animations", "sheets")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(SHEETS_DIR, exist_ok=True)

KEY_FILES = [
    os.path.join(BRAIN_DIR, "cat_bartender_return_prep_1791529738042.jpg"),    # Key 0
    os.path.join(BRAIN_DIR, "cat_bartender_shaker_1791527271368.jpg"),         # Key 1
    os.path.join(BRAIN_DIR, "cat_bartender_thrust_up_1791529651244.jpg"),      # Key 2
    os.path.join(BRAIN_DIR, "cat_bartender_tilt_happy_1791527298601.jpg"),     # Key 3
    os.path.join(BRAIN_DIR, "cat_bartender_descend_apex_1791529682495.jpg"),   # Key 4
    os.path.join(BRAIN_DIR, "cat_bartender_shake_center_1791527320196.jpg"),    # Key 5
    os.path.join(BRAIN_DIR, "cat_bartender_tilt_viewer_left_1791529417860.jpg"), # Key 6
    os.path.join(BRAIN_DIR, "cat_bartender_level_flair_1791529710386.jpg"),    # Key 7
    os.path.join(BRAIN_DIR, "cat_bartender_tilt_left_1791527344173.jpg"),      # Key 8
]

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

    print("Segmenting and anchoring 9 keyframes...")
    raw_keys = []
    for idx, p in enumerate(KEY_FILES):
        seg = segment_white_bg(p)
        sw = int(seg.size[0] * scale)
        sh = int(seg.size[1] * scale)
        seg_scaled = seg.resize((sw, sh), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (target_canvas_w, target_canvas_h), (0, 0, 0, 0))
        canvas.paste(seg_scaled, (paste_x, paste_y), seg_scaled)
        raw_keys.append(canvas)

    # Clean face blends for specific transitions:
    # Frame 15 (8 -> 0): keep crisp open eye from key 0
    f15 = Image.blend(raw_keys[8], raw_keys[0], 0.5)
    eye_clean = raw_keys[0].crop((235, 350, 280, 400))
    f15.paste(eye_clean, (235, 350), eye_clean)

    # Frame 9 (4 -> 5): keep determined face crisp from key 5
    f9 = Image.blend(raw_keys[4], raw_keys[5], 0.5)
    face_5 = raw_keys[5].crop((140, 340, 275, 430))
    f9.paste(face_5, (140, 340), face_5)

    # Frame 11 (5 -> 6): keep crisp face from key 6
    f11 = Image.blend(raw_keys[5], raw_keys[6], 0.5)
    face_6 = raw_keys[6].crop((140, 340, 275, 430))
    f11.paste(face_6, (140, 340), face_6)

    frames_16 = [
        raw_keys[0],                                 # 0: Ready prep pose
        Image.blend(raw_keys[0], raw_keys[1], 0.5), # 1: In-between (Prep -> Pump 1)
        raw_keys[1],                                 # 2: First diagonal pump
        Image.blend(raw_keys[1], raw_keys[2], 0.5), # 3: In-between (Pump 1 -> Thrust)
        raw_keys[2],                                 # 4: Thrust up diagonal
        Image.blend(raw_keys[2], raw_keys[3], 0.5), # 5: In-between (Thrust -> Apex)
        raw_keys[3],                                 # 6: Apex Climax (smiling cheer)
        Image.blend(raw_keys[3], raw_keys[4], 0.5), # 7: In-between (Apex -> Descend)
        raw_keys[4],                                 # 8: Descending from apex
        f9,                                          # 9: In-between (Descend -> Rebound)
        raw_keys[5],                                 # 10: Snap impact at chest
        f11,                                         # 11: In-between (Impact -> Cross pump)
        raw_keys[6],                                 # 12: Cross pump flair
        raw_keys[7],                                 # 13: Level barista flair
        raw_keys[8],                                 # 14: Barista wink
        f15,                                         # 15: Return prep transition
    ]

    # 1. Save all 16 frames
    for i, f in enumerate(frames_16):
        fpath = os.path.join(OUT_DIR, f"frame_{i}.png")
        f.save(fpath)
    print(f"Saved 16 standalone frames in {OUT_DIR}")

    # 2. Save individual sheet (5504 x 768)
    sheet_w = target_canvas_w * len(frames_16)
    sheet_h = target_canvas_h
    sheet = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))
    for i, f in enumerate(frames_16):
        sheet.paste(f, (i * target_canvas_w, 0), f)
    sheet_path = os.path.join(SHEETS_DIR, "chef_bartender_sheet.png")
    sheet.save(sheet_path)
    print(f"Saved {sheet_path}: {sheet.size}")

    # 3. Save animated GIF (duration=260ms per frame, full cycle = ~4.16s, smooth & relaxed)
    gif_path = os.path.join("assets", "animations", "preview_bartender.gif")
    frames_16[0].save(
        gif_path,
        save_all=True,
        append_images=frames_16[1:],
        duration=260, # 260ms = ~3.85 fps, relaxing lofi rhythm
        loop=0,
        disposal=2
    )
    print(f"Saved {gif_path}")

    # 4. Update master spritesheet: 13 rows (2752 x 9984)
    master_img_path = os.path.join(SHEETS_DIR, "chef_master_spritesheet.png")
    master_json_path = os.path.join(SHEETS_DIR, "chef_master_spritesheet.json")

    old_master = Image.open(master_img_path)
    new_master = Image.new("RGBA", (2752, 9984), (0, 0, 0, 0))

    # Rows 0-8 from old master
    new_master.paste(old_master.crop((0, 0, 2752, 6912)), (0, 0))

    # Row 9: bartender 0..7
    for i in range(8):
        new_master.paste(frames_16[i], (i * 344, 6912), frames_16[i])

    # Row 10: bartender 8..15
    for i in range(8):
        new_master.paste(frames_16[8 + i], (i * 344, 7680), frames_16[8 + i])

    # Row 11: bake (from old master row 10, y=7680)
    bake_row = old_master.crop((0, 7680, 2752, 8448))
    new_master.paste(bake_row, (0, 8448))

    # Row 12: serve (from old master row 11, y=8448)
    serve_row = old_master.crop((0, 8448, 2752, 9216))
    new_master.paste(serve_row, (0, 9216))

    new_master.save(master_img_path)
    print(f"Saved {master_img_path}: {new_master.size}")

    # 5. Update master JSON atlas
    with open(master_json_path, "r") as f:
        atlas = json.load(f)

    # Clear any old bartender frames
    old_b_keys = [k for k in atlas["frames"].keys() if "bartender" in k]
    for k in old_b_keys:
        del atlas["frames"][k]

    # Rebuild bartender frames (16 frames)
    for i in range(16):
        k = f"chef_bartender_{i}"
        row_y = 6912 if i < 8 else 7680
        col_x = (i % 8) * 344
        atlas["frames"][k] = {
            "frame": {"x": col_x, "y": row_y, "w": 344, "h": 768},
            "rotated": False,
            "trimmed": False,
            "spriteSourceSize": {"x": 0, "y": 0, "w": 344, "h": 768},
            "sourceSize": {"w": 344, "h": 768}
        }

    # Shift bake frames to y=8448
    for i in range(4):
        k = f"chef_bake_{i}"
        if k in atlas["frames"]:
            atlas["frames"][k]["frame"]["y"] = 8448

    # Shift serve frames to y=9216
    for i in range(4):
        k = f"chef_serve_{i}"
        if k in atlas["frames"]:
            atlas["frames"][k]["frame"]["y"] = 9216

    atlas["meta"]["size"]["w"] = 2752
    atlas["meta"]["size"]["h"] = 9984

    with open(master_json_path, "w") as f:
        json.dump(atlas, f, indent=2)

    total_frames = len(atlas["frames"])
    print(f"Updated {master_json_path}: Total {total_frames} frames in atlas.")

if __name__ == "__main__":
    main()

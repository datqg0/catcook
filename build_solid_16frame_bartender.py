"""
Generates 100% Solid 16-Frame Bartender Animation:
1. ZERO motion blur / ghost trails / double bottles ('không làm hiệu ứng bóng mờ').
2. The bottle physically moves across distinct positions, heights, and angles ('cho cái chai thực sự chuyển động').
3. Strictly locked anchor at (222, 302) for 0px jitter across all frames.
4. Updates individual sheet, master spritesheet, atlas, and preview GIF.
"""
import os
import json
from collections import deque
from PIL import Image, ImageDraw
import numpy as np

BRAIN_DIR = r"C:\Users\cp\.gemini\antigravity-ide\brain\8a339ccb-11f3-4a78-8cfc-ebd42468c328"
OUT_DIR = os.path.join("assets", "animations", "bartender")
SHEETS_DIR = os.path.join("assets", "animations", "sheets")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(SHEETS_DIR, exist_ok=True)

# 8 crisp, 100% solid keyframes with ZERO ghost bottles
CLEAN_KEYS = [
    "cat_bartender_return_prep_1791529738042.jpg",     # 0: Prep pose (steady center-chest grip)
    "cat_bartender_shaker_1791527271368.jpg",          # 1: Right pump (shifts right +5°)
    "cat_bartender_thrust_up_1791529651244.jpg",        # 2: High upward thrust (shoots up +42°)
    "cat_bartender_descend_apex_1791529682495.jpg",    # 3: Descend drop (drops down to 28°)
    "cat_bartender_tilt_happy_1791527298601.jpg",      # 4: Happy ice climax (sparkle stars & ice crystals)
    "cat_bartender_tilt_viewer_left_1791529417860.jpg", # 5: Determined hard shake (powers through at 38°)
    "cat_bartender_tilt_left_1791527344173.jpg",       # 6: Winking flair shake (^_~ with sparkles)
    "cat_bartender_level_flair_1791529710386.jpg",     # 7: Settle flair (smooth level return)
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
    target_nx, target_ny = 222, 302
    raw_nx, raw_ny = 461, 524
    paste_x = int(target_nx - raw_nx * scale)
    paste_y = int(target_ny - raw_ny * scale)

    print("Segmenting and anchoring 8 solid keyframes...")
    loaded = []
    for k in CLEAN_KEYS:
        seg = segment_white_bg(os.path.join(BRAIN_DIR, k))
        sw = int(seg.size[0] * scale)
        sh = int(seg.size[1] * scale)
        scaled = seg.resize((sw, sh), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (target_canvas_w, target_canvas_h), (0, 0, 0, 0))
        canvas.paste(scaled, (paste_x, paste_y), scaled)
        loaded.append(canvas)

    # Clean sparkle for frame 15
    f15_sparkle = loaded[7].copy()
    draw = ImageDraw.Draw(f15_sparkle)
    def draw_star(d, cx, cy, r, col):
        d.polygon([(cx, cy-r), (cx+r*0.4, cy), (cx, cy+r), (cx-r*0.4, cy)], fill=col)
        d.polygon([(cx-r, cy), (cx, cy-r*0.4), (cx+r, cy), (cx, cy+r*0.4)], fill=col)
    draw_star(draw, 275, 435, 12, (255, 255, 255, 240))
    draw_star(draw, 275, 435, 6, (255, 220, 100, 255))

    # 16 Solid Frames: 2 energetic, rhythmic shake beats per cycle
    # ZERO ghosting, ZERO opacity blend, 100% solid bottle moving physically across each frame!
    frames_16 = [
        loaded[0],     # 0: Prep pose (steady grip)
        loaded[1],     # 1: Right pump (bottle shifts right)
        loaded[2],     # 2: High upward thrust (bottle shoots up above shoulder!)
        loaded[3],     # 3: Descend drop (bottle snaps down)
        loaded[4],     # 4: Happy ice climax (ice crystals pop!)
        loaded[5],     # 5: Determined power shake (powers through at 38°)
        loaded[6],     # 6: Winking flair shake (^_~ with stars)
        loaded[7],     # 7: Settle flair
        loaded[0],     # 8: Prep pose 2
        loaded[1],     # 9: Right pump 2
        loaded[2],     # 10: High upward thrust 2!
        loaded[3],     # 11: Descend drop 2
        loaded[4],     # 12: Happy ice climax 2
        loaded[5],     # 13: Determined power shake 2
        loaded[6],     # 14: Winking flair shake 2
        f15_sparkle,   # 15: Settle finish with gold sparkle star!
    ]

    print("Saving 16 individual solid PNG frames...")
    for i, fr in enumerate(frames_16):
        out_p = os.path.join(OUT_DIR, f"frame_{i}.png")
        fr.save(out_p, "PNG")

    # Save animated GIF preview (180ms per frame, smooth ~2.88s cycle)
    gif_path = os.path.join("assets", "animations", "preview_bartender.gif")
    frames_16[0].save(
        gif_path,
        save_all=True,
        append_images=frames_16[1:],
        duration=180,
        loop=0,
        disposal=2
    )
    print(f"Saved animated preview GIF: {gif_path}")

    # Build individual sheet (5504 x 768)
    sheet_single = Image.new("RGBA", (target_canvas_w * 16, target_canvas_h), (0, 0, 0, 0))
    for i, fr in enumerate(frames_16):
        sheet_single.paste(fr, (i * target_canvas_w, 0), fr)
    single_p = os.path.join(SHEETS_DIR, "chef_bartender_sheet.png")
    sheet_single.save(single_p, "PNG")
    print(f"Saved individual sheet: {single_p} ({sheet_single.size})")

    # Update Master Spritesheet (2752 x 9984) and JSON Atlas
    master_w = 2752
    master_h = 9984
    master_img = Image.new("RGBA", (master_w, master_h), (0, 0, 0, 0))

    actions_before = ["idle", "walk", "run", "jump", "attack", "toss", "stir", "chop", "cheer"]
    actions_after = [("bake", 11), ("serve", 12)]

    anim_base = os.path.join("assets", "animations")
    for row_idx, act in enumerate(actions_before):
        act_dir = os.path.join(anim_base, act)
        num_frames = 5 if act == "stir" else 4
        for f_idx in range(num_frames):
            fp = os.path.join(act_dir, f"frame_{f_idx}.png")
            if os.path.exists(fp):
                fr = Image.open(fp)
                master_img.paste(fr, (f_idx * target_canvas_w, row_idx * target_canvas_h), fr)

    # Paste bartender (16 frames across rows 9 and 10)
    for f_idx, fr in enumerate(frames_16):
        if f_idx < 8:
            master_img.paste(fr, (f_idx * target_canvas_w, 9 * target_canvas_h), fr)
        else:
            master_img.paste(fr, ((f_idx - 8) * target_canvas_w, 10 * target_canvas_h), fr)

    for act, row_idx in actions_after:
        act_dir = os.path.join(anim_base, act)
        for f_idx in range(4):
            fp = os.path.join(act_dir, f"frame_{f_idx}.png")
            if os.path.exists(fp):
                fr = Image.open(fp)
                master_img.paste(fr, (f_idx * target_canvas_w, row_idx * target_canvas_h), fr)

    master_p = os.path.join(SHEETS_DIR, "chef_master_spritesheet.png")
    master_img.save(master_p, "PNG")
    print(f"Saved master spritesheet: {master_p} ({master_img.size})")

    # Generate JSON Atlas
    atlas = {
        "meta": {
            "image": "chef_master_spritesheet.png",
            "size": {"w": master_w, "h": master_h},
            "frame_width": target_canvas_w,
            "frame_height": target_canvas_h,
            "anchor": {"x": target_nx, "y": target_ny}
        },
        "frames": {}
    }

    all_actions = actions_before + ["bartender"] + [a for a, _ in actions_after]
    for act in all_actions:
        if act == "stir":
            count = 5
        elif act == "bartender":
            count = 16
        else:
            count = 4

        for f_idx in range(count):
            if act in actions_before:
                r = actions_before.index(act)
                c = f_idx
            elif act == "bartender":
                r = 9 if f_idx < 8 else 10
                c = f_idx if f_idx < 8 else (f_idx - 8)
            else:
                r = 11 if act == "bake" else 12
                c = f_idx

            atlas["frames"][f"{act}_{f_idx}"] = {
                "frame": {
                    "x": c * target_canvas_w,
                    "y": r * target_canvas_h,
                    "w": target_canvas_w,
                    "h": target_canvas_h
                },
                "anchor": {"x": target_nx, "y": target_ny}
            }

    atlas_p = os.path.join(SHEETS_DIR, "chef_master_spritesheet.json")
    with open(atlas_p, "w", encoding="utf-8") as f:
        json.dump(atlas, f, indent=2)
    print(f"Saved JSON atlas: {atlas_p} ({len(atlas['frames'])} frames)")

if __name__ == "__main__":
    main()

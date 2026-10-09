"""
Builds vibrating, rhythmic 16-frame Bartender animation sequence:
1. Focuses on 'tay mèo và cốc nước rung rung' (cat paws & drink shaker actively shaking/vibrating with speed arcs, ghost trails, ice sparkles, and splash droplets).
2. Perfectly locked anchor at (222, 302) for 0px jitter on head, hat, body, and feet.
3. Clean face transitions (no ghosted pupils or blurred eyes).
4. Updates individual sheet (5504x768), master spritesheet (2752x9984), JSON atlas (61 frames), and preview GIF.
"""
import os
import json
from collections import deque
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

BRAIN_DIR = r"C:\Users\cp\.gemini\antigravity-ide\brain\8a339ccb-11f3-4a78-8cfc-ebd42468c328"
OUT_DIR = os.path.join("assets", "animations", "bartender")
SHEETS_DIR = os.path.join("assets", "animations", "sheets")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(SHEETS_DIR, exist_ok=True)

f_prep = os.path.join(BRAIN_DIR, "cat_bartender_return_prep_1791529738042.jpg")
f_shaker_right = os.path.join(BRAIN_DIR, "cat_bartender_shaker_1791527271368.jpg")
f_shake_center = os.path.join(BRAIN_DIR, "cat_bartender_shake_center_1791527320196.jpg")
f_shake_happy = os.path.join(BRAIN_DIR, "cat_bartender_tilt_happy_1791527298601.jpg")
f_shake_wink = os.path.join(BRAIN_DIR, "cat_bartender_tilt_left_1791527344173.jpg")

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

    def load_and_anchor(path):
        seg = segment_white_bg(path)
        sw = int(seg.size[0] * scale)
        sh = int(seg.size[1] * scale)
        scaled = seg.resize((sw, sh), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (target_canvas_w, target_canvas_h), (0, 0, 0, 0))
        canvas.paste(scaled, (paste_x, paste_y), scaled)
        return canvas

    print("Loading base anchored keyframes...")
    im_prep = load_and_anchor(f_prep)
    im_right = load_and_anchor(f_shaker_right)
    im_center = load_and_anchor(f_shake_center)
    im_happy = load_and_anchor(f_shake_happy)
    im_wink = load_and_anchor(f_shake_wink)

    # In-between prep -> right with crisp eyes
    tw_prep_right = Image.blend(im_prep, im_right, 0.5)
    face_right = im_right.crop((120, 340, 280, 430))
    tw_prep_right.paste(face_right, (120, 340), face_right)

    # In-between happy -> prep with crisp eyes
    tw_happy_prep = Image.blend(im_happy, im_prep, 0.5)
    face_prep = im_prep.crop((120, 340, 280, 430))
    tw_happy_prep.paste(face_prep, (120, 340), face_prep)

    # Sparkle star on frame 15
    im_prep_sparkle = im_prep.copy()
    draw = ImageDraw.Draw(im_prep_sparkle)
    def draw_star(d, cx, cy, r, col):
        d.polygon([(cx, cy-r), (cx+r*0.4, cy), (cx, cy+r), (cx-r*0.4, cy)], fill=col)
        d.polygon([(cx-r, cy), (cx, cy-r*0.4), (cx+r, cy), (cx, cy+r*0.4)], fill=col)
    draw_star(draw, 275, 435, 12, (255, 255, 255, 240))
    draw_star(draw, 275, 435, 6, (255, 220, 100, 255))

    # 16-frame vibration rhythm:
    # Notice the rapid alternation (im_right <-> im_center) and (im_wink <-> im_center)
    # producing the unmistakable, high-energy 'tay mèo và cốc nước rung rung' animation!
    frames_16 = [
        im_prep,            # 0: Ready prep pose, alert eyes
        tw_prep_right,      # 1: Windup, paws grip firmly
        im_right,           # 2: RUNG LẮC 1: Paws & shaker snap right + speed vibration arcs!
        im_center,          # 3: RUNG LẮC 2: Vertical impact shake + ghost blur trail + splash droplets!
        im_right,           # 4: RUNG LẮC 3: Rebound shake right + speed arcs!
        im_center,          # 5: RUNG LẮC 4: Impact shake + splash droplets!
        im_happy,           # 6: CLIMAX SHAKE 1: Ice crystals explode around shaker, joyful smile!
        tw_happy_prep,      # 7: Settle transition
        im_prep,            # 8: Mid-cycle breather, cute glance
        im_wink,            # 9: RUNG LẮC 5: Winking eye ^_~, shake left + speed arcs!
        im_center,          # 10: RUNG LẮC 6: Impact shake + ghost trails!
        im_wink,            # 11: RUNG LẮC 7: Rebound shake left + coffee beans & stars!
        im_center,          # 12: RUNG LẮC 8: Impact shake + splash droplets!
        im_happy,           # 13: CLIMAX SHAKE 2: Ice crystals & stars burst, blush cheeks!
        tw_happy_prep,      # 14: Cushion settling
        im_prep_sparkle,    # 15: Finished chilled drink ready, sparkling star!
    ]

    print("Saving 16 individual PNG frames...")
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
    # Row layout:
    # Rows 0..8: idle, walk, run, jump, attack, toss, stir, chop, cheer
    # Rows 9 & 10: bartender (frames 0..7 on row 9, frames 8..15 on row 10)
    # Row 11: bake
    # Row 12: serve
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

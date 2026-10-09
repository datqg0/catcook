import os
import math
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = r"c:\Users\cp\Downloads\New folder (12)"
ANIM_DIR = os.path.join(BASE_DIR, "assets", "animations")
SERVE_DIR = os.path.join(ANIM_DIR, "serve")
SHEETS_DIR = os.path.join(ANIM_DIR, "sheets")
os.makedirs(SERVE_DIR, exist_ok=True)
os.makedirs(SHEETS_DIR, exist_ok=True)

idle_base = Image.open(os.path.join(ANIM_DIR, "idle", "frame_0.png"))
w, h = idle_base.size

skin = (249, 232, 212, 255)
ink = (42, 32, 28, 255)

def draw_star(draw, cx, cy, ro, ri, fill):
    pts = []
    for i in range(8):
        ang = i * math.pi / 4 - math.pi / 2
        r = ro if i % 2 == 0 else ri
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    draw.polygon(pts, fill=fill)

def draw_diamond(draw, cx, cy, r, fill):
    draw.polygon([(cx, cy - r), (cx + r*0.6, cy), (cx, cy + r), (cx - r*0.6, cy)], fill=fill)

def apply_happy_eyes(img):
    out = img.copy()
    draw = ImageDraw.Draw(out)
    # Fill pupils
    draw.ellipse([124, 375, 161, 420], fill=skin)
    draw.ellipse([225, 375, 266, 420], fill=skin)
    # Arcs ^‿^
    draw.arc([125, 376, 161, 412], start=200, end=340, fill=ink, width=4)
    draw.arc([227, 376, 263, 412], start=200, end=340, fill=ink, width=4)
    draw.line([(127, 395), (121, 398)], fill=ink, width=3)
    draw.line([(261, 395), (267, 398)], fill=ink, width=3)
    # Pink blushing cheeks
    draw.ellipse([98, 400, 134, 422], fill=(255, 120, 150, 160))
    draw.ellipse([252, 400, 288, 422], fill=(255, 120, 150, 160))
    return out

def apply_blink_eyes(img):
    out = img.copy()
    draw = ImageDraw.Draw(out)
    draw.ellipse([124, 375, 161, 420], fill=skin)
    draw.ellipse([225, 375, 266, 420], fill=skin)
    draw.arc([125, 386, 161, 416], start=20, end=160, fill=ink, width=4)
    draw.arc([227, 386, 263, 416], start=20, end=160, fill=ink, width=4)
    return out

# --- FRAME 0: Welcoming Attentive Pose ---
frame0 = idle_base.copy()
f0_draw = ImageDraw.Draw(frame0)
f0_draw.ellipse([100, 402, 132, 420], fill=(255, 130, 150, 120))
f0_draw.ellipse([254, 402, 286, 420], fill=(255, 130, 150, 120))

# --- FRAME 1: Gentle Bow Incline (Dip 3px) with Resting Blink ---
frame1 = Image.new("RGBA", (w, h), (0, 0, 0, 0))
frame1.paste(idle_base, (0, 3), idle_base)
frame1 = apply_blink_eyes(frame1)

# Subtle warm hospitality glow around chef
glow1 = Image.new("RGBA", (w, h), (0, 0, 0, 0))
g1_draw = ImageDraw.Draw(glow1)
g1_draw.ellipse([100, 360, 290, 560], fill=(255, 220, 120, 40))
glow1 = glow1.filter(ImageFilter.GaussianBlur(12))
frame1 = Image.alpha_composite(frame1, glow1)

# --- FRAME 2: Full Respectful Hospitality Bow (Dip 7px) "Mời Bạn Dùng Bữa!" ---
frame2 = Image.new("RGBA", (w, h), (0, 0, 0, 0))
frame2.paste(idle_base, (0, 7), idle_base)
frame2 = apply_happy_eyes(frame2)

# Golden hospitality stars & sparkles
fx2 = Image.new("RGBA", (w, h), (0, 0, 0, 0))
fx2_draw = ImageDraw.Draw(fx2)
draw_star(fx2_draw, 70, 430, 9, 3, (255, 225, 90, 240))
draw_star(fx2_draw, 280, 425, 10, 4, (255, 220, 80, 250))
draw_diamond(fx2_draw, 295, 470, 6, (255, 255, 180, 230))
draw_diamond(fx2_draw, 55, 465, 5, (255, 255, 180, 220))
fx2_glow = fx2.filter(ImageFilter.GaussianBlur(3))
frame2 = Image.alpha_composite(frame2, fx2_glow)
frame2 = Image.alpha_composite(frame2, fx2)

# --- FRAME 3: Rising with Warm Proud Smile ---
frame3 = Image.new("RGBA", (w, h), (0, 0, 0, 0))
frame3.paste(idle_base, (0, 2), idle_base)
f3_draw = ImageDraw.Draw(frame3)
# Bright blushing cheeks
f3_draw.ellipse([98, 400, 134, 422], fill=(255, 120, 150, 160))
f3_draw.ellipse([252, 400, 288, 422], fill=(255, 120, 150, 160))
# Tiny sparkle
fx3 = Image.new("RGBA", (w, h), (0, 0, 0, 0))
fx3_draw = ImageDraw.Draw(fx3)
draw_star(fx3_draw, 285, 410, 8, 3, (255, 235, 120, 230))
fx3_glow = fx3.filter(ImageFilter.GaussianBlur(2))
frame3 = Image.alpha_composite(frame3, fx3_glow)
frame3 = Image.alpha_composite(frame3, fx3)

# Save 4 frames
serve_frames = [frame0, frame1, frame2, frame3]
for i, f in enumerate(serve_frames):
    out_p = os.path.join(SERVE_DIR, f"frame_{i}.png")
    f.save(out_p)
    print(f"Saved {out_p}: {f.size}, bbox={f.getbbox()}")

# Save preview GIF
gif_p = os.path.join(ANIM_DIR, "preview_serve.gif")
frame0.save(
    gif_p,
    save_all=True,
    append_images=serve_frames[1:],
    duration=280,
    loop=0,
    disposal=2
)
print(f"Saved {gif_p}")

# Save chef_serve_sheet.png (1376 x 768)
serve_sheet = Image.new("RGBA", (w * len(serve_frames), h), (0, 0, 0, 0))
for i, f in enumerate(serve_frames):
    serve_sheet.paste(f, (i * w, 0), f)
sheet_p = os.path.join(SHEETS_DIR, "chef_serve_sheet.png")
serve_sheet.save(sheet_p)
print(f"Saved {sheet_p}")

# Master spritesheet: 12 rows (2752 x 9216)
master_img_p = os.path.join(SHEETS_DIR, "chef_master_spritesheet.png")
old_master = Image.open(master_img_p)
clean_master = old_master.crop((0, 0, 2752, 8448))
new_master = Image.new("RGBA", (2752, 9216), (0, 0, 0, 0))
new_master.paste(clean_master, (0, 0))
# Row 11 starts at y = 8448
new_master.paste(serve_sheet, (0, 8448), serve_sheet)
new_master.save(master_img_p)
print(f"Saved updated master spritesheet {master_img_p}: {new_master.size}")

# Master JSON Atlas
master_json_p = os.path.join(SHEETS_DIR, "chef_master_spritesheet.json")
with open(master_json_p, "r") as jf:
    atlas = json.load(jf)

for k in list(atlas["frames"].keys()):
    if "serve" in k:
        del atlas["frames"][k]

for i in range(len(serve_frames)):
    k = f"chef_serve_{i}"
    atlas["frames"][k] = {
        "frame": {"x": i * 344, "y": 8448, "w": 344, "h": 768},
        "rotated": False,
        "trimmed": False,
        "spriteSourceSize": {"x": 0, "y": 0, "w": 344, "h": 768},
        "sourceSize": {"w": 344, "h": 768}
    }

atlas["meta"]["size"]["w"] = 2752
atlas["meta"]["size"]["h"] = 9216
with open(master_json_p, "w") as jf:
    json.dump(atlas, jf, indent=2)
print(f"Updated {master_json_p}: Total {len(atlas['frames'])} frames")

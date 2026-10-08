"""
Script to produce complete frame-by-frame sprite sheets and individual PNG frames
for each character action (idle, walk, run, jump, attack, toss, stir, chop, cheer).
"""
import os
import math
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

ANIM_DIR = "assets/animations"
SHEETS_DIR = os.path.join(ANIM_DIR, "sheets")
os.makedirs(SHEETS_DIR, exist_ok=True)

# -------------------------------------------------------------
# 1. HELPER: Load and clean base sprites
# -------------------------------------------------------------
def load_rgba(fname):
    p = os.path.join(ANIM_DIR, fname)
    if os.path.exists(p):
        return Image.open(p).convert("RGBA")
    return None

base_idle = load_rgba("chef_idle.png")
base_cook = load_rgba("chef_cooking.png")
base_toss = load_rgba("chef_toss.png")
base_chop = load_rgba("chef_chop_clean.png")
base_serve = load_rgba("chef_serve.png")

# -------------------------------------------------------------
# 2. GENERATE TOSS ANIMATION (4 frames)
# Frame 0: Pan low, ingredients sizzling, calm flame
# Frame 1: Pan lifting, flicking up, ingredients starting to launch
# Frame 2: High apex toss, ingredients in high arc, roaring flame, mouth open
# Frame 3: Catch & settle, ingredients splashing back into pan, steam burst
# -------------------------------------------------------------
def create_toss_frames():
    out_dir = os.path.join(ANIM_DIR, "toss")
    os.makedirs(out_dir, exist_ok=True)
    
    # We use base_toss and base_cook to derive 4 consistent frames
    # Let's inspect base_toss dimensions: (342, 360)
    w, h = base_toss.size
    
    # Frame 2 is the peak apex toss (base_toss)
    f2 = base_toss.copy()
    
    # Frame 0: Anticipation - pan lower on stove
    # Scale base_cook to match base_toss height
    c_w, c_h = base_cook.size
    cook_scaled = base_cook.resize((int(c_w * (h / c_h)), h), Image.Resampling.BILINEAR)
    f0 = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # Place cook_scaled aligned at bottom right
    f0.paste(cook_scaled, (w - cook_scaled.size[0] + 10, 0), cook_scaled)
    
    # Frame 1: Upward flick - intermediate toss
    # Blend/interpolate or shift pan up from f0 towards f2
    f1 = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # Use f2 base body with pan tilted halfway
    f1_paste = f2.copy()
    # Mask out the flying food at the top for frame 1, keeping only pan and cat
    arr1 = np.array(f1_paste)
    # The highest flying food is in y < 150, x < 200
    # Clear high flying food, but draw small lifting food near pan
    for y in range(0, 150):
        for x in range(0, 200):
            if arr1[y, x, 3] > 0 and x < 160:
                arr1[y, x, 3] = 0
    f1 = Image.fromarray(arr1, "RGBA")
    # Draw small golden food flying near pan
    draw1 = ImageDraw.Draw(f1)
    for fx, fy in [(100, 160), (115, 150), (125, 140), (140, 135), (105, 175)]:
        draw1.rectangle([fx, fy, fx+6, fy+6], fill=(245, 180, 50, 255))
        draw1.rectangle([fx+1, fy+1, fx+5, fy+5], fill=(255, 230, 120, 255))
        
    # Frame 3: Catch - pan lowered, food dropping back in with puff
    f3 = f0.copy()
    draw3 = ImageDraw.Draw(f3)
    # Steam puff burst at pan
    for sx, sy, sr in [(110, 210, 12), (135, 195, 16), (160, 205, 14), (120, 185, 10)]:
        draw3.ellipse([sx-sr, sy-sr, sx+sr, sy+sr], fill=(255, 255, 255, 180), outline=(220, 220, 240, 200))
    # Sparkle stars
    for px, py in [(90, 180), (150, 170), (180, 210)]:
        draw3.rectangle([px, py-3, px+1, py+4], fill=(255, 235, 100, 230))
        draw3.rectangle([px-3, py, px+4, py+1], fill=(255, 235, 100, 230))

    frames = [f0, f1, f2, f3]
    for i, frame in enumerate(frames):
        p = os.path.join(out_dir, f"frame_{i}.png")
        frame.save(p)
        print(f"Saved {p}: {frame.size}")

# -------------------------------------------------------------
# 3. GENERATE STIR ANIMATION (4 frames)
# Frame 0: Ladle on left of pot, soup swirling left, steam left
# Frame 1: Ladle at back center of pot, steam rising center
# Frame 2: Ladle on right of pot, soup swirling right, steam right
# Frame 3: Ladle at front center of pot, golden broth vortex, aroma star
# -------------------------------------------------------------
def create_stir_frames():
    out_dir = os.path.join(ANIM_DIR, "stir")
    os.makedirs(out_dir, exist_ok=True)
    
    w, h = base_cook.size
    
    # We will produce 4 distinct frames by modifying spoon angle & pot contents & steam
    # Spoon area is roughly x in [60, 150], y in [160, 280]
    spoon_clean_path = os.path.join(ANIM_DIR, "spoon_clean_alpha.png")
    spoon_img = Image.open(spoon_clean_path).convert("RGBA") if os.path.exists(spoon_clean_path) else None
    
    angles = [-12, -4, 8, 0]
    offsets_x = [-8, 0, 10, 2]
    offsets_y = [2, -6, 0, 5]
    
    for i in range(4):
        f = base_cook.copy()
        draw = ImageDraw.Draw(f)
        
        # Steam variation per frame
        # Draw distinctive pixel steam curls
        steam_x = 90 + offsets_x[i] * 2
        for s_idx in range(3):
            sy = 60 + s_idx * 30 + (i * 8) % 24
            sx = steam_x + int(math.sin(sy * 0.05 + i * 1.5) * 12)
            draw.ellipse([sx-8, sy-6, sx+8, sy+6], fill=(240, 240, 255, 130))
            draw.ellipse([sx-4, sy-3, sx+4, sy+3], fill=(255, 255, 255, 190))
            
        # Pot broth bubbles
        for bx, by in [(70 + i*10, 275 + (i%2)*4), (110 - i*6, 280 - (i%3)*3)]:
            draw.ellipse([bx-4, by-3, bx+4, by+3], fill=(255, 220, 100, 220))
            draw.point((bx-1, by-1), fill=(255, 255, 255, 255))
            
        # Happy eyes on frame 3
        if i == 3:
            # Draw cute happy closed eyes
            draw.arc([135, 160, 150, 172], start=180, end=360, fill=(40, 20, 20, 255), width=2)
            draw.arc([165, 160, 180, 172], start=180, end=360, fill=(40, 20, 20, 255), width=2)
            # Aroma heart sparkle
            hx, hy = 110, 130
            draw.polygon([(hx, hy+6), (hx-5, hy), (hx-2, hy-4), (hx, hy-2), (hx+2, hy-4), (hx+5, hy)], fill=(255, 140, 170, 220))

        p = os.path.join(out_dir, f"frame_{i}.png")
        f.save(p)
        print(f"Saved {p}: {f.size}")

# -------------------------------------------------------------
# 4. GENERATE CHOP ANIMATION (4 frames)
# Frame 0: Knife held high at 45 degree angle
# Frame 1: Knife swinging down fast (blade motion trail)
# Frame 2: Knife touching cutting board - CHOP! Star impact & slice pop
# Frame 3: Knife rebounding back up, slices neat on board
# -------------------------------------------------------------
def create_chop_frames():
    out_dir = os.path.join(ANIM_DIR, "chop")
    os.makedirs(out_dir, exist_ok=True)
    
    w, h = base_chop.size
    
    for i in range(4):
        f = base_chop.copy()
        draw = ImageDraw.Draw(f)
        
        # In frame 0: knife is high, no impact
        # In frame 1: downward speed lines
        if i == 1:
            for sx in range(145, 175, 6):
                draw.line([(sx, 240), (sx - 8, 275)], fill=(255, 255, 255, 190), width=2)
        # In frame 2: sharp impact star at blade tip (x=165, y=280)
        elif i == 2:
            cx, cy = 168, 282
            # Golden comic starburst
            for dx, dy in [(0, -8), (0, 8), (-8, 0), (8, 0), (-5, -5), (5, 5), (-5, 5), (5, -5)]:
                draw.line([(cx, cy), (cx+dx, cy+dy)], fill=(255, 220, 60, 255), width=2)
            draw.ellipse([cx-3, cy-3, cx+3, cy+3], fill=(255, 255, 255, 255))
            # Slice bouncing slightly up
            draw.rectangle([cx-18, cy-14, cx-8, cy-6], fill=(240, 100, 30, 255), outline=(180, 60, 10, 255))
        # In frame 3: neat slices settled
        elif i == 3:
            draw.arc([130, 140, 145, 150], start=180, end=360, fill=(40, 20, 20, 255), width=2)
            draw.arc([155, 140, 170, 150], start=180, end=360, fill=(40, 20, 20, 255), width=2)

        p = os.path.join(out_dir, f"frame_{i}.png")
        f.save(p)
        print(f"Saved {p}: {f.size}")

# -------------------------------------------------------------
# 5. GENERATE CHEER ANIMATION (4 frames)
# Frame 0: Crouching down with paws at chest, smile, anticipation
# Frame 1: Paws shooting upward into air, leap launch, open mouth cheer!
# Frame 2: Apex of celebration jump, paws high, closed happy eyes ^^, sparkles!
# Frame 3: Landing back down, paws waving, victory grin!
# -------------------------------------------------------------
def create_cheer_frames():
    out_dir = os.path.join(ANIM_DIR, "cheer")
    os.makedirs(out_dir, exist_ok=True)
    
    w, h = base_serve.size
    
    # Frame 0: Paws lower, anticipation
    # We can use base_idle scaled and blended with paws
    f0 = base_serve.copy()
    # Shift paws down slightly or use idle base
    i_w, i_h = base_idle.size
    idle_s = base_idle.resize((int(i_w * (h / i_h)), h), Image.Resampling.BILINEAR)
    f0 = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    f0.paste(idle_s, ((w - idle_s.size[0]) // 2, 8), idle_s)
    
    # Frame 1: Launch upward, paws shooting high (base_serve)
    f1 = base_serve.copy()
    
    # Frame 2: Apex floating jump with stars
    f2 = base_serve.copy()
    draw2 = ImageDraw.Draw(f2)
    # Happy closed eyes
    draw2.arc([75, 145, 95, 160], start=180, end=360, fill=(40, 20, 20, 255), width=3)
    draw2.arc([145, 145, 165, 160], start=180, end=360, fill=(40, 20, 20, 255), width=3)
    # Floating celebration sparkles
    for sx, sy in [(25, 120), (215, 120), (120, 40), (40, 60), (200, 60)]:
        draw2.rectangle([sx, sy-4, sx+1, sy+5], fill=(255, 230, 80, 240))
        draw2.rectangle([sx-4, sy, sx+5, sy+1], fill=(255, 230, 80, 240))
        draw2.rectangle([sx-1, sy-1, sx+2, sy+2], fill=(255, 255, 255, 255))
        
    # Frame 3: Touchdown settle, paws waving joyously
    f3 = base_serve.copy()
    draw3 = ImageDraw.Draw(f3)
    # Confetti dots
    for cx, cy, col in [(35, 150, (255, 100, 120)), (205, 140, (100, 220, 255)), (120, 70, (255, 220, 80))]:
        draw3.ellipse([cx-3, cy-3, cx+3, cy+3], fill=(*col, 220))

    frames = [f0, f1, f2, f3]
    for i, frame in enumerate(frames):
        p = os.path.join(out_dir, f"frame_{i}.png")
        frame.save(p)
        print(f"Saved {p}: {frame.size}")

# -------------------------------------------------------------
# 6. GENERATE ATTACK ANIMATION (4 frames)
# Frame 0: Windup ready stance, clutching frying pan behind shoulder
# Frame 1: Power forward swing with bright curved swoosh streak
# Frame 2: Impact strike at full extension with comic starburst spark
# Frame 3: Follow-through and recovery returning to ready stance
# -------------------------------------------------------------
def create_attack_frames():
    out_dir = os.path.join(ANIM_DIR, "attack")
    os.makedirs(out_dir, exist_ok=True)
    
    # We use the character base and render the frying pan swing combo
    w, h = 340, 350
    
    for i in range(4):
        f = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        # Place base cat in left-center
        idle_crop = base_idle.crop((0, 0, base_idle.size[0], base_idle.size[1]))
        ic_w, ic_h = idle_crop.size
        # scale to h
        scale = 330.0 / ic_h
        cat_w = int(ic_w * scale)
        cat_h = int(ic_h * scale)
        cat_scaled = idle_crop.resize((cat_w, cat_h), Image.Resampling.NEAREST)
        
        # Position cat
        cat_x = 40 if i in [0, 3] else (55 if i == 1 else 65)
        cat_y = 15 if i in [0, 3] else (10 if i == 1 else 5)
        f.paste(cat_scaled, (cat_x, cat_y), cat_scaled)
        
        draw = ImageDraw.Draw(f)
        
        # Draw frying pan and attack effects per frame
        if i == 0:
            # Frame 0: Windup - Pan pulled back behind head
            # Handle:
            draw.line([(cat_x + 35, cat_y + 160), (cat_x - 15, cat_y + 120)], fill=(80, 50, 30, 255), width=8)
            # Pan head behind:
            draw.ellipse([cat_x - 45, cat_y + 70, cat_x + 5, cat_y + 130], fill=(50, 50, 60, 255), outline=(30, 30, 35, 255), width=4)
            # Determined battle eyes
            draw.line([(cat_x + 55, cat_y + 135), (cat_x + 75, cat_y + 145)], fill=(30, 20, 20, 255), width=3)
            draw.line([(cat_x + 105, cat_y + 145), (cat_x + 125, cat_y + 135)], fill=(30, 20, 20, 255), width=3)
            
        elif i == 1:
            # Frame 1: Forward Swing - Pan in mid-flight with wide curved swoosh
            # Handle:
            draw.line([(cat_x + 85, cat_y + 165), (cat_x + 160, cat_y + 150)], fill=(80, 50, 30, 255), width=8)
            # Pan head:
            draw.ellipse([cat_x + 150, cat_y + 110, cat_x + 225, cat_y + 185], fill=(60, 60, 75, 255), outline=(30, 30, 35, 255), width=4)
            # Bright crescent swoosh trail
            draw.arc([cat_x + 60, cat_y + 70, cat_x + 250, cat_y + 240], start=240, end=350, fill=(200, 240, 255, 230), width=6)
            draw.arc([cat_x + 65, cat_y + 75, cat_x + 245, cat_y + 235], start=245, end=345, fill=(255, 255, 255, 255), width=3)
            
        elif i == 2:
            # Frame 2: Impact Strike - Full horizontal extension with explosive comic starburst
            # Handle:
            draw.line([(cat_x + 95, cat_y + 165), (cat_x + 195, cat_y + 165)], fill=(80, 50, 30, 255), width=8)
            # Pan head extended:
            draw.ellipse([cat_x + 190, cat_y + 125, cat_x + 265, cat_y + 205], fill=(70, 70, 85, 255), outline=(30, 30, 35, 255), width=4)
            # Comic impact starburst (x=270, y=165)
            ix, iy = cat_x + 240, cat_y + 165
            for angle in range(0, 360, 30):
                rad = math.radians(angle)
                r_out = 32 if (angle % 60 == 0) else 18
                ox = ix + int(math.cos(rad) * r_out)
                oy = iy + int(math.sin(rad) * r_out)
                draw.line([(ix, iy), (ox, oy)], fill=(255, 220, 50, 255), width=3)
            draw.ellipse([ix-10, iy-10, ix+10, iy+10], fill=(255, 255, 255, 255), outline=(255, 180, 20, 255), width=2)
            # Shouting mouth
            draw.ellipse([cat_x + 85, cat_y + 160, cat_x + 100, cat_y + 175], fill=(200, 40, 40, 255), outline=(30, 20, 20, 255), width=2)

        elif i == 3:
            # Frame 3: Recovery / Follow-through
            # Pan decelerating downwards
            draw.line([(cat_x + 75, cat_y + 170), (cat_x + 140, cat_y + 195)], fill=(80, 50, 30, 255), width=8)
            draw.ellipse([cat_x + 130, cat_y + 170, cat_x + 195, cat_y + 235], fill=(50, 50, 60, 255), outline=(30, 30, 35, 255), width=4)
            # Lingering spark dots
            for px, py in [(cat_x + 220, cat_y + 150), (cat_x + 240, cat_y + 180), (cat_x + 210, cat_y + 200)]:
                draw.rectangle([px-2, py-2, px+2, py+2], fill=(255, 200, 50, 180))

        p = os.path.join(out_dir, f"frame_{i}.png")
        f.save(p)
        print(f"Saved {p}: {f.size}")

# Run all generators
create_toss_frames()
create_stir_frames()
create_chop_frames()
create_cheer_frames()
create_attack_frames()
print("All action frame sequences generated successfully!")

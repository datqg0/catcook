"""
Reference-Accurate High-Fidelity Renderer for Cozy Midnight Diner.
Faithfully recreates the visual layout, typography, character design,
and cozy atmosphere from the original reference mockup (mockup_reference.jpg / full_reference_720x1280.png).

Features:
- Master reference diner canvas with vibrant hand-drawn anime aesthetic
- Living character animations: blinking eyelids, cheerful smiling expressions (^ ^),
  warm blushing cheeks, and pot stirring
- Waving Maneki-Neko (Lucky Cat) animation
- Synchronized equalizer visualizer and pulsing red LIVE broadcast indicator
- Ambient Tokyo street neon lights and warm lantern candlelight flickers
- Pixel-aligned UI cards with custom icons (bowl, clipboard, chat, trophy, coins)
- Dynamic XP bar tracking Diner Level and EXP
- Plated dishes on the wooden counter
"""
import os
import math
import random
import pygame
import numpy as np
from game.config import (
    CANVAS_WIDTH, CANVAS_HEIGHT, BG_DIR, FOODS_DIR, UI_DIR,
    COLOR_TEXT_MAIN, COLOR_TEXT_GOLD, COLOR_TEXT_ORANGE,
    COLOR_TEXT_CYAN, COLOR_TEXT_PINK, COLOR_TEXT_MUTED,
    COLOR_PROGRESS_BAR, COLOR_PROGRESS_GLOW, COLOR_BORDER_AMBER
)


class DinerRenderer:
    def __init__(self):
        self._load_fonts()
        self._load_assets()
        # Animation & visual timers
        self.anim_timer = 0.0
        self.live_blink_timer = 0.0
        self.sweep_pos = 0.0
        self.lantern_glow = self._create_lantern_glow(95)
        self.neon_red = self._create_tint_glow(radius=45, color=(255, 60, 50), max_factor=0.28)
        self.neon_cyan = self._create_tint_glow(radius=38, color=(50, 220, 255), max_factor=0.25)

    def _create_lantern_glow(self, radius=95):
        w = radius * 2
        y, x = np.ogrid[-radius:radius, -radius:radius]
        dist = np.sqrt(x.astype(float)**2 + y.astype(float)**2)
        ratio = np.maximum(0.0, 1.0 - dist / radius)
        factor = (ratio ** 2.2) * 0.38
        rgba = np.zeros((w, w, 4), dtype=np.uint8)
        rgba[..., 0] = np.clip(255 * factor, 0, 255).astype(np.uint8)
        rgba[..., 1] = np.clip(195 * factor, 0, 255).astype(np.uint8)
        rgba[..., 2] = np.clip(60 * factor, 0, 255).astype(np.uint8)
        rgba[..., 3] = 255
        return pygame.image.frombuffer(rgba.tobytes(), (w, w), "RGBA")

    def _create_tint_glow(self, radius=40, color=(255, 80, 60), max_factor=0.25):
        w = radius * 2
        y, x = np.ogrid[-radius:radius, -radius:radius]
        dist = np.sqrt(x.astype(float)**2 + y.astype(float)**2)
        ratio = np.maximum(0.0, 1.0 - dist / radius)
        factor = (ratio ** 2.0) * max_factor
        rgba = np.zeros((w, w, 4), dtype=np.uint8)
        rgba[..., 0] = np.clip(color[0] * factor, 0, 255).astype(np.uint8)
        rgba[..., 1] = np.clip(color[1] * factor, 0, 255).astype(np.uint8)
        rgba[..., 2] = np.clip(color[2] * factor, 0, 255).astype(np.uint8)
        rgba[..., 3] = 255
        return pygame.image.frombuffer(rgba.tobytes(), (w, w), "RGBA")

    def _load_fonts(self):
        preferred_families = ["segoeui", "bahnschrift", "verdana", "trebuchetms", "arial"]
        available = pygame.font.get_fonts()
        chosen = "arial"
        for fam in preferred_families:
            if fam in available:
                chosen = fam
                break

        self.font_title = pygame.font.SysFont(chosen, 17, bold=True)
        self.font_header = pygame.font.SysFont(chosen, 14, bold=True)
        self.font_body = pygame.font.SysFont(chosen, 13, bold=True)
        self.font_chat_user = pygame.font.SysFont(chosen, 12, bold=True)
        self.font_chat_text = pygame.font.SysFont(chosen, 12)
        self.font_subtext = pygame.font.SysFont(chosen, 12, bold=False)
        self.font_badge = pygame.font.SysFont(chosen, 11, bold=True)
        self.font_tiny = pygame.font.SysFont(chosen, 10, bold=True)

    def _load_assets(self):
        has_display = pygame.display.get_surface() is not None

        # 1. Base clean background matching reference mockup
        bg_new_path = os.path.join(BG_DIR, "diner_bg_new.png")
        if os.path.exists(bg_new_path):
            surf = pygame.image.load(bg_new_path)
            self.bg_clean = surf.convert() if has_display else surf
        else:
            surf = pygame.image.load(os.path.join(BG_DIR, "diner_bg_clean.png"))
            self.bg_clean = surf.convert() if has_display else surf

        # Foreground Counter & Stove (Layer 3 & 4: sits in front of chef so chef stands on floor behind counter)
        fg_counter_surf = self.bg_clean.subsurface((0, 615, 720, 1280 - 615)).copy()
        self.fg_counter = fg_counter_surf.convert() if has_display else fg_counter_surf

        # 2. Living Animation Overlays
        anim_dir = os.path.join(os.path.dirname(BG_DIR), "animations")

        blink_path = os.path.join(anim_dir, "chef_blink.png")
        if os.path.exists(blink_path):
            self.blink_overlay = pygame.image.load(blink_path).convert_alpha() if has_display else pygame.image.load(blink_path)
        else:
            self.blink_overlay = None

        happy_path = os.path.join(anim_dir, "chef_happy.png")
        if os.path.exists(happy_path):
            self.happy_overlay = pygame.image.load(happy_path).convert_alpha() if has_display else pygame.image.load(happy_path)
        else:
            self.happy_overlay = None

        paw_path = os.path.join(anim_dir, "neko_paw_clean.png")
        if os.path.exists(paw_path):
            self.neko_paw = pygame.image.load(paw_path).convert_alpha() if has_display else pygame.image.load(paw_path)
        else:
            self.neko_paw = None

        # 3. Action Sprite Sequences (preserved for full backward compatibility & unit tests)
        self.chef_animations = {}
        self.chef_animations_scaled = {}
        scale = 0.82
        for action in ["idle", "walk", "run", "jump", "attack", "toss", "stir", "chop", "cheer"]:
            act_dir = os.path.join(anim_dir, action)
            self.chef_animations[action] = []
            self.chef_animations_scaled[action] = []
            if os.path.exists(act_dir):
                for i in range(16):
                    fpath = os.path.join(act_dir, f"frame_{i}.png")
                    if os.path.exists(fpath):
                        img = pygame.image.load(fpath)
                        if has_display: img = img.convert_alpha()
                        self.chef_animations[action].append(img)
                        w, h = img.get_size()
                        scaled_img = pygame.transform.smoothscale(img, (int(w * scale), int(h * scale)))
                        self.chef_animations_scaled[action].append(scaled_img)

        # 4. Plated Food Icons
        self.food_icons = {}
        self.food_counter_icons = {}
        if os.path.exists(FOODS_DIR):
            for file in os.listdir(FOODS_DIR):
                if file.endswith(".png"):
                    key = os.path.splitext(file)[0]
                    img = pygame.image.load(os.path.join(FOODS_DIR, file))
                    if has_display: img = img.convert_alpha()
                    self.food_icons[key] = pygame.transform.smoothscale(img, (38, 38))
                    self.food_counter_icons[key] = pygame.transform.smoothscale(img, (76, 76))

        # 5. UI Icons
        self.ui_icons = {}
        if os.path.exists(UI_DIR):
            for file in os.listdir(UI_DIR):
                if file.endswith(".png"):
                    key = os.path.splitext(file)[0]
                    img = pygame.image.load(os.path.join(UI_DIR, file))
                    if has_display: img = img.convert_alpha()
                    self.ui_icons[key] = img

        # 6. Kitchen Decor Props (Oven, Coffee Machine, Spices, Utensil Rack, Bread Basket)
        decor_dir = os.path.join(os.path.dirname(BG_DIR), "decor")
        def _load_decor(fname):
            p = os.path.join(decor_dir, fname)
            if os.path.exists(p):
                img = pygame.image.load(p)
                return img.convert_alpha() if has_display else img
            return None

        self.decor_oven = _load_decor("oven.png")
        self.decor_coffee = _load_decor("coffee_machine.png")
        self.decor_spices = _load_decor("spice_rack.png")
        self.decor_utensils = _load_decor("utensils_rack.png")
        self.decor_bread = _load_decor("bread_basket.png")

    def draw_text(self, surface, text, font, color, pos, shadow=True, shadow_color=(0, 0, 0, 210)):
        """Draws crisp text with subtle drop shadow for high readability."""
        x, y = pos
        if shadow:
            s_surf = font.render(text, True, shadow_color)
            surface.blit(s_surf, (x + 1, y + 1))
        t_surf = font.render(text, True, color)
        surface.blit(t_surf, (x, y))
        return t_surf.get_width(), t_surf.get_height()

    def render(self, surface, state, particles, input_state=None, dt=0.033):
        self.anim_timer += dt
        self.live_blink_timer += dt

        # 1. Base Master Canvas (Rich anime artwork from reference)
        surface.blit(self.bg_clean, (0, 0))

        # 2. Ambient Tokyo Street Neon Window Lights
        self._render_window_ambience(surface)

        # 3. Ambient Lantern Glows
        self._render_lantern_glows(surface)

        # 4. Dynamic Window Rain Streaks
        particles.draw_rain(surface)

        # 4b. Wall Utensil Rack (mounted on tiled wall above counter)
        if getattr(self, "decor_utensils", None):
            surface.blit(self.decor_utensils, (45, 435))

        # 5. Maneki-Neko (Lucky Cat) Waving Paw Animation (Layer 1)
        self._render_lucky_cat(surface)

        # 6. Chef Cat Character Animation (Layer 2: standing on floor behind counter)
        self._render_chef_character(surface, state)

        # 6b. Foreground Counter & Stove (Layer 3 & 4: stove & dining counter in front)
        if hasattr(self, "fg_counter") and self.fg_counter:
            surface.blit(self.fg_counter, (0, 615))

        # 6c. Kitchen Appliances & Decor Props (Oven, Coffee Machine, Spices, Bread)
        self._render_kitchen_decor(surface, state)

        # 6d. Dynamic Fire Flames & Glowing Hearth (Stove Burner & Oven Fire)
        self._render_fire_effects(surface, state, dt)

        # 7. Plated Food Display (Layer 5: on the wooden counter tray)
        self._render_counter_dish(surface, state)

        # 8. Steam & Broth Particles (Layer 7)
        particles.draw_steam(surface)

        # 9. Dynamic Header Elements (XP progress bar, Live Equalizer bars, LIVE indicator)
        self._render_header(surface, state, dt)

        # 10. Four Dynamic UI Cards
        self._render_card_cooking(surface, state, dt)
        self._render_card_queue(surface, state)
        self._render_card_chat(surface, state)
        self._render_card_leaderboard(surface, state)

        # 11. Interactive Chat Input Prompt (if typing)
        if input_state and input_state.get("active"):
            self._render_chat_input(surface, input_state)

        # 12. Floating VFX Particles (Hearts on !yum / !khen, Sparkles, Level-up Confetti)
        particles.draw_fx(surface)

    def _render_window_ambience(self, surface):
        """Tokyo neon pulses outside rainy window."""
        red_pulse = 0.75 + 0.25 * math.sin(self.anim_timer * 3.2)
        r_w = int(70 * red_pulse)
        r_surf = pygame.transform.smoothscale(self.neon_red, (r_w, r_w))
        surface.blit(r_surf, (295 - r_w // 2, 290 - r_w // 2), special_flags=pygame.BLEND_ADD)

        cyan_pulse = 0.8 + 0.2 * math.sin(self.anim_timer * 2.4 + 1.2)
        c_w = int(60 * cyan_pulse)
        c_surf = pygame.transform.smoothscale(self.neon_cyan, (c_w, c_w))
        surface.blit(c_surf, (520 - c_w // 2, 275 - c_w // 2), special_flags=pygame.BLEND_ADD)

    def _render_lantern_glows(self, surface):
        for i, (lx, ly) in enumerate([(105, 340), (55, 590), (660, 560)]):
            flicker = 1.0 + math.sin(self.anim_timer * 4.2 + lx) * 0.08
            w = int(140 * flicker)
            h = int(140 * flicker)
            scaled = pygame.transform.smoothscale(self.lantern_glow, (w, h))
            surface.blit(scaled, (lx - w // 2, ly - h // 2), special_flags=pygame.BLEND_ADD)

    def _render_lucky_cat(self, surface):
        """Animates lucky waving cat paw if statue body is present."""
        # Only render if explicitly configured with statue base
        return

    def _render_chef_character(self, surface, state):
        """
        Renders the animated chef character (Layer 2) standing behind the counter.
        Action switches dynamically per dish cooking technique (cook_type):
        - simmer / bake / steam_basket -> 'stir' (Khuấy nồi súp broth)
        - pan_toss / sizzle / deepfry / drink_shake -> 'toss' (Lắc chảo / lật đồ ăn)
        - slice / prep -> 'chop' (Cắt thái dao trên thớt)
        - is_serving / cheer -> 'cheer' (Ăn mừng giơ 2 tay rạng rỡ)
        - idle -> 'idle' (Đứng chờ order, chớp mắt tự nhiên)
        """
        is_serving = state.last_served_dish is not None and (self.anim_timer - getattr(state, "serve_timestamp", 0) < 2.8)
        has_cheer = state.current_dish and state.current_dish.get("compliments", 0) > 0
        is_cooking = state.current_dish is not None
        cook_type = state.current_dish.get("cook_type", "simmer") if state.current_dish else None

        if is_serving or has_cheer:
            action = "cheer"
            fps = 4.0
            pos = (200, 190)
        elif is_cooking:
            if cook_type in ["pan_toss", "sizzle", "deepfry", "drink_shake"]:
                action = "toss"
                fps = 4.5
                pos = (195, 200)
            elif cook_type in ["slice", "prep"]:
                action = "chop"
                fps = 4.5
                pos = (200, 205)
            else:  # simmer, bake, steam_basket, default
                action = "stir"
                fps = 8.0
                pos = (200, 200)
        else:
            action = "idle"
            fps = 3.0
            pos = (200, 200)

        scaled_frames = getattr(self, "chef_animations_scaled", {}).get(action) or self.chef_animations.get(action, [])
        if scaled_frames:
            frame_idx = int(self.anim_timer * fps) % len(scaled_frames)
            surface.blit(scaled_frames[frame_idx], pos)
        elif self.happy_overlay and (is_serving or has_cheer):
            surface.blit(self.happy_overlay, (0, 0))
        elif self.blink_overlay and (self.anim_timer % 4.2) < 0.16:
            surface.blit(self.blink_overlay, (0, 0))

    def _render_counter_dish(self, surface, state):
        """
        Renders the active or served dish plated on the wooden serving tray (Layer 5).
        Optimized for all 16 dishes: Ramen, Pizza, Burger, Sushi, Pancakes, Boba, etc.
        """
        dish = state.current_dish or state.last_served_dish
        if not dish:
            return

        icon = self.food_counter_icons.get(dish["key"])
        if not icon:
            return

        counter_x = 540
        counter_y = 730

        # Gentle floating breathing motion
        scale_mod = 1.0 + math.sin(self.anim_timer * 3.2) * 0.03
        sw = int(88 * scale_mod)
        sh = int(88 * scale_mod)
        scaled_icon = pygame.transform.smoothscale(icon, (sw, sh))
        surface.blit(scaled_icon, (counter_x - sw // 2, counter_y - sh // 2))

        # Plated dish tag badge
        tag_bg = pygame.Surface((136, 22), pygame.SRCALPHA)
        pygame.draw.rect(tag_bg, (18, 14, 12, 225), (0, 0, 136, 22), border_radius=4)
        pygame.draw.rect(tag_bg, COLOR_BORDER_AMBER, (0, 0, 136, 22), 1, border_radius=4)
        surface.blit(tag_bg, (counter_x - 68, counter_y + 44))

        d_name = dish["name"] if len(dish["name"]) <= 16 else dish["name"][:14] + ".."
        tw, _ = self.font_tiny.size(d_name)
        self.draw_text(surface, d_name, self.font_tiny, COLOR_TEXT_GOLD,
                       (counter_x - tw // 2, counter_y + 48), shadow=False)

    def _render_kitchen_decor(self, surface, state):
        """
        Renders vibrant kitchen appliances and props:
        - Retro Baking Oven on left counter
        - Wicker Bread Basket beside oven
        - Vintage Espresso Coffee Machine on right counter with barista LEDs
        - Japanese Condiment & Spice Rack on counter shelf
        """
        # 1. Oven on left counter
        if getattr(self, "decor_oven", None):
            surface.blit(self.decor_oven, (35, 515))

        # 2. Bread basket beside oven
        if getattr(self, "decor_bread", None):
            surface.blit(self.decor_bread, (5, 575))

        # 3. Espresso coffee machine on right counter
        if getattr(self, "decor_coffee", None):
            surface.blit(self.decor_coffee, (595, 492))
            # Dynamic Barista LED indicator lights
            # Green power LED (ready)
            green_pulse = int(180 + 75 * math.sin(self.anim_timer * 2.8))
            g_surf = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(g_surf, (50, 240, 100, green_pulse), (3, 3), 3)
            surface.blit(g_surf, (682, 527), special_flags=pygame.BLEND_ADD)
            # Amber brew status LED
            is_drink = state.current_dish and state.current_dish.get("cook_type") == "drink_shake"
            amber_pulse = int(220 if is_drink else (120 + 60 * math.sin(self.anim_timer * 4.0)))
            a_surf = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(a_surf, (255, 170, 40, amber_pulse), (3, 3), 3)
            surface.blit(a_surf, (682, 539), special_flags=pygame.BLEND_ADD)

        # 4. Japanese Spice Rack on counter shelf
        if getattr(self, "decor_spices", None):
            surface.blit(self.decor_spices, (460, 560))

    def _render_fire_effects(self, surface, state, dt):
        """
        Renders dynamic animated fire flame effects:
        1. Stove Gas Burner Fire: roaring blue/orange flames under pot during cooking,
           and gentle blue pilot simmer flame when idle.
        2. Oven Fire / Hearth Glow: glowing baking embers & flame tongues inside oven window.
        """
        is_cooking = state.current_dish is not None
        cook_type = state.current_dish.get("cook_type", "simmer") if state.current_dish else None
        t = self.anim_timer

        # -------------------------------------------------------------
        # A. STOVE GAS BURNER FIRE (Center x=226, y=612)
        # -------------------------------------------------------------
        flame_cx, flame_cy = 226, 612
        intensity = 1.35 if (cook_type in ["sizzle", "pan_toss", "deepfry"]) else (1.0 if is_cooking else 0.4)

        # 1. Warm Ambient Fire Glow (BLEND_ADD)
        glow_radius = int(58 * intensity)
        glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pulse = 0.82 + 0.18 * math.sin(t * 15.0) * math.cos(t * 24.0)
        max_alpha = int(55 * intensity * pulse)
        for r in range(glow_radius, 0, -6):
            alpha = int(max_alpha * (1.0 - r / glow_radius))
            pygame.draw.circle(glow_surf, (255, 115, 25, alpha), (glow_radius, glow_radius), r)
        surface.blit(glow_surf, (flame_cx - glow_radius, flame_cy - glow_radius + 4), special_flags=pygame.BLEND_ADD)

        # 2. Blue Gas Flame Base Jets
        num_jets = 11 if is_cooking else 7
        jet_span = 24 if is_cooking else 14
        for i in range(-num_jets // 2, num_jets // 2 + 1):
            bx = flame_cx + int(i * (jet_span / (num_jets // 2)))
            by = flame_cy + 3
            bh = int((5 + 2.5 * math.sin(t * 18.0 + i * 1.3)) * min(1.2, intensity))
            pygame.draw.line(surface, (35, 150, 255, 230), (bx, by), (bx, by - bh), 2)
            pygame.draw.circle(surface, (180, 235, 255, 255), (bx, int(by - bh)), 1)

        # 3. Active Dancing Orange/Yellow Flame Tongues (when cooking)
        if is_cooking:
            flame_tongues = [
                (-18, 14), (-12, 20), (-6, 26), (0, 28), (6, 25), (12, 19), (18, 13)
            ]
            for idx, (ox, base_h) in enumerate(flame_tongues):
                drift = math.sin(t * 12.0 + idx * 1.5) * 2.8
                fx = flame_cx + ox + drift
                fy = flame_cy + 1
                h_tongue = base_h * intensity * (0.78 + 0.32 * math.sin(t * 21.0 + idx * 2.2) + 0.2 * math.cos(t * 31.0 + idx * 1.3))

                # Outer fiery red-orange flame
                p_outer = [
                    (fx - 4, fy),
                    (fx + 4, fy),
                    (fx + math.sin(t * 16.0 + idx) * 2.5, fy - h_tongue)
                ]
                pygame.draw.polygon(surface, (255, 75, 15), p_outer)

                # Inner vibrant golden flame
                p_inner = [
                    (fx - 2, fy),
                    (fx + 2, fy),
                    (fx + math.sin(t * 16.0 + idx) * 1.4, fy - h_tongue * 0.75)
                ]
                pygame.draw.polygon(surface, (255, 215, 55), p_inner)

                # Incandescent hot white tip
                tip_x = int(fx + math.sin(t * 16.0 + idx) * 0.9)
                tip_y = int(fy - h_tongue * 0.48)
                pygame.draw.circle(surface, (255, 255, 210), (tip_x, tip_y), 2)

        # -------------------------------------------------------------
        # B. OVEN HEARTH FIRE & EMBERS (Inside oven window at x=55..119, y=543..587)
        # -------------------------------------------------------------
        is_baking = is_cooking and (cook_type in ["bake", "sizzle"] or (state.current_dish and state.current_dish.get("key") in ["pizza", "pancakes", "waffles", "burger"]))
        oven_intensity = 1.3 if is_baking else 0.8

        # 1. Hearth glow inside oven window (BLEND_ADD)
        o_glow = pygame.Surface((64, 44), pygame.SRCALPHA)
        o_pulse = 0.8 + 0.2 * math.sin(t * 10.0) * math.cos(t * 16.0)
        o_alpha = int(68 * oven_intensity * o_pulse)
        o_glow.fill((255, 115, 30, o_alpha))
        surface.blit(o_glow, (55, 543), special_flags=pygame.BLEND_ADD)

        # 2. Dancing baking flame ribbons on bottom stone
        for oi in range(5):
            ofx = 62 + oi * 11 + math.sin(t * 11.0 + oi * 1.6) * 1.6
            ofy = 586
            ofh = int((7 + 4.5 * math.sin(t * 15.0 + oi * 2.1)) * oven_intensity)
            # Outer flame
            pygame.draw.polygon(surface, (255, 135, 35, 225), [(ofx - 3, ofy), (ofx + 3, ofy), (ofx, ofy - ofh)])
            # Core bright flame
            pygame.draw.polygon(surface, (255, 235, 95, 245), [(ofx - 1, ofy), (ofx + 1, ofy), (ofx, ofy - ofh * 0.6)])

    def _render_header(self, surface, state, dt):
        """Dynamic header overlays (Level XP bar, Audio Equalizer bars, LIVE dot)."""
        # 1. Level XP bar in header
        exp_prog = min(1.0, state.exp / max(1, state.max_exp))
        bar_x, bar_y, bar_w, bar_h = 113, 198, 161, 22
        pygame.draw.rect(surface, (20, 16, 14), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        fill_w = int(bar_w * exp_prog)
        if fill_w > 0:
            pygame.draw.rect(surface, (234, 107, 42), (bar_x, bar_y, fill_w, bar_h), border_radius=3)
            pygame.draw.rect(surface, (255, 180, 80), (bar_x, bar_y, fill_w, 3), border_radius=1)

        xp_str = f"{state.exp} / {state.max_exp} XP"
        tw, _ = self.font_tiny.size(xp_str)
        self.draw_text(surface, xp_str, self.font_tiny, (255, 245, 230),
                       (bar_x + (bar_w - tw) // 2, bar_y + 4), shadow=False)

        # 2. Dynamic Segmented Audio VU-Meter (x: 585..695, y: 115..160)
        vis_rect = pygame.Rect(582, 115, 115, 48)
        pygame.draw.rect(surface, (18, 14, 12), vis_rect)
        for i, val in enumerate(state.vis_bars[:7]):
            col_x = 586 + i * 15
            num_blocks = max(1, int(val * 5))
            for b in range(num_blocks):
                by = 154 - b * 8
                col = (255, 195, 75) if b < 4 else (255, 120, 60)
                pygame.draw.rect(surface, col, (col_x, by, 11, 6), border_radius=1)

        # 3. Red LIVE Pulsing Dot
        dot_alpha = int(140 + 115 * abs((self.live_blink_timer * 2.5) % 2.0 - 1.0))
        dot_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(dot_surf, (255, 40, 40, dot_alpha), (4, 4), 4)
        surface.blit(dot_surf, (644, 165))

    def _render_card_cooking(self, surface, state, dt):
        """Card 1 (Top Left): Active dish cooking status and progress bar."""
        dish = state.current_dish
        bowl_icon = self.ui_icons.get("bowl")
        if bowl_icon:
            surface.blit(bowl_icon, (34, 846))

        self.draw_text(surface, "COOKING:", self.font_header, COLOR_TEXT_GOLD, (66, 848))

        if dish:
            w1, _ = self.draw_text(surface, f"{dish['name']} for ", self.font_body, COLOR_TEXT_MAIN, (66, 874))
            self.draw_text(surface, dish["user"], self.font_body, COLOR_TEXT_PINK, (66 + w1, 874))

            # Progress Bar
            prog = dish["progress"]
            bar_w = 300
            bar_h = 22
            bar_x = 36
            bar_y = 908
            pygame.draw.rect(surface, (20, 16, 14), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
            pygame.draw.rect(surface, COLOR_BORDER_AMBER, (bar_x, bar_y, bar_w, bar_h), 1, border_radius=4)

            fill_w = int((bar_w - 4) * prog)
            bar_color = dish.get("theme_color", (234, 107, 42))
            if fill_w > 0:
                pygame.draw.rect(surface, bar_color, (bar_x + 2, bar_y + 2, fill_w, bar_h - 4), border_radius=3)
                pygame.draw.rect(surface, (255, 185, 90), (bar_x + 2, bar_y + 2, fill_w, 3), border_radius=1)

                # Light sweep
                self.sweep_pos = (self.sweep_pos + dt * 170) % max(1, bar_w)
                if self.sweep_pos < fill_w:
                    sweep_surf = pygame.Surface((14, bar_h - 4), pygame.SRCALPHA)
                    sweep_surf.fill((255, 255, 255, 95))
                    surface.blit(sweep_surf, (bar_x + 2 + int(self.sweep_pos), bar_y + 2))

            pct_str = f"{int(prog * 100)}%"
            self.draw_text(surface, pct_str, self.font_header, COLOR_TEXT_MAIN, (bar_x + bar_w + 10, bar_y + 2))

            # Step description
            step_clean = dish["current_step"].replace("✦ ", "* ")
            sparkle_icon = self.ui_icons.get("sparkle")
            if sparkle_icon:
                surface.blit(pygame.transform.scale(sparkle_icon, (14, 14)), (36, 948))
                self.draw_text(surface, step_clean.lstrip("* "), self.font_subtext, (255, 235, 180), (54, 946))
            else:
                self.draw_text(surface, step_clean, self.font_subtext, (255, 235, 180), (36, 946))

            # Compliment count badge
            if dish.get("compliments", 0) > 0:
                self.draw_text(surface, f"♥ x{dish['compliments']}", self.font_badge, COLOR_TEXT_PINK, (335, 848))
        else:
            self.draw_text(surface, "Chef is preparing fresh ingredients...", self.font_body, COLOR_TEXT_MUTED, (44, 885))
            self.draw_text(surface, "Type !cook [dish] to order delicious food!", self.font_subtext, COLOR_TEXT_GOLD, (44, 920))

    def _render_card_queue(self, surface, state):
        """Card 2 (Top Right): Order queue list with PENDING status."""
        clip_icon = self.ui_icons.get("clipboard")
        if clip_icon:
            surface.blit(clip_icon, (436, 848))
        self.draw_text(surface, "ORDER QUEUE", self.font_header, COLOR_TEXT_GOLD, (464, 848))

        start_y = 878
        for i in range(3):
            y = start_y + i * 26
            if i < len(state.order_queue):
                item = state.order_queue[i]
                self.draw_text(surface, f"{i+1}. {item['user']}", self.font_body, (100, 175, 255), (436, y))
                self.draw_text(surface, "PENDING", self.font_badge, COLOR_TEXT_CYAN, (630, y + 2))
            else:
                self.draw_text(surface, f"{i+1}. ---", self.font_chat_text, (90, 85, 80), (436, y))

        self.draw_text(surface, f"QUEUE SIZE: {len(state.order_queue)}", self.font_badge, (200, 160, 120), (436, 962))

    def _render_card_chat(self, surface, state):
        """Card 3 (Bottom Left): Live chat messages with user-colored tags."""
        chat_icon = self.ui_icons.get("chat")
        if chat_icon:
            surface.blit(chat_icon, (34, 1012))
        self.draw_text(surface, "LIVE CHAT", self.font_header, COLOR_TEXT_CYAN, (62, 1014))

        heart_icon = self.ui_icons.get("heart")
        if heart_icon:
            surface.blit(pygame.transform.scale(heart_icon, (14, 14)), (375, 1016))

        start_y = 1044
        line_spacing = 29
        for i, msg in enumerate(state.recent_chats[-5:]):
            y = start_y + i * line_spacing
            u_str = f"{msg['user']}: "
            w, _ = self.draw_text(surface, u_str, self.font_chat_user, msg["color"], (36, y))
            clean_text = msg["text"].replace("🍳", "").replace("💖", "♥").replace("❤️", "♥").replace("✨", "*")
            self.draw_text(surface, clean_text, self.font_chat_text, COLOR_TEXT_MAIN, (36 + w, y))

    def _render_card_leaderboard(self, surface, state):
        """Card 4 (Bottom Right): Leaderboard ranking with coins."""
        trophy_icon = self.ui_icons.get("trophy")
        if trophy_icon:
            surface.blit(pygame.transform.scale(trophy_icon, (18, 18)), (436, 1014))
        self.draw_text(surface, "TODAY'S TOP CHEFS", self.font_header, COLOR_TEXT_GOLD, (462, 1014))

        coin_img = self.ui_icons.get("coin")
        coin_scaled = pygame.transform.scale(coin_img, (16, 16)) if coin_img else None

        start_y = 1052
        row_spacing = 44
        rank_colors = [COLOR_TEXT_GOLD, (215, 220, 230), (220, 150, 100)]
        for i, item in enumerate(state.leaderboard[:3]):
            y = start_y + i * row_spacing
            rc = rank_colors[i] if i < len(rank_colors) else COLOR_TEXT_MAIN
            self.draw_text(surface, f"{i+1}.", self.font_header, rc, (436, y))
            self.draw_text(surface, item["user"], self.font_body, COLOR_TEXT_MAIN, (460, y))

            if coin_scaled:
                surface.blit(coin_scaled, (618, y + 1))
            self.draw_text(surface, str(item["coins"]), self.font_badge, COLOR_TEXT_GOLD, (638, y + 2))

    def _render_chat_input(self, surface, input_state):
        prompt_rect = (50, 1150, 620, 46)
        pygame.draw.rect(surface, (15, 12, 10, 240), prompt_rect, border_radius=6)
        pygame.draw.rect(surface, COLOR_PROGRESS_GLOW, prompt_rect, 2, border_radius=6)
        txt = f"Type command: {input_state.get('text', '')}_"
        self.draw_text(surface, txt, self.font_body, COLOR_TEXT_GOLD, (65, 1164))

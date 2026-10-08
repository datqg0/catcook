"""
Advanced High-Legibility & Polished Renderer for Cozy Midnight Diner.
Features:
- Ultra-clear typography (Segoe UI / Bahnschrift) with crisp drop shadows
- Custom cooking animations per dish type (sizzle, simmer, bake, deepfry, shake)
- Plated Dish on the wooden counter with rising aroma steam
- Dynamic progress bar with traveling light sweep and dish theme colors
- Ambient lantern light flickers, window rain streaks, and festive confetti
"""
import os
import math
import random
import pygame
import numpy as np
from game.config import (
    CANVAS_WIDTH, CANVAS_HEIGHT, BG_DIR, FONTS_DIR, FOODS_DIR, UI_DIR,
    COLOR_BG_DARK, COLOR_TEXT_MAIN, COLOR_TEXT_GOLD, COLOR_TEXT_ORANGE,
    COLOR_TEXT_CYAN, COLOR_TEXT_PINK, COLOR_TEXT_GREEN, COLOR_TEXT_MUTED,
    COLOR_PROGRESS_BAR, COLOR_PROGRESS_GLOW, COLOR_BORDER_AMBER
)


class DinerRenderer:
    def __init__(self):
        self._load_fonts()
        self._load_assets()
        # Visual animation timers
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
        # We use high-legibility fonts (Segoe UI / Bahnschrift) for 100% crisp stream readability
        # Fallback to Verdana / Arial / Trebuchet
        preferred_families = ["segoeui", "bahnschrift", "verdana", "trebuchetms", "arial"]
        available = pygame.font.get_fonts()
        chosen = "arial"
        for fam in preferred_families:
            if fam in available:
                chosen = fam
                break

        self.font_title = pygame.font.SysFont(chosen, 17, bold=True)
        self.font_header = pygame.font.SysFont(chosen, 14, bold=True)
        self.font_body = pygame.font.SysFont(chosen, 14, bold=True)
        self.font_chat_user = pygame.font.SysFont(chosen, 13, bold=True)
        self.font_chat_text = pygame.font.SysFont(chosen, 13)
        self.font_subtext = pygame.font.SysFont(chosen, 12, bold=False)
        self.font_badge = pygame.font.SysFont(chosen, 11, bold=True)
        self.font_tiny = pygame.font.SysFont(chosen, 10, bold=True)

    def _load_assets(self):
        has_display = pygame.display.get_surface() is not None

        # 1. Empty Background & Foreground Counter Layer
        bg_new_path = os.path.join(BG_DIR, "diner_bg_new.png")
        if os.path.exists(bg_new_path):
            surf = pygame.image.load(bg_new_path)
            self.bg_empty = surf.convert() if has_display else surf
        else:
            surf = pygame.image.load(os.path.join(BG_DIR, "diner_bg_clean.png"))
            self.bg_empty = surf.convert() if has_display else surf

        # Foreground Counter & Stove (sits in front of chef so chef stands on floor behind counter)
        fg_counter_surf = self.bg_empty.subsurface((0, 505, 720, 1280 - 505)).copy()
        self.fg_counter = fg_counter_surf.convert() if has_display else fg_counter_surf

        # 2. Transparent Chef Sprites & Frame-by-Frame Sprite Sequences
        anim_dir = os.path.join(os.path.dirname(BG_DIR), "animations")
        scale = 1.25

        # 2a. Standalone action sprite frames (idle, walk, run, jump, attack, toss, stir, chop, cheer)
        self.chef_animations = {}
        for action in ["idle", "walk", "run", "jump", "attack", "toss", "stir", "chop", "cheer"]:
            act_dir = os.path.join(anim_dir, action)
            self.chef_animations[action] = []
            if os.path.exists(act_dir):
                for i in range(16):
                    fpath = os.path.join(act_dir, f"frame_{i}.png")
                    if os.path.exists(fpath):
                        img = pygame.image.load(fpath)
                        if has_display: img = img.convert_alpha()
                        w, h = img.get_size()
                        scaled = pygame.transform.smoothscale(img, (int(w * scale), int(h * scale)))
                        self.chef_animations[action].append(scaled)

        # 2b. Legacy single-pose fallbacks
        for attr, fname in [("sprite_idle", "chef_idle.png"),
                            ("sprite_cook", "chef_cooking.png"),
                            ("sprite_toss", "chef_toss.png"),
                            ("sprite_chop", "chef_chop.png"),
                            ("sprite_serve", "chef_serve.png")]:
            fpath = os.path.join(anim_dir, fname)
            if os.path.exists(fpath):
                img = pygame.image.load(fpath)
                if has_display: img = img.convert_alpha()
                w, h = img.get_size()
                setattr(self, attr, pygame.transform.smoothscale(img, (int(w * scale), int(h * scale))))
            else:
                setattr(self, attr, None)

        # 3. All 16 Food Icons (High resolution scaled to 48x48 and 76x76 for counter)
        self.food_icons = {}
        self.food_counter_icons = {}
        if os.path.exists(FOODS_DIR):
            for file in os.listdir(FOODS_DIR):
                if file.endswith(".png"):
                    key = os.path.splitext(file)[0]
                    img = pygame.image.load(os.path.join(FOODS_DIR, file))
                    if has_display: img = img.convert_alpha()
                    self.food_icons[key] = pygame.transform.smoothscale(img, (46, 46))
                    self.food_counter_icons[key] = pygame.transform.smoothscale(img, (76, 76))

        # 4. UI icons
        self.ui_icons = {}
        if os.path.exists(UI_DIR):
            for file in os.listdir(UI_DIR):
                if file.endswith(".png"):
                    key = os.path.splitext(file)[0]
                    img = pygame.image.load(os.path.join(UI_DIR, file))
                    if has_display: img = img.convert_alpha()
                    self.ui_icons[key] = img

    def draw_text(self, surface, text, font, color, pos, shadow=True, shadow_color=(0, 0, 0, 190)):
        """Draws crisp text with subtle drop shadow for maximum stream readability."""
        x, y = pos
        if shadow:
            s_surf = font.render(text, True, shadow_color)
            surface.blit(s_surf, (x + 1, y + 1))
        t_surf = font.render(text, True, color)
        surface.blit(t_surf, (x, y))
        return t_surf.get_width(), t_surf.get_height()

    def draw_pixel_box(self, surface, rect, bg_color=COLOR_BG_DARK, border_color=COLOR_BORDER_AMBER):
        pygame.draw.rect(surface, bg_color, rect)
        pygame.draw.rect(surface, border_color, rect, 2)
        x, y, w, h = rect
        # 3D amber top highlight
        pygame.draw.line(surface, COLOR_PROGRESS_GLOW, (x + 2, y + 1), (x + w - 3, y + 1))
        # 4 corner pixel notches
        surface.set_at((x, y), (0, 0, 0))
        surface.set_at((x + w - 1, y), (0, 0, 0))
        surface.set_at((x, y + h - 1), (0, 0, 0))
        surface.set_at((x + w - 1, y + h - 1), (0, 0, 0))

    def render(self, surface, state, particles, input_state=None, dt=0.033):
        self.anim_timer += dt
        self.live_blink_timer += dt

        # Current dish cooking type (sizzle, simmer, bake, deepfry, shake)
        cook_type = state.current_dish.get("cook_type", "sizzle") if state.current_dish else None

        # 1. Background image (Clean kitchen plate)
        surface.blit(self.bg_empty, (0, 0))

        # 2. Tokyo Street Neon Window Ambience
        self._render_window_ambience(surface)

        # 3. Ambient Lantern Light Glows with gentle swaying
        self._render_lantern_glows(surface)

        # 4. Rain streaks outside the window
        particles.draw_rain(surface)

        # 5. Animated Transparent Chef (standing on floor behind counter)
        self._render_chef_character(surface, state, cook_type)

        # 5b. Foreground Kitchen Counter & Stove (stove in front, cleanly occludes lower body)
        if hasattr(self, "fg_counter") and self.fg_counter:
            surface.blit(self.fg_counter, (0, 505))

        # 6. Plated Counter Dish Display (Shows current dish on wooden counter)
        self._render_counter_dish(surface, state)

        # 7. Steam & Cooking Flame Particles (custom by cook_type)
        particles.draw_steam(surface)

        # 8. Header Bar (Status, Level, Music, Visualizer)
        self._render_header(surface, state, dt)

        # 9. Render 4 Dynamic Cards
        self._render_card_cooking(surface, state, dt)
        self._render_card_queue(surface, state)
        self._render_card_chat(surface, state)
        self._render_card_leaderboard(surface, state)

        # 10. Bottom Command Bar
        self._render_bottom_command_bar(surface)

        # 11. Floating VFX Particles (Hearts, Sparkles, Confetti)
        particles.draw_fx(surface)

        # 12. Chat prompt if active
        if input_state and input_state.get("active"):
            self._render_chat_input(surface, input_state)

    def _render_window_ambience(self, surface):
        """Subtle ambient lighting through the rain-streaked window from Tokyo neon signs."""
        # 1. Vertical Red Ramen Neon Sign at (305, 290)
        red_pulse = 0.75 + 0.25 * math.sin(self.anim_timer * 3.2)
        r_w = int(70 * red_pulse)
        r_surf = pygame.transform.smoothscale(self.neon_red, (r_w, r_w))
        surface.blit(r_surf, (305 - r_w // 2, 290 - r_w // 2), special_flags=pygame.BLEND_ADD)

        # 2. Cyan Ramen Bowl Neon Sign at (525, 305)
        cyan_pulse = 0.8 + 0.2 * math.sin(self.anim_timer * 2.4 + 1.2)
        c_w = int(60 * cyan_pulse)
        c_surf = pygame.transform.smoothscale(self.neon_cyan, (c_w, c_w))
        surface.blit(c_surf, (525 - c_w // 2, 305 - c_w // 2), special_flags=pygame.BLEND_ADD)

    def _render_lantern_glows(self, surface):
        for i, (lx, ly) in enumerate([(220, 130), (601, 179), (55, 590)]):
            sway_x = math.sin(self.anim_timer * 1.6 + i * 1.8) * 2.5
            sway_y = math.cos(self.anim_timer * 3.2 + i * 1.8) * 0.8
            flicker = 1.0 + math.sin(self.anim_timer * 4.8 + lx) * 0.08
            w = int(160 * flicker)
            h = int(160 * flicker)
            scaled = pygame.transform.smoothscale(self.lantern_glow, (w, h))
            surface.blit(scaled, (int(lx + sway_x - w // 2), int(ly + sway_y - h // 2)), special_flags=pygame.BLEND_ADD)

    def _render_chef_character(self, surface, state, cook_type):
        """
        Renders the chef character purely using frame-by-frame sprite animation.
        Zero rigging, zero skeletal animation, and zero procedural coordinate motion:
        movement is 100% driven by discrete frame swapping at steady anchors.
        """
        is_serving = state.last_served_dish is not None and (self.anim_timer - getattr(state, "serve_timestamp", 0) < 2.8)
        is_cooking = state.current_dish is not None

        # Position behind the stove/counter (chef stands on floor behind counter)
        base_x = 230
        base_y = 175

        # Select action state and playback frame rate
        if is_serving:
            action = "cheer"
            fps = 5.0
            pos = (base_x + 5, base_y - 15)
        elif is_cooking:
            if cook_type in ["sizzle", "pan_toss", "deepfry"]:
                action = "toss"
                fps = 5.0
                pos = (base_x - 15, base_y)
            elif cook_type in ["slice", "prep"]:
                action = "chop"
                fps = 5.0
                pos = (base_x - 10, base_y + 10)
            else:  # simmer / drink_shake / bake / general cook
                action = "stir"
                fps = 4.0
                pos = (base_x - 15, base_y)
        else:
            action = "idle"
            fps = 3.5
            pos = (base_x, base_y)

        # Pure frame-by-frame sprite cycle (no procedural translation offsets)
        frames = self.chef_animations.get(action, [])
        if frames:
            frame_idx = int(self.anim_timer * fps) % len(frames)
            surface.blit(frames[frame_idx], pos)
        elif getattr(self, f"sprite_{action}", None):
            surface.blit(getattr(self, f"sprite_{action}"), pos)
        elif self.sprite_idle:
            surface.blit(self.sprite_idle, (base_x, base_y))

    def _render_counter_dish(self, surface, state):
        """Displays the active or served dish plated on the front wooden counter bar."""
        dish = state.current_dish or state.last_served_dish
        if not dish:
            return

        icon = self.food_counter_icons.get(dish["key"])
        if not icon:
            return

        counter_x = 515
        counter_y = 705

        # 1. Soft wooden tray / plate shadow
        shadow_surf = pygame.Surface((90, 24), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (20, 12, 8, 140), (0, 0, 90, 24))
        surface.blit(shadow_surf, (counter_x - 7, counter_y + 54))

        # 2. Wooden serving plate rim
        plate_surf = pygame.Surface((86, 22), pygame.SRCALPHA)
        pygame.draw.ellipse(plate_surf, (190, 130, 60, 230), (0, 0, 86, 22))
        pygame.draw.ellipse(plate_surf, (130, 80, 30, 255), (0, 0, 86, 22), 2)
        surface.blit(plate_surf, (counter_x - 5, counter_y + 50))

        # 3. Floating dish breathing motion
        scale_mod = 1.0 + math.sin(self.anim_timer * 3.5) * 0.02
        sw = int(76 * scale_mod)
        sh = int(76 * scale_mod)
        scaled_icon = pygame.transform.smoothscale(icon, (sw, sh))
        surface.blit(scaled_icon, (counter_x, counter_y - (sh - 76)))

        # 4. Plated label badge
        tag_bg = pygame.Surface((120, 22), pygame.SRCALPHA)
        pygame.draw.rect(tag_bg, (15, 12, 10, 210), (0, 0, 120, 22), border_radius=4)
        pygame.draw.rect(tag_bg, COLOR_BORDER_AMBER, (0, 0, 120, 22), 1, border_radius=4)
        surface.blit(tag_bg, (counter_x - 22, counter_y + 74))
        
        name_trunc = dish["name"] if len(dish["name"]) <= 16 else dish["name"][:14] + ".."
        tw, _ = self.font_tiny.size(name_trunc)
        tag_w = 120
        self.draw_text(surface, name_trunc, self.font_tiny, COLOR_TEXT_GOLD,
                       (counter_x - 22 + (tag_w - tw) // 2, counter_y + 78), shadow=False)

    def _render_header(self, surface, state, dt):
        h_rect = (20, 20, 680, 115)
        self.draw_pixel_box(surface, h_rect, bg_color=(18, 14, 12, 235))

        # Main Title & Subtitle with high contrast
        self.draw_text(surface, "* COZY MIDNIGHT DINER *", self.font_title, COLOR_TEXT_GOLD, (38, 30))
        self.draw_text(surface, "24/7 INTERACTIVE COOKING LIVESTREAM", self.font_tiny, COLOR_TEXT_MAIN, (38, 52))

        # Diner Level & EXP bar
        self.draw_text(surface, f"DINER LEVEL: Lv.{state.diner_level}", self.font_header, COLOR_TEXT_MAIN, (38, 76))

        bar_w = 230
        bar_h = 16
        pygame.draw.rect(surface, (28, 20, 18), (38, 98, bar_w, bar_h))
        pygame.draw.rect(surface, COLOR_BORDER_AMBER, (38, 98, bar_w, bar_h), 1)

        exp_prog = min(1.0, state.exp / state.max_exp)
        fill_w = int((bar_w - 4) * exp_prog)
        if fill_w > 0:
            pygame.draw.rect(surface, COLOR_PROGRESS_BAR, (40, 100, fill_w, bar_h - 4))
            pygame.draw.rect(surface, COLOR_PROGRESS_GLOW, (40, 100, fill_w, 3))
        self.draw_text(surface, f"{state.exp} / {state.max_exp} XP", self.font_tiny, COLOR_TEXT_MAIN, (50, 100), shadow=False)

        # Now Playing Track
        self.draw_text(surface, "♫ NOW PLAYING:", self.font_tiny, COLOR_TEXT_GOLD, (300, 76))
        self.draw_text(surface, state.now_playing, self.font_subtext, COLOR_TEXT_MAIN, (300, 96))

        # Audio Visualizer Bars
        for i, val in enumerate(state.vis_bars):
            h = int(val * 34)
            x = 590 + i * 10
            y = 115 - h
            col = COLOR_PROGRESS_GLOW if val > 0.65 else COLOR_TEXT_GOLD
            pygame.draw.rect(surface, col, (x, y, 7, h))

        # Red dot LIVE
        dot_alpha = int(140 + 115 * abs((self.live_blink_timer * 2.5) % 2.0 - 1.0))
        dot_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(dot_surf, (255, 40, 40, dot_alpha), (4, 4), 4)
        surface.blit(dot_surf, (644, 38))
        self.draw_text(surface, "LIVE", self.font_tiny, (255, 60, 60), (656, 34), shadow=False)

    def _render_card_cooking(self, surface, state, dt):
        box = (20, 830, 400, 160)
        self.draw_pixel_box(surface, box)

        dish = state.current_dish
        if dish:
            icon = self.food_icons.get(dish["key"])
            if icon:
                surface.blit(icon, (34, 846))

            self.draw_text(surface, "COOKING:", self.font_header, COLOR_TEXT_GOLD, (90, 846))

            # Dish Name & Ordering Viewer
            w1, _ = self.draw_text(surface, f"{dish['name']} for ", self.font_body, COLOR_TEXT_MAIN, (90, 868))
            self.draw_text(surface, dish["user"], self.font_body, COLOR_TEXT_PINK, (90 + w1, 868))

            # Progress Bar with animated sweep light
            prog = dish["progress"]
            bar_w = 300
            bar_h = 22
            bar_x = 36
            bar_y = 902
            pygame.draw.rect(surface, (25, 20, 22), (bar_x, bar_y, bar_w, bar_h))
            pygame.draw.rect(surface, COLOR_BORDER_AMBER, (bar_x, bar_y, bar_w, bar_h), 1)

            fill_w = int((bar_w - 4) * prog)
            bar_color = dish.get("theme_color", COLOR_PROGRESS_BAR)
            if fill_w > 0:
                pygame.draw.rect(surface, bar_color, (bar_x + 2, bar_y + 2, fill_w, bar_h - 4))
                pygame.draw.rect(surface, COLOR_PROGRESS_GLOW, (bar_x + 2, bar_y + 2, fill_w, 3))
                # Sweep shine
                self.sweep_pos = (self.sweep_pos + dt * 160) % max(1, bar_w)
                if self.sweep_pos < fill_w:
                    sweep_surf = pygame.Surface((12, bar_h - 4), pygame.SRCALPHA)
                    sweep_surf.fill((255, 255, 255, 90))
                    surface.blit(sweep_surf, (bar_x + 2 + int(self.sweep_pos), bar_y + 2))

            pct_str = f"{int(prog * 100)}%"
            self.draw_text(surface, pct_str, self.font_header, COLOR_TEXT_MAIN, (bar_x + bar_w + 10, bar_y + 3))

            # Subtext step description
            clean_step = dish["current_step"].replace("✦ ", "+ ")
            self.draw_text(surface, clean_step, self.font_subtext, COLOR_TEXT_GOLD, (36, 946))

            # Cheer count
            if dish["compliments"] > 0:
                self.draw_text(surface, f"♥ x{dish['compliments']}", self.font_badge, COLOR_TEXT_PINK, (340, 846))
        else:
            self.draw_text(surface, "Chef is preparing fresh ingredients...", self.font_body, COLOR_TEXT_MUTED, (44, 880))
            self.draw_text(surface, "Type !cook [dish] to order delicious food!", self.font_subtext, COLOR_TEXT_GOLD, (44, 915))

    def _render_card_queue(self, surface, state):
        box = (435, 830, 265, 160)
        self.draw_pixel_box(surface, box)

        self.draw_text(surface, "📋 ORDER QUEUE", self.font_header, COLOR_TEXT_GOLD, (450, 846))

        start_y = 878
        for i in range(3):
            y = start_y + i * 26
            if i < len(state.order_queue):
                item = state.order_queue[i]
                self.draw_text(surface, f"{i+1}. {item['user']}", self.font_chat_user, COLOR_TEXT_MAIN, (450, y))
                self.draw_text(surface, "PENDING", self.font_badge, COLOR_TEXT_CYAN, (628, y + 2))
            else:
                self.draw_text(surface, f"{i+1}. ---", self.font_chat_text, (75, 80, 85), (450, y))

        self.draw_text(surface, f"QUEUE SIZE: {len(state.order_queue)}", self.font_badge, COLOR_TEXT_MUTED, (450, 965))

    def _render_card_chat(self, surface, state):
        box = (20, 1005, 400, 195)
        self.draw_pixel_box(surface, box)

        self.draw_text(surface, "💬 LIVE CHAT", self.font_header, COLOR_TEXT_CYAN, (36, 1020))

        start_y = 1048
        line_spacing = 28
        for i, msg in enumerate(state.recent_chats[-5:]):
            y = start_y + i * line_spacing
            u_str = f"{msg['user']}: "
            w, _ = self.draw_text(surface, u_str, self.font_chat_user, msg["color"], (36, y))
            clean_text = msg["text"].replace("🍳", "").replace("💖", "♥").replace("❤️", "♥").replace("✨", "*")
            self.draw_text(surface, clean_text, self.font_chat_text, COLOR_TEXT_MAIN, (36 + w, y))

    def _render_card_leaderboard(self, surface, state):
        box = (435, 1005, 265, 195)
        self.draw_pixel_box(surface, box)

        self.draw_text(surface, "👑 TOP CHEFS", self.font_header, COLOR_TEXT_GOLD, (450, 1020))

        coin_img = self.ui_icons.get("coin")
        coin_scaled = pygame.transform.scale(coin_img, (16, 16)) if coin_img else None

        start_y = 1056
        row_spacing = 42
        rank_colors = [COLOR_TEXT_GOLD, (215, 220, 230), (220, 150, 100)]
        for i, item in enumerate(state.leaderboard[:3]):
            y = start_y + i * row_spacing
            rc = rank_colors[i] if i < len(rank_colors) else COLOR_TEXT_MAIN
            self.draw_text(surface, f"{i+1}.", self.font_header, rc, (450, y))
            self.draw_text(surface, item["user"], self.font_body, COLOR_TEXT_MAIN, (476, y - 1))

            if coin_scaled:
                surface.blit(coin_scaled, (615, y))
            self.draw_text(surface, str(item["coins"]), self.font_badge, COLOR_TEXT_GOLD, (638, y + 1))

    def _render_bottom_command_bar(self, surface):
        box = (20, 1215, 680, 48)
        self.draw_pixel_box(surface, box, bg_color=(15, 12, 10, 240))

        cmd_str = "!cook [dish]   |   !yum   |   !menu   |   !tip"
        tw, _ = self.font_header.size(cmd_str)
        self.draw_text(surface, cmd_str, self.font_header, COLOR_TEXT_GOLD,
                       (CANVAS_WIDTH // 2 - tw // 2, 1224))

        sub_str = "Type in YouTube Live Chat to order & cheer!"
        sw, _ = self.font_tiny.size(sub_str)
        self.draw_text(surface, sub_str, self.font_tiny, COLOR_TEXT_MUTED,
                       (CANVAS_WIDTH // 2 - sw // 2, 1245))

    def _render_chat_input(self, surface, input_state):
        prompt_rect = (50, 1150, 620, 46)
        pygame.draw.rect(surface, (10, 15, 22), prompt_rect)
        pygame.draw.rect(surface, COLOR_PROGRESS_GLOW, prompt_rect, 2)
        txt = f"Type command: {input_state.get('text', '')}_"
        self.draw_text(surface, txt, self.font_body, COLOR_TEXT_GOLD, (65, 1164))

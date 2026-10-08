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
        bg_clean_path = os.path.join(BG_DIR, "diner_bg_clean.png")
        if os.path.exists(bg_clean_path):
            surf = pygame.image.load(bg_clean_path)
            self.bg_clean = surf.convert() if has_display else surf
        else:
            surf = pygame.image.load(os.path.join(BG_DIR, "full_reference_720x1280.png"))
            self.bg_clean = surf.convert() if has_display else surf

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
        for action in ["idle", "walk", "run", "jump", "attack", "toss", "stir", "chop", "cheer"]:
            act_dir = os.path.join(anim_dir, action)
            self.chef_animations[action] = []
            if os.path.exists(act_dir):
                for i in range(16):
                    fpath = os.path.join(act_dir, f"frame_{i}.png")
                    if os.path.exists(fpath):
                        img = pygame.image.load(fpath)
                        if has_display: img = img.convert_alpha()
                        self.chef_animations[action].append(img)

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

        # 5. Maneki-Neko (Lucky Cat) Waving Paw Animation
        self._render_lucky_cat(surface)

        # 6. Chef Cat Living Animation (Natural Blinking, Smiling Expressions)
        self._render_chef_character(surface, state)

        # 7. Plated Food Display (When a dish other than signature ramen is active)
        self._render_counter_dish(surface, state)

        # 8. Steam & Broth Particles
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
        """Animates the lucky waving cat paw on the front counter."""
        if self.neko_paw:
            paw_angle = math.sin(self.anim_timer * 2.8) * 7.5
            rot_paw = pygame.transform.rotate(self.neko_paw, paw_angle)
            surface.blit(rot_paw, (644, 562))

    def _render_chef_character(self, surface, state):
        """
        Renders living facial expressions for the chef cat:
        - When praised/tipped or serving dish: Happy anime smiling eyes (^ ^) with rosy blush
        - While idle/cooking: Natural blinking every ~4 seconds
        """
        is_serving = state.last_served_dish is not None and (self.anim_timer - getattr(state, "serve_timestamp", 0) < 2.5)
        has_cheer = state.current_dish and state.current_dish.get("compliments", 0) > 0

        if is_serving or has_cheer:
            if self.happy_overlay:
                surface.blit(self.happy_overlay, (0, 0))
        else:
            # Natural blink every 4.2s for 0.16s
            if self.blink_overlay and (self.anim_timer % 4.2) < 0.16:
                surface.blit(self.blink_overlay, (0, 0))

    def _render_counter_dish(self, surface, state):
        """
        When cooking a dish other than the default signature ramen (e.g. Pizza, Burger, Sushi),
        renders the plated dish badge on the wooden counter tray.
        """
        dish = state.current_dish or state.last_served_dish
        if not dish or dish.get("key") == "ramen":
            return

        icon = self.food_counter_icons.get(dish["key"])
        if not icon:
            return

        counter_x = 485
        counter_y = 690

        # Gentle floating breathing motion
        scale_mod = 1.0 + math.sin(self.anim_timer * 3.2) * 0.03
        sw = int(72 * scale_mod)
        sh = int(72 * scale_mod)
        scaled_icon = pygame.transform.smoothscale(icon, (sw, sh))
        surface.blit(scaled_icon, (counter_x - sw // 2, counter_y - sh // 2))

        # Plated dish tag badge
        tag_bg = pygame.Surface((130, 22), pygame.SRCALPHA)
        pygame.draw.rect(tag_bg, (18, 14, 12, 215), (0, 0, 130, 22), border_radius=4)
        pygame.draw.rect(tag_bg, COLOR_BORDER_AMBER, (0, 0, 130, 22), 1, border_radius=4)
        surface.blit(tag_bg, (counter_x - 65, counter_y + 44))

        d_name = dish["name"] if len(dish["name"]) <= 16 else dish["name"][:14] + ".."
        tw, _ = self.font_tiny.size(d_name)
        self.draw_text(surface, d_name, self.font_tiny, COLOR_TEXT_GOLD,
                       (counter_x - tw // 2, counter_y + 48), shadow=False)

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

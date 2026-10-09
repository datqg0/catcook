"""
Advanced Particle Effects Engine for Cozy Midnight Diner.
Custom cooking particles tailored per dish type: Sizzle sparks, Broth bubbles,
Steam basket billows, Ice chill sparkle, Confetti celebration, and Ambient Lighting.
"""
import random
import math
import pygame


class SteamParticle:
    def __init__(self, x, y, size_range=(3, 8), color=(235, 230, 225), speed_mult=1.0):
        self.x = x + random.uniform(-14, 14)
        self.y = y + random.uniform(-4, 4)
        self.vx = random.uniform(-0.35, 0.35)
        self.vy = random.uniform(-1.0, -1.8) * speed_mult
        self.size = random.uniform(size_range[0], size_range[1])
        self.max_size = self.size * random.uniform(2.5, 3.8)
        self.alpha = random.uniform(120, 180)
        self.lifetime = random.uniform(1.6, 2.6)
        self.age = 0.0
        self.color = color

    def update(self, dt):
        self.age += dt
        progress = self.age / self.lifetime
        self.x += self.vx + math.sin(self.age * 2.5) * 0.25
        self.y += self.vy
        self.current_size = self.size + (self.max_size - self.size) * progress
        self.current_alpha = max(0, int(self.alpha * (1.0 - progress)))
        return self.age < self.lifetime

    def draw(self, surface):
        if self.current_alpha <= 0:
            return
        r = int(self.current_size)
        temp_surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        c = (self.color[0], self.color[1], self.color[2], self.current_alpha)
        pygame.draw.circle(temp_surf, c, (r + 1, r + 1), r)
        surface.blit(temp_surf, (int(self.x - r), int(self.y - r)))


class SizzleSpark:
    """Juicy sizzling sparks for grilled meats, burgers, and steak."""
    def __init__(self, x, y):
        self.x = x + random.uniform(-20, 20)
        self.y = y + random.uniform(-5, 5)
        angle = random.uniform(-math.pi * 0.8, -math.pi * 0.2)
        speed = random.uniform(40, 110)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.lifetime = random.uniform(0.3, 0.7)
        self.age = 0.0
        self.color = random.choice([
            (255, 230, 100), (255, 160, 40), (255, 90, 20), (255, 255, 180)
        ])

    def update(self, dt):
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 80 * dt  # gravity
        return self.age < self.lifetime

    def draw(self, surface):
        alpha = max(0, int(255 * (1.0 - (self.age / self.lifetime))))
        s = pygame.Surface((3, 3), pygame.SRCALPHA)
        s.fill((*self.color, alpha))
        surface.blit(s, (int(self.x), int(self.y)))


class BrothBubble:
    """Simmering broth bubbles popping on soup surface."""
    def __init__(self, x, y):
        self.x = x + random.uniform(-25, 25)
        self.y = y + random.uniform(-8, 8)
        self.lifetime = random.uniform(0.4, 0.9)
        self.age = 0.0
        self.max_r = random.uniform(2.5, 5.0)

    def update(self, dt):
        self.age += dt
        return self.age < self.lifetime

    def draw(self, surface):
        progress = self.age / self.lifetime
        r = int(self.max_r * math.sin(progress * math.pi))
        if r > 0:
            s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 235, 190, 190), (r + 1, r + 1), r, 1)
            pygame.draw.circle(s, (255, 255, 240, 120), (r, r), max(1, r - 1))
            surface.blit(s, (int(self.x - r), int(self.y - r)))


class IceChillSparkle:
    """Chilly cold sparkles for Boba and Iced Latte drinks."""
    def __init__(self, x, y):
        self.x = x + random.uniform(-18, 18)
        self.y = y + random.uniform(-15, 15)
        self.lifetime = random.uniform(0.6, 1.2)
        self.age = 0.0
        self.vx = random.uniform(-10, 10)
        self.vy = random.uniform(-20, -45)

    def update(self, dt):
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        return self.age < self.lifetime

    def draw(self, surface):
        alpha = max(0, int(220 * (1.0 - (self.age / self.lifetime))))
        s = pygame.Surface((4, 4), pygame.SRCALPHA)
        color = random.choice([(180, 240, 255), (220, 250, 255), (140, 210, 255)])
        s.fill((*color, alpha))
        surface.blit(s, (int(self.x), int(self.y)))


class RainDrop:
    def __init__(self, x_min=200, x_max=640, y_min=180, y_max=460):
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.reset(random_y=True)

    def reset(self, random_y=False):
        self.x = random.uniform(self.x_min, self.x_max)
        self.y = random.uniform(self.y_min, self.y_max) if random_y else self.y_min
        self.speed = random.uniform(210, 310)
        self.length = random.uniform(10, 18)
        self.alpha = random.randint(35, 95)

    def update(self, dt):
        self.y += self.speed * dt
        self.x += self.speed * 0.2 * dt
        if self.y > self.y_max or self.x > self.x_max:
            self.reset(random_y=False)

    def draw(self, surface):
        temp_surf = pygame.Surface((4, int(self.length) + 4), pygame.SRCALPHA)
        pygame.draw.line(temp_surf, (170, 220, 250, self.alpha), (1, 1), (3, int(self.length)), 1)
        surface.blit(temp_surf, (int(self.x), int(self.y)))


class FloatingHeart:
    def __init__(self, x, y, heart_img=None):
        self.x = x + random.uniform(-20, 20)
        self.y = y
        self.vy = random.uniform(-50, -90)
        self.lifetime = 2.2
        self.age = 0.0
        self.seed = random.uniform(0, 100)
        self.heart_img = heart_img
        self.target_size = random.randint(22, 30)

    def update(self, dt):
        self.age += dt
        self.y += self.vy * dt
        self.x += math.sin(self.age * 4.5 + self.seed) * 1.8
        return self.age < self.lifetime

    def draw(self, surface):
        if not self.heart_img:
            return
        alpha = max(0, int(255 * (1.0 - (self.age / self.lifetime))))
        scaled = pygame.transform.scale(self.heart_img, (self.target_size, self.target_size))
        scaled.set_alpha(alpha)
        surface.blit(scaled, (int(self.x - self.target_size / 2), int(self.y - self.target_size / 2)))


class SparkleParticle:
    def __init__(self, x, y, sparkle_img=None):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(30, 85)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.lifetime = random.uniform(0.7, 1.4)
        self.age = 0.0
        self.sparkle_img = sparkle_img
        self.target_size = random.randint(18, 26)

    def update(self, dt):
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 15 * dt
        return self.age < self.lifetime

    def draw(self, surface):
        if not self.sparkle_img:
            return
        alpha = max(0, int(255 * (1.0 - (self.age / self.lifetime))))
        scaled = pygame.transform.scale(self.sparkle_img, (self.target_size, self.target_size))
        scaled.set_alpha(alpha)
        surface.blit(scaled, (int(self.x - self.target_size / 2), int(self.y - self.target_size / 2)))


class ConfettiPiece:
    """Festive confetti cascading down when Level Up or big tip occurs."""
    def __init__(self, x_max=720):
        self.x = random.uniform(20, x_max - 20)
        self.y = random.uniform(-40, -5)
        self.vy = random.uniform(80, 160)
        self.vx = random.uniform(-25, 25)
        self.color = random.choice([
            (255, 90, 90), (255, 210, 60), (70, 215, 255), (120, 240, 130),
            (255, 130, 200), (255, 175, 40)
        ])
        self.w = random.randint(4, 7)
        self.h = random.randint(3, 6)
        self.rot_speed = random.uniform(2.0, 7.0)
        self.age = 0.0
        self.lifetime = random.uniform(2.5, 4.0)

    def update(self, dt):
        self.age += dt
        self.y += self.vy * dt
        self.x += self.vx * dt + math.sin(self.age * 4.0) * 1.5
        return self.age < self.lifetime and self.y < 1280

    def draw(self, surface):
        scale = abs(math.cos(self.age * self.rot_speed))
        pw = max(1, int(self.w * scale))
        s = pygame.Surface((pw, self.h))
        s.fill(self.color)
        surface.blit(s, (int(self.x), int(self.y)))


class FireEmberParticle:
    """Rising glowing embers and heat sparks from cooking flames."""
    def __init__(self, x, y):
        self.x = x + random.uniform(-14, 14)
        self.y = y + random.uniform(-4, 4)
        angle = random.uniform(-math.pi * 0.85, -math.pi * 0.15)
        speed = random.uniform(35, 90)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.lifetime = random.uniform(0.4, 0.9)
        self.age = 0.0
        self.size = random.uniform(1.5, 3.2)
        self.color_stages = [
            (255, 250, 180),  # White-hot gold
            (255, 170, 40),   # Vibrant orange
            (230, 60, 20),    # Deep ember red
        ]

    def update(self, dt):
        self.age += dt
        self.x += self.vx * dt + math.sin(self.age * 9.0) * 0.6
        self.y += self.vy * dt
        self.vy -= 15 * dt  # slight thermal buoyancy
        return self.age < self.lifetime

    def draw(self, surface):
        progress = self.age / self.lifetime
        alpha = max(0, int(255 * (1.0 - progress)))
        if progress < 0.35:
            c = self.color_stages[0]
        elif progress < 0.7:
            c = self.color_stages[1]
        else:
            c = self.color_stages[2]
            
        r = int(max(1, self.size * (1.0 - progress * 0.5)))
        s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*c, alpha), (r + 1, r + 1), r)
        surface.blit(s, (int(self.x - r), int(self.y - r)), special_flags=pygame.BLEND_ADD)


class ParticleManager:
    def __init__(self, heart_img=None, sparkle_img=None):
        self.heart_img = heart_img
        self.sparkle_img = sparkle_img
        self.steams = []
        self.hearts = []
        self.sparkles = []
        self.sizzle_sparks = []
        self.broth_bubbles = []
        self.ice_sparkles = []
        self.fire_embers = []
        self.confetti = []
        self.raindrops = [RainDrop() for _ in range(40)]
        self.steam_timer = 0.0
        self.counter_steam_timer = 0.0
        self.coffee_steam_timer = 0.0

    def spawn_steam(self, x, y, size_range=(3, 8), color=(235, 230, 225)):
        self.steams.append(SteamParticle(x, y, size_range, color))

    def spawn_hearts(self, x, y, count=3):
        for _ in range(count):
            self.hearts.append(FloatingHeart(x, y, self.heart_img))

    def spawn_sparkles(self, x, y, count=12):
        for _ in range(count):
            self.sparkles.append(SparkleParticle(x, y, self.sparkle_img))

    def spawn_confetti(self, count=40):
        for _ in range(count):
            self.confetti.append(ConfettiPiece())

    def update(self, dt, current_cook_type=None, counter_dish_pos=None):
        # Regular ambient steam from kitchen pot and counter bowl
        self.steam_timer += dt
        if self.steam_timer > 0.12:
            self.steam_timer = 0.0
            # Soup pot on the left stove
            self.spawn_steam(230, 530, size_range=(4, 9), color=(245, 235, 220))
            self.broth_bubbles.append(BrothBubble(230, 595))
            # Hot bowl on the wooden tray
            self.spawn_steam(480, 620, size_range=(3, 7), color=(250, 245, 240))

            # Custom cooking particle by dish type
            if current_cook_type in ["sizzle", "pan_toss", "deepfry"]:
                for _ in range(random.randint(1, 2)):
                    self.sizzle_sparks.append(SizzleSpark(230, 560))
                # Rising fire embers from sizzling stove
                self.fire_embers.append(FireEmberParticle(226, 608))
            elif current_cook_type in ["simmer", "bake", "steam_basket"]:
                if random.random() < 0.65:
                    self.fire_embers.append(FireEmberParticle(226, 610))
                if current_cook_type == "bake":
                    self.fire_embers.append(FireEmberParticle(85, 575))
            elif current_cook_type in ["drink_shake", "bartender"]:
                if random.random() < 0.65:
                    self.ice_sparkles.append(IceChillSparkle(345 + random.randint(-35, 35), 540 + random.randint(-30, 30)))

        # Delicate aromatic steam from coffee machine
        self.coffee_steam_timer += dt
        if self.coffee_steam_timer > 0.32:
            self.coffee_steam_timer = 0.0
            self.spawn_steam(630, 584, size_range=(2, 4), color=(245, 240, 235))

        # Gentle aroma steam from served counter dish
        if counter_dish_pos:
            self.counter_steam_timer += dt
            if self.counter_steam_timer > 0.28:
                self.counter_steam_timer = 0.0
                cx, cy = counter_dish_pos
                self.spawn_steam(cx, cy, size_range=(2, 5), color=(250, 245, 240))

        # Update rain
        for r in self.raindrops:
            r.update(dt)

        # Update particle lists
        self.steams = [p for p in self.steams if p.update(dt)]
        self.hearts = [h for h in self.hearts if h.update(dt)]
        self.sparkles = [s for s in self.sparkles if s.update(dt)]
        self.sizzle_sparks = [s for s in self.sizzle_sparks if s.update(dt)]
        self.broth_bubbles = [b for b in self.broth_bubbles if b.update(dt)]
        self.ice_sparkles = [i for i in self.ice_sparkles if i.update(dt)]
        self.fire_embers = [e for e in self.fire_embers if e.update(dt)]
        self.confetti = [c for c in self.confetti if c.update(dt)]

    def draw_rain(self, surface):
        for r in self.raindrops:
            r.draw(surface)

    def draw_steam(self, surface):
        for s in self.steams:
            s.draw(surface)
        for b in self.broth_bubbles:
            b.draw(surface)
        for sp in self.sizzle_sparks:
            sp.draw(surface)
        for ic in self.ice_sparkles:
            ic.draw(surface)
        for fe in self.fire_embers:
            fe.draw(surface)

    def draw_fx(self, surface):
        for h in self.hearts:
            h.draw(surface)
        for sp in self.sparkles:
            sp.draw(surface)
        for cf in self.confetti:
            cf.draw(surface)

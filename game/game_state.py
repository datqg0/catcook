"""
Game state manager for Cozy Midnight Diner.
Handles order queue, cooking lifecycle, chat log, and leaderboards.
"""
import random
import math
from game.config import MENU_ITEMS, COLOR_TEXT_GREEN, COLOR_TEXT_PINK, COLOR_TEXT_CYAN, COLOR_TEXT_GOLD


class GameState:
    def __init__(self):
        self.diner_level = 27
        self.exp = 1250
        self.max_exp = 2000
        self.now_playing = "lofi hip hop radio [chill beats to cook/study to]"

        # Current dish being prepared
        self.current_dish = None
        self.last_served_dish = None

        # Order queue: list of dicts [{'user': str, 'key': str, 'name': str}]
        self.order_queue = []

        # Live chat history (up to 5 recent lines)
        self.recent_chats = []

        # Today's Top Chefs (Leaderboard)
        self.leaderboard = [
            {"user": "@RamenKing", "coins": 1500},
            {"user": "@SoupMaster", "coins": 1000},
            {"user": "@CozyCat", "coins": 750}
        ]

        # Visualizer animation state
        self.vis_timer = 0.0
        self.vis_bars = [0.4, 0.7, 0.5, 0.9, 0.8, 0.6, 0.3, 0.7]

        # Auto-idle chef mechanism
        self.idle_timer = 0.0
        self.elapsed_total = 0.0
        self.last_donate_timestamp = -999.0
        self.serve_timestamp = -999.0

        # Hook for particle callbacks
        self.on_cheer_callback = None
        self.on_complete_callback = None
        self.on_tip_callback = None
        self.on_levelup_callback = None

        # Pre-seed initial state for demonstration
        self._seed_initial_demo()

    def _seed_initial_demo(self):
        # Initial dish
        self.start_cooking("ramen", "@Sarah")
        if self.current_dish:
            self.current_dish["elapsed"] = self.current_dish["cook_time"] * 0.75

        # Initial queue with diverse dishes
        self.order_queue = [
            {"user": "@Alex", "key": "pizza", "name": "Pepperoni Pizza"},
            {"user": "@MochiBear", "key": "tacos", "name": "Birria Tacos"},
            {"user": "@NightOwl", "key": "boba", "name": "Boba Milk Tea"}
        ]

        # Initial chat messages
        initial_msgs = [
            ("@NoodleFan", "that looks amazing!", COLOR_TEXT_GREEN),
            ("@CozyCat", "add extra egg pls! 🍳", COLOR_TEXT_PINK),
            ("@RamenLover", "!cook ramen", COLOR_TEXT_CYAN),
            ("@ChillChef", "yesss lofi + ramen = perfect", COLOR_TEXT_GREEN),
            ("@Sarah", "omg thank you so much! 💖", COLOR_TEXT_GOLD)
        ]
        for user, text, color in initial_msgs:
            self.add_chat(user, text, color)

    def add_chat(self, user, text, color=None):
        if not color:
            colors = [COLOR_TEXT_GREEN, COLOR_TEXT_PINK, COLOR_TEXT_CYAN, COLOR_TEXT_GOLD]
            color = random.choice(colors)
        self.recent_chats.append({"user": user, "text": text, "color": color})
        if len(self.recent_chats) > 5:
            self.recent_chats.pop(0)

    def start_cooking(self, item_key, user):
        if item_key not in MENU_ITEMS:
            item_key = random.choice(list(MENU_ITEMS.keys()))
        data = MENU_ITEMS[item_key]
        self.current_dish = {
            "key": item_key,
            "name": data["name"],
            "user": user,
            "cook_time": data["cook_time"],
            "cook_type": data.get("cook_type", "sizzle"),
            "theme_color": data.get("theme_color", (255, 175, 60)),
            "elapsed": 0.0,
            "progress": 0.0,
            "xp": data["xp"],
            "coins": data["coins"],
            "steps": data["steps"],
            "current_step": data["steps"][0],
            "compliments": 0,
            "cheered_users": set()
        }

    def add_order(self, user, dish_query=""):
        # Normalize dish query
        matched_key = None
        q = dish_query.lower().strip()
        if q:
            for key, data in MENU_ITEMS.items():
                if key in q or data["name"].lower() in q:
                    matched_key = key
                    break
        if not matched_key:
            matched_key = random.choice(list(MENU_ITEMS.keys()))

        dish_name = MENU_ITEMS[matched_key]["name"]
        
        # Check if already in queue
        if any(item["user"].lower() == user.lower() for item in self.order_queue):
            self.add_chat("System", f"{user} already has a dish waiting in queue!", COLOR_TEXT_PINK)
            return False

        # Add to queue
        self.order_queue.append({
            "user": user,
            "key": matched_key,
            "name": dish_name
        })
        self.add_chat(user, f"!cook {dish_name}")
        return True

    def cheer(self, user):
        if not self.current_dish:
            self.add_chat(user, "!yum (No dish is being cooked right now!)")
            return False

        if user in self.current_dish["cheered_users"]:
            self.add_chat(user, "!yum (Already cheered for this dish!)")
            return False

        self.current_dish["cheered_users"].add(user)
        self.current_dish["compliments"] += 1
        self.add_exp(15)
        self.add_chat(user, "!yum ❤️ Delicious vibes!", COLOR_TEXT_PINK)

        if self.on_cheer_callback:
            self.on_cheer_callback()
        return True

    def tip(self, user, amount=100):
        self.last_donate_timestamp = getattr(self, "elapsed_total", 0.0)
        self.add_exp(amount // 2)
        # Update user in leaderboard
        found = False
        for item in self.leaderboard:
            if item["user"].lower() == user.lower():
                item["coins"] += amount
                found = True
                break
        if not found:
            self.leaderboard.append({"user": user, "coins": amount})
        
        # Sort leaderboard
        self.leaderboard.sort(key=lambda x: x["coins"], reverse=True)
        if len(self.leaderboard) > 50:
            self.leaderboard = self.leaderboard[:50]

        self.add_chat(user, f"!tip {amount} coins! Thank you for supporting! ✨", COLOR_TEXT_GOLD)
        if self.on_tip_callback:
            self.on_tip_callback()
        return True

    def add_exp(self, amount):
        self.exp += amount
        if self.exp >= self.max_exp:
            self.exp -= self.max_exp
            self.diner_level += 1
            self.max_exp = int(self.max_exp * 1.25)
            self.add_chat("System", f"🎉 LEVEL UP! Diner reached Lv. {self.diner_level}!", COLOR_TEXT_GOLD)
            if self.on_levelup_callback:
                self.on_levelup_callback()

    def update(self, dt):
        self.elapsed_total = getattr(self, "elapsed_total", 0.0) + dt
        # Update music visualizer bars
        self.vis_timer += dt
        for i in range(len(self.vis_bars)):
            # Combine sine frequencies for realistic audio bounce
            val = (math.sin(self.vis_timer * (4.0 + i * 1.2) + i) * 0.45 +
                   math.cos(self.vis_timer * 6.5 + i * 2) * 0.35 + 0.5)
            self.vis_bars[i] = max(0.15, min(1.0, val))

        # Handle cooking progress
        if self.current_dish:
            self.current_dish["elapsed"] += dt
            prog = min(1.0, self.current_dish["elapsed"] / self.current_dish["cook_time"])
            self.current_dish["progress"] = prog

            # Update step message based on progress
            steps = self.current_dish["steps"]
            step_idx = min(len(steps) - 1, int(prog * len(steps)))
            self.current_dish["current_step"] = steps[step_idx]

            # Dish completed
            if prog >= 1.0:
                self._finish_cooking()
        else:
            # Check queue or auto-cook
            if self.order_queue:
                next_order = self.order_queue.pop(0)
                self.start_cooking(next_order["key"], next_order["user"])
            else:
                self.idle_timer += dt
                if self.idle_timer > 3.0:
                    self.idle_timer = 0.0
                    walk_ins = ["@MochiCat", "@RainyWanderer", "@ChillGuest", "@NightOwl", "@Passerby"]
                    random_guest = random.choice(walk_ins)
                    random_key = random.choice(list(MENU_ITEMS.keys()))
                    self.start_cooking(random_key, random_guest)

    def _finish_cooking(self):
        dish = self.current_dish
        self.last_served_dish = dish
        self.serve_timestamp = getattr(self, "elapsed_total", 0.0)
        self.add_exp(dish["xp"])
        self.add_chat("Chef", f"🍲 Served hot {dish['name']} for {dish['user']}!", COLOR_TEXT_GOLD)
        
        # Reward coins to the ordering user in leaderboard
        user = dish["user"]
        for item in self.leaderboard:
            if item["user"].lower() == user.lower():
                item["coins"] += dish["coins"]
                break

        if self.on_complete_callback:
            self.on_complete_callback()

        self.current_dish = None

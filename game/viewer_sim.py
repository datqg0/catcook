"""
Realistic Viewer Interaction Simulator for Cozy Midnight Diner.
Simulates natural YouTube chatters to keep the 24/7 livestream lively and warm.
Can be toggled on/off at runtime or via config.
"""
import random
from game.config import MENU_ITEMS


VIEWER_NAMES = [
    "@TokyoDrifter", "@RainyCat", "@StarGazer", "@MatchaMoments",
    "@PixelFoodie", "@NightOwlChef", "@ChaiLover", "@Luna_Boba",
    "@CoffeeAndCode", "@VelvetPaws", "@CozyGamer", "@SojuNights",
    "@SunnySideUp", "@NekoMaster", "@Wanderlust22", "@LofiStudyCafe"
]

CASUAL_CHATS = [
    "smells so amazing in here ✨",
    "lofi beats are so relaxing tonight 🎧",
    "chef cat is working so hard! 🐾",
    "saving this stream to study with 📖",
    "my mouth is watering haha 🤤",
    "best midnight hangout on YouTube ❤️",
    "hope everyone is having a peaceful night 🌙",
    "can't decide between ramen and pizza!",
    "vibes are immaculate ✨",
    "extra cheese please! 🧀",
    "greetings from Tokyo! 🗼",
    "stay cozy everyone ☕"
]


class ViewerSimulator:
    def __init__(self, command_dispatcher, enabled=True, min_interval=14.0, max_interval=28.0):
        self.dispatcher = command_dispatcher
        self.enabled = enabled
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.timer = 0.0
        self.next_action_time = random.uniform(5.0, 10.0)

    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled

    def update(self, dt):
        if not self.enabled:
            return

        self.timer += dt
        if self.timer >= self.next_action_time:
            self.timer = 0.0
            self.next_action_time = random.uniform(self.min_interval, self.max_interval)
            self._perform_random_action()

    def _perform_random_action(self):
        user = random.choice(VIEWER_NAMES)
        r = random.random()

        if r < 0.40:
            # Order a dish
            dish_key = random.choice(list(MENU_ITEMS.keys()))
            dish_name = MENU_ITEMS[dish_key]["name"]
            self.dispatcher.dispatch(user, f"!cook {dish_name}")

        elif r < 0.65:
            # Cheer with !yum
            self.dispatcher.dispatch(user, "!yum")

        elif r < 0.85:
            # Casual chat message
            chat_msg = random.choice(CASUAL_CHATS)
            self.dispatcher.dispatch(user, chat_msg)

        else:
            # Tip / donate
            tip_amount = random.choice([50, 100, 150, 200])
            self.dispatcher.dispatch(user, f"!tip {tip_amount}")

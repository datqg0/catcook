"""
Configuration and constants for Cozy Midnight Diner.
Includes 16 globally loved comfort dishes with custom cooking animations and behaviors.
"""
import os

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")
FOODS_DIR = os.path.join(ASSETS_DIR, "foods")
UI_DIR = os.path.join(ASSETS_DIR, "ui")
BG_DIR = os.path.join(ASSETS_DIR, "backgrounds")
ANIM_DIR = os.path.join(ASSETS_DIR, "animations")

# Target canvas resolution (YouTube Vertical 9:16)
CANVAS_WIDTH = 720
CANVAS_HEIGHT = 1280
FPS = 30

# Window display resolution (default 540x960 for comfortable PC monitoring)
WINDOW_SCALE = 0.75
WINDOW_WIDTH = int(CANVAS_WIDTH * WINDOW_SCALE)
WINDOW_HEIGHT = int(CANVAS_HEIGHT * WINDOW_SCALE)

# High-contrast readable color palette (optimized for stream visibility)
COLOR_BG_DARK = (13, 19, 26)
COLOR_CARD_BG = (15, 20, 28, 240)
COLOR_TEXT_MAIN = (255, 252, 245)
COLOR_TEXT_GOLD = (255, 218, 85)
COLOR_TEXT_ORANGE = (255, 155, 65)
COLOR_TEXT_CYAN = (95, 225, 255)
COLOR_TEXT_GREEN = (95, 245, 160)
COLOR_TEXT_PINK = (255, 150, 190)
COLOR_TEXT_MUTED = (195, 185, 175)
COLOR_BORDER_AMBER = (195, 130, 60)
COLOR_PROGRESS_BAR = (245, 110, 25)
COLOR_PROGRESS_GLOW = (255, 175, 60)

# Full Menu: 16 Diverse Comfort Foods (Cook times balanced for 30s -> 45s interactive stream distribution)
MENU_ITEMS = {
    "ramen": {
        "name": "Tonkotsu Ramen",
        "icon": "ramen.png",
        "cook_time": 44.0,
        "cook_type": "simmer",
        "theme_color": (255, 190, 60),
        "xp": 35,
        "coins": 20,
        "steps": [
            "✦ Simmering rich pork bone broth for 12 hours...",
            "✦ Boiling handmade alkaline noodles to al dente...",
            "✦ Torching tender chashu slices with sweet shoyu...",
            "✦ Plating with seasoned ramen egg, nori & scallions!"
        ]
    },
    "pizza": {
        "name": "Pepperoni Pizza",
        "icon": "pizza.png",
        "cook_time": 42.0,
        "cook_type": "bake",
        "theme_color": (255, 95, 45),
        "xp": 30,
        "coins": 18,
        "steps": [
            "✦ Hand-stretching fresh artisan sourdough...",
            "✦ Spreading crushed San Marzano tomato marinara...",
            "✦ Layering whole-milk mozzarella & crispy pepperoni...",
            "✦ Stone-oven baked until bubbly golden cheese pull!"
        ]
    },
    "burger": {
        "name": "Smash Burger",
        "icon": "burger.png",
        "cook_time": 38.0,
        "cook_type": "sizzle",
        "theme_color": (255, 160, 50),
        "xp": 28,
        "coins": 15,
        "steps": [
            "✦ Searing prime beef on screaming hot flat-top...",
            "✦ Smashing thin for irresistible crispy lacy edges...",
            "✦ Melting two slices of creamy American cheese...",
            "✦ Stacking on toasted brioche with signature sauce!"
        ]
    },
    "sushi": {
        "name": "Salmon Sushi",
        "icon": "sushi.png",
        "cook_time": 36.0,
        "cook_type": "slice",
        "theme_color": (255, 120, 90),
        "xp": 32,
        "coins": 22,
        "steps": [
            "✦ Fanning seasoned Koshihikari sushi rice to temp...",
            "✦ Master-slicing fresh Norwegian salmon nigiri...",
            "✦ Dabbing authentic Shizuoka wasabi with precision...",
            "✦ Brushing aged nikiri soy sauce on glistening fish!"
        ]
    },
    "pancakes": {
        "name": "Fluffy Pancakes",
        "icon": "pancakes.png",
        "cook_time": 34.0,
        "cook_type": "pan_toss",
        "theme_color": (255, 210, 100),
        "xp": 25,
        "coins": 12,
        "steps": [
            "✦ Whisking fluffy soufflé batter with sweet vanilla...",
            "✦ Golden griddled on low gentle heat until puffy...",
            "✦ Stacking sky-high with melting Hokkaido butter...",
            "✦ Drizzling pure amber Canadian maple syrup!"
        ]
    },
    "boba": {
        "name": "Boba Milk Tea",
        "icon": "boba.png",
        "cook_time": 30.0,
        "cook_type": "drink_shake",
        "theme_color": (210, 160, 120),
        "xp": 22,
        "coins": 10,
        "steps": [
            "✦ Cooking brown sugar boba pearls to chewy perfection...",
            "✦ Brewing bold Assam black tea with rich creamer...",
            "✦ Shaking vigorously over hand-cracked ice cubes...",
            "✦ Sealed tight with jumbo straw, ready to sip!"
        ]
    },
    "chicken": {
        "name": "Fried Chicken",
        "icon": "chicken.png",
        "cook_time": 40.0,
        "cook_type": "deepfry",
        "theme_color": (255, 140, 30),
        "xp": 30,
        "coins": 18,
        "steps": [
            "✦ Marinating drumstick in savory buttermilk & herbs...",
            "✦ Double dredging in secret 11-spice crispy coating...",
            "✦ Deep frying until golden shattered-glass crunch...",
            "✦ Glazing with sticky sweet Korean honey garlic!"
        ]
    },
    "steak": {
        "name": "Ribeye Steak",
        "icon": "steak.png",
        "cook_time": 45.0,
        "cook_type": "sizzle",
        "theme_color": (230, 70, 70),
        "xp": 45,
        "coins": 30,
        "steps": [
            "✦ Seasoning prime bone-in ribeye with flaky sea salt...",
            "✦ Searing hard on blazing cast iron skillet...",
            "✦ Basting continuously with brown butter & rosemary...",
            "✦ Resting to juicy medium-rare perfection!"
        ]
    },
    "tacos": {
        "name": "Birria Tacos",
        "icon": "tacos.png",
        "cook_time": 38.0,
        "cook_type": "sizzle",
        "theme_color": (245, 115, 40),
        "xp": 32,
        "coins": 18,
        "steps": [
            "✦ Dipping corn tortillas in rich spiced chili consommé...",
            "✦ Griddling crispy with shredded slow-cooked beef...",
            "✦ Melting Oaxaca cheese with sweet diced onions...",
            "✦ Served with hot dipping broth & fresh lime wedge!"
        ]
    },
    "dumplings": {
        "name": "Dim Sum Dumplings",
        "icon": "dumplings.png",
        "cook_time": 35.0,
        "cook_type": "steam_basket",
        "theme_color": (240, 220, 160),
        "xp": 28,
        "coins": 16,
        "steps": [
            "✦ Hand-pleating thin dough around juicy pork & shrimp...",
            "✦ Arranging carefully in fragrant cedar bamboo baskets...",
            "✦ Steaming over boiling aromatics until translucent...",
            "✦ Served steaming hot with ginger black vinegar dip!"
        ]
    },
    "carbonara": {
        "name": "Creamy Carbonara",
        "icon": "carbonara.png",
        "cook_time": 42.0,
        "cook_type": "pan_toss",
        "theme_color": (255, 205, 80),
        "xp": 32,
        "coins": 20,
        "steps": [
            "✦ Crisping savory guanciale in its own rich juices...",
            "✦ Whisking farm egg yolks with aged Pecorino Romano...",
            "✦ Tossing al dente spaghetti to create silky emulsion...",
            "✦ Finishing with freshly cracked tellicherry black pepper!"
        ]
    },
    "hotdog": {
        "name": "NYC Loaded Hot Dog",
        "icon": "hotdog.png",
        "cook_time": 33.0,
        "cook_type": "sizzle",
        "theme_color": (255, 100, 50),
        "xp": 24,
        "coins": 12,
        "steps": [
            "✦ Grilling all-beef frankfurter until blistered snap...",
            "✦ Steaming potato brioche bun pillow-soft...",
            "✦ Layering sauerkraut, sweet relish & melted cheddar...",
            "✦ Zig-zagging tangy deli mustard across the top!"
        ]
    },
    "donut": {
        "name": "Strawberry Donut",
        "icon": "donut.png",
        "cook_time": 30.0,
        "cook_type": "bake",
        "theme_color": (255, 120, 170),
        "xp": 22,
        "coins": 12,
        "steps": [
            "✦ Proofing pillowy brioche donut dough to airy perfection...",
            "✦ Frying in clean oil until golden with a blonde ring...",
            "✦ Dipping in glossy pink strawberry sugar glaze...",
            "✦ Showering generously with rainbow confetti sprinkles!"
        ]
    },
    "waffles": {
        "name": "Belgian Waffles",
        "icon": "waffles.png",
        "cook_time": 36.0,
        "cook_type": "bake",
        "theme_color": (240, 180, 80),
        "xp": 26,
        "coins": 14,
        "steps": [
            "✦ Folding pearl sugar into rich yeasted brioche batter...",
            "✦ Pressing deep into sizzling cast iron waffle irons...",
            "✦ Caramelizing sugar pearls to sweet crunchy pockets...",
            "✦ Pillowed with vanilla whipped cream & fresh berries!"
        ]
    },
    "curry": {
        "name": "Katsu Curry Bowl",
        "icon": "curry.png",
        "cook_time": 44.0,
        "cook_type": "simmer",
        "theme_color": (215, 140, 45),
        "xp": 36,
        "coins": 24,
        "steps": [
            "✦ Simmering fragrant spiced golden Japanese curry roux...",
            "✦ Frying panko pork cutlet until golden shatter crunch...",
            "✦ Slicing juicy katsu and fanning over steaming rice...",
            "✦ Ladling velvety curry sauce with sweet pickled fukujinzuke!"
        ]
    },
    "latte": {
        "name": "Iced Caramel Latte",
        "icon": "latte.png",
        "cook_time": 32.0,
        "cook_type": "drink_shake",
        "theme_color": (210, 150, 95),
        "xp": 22,
        "coins": 10,
        "steps": [
            "✦ Pulling a double shot of dark nutty espresso...",
            "✦ Swirling rich sea salt caramel around chilled glass...",
            "✦ Layering cold whole milk over crystalline ice...",
            "✦ Topped with whipped cream & dark caramel drizzle!"
        ]
    }
}

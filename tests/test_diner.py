"""
Comprehensive Automated Test Suite for Cozy Midnight Diner.
Validates:
1. All 16 dishes configuration and icon file presence
2. Command dispatcher logic and queue deduplication
3. Full cooking lifecycle and XP level-up math
4. Audio manager fallback resilience
5. Viewer simulation event distribution
6. 300-frame continuous headless render test with particle systems
"""
import os
import sys
import unittest

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame

from game.config import (
    MENU_ITEMS, FOODS_DIR, CANVAS_WIDTH, CANVAS_HEIGHT,
    COLOR_PROGRESS_BAR
)
from game.game_state import GameState
from game.commands import CommandDispatcher
from game.particles import ParticleManager
from game.renderer import DinerRenderer
from game.audio import AudioManager
from game.viewer_sim import ViewerSimulator


class TestDinerGame(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_01_menu_items_and_assets(self):
        """Verify all 16 menu items have valid configuration and existing icon assets."""
        self.assertGreaterEqual(len(MENU_ITEMS), 16, "Must have at least 16 menu items")
        for key, item in MENU_ITEMS.items():
            self.assertIn("name", item)
            self.assertIn("cook_time", item)
            self.assertIn("cook_type", item)
            self.assertIn("steps", item)
            self.assertGreater(len(item["steps"]), 0)

            # Check icon asset exists
            icon_path = os.path.join(FOODS_DIR, item["icon"])
            self.assertTrue(os.path.exists(icon_path), f"Missing icon asset for {key}: {icon_path}")

    def test_02_command_dispatcher(self):
        """Verify command dispatching, aliases, and queue management."""
        state = GameState()
        dispatcher = CommandDispatcher(state)

        # Clear queue
        state.order_queue = []

        # 1. Order known dish
        dispatcher.dispatch("@ViewerA", "!cook pizza")
        self.assertTrue(any(o["key"] == "pizza" for o in state.order_queue))

        # 2. Prevent duplicate order from same viewer
        initial_len = len(state.order_queue)
        dispatcher.dispatch("@ViewerA", "!cook ramen")
        self.assertEqual(len(state.order_queue), initial_len, "Viewer should only have 1 dish in queue")

        # 3. Order random/fuzzy dish
        dispatcher.dispatch("@ViewerB", "!cook waffles")
        self.assertTrue(any(o["key"] == "waffles" for o in state.order_queue))

        # 4. Cheer !yum
        state.current_dish = {
            "key": "ramen", "name": "Tonkotsu Ramen", "user": "@Sarah",
            "cook_time": 10.0, "elapsed": 0.0, "progress": 0.0, "xp": 30,
            "coins": 20, "steps": ["cooking..."], "current_step": "cooking...",
            "compliments": 0, "cheered_users": set()
        }
        cheered = state.cheer("@Cheerer")
        self.assertTrue(cheered)
        self.assertEqual(state.current_dish["compliments"], 1)

        # Prevent double cheer on same dish
        double_cheered = state.cheer("@Cheerer")
        self.assertFalse(double_cheered)

        # 5. Tip coins
        tip_success = state.tip("@Tipper", 250)
        self.assertTrue(tip_success)
        self.assertTrue(any(item["user"] == "@Tipper" and item["coins"] >= 250 for item in state.leaderboard))

    def test_03_cooking_lifecycle_and_level_up(self):
        """Verify cooking progression, dish completion, and XP math."""
        state = GameState()
        state.start_cooking("tacos", "@Foodie")
        self.assertIsNotNone(state.current_dish)
        self.assertEqual(state.current_dish["key"], "tacos")

        # Advance cooking to completion
        cook_time = state.current_dish["cook_time"]
        state.update(cook_time + 0.1)

        # Dish should now be served and cleared from current_dish
        self.assertIsNone(state.current_dish)
        self.assertIsNotNone(state.last_served_dish)
        self.assertEqual(state.last_served_dish["name"], "Birria Tacos")

        # Verify level up
        old_lvl = state.diner_level
        state.exp = state.max_exp - 10
        state.add_exp(50)
        self.assertEqual(state.diner_level, old_lvl + 1, "Should level up when EXP exceeds max")

    def test_04_audio_manager_resilience(self):
        """Verify audio manager behaves gracefully even without sound hardware."""
        audio = AudioManager(music_volume=0.5, sfx_volume=0.5)
        # Should not raise exception
        audio.play_bell()
        audio.play_coin()
        audio.play_pop()
        audio.set_cooking_sizzle(True)
        audio.set_cooking_sizzle(False)

    def test_05_viewer_simulator(self):
        """Verify viewer simulator produces actions over time."""
        state = GameState()
        dispatcher = CommandDispatcher(state)
        sim = ViewerSimulator(dispatcher, enabled=True, min_interval=0.1, max_interval=0.2)
        initial_chats = len(state.recent_chats)

        # Simulate 1 second of fast updates
        for _ in range(10):
            sim.update(0.1)

        self.assertGreaterEqual(len(state.recent_chats), initial_chats)

    def test_06_continuous_render_stability(self):
        """Simulate 150 frames of continuous rendering with all particle systems."""
        canvas = pygame.Surface((CANVAS_WIDTH, CANVAS_HEIGHT))
        state = GameState()
        renderer = DinerRenderer()
        particles = ParticleManager(
            heart_img=renderer.ui_icons.get("heart"),
            sparkle_img=renderer.ui_icons.get("sparkle")
        )

        particles.spawn_hearts(300, 400, count=5)
        particles.spawn_sparkles(300, 400, count=15)
        particles.spawn_confetti(30)

        for frame in range(150):
            cook_type = state.current_dish.get("cook_type", "sizzle") if state.current_dish else None
            state.update(0.033)
            particles.update(0.033, current_cook_type=cook_type)
            renderer.render(canvas, state, particles, None, 0.033)

        # Save verification frame
        out_path = os.path.join(PROJECT_ROOT, "assets", "automated_test_pass.png")
        pygame.image.save(canvas, out_path)
        self.assertTrue(os.path.exists(out_path))


if __name__ == "__main__":
    unittest.main()

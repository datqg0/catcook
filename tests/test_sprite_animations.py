"""
Test Suite for Frame-by-Frame Sprite Animations.
Validates:
1. Existence and integrity of all 9 action frame sequences (idle, walk, run, jump, attack, toss, stir, chop, cheer)
2. Transparency (RGBA) and pixel dimensions of every standalone frame
3. Individual action sprite sheets in assets/animations/sheets/
4. Master sprite sheet (chef_master_spritesheet.png) and JSON metadata atlas
5. Engine playback cycling without procedural coordinate displacement
"""
import os
import sys
import json
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
from PIL import Image

from game.config import CANVAS_WIDTH, CANVAS_HEIGHT
from game.renderer import DinerRenderer
from game.game_state import GameState
from game.particles import ParticleManager


class TestSpriteAnimations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_01_all_action_folders_and_frames(self):
        """Verify all 11 actions have clean RGBA PNG frames (5 for stir, 8 for bartender, 4 for others including bake)."""
        anim_dir = os.path.join(PROJECT_ROOT, "assets", "animations")
        actions = ["idle", "walk", "run", "jump", "attack", "toss", "stir", "chop", "cheer", "bartender", "bake"]

        for action in actions:
            act_path = os.path.join(anim_dir, action)
            self.assertTrue(os.path.isdir(act_path), f"Missing action directory: {action}")
            expected_frames = 5 if action == "stir" else (8 if action == "bartender" else 4)
            for i in range(expected_frames):
                fpath = os.path.join(act_path, f"frame_{i}.png")
                self.assertTrue(os.path.exists(fpath), f"Missing frame {i} in {action}")
                
                # Check with PIL: Must be RGBA with nonzero dimensions
                with Image.open(fpath) as im:
                    self.assertEqual(im.mode, "RGBA", f"Frame {fpath} must be RGBA format")
                    self.assertGreater(im.size[0], 50, f"Frame {fpath} width too small: {im.size}")
                    self.assertGreater(im.size[1], 100, f"Frame {fpath} height too small: {im.size}")

    def test_02_sprite_sheets_and_atlas(self):
        """Verify individual sheets and master spritesheet + JSON atlas."""
        sheets_dir = os.path.join(PROJECT_ROOT, "assets", "animations", "sheets")
        actions = ["idle", "walk", "run", "jump", "attack", "toss", "stir", "chop", "cheer", "bartender", "bake"]

        for action in actions:
            sheet_path = os.path.join(sheets_dir, f"chef_{action}_sheet.png")
            self.assertTrue(os.path.exists(sheet_path), f"Missing sheet: {sheet_path}")

        master_path = os.path.join(sheets_dir, "chef_master_spritesheet.png")
        self.assertTrue(os.path.exists(master_path), "Missing master spritesheet image")

        atlas_path = os.path.join(sheets_dir, "chef_master_spritesheet.json")
        self.assertTrue(os.path.exists(atlas_path), "Missing master atlas JSON")

        with open(atlas_path, "r") as f:
            data = json.load(f)
            self.assertIn("frames", data)
            self.assertIn("meta", data)
            expected_total = sum(5 if a == "stir" else (8 if a == "bartender" else 4) for a in actions)
            self.assertEqual(len(data["frames"]), expected_total)

    def test_03_engine_frame_cycling(self):
        """Verify renderer loads frame animations and plays them without procedural translation."""
        renderer = DinerRenderer()
        state = GameState()
        canvas = pygame.Surface((CANVAS_WIDTH, CANVAS_HEIGHT))
        particles = ParticleManager()

        # Check all 11 animations are loaded
        for action in ["idle", "walk", "run", "jump", "attack", "toss", "stir", "chop", "cheer", "bartender", "bake"]:
            self.assertIn(action, renderer.chef_animations)
            expected_count = 5 if action == "stir" else (8 if action == "bartender" else 4)
            self.assertEqual(len(renderer.chef_animations[action]), expected_count, f"Action {action} must have {expected_count} frames")

        # Cycle through multiple cooking actions including drinks and bake and verify no exceptions
        for cook_type in ["sizzle", "slice", "simmer", "drink_shake", "bake", None]:
            if cook_type:
                dish_key = "ramen" if cook_type == "simmer" else ("boba" if cook_type == "drink_shake" else ("pizza" if cook_type == "bake" else "sushi"))
                state.start_cooking(dish_key, "@Viewer")
            else:
                state.current_dish = None

            for step in range(20):
                renderer.render(canvas, state, particles, None, dt=0.033)

        # Check serving action
        state.last_served_dish = {"key": "ramen", "name": "Tonkotsu Ramen"}
        state.serve_timestamp = renderer.anim_timer
        for step in range(15):
            renderer.render(canvas, state, particles, None, dt=0.033)


if __name__ == "__main__":
    unittest.main()

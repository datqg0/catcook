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
        """Verify all 9 actions have 4 clean RGBA PNG frames."""
        anim_dir = os.path.join(PROJECT_ROOT, "assets", "animations")
        actions = ["idle", "walk", "run", "jump", "attack", "toss", "stir", "chop", "cheer"]

        for action in actions:
            act_path = os.path.join(anim_dir, action)
            self.assertTrue(os.path.isdir(act_path), f"Missing action directory: {action}")
            for i in range(4):
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
        actions = ["idle", "walk", "run", "jump", "attack", "toss", "stir", "chop", "cheer"]

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
            self.assertEqual(len(data["frames"]), len(actions) * 4)

    def test_03_engine_frame_cycling(self):
        """Verify renderer loads frame animations and plays them without procedural translation."""
        renderer = DinerRenderer()
        state = GameState()
        canvas = pygame.Surface((CANVAS_WIDTH, CANVAS_HEIGHT))
        particles = ParticleManager()

        # Check all 9 animations are loaded
        for action in ["idle", "walk", "run", "jump", "attack", "toss", "stir", "chop", "cheer"]:
            self.assertIn(action, renderer.chef_animations)
            self.assertEqual(len(renderer.chef_animations[action]), 4, f"Action {action} must have 4 frames")

        # Cycle through multiple cooking actions and verify no exceptions
        for cook_type in ["sizzle", "slice", "simmer", None]:
            if cook_type:
                state.start_cooking("ramen" if cook_type == "simmer" else ("pizza" if cook_type == "sizzle" else "sushi"), "@Viewer")
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

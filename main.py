"""
Main entry point for Cozy Midnight Diner (24/7 Interactive YouTube Stream).
Renders 720x1280 vertical canvas, plays chill lofi music, handles interactive commands.
Features 16 comfort foods, custom dish animations, procedural SFX, viewer simulator,
and YouTube chat polling integration.
"""
import sys
import os
import json
import pygame

from game.config import (
    CANVAS_WIDTH, CANVAS_HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT, FPS,
    MENU_ITEMS
)
from game.game_state import GameState
from game.renderer import DinerRenderer
from game.particles import ParticleManager
from game.commands import CommandDispatcher
from game.audio import AudioManager
from game.viewer_sim import ViewerSimulator
from youtube.chat_poller import YouTubeChatPoller


def load_config():
    config_file = os.path.join(os.path.dirname(__file__), "config", "config.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Config] Error reading config.json: {e}")
    return {}


def main():
    pygame.init()
    pygame.display.set_caption("Cozy Midnight Diner - 24/7 Interactive Stream")

    cfg = load_config()
    game_cfg = cfg.get("game", {})

    # Initialize Audio System (Lofi music + SFX)
    audio = AudioManager(
        music_volume=game_cfg.get("music_volume", 0.55),
        sfx_volume=game_cfg.get("sfx_volume", 0.70)
    )

    # Window display (scaled for comfortable viewing on PC monitors)
    display_surf = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
    # Master rendering surface (standard 720x1280 vertical format)
    canvas = pygame.Surface((CANVAS_WIDTH, CANVAS_HEIGHT))

    clock = pygame.time.Clock()

    # Initialize Core Systems
    state = GameState()
    renderer = DinerRenderer()
    particles = ParticleManager(
        heart_img=renderer.ui_icons.get("heart"),
        sparkle_img=renderer.ui_icons.get("sparkle")
    )
    dispatcher = CommandDispatcher(state)

    # Viewer Simulator (keeps stream active with natural chatters)
    sim_enabled = game_cfg.get("simulate_viewers", True)
    viewer_sim = ViewerSimulator(
        dispatcher,
        enabled=sim_enabled,
        min_interval=game_cfg.get("simulation_interval_min", 14.0),
        max_interval=game_cfg.get("simulation_interval_max", 28.0)
    )

    # YouTube Chat Poller (if configured with API key)
    config_path = os.path.join(os.path.dirname(__file__), "config", "config.json")
    chat_poller = YouTubeChatPoller(dispatcher, config_path=config_path)
    chat_poller.start()

    # Wire Visual & Audio Event Hooks
    state.on_cheer_callback = lambda: (
        audio.play_pop(),
        particles.spawn_hearts(320, 430, count=5),
        particles.spawn_hearts(515, 630, count=3)
    )
    state.on_complete_callback = lambda: (
        audio.play_bell(),
        particles.spawn_sparkles(515, 640, count=22),
        particles.spawn_confetti(30)
    )
    state.on_tip_callback = lambda: (
        audio.play_coin(),
        particles.spawn_sparkles(CANVAS_WIDTH // 2, 450, count=25),
        particles.spawn_hearts(CANVAS_WIDTH // 2, 450, count=6),
        particles.spawn_confetti(40)
    )
    state.on_levelup_callback = lambda: (
        audio.play_bell(),
        audio.play_coin(),
        particles.spawn_confetti(75),
        particles.spawn_sparkles(CANVAS_WIDTH // 2, 350, count=35)
    )

    # In-game interactive typing state
    input_state = {"active": False, "text": ""}
    running = True

    # Quick menu mapping for keys
    dish_keys = list(MENU_ITEMS.keys())

    print("\n" + "=" * 65)
    print("  COZY MIDNIGHT DINER - 24/7 INTERACTIVE LIVESTREAM")
    print("=" * 65)
    print(f"  Menu: {len(dish_keys)} Comfort Foods loaded.")
    print("  Controls:")
    print("    [1-9, 0]  : Quick order dishes (Ramen, Pizza, Tacos, Boba...)")
    print("    [SPACE/Y] : Cheer with !yum (Floating hearts + sound)")
    print("    [T]       : Send !tip 100 coins (Golden sparkles + confetti + coin chime)")
    print("    [M]       : Show !menu in chat")
    print("    [C]       : Type custom chat command (e.g. !cook waffles)")
    print("    [V]       : Toggle Viewer Simulator ON/OFF")
    print("    [ESC]     : Exit")
    print("=" * 65 + "\n")

    was_cooking = False

    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                display_surf = pygame.display.set_mode(event.size, pygame.RESIZABLE)

            elif event.type == pygame.KEYDOWN:
                if input_state["active"]:
                    if event.key == pygame.K_RETURN:
                        msg = input_state["text"].strip()
                        if msg:
                            dispatcher.dispatch("@You", msg)
                        input_state["active"] = False
                        input_state["text"] = ""
                    elif event.key == pygame.K_ESCAPE:
                        input_state["active"] = False
                        input_state["text"] = ""
                    elif event.key == pygame.K_BACKSPACE:
                        input_state["text"] = input_state["text"][:-1]
                    else:
                        if event.unicode and len(input_state["text"]) < 40:
                            input_state["text"] += event.unicode
                else:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_c:
                        input_state["active"] = True
                        input_state["text"] = "!cook "
                    elif event.key in (pygame.K_SPACE, pygame.K_y):
                        dispatcher.dispatch("@You", "!yum")
                    elif event.key == pygame.K_t:
                        dispatcher.dispatch("@You", "!tip 100")
                    elif event.key == pygame.K_m:
                        dispatcher.dispatch("@You", "!menu")
                    elif event.key == pygame.K_v:
                        is_on = viewer_sim.toggle()
                        status = "ENABLED" if is_on else "DISABLED"
                        state.add_chat("System", f"Viewer simulator {status}", (255, 204, 77))
                    elif pygame.K_1 <= event.key <= pygame.K_9:
                        idx = event.key - pygame.K_1
                        if idx < len(dish_keys):
                            dispatcher.dispatch("@You", f"!cook {dish_keys[idx]}")
                    elif event.key == pygame.K_0:
                        if len(dish_keys) >= 10:
                            dispatcher.dispatch("@You", f"!cook {dish_keys[9]}")

        # Update viewer simulation
        viewer_sim.update(dt)

        # Update game state & particles
        cook_type = state.current_dish.get("cook_type", "sizzle") if state.current_dish else None
        state.update(dt)
        counter_pos = (553, 715) if (state.current_dish or state.last_served_dish) else None
        particles.update(dt, current_cook_type=cook_type, counter_dish_pos=counter_pos)

        # Audio cooking sizzle loop management
        is_cooking = state.current_dish is not None
        if is_cooking != was_cooking:
            audio.set_cooking_sizzle(is_cooking)
            was_cooking = is_cooking

        # Render 720x1280 canvas
        renderer.render(canvas, state, particles, input_state, dt)

        # Scale canvas to display window
        cur_w, cur_h = display_surf.get_size()
        scaled = pygame.transform.smoothscale(canvas, (cur_w, cur_h))
        display_surf.blit(scaled, (0, 0))

        pygame.display.flip()

    chat_poller.stop()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

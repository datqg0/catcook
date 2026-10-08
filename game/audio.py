"""
Robust Audio Manager for Cozy Midnight Diner.
Plays looping background Lofi music and procedural sound effects (bell, coin, pop, sizzle).
Gracefully handles headless environments and missing audio endpoints.
"""
import os
import pygame
from game.config import SOUNDS_DIR


class AudioManager:
    def __init__(self, music_volume=0.55, sfx_volume=0.70):
        self.enabled = False
        self.sounds = {}
        self.music_volume = music_volume
        self.sfx_volume = sfx_volume
        self.sizzle_channel = None

        self._init_audio()

    def _init_audio(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.enabled = True
            self._load_sounds()
            self._start_music()
            print("[AudioManager] Audio initialized successfully.")
        except Exception as e:
            self.enabled = False
            print(f"[AudioManager] Audio device not available (silent fallback): {e}")

    def _load_sounds(self):
        if not self.enabled:
            return

        sfx_files = {
            "bell": "bell_ding.wav",
            "coin": "coin_chime.wav",
            "pop": "pop.wav",
            "sizzle": "sizzle.wav"
        }
        for key, fname in sfx_files.items():
            fpath = os.path.join(SOUNDS_DIR, fname)
            if os.path.exists(fpath):
                try:
                    snd = pygame.mixer.Sound(fpath)
                    snd.set_volume(self.sfx_volume)
                    self.sounds[key] = snd
                except Exception as e:
                    print(f"[AudioManager] Could not load {fname}: {e}")

    def _start_music(self):
        if not self.enabled:
            return
        music_path = os.path.join(SOUNDS_DIR, "lofi_chill.mp3")
        if os.path.exists(music_path):
            try:
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play(-1)  # infinite loop
            except Exception as e:
                print(f"[AudioManager] Could not play music: {e}")

    def play_bell(self):
        if self.enabled and "bell" in self.sounds:
            try:
                self.sounds["bell"].play()
            except Exception:
                pass

    def play_coin(self):
        if self.enabled and "coin" in self.sounds:
            try:
                self.sounds["coin"].play()
            except Exception:
                pass

    def play_pop(self):
        if self.enabled and "pop" in self.sounds:
            try:
                self.sounds["pop"].play()
            except Exception:
                pass

    def set_cooking_sizzle(self, is_cooking):
        if not self.enabled or "sizzle" not in self.sounds:
            return
        try:
            if is_cooking:
                if self.sizzle_channel is None or not self.sizzle_channel.get_busy():
                    self.sizzle_channel = self.sounds["sizzle"].play(-1)
            else:
                if self.sizzle_channel and self.sizzle_channel.get_busy():
                    self.sizzle_channel.stop()
        except Exception:
            pass

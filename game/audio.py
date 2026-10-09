"""
Robust Audio Manager for Cozy Midnight Diner.
Plays looping background Lofi music and procedural sound effects (bell, coin, pop, sizzle).
Provides dynamic real-time volume control, track switching, and mute capabilities.
Gracefully handles headless environments and missing audio endpoints.
"""
import os
import pygame
from game.config import SOUNDS_DIR


class AudioManager:
    def __init__(self, music_volume=0.55, sfx_volume=0.70):
        self.enabled = False
        self.sounds = {}
        self.music_volume = max(0.0, min(1.0, float(music_volume)))
        self.sfx_volume = max(0.0, min(1.0, float(sfx_volume)))
        self.muted_bgm = False
        self.muted_sfx = False
        self.current_track = "lofi_chill.mp3"
        self.sizzle_channel = None

        self._init_audio()

    def _init_audio(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.enabled = True
            self._load_sounds()
            self._start_music(self.current_track)
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
                    vol = 0.0 if self.muted_sfx else self.sfx_volume
                    snd.set_volume(vol)
                    self.sounds[key] = snd
                except Exception as e:
                    print(f"[AudioManager] Could not load {fname}: {e}")

    def _start_music(self, track_name=None):
        if not self.enabled:
            return
        if track_name:
            self.current_track = track_name
        music_path = os.path.join(SOUNDS_DIR, self.current_track)
        if os.path.exists(music_path):
            try:
                pygame.mixer.music.load(music_path)
                vol = 0.0 if self.muted_bgm else self.music_volume
                pygame.mixer.music.set_volume(vol)
                pygame.mixer.music.play(-1)  # infinite loop
            except Exception as e:
                print(f"[AudioManager] Could not play music ({self.current_track}): {e}")

    def set_music_volume(self, volume):
        """Set BGM volume (0.0 to 1.0). Updates mixer immediately."""
        self.music_volume = max(0.0, min(1.0, float(volume)))
        if self.enabled and not self.muted_bgm:
            try:
                pygame.mixer.music.set_volume(self.music_volume)
            except Exception:
                pass

    def set_sfx_volume(self, volume):
        """Set SFX volume (0.0 to 1.0). Updates all active sounds immediately."""
        self.sfx_volume = max(0.0, min(1.0, float(volume)))
        if self.enabled and not self.muted_sfx:
            for snd in self.sounds.values():
                try:
                    snd.set_volume(self.sfx_volume)
                except Exception:
                    pass

    def set_mute_bgm(self, muted):
        """Mute or unmute BGM."""
        self.muted_bgm = bool(muted)
        if self.enabled:
            try:
                vol = 0.0 if self.muted_bgm else self.music_volume
                pygame.mixer.music.set_volume(vol)
            except Exception:
                pass

    def set_mute_sfx(self, muted):
        """Mute or unmute SFX."""
        self.muted_sfx = bool(muted)
        if self.enabled:
            vol = 0.0 if self.muted_sfx else self.sfx_volume
            for snd in self.sounds.values():
                try:
                    snd.set_volume(vol)
                except Exception:
                    pass

    def switch_music(self, track_name):
        """Switch to a different background music track in SOUNDS_DIR."""
        if not track_name:
            return False
        track_path = os.path.join(SOUNDS_DIR, track_name)
        if not os.path.exists(track_path):
            return False
        self.current_track = track_name
        if self.enabled:
            try:
                pygame.mixer.music.stop()
                self._start_music(track_name)
                return True
            except Exception as e:
                print(f"[AudioManager] Failed to switch music: {e}")
                return False
        return True

    def get_available_tracks(self):
        """List all valid music tracks in SOUNDS_DIR."""
        known_sfx = {"bell_ding.wav", "coin_chime.wav", "pop.wav", "sizzle.wav"}
        tracks = []
        if os.path.exists(SOUNDS_DIR):
            for f in sorted(os.listdir(SOUNDS_DIR)):
                if f.lower().endswith((".mp3", ".ogg", ".wav")) and f not in known_sfx:
                    tracks.append(f)
        return tracks

    def play_sfx(self, name):
        """Play any sound effect by name for testing or events."""
        if name == "bell":
            self.play_bell()
        elif name == "coin":
            self.play_coin()
        elif name == "pop":
            self.play_pop()
        elif name == "sizzle":
            if self.enabled and "sizzle" in self.sounds:
                self.sounds["sizzle"].play(0)

    def play_bell(self):
        if self.enabled and not self.muted_sfx and "bell" in self.sounds:
            try:
                self.sounds["bell"].play()
            except Exception:
                pass

    def play_coin(self):
        if self.enabled and not self.muted_sfx and "coin" in self.sounds:
            try:
                self.sounds["coin"].play()
            except Exception:
                pass

    def play_pop(self):
        if self.enabled and not self.muted_sfx and "pop" in self.sounds:
            try:
                self.sounds["pop"].play()
            except Exception:
                pass

    def set_cooking_sizzle(self, is_cooking):
        if not self.enabled or "sizzle" not in self.sounds:
            return
        try:
            if is_cooking and not self.muted_sfx:
                if self.sizzle_channel is None or not self.sizzle_channel.get_busy():
                    self.sizzle_channel = self.sounds["sizzle"].play(-1)
            else:
                if self.sizzle_channel and self.sizzle_channel.get_busy():
                    self.sizzle_channel.stop()
        except Exception:
            pass

    def get_status(self):
        """Returns JSON-serializable audio status for Studio Controller."""
        return {
            "enabled": self.enabled,
            "music_volume": round(self.music_volume, 2),
            "sfx_volume": round(self.sfx_volume, 2),
            "muted_bgm": self.muted_bgm,
            "muted_sfx": self.muted_sfx,
            "current_track": self.current_track,
            "available_tracks": self.get_available_tracks()
        }

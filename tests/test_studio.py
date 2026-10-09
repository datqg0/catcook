"""
Unit tests for AudioManager extensions, GameState studio controls,
StudioBridge IPC communication, and Studio Controller integration.
"""
import json
import os
import socket
import time
import pytest

from game.audio import AudioManager
from game.game_state import GameState
from game.viewer_sim import ViewerSimulator
from game.commands import CommandDispatcher
from game.studio_bridge import StudioBridge


def test_audio_manager_volume_and_mute():
    audio = AudioManager(music_volume=0.5, sfx_volume=0.6)
    
    # Test volume adjustment
    audio.set_music_volume(0.85)
    assert audio.music_volume == 0.85
    audio.set_sfx_volume(0.35)
    assert audio.sfx_volume == 0.35

    # Test volume clamping
    audio.set_music_volume(1.5)
    assert audio.music_volume == 1.0
    audio.set_sfx_volume(-0.5)
    assert audio.sfx_volume == 0.0

    # Test muting
    audio.set_mute_bgm(True)
    assert audio.muted_bgm is True
    audio.set_mute_bgm(False)
    assert audio.muted_bgm is False

    audio.set_mute_sfx(True)
    assert audio.muted_sfx is True
    audio.set_mute_sfx(False)
    assert audio.muted_sfx is False

    # Test status dict
    status = audio.get_status()
    assert "music_volume" in status
    assert "sfx_volume" in status
    assert "current_track" in status
    assert "available_tracks" in status


def test_audio_manager_tracks_and_sfx():
    audio = AudioManager()
    tracks = audio.get_available_tracks()
    assert isinstance(tracks, list)
    assert len(tracks) > 0  # Should include at least lofi_chill.mp3 and outfoxing.mp3

    # Test track switching
    assert audio.switch_music(tracks[0]) is True
    assert audio.current_track == tracks[0]

    # Test sfx triggering
    audio.play_sfx("bell")
    audio.play_sfx("coin")
    audio.play_sfx("pop")
    audio.play_sfx("sizzle")


def test_game_state_studio_controls():
    state = GameState()

    # Test summary structure
    summary = state.get_summary()
    assert "level" in summary
    assert "current_dish" in summary
    assert "order_queue" in summary

    # Test set_level
    state.set_level(42)
    assert state.diner_level == 42

    # Test clear_order_queue
    state.add_order("@User1", "ramen")
    state.add_order("@User2", "pizza")
    assert len(state.order_queue) >= 2
    cleared = state.clear_order_queue()
    assert cleared >= 2
    assert len(state.order_queue) == 0

    # Test instant_finish
    state.start_cooking("ramen", "@TestChef")
    assert state.current_dish is not None
    finished = state.instant_finish()
    assert finished is True
    assert state.current_dish is None

    # Test skip_dish
    state.start_cooking("pizza", "@TestChef")
    assert state.current_dish is not None
    skipped = state.skip_dish()
    assert skipped is True


def test_studio_bridge_socket_communication():
    test_port = 18799
    bridge = StudioBridge(port=test_port)
    assert bridge.start() is True

    time.sleep(0.1)

    state = GameState()
    audio = AudioManager()
    dispatcher = CommandDispatcher(state)
    sim = ViewerSimulator(dispatcher)
    cfg = {"game": {"music_volume": 0.5, "sfx_volume": 0.7}}

    # Connect client socket
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("127.0.0.1", test_port))
    client.settimeout(1.0)

    # Send command to set volume
    cmd = {"action": "set_music_volume", "value": 0.92}
    client.sendall((json.dumps(cmd) + "\n").encode("utf-8"))

    # Send command to add order
    order_cmd = {"action": "order_dish", "dish": "pizza", "user": "@SocketTester"}
    client.sendall((json.dumps(order_cmd) + "\n").encode("utf-8"))

    time.sleep(0.1)

    # Process inside tick
    bridge.tick(state, audio, sim, dispatcher, cfg)

    assert audio.music_volume == 0.92
    assert any(item["user"] == "@SocketTester" for item in state.order_queue)

    # Receive broadcasted status
    data = client.recv(4096)
    lines = [json.loads(l) for l in data.decode("utf-8").splitlines() if l.strip()]
    assert len(lines) >= 1
    assert lines[0]["type"] == "status"
    assert lines[0]["audio"]["music_volume"] == 0.92

    client.close()
    bridge.stop()

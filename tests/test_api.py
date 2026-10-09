"""
Unit tests for YouTube Live Chat API parser and International Donate Webhook service.
"""
import json
import time
import pytest

from game.game_state import GameState
from game.commands import CommandDispatcher
from game.donate_receiver import DonateReceiver
from youtube.chat_poller import extract_video_id, YouTubeChatPoller


def test_youtube_video_id_extraction():
    test_cases = [
        ("dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/live/dQw4w9WgXcQ?feature=share", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/shorts/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtube.com/watch?v=dQw4w9WgXcQ&t=42s", "dQw4w9WgXcQ"),
    ]
    for raw_input, expected_id in test_cases:
        assert extract_video_id(raw_input) == expected_id


def test_youtube_chat_poller_state():
    state = GameState()
    dispatcher = CommandDispatcher(state)
    poller = YouTubeChatPoller(dispatcher)

    assert poller.running is False
    status = poller.get_status()
    assert "has_api_key" in status
    assert status["has_api_key"] is False

    # Update credentials
    poller.update_credentials(api_key="TEST_KEY", video_id="https://youtu.be/dQw4w9WgXcQ", enabled=False)
    assert poller.api_key == "TEST_KEY"
    assert poller.video_id == "dQw4w9WgXcQ"


def test_donate_receiver_simulation():
    state = GameState()
    dispatcher = CommandDispatcher(state)

    receiver = DonateReceiver(state, dispatcher, port=8099)
    assert receiver.start() is True

    # 1. Test basic donation ($5.00 USD -> 500 coins)
    prev_coins = sum(item["coins"] for item in state.leaderboard if item["user"] == "@Sarah")
    ok, msg = receiver.simulate_donation(user="@Sarah", amount=5.0, currency="USD", message="Great stream!")
    assert ok is True
    new_coins = sum(item["coins"] for item in state.leaderboard if item["user"] == "@Sarah")
    assert new_coins >= prev_coins + 500

    # 2. Test donation with VIP dish order in message
    ok, msg = receiver.simulate_donation(user="@VIPFan", amount=10.0, currency="USD", message="Please make waffles! !cook waffles")
    assert ok is True
    # Verify waffles was added to queue
    assert any("waffles" in item["key"] for item in state.order_queue)

    status = receiver.get_status()
    assert status["total_count"] == 2
    assert status["total_usd"] == 15.0
    assert status["last_donation"]["user"] == "@VIPFan"

    receiver.stop()

"""
YouTube Live Chat Poller Service.
Polls liveChatMessages from YouTube Data API v3 in a background thread
and safely pushes commands into the game's CommandDispatcher.
Supports auto-resolving activeLiveChatId from YouTube Video ID or Stream URL.
"""
import json
import os
import re
import threading
import time
import requests


def extract_video_id(url_or_id):
    """Extracts an 11-character YouTube video ID from various URL formats or raw string."""
    if not url_or_id:
        return ""
    text = url_or_id.strip()
    if len(text) == 11 and "/" not in text and "?" not in text and "&" not in text:
        return text

    patterns = [
        r"(?:v=|\/v\/|\/embed\/|\/live\/|\/shorts\/|youtu\.be\/)([^#&?\/]{11})",
        r"([a-zA-Z0-9_-]{11})"
    ]
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            return m.group(1)
    return text


def resolve_live_chat_id(api_key, video_id):
    """
    Calls YouTube Data API v3 to look up activeLiveChatId from a video ID.
    Returns (live_chat_id, message, is_success).
    """
    if not api_key:
        return None, "API Key is required.", False
    v_id = extract_video_id(video_id)
    if not v_id:
        return None, "Invalid Video ID or Stream URL.", False

    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "liveStreamingDetails,snippet",
        "id": v_id,
        "key": api_key
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            if not items:
                return None, f"Video '{v_id}' not found on YouTube.", False

            item = items[0]
            title = item.get("snippet", {}).get("title", "Livestream")
            live_details = item.get("liveStreamingDetails", {})
            active_chat_id = live_details.get("activeLiveChatId")

            if not active_chat_id:
                return None, f"Video '{title}' is not an active livestream or Live Chat is disabled.", False

            return active_chat_id, f"Connected to Live Chat: '{title}'", True
        elif resp.status_code == 400:
            return None, "API Error: Invalid API Key or request parameters.", False
        elif resp.status_code == 403:
            return None, "API Error: Quota exceeded or YouTube Data API v3 not enabled on Google Cloud project.", False
        else:
            return None, f"API Error (HTTP {resp.status_code}): {resp.text[:120]}", False
    except Exception as e:
        return None, f"Connection error: {e}", False


class YouTubeChatPoller:
    def __init__(self, command_dispatcher, config_path=None):
        self.dispatcher = command_dispatcher
        self.config_path = config_path
        self.running = False
        self.thread = None
        self.api_key = ""
        self.video_id = ""
        self.live_chat_id = ""
        self.enabled = False
        self.next_page_token = None
        self.polling_interval = 4.0
        self.seen_message_ids = set()
        self.status_message = "Chưa kết nối"
        self.last_poll_time = 0.0

        if config_path and os.path.exists(config_path):
            self.load_config(config_path)

    def load_config(self, config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                yt_conf = data.get("youtube", {})
                self.api_key = yt_conf.get("api_key", "").strip()
                self.video_id = yt_conf.get("video_id", "").strip()
                self.live_chat_id = yt_conf.get("live_chat_id", "").strip()
                self.enabled = yt_conf.get("enabled", False)
                self.polling_interval = float(yt_conf.get("polling_interval", 4.0))
        except Exception as e:
            print(f"[YouTubePoller] Error reading config: {e}")

    def update_credentials(self, api_key, video_id=None, live_chat_id=None, enabled=True):
        """Dynamically updates credentials and restarts poller if enabled."""
        self.api_key = (api_key or "").strip()
        if video_id is not None:
            self.video_id = extract_video_id(video_id)
        if live_chat_id is not None:
            self.live_chat_id = (live_chat_id or "").strip()
        self.enabled = bool(enabled)

        if self.running:
            self.stop()
        if self.enabled:
            return self.start()
        return True

    def start(self):
        if not self.api_key:
            self.status_message = "Chưa cấu hình API Key"
            print("[YouTubePoller] API Key not set. Polling inactive.")
            return False

        # Auto-resolve live_chat_id if missing but video_id is provided
        if not self.live_chat_id and self.video_id:
            chat_id, msg, ok = resolve_live_chat_id(self.api_key, self.video_id)
            if ok:
                self.live_chat_id = chat_id
                self.status_message = msg
                print(f"[YouTubePoller] {msg}")
            else:
                self.status_message = f"Lỗi: {msg}"
                print(f"[YouTubePoller] Auto-resolve failed: {msg}")
                return False

        if not self.live_chat_id:
            self.status_message = "Thiếu Live Chat ID hoặc Video ID"
            print("[YouTubePoller] Neither live_chat_id nor valid video_id provided.")
            return False

        self.running = True
        self.seen_message_ids.clear()
        self.next_page_token = None
        self.thread = threading.Thread(target=self._poll_loop, daemon=True, name="YouTubeChatPoller")
        self.thread.start()
        self.status_message = "Đang lắng nghe Live Chat"
        print("[YouTubePoller] YouTube Live Chat poller started in background thread.")
        return True

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.5)
        self.status_message = "Đã dừng"
        print("[YouTubePoller] YouTube Live Chat poller stopped.")

    def get_status(self):
        """Returns JSON-serializable status dictionary for Studio Controller."""
        return {
            "running": self.running,
            "enabled": self.enabled,
            "has_api_key": bool(self.api_key),
            "video_id": self.video_id,
            "live_chat_id": self.live_chat_id,
            "status_message": self.status_message,
            "last_poll_time": self.last_poll_time
        }

    def _poll_loop(self):
        url = "https://www.googleapis.com/youtube/v3/liveChat/messages"
        is_first_fetch = True

        while self.running:
            try:
                params = {
                    "liveChatId": self.live_chat_id,
                    "part": "snippet,authorDetails",
                    "key": self.api_key,
                    "maxResults": 30
                }
                if self.next_page_token:
                    params["pageToken"] = self.next_page_token

                resp = requests.get(url, params=params, timeout=10)
                self.last_poll_time = time.time()

                if resp.status_code == 200:
                    data = resp.json()
                    self.next_page_token = data.get("nextPageToken")
                    poll_interval_ms = data.get("pollingIntervalMillis", 4000)
                    self.polling_interval = max(3.0, poll_interval_ms / 1000.0)

                    items = data.get("items", [])

                    # On initial fetch, mark existing messages as seen to avoid flood
                    if is_first_fetch:
                        for item in items:
                            msg_id = item.get("id")
                            if msg_id:
                                self.seen_message_ids.add(msg_id)
                        is_first_fetch = False
                    else:
                        for item in items:
                            msg_id = item.get("id")
                            if msg_id and msg_id in self.seen_message_ids:
                                continue
                            if msg_id:
                                self.seen_message_ids.add(msg_id)
                                if len(self.seen_message_ids) > 1000:
                                    self.seen_message_ids.clear()

                            snippet = item.get("snippet", {})
                            author_details = item.get("authorDetails", {})
                            display_name = author_details.get("displayName", "Viewer")
                            text_message = snippet.get("displayMessage", "")

                            if text_message:
                                formatted_user = f"@{display_name}"
                                self.dispatcher.dispatch(formatted_user, text_message)

                elif resp.status_code == 403:
                    self.status_message = "Vượt hạn mức Quota API (Backoff 60s)"
                    print("[YouTubePoller] API quota limit reached. Backing off for 60 seconds...")
                    time.sleep(60.0)
                elif resp.status_code == 404:
                    self.status_message = "Live Chat không tồn tại hoặc đã kết thúc"
                    print("[YouTubePoller] Live chat session not found or stream ended.")
                    break
                else:
                    self.status_message = f"Lỗi HTTP {resp.status_code}"
                    print(f"[YouTubePoller] HTTP error {resp.status_code}: {resp.text[:120]}")

            except Exception as e:
                self.status_message = f"Lỗi mạng: {e}"
                print(f"[YouTubePoller] Network error during chat poll: {e}")

            time.sleep(self.polling_interval)

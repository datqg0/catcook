"""
YouTube Live Chat Poller Service.
Polls liveChatMessages from YouTube Data API v3 in a background thread
and safely pushes commands into the game's CommandDispatcher.
"""
import time
import threading
import json
import os
import requests


class YouTubeChatPoller:
    def __init__(self, command_dispatcher, config_path=None):
        self.dispatcher = command_dispatcher
        self.running = False
        self.thread = None
        self.live_chat_id = None
        self.api_key = None
        self.next_page_token = None
        self.polling_interval = 4.0

        if config_path and os.path.exists(config_path):
            self._load_config(config_path)

    def _load_config(self, config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                yt_conf = data.get("youtube", {})
                self.live_chat_id = yt_conf.get("live_chat_id")
                self.api_key = yt_conf.get("api_key")
        except Exception as e:
            print(f"[YouTubePoller] Error reading config: {e}")

    def start(self):
        if not self.live_chat_id or not self.api_key:
            print("[YouTubePoller] LiveChatId or ApiKey not set. YouTube chat polling inactive (running in local/mock mode).")
            return False

        self.running = True
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.thread.start()
        print("[YouTubePoller] YouTube Live Chat poller started in background thread.")
        return True

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        print("[YouTubePoller] YouTube Live Chat poller stopped.")

    def _poll_loop(self):
        url = "https://www.googleapis.com/youtube/v3/liveChat/messages"
        while self.running:
            try:
                params = {
                    "liveChatId": self.live_chat_id,
                    "part": "snippet,authorDetails",
                    "key": self.api_key,
                    "maxResults": 20
                }
                if self.next_page_token:
                    params["pageToken"] = self.next_page_token

                resp = requests.get(url, params=params, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    self.next_page_token = data.get("nextPageToken")
                    poll_interval_ms = data.get("pollingIntervalMillis", 4000)
                    self.polling_interval = max(3.0, poll_interval_ms / 1000.0)

                    items = data.get("items", [])
                    for item in items:
                        snippet = item.get("snippet", {})
                        author_details = item.get("authorDetails", {})
                        display_name = author_details.get("displayName", "Viewer")
                        text_message = snippet.get("displayMessage", "")
                        
                        if text_message:
                            formatted_user = f"@{display_name}"
                            self.dispatcher.dispatch(formatted_user, text_message)

                elif resp.status_code == 403:
                    print("[YouTubePoller] API quota limit reached. Backing off for 60 seconds...")
                    time.sleep(60.0)
                else:
                    print(f"[YouTubePoller] HTTP error {resp.status_code}: {resp.text}")

            except Exception as e:
                print(f"[YouTubePoller] Network error during chat poll: {e}")

            time.sleep(self.polling_interval)

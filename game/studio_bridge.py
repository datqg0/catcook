"""
Studio Bridge - IPC communication bridge between Pygame game loop and Desktop Studio Controller.
Runs a lightweight localhost TCP socket server.
Processes commands safely inside the main Pygame thread and streams game status to the Controller.
"""
import json
import os
import queue
import socket
import threading
import time

DEFAULT_PORT = 18765


class StudioBridge:
    def __init__(self, port=DEFAULT_PORT, host="127.0.0.1"):
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None
        self.clients = []
        self.clients_lock = threading.Lock()
        self.command_queue = queue.Queue()
        self.last_broadcast_time = 0.0
        self.broadcast_interval = 0.10  # 10 updates per second for smooth UI

    def start(self):
        """Starts the IPC server thread."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1.0)
            self.running = True

            self.accept_thread = threading.Thread(target=self._accept_loop, daemon=True, name="StudioBridgeAccept")
            self.accept_thread.start()
            print(f"[StudioBridge] Control server active on {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"[StudioBridge] Could not start socket server on port {self.port}: {e}")
            self.running = False
            return False

    def _accept_loop(self):
        while self.running:
            try:
                client_sock, addr = self.server_socket.accept()
                client_sock.settimeout(0.5)
                with self.clients_lock:
                    self.clients.append(client_sock)
                # Spawn client reader thread
                t = threading.Thread(target=self._client_reader, args=(client_sock,), daemon=True)
                t.start()
            except socket.timeout:
                continue
            except Exception:
                break

    def _client_reader(self, sock):
        buffer = ""
        while self.running:
            try:
                data = sock.recv(4096)
                if not data:
                    break
                buffer += data.decode("utf-8", errors="ignore")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if line:
                        try:
                            msg = json.loads(line)
                            self.command_queue.put(msg)
                        except json.JSONDecodeError:
                            pass
            except socket.timeout:
                continue
            except Exception:
                break

        with self.clients_lock:
            if sock in self.clients:
                self.clients.remove(sock)
        try:
            sock.close()
        except Exception:
            pass

    def broadcast(self, payload):
        """Broadcasts a JSON payload to all connected Studio Controller clients."""
        if not self.running:
            return
        msg = (json.dumps(payload) + "\n").encode("utf-8")
        dead_clients = []
        with self.clients_lock:
            for c in self.clients:
                try:
                    c.sendall(msg)
                except Exception:
                    dead_clients.append(c)
            for d in dead_clients:
                if d in self.clients:
                    self.clients.remove(d)

    def tick(self, state, audio, viewer_sim, dispatcher, cfg_data, config_path=None,
             chat_poller=None, donate_receiver=None):
        """
        Executes inside Pygame's main loop frame update.
        Safely drains incoming commands and broadcasts status periodically.
        """
        if not self.running:
            return

        # 1. Process queued commands from Studio Controller
        while not self.command_queue.empty():
            try:
                cmd = self.command_queue.get_nowait()
                self._handle_command(cmd, state, audio, viewer_sim, dispatcher, cfg_data, config_path,
                                     chat_poller, donate_receiver)
            except queue.Empty:
                break
            except Exception as e:
                print(f"[StudioBridge] Error handling command: {e}")

        # 2. Periodically broadcast game state
        now = time.time()
        if now - self.last_broadcast_time >= self.broadcast_interval:
            self.last_broadcast_time = now
            self._send_status(state, audio, viewer_sim, cfg_data, chat_poller, donate_receiver)

    def _handle_command(self, cmd, state, audio, viewer_sim, dispatcher, cfg_data, config_path,
                        chat_poller=None, donate_receiver=None):
        action = cmd.get("action")
        if not action:
            return

        # Audio commands
        if action == "set_music_volume":
            val = float(cmd.get("value", 0.5))
            audio.set_music_volume(val)
            if "game" in cfg_data:
                cfg_data["game"]["music_volume"] = round(val, 2)
        elif action == "set_sfx_volume":
            val = float(cmd.get("value", 0.7))
            audio.set_sfx_volume(val)
            if "game" in cfg_data:
                cfg_data["game"]["sfx_volume"] = round(val, 2)
        elif action == "set_mute_bgm":
            audio.set_mute_bgm(cmd.get("value", False))
        elif action == "set_mute_sfx":
            audio.set_mute_sfx(cmd.get("value", False))
        elif action == "switch_music":
            audio.switch_music(cmd.get("track", ""))
        elif action == "play_sfx":
            audio.play_sfx(cmd.get("sfx", "bell"))

        # Gameplay & Kitchen commands
        elif action == "order_dish":
            dish = cmd.get("dish", "")
            user = cmd.get("user", "@Host")
            state.add_order(user, dish)
        elif action == "instant_finish":
            state.instant_finish()
        elif action == "skip_dish":
            state.skip_dish()
        elif action == "clear_queue":
            state.clear_order_queue()
        elif action == "set_level":
            state.set_level(int(cmd.get("level", 1)))

        # Interactive Chat & Viewer Events
        elif action == "toggle_sim":
            enabled = cmd.get("value")
            if enabled is not None:
                viewer_sim.enabled = bool(enabled)
            else:
                viewer_sim.toggle()
        elif action == "cheer":
            user = cmd.get("user", "@Host")
            state.cheer(user)
        elif action == "tip":
            user = cmd.get("user", "@Host")
            amount = int(cmd.get("amount", 100))
            state.tip(user, amount)
        elif action == "send_chat":
            user = cmd.get("user", "@Host")
            message = cmd.get("message", "")
            if message:
                dispatcher.dispatch(user, message)

        # YouTube Live Chat Credentials & Control
        elif action == "update_youtube_credentials":
            if chat_poller:
                chat_poller.update_credentials(
                    api_key=cmd.get("api_key", ""),
                    video_id=cmd.get("video_id", ""),
                    live_chat_id=cmd.get("live_chat_id", ""),
                    enabled=cmd.get("enabled", True)
                )
                if "youtube" not in cfg_data:
                    cfg_data["youtube"] = {}
                cfg_data["youtube"]["api_key"] = chat_poller.api_key
                cfg_data["youtube"]["video_id"] = chat_poller.video_id
                cfg_data["youtube"]["live_chat_id"] = chat_poller.live_chat_id
                cfg_data["youtube"]["enabled"] = chat_poller.enabled

        # Donate Webhook Configuration
        elif action == "update_donate_config":
            if donate_receiver:
                donate_receiver.enabled = bool(cmd.get("enabled", True))
                donate_receiver.usd_to_coins = int(cmd.get("usd_to_coins", 100))
                donate_receiver.auto_cook_on_message = bool(cmd.get("auto_cook", True))
                if "donate" not in cfg_data:
                    cfg_data["donate"] = {}
                cfg_data["donate"]["enabled"] = donate_receiver.enabled
                cfg_data["donate"]["usd_to_coins"] = donate_receiver.usd_to_coins
                cfg_data["donate"]["auto_cook_on_message"] = donate_receiver.auto_cook_on_message
                cfg_data["donate"]["webhook_port"] = donate_receiver.port

        # Donate Simulation / Test
        elif action == "simulate_donate":
            if donate_receiver:
                donate_receiver.simulate_donation(
                    user=cmd.get("user", "@Alex"),
                    amount=float(cmd.get("amount", 5.0)),
                    currency=cmd.get("currency", "USD"),
                    message=cmd.get("message", "!cook ramen")
                )

        # Config save
        elif action == "save_config":
            new_cfg = cmd.get("config", {})
            if isinstance(new_cfg, dict):
                # Update in-memory config
                for k, v in new_cfg.items():
                    if isinstance(v, dict) and k in cfg_data:
                        cfg_data[k].update(v)
                    else:
                        cfg_data[k] = v
                # Save to disk if path provided
                if config_path and os.path.exists(os.path.dirname(config_path)):
                    try:
                        with open(config_path, "w", encoding="utf-8") as f:
                            json.dump(cfg_data, f, indent=2)
                        print(f"[StudioBridge] Config successfully saved to {config_path}")
                    except Exception as e:
                        print(f"[StudioBridge] Error saving config: {e}")

    def _send_status(self, state, audio, viewer_sim, cfg_data, chat_poller=None, donate_receiver=None):
        payload = {
            "type": "status",
            "connected": True,
            "timestamp": time.time(),
            "audio": audio.get_status(),
            "game": state.get_summary(),
            "viewer_sim": {
                "enabled": viewer_sim.enabled,
                "min_interval": viewer_sim.min_interval,
                "max_interval": viewer_sim.max_interval
            },
            "youtube": chat_poller.get_status() if chat_poller else {},
            "donate": donate_receiver.get_status() if donate_receiver else {},
            "config": {
                "stream": cfg_data.get("stream", {}),
                "game": cfg_data.get("game", {}),
                "youtube": cfg_data.get("youtube", {}),
                "donate": cfg_data.get("donate", {})
            }
        }
        self.broadcast(payload)

    def stop(self):
        """Stops the IPC server."""
        self.running = False
        with self.clients_lock:
            for c in self.clients:
                try:
                    c.close()
                except Exception:
                    pass
            self.clients.clear()

        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass

"""
Universal International Donate Webhook Service for Cozy Midnight Diner.
Receives donation webhooks from Streamlabs, Ko-fi, PayPal, and custom endpoints.
Converts donation currency to in-game coins, triggers tip animations, and priority-cooks dishes!
"""
import json
import os
import re
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs

from game.config import MENU_ITEMS, COLOR_TEXT_GOLD, COLOR_TEXT_PINK


class DonateHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress noisy standard HTTP logs
        return

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        info = {
            "service": "Cozy Midnight Diner Donate Webhook",
            "status": "online",
            "supported_gateways": ["Streamlabs", "Ko-fi", "PayPal", "Generic POST"],
            "endpoints": ["/webhook/donate", "/webhook/streamlabs", "/webhook/kofi"]
        }
        self.wfile.write(json.dumps(info).encode("utf-8"))

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len)

        receiver = getattr(self.server, "donate_receiver", None)
        if not receiver:
            self.send_response(500)
            self.end_headers()
            return

        content_type = self.headers.get("Content-Type", "")
        payload = {}

        try:
            if "application/json" in content_type:
                payload = json.loads(post_body.decode("utf-8", errors="ignore"))
            elif "application/x-www-form-urlencoded" in content_type:
                parsed_form = parse_qs(post_body.decode("utf-8", errors="ignore"))
                # Ko-fi sends form field 'data' with a JSON string
                if "data" in parsed_form:
                    payload = json.loads(parsed_form["data"][0])
                else:
                    payload = {k: v[0] for k, v in parsed_form.items()}
            else:
                # Try JSON fallback
                payload = json.loads(post_body.decode("utf-8", errors="ignore"))
        except Exception as e:
            print(f"[DonateReceiver] Error parsing webhook payload: {e}")
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error": "Invalid payload format"}')
            return

        success, result_msg = receiver.process_donation(payload)

        self.send_response(200 if success else 400)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        resp = {"success": success, "message": result_msg}
        self.wfile.write(json.dumps(resp).encode("utf-8"))


class DonateReceiver:
    def __init__(self, game_state, command_dispatcher, port=8088, config_path=None):
        self.state = game_state
        self.dispatcher = command_dispatcher
        self.port = port
        self.config_path = config_path
        self.server = None
        self.thread = None
        self.running = False
        self.enabled = True
        self.secret_token = ""
        self.usd_to_coins = 100  # Default: $1.00 USD = 100 game coins
        self.auto_cook_on_message = True
        self.last_donation = None
        self.total_donations_count = 0
        self.total_donated_usd = 0.0

        if config_path and os.path.exists(config_path):
            self.load_config(config_path)

    def load_config(self, config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                d_conf = data.get("donate", {})
                self.enabled = d_conf.get("enabled", True)
                self.port = int(d_conf.get("webhook_port", 8088))
                self.secret_token = d_conf.get("webhook_secret", "").strip()
                self.usd_to_coins = int(d_conf.get("usd_to_coins", 100))
                self.auto_cook_on_message = d_conf.get("auto_cook_on_message", True)
        except Exception as e:
            print(f"[DonateReceiver] Error loading config: {e}")

    def start(self):
        if not self.enabled:
            print("[DonateReceiver] Donate Webhook is disabled in config.")
            return False

        try:
            self.server = HTTPServer(("0.0.0.0", self.port), DonateHandler)
            self.server.donate_receiver = self
            self.running = True
            self.thread = threading.Thread(target=self._run_server, daemon=True, name="DonateWebhookServer")
            self.thread.start()
            print(f"[DonateReceiver] Universal Donate Webhook active on http://0.0.0.0:{self.port}/webhook/donate")
            return True
        except Exception as e:
            print(f"[DonateReceiver] Failed to start Donate Webhook server on port {self.port}: {e}")
            self.running = False
            return False

    def _run_server(self):
        while self.running and self.server:
            try:
                self.server.handle_request()
            except Exception:
                break

    def stop(self):
        self.running = False
        if self.server:
            try:
                self.server.server_close()
            except Exception:
                pass
        self.server = None
        print("[DonateReceiver] Donate Webhook server stopped.")

    def process_donation(self, payload):
        """Parses donation payload from Streamlabs, Ko-fi, or PayPal."""
        # 1. Extract donor name
        name = (
            payload.get("from_name") or
            payload.get("name") or
            payload.get("donor") or
            payload.get("user") or
            payload.get("username") or
            "Generous Guest"
        ).strip()
        formatted_user = name if name.startswith("@") else f"@{name}"

        # 2. Extract amount and currency
        raw_amount = payload.get("amount", 1.0)
        currency = payload.get("currency", "USD").upper()
        try:
            amount_val = float(raw_amount)
        except (ValueError, TypeError):
            amount_val = 1.0

        # 3. Extract message
        message = (payload.get("message") or payload.get("comment") or "").strip()

        # 4. Convert to game coins
        coins = int(amount_val * self.usd_to_coins)
        if coins < 10:
            coins = 10

        self.total_donations_count += 1
        self.total_donated_usd += amount_val
        self.last_donation = {
            "user": formatted_user,
            "amount": amount_val,
            "currency": currency,
            "coins": coins,
            "message": message,
            "time": time.strftime("%H:%M:%S")
        }

        # 5. Trigger game state tip & event
        self.state.tip(formatted_user, coins)

        # 6. Check for dish order command in the donation message
        dish_ordered = None
        if self.auto_cook_on_message and message:
            # Check for !cook <dish>
            cook_match = re.search(r"!(?:cook|order|nau)\s+([a-zA-Z0-9_-]+)", message, re.IGNORECASE)
            dish_query = cook_match.group(1).lower() if cook_match else ""

            if not dish_query:
                # Check if message mentions any known dish
                for key, data in MENU_ITEMS.items():
                    if key in message.lower() or data["name"].lower() in message.lower():
                        dish_query = key
                        break

            if dish_query:
                matched_key = None
                for key, data in MENU_ITEMS.items():
                    if key in dish_query or data["name"].lower() in dish_query:
                        matched_key = key
                        break
                if not matched_key and dish_query in MENU_ITEMS:
                    matched_key = dish_query

                if matched_key:
                    dish_name = MENU_ITEMS[matched_key]["name"]
                    dish_ordered = dish_name
                    # VIP Priority: Place directly at the front of queue or start cooking
                    self.state.order_queue.insert(0, {
                        "user": f"⭐ {formatted_user}",
                        "key": matched_key,
                        "name": f"VIP {dish_name}"
                    })
                    self.state.add_chat("VIP", f"⭐ {formatted_user} ordered {dish_name} with ${amount_val:.2f} tip!", COLOR_TEXT_GOLD)

        log_msg = f"[DonateReceiver] Received donation from {formatted_user}: ${amount_val:.2f} {currency} -> {coins} coins"
        if dish_ordered:
            log_msg += f" (VIP Dish: {dish_ordered})"
        print(log_msg)
        return True, log_msg

    def simulate_donation(self, user="@Alex", amount=5.0, currency="USD", message="Love this diner! !cook ramen"):
        """Locally tests donation processing without external network."""
        payload = {
            "name": user,
            "amount": amount,
            "currency": currency,
            "message": message
        }
        return self.process_donation(payload)

    def get_status(self):
        """Returns JSON-serializable status dictionary for Studio Controller."""
        return {
            "running": self.running,
            "enabled": self.enabled,
            "port": self.port,
            "usd_to_coins": self.usd_to_coins,
            "auto_cook": self.auto_cook_on_message,
            "total_count": self.total_donations_count,
            "total_usd": round(self.total_donated_usd, 2),
            "last_donation": self.last_donation,
            "webhook_url": f"http://localhost:{self.port}/webhook/donate"
        }

"""
Cozy Midnight Diner - Independent Studio Controller
Standalone Desktop GUI (Tkinter) for live audio control, kitchen management,
chat simulator events, stream settings, YouTube Live Chat API, and International Donate Webhook.
Runs independently of the game window; communicates in real-time via local IPC.
"""
import json
import os
import queue
import socket
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

from youtube.chat_poller import extract_video_id, resolve_live_chat_id

# Resolve base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.json")
SOUNDS_DIR = os.path.join(BASE_DIR, "assets", "sounds")

DEFAULT_PORT = 18765

# Color Palette (Dark Midnight theme)
COLOR_BG_DARK = "#0f141d"
COLOR_PANEL_BG = "#161e2b"
COLOR_CARD_BG = "#1c2637"
COLOR_CARD_BORDER = "#2a3952"
COLOR_TEXT_WHITE = "#ffffff"
COLOR_TEXT_MUTED = "#9ba8ba"
COLOR_TEXT_GOLD = "#ffbe3b"
COLOR_ACCENT_ORANGE = "#ff7f38"
COLOR_ACCENT_CYAN = "#45caff"
COLOR_ACCENT_GREEN = "#32d77a"
COLOR_ACCENT_RED = "#ff4f64"
COLOR_INPUT_BG = "#101620"

ALL_MENU_ITEMS = [
    ("ramen", "Tonkotsu Ramen"),
    ("pizza", "Pepperoni Pizza"),
    ("tacos", "Birria Tacos"),
    ("boba", "Boba Milk Tea"),
    ("matcha", "Matcha Parfait"),
    ("curry", "Japanese Katsu Curry"),
    ("dumplings", "Steamy Xiao Long Bao"),
    ("gyoza", "Crispy Pan-fried Gyoza"),
    ("sushi", "Salmon Nigiri Sushi"),
    ("udon", "Golden Tempura Udon"),
    ("waffles", "Belgian Waffle Tower"),
    ("taiyaki", "Honey Glazed Taiyaki"),
    ("matcha_boba", "Matcha Boba Float"),
    ("shoyu_ramen", "Shoyu Ramen Classic"),
    ("pasta", "Creamy Carbonara"),
    ("coffee", "Iced Caramel Latte")
]


def load_local_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "stream": {
            "title": "Cozy Midnight Diner 24/7",
            "canvas_width": 720,
            "canvas_height": 1280,
            "fps": 30,
            "video_bitrate": "3500k",
            "audio_bitrate": "128k",
            "stream_key": ""
        },
        "youtube": {
            "api_key": "",
            "video_id": "",
            "live_chat_id": "",
            "enabled": False,
            "polling_interval": 4.0
        },
        "donate": {
            "enabled": True,
            "webhook_port": 8088,
            "webhook_secret": "",
            "usd_to_coins": 100,
            "auto_cook_on_message": True
        },
        "game": {
            "diner_name": "Cozy Midnight Diner",
            "initial_level": 27,
            "simulate_viewers": True,
            "music_volume": 0.55,
            "sfx_volume": 0.70
        }
    }


def save_local_config(data):
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False


class StudioControllerClient:
    """Manages the background socket connection to the Pygame main game loop."""
    def __init__(self, on_status_callback, port=DEFAULT_PORT):
        self.port = port
        self.on_status = on_status_callback
        self.running = True
        self.sock = None
        self.connected = False
        self.out_queue = queue.Queue()

        self.thread = threading.Thread(target=self._connection_loop, daemon=True, name="StudioClientWorker")
        self.thread.start()

    def send(self, action, **kwargs):
        payload = {"action": action, **kwargs}
        self.out_queue.put(payload)

    def _connection_loop(self):
        while self.running:
            if not self.connected:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(1.5)
                    s.connect(("127.0.0.1", self.port))
                    s.settimeout(0.5)
                    self.sock = s
                    self.connected = True
                except Exception:
                    self.connected = False
                    self.sock = None
                    time.sleep(1.0)
                    continue

            # Connected: handle sending and receiving
            try:
                # 1. Send pending messages
                while not self.out_queue.empty():
                    msg = self.out_queue.get_nowait()
                    line = (json.dumps(msg) + "\n").encode("utf-8")
                    self.sock.sendall(line)

                # 2. Receive status broadcast
                try:
                    raw = self.sock.recv(8192)
                    if not raw:
                        self.connected = False
                        continue
                    lines = raw.decode("utf-8", errors="ignore").splitlines()
                    for line in lines:
                        line = line.strip()
                        if line:
                            try:
                                data = json.loads(line)
                                if self.on_status:
                                    self.on_status(data)
                            except json.JSONDecodeError:
                                pass
                except socket.timeout:
                    pass

            except Exception:
                self.connected = False
                if self.sock:
                    try:
                        self.sock.close()
                    except Exception:
                        pass
                self.sock = None
                time.sleep(1.0)

    def stop(self):
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass


class StudioControllerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🐱 Cozy Midnight Diner - Studio Controller")
        self.root.geometry("960x780")
        self.root.minsize(880, 700)
        self.root.configure(bg=COLOR_BG_DARK)

        # High DPI Awareness
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        self.local_cfg = load_local_config()
        self.game_status = None
        self.is_connected = False
        self.local_preview_player = None

        # Audio variables
        self.var_bgm_vol = tk.DoubleVar(value=self.local_cfg.get("game", {}).get("music_volume", 0.55) * 100)
        self.var_sfx_vol = tk.DoubleVar(value=self.local_cfg.get("game", {}).get("sfx_volume", 0.70) * 100)
        self.var_mute_bgm = tk.BooleanVar(value=False)
        self.var_mute_sfx = tk.BooleanVar(value=False)
        self.var_current_track = tk.StringVar(value="lofi_chill.mp3")

        # Gameplay variables
        self.var_sim_enabled = tk.BooleanVar(value=self.local_cfg.get("game", {}).get("simulate_viewers", True))
        self.var_order_dish = tk.StringVar(value="ramen")
        self.var_order_user = tk.StringVar(value="@Host")
        self.var_level = tk.IntVar(value=self.local_cfg.get("game", {}).get("initial_level", 27))

        # Event variables
        self.var_chat_user = tk.StringVar(value="@Host")
        self.var_chat_msg = tk.StringVar(value="!cook ramen")
        self.var_tip_user = tk.StringVar(value="@SuperFan")
        self.var_tip_amount = tk.IntVar(value=100)

        # Stream config variables
        stream_cfg = self.local_cfg.get("stream", {})
        game_cfg = self.local_cfg.get("game", {})
        self.var_stream_title = tk.StringVar(value=stream_cfg.get("title", "Cozy Midnight Diner 24/7"))
        self.var_stream_key = tk.StringVar(value=stream_cfg.get("stream_key", ""))
        self.var_diner_name = tk.StringVar(value=game_cfg.get("diner_name", "Cozy Midnight Diner"))
        self.var_bitrate = tk.StringVar(value=stream_cfg.get("video_bitrate", "3500k"))
        self.var_audio_bitrate = tk.StringVar(value=stream_cfg.get("audio_bitrate", "128k"))
        self.var_show_key = tk.BooleanVar(value=False)

        # YouTube Live Chat API variables
        yt_cfg = self.local_cfg.get("youtube", {})
        self.var_yt_enabled = tk.BooleanVar(value=yt_cfg.get("enabled", False))
        self.var_yt_api_key = tk.StringVar(value=yt_cfg.get("api_key", ""))
        self.var_yt_video_id = tk.StringVar(value=yt_cfg.get("video_id", ""))
        self.var_yt_chat_id = tk.StringVar(value=yt_cfg.get("live_chat_id", ""))
        self.var_show_yt_key = tk.BooleanVar(value=False)

        # International Donate Webhook variables (Streamlabs / Ko-fi / PayPal)
        donate_cfg = self.local_cfg.get("donate", {})
        self.var_donate_enabled = tk.BooleanVar(value=donate_cfg.get("enabled", True))
        self.var_donate_port = tk.IntVar(value=donate_cfg.get("webhook_port", 8088))
        self.var_donate_rate = tk.IntVar(value=donate_cfg.get("usd_to_coins", 100))
        self.var_donate_autocook = tk.BooleanVar(value=donate_cfg.get("auto_cook_on_message", True))

        # Test donate variables
        self.var_test_donor = tk.StringVar(value="@Alex")
        self.var_test_amount = tk.DoubleVar(value=5.0)
        self.var_test_msg = tk.StringVar(value="Love your stream! !cook ramen")

        self._setup_styles()
        self._build_header()
        self._build_tabs()
        self._build_footer()

        # Connect to game via IPC client
        self.client = StudioControllerClient(self._on_status_received)

        # Polling ticker to update connection badge & UI
        self.root.after(300, self._ui_heartbeat)

    def _setup_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure("TNotebook", background=COLOR_BG_DARK, borderwidth=0)
        style.configure("TNotebook.Tab",
                        background=COLOR_PANEL_BG,
                        foreground=COLOR_TEXT_MUTED,
                        padding=[14, 8],
                        font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", COLOR_CARD_BG)],
                  foreground=[("selected", COLOR_TEXT_GOLD)])

        style.configure("TProgressbar",
                        thickness=14,
                        troughcolor=COLOR_INPUT_BG,
                        background=COLOR_ACCENT_ORANGE)

        style.configure("TCombobox",
                        fieldbackground=COLOR_INPUT_BG,
                        background=COLOR_CARD_BORDER,
                        foreground=COLOR_TEXT_WHITE,
                        arrowcolor=COLOR_TEXT_GOLD)

    def _build_header(self):
        header_frame = tk.Frame(self.root, bg=COLOR_PANEL_BG, padx=18, pady=12)
        header_frame.pack(fill="x", side="top")

        left_box = tk.Frame(header_frame, bg=COLOR_PANEL_BG)
        left_box.pack(side="left")

        title_lbl = tk.Label(left_box, text="🐱 COZY MIDNIGHT DINER", font=("Segoe UI", 15, "bold"),
                             fg=COLOR_TEXT_GOLD, bg=COLOR_PANEL_BG)
        title_lbl.pack(anchor="w")

        sub_lbl = tk.Label(left_box, text="Studio Control Panel — Quản lý Âm thanh, Gameplay, Chat API & Donate",
                           font=("Segoe UI", 9), fg=COLOR_TEXT_MUTED, bg=COLOR_PANEL_BG)
        sub_lbl.pack(anchor="w")

        right_box = tk.Frame(header_frame, bg=COLOR_PANEL_BG)
        right_box.pack(side="right")

        self.status_badge = tk.Label(right_box, text="○ OFFLINE (CONFIG ONLY)",
                                     font=("Segoe UI", 9, "bold"),
                                     bg="#3d181c", fg=COLOR_ACCENT_RED,
                                     padx=10, pady=5, relief="flat")
        self.status_badge.pack(side="right", padx=(10, 0))

        self.btn_launch_game = tk.Button(right_box, text="🚀 Khởi động Game", font=("Segoe UI", 9, "bold"),
                                         bg="#1d3b2c", fg=COLOR_ACCENT_GREEN, activebackground="#29553f",
                                         activeforeground=COLOR_TEXT_WHITE, bd=0, padx=12, pady=5,
                                         command=self._launch_game_process)
        self.btn_launch_game.pack(side="right")

    def _build_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(8, 4))

        self.tab_audio = tk.Frame(self.notebook, bg=COLOR_BG_DARK, padx=14, pady=12)
        self.tab_game = tk.Frame(self.notebook, bg=COLOR_BG_DARK, padx=14, pady=12)
        self.tab_chat = tk.Frame(self.notebook, bg=COLOR_BG_DARK, padx=14, pady=12)
        self.tab_api = tk.Frame(self.notebook, bg=COLOR_BG_DARK, padx=14, pady=12)
        self.tab_config = tk.Frame(self.notebook, bg=COLOR_BG_DARK, padx=14, pady=12)

        self.notebook.add(self.tab_audio, text=" 🎵 Âm thanh & Nhạc ")
        self.notebook.add(self.tab_game, text=" 🍳 Bếp & Gameplay ")
        self.notebook.add(self.tab_chat, text=" 💬 Sự kiện & Chat Sim ")
        self.notebook.add(self.tab_api, text=" 🌐 API (YouTube & Donate) ")
        self.notebook.add(self.tab_config, text=" 📡 Cài đặt Stream ")

        self._build_tab_audio()
        self._build_tab_game()
        self._build_tab_chat()
        self._build_tab_api()
        self._build_tab_config()

    # ---------------- TAB 1: AUDIO ----------------
    def _build_tab_audio(self):
        parent = self.tab_audio

        # Card 1: Background Music (BGM)
        card_bgm = self._create_card(parent, "🎵 NHẠC NỀN (BACKGROUND MUSIC - BGM)")
        card_bgm.pack(fill="x", pady=(0, 10))

        # Slider BGM
        row1 = tk.Frame(card_bgm, bg=COLOR_CARD_BG)
        row1.pack(fill="x", pady=4)
        tk.Label(row1, text="Âm lượng BGM:", font=("Segoe UI", 10), fg=COLOR_TEXT_WHITE, bg=COLOR_CARD_BG, width=14, anchor="w").pack(side="left")

        self.scale_bgm = tk.Scale(row1, from_=0, to=100, orient="horizontal", variable=self.var_bgm_vol,
                                  bg=COLOR_CARD_BG, fg=COLOR_TEXT_GOLD, highlightthickness=0,
                                  troughcolor=COLOR_INPUT_BG, activebackground=COLOR_ACCENT_ORANGE,
                                  command=self._on_bgm_vol_change)
        self.scale_bgm.pack(side="left", fill="x", expand=True, padx=8)

        self.lbl_bgm_val = tk.Label(row1, text=f"{int(self.var_bgm_vol.get())}%", font=("Segoe UI", 10, "bold"),
                                    fg=COLOR_TEXT_GOLD, bg=COLOR_CARD_BG, width=5)
        self.lbl_bgm_val.pack(side="left")

        chk_mute_bgm = tk.Checkbutton(row1, text="🔇 Tắt tiếng BGM", variable=self.var_mute_bgm,
                                      font=("Segoe UI", 9, "bold"), fg=COLOR_TEXT_WHITE, bg=COLOR_CARD_BG,
                                      selectcolor=COLOR_INPUT_BG, activebackground=COLOR_CARD_BG,
                                      command=self._on_mute_bgm_toggle)
        chk_mute_bgm.pack(side="left", padx=10)

        # Track switcher
        row2 = tk.Frame(card_bgm, bg=COLOR_CARD_BG)
        row2.pack(fill="x", pady=6)
        tk.Label(row2, text="Bài nhạc:", font=("Segoe UI", 10), fg=COLOR_TEXT_WHITE, bg=COLOR_CARD_BG, width=14, anchor="w").pack(side="left")

        available_tracks = self._get_sound_tracks()
        self.combo_tracks = ttk.Combobox(row2, textvariable=self.var_current_track, values=available_tracks, state="readonly", width=30)
        self.combo_tracks.pack(side="left", padx=8)

        btn_switch_track = tk.Button(row2, text="▶ Đổi bài ngay", font=("Segoe UI", 9, "bold"),
                                     bg="#2a4563", fg=COLOR_ACCENT_CYAN, activebackground="#3a5d85",
                                     bd=0, padx=10, pady=3, command=self._switch_track)
        btn_switch_track.pack(side="left", padx=4)

        btn_refresh_tracks = tk.Button(row2, text="🔄 Quét thư mục", font=("Segoe UI", 9),
                                       bg="#242e3f", fg=COLOR_TEXT_MUTED, bd=0, padx=8, pady=3,
                                       command=self._refresh_tracks)
        btn_refresh_tracks.pack(side="left")

        # Card 2: Sound Effects (SFX)
        card_sfx = self._create_card(parent, "🔊 HIỆU ỨNG ÂM THANH (SOUND EFFECTS - SFX)")
        card_sfx.pack(fill="x", pady=(0, 10))

        # Slider SFX
        sfx_row1 = tk.Frame(card_sfx, bg=COLOR_CARD_BG)
        sfx_row1.pack(fill="x", pady=4)
        tk.Label(sfx_row1, text="Âm lượng SFX:", font=("Segoe UI", 10), fg=COLOR_TEXT_WHITE, bg=COLOR_CARD_BG, width=14, anchor="w").pack(side="left")

        self.scale_sfx = tk.Scale(sfx_row1, from_=0, to=100, orient="horizontal", variable=self.var_sfx_vol,
                                  bg=COLOR_CARD_BG, fg=COLOR_TEXT_GOLD, highlightthickness=0,
                                  troughcolor=COLOR_INPUT_BG, activebackground=COLOR_ACCENT_ORANGE,
                                  command=self._on_sfx_vol_change)
        self.scale_sfx.pack(side="left", fill="x", expand=True, padx=8)

        self.lbl_sfx_val = tk.Label(sfx_row1, text=f"{int(self.var_sfx_vol.get())}%", font=("Segoe UI", 10, "bold"),
                                    fg=COLOR_TEXT_GOLD, bg=COLOR_CARD_BG, width=5)
        self.lbl_sfx_val.pack(side="left")

        chk_mute_sfx = tk.Checkbutton(sfx_row1, text="🔇 Tắt tiếng SFX", variable=self.var_mute_sfx,
                                      font=("Segoe UI", 9, "bold"), fg=COLOR_TEXT_WHITE, bg=COLOR_CARD_BG,
                                      selectcolor=COLOR_INPUT_BG, activebackground=COLOR_CARD_BG,
                                      command=self._on_mute_sfx_toggle)
        chk_mute_sfx.pack(side="left", padx=10)

        # SFX Test Buttons
        sfx_box = tk.LabelFrame(card_sfx, text="Thử nghiệm âm thanh trực tiếp (Click để nghe)",
                                font=("Segoe UI", 9, "italic"), fg=COLOR_TEXT_MUTED, bg=COLOR_CARD_BG, padx=8, pady=8)
        sfx_box.pack(fill="x", pady=6)

        btn_bell = tk.Button(sfx_box, text="🔔 Chuông Xong Món\n(bell_ding.wav)", font=("Segoe UI", 9, "bold"),
                             bg="#2b3d30", fg=COLOR_ACCENT_GREEN, bd=0, padx=12, pady=6,
                             command=lambda: self._test_sfx("bell"))
        btn_bell.pack(side="left", expand=True, fill="x", padx=4)

        btn_coin = tk.Button(sfx_box, text="💰 Tiền Xu Tip\n(coin_chime.wav)", font=("Segoe UI", 9, "bold"),
                             bg="#40361e", fg=COLOR_TEXT_GOLD, bd=0, padx=12, pady=6,
                             command=lambda: self._test_sfx("coin"))
        btn_coin.pack(side="left", expand=True, fill="x", padx=4)

        btn_pop = tk.Button(sfx_box, text="💖 Pop Thả Tim\n(pop.wav)", font=("Segoe UI", 9, "bold"),
                            bg="#45243b", fg="#ff7cb8", bd=0, padx=12, pady=6,
                            command=lambda: self._test_sfx("pop"))
        btn_pop.pack(side="left", expand=True, fill="x", padx=4)

        btn_sizzle = tk.Button(sfx_box, text="🔥 Tiếng Xèo Xèo\n(sizzle.wav)", font=("Segoe UI", 9, "bold"),
                               bg="#42251a", fg=COLOR_ACCENT_ORANGE, bd=0, padx=12, pady=6,
                               command=lambda: self._test_sfx("sizzle"))
        btn_sizzle.pack(side="left", expand=True, fill="x", padx=4)

        # Quick Save Volumes Button
        btn_save_vols = tk.Button(parent, text="💾 Lưu âm lượng hiện tại làm MẶC ĐỊNH vào config.json",
                                  font=("Segoe UI", 10, "bold"), bg="#1d3b2c", fg=COLOR_ACCENT_GREEN,
                                  activebackground="#29553f", activeforeground=COLOR_TEXT_WHITE,
                                  bd=0, pady=8, command=self._save_default_volumes)
        btn_save_vols.pack(fill="x", pady=10)

    # ---------------- TAB 2: GAMEPLAY ----------------
    def _build_tab_game(self):
        parent = self.tab_game

        # Card 1: Live Dish & Cooking Status
        card_dish = self._create_card(parent, "🍳 MÓN ĂN ĐANG NẤU TRỰC TIẾP")
        card_dish.pack(fill="x", pady=(0, 10))

        self.lbl_current_dish = tk.Label(card_dish, text="Hiện không có món nào đang nấu",
                                         font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT_GOLD, bg=COLOR_CARD_BG, anchor="w")
        self.lbl_current_dish.pack(fill="x", pady=(0, 2))

        self.lbl_current_step = tk.Label(card_dish, text="Đầu bếp đang chuẩn bị...",
                                         font=("Segoe UI", 9, "italic"), fg=COLOR_TEXT_MUTED, bg=COLOR_CARD_BG, anchor="w")
        self.lbl_current_step.pack(fill="x", pady=(0, 4))

        self.prog_dish = ttk.Progressbar(card_dish, orient="horizontal", mode="determinate")
        self.prog_dish.pack(fill="x", pady=4)

        dish_btn_box = tk.Frame(card_dish, bg=COLOR_CARD_BG)
        dish_btn_box.pack(fill="x", pady=4)

        btn_instant = tk.Button(dish_btn_box, text="⚡ Nấu xong ngay (Instant Finish)", font=("Segoe UI", 9, "bold"),
                                bg="#2b3d30", fg=COLOR_ACCENT_GREEN, bd=0, padx=12, pady=4,
                                command=self._instant_finish)
        btn_instant.pack(side="left", padx=(0, 6))

        btn_skip = tk.Button(dish_btn_box, text="⏭️ Hủy / Bỏ qua món (Skip)", font=("Segoe UI", 9, "bold"),
                             bg="#3d1f22", fg=COLOR_ACCENT_RED, bd=0, padx=12, pady=4,
                             command=self._skip_dish)
        btn_skip.pack(side="left")

        # Card 2: Manual Order Dispatch
        card_order = self._create_card(parent, "📋 GỌI MÓN VÀO HÀNG ĐỢI (MANUAL DISPATCH)")
        card_order.pack(fill="x", pady=(0, 10))

        order_row = tk.Frame(card_order, bg=COLOR_CARD_BG)
        order_row.pack(fill="x", pady=4)

        tk.Label(order_row, text="Món ăn:", font=("Segoe UI", 10), fg=COLOR_TEXT_WHITE, bg=COLOR_CARD_BG).pack(side="left", padx=(0, 6))
        dish_names = [f"{name} ({key})" for key, name in ALL_MENU_ITEMS]
        self.combo_order_dish = ttk.Combobox(order_row, values=dish_names, state="readonly", width=26)
        self.combo_order_dish.current(0)
        self.combo_order_dish.pack(side="left", padx=(0, 12))

        tk.Label(order_row, text="Người order:", font=("Segoe UI", 10), fg=COLOR_TEXT_WHITE, bg=COLOR_CARD_BG).pack(side="left", padx=(0, 6))
        ent_user = tk.Entry(order_row, textvariable=self.var_order_user, font=("Segoe UI", 10),
                            bg=COLOR_INPUT_BG, fg=COLOR_TEXT_WHITE, insertbackground=COLOR_TEXT_WHITE, width=12)
        ent_user.pack(side="left", padx=(0, 10))

        btn_add_order = tk.Button(order_row, text="➕ Thêm vào hàng đợi", font=("Segoe UI", 9, "bold"),
                                  bg="#2a4563", fg=COLOR_ACCENT_CYAN, bd=0, padx=12, pady=4,
                                  command=self._dispatch_order)
        btn_add_order.pack(side="left")

        # Card 3: Queue & Diner Level
        row_split = tk.Frame(parent, bg=COLOR_BG_DARK)
        row_split.pack(fill="both", expand=True)

        card_queue = self._create_card(row_split, "📦 HÀNG ĐỢI NẤU (QUEUE)")
        card_queue.pack(side="left", fill="both", expand=True, padx=(0, 6))

        self.list_queue = tk.Listbox(card_queue, font=("Segoe UI", 9), bg=COLOR_INPUT_BG, fg=COLOR_TEXT_WHITE,
                                     selectbackground=COLOR_CARD_BORDER, bd=0, highlightthickness=0, height=5)
        self.list_queue.pack(fill="both", expand=True, pady=4)

        btn_clear_q = tk.Button(card_queue, text="🗑️ Xóa sạch hàng đợi", font=("Segoe UI", 8, "bold"),
                                bg="#3d1f22", fg=COLOR_ACCENT_RED, bd=0, pady=3,
                                command=self._clear_queue)
        btn_clear_q.pack(fill="x", pady=2)

        card_stats = self._create_card(row_split, "⭐ CHỈ SỐ QUÁN ĂN")
        card_stats.pack(side="right", fill="both", expand=True, padx=(6, 0))

        self.lbl_level_info = tk.Label(card_stats, text="Level: Lv. 27 | EXP: 1250 / 2000",
                                       font=("Segoe UI", 10, "bold"), fg=COLOR_TEXT_GOLD, bg=COLOR_CARD_BG)
        self.lbl_level_info.pack(fill="x", pady=6)

        lvl_ctrl = tk.Frame(card_stats, bg=COLOR_CARD_BG)
        lvl_ctrl.pack(fill="x", pady=4)
        tk.Label(lvl_ctrl, text="Đổi Level:", font=("Segoe UI", 9), fg=COLOR_TEXT_WHITE, bg=COLOR_CARD_BG).pack(side="left", padx=(0, 6))
        sp_lvl = tk.Spinbox(lvl_ctrl, from_=1, to=99, textvariable=self.var_level, width=6,
                            bg=COLOR_INPUT_BG, fg=COLOR_TEXT_WHITE, insertbackground=COLOR_TEXT_WHITE)
        sp_lvl.pack(side="left", padx=(0, 8))
        btn_set_lvl = tk.Button(lvl_ctrl, text="Áp dụng Level", font=("Segoe UI", 9, "bold"),
                                bg="#2a4563", fg=COLOR_ACCENT_CYAN, bd=0, padx=8, pady=2,
                                command=self._set_level)
        btn_set_lvl.pack(side="left")

    # ---------------- TAB 3: CHAT & EVENTS ----------------
    def _build_tab_chat(self):
        parent = self.tab_chat

        # Card 1: Viewer Simulator
        card_sim = self._create_card(parent, "🤖 GIẢ LẬP VIEWER YOUTUBE (VIEWER SIMULATOR)")
        card_sim.pack(fill="x", pady=(0, 10))

        sim_row = tk.Frame(card_sim, bg=COLOR_CARD_BG)
        sim_row.pack(fill="x", pady=4)

        chk_sim = tk.Checkbutton(sim_row, text="Bật chế độ Giả lập tương tác (Tự động chat, gọi món, thả tim, tip)",
                                 variable=self.var_sim_enabled, font=("Segoe UI", 10, "bold"),
                                 fg=COLOR_TEXT_GOLD, bg=COLOR_CARD_BG, selectcolor=COLOR_INPUT_BG,
                                 activebackground=COLOR_CARD_BG, command=self._toggle_sim)
        chk_sim.pack(side="left")

        # Card 2: Interactive Event Triggers
        card_events = self._create_card(parent, "⚡ MÔ PHỎNG SỰ KIỆN TƯƠNG TÁC (QUICK TRIGGERS)")
        card_events.pack(fill="x", pady=(0, 10))

        ev_row1 = tk.Frame(card_events, bg=COLOR_CARD_BG)
        ev_row1.pack(fill="x", pady=4)

        btn_cheer = tk.Button(ev_row1, text="💖 Cổ vũ / Thả tim (!yum)", font=("Segoe UI", 9, "bold"),
                              bg="#45243b", fg="#ff7cb8", bd=0, padx=12, pady=6,
                              command=self._trigger_cheer)
        btn_cheer.pack(side="left", padx=(0, 8))

        btn_levelup = tk.Button(ev_row1, text="🎉 Thử nghiệm Lên Cấp (Level Up)", font=("Segoe UI", 9, "bold"),
                                bg="#40361e", fg=COLOR_TEXT_GOLD, bd=0, padx=12, pady=6,
                                command=self._trigger_levelup)
        btn_levelup.pack(side="left")

        # Tip / Donate simulator
        ev_row2 = tk.Frame(card_events, bg=COLOR_CARD_BG)
        ev_row2.pack(fill="x", pady=6)

        tk.Label(ev_row2, text="Người Tip:", font=("Segoe UI", 9), fg=COLOR_TEXT_WHITE, bg=COLOR_CARD_BG).pack(side="left", padx=(0, 4))
        ent_tip_u = tk.Entry(ev_row2, textvariable=self.var_tip_user, width=12,
                             bg=COLOR_INPUT_BG, fg=COLOR_TEXT_WHITE, insertbackground=COLOR_TEXT_WHITE)
        ent_tip_u.pack(side="left", padx=(0, 8))

        tk.Label(ev_row2, text="Coins:", font=("Segoe UI", 9), fg=COLOR_TEXT_WHITE, bg=COLOR_CARD_BG).pack(side="left", padx=(0, 4))
        for coin_val in [50, 100, 200, 500]:
            btn_c = tk.Button(ev_row2, text=f"{coin_val}", font=("Segoe UI", 8, "bold"),
                              bg=COLOR_CARD_BORDER, fg=COLOR_TEXT_WHITE, bd=0, padx=6, pady=2,
                              command=lambda v=coin_val: self.var_tip_amount.set(v))
            btn_c.pack(side="left", padx=2)

        sp_coins = tk.Spinbox(ev_row2, from_=10, to=5000, increment=50, textvariable=self.var_tip_amount, width=6,
                              bg=COLOR_INPUT_BG, fg=COLOR_TEXT_WHITE, insertbackground=COLOR_TEXT_WHITE)
        sp_coins.pack(side="left", padx=(6, 8))

        btn_send_tip = tk.Button(ev_row2, text="💰 Gửi Tip Donate", font=("Segoe UI", 9, "bold"),
                                 bg="#2b3d30", fg=COLOR_ACCENT_GREEN, bd=0, padx=12, pady=4,
                                 command=self._trigger_tip)
        btn_send_tip.pack(side="left")

        # Card 3: Send Custom Chat & Live Chat Log
        card_chat = self._create_card(parent, "💬 GỬI CHAT & LIVE CHAT FEED")
        card_chat.pack(fill="both", expand=True)

        chat_input_row = tk.Frame(card_chat, bg=COLOR_CARD_BG)
        chat_input_row.pack(fill="x", pady=4)

        tk.Label(chat_input_row, text="User:", font=("Segoe UI", 9), fg=COLOR_TEXT_WHITE, bg=COLOR_CARD_BG).pack(side="left", padx=(0, 4))
        ent_cuser = tk.Entry(chat_input_row, textvariable=self.var_chat_user, width=12,
                             bg=COLOR_INPUT_BG, fg=COLOR_TEXT_WHITE, insertbackground=COLOR_TEXT_WHITE)
        ent_cuser.pack(side="left", padx=(0, 8))

        tk.Label(chat_input_row, text="Tin nhắn:", font=("Segoe UI", 9), fg=COLOR_TEXT_WHITE, bg=COLOR_CARD_BG).pack(side="left", padx=(0, 4))
        ent_cmsg = tk.Entry(chat_input_row, textvariable=self.var_chat_msg,
                            bg=COLOR_INPUT_BG, fg=COLOR_TEXT_WHITE, insertbackground=COLOR_TEXT_WHITE)
        ent_cmsg.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ent_cmsg.bind("<Return>", lambda e: self._send_custom_chat())

        btn_send_chat = tk.Button(chat_input_row, text="📤 Gửi Chat", font=("Segoe UI", 9, "bold"),
                                  bg="#2a4563", fg=COLOR_ACCENT_CYAN, bd=0, padx=12, pady=4,
                                  command=self._send_custom_chat)
        btn_send_chat.pack(side="right")

        self.list_chats = tk.Listbox(card_chat, font=("Segoe UI", 9), bg=COLOR_INPUT_BG, fg=COLOR_TEXT_WHITE,
                                     selectbackground=COLOR_CARD_BORDER, bd=0, highlightthickness=0, height=4)
        self.list_chats.pack(fill="both", expand=True, pady=4)

    # ---------------- TAB 4: API (YOUTUBE & DONATE) ----------------
    def _build_tab_api(self):
        parent = self.tab_api

        # Card 1: YouTube Live Chat API
        card_yt = self._create_card(parent, "📺 YOUTUBE LIVE CHAT API (ĐỌC BÌNH LUẬN TRỰC TIẾP)")
        card_yt.pack(fill="x", pady=(0, 10))

        yt_chk_row = tk.Frame(card_yt, bg=COLOR_CARD_BG)
        yt_chk_row.pack(fill="x", pady=2)
        chk_yt = tk.Checkbutton(yt_chk_row, text="Bật kết nối đọc bình luận từ YouTube Live Chat",
                                variable=self.var_yt_enabled, font=("Segoe UI", 10, "bold"),
                                fg=COLOR_TEXT_GOLD, bg=COLOR_CARD_BG, selectcolor=COLOR_INPUT_BG,
                                activebackground=COLOR_CARD_BG, command=self._on_yt_toggle)
        chk_yt.pack(side="left")

        self.lbl_yt_badge = tk.Label(yt_chk_row, text="⚪ Chưa kích hoạt", font=("Segoe UI", 9, "bold"),
                                     bg="#242e3f", fg=COLOR_TEXT_MUTED, padx=8, pady=2)
        self.lbl_yt_badge.pack(side="right")

        # YouTube API Key
        r_key = tk.Frame(card_yt, bg=COLOR_CARD_BG)
        r_key.pack(fill="x", pady=4)
        tk.Label(r_key, text="Google API Key:", font=("Segoe UI", 10), fg=COLOR_TEXT_WHITE, bg=COLOR_CARD_BG, width=18, anchor="w").pack(side="left")
        self.ent_yt_key = tk.Entry(r_key, textvariable=self.var_yt_api_key, font=("Segoe UI", 10), show="*",
                                   bg=COLOR_INPUT_BG, fg=COLOR_TEXT_WHITE, insertbackground=COLOR_TEXT_WHITE)
        self.ent_yt_key.pack(side="left", fill="x", expand=True, padx=(0, 6))

        chk_show_yt = tk.Checkbutton(r_key, text="👁️ Hiện Key", variable=self.var_show_yt_key,
                                     font=("Segoe UI", 9), fg=COLOR_TEXT_WHITE, bg=COLOR_CARD_BG,
                                     selectcolor=COLOR_INPUT_BG, activebackground=COLOR_CARD_BG,
                                     command=self._toggle_show_yt_key)
        chk_show_yt.pack(side="left")

        # YouTube Stream URL or Video ID
        r_vid = tk.Frame(card_yt, bg=COLOR_CARD_BG)
        r_vid.pack(fill="x", pady=4)
        tk.Label(r_vid, text="Stream URL / Video ID:", font=("Segoe UI", 10), fg=COLOR_TEXT_WHITE, bg=COLOR_CARD_BG, width=18, anchor="w").pack(side="left")
        ent_vid = tk.Entry(r_vid, textvariable=self.var_yt_video_id, font=("Segoe UI", 10),
                           bg=COLOR_INPUT_BG, fg=COLOR_TEXT_WHITE, insertbackground=COLOR_TEXT_WHITE)
        ent_vid.pack(side="left", fill="x", expand=True, padx=(0, 6))

        btn_test_yt = tk.Button(r_vid, text="🔍 Dò Live Chat ID", font=("Segoe UI", 9, "bold"),
                                bg="#2a4563", fg=COLOR_ACCENT_CYAN, activebackground="#3a5d85",
                                bd=0, padx=12, pady=3, command=self._test_and_resolve_yt_chat)
        btn_test_yt.pack(side="left")

        # Live Chat ID (auto-resolved)
        r_cid = tk.Frame(card_yt, bg=COLOR_CARD_BG)
        r_cid.pack(fill="x", pady=2)
        tk.Label(r_cid, text="Active Live Chat ID:", font=("Segoe UI", 9), fg=COLOR_TEXT_MUTED, bg=COLOR_CARD_BG, width=18, anchor="w").pack(side="left")
        self.lbl_yt_cid = tk.Label(r_cid, textvariable=self.var_yt_chat_id, font=("Segoe UI", 9, "italic"),
                                   fg=COLOR_ACCENT_GREEN, bg=COLOR_CARD_BG, anchor="w")
        self.lbl_yt_cid.pack(side="left", fill="x", expand=True)

        # Card 2: International Donate Webhook
        card_dn = self._create_card(parent, "💰 DONATE QUỐC TẾ (STREAMLABS / KO-FI / PAYPAL)")
        card_dn.pack(fill="both", expand=True, pady=(0, 8))

        dn_row1 = tk.Frame(card_dn, bg=COLOR_CARD_BG)
        dn_row1.pack(fill="x", pady=2)
        chk_dn = tk.Checkbutton(dn_row1, text="Bật Donate Webhook Server (Nhận tiền & ưu tiên nấu món)",
                                variable=self.var_donate_enabled, font=("Segoe UI", 10, "bold"),
                                fg=COLOR_TEXT_GOLD, bg=COLOR_CARD_BG, selectcolor=COLOR_INPUT_BG,
                                activebackground=COLOR_CARD_BG, command=self._on_donate_toggle)
        chk_dn.pack(side="left")

        self.lbl_dn_badge = tk.Label(dn_row1, text="🟢 Webhook Port 8088 Active", font=("Segoe UI", 9, "bold"),
                                     bg="#123a22", fg=COLOR_ACCENT_GREEN, padx=8, pady=2)
        self.lbl_dn_badge.pack(side="right")

        # Webhook URL display
        dn_url_row = tk.Frame(card_dn, bg=COLOR_CARD_BG)
        dn_url_row.pack(fill="x", pady=4)
        tk.Label(dn_url_row, text="Webhook Endpoint:", font=("Segoe UI", 9), fg=COLOR_TEXT_WHITE, bg=COLOR_CARD_BG, width=18, anchor="w").pack(side="left")
        self.lbl_hook_url = tk.Label(dn_url_row, text="http://localhost:8088/webhook/donate", font=("Segoe UI", 9, "bold"),
                                     fg=COLOR_ACCENT_CYAN, bg=COLOR_INPUT_BG, padx=8, pady=3, anchor="w")
        self.lbl_hook_url.pack(side="left", fill="x", expand=True, padx=(0, 6))

        btn_copy_url = tk.Button(dn_url_row, text="📋 Copy", font=("Segoe UI", 8), bg=COLOR_CARD_BORDER,
                                 fg=COLOR_TEXT_WHITE, bd=0, padx=8, pady=2, command=self._copy_webhook_url)
        btn_copy_url.pack(side="left")

        # Conversion rate & auto-cook options
        dn_opt_row = tk.Frame(card_dn, bg=COLOR_CARD_BG)
        dn_opt_row.pack(fill="x", pady=4)
        tk.Label(dn_opt_row, text="Tỷ lệ: 1 USD =", font=("Segoe UI", 9), fg=COLOR_TEXT_WHITE, bg=COLOR_CARD_BG).pack(side="left", padx=(0, 4))
        sp_rate = tk.Spinbox(dn_opt_row, from_=10, to=2000, increment=25, textvariable=self.var_donate_rate, width=6,
                             bg=COLOR_INPUT_BG, fg=COLOR_TEXT_WHITE, insertbackground=COLOR_TEXT_WHITE)
        sp_rate.pack(side="left", padx=(0, 8))
        tk.Label(dn_opt_row, text="Coins", font=("Segoe UI", 9), fg=COLOR_TEXT_GOLD, bg=COLOR_CARD_BG).pack(side="left", padx=(0, 16))

        chk_autocook = tk.Checkbutton(dn_opt_row, text="⭐ Tự động ưu tiên nấu món khi tin nhắn donate có tên món (!cook ...)",
                                      variable=self.var_donate_autocook, font=("Segoe UI", 9),
                                      fg=COLOR_TEXT_WHITE, bg=COLOR_CARD_BG, selectcolor=COLOR_INPUT_BG,
                                      activebackground=COLOR_CARD_BG, command=self._on_donate_toggle)
        chk_autocook.pack(side="left")

        # Live donation stats
        self.lbl_dn_stats = tk.Label(card_dn, text="Tổng tiền đã nhận: 0 lượt ($0.00 USD) | Chưa có donate mới",
                                     font=("Segoe UI", 9, "italic"), fg=COLOR_TEXT_MUTED, bg=COLOR_CARD_BG, anchor="w")
        self.lbl_dn_stats.pack(fill="x", pady=4)

        # Simulator Box
        test_box = tk.LabelFrame(card_dn, text="Thử nghiệm mô phỏng Donate (Test Streamlabs / Ko-fi)",
                                 font=("Segoe UI", 9, "italic"), fg=COLOR_TEXT_MUTED, bg=COLOR_CARD_BG, padx=8, pady=6)
        test_box.pack(fill="x", pady=4)

        t_row = tk.Frame(test_box, bg=COLOR_CARD_BG)
        t_row.pack(fill="x", pady=2)
        tk.Label(t_row, text="Donor:", font=("Segoe UI", 9), fg=COLOR_TEXT_WHITE, bg=COLOR_CARD_BG).pack(side="left", padx=(0, 4))
        tk.Entry(t_row, textvariable=self.var_test_donor, width=12,
                 bg=COLOR_INPUT_BG, fg=COLOR_TEXT_WHITE, insertbackground=COLOR_TEXT_WHITE).pack(side="left", padx=(0, 8))

        tk.Label(t_row, text="USD ($):", font=("Segoe UI", 9), fg=COLOR_TEXT_WHITE, bg=COLOR_CARD_BG).pack(side="left", padx=(0, 4))
        tk.Spinbox(t_row, from_=1.0, to=500.0, increment=5.0, textvariable=self.var_test_amount, width=6,
                   bg=COLOR_INPUT_BG, fg=COLOR_TEXT_WHITE, insertbackground=COLOR_TEXT_WHITE).pack(side="left", padx=(0, 8))

        tk.Label(t_row, text="Lời nhắn:", font=("Segoe UI", 9), fg=COLOR_TEXT_WHITE, bg=COLOR_CARD_BG).pack(side="left", padx=(0, 4))
        tk.Entry(t_row, textvariable=self.var_test_msg,
                 bg=COLOR_INPUT_BG, fg=COLOR_TEXT_WHITE, insertbackground=COLOR_TEXT_WHITE).pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn_sim_dn = tk.Button(t_row, text="🧪 Bắn Donate Thử ($)", font=("Segoe UI", 9, "bold"),
                               bg="#2b3d30", fg=COLOR_ACCENT_GREEN, bd=0, padx=12, pady=4,
                               command=self._simulate_test_donate)
        btn_sim_dn.pack(side="right")

        # Save Button for API tab
        btn_save_api = tk.Button(parent, text="💾 Lưu Cấu hình API (YouTube & Donate) vào config.json",
                                 font=("Segoe UI", 10, "bold"), bg="#1d3b2c", fg=COLOR_ACCENT_GREEN,
                                 activebackground="#29553f", activeforeground=COLOR_TEXT_WHITE,
                                 bd=0, pady=8, command=self._save_api_config)
        btn_save_api.pack(fill="x", pady=6)

    # ---------------- TAB 5: CONFIG ----------------
    def _build_tab_config(self):
        parent = self.tab_config

        card_stream = self._create_card(parent, "📡 THÔNG TIN LIVESTREAM YOUTUBE & HỆ THỐNG")
        card_stream.pack(fill="x", pady=(0, 10))

        # Stream title
        r1 = tk.Frame(card_stream, bg=COLOR_CARD_BG)
        r1.pack(fill="x", pady=4)
        tk.Label(r1, text="Tiêu đề Stream:", font=("Segoe UI", 10), fg=COLOR_TEXT_WHITE, bg=COLOR_CARD_BG, width=16, anchor="w").pack(side="left")
        tk.Entry(r1, textvariable=self.var_stream_title, font=("Segoe UI", 10),
                 bg=COLOR_INPUT_BG, fg=COLOR_TEXT_WHITE, insertbackground=COLOR_TEXT_WHITE).pack(side="left", fill="x", expand=True)

        # Stream Key
        r2 = tk.Frame(card_stream, bg=COLOR_CARD_BG)
        r2.pack(fill="x", pady=4)
        tk.Label(r2, text="YouTube Stream Key:", font=("Segoe UI", 10), fg=COLOR_TEXT_WHITE, bg=COLOR_CARD_BG, width=16, anchor="w").pack(side="left")
        self.ent_key = tk.Entry(r2, textvariable=self.var_stream_key, font=("Segoe UI", 10), show="*",
                                bg=COLOR_INPUT_BG, fg=COLOR_TEXT_WHITE, insertbackground=COLOR_TEXT_WHITE)
        self.ent_key.pack(side="left", fill="x", expand=True, padx=(0, 6))

        btn_show_key = tk.Checkbutton(r2, text="👁️ Hiện Key", variable=self.var_show_key,
                                      font=("Segoe UI", 9), fg=COLOR_TEXT_WHITE, bg=COLOR_CARD_BG,
                                      selectcolor=COLOR_INPUT_BG, activebackground=COLOR_CARD_BG,
                                      command=self._toggle_show_key)
        btn_show_key.pack(side="left")

        # Diner name
        r3 = tk.Frame(card_stream, bg=COLOR_CARD_BG)
        r3.pack(fill="x", pady=4)
        tk.Label(r3, text="Tên Quán Ăn:", font=("Segoe UI", 10), fg=COLOR_TEXT_WHITE, bg=COLOR_CARD_BG, width=16, anchor="w").pack(side="left")
        tk.Entry(r3, textvariable=self.var_diner_name, font=("Segoe UI", 10),
                 bg=COLOR_INPUT_BG, fg=COLOR_TEXT_WHITE, insertbackground=COLOR_TEXT_WHITE).pack(side="left", fill="x", expand=True)

        # Bitrates & Specs
        r4 = tk.Frame(card_stream, bg=COLOR_CARD_BG)
        r4.pack(fill="x", pady=4)
        tk.Label(r4, text="Video Bitrate:", font=("Segoe UI", 10), fg=COLOR_TEXT_WHITE, bg=COLOR_CARD_BG, width=16, anchor="w").pack(side="left")
        cb_vbit = ttk.Combobox(r4, textvariable=self.var_bitrate, values=["2500k", "3500k", "4500k", "6000k"], state="readonly", width=12)
        cb_vbit.pack(side="left", padx=(0, 16))

        tk.Label(r4, text="Audio Bitrate:", font=("Segoe UI", 10), fg=COLOR_TEXT_WHITE, bg=COLOR_CARD_BG).pack(side="left", padx=(0, 6))
        cb_abit = ttk.Combobox(r4, textvariable=self.var_audio_bitrate, values=["128k", "160k", "192k", "256k"], state="readonly", width=12)
        cb_abit.pack(side="left")

        # Static Specs
        r5 = tk.Frame(card_stream, bg=COLOR_CARD_BG)
        r5.pack(fill="x", pady=6)
        tk.Label(r5, text="Độ phân giải Master: 720x1280 (Vertical 9:16)  |  Khung hình: 30 FPS",
                 font=("Segoe UI", 9, "italic"), fg=COLOR_TEXT_MUTED, bg=COLOR_CARD_BG).pack(anchor="w")

        # Save Button & Open Folder
        btn_box = tk.Frame(parent, bg=COLOR_BG_DARK)
        btn_box.pack(fill="x", pady=12)

        btn_save_all = tk.Button(btn_box, text="💾 Lưu Cấu hình Stream vào config.json", font=("Segoe UI", 10, "bold"),
                                 bg="#1d3b2c", fg=COLOR_ACCENT_GREEN, activebackground="#29553f",
                                 activeforeground=COLOR_TEXT_WHITE, bd=0, pady=8, command=self._save_stream_config)
        btn_save_all.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn_open_assets = tk.Button(btn_box, text="📂 Mở thư mục Sounds", font=("Segoe UI", 10),
                                    bg="#242e3f", fg=COLOR_TEXT_WHITE, bd=0, padx=16, pady=8,
                                    command=self._open_sounds_dir)
        btn_open_assets.pack(side="right")

    def _build_footer(self):
        footer_frame = tk.Frame(self.root, bg=COLOR_PANEL_BG, padx=16, pady=6)
        footer_frame.pack(fill="x", side="bottom")

        self.lbl_footer_status = tk.Label(footer_frame, text="Sẵn sàng.", font=("Segoe UI", 9),
                                          fg=COLOR_TEXT_MUTED, bg=COLOR_PANEL_BG)
        self.lbl_footer_status.pack(side="left")

        lbl_hint = tk.Label(footer_frame, text="Cozy Midnight Diner 24/7 • Independent Controller",
                            font=("Segoe UI", 8), fg="#647388", bg=COLOR_PANEL_BG)
        lbl_hint.pack(side="right")

    def _create_card(self, parent, title):
        card = tk.LabelFrame(parent, text=f"  {title}  ", font=("Segoe UI", 9, "bold"),
                             fg=COLOR_TEXT_GOLD, bg=COLOR_CARD_BG, bd=1, relief="solid",
                             padx=12, pady=10)
        return card

    # ---------------- EVENT HANDLERS ----------------
    def _on_bgm_vol_change(self, val):
        vol = float(val) / 100.0
        self.lbl_bgm_val.config(text=f"{int(float(val))}%")
        self.client.send("set_music_volume", value=vol)

    def _on_sfx_vol_change(self, val):
        vol = float(val) / 100.0
        self.lbl_sfx_val.config(text=f"{int(float(val))}%")
        self.client.send("set_sfx_volume", value=vol)

    def _on_mute_bgm_toggle(self):
        self.client.send("set_mute_bgm", value=self.var_mute_bgm.get())

    def _on_mute_sfx_toggle(self):
        self.client.send("set_mute_sfx", value=self.var_mute_sfx.get())

    def _switch_track(self):
        track = self.var_current_track.get()
        if track:
            self.client.send("switch_music", track=track)
            self._set_status_msg(f"Đã chuyển bài nhạc nền: {track}")

    def _refresh_tracks(self):
        tracks = self._get_sound_tracks()
        self.combo_tracks.config(values=tracks)
        self._set_status_msg(f"Đã cập nhật danh sách {len(tracks)} bài nhạc trong assets/sounds.")

    def _get_sound_tracks(self):
        known_sfx = {"bell_ding.wav", "coin_chime.wav", "pop.wav", "sizzle.wav"}
        tracks = []
        if os.path.exists(SOUNDS_DIR):
            for f in sorted(os.listdir(SOUNDS_DIR)):
                if f.lower().endswith((".mp3", ".ogg", ".wav")) and f not in known_sfx:
                    tracks.append(f)
        if not tracks:
            tracks = ["lofi_chill.mp3", "outfoxing.mp3"]
        return tracks

    def _test_sfx(self, name):
        if self.is_connected:
            self.client.send("play_sfx", sfx=name)
            self._set_status_msg(f"Đã kích hoạt phát SFX '{name}' trong game.")
        else:
            self._play_local_sfx(name)

    def _play_local_sfx(self, name):
        sfx_map = {
            "bell": "bell_ding.wav",
            "coin": "coin_chime.wav",
            "pop": "pop.wav",
            "sizzle": "sizzle.wav"
        }
        fname = sfx_map.get(name)
        if fname:
            fpath = os.path.join(SOUNDS_DIR, fname)
            if os.path.exists(fpath):
                try:
                    import pygame
                    if not pygame.mixer.get_init():
                        pygame.mixer.init()
                    snd = pygame.mixer.Sound(fpath)
                    snd.set_volume(self.var_sfx_vol.get() / 100.0)
                    snd.play()
                    self._set_status_msg(f"Đang nghe thử SFX preview nội bộ: {fname}")
                except Exception as e:
                    self._set_status_msg(f"Không thể nghe thử local: {e}")

    def _save_default_volumes(self):
        m_vol = round(self.var_bgm_vol.get() / 100.0, 2)
        s_vol = round(self.var_sfx_vol.get() / 100.0, 2)
        cfg = load_local_config()
        if "game" not in cfg:
            cfg["game"] = {}
        cfg["game"]["music_volume"] = m_vol
        cfg["game"]["sfx_volume"] = s_vol
        if save_local_config(cfg):
            self.client.send("save_config", config={"game": {"music_volume": m_vol, "sfx_volume": s_vol}})
            messagebox.showinfo("Thành công", f"Đã lưu âm lượng mặc định vào config.json:\n• BGM: {int(m_vol*100)}%\n• SFX: {int(s_vol*100)}%")
            self._set_status_msg("Đã lưu âm lượng mặc định.")

    def _instant_finish(self):
        self.client.send("instant_finish")
        self._set_status_msg("Lệnh Nấu xong ngay đã được gửi!")

    def _skip_dish(self):
        self.client.send("skip_dish")
        self._set_status_msg("Đã bỏ qua món hiện tại.")

    def _clear_queue(self):
        self.client.send("clear_queue")
        self._set_status_msg("Đã xóa sạch hàng đợi món.")

    def _dispatch_order(self):
        val = self.combo_order_dish.get()
        key = "ramen"
        if "(" in val and ")" in val:
            key = val.split("(")[-1].replace(")", "").strip()
        user = self.var_order_user.get().strip() or "@Host"
        self.client.send("order_dish", dish=key, user=user)
        self._set_status_msg(f"Đã thêm order món '{key}' cho {user}")

    def _set_level(self):
        lvl = self.var_level.get()
        self.client.send("set_level", level=lvl)
        self._set_status_msg(f"Đã gửi lệnh đặt Diner Level thành Lv. {lvl}")

    def _toggle_sim(self):
        val = self.var_sim_enabled.get()
        self.client.send("toggle_sim", value=val)
        status = "BẬT" if val else "TẮT"
        self._set_status_msg(f"Giả lập viewer đã được {status}.")

    def _trigger_cheer(self):
        self.client.send("cheer", user=self.var_chat_user.get() or "@Host")
        self._set_status_msg("Đã kích hoạt thả tim cổ vũ (!yum).")

    def _trigger_levelup(self):
        lvl = self.var_level.get() + 1
        self.var_level.set(lvl)
        self.client.send("set_level", level=lvl)
        self._set_status_msg(f"Đã kích hoạt Lên cấp (Lv. {lvl})!")

    def _trigger_tip(self):
        user = self.var_tip_user.get().strip() or "@SuperFan"
        amount = self.var_tip_amount.get()
        self.client.send("tip", user=user, amount=amount)
        self._set_status_msg(f"Đã gửi tip {amount} coin từ {user}!")

    def _send_custom_chat(self):
        msg = self.var_chat_msg.get().strip()
        user = self.var_chat_user.get().strip() or "@Host"
        if msg:
            self.client.send("send_chat", user=user, message=msg)
            self.var_chat_msg.set("")
            self._set_status_msg(f"Đã gửi chat từ {user}: {msg}")

    def _toggle_show_key(self):
        if self.var_show_key.get():
            self.ent_key.config(show="")
        else:
            self.ent_key.config(show="*")

    def _toggle_show_yt_key(self):
        if self.var_show_yt_key.get():
            self.ent_yt_key.config(show="")
        else:
            self.ent_yt_key.config(show="*")

    # ---------------- YOUTUBE & DONATE API HANDLERS ----------------
    def _on_yt_toggle(self):
        self.client.send("update_youtube_credentials",
                         api_key=self.var_yt_api_key.get().strip(),
                         video_id=self.var_yt_video_id.get().strip(),
                         live_chat_id=self.var_yt_chat_id.get().strip(),
                         enabled=self.var_yt_enabled.get())
        status = "BẬT" if self.var_yt_enabled.get() else "TẮT"
        self._set_status_msg(f"Đã {status} đọc bình luận YouTube Live Chat.")

    def _test_and_resolve_yt_chat(self):
        api_key = self.var_yt_api_key.get().strip()
        video_url = self.var_yt_video_id.get().strip()
        if not api_key:
            messagebox.showwarning("Cần API Key", "Vui lòng nhập Google Data API Key trước khi kiểm tra.")
            return

        vid = extract_video_id(video_url)
        self._set_status_msg("Đang kết nối YouTube API để tìm Live Chat...")

        def worker():
            chat_id, msg, ok = resolve_live_chat_id(api_key, vid)
            self.root.after(0, lambda: self._on_yt_resolve_result(chat_id, msg, ok, vid))

        threading.Thread(target=worker, daemon=True).start()

    def _on_yt_resolve_result(self, chat_id, msg, ok, vid):
        if ok and chat_id:
            self.var_yt_chat_id.set(chat_id)
            self.var_yt_video_id.set(vid)
            self.lbl_yt_badge.config(text="🟢 Đã tìm thấy Live Chat", bg="#123a22", fg=COLOR_ACCENT_GREEN)
            messagebox.showinfo("Thành công", f"{msg}\n\nLive Chat ID: {chat_id}")
            self._set_status_msg("Đã lấy thành công Live Chat ID!")
            # Send to game
            self.client.send("update_youtube_credentials",
                             api_key=self.var_yt_api_key.get().strip(),
                             video_id=vid,
                             live_chat_id=chat_id,
                             enabled=self.var_yt_enabled.get())
        else:
            self.lbl_yt_badge.config(text="🔴 Kết nối thất bại", bg="#3d181c", fg=COLOR_ACCENT_RED)
            messagebox.showerror("Lỗi YouTube API", msg)
            self._set_status_msg(f"Lỗi: {msg}")

    def _on_donate_toggle(self):
        self.client.send("update_donate_config",
                         enabled=self.var_donate_enabled.get(),
                         usd_to_coins=self.var_donate_rate.get(),
                         auto_cook=self.var_donate_autocook.get())
        self._set_status_msg("Đã cập nhật cài đặt Donate Webhook.")

    def _copy_webhook_url(self):
        self.root.clipboard_clear()
        self.root.clipboard_append("http://localhost:8088/webhook/donate")
        self._set_status_msg("Đã copy Webhook URL vào clipboard!")

    def _simulate_test_donate(self):
        donor = self.var_test_donor.get().strip() or "@Alex"
        amount = float(self.var_test_amount.get())
        msg = self.var_test_msg.get().strip()

        self.client.send("simulate_donate", user=donor, amount=amount, currency="USD", message=msg)
        self._set_status_msg(f"Đã bắn donate thử nghiệm: ${amount:.2f} từ {donor}!")

    def _save_api_config(self):
        cfg = load_local_config()
        if "youtube" not in cfg:
            cfg["youtube"] = {}
        if "donate" not in cfg:
            cfg["donate"] = {}

        cfg["youtube"]["api_key"] = self.var_yt_api_key.get().strip()
        cfg["youtube"]["video_id"] = self.var_yt_video_id.get().strip()
        cfg["youtube"]["live_chat_id"] = self.var_yt_chat_id.get().strip()
        cfg["youtube"]["enabled"] = self.var_yt_enabled.get()

        cfg["donate"]["enabled"] = self.var_donate_enabled.get()
        cfg["donate"]["webhook_port"] = self.var_donate_port.get()
        cfg["donate"]["usd_to_coins"] = self.var_donate_rate.get()
        cfg["donate"]["auto_cook_on_message"] = self.var_donate_autocook.get()

        if save_local_config(cfg):
            self.client.send("save_config", config=cfg)
            messagebox.showinfo("Thành công", "Đã lưu toàn bộ cấu hình API YouTube & Donate vào config/config.json!")
            self._set_status_msg("Đã lưu cấu hình API thành công.")
        else:
            messagebox.showerror("Lỗi", "Không thể lưu file config/config.json.")

    def _save_stream_config(self):
        cfg = load_local_config()
        if "stream" not in cfg:
            cfg["stream"] = {}
        if "game" not in cfg:
            cfg["game"] = {}

        cfg["stream"]["title"] = self.var_stream_title.get().strip()
        cfg["stream"]["stream_key"] = self.var_stream_key.get().strip()
        cfg["stream"]["video_bitrate"] = self.var_bitrate.get().strip()
        cfg["stream"]["audio_bitrate"] = self.var_audio_bitrate.get().strip()
        cfg["game"]["diner_name"] = self.var_diner_name.get().strip()

        if save_local_config(cfg):
            self.client.send("save_config", config=cfg)
            messagebox.showinfo("Cấu hình", "Đã lưu thành công cấu hình Stream vào config/config.json!")
            self._set_status_msg("Đã lưu cấu hình Stream thành công.")
        else:
            messagebox.showerror("Lỗi", "Không thể lưu file config/config.json.")

    def _open_sounds_dir(self):
        if os.path.exists(SOUNDS_DIR):
            try:
                if sys.platform == "win32":
                    os.startfile(SOUNDS_DIR)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", SOUNDS_DIR])
                else:
                    subprocess.Popen(["xdg-open", SOUNDS_DIR])
            except Exception as e:
                self._set_status_msg(f"Không thể mở thư mục: {e}")

    def _launch_game_process(self):
        main_py = os.path.join(BASE_DIR, "main.py")
        if os.path.exists(main_py):
            try:
                subprocess.Popen([sys.executable, main_py], cwd=BASE_DIR)
                self._set_status_msg("Đã khởi chạy Cozy Midnight Diner (main.py)...")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể khởi động game: {e}")

    def _set_status_msg(self, msg):
        self.lbl_footer_status.config(text=msg)

    # ---------------- REAL-TIME STATE SYNC ----------------
    def _on_status_received(self, data):
        """Called from socket client thread when status JSON arrives."""
        self.root.after(0, self._apply_game_status, data)

    def _apply_game_status(self, data):
        self.game_status = data
        self.is_connected = True

        # Update Audio state if not currently being actively dragged
        audio_info = data.get("audio", {})
        if audio_info:
            curr_track = audio_info.get("current_track")
            if curr_track and curr_track != self.var_current_track.get():
                self.var_current_track.set(curr_track)

            tracks = audio_info.get("available_tracks")
            if tracks:
                self.combo_tracks.config(values=tracks)

        # Update Kitchen / Dish status
        game_info = data.get("game", {})
        if game_info:
            curr_dish = game_info.get("current_dish")
            if curr_dish:
                name = curr_dish.get("name", "Món ăn")
                user = curr_dish.get("user", "")
                step = curr_dish.get("current_step", "")
                prog = curr_dish.get("progress", 0.0)
                comp = curr_dish.get("compliments", 0)

                self.lbl_current_dish.config(text=f"Đang nấu: {name} (cho {user}) — ❤️ {comp} tim", fg=COLOR_TEXT_GOLD)
                self.lbl_current_step.config(text=step, fg=COLOR_TEXT_MUTED)
                self.prog_dish["value"] = prog * 100.0
            else:
                is_serving = game_info.get("is_serving", False)
                if is_serving:
                    self.lbl_current_dish.config(text="✨ ĐANG PHỤC VỤ MÓN LÊN QUẦY BAR!", fg=COLOR_ACCENT_GREEN)
                    self.lbl_current_step.config(text="Món ăn thơm phức đang được thưởng thức...", fg=COLOR_TEXT_GOLD)
                    self.prog_dish["value"] = 100.0
                else:
                    self.lbl_current_dish.config(text="Bếp đang trống (Đầu bếp đang chuẩn bị món tiếp theo)", fg=COLOR_TEXT_MUTED)
                    self.lbl_current_step.config(text="Chờ order mới...", fg=COLOR_TEXT_MUTED)
                    self.prog_dish["value"] = 0.0

            # Update Queue listbox
            queue_items = game_info.get("order_queue", [])
            self.list_queue.delete(0, tk.END)
            for i, q in enumerate(queue_items):
                self.list_queue.insert(tk.END, f"{i+1}. {q.get('name')} (từ {q.get('user')})")

            # Update Level & Exp
            lvl = game_info.get("level", 27)
            exp = game_info.get("exp", 0)
            max_exp = game_info.get("max_exp", 2000)
            self.lbl_level_info.config(text=f"Level: Lv. {lvl}  |  EXP: {exp} / {max_exp}")

            # Update Recent Chats listbox
            chats = game_info.get("recent_chats", [])
            self.list_chats.delete(0, tk.END)
            for c in chats:
                self.list_chats.insert(tk.END, f"{c.get('user')}: {c.get('text')}")

        # Update YouTube API status
        yt_stat = data.get("youtube", {})
        if yt_stat:
            is_running = yt_stat.get("running", False)
            msg = yt_stat.get("status_message", "Chưa kết nối")
            if is_running:
                self.lbl_yt_badge.config(text=f"🟢 {msg}", bg="#123a22", fg=COLOR_ACCENT_GREEN)
            else:
                self.lbl_yt_badge.config(text=f"⚪ {msg}", bg="#242e3f", fg=COLOR_TEXT_MUTED)

        # Update Donate Webhook status
        dn_stat = data.get("donate", {})
        if dn_stat:
            dn_running = dn_stat.get("running", False)
            total_count = dn_stat.get("total_count", 0)
            total_usd = dn_stat.get("total_usd", 0.0)
            last_dn = dn_stat.get("last_donation")
            last_txt = f"Gần nhất: {last_dn.get('user')} (${last_dn.get('amount')} {last_dn.get('currency')})" if last_dn else "Chưa có donate mới"
            self.lbl_dn_stats.config(text=f"Đã nhận: {total_count} lượt (${total_usd:.2f} USD) | {last_txt}")
            if dn_running:
                self.lbl_dn_badge.config(text="🟢 Webhook Port 8088 Active", bg="#123a22", fg=COLOR_ACCENT_GREEN)
            else:
                self.lbl_dn_badge.config(text="⚪ Webhook Tắt", bg="#3d181c", fg=COLOR_ACCENT_RED)

        # Update Viewer Simulator check
        vsim = data.get("viewer_sim", {})
        if "enabled" in vsim and vsim["enabled"] != self.var_sim_enabled.get():
            self.var_sim_enabled.set(vsim["enabled"])

    def _ui_heartbeat(self):
        """Checks connection status every 300ms."""
        if self.client.connected:
            self.status_badge.config(text="● LIVE CONNECTED (127.0.0.1:18765)",
                                     bg="#0f3b20", fg=COLOR_ACCENT_GREEN)
            self.btn_launch_game.config(state="disabled", text="✓ Game Đang Chạy")
        else:
            self.status_badge.config(text="○ OFFLINE (STANDALONE CONFIG MODE)",
                                     bg="#3d181c", fg=COLOR_ACCENT_RED)
            self.btn_launch_game.config(state="normal", text="🚀 Khởi động Game")

        self.root.after(300, self._ui_heartbeat)


def main():
    root = tk.Tk()
    app = StudioControllerApp(root)

    def on_closing():
        app.client.stop()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()

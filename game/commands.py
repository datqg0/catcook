"""
Command parser and dispatcher for chat inputs.
Interprets !cook, !yum, !menu, !tip, and other player interactions.
"""
from game.config import MENU_ITEMS, COLOR_TEXT_GOLD, COLOR_TEXT_CYAN


class CommandDispatcher:
    def __init__(self, game_state):
        self.state = game_state

    def dispatch(self, user, raw_message):
        msg = raw_message.strip()
        if not msg.startswith("!"):
            # Regular chat message
            self.state.add_chat(user, msg)
            return

        parts = msg.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1].strip() if len(parts) > 1 else ""

        if cmd in ["!cook", "!order", "!nau"]:
            self.state.add_order(user, args)
        elif cmd in ["!yum", "!cheer", "!love", "!khen"]:
            self.state.cheer(user)
        elif cmd in ["!tip", "!donate"]:
            amount = 100
            if args:
                try:
                    amount = max(10, int(args))
                except ValueError:
                    amount = 100
            self.state.tip(user, amount)
        elif cmd == "!menu":
            menu_list = ", ".join([d["name"] for d in MENU_ITEMS.values()])
            self.state.add_chat("Menu", f"Available: {menu_list}", COLOR_TEXT_GOLD)
        elif cmd in ["!top", "!rank"]:
            top_str = " | ".join([f"{i+1}.{item['user']} ({item['coins']}c)" for i, item in enumerate(self.state.leaderboard)])
            self.state.add_chat("Rank", top_str, COLOR_TEXT_CYAN)
        else:
            self.state.add_chat(user, msg)

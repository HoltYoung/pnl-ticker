#!/usr/bin/env python3
"""
PnL Ticker — System tray app showing live portfolio PnL in bps.
Works on Windows, macOS, and Linux.
Uses a floating overlay window for always-visible BPS display.
"""

import threading
import time
import tkinter as tk
import yfinance as yf

# ============================================================
# PORTFOLIO — Edit these to match your positions
# Format: {TICKER: (entry_price, position_value_at_entry)}
# ============================================================

LONGS = {
    "AAPL": (255.78, 242.38),
    "APP": (390.55, 156.10),
    "DLTR": (126.06, 242.35),
    "INTC": (46.79, 180.09),
    "KLAC": (1464.13, 243.19),
    "MDB": (368.40, 205.49),
    "MU": (411.66, 187.26),
    "NET": (195.85, 243.03),
    "NVDA": (182.81, 254.87),
    "ROKU": (90.06, 243.03),
    "SNAP": (4.83, 242.46),
    "TEAM": (84.38, 243.19),
}

SHORTS = {
    "BKNG": (4140.60, 144.09),
    "CMCSA": (31.57, 184.19),
    "COST": (1018.48, 227.94),
    "DIS": (105.45, 166.91),
    "HD": (391.05, 191.61),
    "LOW": (287.39, 191.14),
    "MCD": (327.58, 242.67),
    "MSFT": (401.32, 159.40),
    "NKE": (63.13, 130.19),
    "PYPL": (40.29, 103.79),
    "ROST": (196.54, 225.96),
    "SPY": (681.75, 436.12),
    "TJX": (154.46, 243.18),
}

REFRESH_SECONDS = 5


class PnLOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PnL")
        self.root.overrideredirect(True)  # no title bar
        self.root.attributes("-topmost", True)  # always on top
        self.root.configure(bg="#1a1a2e")

        # Position: top right of screen
        screen_w = self.root.winfo_screenwidth()
        self.root.geometry(f"+{screen_w - 220}+5")

        # Main BPS label (big)
        self.bps_label = tk.Label(
            self.root,
            text="Loading...",
            font=("Helvetica", 16, "bold"),
            fg="#00ff88",
            bg="#1a1a2e",
            padx=10,
            pady=2,
        )
        self.bps_label.pack()

        # Spacer (no dollar label)
        self.pnl_label = None

        # Time label
        self.time_label = tk.Label(
            self.root,
            text="",
            font=("Helvetica", 8),
            fg="#555555",
            bg="#1a1a2e",
            padx=10,
            pady=0,
        )
        self.time_label.pack()

        # Detail panel (hidden by default, shown on click)
        self.detail_frame = tk.Frame(self.root, bg="#1a1a2e")
        self.detail_text = tk.Text(
            self.detail_frame,
            font=("Courier", 9),
            fg="#cccccc",
            bg="#0f0f23",
            width=35,
            height=20,
            relief="flat",
            state="disabled",
        )
        self.detail_text.pack(padx=5, pady=5)
        self.details_visible = False
        self.detail_content = ""

        # Click to toggle details
        self.bps_label.bind("<Button-1>", self.toggle_details)

        # Right click to quit
        self.bps_label.bind("<Button-3>", lambda e: self.root.quit())

        # Drag to move
        self.bps_label.bind("<ButtonPress-1>", self.start_drag)
        self.bps_label.bind("<B1-Motion>", self.do_drag)
        self._drag_x = 0
        self._drag_y = 0

        # Start fetching
        self.fetch_thread = threading.Thread(target=self.refresh_loop, daemon=True)
        self.fetch_thread.start()

    def start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def do_drag(self, event):
        x = self.root.winfo_x() + event.x - self._drag_x
        y = self.root.winfo_y() + event.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    def toggle_details(self, event=None):
        if self.details_visible:
            self.detail_frame.pack_forget()
            self.details_visible = False
        else:
            self.detail_frame.pack()
            self.detail_text.config(state="normal")
            self.detail_text.delete("1.0", "end")
            self.detail_text.insert("1.0", self.detail_content)
            self.detail_text.config(state="disabled")
            self.details_visible = True

    def refresh_loop(self):
        while True:
            try:
                self.fetch_and_update()
            except Exception as e:
                self.root.after(0, lambda: self.bps_label.config(text="ERR", fg="#ff4444"))
                print(f"Error: {e}")
            time.sleep(REFRESH_SECONDS)

    def fetch_and_update(self):
        all_tickers = list(LONGS.keys()) + list(SHORTS.keys())

        # Batch download — much faster than per-ticker .info calls
        data = yf.download(all_tickers, period="1d", interval="1m", progress=False)
        
        # Get latest price for each ticker
        prices = {}
        for t in all_tickers:
            try:
                col = data["Close"][t].dropna()
                if len(col) > 0:
                    prices[t] = float(col.iloc[-1])
            except Exception:
                pass

        total_pnl = 0.0
        total_val = 0.0
        details_long = []
        details_short = []

        for t, (entry, val) in sorted(LONGS.items()):
            now = prices.get(t)
            if now is None:
                details_long.append(f" ? {t:6s}  no data")
                continue
            pnl = val * (now - entry) / entry
            chg = ((now - entry) / entry) * 100
            total_pnl += pnl
            total_val += abs(val)
            marker = "+" if pnl >= 0 else "-"
            details_long.append(f" {marker} {t:6s} {chg:+6.1f}%  ${pnl:+7.2f}")

        for t, (entry, val) in sorted(SHORTS.items()):
            now = prices.get(t)
            if now is None:
                details_short.append(f" ? {t:6s}  no data")
                continue
            pnl = val * (entry - now) / entry
            chg = ((entry - now) / entry) * 100
            total_pnl += pnl
            total_val += abs(val)
            marker = "+" if pnl >= 0 else "-"
            details_short.append(f" {marker} {t:6s} {chg:+6.1f}%  ${pnl:+7.2f}")

        if total_val > 0:
            bps = (total_pnl / total_val) * 10000
        else:
            bps = 0

        # Build detail content
        self.detail_content = "=== LONGS ===\n"
        self.detail_content += "\n".join(details_long)
        self.detail_content += "\n\n=== SHORTS ===\n"
        self.detail_content += "\n".join(details_short)
        self.detail_content += f"\n\nTotal: ${total_pnl:+.2f} | {bps:+.0f}bps"

        # Update labels on main thread
        now_str = time.strftime("%I:%M %p")

        if bps >= 0:
            color = "#00ff88"
            bps_text = f"+{bps:.0f} bps"
        else:
            color = "#ff4444"
            bps_text = f"{bps:.0f} bps"

        def update_ui():
            self.bps_label.config(text=bps_text, fg=color)
            self.time_label.config(text=f"Updated {now_str}")
            # If details are showing, refresh them
            if self.details_visible:
                self.detail_text.config(state="normal")
                self.detail_text.delete("1.0", "end")
                self.detail_text.insert("1.0", self.detail_content)
                self.detail_text.config(state="disabled")

        self.root.after(0, update_ui)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = PnLOverlay()
    app.run()

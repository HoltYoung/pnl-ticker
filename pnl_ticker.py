#!/usr/bin/env python3
"""
PnL Ticker — macOS menu bar app showing live portfolio PnL in bps.
Sits in the top-right menu bar, always visible. Refreshes every 60 seconds.
"""

import threading
import time
import rumps
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

REFRESH_SECONDS = 60


class PnLTicker(rumps.App):
    def __init__(self):
        super().__init__("📊 --", quit_button=None)
        self.menu = [
            rumps.MenuItem("Loading...", callback=None),
            None,  # separator
            rumps.MenuItem("Refresh Now", callback=self.manual_refresh),
            rumps.MenuItem("Quit", callback=rumps.quit_application),
        ]
        self.long_items = {}
        self.short_items = {}
        self.summary_item = self.menu["Loading..."]

        # Start background thread
        self.thread = threading.Thread(target=self.refresh_loop, daemon=True)
        self.thread.start()

    def manual_refresh(self, _):
        self.title = "📊 ..."
        threading.Thread(target=self.fetch_and_update, daemon=True).start()

    def refresh_loop(self):
        while True:
            self.fetch_and_update()
            time.sleep(REFRESH_SECONDS)

    def fetch_and_update(self):
        try:
            all_tickers = list(LONGS.keys()) + list(SHORTS.keys())
            tickers_obj = {t: yf.Ticker(t) for t in all_tickers}

            total_pnl = 0.0
            total_val = 0.0
            details_long = []
            details_short = []

            for t, (entry, val) in sorted(LONGS.items()):
                try:
                    info = tickers_obj[t].info
                    now = info.get("currentPrice") or info.get("regularMarketPrice")
                    if now is None:
                        continue
                    pnl = val * (now - entry) / entry
                    chg = ((now - entry) / entry) * 100
                    total_pnl += pnl
                    total_val += abs(val)
                    emoji = "🟢" if pnl >= 0 else "🔴"
                    details_long.append(f"{emoji} {t}: {chg:+.1f}% (${pnl:+.2f})")
                except Exception:
                    details_long.append(f"⚪ {t}: error")

            for t, (entry, val) in sorted(SHORTS.items()):
                try:
                    info = tickers_obj[t].info
                    now = info.get("currentPrice") or info.get("regularMarketPrice")
                    if now is None:
                        continue
                    pnl = val * (entry - now) / entry
                    chg = ((entry - now) / entry) * 100
                    total_pnl += pnl
                    total_val += abs(val)
                    emoji = "🟢" if pnl >= 0 else "🔴"
                    details_short.append(f"{emoji} {t}: {chg:+.1f}% (${pnl:+.2f})")
                except Exception:
                    details_short.append(f"⚪ {t}: error")

            if total_val > 0:
                bps = (total_pnl / total_val) * 10000
            else:
                bps = 0

            # Update menu bar title
            if bps >= 0:
                self.title = f"📈 +{bps:.0f}bps (${total_pnl:+.2f})"
            else:
                self.title = f"📉 {bps:.0f}bps (${total_pnl:+.2f})"

            # Rebuild menu
            self.menu.clear()

            self.menu.add(rumps.MenuItem(
                f"Portfolio: {bps:+.0f} bps | ${total_pnl:+.2f}",
                callback=None
            ))
            self.menu.add(None)

            # Longs header
            self.menu.add(rumps.MenuItem("── LONGS ──", callback=None))
            for detail in details_long:
                self.menu.add(rumps.MenuItem(detail, callback=None))

            self.menu.add(None)

            # Shorts header
            self.menu.add(rumps.MenuItem("── SHORTS ──", callback=None))
            for detail in details_short:
                self.menu.add(rumps.MenuItem(detail, callback=None))

            self.menu.add(None)
            self.menu.add(rumps.MenuItem(
                f"Last update: {time.strftime('%I:%M:%S %p')}",
                callback=None
            ))
            self.menu.add(rumps.MenuItem("Refresh Now", callback=self.manual_refresh))
            self.menu.add(rumps.MenuItem("Quit", callback=rumps.quit_application))

        except Exception as e:
            self.title = "📊 ERR"
            print(f"Error: {e}")


if __name__ == "__main__":
    PnLTicker().run()

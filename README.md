# PnL Ticker 📈

Live portfolio PnL in your macOS menu bar. Always on top, always visible.

Shows total PnL in basis points with per-position breakdown in the dropdown.

![menu bar](https://img.shields.io/badge/macOS-menu%20bar-blue)

## Setup

```bash
git clone https://github.com/HoltYoung/pnl-ticker.git
cd pnl-ticker
pip install -r requirements.txt
python pnl_ticker.py
```

## Edit Positions

Open `pnl_ticker.py` and edit the `LONGS` and `SHORTS` dictionaries at the top:

```python
LONGS = {
    "NVDA": (182.81, 254.87),  # (entry_price, position_value)
    ...
}

SHORTS = {
    "COST": (1018.48, 227.94),
    ...
}
```

## Features

- **Menu bar display**: Shows `📈 +42bps ($12.34)` or `📉 -17bps (-$9.04)`
- **Click to expand**: See per-position P&L with 🟢/🔴 indicators
- **Auto-refresh**: Every 60 seconds (configurable via `REFRESH_SECONDS`)
- **Manual refresh**: Click "Refresh Now" in dropdown
- **Longs & shorts**: Separate sections in dropdown

## Run on Login (Optional)

1. Open **System Settings → General → Login Items**
2. Click **+** and add a shell script or create an Automator app that runs:
   ```bash
   cd /path/to/pnl-ticker && python3.11 pnl_ticker.py
   ```

## Requirements

- macOS (uses `rumps` for native menu bar)
- Python 3.8+
- Internet connection for live quotes

#!/usr/bin/env python3
"""fetch_prices.py — daily commodity/FX fetch for the IDX price-cache.

Runs on a GitHub Actions runner (full internet). Pulls ~5y of daily closes
per series via yfinance and writes price-cache/<name>.csv as `Date,Close`.

Design rules:
- Fail SOFT per series: if a symbol won't fetch after retries, we LEAVE the
  existing CSV untouched (never overwrite good history with an empty file).
- `pulp` has no free feed and is intentionally NOT fetched here — it stays a
  manual file. This script never touches pulp.csv.
- Full-history overwrite (not append): yfinance is the source of truth for the
  automated series; a clean 5y pull each day avoids drift/dedup complexity.
"""
import sys
import time
from pathlib import Path

import yfinance as yf

# name -> yahoo symbol. Mirrors COMMODITY_PROXIES in the skill (pulp excluded).
SERIES = {
    "coal":   "MTF=F",   # API2 Rotterdam proxy (ICI is paywalled)
    "brent":  "BZ=F",
    "cpo":    "CPO=F",
    "nickel": "NI=F",
    "gold":   "GC=F",
    "usdidr": "IDR=X",
}

OUT_DIR = Path(__file__).parent / "price-cache"
PERIOD = "5y"
RETRIES = 4


def fetch(symbol: str):
    last = None
    for attempt in range(1, RETRIES + 1):
        try:
            df = yf.Ticker(symbol).history(period=PERIOD, interval="1d",
                                           auto_adjust=False)
            if df is not None and not df.empty and "Close" in df.columns:
                return df["Close"].dropna()
            last = "empty frame"
        except Exception as e:  # noqa: BLE001 — runner-side, log and retry
            last = repr(e)
        time.sleep(3 * attempt)  # linear backoff; be gentle on shared IPs
    print(f"  ! {symbol}: failed after {RETRIES} tries ({last})")
    return None


def write_csv(name: str, closes) -> None:
    OUT_DIR.mkdir(exist_ok=True)
    path = OUT_DIR / f"{name}.csv"
    lines = ["Date,Close"]
    for ts, val in closes.items():
        lines.append(f"{ts.date().isoformat()},{round(float(val), 4)}")
    path.write_text("\n".join(lines) + "\n")
    print(f"  ok {name}: {len(closes)} rows -> {path.name}")


def main() -> int:
    failures = 0
    for name, symbol in SERIES.items():
        print(f"{name} ({symbol})")
        closes = fetch(symbol)
        if closes is None or len(closes) == 0:
            failures += 1
            continue
        write_csv(name, closes)
    # Non-zero only if EVERYTHING failed — a partial run is still worth committing.
    if failures == len(SERIES):
        print("all series failed; nothing to commit")
        return 1
    print(f"done ({len(SERIES) - failures}/{len(SERIES)} series updated)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

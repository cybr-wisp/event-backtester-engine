from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator

from backtester.events import MarketEvent


def parse_ts(raw: str) -> str:
    """
    Return ISO-8601 string with timezone if possible (ends with 'Z' or '+00:00').
    Your MarketEvent accepts str or datetime; we'll store a normalized ISO string.
    """
    s = raw.strip()

    # Try common formats (daily + intraday)
    fmts = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y",
    ]
    for fmt in fmts:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.isoformat()
        except ValueError:
            pass

    # ISO fallback
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt.isoformat()
    except ValueError as e:
        raise ValueError(f"Unrecognized timestamp format: {raw!r}") from e


@dataclass(slots=True)
class CSVDataHandler:
    csv_path: str
    symbol: str

    # column names in your CSV (adjust if needed)
    ts_col: str = "timestamp"
    open_col: str = "open"
    high_col: str = "high"
    low_col: str = "low"
    close_col: str = "close"
    volume_col: str = "volume"

    def stream_market_events(self) -> Iterator[MarketEvent]:
        path = Path(self.csv_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV not found: {path}")

        with path.open("r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise ValueError("CSV has no header row.")

            required = {
                self.ts_col, self.open_col, self.high_col,
                self.low_col, self.close_col, self.volume_col
            }
            missing = required - set(reader.fieldnames)
            if missing:
                raise ValueError(f"Missing columns: {missing}. Found: {reader.fieldnames}")

            for row in reader:
                yield MarketEvent(
                    ts=parse_ts(row[self.ts_col]),
                    symbol=self.symbol,
                    open=float(row[self.open_col]),
                    high=float(row[self.high_col]),
                    low=float(row[self.low_col]),
                    close=float(row[self.close_col]),
                    volume=float(row[self.volume_col] or 0.0),
                )

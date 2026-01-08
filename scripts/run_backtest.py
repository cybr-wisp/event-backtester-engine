from __future__ import annotations

from backtester.data.csv_data_handler import CSVDataHandler


class SimpleQueue:
    def __init__(self) -> None:
        self.items = []

    def put(self, event) -> None:
        self.items.append(event)


def _ohlc_sane(o: float, h: float, l: float, c: float) -> bool:
    return (h >= max(o, c)) and (l <= min(o, c)) and (h >= l)


def main():
    q = SimpleQueue()

    data = CSVDataHandler(
        csv_path="backtester/data/SPY_1_min.csv",
        symbol="SPY",
        ts_col="date",  # make sure this matches your handler’s expectation
        open_col="open",
        high_col="high",
        low_col="low",
        close_col="close",
        volume_col="volume",
    )

    # --- Loader summary + sanity checks while streaming ---
    n_total = 0
    first_ts = None
    last_ts = None
    prev_ts = None

    bad_ohlc = 0
    non_increasing_ts = 0

    # Print first 50 bars but keep counting totals (optional: remove break to count all)
    MAX_BARS = 50

    for evt in data.stream_market_events():
        # summary stats
        if first_ts is None:
            first_ts = evt.ts
        last_ts = evt.ts
        n_total += 1

        # sanity checks
        if prev_ts is not None and evt.ts <= prev_ts:
            non_increasing_ts += 1
        prev_ts = evt.ts

        if not _ohlc_sane(evt.open, evt.high, evt.low, evt.close):
            bad_ohlc += 1

        # queue + print first MAX_BARS only
        if n_total <= MAX_BARS:
            q.put(evt)
            print(
                f"PUT {evt.type} {evt.ts} {evt.symbol} "
                f"O={evt.open} H={evt.high} L={evt.low} C={evt.close} V={evt.volume}"
            )

        # stop after MAX_BARS (so summary matches what you printed)
        if n_total >= MAX_BARS:
            break

    # --- Summary line (the “real system” vibe) ---
    print(
        f"\nLoaded {n_total:,} bars for SPY: {first_ts} \u2192 {last_ts}"
    )

    # --- Sanity check report ---
    if non_increasing_ts == 0 and bad_ohlc == 0:
        print("Sanity checks: PASS (timestamps increasing, OHLC sane)")
    else:
        print(
            "Sanity checks: FAIL "
            f"(non_increasing_ts={non_increasing_ts}, bad_ohlc={bad_ohlc})"
        )

    print(f"\nQueued {len(q.items)} market events (showing first {min(50, len(q.items))}).")


if __name__ == "__main__":
    main()

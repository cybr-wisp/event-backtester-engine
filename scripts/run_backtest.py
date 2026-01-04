from __future__ import annotations

from backtester.data.csv_data_handler import CSVDataHandler


class SimpleQueue:
    def __init__(self) -> None:
        self.items = []

    def put(self, event) -> None:
        self.items.append(event)


def main():
    q = SimpleQueue()

    data = CSVDataHandler(
        csv_path="backtester/data/SPY_1_min.csv",
        symbol="SPY",
        # If your CSV has different headers, change these:
        # ts_col="Date",
        # open_col="Open",
        # high_col="High",
        # low_col="Low",
        # close_col="Close",
        # volume_col="Volume",
    )

    n = 0
    for evt in data.stream_market_events():
        q.put(evt)
        print(
            f"PUT {evt.type} {evt.ts} {evt.symbol} "
            f"O={evt.open} H={evt.high} L={evt.low} C={evt.close} V={evt.volume}"
        )
        n += 1
        if n >= 50:  # print first 50 only
            break

    print(f"\nQueued {len(q.items)} market events (showing first {min(50, len(q.items))}).")


if __name__ == "__main__":
    main()

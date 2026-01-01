1.0 | Goal:
Build an event-driven backtesting engine that replays historical market data as a sequence of events (Market → Signal → Order → Fill) to simulate trading decisions through time.
The System must be:
Deterministic and reproducible (same data + config → same results)
Free of look-ahead bias, ensuring strategies react only to information available at each timestamp
Modular, so components (data feed, strategy, execution model, portfolio) can be swapped without changing the core event loop
The v1.0 engine is implemented as a single-threaded FIFO event loop, which assures strict ordering and deterministic replay. 

 2.0 | Outputs:
Running a backtest produces the following outputs:
Equity curve (portfolio value over time)
Drawdown curve (peak-to-trough losses)
Trade markers on price chart (▲ buys, ▼ sells)
PnL distribution (histogram of trade returns)
Exposure / position size over time
Event log timeline (optional, for debugging and analysis)

3.0 | Non-Goals (v1.0)
The following features are explicitly out of scope for v1.0:
1) Live trading
2) Tick-level microstructure modeling
3) Multi-asset or cross-asset portfolios
4) Latency modeling beyond basic simulation




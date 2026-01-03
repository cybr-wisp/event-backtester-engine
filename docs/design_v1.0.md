# Design Document – Event-Driven Backtesting Engine (v1.0)

---

## 1.0 | Goal

Build an **event-driven backtesting engine** that replays historical market data as a sequence of events  
(**Market → Signal → Order → Fill**) to simulate trading decisions through time.

The system must be:

- **Deterministic and reproducible**  
  (same data + same configuration → same results)

- **Free of look-ahead bias**, ensuring strategies react only to information available at each timestamp

- **Modular**, allowing components (data feed, strategy, execution model, portfolio) to be swapped without modifying the core event loop

The **v1.0 engine** is implemented as a **single-threaded FIFO event loop**, ensuring strict ordering and fully deterministic replay.

---

## 2.0 | Outputs

Running a backtest produces the following outputs:

- **Equity curve** (portfolio value over time)
- **Drawdown curve** (peak-to-trough losses)
- **Trade markers** on price chart (▲ buys, ▼ sells)
- **PnL distribution** (histogram of trade returns)
- **Exposure / position size over time**
- **Event log timeline** (optional, for debugging and analysis)

---

## 3.0 | Non-Goals (v1.0)

The following features are explicitly **out of scope** for version 1.0:

1. Live trading  
2. Tick-level microstructure modeling  
3. Multi-asset or cross-asset portfolios  
4. Latency modeling beyond basic simulation

---

## 4.0 | Event-Driven Architecture

The system is built around a small set of **typed events** that flow through the engine. Each module **consumes events**, updates internal state if needed, and may **emit new events**.

### Core Event Types

Minimum event types supported in v1:

- **MarketEvent** — market data updates (bars, quotes, or trades)
- **SignalEvent** — strategy intent (buy/sell/hold)
- **OrderEvent** — order creation/modification/cancellation
- **FillEvent** — execution reports filled orders
- **PositionEvent / PnLEvent** — accounting updates
- **RiskEvent** — risk or limit breaches *(optional)*
- **CorporateActionEvent** — splits/dividends *(future)*
- **LatencyEvent** — execution latency modeling *(future)*

---

## Event Schemas (v1.0)

Canonical schemas used in the engine.

### MarketEvent
- `ts`, `symbol`, `open`, `high`, `low`, `close`, `volume`

### SignalEvent
- `ts`, `symbol`, `side` *(BUY / SELL)*, `strength` 

### OrderEvent
- `ts`, `symbol`, `side`, `qty`, `order_type` *(MKT)*, `id` 

### FillEvent
- `ts`, `symbol`, `side`, `qty`, `fill_price`, `fee`

Formal field constraints and guarantees are specified in `system.md`.

---

## 5.0 | Module Interfaces

The modules communicate **only through events**.

### Strategy
- `on_market(MarketEvent) → SignalEvent | None`

### Execution / Broker
- `on_signal(SignalEvent) → OrderEvent`
- `on_market(MarketEvent) → FillEvent | None`

### Portfolio
- `on_fill(FillEvent) → None`
- `on_market(MarketEvent) → None` *(mark-to-market only)*

---

## 6.0 | Main Event Loop: Event Processing & Control Flow

At each timestamp `t`, events flow through the system as follows:

1. **DataFeed** emits `MarketEvent(t)` into the EventBus.
2. **Execution Engine** consumes `MarketEvent(t)` and may emit `FillEvent(t)` if a pending order is scheduled to fill on this bar.
3. **Strategy Engine** consumes `MarketEvent(t)` and may emit `SignalEvent(t)` using only information available up to time `t`.
4. **Execution Engine** consumes `SignalEvent(t)`, creates an `OrderEvent(t)`, and stores it as pending.
5. **Portfolio** consumes `FillEvent(s)` to update cash and positions, and consumes `MarketEvent(t)` to mark-to-market and record equity.

---

## 7.0 | Execution Model Assumptions (v1.0)

Execution behavior is intentionally simple and explicit:

- **Fill timing**
  - Market orders created at bar `t` fill at the **open of bar `t+1`**
- **Fees**
  - Fixed fee per fill (e.g., `$0.50`)
- **Slippage**
  - Fixed basis-point slippage against the trader (e.g., `1 bp`)

Execution semantics are configurable but deterministic. Exact rules are specified in `system.md`.

---

## 8.0 | Invariants – Design Guarantees

- **No look-ahead bias**  
  Strategy decisions at time `t` use only data available up to `t`. Fills never reference prices that occur after the decision timestamp.

- **Deterministic replay**  
  Given the same input data and configuration, the backtest produces identical trades, fills, and equity curves.

- **Accounting correctness**  
  Portfolio state (cash and positions) changes only in response to `FillEvent`s, never from signals or orders.

- **Time ordering**  
  Events are processed in non-decreasing timestamp order for the single-symbol v1 engine.

These invariants are formally enforced and tested as part of the system contract (`system.md`).

---

## 9.0 | Summary

gitv1.0 prioritizes **clarity, correctness, and reproducibility** over raw performance or realism. By modeling trading as a strict sequence of events with explicit boundaries between modules, the engine mirrors the structure of real trading systems while remaining simple enough to reason about and extend for further updates.
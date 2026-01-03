# System Document – Event-Driven Backtesting Engine (v1.0)

This document defines the **behavioral contract** for the v1.0 backtesting engine.  
It specifies what must always be true about **event flow, execution, accounting, configuration, and correctness**.

---

## 1.0 | Scope

### In Scope – v1.0
- Single-symbol backtesting
- OHLCV bar-based market data
- Event pipeline:  
  **MarketEvent → SignalEvent → OrderEvent → FillEvent**
- Market orders only
- Deterministic & reproducible replay
- No look-ahead bias

### Out of Scope – v1.0 (Flagship Model)
- Live trading
- Tick-level microstructure
- Order book simulation
- Multi-asset portfolios
- Corporate actions (splits, dividends)
- Advanced latency modeling

---

## 2.0 | Definitions

- **Bar**: A single OHLCV record for a symbol at timestamp `ts`
- **Decision time (`t`)**: The timestamp when the strategy reacts to a `MarketEvent`
- **Order time (`t`)**: The timestamp when an order is created from a signal
- **Fill time (`t+1`)**: The timestamp when a market order is filled (next bar)

---

## 3.0 | Canonical Event Flow

For each bar timestamp `t`, events **MUST** occur in the following order:

1. `MarketEvent(t)` is emitted by the data feed
2. Execution processes pending orders scheduled to fill at `t` and may emit `FillEvent(t)`
3. Strategy consumes `MarketEvent(t)` and may emit `SignalEvent(t)`
4. Execution consumes `SignalEvent(t)` and creates an `OrderEvent(t)` (stored as pending)
5. Portfolio processes:
   - `FillEvent` (state mutation)
   - `MarketEvent(t)` (mark-to-market)

No other ordering is permitted.

---

## 4.0 | Ordering & Determinism Guarantees

- Market events are processed in **non-decreasing timestamp order**
- v1.0 assumes **one symbol**, so at most one `MarketEvent` exists per timestamp
- Given the same:
  - market data
  - configuration  

  the engine **MUST** produce identical:
  - fills
  - trades
  - equity curve

- v1.0 **MUST NOT** use randomness in pricing, execution, or accounting

---

## 5.0 | Event Schemas

### 5.1 | MarketEvent

**Fields**
- `ts` — timestamp (ISO-8601 string or datetime)
- `symbol` — string
- `open`, `high`, `low`, `close` — floats
- `volume` — int or float

**Constraints**
- `open`, `high`, `low`, `close` > 0
- `volume ≥ 0`
- `high ≥ max(open, close)`
- `low ≤ min(open, close)`
- `high ≥ low`

**Semantics**
- Execution uses **`open`** of the fill bar
- Portfolio marks to market using **`close`** of the current bar

---

### 5.2 | SignalEvent

**Fields**
- `ts` — same timestamp as triggering `MarketEvent`
- `symbol`
- `side` ∈ {BUY, SELL}
- `strength` (optional)

**Rules**
- Signals **MUST** be generated using only data available at time `ts`

---

### 5.3 | OrderEvent

**Fields**
- `ts` — same as `SignalEvent.ts`
- `symbol`
- `side` ∈ {BUY, SELL}
- `qty` — numeric, `qty > 0`
- `order_type` — `"MKT"`
- `id` (optional)

**Rules**
- v1.0 supports **market orders only**

---

### 5.4 | FillEvent

**Fields**
- `ts` — fill timestamp
- `symbol`
- `side`
- `qty` — numeric, `qty > 0`
- `fill_price` — float, `> 0`
- `fee` — float, `≥ 0`

---

## 6.0 | Hard Constraints — No Look-Ahead Rules

- Strategy **MUST NOT** access market data with timestamp greater than the current `MarketEvent.ts`
- Orders created at time `t` **MUST NOT** fill using prices from time `t`
- Portfolio cash and positions **MUST** change only when processing `FillEvent`

Violating any of these rules invalidates the backtest.

---

## 7.0 | Execution Semantics

### Fill Timing
- A market order created at bar `t` fills at bar `t+1`
- Fill timestamp **MUST** be strictly greater than order timestamp

### Fill Price
Let:
- `open_next = open[t+1]`
- `s = slippage_bps / 10000`

Then:
- **BUY**: `fill_price = open_next × (1 + s)`
- **SELL**: `fill_price = open_next × (1 − s)`

### Fees
- `fee = fee_per_fill` applied once per fill

### End-of-Data Behavior
- If bar `t+1` does not exist, the order **MUST** remain unfilled and be dropped

---

## 8.0 | Portfolio & Accounting Semantics

### State Tracked
- `cash`
- `position_qty`
- `avg_cost`
- `equity`

### Update Rules

**On `FillEvent`:**
- Update cash using `qty × fill_price ± fee`
- Update position quantity
- Update average cost (average-cost method)

**On each `MarketEvent(t)`:**
- Mark to market using `close[t]`
- `equity = cash + position_qty × close[t]`

### PnL
- **Unrealized PnL**: `(close[t] − avg_cost) × position_qty`
- **Realized PnL**: generated when position is reduced or closed

### Trading Mode (v1.0)
- **Long-only**
  - Positions may not go below zero
  - Sell orders exceeding current position **MUST** be rejected

---

## 9.0 | Configuration — YAML Runtime

A valid v1.0 run **MUST** define:
- `symbol` — instrument being traded
- `starting_cash` — initial portfolio cash
- `order_size` — fixed quantity per trade
- `fee_per_fill` — fixed commission per fill
- `slippage_bps` — slippage in basis points
- `data_path` — path to OHLCV CSV file
- `start_date`
- `end_date`
- `seed`

Missing required fields **MUST** raise a clear error.

---

## 10.0 | Error Handling & Acceptance Tests

### Error Handling
- Invalid market data (bad OHLC) **SHOULD** raise an exception
- Invalid orders (`qty ≤ 0`) **MUST** be rejected
- Long-only violations **MUST** be rejected
- Silent failure is not permitted

### Acceptance Tests (Must Hold)
- Same data + same config → identical equity curve
- Market orders placed at `t` never fill at `t`
- Cash and positions change only on `FillEvent`
- Events are processed in non-decreasing timestamp order
- Slippage is always applied against the trader
- Fees are applied exactly once per fill

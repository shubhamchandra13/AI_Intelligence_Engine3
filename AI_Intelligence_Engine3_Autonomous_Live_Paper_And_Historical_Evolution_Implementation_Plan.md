# AI_Intelligence_Engine3
## Autonomous Live Paper Trading + After-Hours Historical Evolution Framework

**Version:** 1.0  
**Document Type:** Implementation Blueprint  
**Target System:** AI_Intelligence_Engine3  
**Base Reference Repository:** AI_Intelligence_Engine  
**Primary Broker/Data Source:** Upstox API  
**Execution Scope:** Paper Trading Only  

---

## 1. Objective

The objective of `AI_Intelligence_Engine3` is to build an autonomous AI-driven paper trading system that:

- performs live paper trading during market hours,
- performs historical simulated paper trading after market close,
- logs both live and replay decisions in a structured way,
- evaluates performance across multiple market regimes,
- evolves thresholds, filters, and risk behavior over time,
- remains disciplined, auditable, and protected from uncontrolled overfitting.

This system is not intended to take real exchange executions at this stage.  
Its purpose is to become a strong, mature, and adaptive paper-trading intelligence engine first.

---

## 2. Core Vision

`AI_Intelligence_Engine3` should operate in two trading environments:

### 2.1 Live Market Environment
During market hours, the system should connect to Upstox live and intraday data, evaluate signals in real time, and autonomously take paper trades.

### 2.2 Historical Simulated Environment
After market close, the system should replay 3-6 months of historical data candle by candle, simulate a live market environment, and autonomously take paper trades using the same decision logic used in the live session.

The combined purpose of these two environments is:

- to expose the system to more market conditions,
- to test behavior in different regimes,
- to capture weak and strong setups,
- to improve filters and confidence logic,
- to make the engine more mature and intelligent with controlled evolution.

---

## 3. Core Principle

The system should not aim to "take every trade."

The correct objective is:

- observe a wide variety of market scenarios,
- trade only when setup quality is acceptable,
- learn from valid outcomes,
- improve with measured, data-backed evolution.

In short:

**The system should see more scenarios, not blindly force more trades.**

This distinction is critical because brute-force trading creates noisy learning, overtrading, and overfitting.

---

## 4. Operating Model

## 4.1 Market Hours Mode
**Time Window:** `09:15 AM to 03:30 PM IST`

### Behavior
- connect to live Upstox data,
- fetch spot, LTP, intraday candles, and market context,
- generate strategy decisions,
- take paper entries and exits autonomously,
- update floating PnL and trade state,
- log each trade and decision context.

### Output
- live paper trades,
- real market session observations,
- decision quality dataset,
- intraday performance data.

---

## 4.2 After-Hours Historical Replay Mode
**Time Window:** after market close

### Behavior
- load historical candles for the last 3-6 months,
- replay candles sequentially as if they were arriving live,
- run the same strategy engine on each replay step,
- take autonomous simulated paper trades,
- record entries, exits, reasons, and outcomes.

### Output
- historical simulation trades,
- scenario-based performance data,
- replay-specific learning datasets,
- market regime exposure beyond the current session.

---

## 4.3 Evolution Mode
**Time Window:** replay completion onward

### Behavior
- compare live paper trades and historical replay trades,
- evaluate win rate, expectancy, drawdown, regime fit, and confidence bucket behavior,
- generate tuned candidate parameters,
- validate whether improvements are safe,
- prepare the next-day active configuration.

### Output
- tuned configurations,
- evaluation reports,
- champion vs challenger decisions,
- next-session deployable settings.

---

## 5. High-Level Architecture

The system should be split into the following components.

### 5.1 Mode Manager
Responsible for switching the engine between:

- `LIVE_PAPER`
- `HISTORICAL_REPLAY`
- `EVOLUTION`
- `IDLE`

### 5.2 Data Layer
Provides data from two sources through one common interface:

- live Upstox market data,
- historical replay data.

### 5.3 Strategy Engine
A reusable decision engine that works identically in both live and historical replay modes.

### 5.4 Paper Execution Engine
Handles virtual trade entry, exit, position management, stop loss, target logic, and floating PnL.

### 5.5 Replay Engine
Feeds historical candles one by one to the strategy engine to simulate a live market.

### 5.6 Trade Logger
Stores all trades and decision context with mode-based tagging.

### 5.7 Evaluation Engine
Calculates metrics and generates performance summaries.

### 5.8 Evolution Engine
Tunes safe parameters based on measured performance.

### 5.9 Scheduler
Automates the daily system cycle.

---

## 6. End-to-End Flow

## 6.1 Live Paper Flow
1. Start engine in `LIVE_PAPER` mode.
2. Authenticate and connect to Upstox feeds.
3. Fetch real-time or intraday candles and LTPs.
4. Build market snapshot.
5. Run indicators, regime logic, confidence scoring, and signal logic.
6. If valid setup exists, take paper entry.
7. Manage floating PnL and exits.
8. Log trade details and market context.
9. Update dashboard and runtime state.
10. Save session summary after market close.

---

## 6.2 Historical Replay Flow
1. Switch to `HISTORICAL_REPLAY` mode after market close.
2. Select replay window such as last 3 months or 6 months.
3. Load historical candles.
4. Replay candles step by step in chronological order.
5. At each step, run the same strategy engine used in live mode.
6. Enter or exit simulated paper trades as conditions trigger.
7. Log all replay trades with replay metadata.
8. Generate replay summary and save batch results.

---

## 6.3 Evolution Flow
1. Load all new live paper trade results.
2. Load all replay batch results.
3. Compare performance by regime, confidence, symbol, and session type.
4. Identify weak filters and strong filters.
5. Tune eligible parameters.
6. validate candidate configuration against safety checks.
7. Store proposed configuration.
8. Promote only if challenger beats or safely matches champion.

---

## 7. Phase-Wise Implementation Backlog

## Phase 1: Foundation and Separation
### Goal
Refactor the current system into reusable and clearly separated operational units.

### Primary Focus
- stabilize current live paper trading,
- separate strategy logic from UI/runtime loop,
- prepare the system for mode-based execution,
- document baseline architecture.

### Concrete Tasks
1. Audit the existing flow inside `main.py`.
2. Identify and isolate signal generation logic.
3. Create a reusable `strategy_engine`.
4. Validate current `institutional_paper_execution_engine`.
5. Design and add a `mode_manager`.
6. Standardize config loading and runtime flags.
7. Confirm data dependencies from `data_fetcher` and `upstox_client`.

### Files to Review
- `main.py`
- `core/data_fetcher.py`
- `core/upstox_client.py`
- `engines/institutional_paper_execution_engine.py`
- `engines/ml_evolution_engine.py`
- `config.py`

### New Files to Create
- `core/mode_manager.py`
- `core/data_provider.py`
- `engines/strategy_engine.py`

### Deliverables
- stable live paper baseline,
- mode-ready architecture,
- reusable strategy decision layer,
- initial implementation documentation.

---

## Phase 2: Historical Replay and Structured Logging
### Goal
Build autonomous after-hours historical paper trading and store the results in a clean, tagged format.

### Primary Focus
- create replay engine,
- ensure live and replay use the same strategy logic,
- redesign logging for clean separation,
- generate replay analytics.

### Concrete Tasks
1. Create `historical_replay_engine`.
2. Implement candle-by-candle replay logic.
3. Connect replay flow to the same strategy engine used in live mode.
4. Ensure replay uses the paper execution engine in simulation mode.
5. Tag replay trades as `historical_sim`.
6. Add replay batch IDs and metadata.
7. Create summary reporting for replay sessions.

### New Files to Create
- `engines/historical_replay_engine.py`
- `engines/evaluation_engine.py`

### Files to Modify
- `engines/trade_logger.py`
- `config.py`
- database schema or logging layer

### Required Logging Fields
- `trade_mode`
- `session_type`
- `strategy_version`
- `config_version`
- `replay_batch_id`
- `market_regime`
- `confidence_bucket`
- `data_source`

### Deliverables
- autonomous historical replay mode,
- separate live vs replay trade records,
- replay performance summaries,
- structured simulation datasets for evolution.

---

## Phase 3: Evolution, Scheduling, and Controlled Autonomy
### Goal
Turn the system into a self-improving, scheduled paper trading engine.

### Primary Focus
- evaluation metrics,
- nightly tuning,
- champion-challenger promotion,
- automated daily cycle.

### Concrete Tasks
1. Finalize evaluation metrics.
2. Create `config_evolution_engine`.
3. Tune safe parameters only.
4. Add validation rules before promotion.
5. Build `scheduler`.
6. Create operational scripts for live, replay, and evolution.
7. Add dashboard and reporting visibility.

### New Files to Create
- `engines/config_evolution_engine.py`
- `core/scheduler.py`
- `scripts/run_live.py`
- `scripts/run_replay.py`
- `scripts/run_evolution.py`
- `scripts/run_daily_cycle.py`

### Deliverables
- automated daily operation,
- nightly evolution cycle,
- controlled configuration upgrades,
- next-day deployable improved paper model.

---

## 8. Suggested Folder Layout for AI_Intelligence_Engine3

```text
AI_Intelligence_Engine3/
  core/
    mode_manager.py
    scheduler.py
    data_provider.py
    data_fetcher.py
    upstox_client.py

  engines/
    strategy_engine.py
    institutional_paper_execution_engine.py
    historical_replay_engine.py
    evaluation_engine.py
    config_evolution_engine.py
    ml_evolution_engine.py

  scripts/
    run_live.py
    run_replay.py
    run_evolution.py
    run_daily_cycle.py

  database/
    trades.db
    runtime_state.json
    optimized_params.json
    model_registry.json

  reports/
    daily_reports/
    replay_reports/
    evolution_reports/
```

---

## 9. Data and Logging Design

### 9.1 Required Trade Sources
Every trade should be tagged with a clear origin:

- `live_paper`
- `historical_sim`
- `manual_test`

### 9.2 Why Separation Is Mandatory
Live paper and replay data should not be mixed without identification.

If both are mixed blindly:
- the model will learn from unrealistic aggregates,
- confidence logic may become unstable,
- replay success can be mistaken for live robustness,
- evaluation reports become unreliable.

### 9.3 Required Trade Context
Every trade should store:

- symbol,
- timestamp,
- entry price,
- exit price,
- PnL,
- confidence,
- regime,
- rationale,
- strategy version,
- config version,
- trade mode,
- market session type,
- data source.

---

## 10. Safe Evolution Rules

### 10.1 Parameters That Can Be Tuned
- minimum confidence threshold,
- regime filters,
- target multipliers,
- stop-loss behavior,
- cooldown duration,
- time-of-day restrictions,
- position sizing caps.

### 10.2 Parameters That Should Not Be Tuned Blindly
- entire strategy logic at once,
- all feature weights simultaneously,
- unrestricted position risk,
- unconditional always-trade behavior.

### 10.3 Promotion Rule
A new candidate configuration should become active only if:

- sample size is sufficient,
- drawdown remains acceptable,
- expectancy is not worse,
- live paper performance is not degraded,
- validation rules pass.

---

## 11. Daily Operating Schedule

### Pre-Market
- broker auth check,
- config load,
- data health check,
- runtime reset,
- dashboard readiness.

### Market Hours
- live paper trading,
- runtime monitoring,
- trade logging,
- session state updates.

### Post-Market
- live session summary,
- historical replay start,
- replay trade generation,
- replay reporting.

### Night Cycle
- evaluation,
- evolution,
- challenger creation,
- champion-challenger review,
- next-day ready state.

---

## 12. Safety Framework

Even in paper mode, autonomy must be disciplined.

### Mandatory Safety Controls
- max trades per day,
- max drawdown per session,
- max concurrent positions,
- stale data detection,
- duplicate signal block,
- cooldown after losses,
- low-confidence entry block,
- separate handling of weekends and non-trading sessions,
- strict live vs replay data separation.

### Safety Principle
Autonomy without discipline will make the engine noisy and unstable.  
Discipline with logging, validation, and controlled tuning will make it mature.

---

## 13. Best Build Order

1. Stabilize the current live paper trading flow.
2. Extract reusable strategy logic from `main.py`.
3. Add a mode manager.
4. Build the historical replay engine.
5. Redesign trade logging with mode separation.
6. Add an evaluation engine.
7. Add a controlled evolution engine.
8. Add a scheduler and daily-cycle automation.
9. Extend dashboard visibility.
10. Run a 2-4 week paper validation cycle.

---

## 14. Implementation Mapping from Current Repository

The existing `AI_Intelligence_Engine` repository already contains useful building blocks that can be used as a base for `AI_Intelligence_Engine3`.

### Existing Useful Components
- `main.py`
- `core/data_fetcher.py`
- `core/upstox_client.py`
- `engines/institutional_paper_execution_engine.py`
- `engines/ml_evolution_engine.py`
- `dual_mode_engine.py`

### Implementation Direction
- do not build a second unrelated architecture,
- reuse the current live data and paper execution foundation,
- decouple live logic from the monolithic loop,
- add replay and evolution as structured new layers.

---

## 15. Final Summary

`AI_Intelligence_Engine3` should be implemented as an autonomous paper trading intelligence system that:

- trades live on real-time market data during market hours,
- trades autonomously on historical replay after market close,
- logs both sources separately,
- evaluates both sources carefully,
- evolves only through controlled and validated improvements,
- becomes more mature through disciplined learning rather than uncontrolled overtrading.

This is the correct architecture for building an adaptive AI trading engine before real execution is ever introduced.

---

## 16. Immediate Next Document

The next recommended document after this one is:

**`AI_Intelligence_Engine3_Phasewise_Execution_Backlog.md`**

That document should contain:

- file-by-file responsibilities,
- implementation order by module,
- exact coding backlog,
- acceptance criteria for each phase,
- testing checklist,
- deployment and runtime checklist.

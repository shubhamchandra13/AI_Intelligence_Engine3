# AI_Intelligence_Engine3
## Phasewise Execution Backlog

**Version:** 1.0  
**Document Type:** Implementation Backlog  
**Base System:** AI_Intelligence_Engine upgraded into AI_Intelligence_Engine3  
**Trading Scope:** Autonomous Live Paper Trading + After-Hours Historical Replay + Controlled Evolution  

---

## Table of Contents

1. Purpose
2. Upgrade Principle
3. Target Outcome
4. Module Responsibilities
5. Phase 1 Backlog
6. Phase 2 Backlog
7. Phase 3 Backlog
8. File-by-File Implementation Map
9. Acceptance Criteria
10. Testing Checklist
11. Execution Order
12. Deployment Readiness Checklist

---

## 1. Purpose

This document defines the exact execution backlog for converting the current `AI_Intelligence_Engine` into `AI_Intelligence_Engine3` without losing any existing capability.

The purpose is:

- preserve the current working base,
- upgrade the architecture in a controlled way,
- avoid breaking existing live paper functionality,
- add after-hours historical replay trading,
- add structured evaluation and evolution,
- keep the system disciplined and auditable.

---

## 2. Upgrade Principle

`AI_Intelligence_Engine3` must be treated as an **upgrade version**, not a rewrite from scratch.

### Rules
- nothing important from the current engine should disappear,
- existing working live-paper capabilities should be preserved,
- refactoring should extract and organize logic rather than delete it blindly,
- new features should wrap and extend the base system,
- the migration should happen in stages,
- each phase should remain runnable.

### Meaning in Practice
- existing Upstox integration stays,
- existing paper execution stays,
- existing strategy components stay,
- existing ML/evolution pieces stay where reusable,
- monolithic logic gets modularized,
- replay and mode orchestration get added around the current base.

---

## 3. Target Outcome

At completion, `AI_Intelligence_Engine3` should:

- run live paper trading during market hours,
- run autonomous historical paper trading after market close,
- log both trade types separately,
- evaluate performance by scenario and regime,
- adapt through safe nightly tuning,
- keep a champion-challenger configuration model,
- become progressively more mature without uncontrolled overtrading.

---

## 4. Module Responsibilities

## 4.1 Existing Modules to Preserve

### Core Live Data and Broker Layer
- `core/upstox_client.py`
- `core/data_fetcher.py`
- `core/upstox_websocket_engine.py`
- `core/upstox_auth_engine.py`

### Existing Trading and Intelligence Layer
- `main.py`
- `engines/institutional_paper_execution_engine.py`
- `engines/trade_logger.py`
- `engines/trade_intelligence_engine.py`
- `engines/ml_evolution_engine.py`
- `dual_mode_engine.py`

### Existing Risk and Signal Support
- `engines/confidence_engine.py`
- `engines/adaptive_risk_engine.py`
- `engines/regime_detection_engine.py`
- `engines/regime_clustering_engine.py`
- `engines/strike_selection_engine.py`
- `engines/target_multiplier_engine.py`
- `core/structure_engine.py`
- `core/multi_timeframe.py`
- `core/market_intelligence_v2.py`

---

## 4.2 New Modules to Add

### `core/mode_manager.py`
Responsibility:
- decide current system mode,
- expose time-based mode rules,
- support forced/manual mode override,
- keep mode transitions predictable.

### `core/data_provider.py`
Responsibility:
- standardize data access for live and replay,
- provide a common interface for market snapshots,
- reduce strategy dependency on data source type.

### `engines/strategy_engine.py`
Responsibility:
- host reusable signal logic,
- generate decisions for both live and replay,
- return structured decision output,
- remove decision logic from `main.py`.

### `engines/historical_replay_engine.py`
Responsibility:
- replay 3-6 month candles sequentially,
- emulate a live environment using historical data,
- use the same strategy engine as live mode,
- generate simulated paper trades.

### `engines/evaluation_engine.py`
Responsibility:
- compute metrics,
- compare live vs replay behavior,
- generate reports,
- identify strong and weak setups.

### `engines/config_evolution_engine.py`
Responsibility:
- tune safe parameters,
- create challenger configs,
- validate candidate improvements,
- prevent uncontrolled changes.

### `core/scheduler.py`
Responsibility:
- automate daily mode transitions,
- coordinate live, replay, and evolution runs,
- maintain a consistent daily cycle.

---

## 5. Phase 1 Backlog

## Phase 1 Goal
Stabilize and modularize the current engine without losing existing behavior.

## Phase 1 Deliverable
A mode-ready, reusable, stable live paper trading core.

### Task 1.1: Baseline Repository Audit
Files:
- `main.py`
- `config.py`
- `core/data_fetcher.py`
- `core/upstox_client.py`
- `engines/institutional_paper_execution_engine.py`
- `engines/trade_logger.py`

Actions:
- map current live trading flow,
- identify signal generation points,
- identify execution points,
- identify logging boundaries,
- identify runtime dependencies.

Output:
- architecture notes,
- dependency map,
- current flow summary.

### Task 1.2: Extract Strategy Logic
New file:
- `engines/strategy_engine.py`

Actions:
- move reusable decision logic out of `main.py`,
- define clear inputs and outputs,
- return structured decision object.

Expected structured output:
- action,
- symbol,
- confidence,
- rationale,
- risk status,
- targets,
- strategy metadata.

### Task 1.3: Add Mode Manager
New file:
- `core/mode_manager.py`

Actions:
- create time-based mode detection,
- add support for:
  - `LIVE_PAPER`
  - `HISTORICAL_REPLAY`
  - `EVOLUTION`
  - `IDLE`
- allow override flags from config/runtime.

### Task 1.4: Add Data Provider Abstraction
New file:
- `core/data_provider.py`

Actions:
- define common data interface,
- create live provider wrapper,
- ensure strategy engine consumes standardized snapshot input.

### Task 1.5: Preserve and Validate Paper Execution
Files:
- `engines/institutional_paper_execution_engine.py`

Actions:
- validate entry flow,
- validate exit flow,
- validate capital tracking,
- validate cooldown handling,
- confirm compatibility with future replay mode.

### Task 1.6: Stabilize Main Runtime
Files:
- `main.py`

Actions:
- reduce business logic inside UI loop,
- move signal computation to strategy engine,
- prepare main runtime to act as live orchestrator.

### Phase 1 Acceptance Criteria
- current live paper flow still runs,
- strategy logic is reusable,
- mode manager exists,
- no major behavior regression,
- paper execution remains functional.

---

## 6. Phase 2 Backlog

## Phase 2 Goal
Add historical replay trading and structured trade separation.

## Phase 2 Deliverable
An autonomous after-hours historical simulation engine using the same trading brain as live mode.

### Task 2.1: Build Historical Replay Engine
New file:
- `engines/historical_replay_engine.py`

Actions:
- load historical candles,
- replay candles chronologically,
- build synthetic market snapshots,
- invoke strategy engine at each replay step,
- invoke paper execution engine for replay trades.

### Task 2.2: Define Replay Dataset Window
Files:
- `config.py`

Actions:
- add replay window settings,
- add symbol selection settings,
- add replay batch controls,
- add start/end date support.

Recommended config fields:
- `REPLAY_LOOKBACK_MONTHS`
- `REPLAY_SYMBOLS`
- `REPLAY_INTERVAL`
- `REPLAY_MAX_DAYS_PER_BATCH`
- `REPLAY_START_DATE`
- `REPLAY_END_DATE`

### Task 2.3: Separate Trade Sources in Logging
Files:
- `engines/trade_logger.py`
- database schema

Actions:
- add trade source tagging,
- preserve live trade records,
- add replay metadata,
- update insert logic to support source-aware analytics.

Required fields:
- `trade_mode`
- `session_type`
- `strategy_version`
- `config_version`
- `replay_batch_id`
- `market_regime`
- `confidence_bucket`
- `data_source`

### Task 2.4: Create Evaluation Engine
New file:
- `engines/evaluation_engine.py`

Actions:
- compute win rate,
- compute expectancy,
- compute max drawdown,
- compute profit factor,
- compute regime-wise stats,
- compute confidence bucket stats,
- compute time-of-day behavior for live mode.

### Task 2.5: Add Replay Reporting
Actions:
- create summary objects,
- save replay run results,
- optionally create report files under `reports/replay_reports/`.

### Phase 2 Acceptance Criteria
- replay can run end-to-end,
- live and replay trades are stored separately,
- strategy engine works in both environments,
- replay results can be evaluated independently,
- no live logging regression.

---

## 7. Phase 3 Backlog

## Phase 3 Goal
Add controlled self-improvement and daily automation.

## Phase 3 Deliverable
A scheduled, nightly-evolving paper trading system with safe promotion rules.

### Task 3.1: Build Config Evolution Engine
New file:
- `engines/config_evolution_engine.py`

Actions:
- load live and replay evaluation results,
- tune safe parameters only,
- create candidate configs,
- score challenger vs champion.

Safe tuning candidates:
- min confidence,
- cooldown windows,
- regime filters,
- target multipliers,
- stop-loss styles,
- time restrictions,
- risk caps.

### Task 3.2: Add Champion-Challenger Flow
Files:
- `database/optimized_params.json`
- `database/ml_model_registry.json`

Actions:
- define current champion config,
- store challenger proposal,
- add promotion rules,
- add rollback protection.

### Task 3.3: Add Scheduler
New file:
- `core/scheduler.py`

Actions:
- create daily cycle,
- switch modes based on time,
- coordinate replay and evolution after market close,
- support manual override.

### Task 3.4: Create Operational Scripts
New files:
- `scripts/run_live.py`
- `scripts/run_replay.py`
- `scripts/run_evolution.py`
- `scripts/run_daily_cycle.py`

Actions:
- expose individual workflows,
- simplify operations,
- support debugging and isolation.

### Task 3.5: Add Reporting and Dashboard Visibility
Files:
- `dashboard_server.py`
- `dashboard_app.js`
- `dashboard_index.html`
- `dashboard_style.css`

Actions:
- show current mode,
- show live stats,
- show replay stats,
- show active config,
- show evolution result,
- show champion/challenger status.

### Phase 3 Acceptance Criteria
- scheduler can drive the daily system cycle,
- replay and evolution run automatically,
- configs are versioned and controlled,
- dashboard reflects new operational state,
- engine remains stable through full-day use.

---

## 8. File-by-File Implementation Map

## Files to Preserve
- `main.py`
- `config.py`
- `core/data_fetcher.py`
- `core/upstox_client.py`
- `core/upstox_websocket_engine.py`
- `engines/institutional_paper_execution_engine.py`
- `engines/trade_logger.py`
- `engines/ml_evolution_engine.py`
- `dashboard_server.py`
- `dashboard_app.js`

## Files to Refactor
- `main.py`
- `engines/trade_logger.py`
- `config.py`

## Files to Create
- `core/mode_manager.py`
- `core/data_provider.py`
- `core/scheduler.py`
- `engines/strategy_engine.py`
- `engines/historical_replay_engine.py`
- `engines/evaluation_engine.py`
- `engines/config_evolution_engine.py`
- `scripts/run_live.py`
- `scripts/run_replay.py`
- `scripts/run_evolution.py`
- `scripts/run_daily_cycle.py`

## Optional Reporting Folders to Add
- `reports/daily_reports/`
- `reports/replay_reports/`
- `reports/evolution_reports/`

---

## 9. Acceptance Criteria

## System-Level Acceptance
- live paper trading still works,
- historical replay works with the same strategy engine,
- logging preserves trade source separation,
- evolution does not overwrite configs blindly,
- upgraded engine retains base functionality.

## Phase-Level Acceptance

### Phase 1
- no live paper regression,
- modular strategy engine introduced,
- mode manager introduced.

### Phase 2
- replay trades execute autonomously,
- replay logs are tagged separately,
- replay metrics can be reviewed.

### Phase 3
- nightly evaluation runs,
- challenger config can be generated,
- promotion rules are enforced,
- daily cycle can be automated.

---

## 10. Testing Checklist

## Functional Tests
- live paper entry test,
- live paper exit test,
- cooldown test,
- duplicate trade prevention test,
- capital accounting test,
- historical replay step progression test,
- replay entry/exit test,
- config promotion test,
- dashboard mode display test.

## Data Integrity Tests
- trade logs contain source tags,
- replay batch IDs persist,
- no null critical fields in trade logs,
- config versions are stored correctly.

## Safety Tests
- low-confidence setup block,
- stale data block,
- max-drawdown stop behavior,
- max concurrent position rule,
- failed replay batch recovery.

---

## 11. Execution Order

### Recommended Build Order
1. preserve current baseline and verify clone,
2. audit and extract strategy logic,
3. add mode manager,
4. add data provider abstraction,
5. stabilize main live paper orchestrator,
6. build historical replay engine,
7. redesign logging separation,
8. build evaluation engine,
9. build config evolution engine,
10. add scheduler and runner scripts,
11. extend dashboard,
12. run multi-day paper validation.

---

## 12. Deployment Readiness Checklist

Before considering `AI_Intelligence_Engine3` operationally ready:

- Upstox auth flow is stable,
- live paper session can run for a full market day,
- historical replay can run without crashing,
- database logging is clean,
- evaluation reports are generated,
- evolution logic is controlled,
- manual override exists,
- current mode is visible,
- rollback path is available,
- no important base feature from `AI_Intelligence_Engine` is missing.

---

## Final Note

`AI_Intelligence_Engine3` should grow by **preserving the old engine and layering structured improvements on top of it**.

This upgrade path is correct because:

- it avoids losing working functionality,
- it reduces rewrite risk,
- it makes debugging easier,
- it lets the system evolve in a controlled, testable way.

The correct approach is:

**preserve -> modularize -> replay -> evaluate -> evolve -> automate**

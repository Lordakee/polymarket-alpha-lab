# Project Instructions

## Scope

This repository is for Polymarket market research, data engineering, strategy validation, paper trading, risk analysis, and staged automation toward user-authorized execution.

Current phase boundary: do not add live trading, account authentication, private-key handling, or automated order placement in Phase 1. Treat this as a staged delivery boundary, not a permanent project non-goal.

Future execution work must be introduced through explicit roadmap documentation, validation gates, risk controls, audit logging, and user authorization for credential handling. Do not read, print, or move stored secrets unless the task is specifically about secret-management infrastructure.

Do not perform compliance, legal, geographic-access, or regulatory analysis in this repository unless the user explicitly reopens that topic.

## CodeGraph

This repository is intended to be indexed by CodeGraph. If `.codegraph/` exists at the repository root, use CodeGraph before `rg`, `find`, or manual file reads when the goal is to understand or locate code:

```bash
codegraph explore "question or symbol names"
codegraph node <symbol-or-file>
```

Use `rg` only after CodeGraph is not enough or the task is plain text search across documentation.

## Data Source Priority

Use official Polymarket sources first:

1. Gamma API for market, event, tag, search, and metadata discovery.
2. CLOB API for order books, prices, spreads, midpoints, price history, and public market data.
3. Data API for public trades, positions, activity, holders, open interest, and leaderboards.
4. WebSocket market channel for real-time watchlist updates.
5. Officially documented third-party chain data only for historical backfill or verification.

Avoid using website scraping as a primary data path unless a needed field is unavailable through official APIs.

## Engineering Defaults

- Keep source files small and domain-focused.
- Preserve raw API payloads before normalization.
- Distinguish `null`, `0`, and `unknown` in data models.
- Use executable bid/ask and order book depth for research calculations, not only displayed midpoint.
- Keep all research outputs reproducible and timestamped.

## Agent Coordination Defaults

- Treat parallel agent utilization as a durable project operating constraint: while avoiding write conflicts, default to keeping multiple independent subagents active, reclaim completed subagents promptly, and redeploy capacity to the next independent research, review, or implementation task.
- Keep as many subagents active as is useful when there are independent tasks that can run in parallel.
- Avoid assigning multiple subagents to edit the same files, the same batch of files, or the same tightly coupled responsibility at the same time.
- For write tasks, split ownership by non-overlapping files or modules before dispatching subagents, and keep each subagent inside its assigned write scope.
- Close completed subagents promptly, then dispatch fresh independent tasks when useful so parallel execution stays active without creating file conflicts.

## Model Defaults

- Codex subagents dispatched for this project should use model `gpt-5.5` with reasoning effort `xhigh`.
- Local opencode reviews for this project should use model `zhipuai-coding-plan/glm-5.2` with variant/thinking level `max`.
- If the user informally writes `xhign` for the Codex subagent reasoning level, treat it as the executable setting `xhigh`.

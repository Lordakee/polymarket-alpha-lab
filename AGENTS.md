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

## OMO / Sisyphus Session Workflow (opencode only — codex ignores this section)

This section binds every opencode/Sisyphus session working on this repository. It is set by the user on 2026-06-16 and survives across sessions. Codex does not use this section; codex resume continues from the latest main commit.

### Authority and handoff

- The user has fully handed the project to opencode/Sisyphus. Codex is paused; it may resume later or run in parallel.
- Work directly in `/home/ubuntu/polymarket-alpha-lab` on the `main` branch. Do not use worktrees or copies.
- A rollback tag `codex-handoff-20260616` is placed at the last codex commit (currently `8182787 feat: add project screening v0`). Keep commits granular and independently revertable so codex can selectively roll back.

### Git strategy

- Commit locally on `main` as work progresses.
- Do NOT push to `origin/main` unless the user explicitly asks. Keep the remote pinned at the codex handoff commit so codex can resume from a clean remote.
- Push only when the user explicitly authorizes it.

### Model configuration (oh-my-openagent.json)

- All OMO agents and categories use `zhipuai-coding-plan/glm-5.2` with variant `max`.
- Subagent parallelism: maximize throughput. Default to firing 5-8 background subagents for independent work, reclaim finished subagents promptly, and redeploy capacity to the next independent task. Drop to 3-4 only if the API returns rate-limit errors. Never serialize independent tasks.

### Dual review gate with reviewer fallback (MANDATORY — never skip)

External review uses TWO reviewers with a fallback policy. **Primary reviewer: Claude Code.** If Claude Code fails twice consecutively (API error / connection / gateway), **fall back to Codex** for that gate.

**Primary reviewer — Claude Code** (`claude-opus-4-8`, effort `max`):

```bash
claude -p --model claude-opus-4-8 --effort max "<review prompt>"
```

**Fallback reviewer — Codex** (`gpt-5.5`, reasoning `xhigh`, bypass sandbox + read-only prompt):

```bash
codex exec -m gpt-5.5 --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check -c model_reasoning_effort=xhigh "<review prompt>"
```

(Codex reads the prompt as an argument or via stdin. NOTE: `-s read-only` sandbox's bwrap loopback fails in this environment (`bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted`), so use `--dangerously-bypass-approvals-and-sandbox` instead and append a HARD read-only constraint to the prompt: "DO NOT modify/create/delete ANY file; output ONLY verdict + findings." Run from the project root.)

**Fallback rule:** Count consecutive Claude Code failures (API/connection/gateway errors, NOT substantive findings). After the 2nd consecutive failure, switch to Codex for that gate. A substantive Claude verdict (Proceed/Block with findings) always resets the failure counter to 0. Record which reviewer produced each verdict and the failure count.

Two gates are mandatory for every stage:

1. **Pre-stage plan gate** — Before any implementation work begins in a stage:
   - Sisyphus drafts the stage plan (goal, scope, files, approach, risks, tests).
   - Submit the plan to the primary reviewer (Claude Code); fall back to Codex after 2 failures.
   - Implementation may start ONLY after the reviewer approves. If the reviewer requests changes, revise the plan and re-review until approved.

2. **Post-stage code gate** — After a stage's implementation is complete and tests pass:
   - Submit the stage plan plus the resulting code/diffs to the primary reviewer (Claude Code); fall back to Codex after 2 failures.
   - The next stage may begin ONLY after the reviewer approves. If the reviewer requests changes, fix them and re-review until approved.

Stage boundary definition: a stage is any meaningful unit of work that has its own plan and deliverable (typically one Node in the existing plan/spec cadence, or a Sisyphus todowrite milestone). Do not collapse multiple stages into one review.

### Workflow summary per stage

1. Draft stage plan → pre-stage review (Claude Code primary, Codex fallback after 2 failures) → approval.
2. Execute with maximum parallel subagents (5-8 background).
3. Run tests, verify diagnostics clean on changed files.
4. Commit locally on main (granular commits).
5. Submit plan + code to post-stage review (Claude Code primary, Codex fallback after 2 failures) → approval.
6. Only then proceed to the next stage.

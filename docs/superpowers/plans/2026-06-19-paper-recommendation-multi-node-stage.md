# Paper Recommendation Multi-Node Stage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the current paper recommendation stage by wiring side-edge strategy rows into ranked paper recommendation queues and research packets.

**Architecture:** This is a pure local report stage. Each node consumes caller-supplied paper objects, emits frozen dataclass reports with hard `paper_only`, `report_only`, and `readonly` flags, and keeps deterministic ordering plus explicit reason codes. No node may create live trading, auth, wallet, private-key, client-mutation, or order-mutation behavior.

**Tech Stack:** Python stdlib, frozen dataclasses, `Decimal`, pytest, CodeGraph-first navigation, local read-only audit reviews.

---

## Stage Scope

Develop only these current nodes:

- `src/polymarket_alpha_lab/paper_side_edge_adapter.py`
  - Adapts strategy-like paper rows into canonical `PaperProbabilitySideEdgeInput` values and delegates to `paper_probability_side_edge`.
  - Preserves source reason codes and rejects unsafe rows/configs before report construction.
- `src/polymarket_alpha_lab/paper_probability_recommendation_queue.py`
  - Ranks canonical `PaperProbabilitySideEdgeRow` reports into a bounded paper review queue.
  - Separates research-review, watch/await-fresh-context, skip, and excluded counts.
- `src/polymarket_alpha_lab/paper_research_packet.py`
  - Produces concise research packet rows from queued paper recommendations.
  - Prioritizes packet checks without promoting rows to execution instructions.

Existing upstream dependency:

- `src/polymarket_alpha_lab/paper_probability_side_edge.py`
  - Treat as the canonical side-edge report contract. Do not widen it unless a focused failing test proves the contract itself is wrong.

## Hard Boundaries

Every module, dataclass, builder, test, and doc update in this stage must remain:

- paper-only
- report-only
- readonly
- deterministic over caller-supplied local inputs
- free of live trading, account auth, credential reads, wallet/private-key access, signing, real order construction, order submission, order cancellation, relayer calls, exchange mutation, network mutation, or client mutation

Allowed outputs are research/review artifacts only. A queue row, packet row, rank, next step, side, score, allocated notional, requested notional, reason code, or required check is not an order, not a trading instruction, and not financial advice.

Do not add package-root exports, CLI commands, file readers, log writers, replay/from-file helpers, API clients, browser automation, or any network path unless a later approved plan explicitly changes this boundary.

## Implementation Tasks

### Task 1: Side-Edge Adapter

**Files:**
- Create or modify: `src/polymarket_alpha_lab/paper_side_edge_adapter.py`
- Test: `tests/test_paper_side_edge_adapter.py`
- Test: `tests/test_paper_side_edge_adapter_scope.py`

- [ ] Add behavior tests for converting safe strategy rows into canonical `PaperProbabilitySideEdgeInput` values.
- [ ] Add behavior tests proving YES/NO probability semantics, all cost components, freshness flags, depth fields, and reason-code preservation flow into the canonical side-edge report.
- [ ] Add scope tests proving unsafe `paper_only`, `report_only`, and `readonly` rows/configs are rejected and no live/auth/wallet/order/client surface exists.
- [ ] Implement the adapter as a thin pure reducer over supplied rows.
- [ ] Keep public exports limited to adapter config, adapter input row, conversion helper, and report builder.

### Task 2: Recommendation Queue

**Files:**
- Create or modify: `src/polymarket_alpha_lab/paper_probability_recommendation_queue.py`
- Test: `tests/test_paper_probability_recommendation_queue.py`
- Test: `tests/test_paper_probability_recommendation_queue_scope.py`

- [ ] Add behavior tests for ranking `recommend` rows before eligible `watch` rows and excluding or filling with rejects only as specified by capacity rules.
- [ ] Add behavior tests for deterministic tie breakers, max queue size, minimum score, include-watch behavior, counts, and frozen dataclass invariants.
- [ ] Add scope tests restricting imports to stdlib plus `paper_probability_side_edge`, and blocking forbidden names/imports for auth, wallet, private keys, account reads, orders, clients, HTTP, filesystem loading, and mutation.
- [ ] Implement queue config, queue row, queue report, and `build_paper_probability_recommendation_queue_report`.
- [ ] Preserve report-only semantics: output `recommended_next_step` values such as research review or await fresh context, never execution instructions.

### Task 3: Research Packet

**Files:**
- Create or modify: `src/polymarket_alpha_lab/paper_research_packet.py`
- Test: `tests/test_paper_research_packet.py`
- Test: `tests/test_paper_research_packet_scope.py`

- [ ] Add behavior tests for packet ordering, packet rank, priority buckets, required checks, min score filtering, skip rows, and count consistency.
- [ ] Add behavior tests for Decimal-only fields, frozen dataclasses, reason-code normalization, and safe handling of missing allocated/requested notional.
- [ ] Add scope tests proving hard safety flags are enforced and no live execution, CLI, network, auth, wallet, or order surface is exposed.
- [ ] Implement packet config, input row, packet row, report, and `build_paper_research_packet_report`.
- [ ] Keep packet rows as research artifacts only; required checks must describe review work, not trading actions.

## Verification Gates

Run focused gates before asking for audit:

```bash
.venv/bin/python -m pytest \
  tests/test_paper_side_edge_adapter.py \
  tests/test_paper_side_edge_adapter_scope.py \
  tests/test_paper_probability_recommendation_queue.py \
  tests/test_paper_probability_recommendation_queue_scope.py \
  tests/test_paper_research_packet.py \
  tests/test_paper_research_packet_scope.py -q
```

Run repository gates before commit:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall src tests
git diff --check
codegraph status .
```

If `.codegraph/` exists and CodeGraph reports stale indexing, sync it before final review and record the command/result in the handoff. Also run a tracked-content secret scan before push.

## Audit Gate

Use the project reviewer fallback rule for both pre-stage and post-stage gates:

- Primary reviewer: Claude Code with `claude-opus-4-8`, effort `max`.
- If Claude fails twice consecutively because of API, gateway, connection, account, or timeout failures, fall back for that gate to local OpenCode/opencode with `zhipuai-coding-plan/glm-5.2`, variant/thinking `max`.
- A substantive Claude verdict resets the Claude failure count to zero.
- Fallback review prompts must be read-only and must explicitly say: `DO NOT modify/create/delete ANY file; output ONLY verdict + findings.`
- Implementation may proceed only after the pre-stage plan gate has no Critical findings and a `Proceed` or equivalent accepted verdict.
- Commit/push may proceed only after the post-stage code gate has Critical findings `0`, Important findings `0`, and `Verdict: Proceed` or equivalent.

Audit prompt must include this plan, the focused diff, untracked stage files, verification output, and the hard boundary list. Treat any live/auth/wallet/private-key/account/order/signing/client-mutation/network-mutation behavior as Critical.

## GitHub Push Checkpoint

Push this stage to GitHub only after all checkpoint criteria are true:

- The stage has one focused local commit.
- Worktree is clean except unrelated parallel-worker files that are intentionally outside this stage and not part of the commit.
- Focused stage tests pass.
- Full pytest suite passes.
- Python compile verification passes.
- `git diff --check` is clean.
- CodeGraph is synced when `.codegraph/` exists.
- Tracked-content secret scan reports no leaked credentials or tokens.
- Post-stage external review passes under the Claude-primary/OpenCode-fallback rule.
- No unresolved Critical or Important findings remain.
- The final diff contains no live trading, auth, wallet/private-key, account-read, order placement/signing/submission/cancellation, relayer, exchange mutation, network mutation, or client-mutation surface.

Do not push half-finished work, failing tests, unreviewed code, or code with unresolved review findings.

# V1 takeover audit: model boundaries and delivery path

Date: 2026-09-19. Packages: **WP-02 / WP-06**, with the existing WP-03 execution
boundary regression-tested. This is an engineering audit, not live-trading,
provider-billing, market-source or strategy-performance certification.

## Scope and source

Baseline `a0fffde24d547cd70c950a39a3fada5f7e29cf92`, tree
`2df55db14ee07573cd55c8547fc7600763d59c60`. All 6,463 committed files were
verified against their Git blobs and the complete tree. Source was obtained via
a separate read-only pinned-source export; that helper is not part of this patch.

The inventory contains 2,830 Python source files (2,458,905 lines), 3,221 Python
test files and 304 Markdown documentation files. These counts are structural
inventory, **not a claim of line-by-line review of every historical module**.
Targeted review covered the current research agent, captured requests/execution,
model-call reservation preflight, legacy GLM transport, task entry and delivery
contracts. Reusing the existing V1 path takes priority over adding report layers.

## Confirmed findings and fixes

| Priority | Finding | Evidence and correction |
| --- | --- | --- |
| P1 security | Legacy GLM dataclass repr exposes the caller token; HTTP endpoints and redirects can transmit credentials outside the original operation. | Synthetic baseline 302 generated two requests, the second HTTP with Authorization. Hide the token in repr, validate HTTPS endpoints/header controls, reject all redirects via a private opener, and mark Authorization nonredirectable. No real token or socket used. |
| P2 correctness/cost | An optional fresh source plus an unreadable mandatory source enters a model loop that cannot finish with valid citations. | Baseline made three synthetic calls then blocked. Fail with existing `invalid_citations` before any model call; retain empty-catalog reason and inclusive freshness boundaries. Align first-message budget preflight; keep the original blocked capture, hashes and inert replay. |
| P2 input contract | Direct agent accepts more than 20 mandatory citations although the finish schema allows at most 20. | Separate self-review reproduced 21/100-source failures. Reject invalid cardinality before calling a model, matching the existing captured-request bound. |
| P1 delivery | Owner decisions were stale in current planning documents. | Record D1 local agents, D2 all needed research data and D3 no first-round business scale/monetary cap. WP-02 is PARTIAL, not AWAITING_OWNER. Preserve historical sections as historical. |
| P1 delivery, OPEN | The standalone task entry has no real model factory; positive-micros allowances cannot express the selected uncapped first-round policy. | No adapter or new policy is claimed by this patch. These are the next implementation items below, not requests to repeat D1-D3 or search for keys. |

No captured-request codec, durable identity, reservation refund/retry rule,
SQL migration, dependency, existing workflow, user database, market source,
credential store or order operation is changed. A blocked attempt is evidence,
not a completed research forecast. Existing historical records replay unchanged.

## Separate self-review and tests

Review was performed in a separate pass by the **same assistant**, not an
external/fresh-agent audit or zero-defect guarantee. It included trace-through of
claim/permit order, future/stale evidence and inclusive boundaries, overfull
mandatory-citation sets, private-vs-global opener behavior, HTTP errors,
interrupt propagation and existing error-text compatibility.

| Evidence | Actual result |
| --- | --- |
| Pristine baseline `verify_local.py --full` | 38,616 passed / 42 skipped; full verification exit 0 |
| Initial 54 new adversarial cases against baseline | 39 failed / 15 passed (expected RED, retained) |
| First fix plus existing focused regressions | 1 failed / 328 passed: blank-token error text changed; restored the original text, not its test |
| Corrected focused tests | 329 passed |
| Additional review counterexamples, before fix | 2 failed / 16 deselected: 21/100 required sources |
| Runtime-focused six-file suite | 338 passed, including 63 new cases |
| First candidate full suite | 1 failed / 38,678 passed / 42 skipped: an old policy test confused an allowed research client with a review provider |
| Corrected policy scope | Preserve all historical review assertions; exclude the current owner research-client override from the old OpenCode word ban, and test their separation explicitly |

Local evidence used Linux/Python 3.13.5 and the existing environment, not the
hosted locked Python 3.12 environment. Exact final full/hosted candidate runs,
commit/tree identities and any failures belong in the implementation PR. Do not
merge before the applicable final-revision gates pass. Skipped native/opt-in
checks are not successes. Overlapping test totals must not be added together.

Focused command:

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=.:src python -m pytest -q tests/test_llm_transport_security.py tests/test_research_required_evidence.py tests/test_llm_forecast.py tests/test_llm_forecast_scope.py tests/test_team_research_agent.py tests/test_research_model_budget.py
```

The synthetic HTTP tests prohibit socket connection, substitute in-memory
responses and use a noncredential sentinel. They cover five redirect statuses
across downgrade/cross-host/same-host destinations, malformed endpoints, HTTP
failures, no retry, interruption, and successful unchanged response conversion.
Evidence tests cover BTC and ETH, optional vs required evidence, zero-call
captures under tiny/normal message allowances and replay without client entry.

## Fixed next implementation sequence

1. **WP-02: one local CLI adapter, Codex first.** Keep the existing inert
   `model_factory(team_id)` / `complete(messages_json, max_output_tokens)` and
   strict `ResearchModelReply` boundary. Verify an explicitly configured
   executable/version/model. Admit only task-approved messages; isolate working
   directory, environment, sessions, plugins/MCP and external tools. Bound
   subprocess output, elapsed I/O and cleanup; prove strict conversion, no hidden
   retry/repair/fallback and no secret in evidence. Claude Code, OpenCode, Grok
   CLI and ZCode CLI are allowed alternatives, not five certified adapters.
2. **WP-02 / WP-03: represent uncapped authorization honestly.** D3 removes a
   first-round business scale/monetary ceiling, not task identity, finite single
   operations, safety/resource limits, cutoff or stop controls. Design an
   explicit reviewed policy compatible with original records. Never fabricate
   zero prices, huge allowances or fee-bound attestations. Record actual usage
   and distinguish unknown fees from zero; do not silently use a legacy
   unbudgeted API. Capped allowances remain available with their current meaning.
3. **WP-03: combined operational acceptance.** Use the selected adapter after
   synthetic process tests, then verify two turns, stop/restart, mixed failures
   and incomplete claims without duplicate original requests or lost history.
4. **WP-04 / WP-05: actual BTC/ETH research-to-settlement-to-paper evidence.**
   Preserve prospective times and contract-matched source/granularity; obtain
   independent human settlement review. Include real spread/slippage/fees and
   rejected/unknown samples. Engineering examples do not establish a profitable
   strategy or statistically adequate sample.
5. **WP-06: one fixed Windows delivery.** Validate selected configuration,
   original-root data preservation/version switching, negative recovery and
   pinned release assets. Existing PS5.1 first-start root cause remains open;
   neither this patch nor a later green sample repairs historical failures.

No local task is necessary for this source patch. Only selected CLI installation,
explicit local configuration and authorized real-run evidence should require a
later local handoff; do not repeat completed DB/network checks. Defer broad CLI
rewrites, new report families, distributed orchestration, eight extra teams and
live trading. **G1 alone remains complete: V1 is still 1/6.**

## Limitations and remaining transport risk

The legacy GLM hardening is not the selected V1 adapter. Its socket timeout is
not a universal wall-clock deadline, response-body size is not bounded here,
and it is not a general redactor for secrets echoed by a provider. The caller
still chooses an HTTPS endpoint; this is not an endpoint-identity allowlist or
protection against malicious in-process code. Client memory is not securely
erased. These limitations must not be hidden behind the new tests; real V1 use
requires the separately verified local-adapter contract above.


### Full-suite review follow-up

The first candidate full run was not green and is retained separately. Its only
failure was a documentation test banning the word OpenCode throughout all current
instructions, including the owner's newly permitted research-client list. The
negative assertion now covers the same historical policy body below Scope; all
original verified-push and review assertions remain. An additional test explicitly
separates allowed research clients from reviewer selection. This does not select
OpenCode as a reviewer or disable the review gate. The plan also spells out the
already-PARTIAL WP-04 status in its historical integration summary; it does not
close any gate. Final full/hosted results must use this corrected complete tree.

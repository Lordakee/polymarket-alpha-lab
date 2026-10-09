# G2 activation-readiness pack (draft; requests decisions; authorizes nothing)

Worker N1 of the post-L9 cycle (§66 all-native-subagent flow), 2026-10-09.
Companion operator document: [g2-first-real-run-runbook-draft.md](g2-first-real-run-runbook-draft.md).
Plan charter: `.agent-artifacts/polymarket-alpha-lab/post-l9-planning/README.md`
(node N1, with Revision 1 findings F1/F3/F5 binding).

**This document is a DRAFT decision-request package. It authorizes nothing.**
`activation_authorized=false`; real provider calls remain false; no credential
material appears here or is requested here. Filling or approving any part of
the draft record below does not flip any activation flag (the L8-D template's
own rule, [research-dispatch.md](../research-dispatch.md) lines 646-648).

Baseline pins (verified `git rev-parse` on the recording host):

| Item | Value |
|---|---|
| Repository | https://github.com/Lordakee/polymarket-alpha-lab, branch `main` |
| Recording commit | `67cad027969f34bc21dfad64bb4fcb1b7e72b2d9e` (67cad027) |
| Recording tree | `3cdb1e846c26b706b778970e0c5dbb1f8640a95f` (worktree was clean at 67cad027 before this draft's two new files) |
| Commit subject | "docs: record the L9 node final-review PASS and close the node pending T8/D-1 (section 68)" |

Evidence discipline (plan Revision 1 F3): every evidence claim below derives
exclusively from LANDED DELIVERY_PLAN.md sections and committed repository
artifacts at 67cad027. W12/W15 environment facts (e.g. the on-154 copy of the
T8 image, the 154 PG18 prefix, the transferred L8-B fixture) are execution
conveniences only: they may be referenced as re-verify instructions but NO
evidence pin in this pack rests on them. Where a value must be re-measured at
decision time, it is marked PENDING with the owning gate named.

Terminology guard: "D1–D3" (§7 owner decisions: local agent, research data,
no first-round cap) are settled and distinct from the NEW decision items
introduced below, which this pack writes as "D-1", "D-2", … per the plan
charter's Revision 1 F1 numbering.

---

## 1. The §65 activation-prerequisite mapping

§65 (DELIVERY_PLAN.md:2777-2799) states the activation prerequisites
verbatim (lines 2793-2796):

> "Effective activation requires accepted final engineering/native/review
> evidence, delivered contained transport, official-image qualification
> through actual L5 wiring, a non-shared trusted runtime, reviewed explicit
> per-call credential supply, and a Codex-approved pinned activation record
> with scoped PG evidence writes."

The table walks each prerequisite against what LANDED today. "L9 node
CLOSED pending T8/D-1" is the §68 final-review record at 67cad027
(DELIVERY_PLAN.md:3030-3042: VERDICT PASS; "节点关闭：pending 仅 T8/D-1").

| # | §65 prerequisite (verbatim fragment) | State | Landed evidence / owning gate |
|---|---|---|---|
| 1 | "accepted final engineering/native/review evidence" | **LANDED** for the L8/L9 engineering arc, with T8 as the single named exception (row 3) | L9 node final review VERDICT: PASS (§68:3030-3042: CI chain re-checked, W2 digests recomputed, frozen pins re-run 9/3, per-commit review chain verified, §67 binding contracts sampled at HEAD, honesty confirmed — "§65 证据点名其树 d3eec34f 满足"). L9.1 landing d3eec34f with the 154 verification chain (§68:3017-3023): binding T1 re-run 12/12 at the L9.1 digests; §65 five-file native block 322 passed/1 skipped (3:37) — L8 native closure (B 3 opt-ins + C 5 + corrected-banner round trip) CLOSED; `verify_local --full` PASS (log `~/pal-artifacts/l91-landing.log` on 154); CI green (run 37955091414); W3 native 121/1 and refusal-stability 40/0. Offline-half commit/review chain: W1 e337ccea (R-W1 PASS), W5 db44df7c (PASS), W6/W6b 91168a31 (R-W6 FAIL→R-W6b PASS), W2 ad07d3be (R-W2 PASS zero findings), W3 11e53cc2 (R-W3 PASS), native fix dd668cd1 (first failure preserved), L9.1 d3eec34f (R-W14 FAIL→supplemental PASS) — §68:2881-2913, 3002-3016. |
| 2 | "delivered contained transport" | **LANDED** | The relay surface is implemented, reviewed and natively exercised: relay core + ENGINE_SOURCE (e337ccea), profile schema v3 + typed RelayTrustConfig admission (db44df7c), RELAY_HELPER_SOURCE + two-value closed egress (ad07d3be), parent-side wiring with the S2 success contract and no-second-channel rule (11e53cc2, arbitration §68:2950-2973 conditions C1-C7), L9.1 reap/drain fixes (d3eec34f). Native proof on 154: binding T1 fd-crossing 12/12 twice (69e35331 pre-L9.1 at §68:2986-2991; re-run at L9.1 digests §68:3017-3018, zero C4 divergence both times), W3 parent-path native tests green (§68:3022-3023). §68 final review verified the §67 binding contracts at HEAD (§68:3033-3035). |
| 3 | "official-image qualification through actual L5 wiring" (= T8) | **PENDING-DECISION D-1 — NOT EXECUTED** | T8 gate file LANDED and reviewed (tests/test_research_claude_relay_native.py, commit 27d78ca7 "test(research): author the L9 native relay qualification gate (W4, T8)", review PASS with 3 findings applied; recorded in the W17 handoff docs/handoffs/l8-l9-status.md §3.2/§8, which landed with the L9.1 batch per §68:3023). The L9 node is closed with T8 as its only remaining gate, blocked on D-1 (§68:3024-3028). Nothing anywhere claims T8 ran. Execution procedure: runbook Step A. |
| 4 | "a non-shared trusted runtime" | **PENDING-DECISION D-1 — UNSATISFIED on the current record** | §68:2975-2981 records 154.89.153.24 as a SHARED machine by owner instruction ("共享机器，仅触碰 ~/polymarket-alpha-lab"). The template's own runtime_isolation fields require a "dedicated host identity" and a "dedicated non-shared UID/name; NEVER the shared ubuntu parent/supplier" (research-dispatch.md:670-676). The W13 recovery runbook's T8 step requires `POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_ISOLATED_HOST=1` to be set only on a genuinely dedicated host, else STOP — and that flag is one of the five mandatory probe variables (tests/claude_cli_probe.py:125-126,152), i.e. setting it IS the attestation. Decision D-1 below requests the owner's ruling with the §68 facts laid out. |
| 5 | "reviewed explicit per-call credential supply" | **PENDING-DECISION D-4 — designed, not approved, not executed** | The operator procedure is designed and landed as design text (research-local-agent.md:1513-1551: dedicated principal, private local channel, `FiniteInMemoryApiKeySupplier` one-slot-per-team, delayed model-phase delivery, no-erasure honesty, no credential in evidence). The supplier type and its stop-token identity binding are implemented and natively proven in the §54 composition (tests/test_project_postgres_uncapped_audit_native.py:347). Approval of the procedure AND of its execution is an owner-gated decision (§53:1681-1685 lists it among the remaining G2 prerequisites) and is preconditioned on D-1 (credentials are typed only on the dedicated principal). |
| 6 | "a … pinned activation record with scoped PG evidence writes" | **DRAFT PROVIDED (this document §3); PINNING IS PENDING-DECISION D-2** | The record template was delivered at 35478f53 (§66:2819-2820, design gate PASS). This pack fills it as a DRAFT with pinned evidence where it exists and PENDING markers naming owning gates where it does not. Making it "pinned" (status `approved-not-yet-effective` or `effective`) is the D-2 decision. |
| 7 | "Codex-approved" (deciding authority) | **TRANSLATED per §66 / plan F5 — not a prerequisite to satisfy but an authority to seat** | §66 (DELIVERY_PLAN.md:2801-2814) records the owner's 2026-10-07 instruction that ALL planning/arbitration/review is native-subagent; §63's "ask Codex" standing delegation (§63:2645-2648) and §64's model pin survive as history applying only to already-issued dispatches. The draft record's `deciding_authority` and `sign_off` fields are therefore filled with the native-arbitration wording (fresh, read-only subagent, explicit VERDICT line, Project Iron Rule 4), with the owner above it (Article 0; §6:155-156: any acceptance-criteria change requires the owner). No Codex dispatch is requested or implied. |

Downstream (not §65 prerequisites, recorded for honesty): the G2 real-research
half itself — at least one reviewed real execution per `crypto_btc`/
`crypto_eth` with authorization/identity/usage reconciliation and original
failures preserved (§61:2299-2301; §63:2743-2751) — plus G3 final combination
(§61:2303-2305), G4 real settlements (§4:74) and G5 real samples (§4:75)
remain open and are NOT advanced by this pack. G2's fixed-official-artifact
six-scenario synthetic-probe subcondition alone is closed (§63:2743-2751).
V1 completion stays 1/6 (§4:78).

---

## 2. Decision requests (owner/arbiter-gated; this pack decides none of them)

These are laid out with facts only. Per the plan charter §2, activation
authorization, the pinned activation record, non-shared runtime provisioning,
per-call credential supply approval and scoped real-run execution are all
owner/arbiter-gated; nothing below may be read as deciding or preconditioning
them (plan-review question 2).

### D-1 — Is 154.89.153.24 a "dedicated/non-shared host" in the §65 sense? (blocks T8 and rows 4-5 above)

- **What §65 requires:** "a non-shared trusted runtime". The activation-record
  template requires a dedicated host identity, a documented host-trust
  reference, and a dedicated non-shared principal — explicitly "NEVER the
  shared ubuntu parent/supplier" (research-dispatch.md:670-676).
- **What the record shows:** 154 is recorded as a shared machine by owner
  instruction; only `~/polymarket-alpha-lab` is touched; the one-time password
  was used solely to install the coordinator public key and never stored
  (§68:2975-2979). The L8-D credential procedure states a separate directory
  does not protect parent memory from the same UID or privileged observers
  (research-local-agent.md:1518-1524).
- **Facts the §68 record already carries for the decision** (§68:3025-3027,
  plan Revision 1 F1): `/home` contains only the `ubuntu` principal; all tmux
  sessions on the machine belong to it and are owner-operated; no other human
  users exist; sudo is passwordless.
- **What is being asked:** the OWNER's explicit attestation (or an arbitration
  ruling under §66) that 154 does — or does not — qualify as dedicated in the
  §65 sense. Possible shapes (the owner chooses; this pack is neutral):
  1. Attest 154 qualifies (e.g. single-trustee machine in the §65 sense) →
     T8 may run on 154 with `POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_ISOLATED_HOST=1`
     as the recorded attestation, and the runtime_isolation fields of the
     record are filled from the attestation.
  2. Rule 154 NOT dedicated → T8 and any activation-time credential supply
     wait for a qualified non-shared host (provisioning is a separate owner
     decision), or for an owner-defined alternative trust posture recorded as
     an acceptance change (§6:155-156).
- **Status:** OPEN. Until it resolves, T8 execution is BLOCKED and the §65
  rows 3-5 stay PENDING (plan Revision 1 F1; l8-l9-status.md §6).

### D-2 — Approval of the pinned activation record (gates effective activation)

- Requires row 3 (T8) evidence to exist first: the record's
  `contained_qualification` field must cite the executed T8 run. The draft in
  §3 therefore stays `status: blocked` and cannot even be submitted for
  approval before D-1 → T8.
- The approving authority under §66 is a native-subagent arbitration (fresh,
  read-only, VERDICT line) with owner confirmation; see row 7 above.
- Approval flips no flag by itself: `activation_authorized` changes only
  through the explicit activation decision recorded with the record
  (research-dispatch.md:646-648, 797-799).

### D-3 — Real-endpoint preflight set (may be required by the pinned CLI's behavior)

- The pinned Claude Code 2.1.278 was observed issuing exactly one bodyless
  unauthenticated `HEAD /api/hello` preflight before the Messages POST in the
  L7 SYNTHETIC loopback environment; that approval "authorizes nothing at a
  real endpoint" (research-local-agent.md:1439-1465). The relay's request set
  today contains exactly one Messages POST and NO preflight entries
  (src/polymarket_alpha_lab/research_linux_relay.py:1913-1914 defaults;
  qualification constants tests/test_research_claude_relay_native.py:83-89).
- If the CLI repeats the preflight at the real origin, the call fails closed
  by design (a deliberate blocker, not a gap to patch). The L8-D order is:
  demonstrate the exact preflight through the contained path with a fake
  service and dummy credentials first, then a reviewed decision approves
  exactly that set into `preflight_set` (research-local-agent.md:1447-1465).
- **Asked here:** nothing yet — D-3 is SCHEDULED, not requested: it becomes a
  concrete request only after T8's fake-service qualification shows whether
  the preflight occurs on the qualification path, and (post-activation
  decision) at the real endpoint. Recorded so the decision list is complete.

### D-4 — Credential-supply procedure approval and execution window

- The procedure is designed (research-local-agent.md:1513-1551) and its
  supplier machinery is proven (§54 native composition); approval to EXECUTE
  it (typed once per key through a private local channel on the dedicated
  principal) is owner-gated and preconditioned on D-1. Requested together
  with D-2 at activation time, not now.

### Cross-reference (owned elsewhere, not re-requested here)

- **Release-tuple / host gap** (Ubuntu 26.04.1 / Python 3.12.14 pinned by
  §61:2287-2288; the only such host, 166, is retired §68:2975-2980; 154 runs
  24.04.1 / CPython 3.12.3 as a recorded deviation §68:2981-2983): this is
  node N3's decision request and the G6 final-build question, NOT an
  activation prerequisite. The draft record pins the interpreter ACTUALLY
  USED at run time (measured, PENDING) and notes the deviation; it does not
  re-pin the tuple.
- The N2 native-evidence re-establishment and N4 relay-surface audit are
  engineering nodes feeding row 1's evidence freshness; they do not gate the
  decision requests above but their outcomes may refresh the citations.

---

## 3. Draft activation record (L8-D template fill — DRAFT ONLY)

Template source: [research-dispatch.md](../research-dispatch.md) lines
655-749. The template's own rule governs (lines 646-653): filling does NOT
flip any activation flag; the template is a review schema recorded through
the documentation/PR path; fields without evidence references stay
placeholders. Authority translation per §66/plan F5 is applied to
`deciding_authority` and `sign_off` (original template wording "Codex
consultation" retained in brackets for traceability). No credential material
appears anywhere in this fill; no claim is made that T8 ran, that activation
occurred, or that any real provider call was made.

```text
activation_record_id : DRAFT-PAL-AR-2026-10-09-A   (draft suffix until pinned)
created_utc          : 2026-10-09 (draft authoring; re-stamped at pinning)
status               : blocked
                      (blocked on D-1 -> T8 -> D-2; nothing below is effective)
deciding_authority   : NATIVE-SUBAGENT ARBITRATION per DELIVERY_PLAN.md 66
                      (fresh, read-only subagent, explicit VERDICT line,
                      Project Iron Rule 4 independence), with owner
                      confirmation for owner-gated items (Article 0;
                      DELIVERY_PLAN.md 6:155-156).
                      [Template original: "Codex consultation" — superseded
                      by the 2026-10-07 owner instruction recorded in 66;
                      63's standing delegation survives as history only.]
valid_window_utc     : PENDING (D-2; must cover the whole intended run)

baseline_pins
  repository         : https://github.com/Lordakee/polymarket-alpha-lab
  commit_sha         : 67cad027969f34bc21dfad64bb4fcb1b7e72b2d9e  (draft pin:
                      the L9 node final-review record commit; RE-PINNED to
                      the exact tree the approved run executes on — D-2)
  tree_sha           : 3cdb1e846c26b706b778970e0c5dbb1f8640a95f (worktree
                      clean at recording; same re-pin rule)
  branch             : main

runtime_isolation
  host_id            : PENDING-DECISION D-1 — candidate ubuntu@154.89.153.24
                      (Ubuntu 24.04.1, kernel 6.8, 16 cores, 31 GiB; recorded
                      SHARED machine, DELIVERY_PLAN.md 68:2975-2981)
  host_trust_doc     : PENDING-DECISION D-1 (no documented host-trust
                      reference exists; the owner attestation or arbitration
                      ruling IS this field's content)
  principal          : PENDING-DECISION D-1 — a dedicated non-shared
                      principal does not exist today; the current principal
                      is the shared ubuntu account, which the template
                      forbids for credential supply (research-dispatch.md
                      :673-674)
  attestation        : PENDING-DECISION D-1 — facts on record: /home holds
                      only the ubuntu principal; all tmux sessions belong to
                      it (owner-operated); no other human users; sudo
                      passwordless (DELIVERY_PLAN.md 68:3025-3027 and the
                      section-68 host-facts addendum; the tmux/sudo facts
                      first surfaced in the post-l9 plan Revision 1 F1).
                      Verifier,
                      method and date are supplied BY the D-1 decision, not
                      by this draft.

engineering_prerequisites   (each field cites its evidence; all mandatory)
  cleanup_corrections       : LANDED — L8-A commit 111420db (cleanup-success
                              suppression + exact contained banner), review
                              VERDICT: PASS (DELIVERY_PLAN.md 66:2818-2821);
                              semantics extended by the L9.1 reap/drain fixes
                              d3eec34f (R-W14 FAIL -> supplemental PASS,
                              68:3002-3016) and exercised natively in the
                              65-block (322 passed/1 skipped, 68:3018-3020).
  relay_design_gate         : LANDED — L8-D design package commit 35478f53,
                              design gate VERDICT: PASS (DELIVERY_PLAN.md
                              66:2819-2820); design text: research-dispatch
                              .md 634-799 + research-local-agent.md 1256-1564.
  relay_implementation      : LANDED — W1 e337ccea (R-W1 PASS), W5 db44df7c
                              (PASS), W6/W6b 91168a31 (R-W6 FAIL -> R-W6b
                              PASS), W2 ad07d3be (R-W2 PASS, zero findings),
                              W3 11e53cc2 (R-W3 PASS; arbitration C1-C7
                              68:2950-2973), L9.1 d3eec34f; node final
                              review PASS 67cad027 (68:3030-3042).
  contained_qualification   : PENDING-DECISION D-1 (T8 NOT EXECUTED) — gate
                              file landed and reviewed (27d78ca7, PASS);
                              execution procedure: runbook Step A; expected
                              evidence shape: 1 passed + the
                              CLAUDE_RELAY_QUALIFICATION JSON line with
                              activation_authorized false (tests/
                              test_research_claude_relay_native.py:752-764).
  reply_composition         : LANDED — L8-B commit 3acdf5cc (review PASS,
                              DELIVERY_PLAN.md 66:2818-2821); native closure
                              on the final tree inside the 65-block (68:
                              3018-3020), fixture re-verify instruction in
                              the runbook (W15 relayed copy is non-evidence).
  recovery_evidence         : LANDED — L8-C commit e88a0c13 (review PASS,
                              DELIVERY_PLAN.md 66:2818-2821); native closure
                              with both mandated proof lines ("native driver
                              loss: PASS", "native useful recovery: PASS")
                              in the 65-block on the final tree (68:3018-
                              3020; proof lines at tests/test_project_
                              postgres_uncapped_audit_native.py:1385,1784).

pins
  vendor_image       : LANDED IDENTITY — Claude Code 2.1.278, sha256
                       5c4735937844e84f8a93306e841a5b0e12252909b07870f789b19
                       0468da147ab, 234,119,480 bytes (DELIVERY_PLAN.md
                       63:2719-2721; signature chain verified 63:2502-2506).
                       On-host path: MEASURED AT RUN (re-verify the digest
                       before use; the W15-relayed on-154 copy is
                       non-evidence by plan F3).
  wrapper            : bubblewrap 0.11.1 built from the official tarball
                       sha256 c1b7455a1283b1295879a46d5f001dfd088c0bb0f238ab
                       b5e128b3583a246f71 (DELIVERY_PLAN.md 68:2984-2985,
                       non-setuid asserted). Wrapper-binary sha256/size:
                       MEASURED AT RUN on the exact host (T1 discipline).
  helper             : OFFLINE_HELPER_SHA256 22a396e384be6f597e33009f7bde23f4
                       9838de010ac74d6a73f3e95b58302b286 (L9.1 re-pin,
                       DELIVERY_PLAN.md 68:3010-3011); protocol
                       research-linux-helper-v1 (RELAY_HELPER_SOURCE header,
                       src/polymarket_alpha_lab/research_linux_relay.py
                       :1041). The relay-helper digest is recomputed by the
                       gate file at admission (tests/test_research_linux_
                       relay_helper_gates.py) — MEASURED VALUE RECORDED AT
                       PINNING.
  interpreter        : the venv interpreter actually used on the runtime
                       host — MEASURED AT PINNING (sha256 + size). On 154 the
                       recorded interpreter is system CPython 3.12.3, a
                       recorded deviation from the 3.12.14 release tuple
                       (DELIVERY_PLAN.md 68:2981-2983); closure provenance of
                       system interpreters established by W10 (fe13da54). The
                       tuple question itself belongs to node N3 / G6, not to
                       this record.
  runtime_closure    : per-file guest path + sha256 + size — MEASURED AT RUN
                       by the existing discover_runtime_closure launch path
                       (recipe: tests/test_research_process_linux.py
                       :2395-2408); no static value exists or is invented.
  relay              : engine peer = ENGINE_SOURCE (src/polymarket_alpha_lab/
                       research_linux_relay.py:102; digest recomputed and
                       sealed at admission per W3), protocol
                       research-linux-relay-v1 (research_linux_relay.py:40);
                       inner peer = RELAY_HELPER_SOURCE (research_linux_
                       relay.py:1041; digest recomputed by the gates).
  trust_configuration: PENDING-DECISION D-2 (approval-time artifact) —
                       defaults LANDED and typed: origin hostname
                       api.anthropic.com (DEFAULT_ORIGIN_HOSTNAME,
                       research_linux_relay.py:41), scheme https, port 443,
                       TLS floor tls12 (research_linux_relay.py:42-44),
                       permitted-address rule public-global-unicast-only
                       (research_linux_relay.py:1901). The CA bundle is a
                       REAL root set to be selected, pinned (sha256 + size,
                       RelayCaBundlePin, research_linux_relay.py:1875-1887)
                       and REVIEWED at approval; no ambient system roots.
  profile            : schema v3 (_relay_v3_digest; W5 db44df7c), profile
                       digest computed over the serialized launch policy
                       including the trust configuration — MEASURED AT
                       PINNING for the real trust config (the landed v3
                       goldens c29b8353…/8f06ef6d… at DELIVERY_PLAN.md
                       68:3010-3011 bind the synthetic trust, not a real
                       one). contract_sha256: from the constructed profile.

provider_and_model
  provider           : Anthropic Messages via the pinned Claude Code CLI
                       (2.1.278; version banner constant CLAUDE_VERSION,
                       src/polymarket_alpha_lab/research_claude_exec.py:23)
  model_id / effort / cli_version : model_id claude-opus-5 (MODEL_ID,
                       src/polymarket_alpha_lab/research_claude_profile.py
                       :27) / effort NOT CARRIED by the profile surface
                       (PENDING: state the exact CLI invocation values at
                       pinning) / cli_version 2.1.278.

reviewed_requests
  rotation/batch/turn IDs : PENDING (D-2 window; assembled per runbook
                       Steps E-F; no real reviewed BTC/ETH requests exist
                       today — real predictions exist only after activation,
                       plan 2/WP-04 row)
  request_roster     : 1..2 exact (record_id, content_sha256) pairs — the
                       reviewed two single-request batches (one per team);
                       template's 1..100 roster applies to the general
                       schema, the reviewed first-run shape is one request
                       per team (src/polymarket_alpha_lab/research_claude_
                       operator.py:131-133)
  authorization      : authorization_id + adapter_contract_sha256 (= profile
                       contract_sha256) + approved_utc + expires_utc —
                       created by the existing typed authorization path at
                       run time (recipe: tests/test_project_postgres_
                       uncapped_native.py:34-41; binding enforced by the
                       operator's canonical-input check, research_claude_
                       operator.py:143-149)
  input_review       : PENDING — reference to the WP-01-reviewed BTC/ETH
                       inputs assembled at run time (runbook Step E)

finite_limits
  dispatch           : max_tasks=2, max_workers=2 (the reviewed first-run
                       configuration; 1..2 are the only admitted values,
                       src/polymarket_alpha_lab/research_claude_operator.py
                       :156-159); one rotation, one turn (turn-one; later
                       turns only via the explicit new-turn path)
  supplier_slots     : per-team 1 (one key per team; FiniteInMemoryApiKey
                       Supplier, src/polymarket_alpha_lab/research_claude_
                       profile.py:248; construction requires the stop token
                       by identity; slots consumed permanently)
  process            : timeout_ms / cleanup_timeout_ms / stdin-stdout-
                       stderr caps / memory-pids-scratch caps — set on the
                       launch at assembly (recipe values in tests/test_
                       research_process_linux.py:2400-2429; the real values
                       are recorded at pinning)
  relay              : LANDED DEFAULTS — max request 16,000,000 B; response
                       32 MiB in 4,096-B reads; connect 10,000 ms; handshake
                       10,000 ms; idle 30,000 ms; total = remaining spec
                       budget (research-linux-relay constants,
                       src/polymarket_alpha_lab/research_linux_relay.py
                       :54-60; design table research-local-agent.md
                       :1369-1377)
  stop               : stop token identity binding — the SAME ResearchDis
                       patchStop object supplied to the supplier
                       construction and the rotation (admission guard,
                       src/polymarket_alpha_lab/research_claude_operator.py
                       :112-115; 54-native identity assertions,
                       tests/test_project_postgres_uncapped_audit_native.py
                       :467-476)

scoped_pg_writes
  project_root       : the project-private root on the runtime host (D-1/
                       D-2); every DSN through the single audited
                       validate_local_postgres_dsn gate only (Project Iron
                       Rule 1)
  permitted_classes  : uncapped authorization row + receipt, call-start
                       rows, outcome rows, batch/turn reservation rows (the
                       existing durable uncapped/dispatch paths; 53:1622-
                       1629; relay adds zero database surface,
                       research-local-agent.md:1498-1511)
  prohibition        : no other writes; no new migrations unless separately
                       reviewed; disposable per-test clusters for any gate
                       runs (W13 boundary); no business-DB mutation

preflight_set        : EMPTY (deliberate blocker; design position
                       research-local-agent.md:1439-1465). The synthetic-
                       loopback HEAD /api/hello approval (63:2658-2688)
                       authorizes nothing at a real endpoint. Any real-
                       endpoint preflight entry requires the L8-D order
                       (demonstrate -> reviewed decision D-3 -> enforcement)
                       before it may appear here.

credential_supply
  channel            : PENDING-DECISION D-1 + D-4 — private local channel on
                       the dedicated principal (interactive local terminal
                       prompt or an explicitly reviewed local entry helper;
                       never chat/Git/repo files/ambient env/argv/stored-
                       secret discovery/logs), research-local-agent.md
                       :1525-1534. This draft contains no channel mechanics
                       beyond that boundary (plan N1 acceptance).
  slots_supplied     : 1 per team (crypto_btc, crypto_eth)
  attestation        : no chat/Git/env/argv/file/log/stored-secret use; no
                       secure-erasure claim (research-local-agent.md
                       :1536-1546)

identity_and_usage
  expected_identity  : the pinned CLI's version banner "2.1.278 (Claude
                       Code)" through the contained version phase
                       (CLAUDE_VERSION, research_claude_exec.py:23; L8-B
                       corrected-banner round trip, 68:3018-3020) and the
                       provider's served identity/usage as reported in the
                       admitted response envelope
  check_method       : the existing durable uncapped audit (call-start/
                       outcome rows + reply fingerprints, 54-native per-
                       record reconciliation) plus decoder admission;
                       identity mismatch stops further admission
  unknown_billing    : remains unknown; never recorded as zero (65:2796-/
                       61:2301 cap-honesty rule)

evidence
  commands_results   : to be the exact commands, outputs, first failures,
                       retries, skipped and unexecuted steps of the approved
                       run (runbook 2/G). Already-pinned baseline evidence:
                       68:3017-3042 (T1 re-run, 65-block, verify_local
                       --full log path ~/pal-artifacts/l91-landing.log, CI
                       37955091414, node final review).

sign_off             : PENDING — operator reference + NATIVE-SUBAGENT
                       ARBITRATION approval reference per 66 [template
                       original: "Codex approval"; superseded as above].
                       No sign-off exists at draft time.
```

Draft-status honesty notes on the fill:

1. Every `MEASURED AT RUN/PINNING` field is a placeholder in the template's
   sense (research-dispatch.md:652-653): it names the mechanism that will
   produce the value, and invents no value.
2. Every `PENDING-DECISION` field names its owning gate (D-1/D-2/D-3/D-4)
   per plan N1's deliverable definition.
3. Nothing in the fill asserts T8 execution, activation, provider calls, or
   credential existence.
4. The W15-relayed on-154 facts (T8 image copy, PG18 prefix, L8-B fixture)
   appear only as re-verify instructions, never as pins (plan F3).

---

## 4. What this pack does NOT claim (honesty section)

- T8 has NOT run; the L9 node is closed *pending T8/D-1* (§68:3042), and no
  engineering pass can authorize activation (the T8 gate file's own header,
  tests/test_research_claude_relay_native.py:1-10).
- No activation has occurred; `activation_authorized=false` everywhere; real
  provider calls false (§65:2791-2792, §68:3027-3028).
- No host-trust document, dedicated principal, CA bundle, reviewed real
  input, or credential exists for a real run today.
- G2 remains PARTIAL (real-research half open); G3/G4/G5 open; G6 PARTIAL;
  V1 1/6 (§4:78, l8-l9-status.md §6).
- This pack adds no new gate, framework, layer or acceptance criterion; it
  converts landed evidence into a decision package (plan §3 N1).

## 5. Labeled self-review (N1 implementer)

Performed against the plan N1 charter and dispatch constraints:

- Scope: only this file and the companion runbook draft created; no src/,
  tests/, workflow, migration or ledger changes; not committed (coordinator
  gates/commits).
- Prerequisite fidelity: all seven §65 fragments walked; landed citations
  checked against DELIVERY_PLAN.md sections 61-68 and repository files at
  67cad027; T8 and every owner-gated item marked PENDING-DECISION with the
  owning gate named; D-1 not resolved or preconditioned (facts only, from
  §68's own record).
- Template fidelity: the fill keeps the template's field order and names;
  filling/flipping rules preserved; the "Codex consultation"/"Codex
  approval" wording translated to the §66 native-arbitration regime with the
  original retained for traceability (plan F5).
- Credential discipline: zero credential material; the credential_supply
  fields carry only the designed boundary text.
- Non-evidence discipline: W12/W15 facts used only as re-verify pointers;
  all pins anchored in ledger sections or repo files (F3).
- Known limits: (a) the draft's `commit_sha` pin will drift if the tree
  moves before D-2 — re-pin at submission (stated in the fill); (b) the
  `effort` value is not carried by any landed profile surface and is left
  PENDING rather than guessed; (c) the request_roster field restates the
  template's 1..100 general schema against the reviewed two-request
  first-run shape — flagged inline, not silently narrowed.

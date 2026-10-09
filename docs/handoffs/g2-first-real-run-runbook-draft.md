# First scoped real-run operator runbook — DRAFT (operative only after owner authorization)

Worker N1 of the post-L9 cycle (§66 all-native-subagent flow), 2026-10-09.
Companion decision package: [g2-activation-readiness.md](g2-activation-readiness.md)
(the §65 prerequisite mapping, the DRAFT activation record, and decision
requests D-1..D-4).

**Status: DRAFT. This runbook is NOT operative.** Nothing in it may be
executed against a real provider endpoint, a real credential, or a live
project database until the owner explicitly authorizes the scoped real run
(decision chain in Step 0). Until then `activation_authorized=false`, real
provider calls remain false, and every step below is a described shape, not
a command to run now. Phase 1 boundaries are absolute: paper-only /
report-only / readonly; no live trading, no account or private-key handling,
no order paths; PostgreSQL-only persistence through the single audited
`validate_local_postgres_dsn` gate (Project Iron Rule 1).

**Credential boundary (plan N1 acceptance):** this runbook contains zero
credential material and stops at the reviewed supply procedure's boundary —
it names WHERE the operator's private local channel sits and what the
supplier contract requires, and nothing more. No key value, no channel
implementation, no discovery.

Evidence discipline (plan Revision 1 F3): every command shape below is
derived from LANDED DELIVERY_PLAN.md sections and repository files at
`67cad027969f34bc21dfad64bb4fcb1b7e72b2d9e` (tree
`3cdb1e846c26b706b778970e0c5dbb1f8640a95f`), with file:line provenance in
§9. W12/W15 environment facts (the on-154 T8 image copy, the 154 PG18
prefix, the transferred L8-B fixture) are re-verify instructions only — no
step's correctness rests on them.

---

## 0. Authorization preconditions (the gate order — each step's entry ticket)

This runbook becomes operative only when ALL of the following hold, in
order. Steps A and B are pre-activation engineering/approval steps; Steps
C-G are the real-run arc itself.

| Order | Gate | Owning decision / evidence | Blocks |
|---|---|---|---|
| 0.1 | D-1 resolved (154 dedicated/non-shared attestation, or an alternative qualified host named) | Owner attestation or §66 arbitration ruling; facts on record in DELIVERY_PLAN.md §68:3025-3027 | Step A (T8), and all of Steps C-G |
| 0.2 | Step A executed: T8 qualification PASS on the final tree | §65 prerequisite 3 (DELIVERY_PLAN.md:2794); expected evidence shape in §2 below | Step B |
| 0.3 | D-2: activation record PINNED and approved (status flips `blocked` → `approved-not-yet-effective` → `effective` only via the explicit decision) | Native-subagent arbitration (fresh, read-only, VERDICT line) + owner confirmation; template rule: approval flips no flag by itself (research-dispatch.md:646-648, 797-799) | Steps C-G |
| 0.4 | D-4: credential-supply procedure approved with an execution window inside the record's `valid_window_utc` | research-local-agent.md:1513-1551 is the designed procedure; approval is owner-gated and preconditioned on D-1 | Step F |
| 0.5 | CI "Offline verification" green at the pinned commit; no unresolved release-blocking review finding | §62/§68 conventions (latest green: run 37955091414 at d3eec34f, §68:3021) | Steps C-G |

No-rerun rule (§5:131-132): do NOT re-run checks that already
passed unaffected — the L9.1 verification chain (binding T1 re-run 12/12,
§65 five-file native block 322/1, `verify_local --full` PASS, CI green;
§68:3017-3023) stands as pinned evidence for tree d3eec34f. Re-run any of
them only if the tree moves past the pinned commit (then re-pin the record)
or if a change touches the affected surface.

## 1. Stop conditions and global boundaries

- STOP on any first failure: capture the full first output separately,
  preserve it, and route to a fresh read-only review — never rerun-to-green
  silently (§68 conventions; l7-l8-status.md evidence rules).
- STOP if the host, bwrap provenance, interpreter or image digest diverges
  from the record pins (the T1 C4 divergence discipline, §68:2989-2991).
- STOP if any D- decision is partially satisfied or verbal: decisions must
  be recorded artifacts, not implications (§6:155-156).
- Replay discipline: the same task replayed returns the original result and
  never appends provider calls (§65:2798-2799 via §61:2300-2301; §53:1626).
  No automatic retry, no identity substitution, no Codex fallback
  (§53:1624-1625).
- Unknown billing stays unknown; never recorded as zero and never faked as
  a cap (§61:2301; §5 WP-02 stop conditions).
- Disposable per-test/qualification PG clusters only; the real project
  cluster is touched only by the parent-side managed session in Step F.

## 2. Step A — T8 qualification (§65 prerequisite 3; BLOCKED pending D-1)

T8 has NOT run (§68:3024-3042; nothing claims otherwise). It is the L9
node's only remaining gate and the §65 "official-image qualification through
actual L5 wiring" prerequisite. It uses a FAKE Messages TLS service and a
DUMMY synthetic key — it authorizes nothing (gate file header,
tests/test_research_claude_relay_native.py:1-21).

Preconditions: D-1 resolved (0.1); the D-1 attestation is what licenses
setting `POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_ISOLATED_HOST=1` — that flag is
one of the five mandatory probe variables (tests/claude_cli_probe.py:
125-126) and its value `1` is validated as part of the image opt-in
(tests/claude_cli_probe.py:146-157); setting it on a non-dedicated host
would be a false attestation — forbidden (W13 STOP rule, restated by plan
Revision 1 F1).

Command shape (verified against the gate file at 67cad027; env names at
tests/test_research_claude_relay_native.py:61-64; every missing
prerequisite after the relay opt-in is a FAILURE, never a skip —
test_research_claude_relay_native.py:106-163):

```bash
cd <repo-on-runtime-host>            # the D-1-qualified host
set -euo pipefail
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONUTF8=1
# Re-verify the image first: find the 234,119,480-byte file and confirm
# sha256 5c4735937844e84f8a93306e841a5b0e12252909b07870f789b190468da147ab
# (identity anchored at DELIVERY_PLAN.md 63:2719-2721; the on-host copy is
# re-measured here, not trusted).
IMG=<measured image path>
export POLYMARKET_ALPHA_LAB_CLAUDE_RELAY_QUALIFICATION=1
export POLYMARKET_ALPHA_LAB_RUN_LINUX_CONTAINMENT=1
export POLYMARKET_ALPHA_LAB_NATIVE_PG_PREFIX="${PG18_PREFIX:?measured prefix}"
export POLYMARKET_ALPHA_LAB_LINUX_CGROUP_ROOT="${CGROUP_ROOT:?delegated subtree with memory+pids}"
export POLYMARKET_ALPHA_LAB_CLAUDE_PROBE=1
export POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_IMAGE="$IMG"
export POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_SHA256=5c4735937844e84f8a93306e841a5b0e12252909b07870f789b190468da147ab
export POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_BYTES=234119480
export POLYMARKET_ALPHA_LAB_CLAUDE_PROBE_ISOLATED_HOST=1   # = the D-1 attestation
.venv/bin/python -u -m pytest -q --tb=short -rA -s \
  tests/test_research_claude_relay_native.py::test_supplied_claude_relay_qualification_native
```

Expected outcome (from the gate file, not from any executed run):
`1 passed` plus the stdout line `CLAUDE_RELAY_QUALIFICATION {...}` with
`activation_authorized: false` inside (tests/test_research_claude_relay_
native.py:752-764). The two closed outcomes are success-with-NON-derived-
relay-evidence (the gate asserts evidence.get('derived') is False) or the
closed preflight blocker; both are honest results. The JSON
line and counts go into the activation record's
`engineering_prerequisites.contained_qualification` field (readiness pack
§3), and — if the qualification shows the CLI issuing a real-endpoint-shaped
preflight — decision D-3 is scheduled with that evidence (readiness pack §2).

## 3. Step B — pin the activation record (D-2)

With T8 evidence in hand: re-measure every `MEASURED AT PINNING` field of
the draft record (readiness pack §3) on the exact host and tree of the
intended run; set `valid_window_utc` to cover the whole run; submit the
completed record through the §66 native-subagent arbitration (fresh,
read-only, VERDICT line) with owner confirmation. The record's
`status` stays `blocked` until the explicit approval decision, and approval
alone still does not flip `activation_authorized` — the effective-activation
decision is recorded with the record (research-dispatch.md:788-799). Only a
record with `status: effective` (or `approved-not-yet-effective` inside its
window, per the deciding authority's wording) opens Step C.

## 4. Step C — runtime host assembly and re-verification (execution conveniences re-measured, not trusted)

On the D-1-qualified host (candidate: ubuntu@154.89.153.24 — Ubuntu 24.04.1,
kernel 6.8, 16 cores, 31 GiB, §68:2975-2981):

1. Repo pinned to the record's `commit_sha`, clean worktree, ff-only sync
   (W13 Step 0.2 idiom):
   ```bash
   git -C <repo> fetch origin && git -C <repo> status --short --branch
   git -C <repo> checkout main && git -C <repo> merge --ff-only origin/main
   git -C <repo> rev-parse HEAD   # must equal the pinned commit_sha
   ```
2. Venv interpreter check (verify_local.py refuses non-venv interpreters,
   scripts/verify_local.py:131-134): `.venv/bin/python --version` — the
   version found is the one pinned in the record (on 154 the recorded value
   is system CPython 3.12.3, a recorded deviation from the release tuple;
   §68:2981-2983. The tuple itself is node N3's / G6's question, not this
   run's).
3. bwrap provenance: `command -v bwrap && bwrap --version` — expect exactly
   `bubblewrap 0.11.1`; provenance against the official tarball sha256
   `c1b7455a1283b1295879a46d5f001dfd088c0bb0f238abb5e128b3583a246f71`
   (§68:2984-2985). Record the binary's own sha256 for the record's
   `wrapper` pin.
4. PG18 runtime prefix discovery (runtime gate accepts a prefix whose
   `bin/{postgres,initdb,pg_ctl,psql,pg_controldata}` report one supported
   major 16/17/18 and which has `share/postgres.bki`,
   src/polymarket_alpha_lab/project_postgres/runtime.py): discover and
   measure; PG18 for fidelity (the W15-relayed 154 prefix is a pointer, not
   evidence — re-verify).
5. Delegated cgroup v2 subtree: a root carrying `cgroup.controllers` with
   `memory` and `pids`, fresh per run (W13 Step 0.6 idiom); the trusted
   parent must already sit inside the delegated subtree (§68 production
   insight, 68:2943-2945).
6. Disk headroom (§62-scale suites needed a few GiB; the real run itself is
   minutes-scale).

## 5. Step D — trust configuration and profile assembly (Python-level; the reviewed recipe)

This is the typed assembly proven by the §54 native composition
(tests/test_project_postgres_uncapped_audit_native.py:347-465) and the W3
relay-launch recipe (tests/test_research_process_linux.py:2380-2430),
composed for the real trust configuration. It runs on the runtime host
inside the operator's assembly script (NOT a new CLI — §53's fixed
three-file scope discipline; the composition point stays
`run_claude_research_rotation`).

1. **Trust configuration** (all values reviewed into the record at Step B;
   nothing discovered at run time — RelayTrustConfig construction is inert
   and declaration-only, src/polymarket_alpha_lab/research_linux_relay.py:
   1890-1914):
   - CA bundle: the reviewed real root set, pinned by absolute path +
     sha256 + exact byte size (`RelayCaBundlePin`, research_linux_relay.py:
     1875-1887; size cap 1 MiB, research_linux_relay.py:66).
   - Defaults landed unless the record says otherwise: hostname
     `api.anthropic.com` (research_linux_relay.py:41), scheme https, port
     443, TLS floor tls12, permitted-address rule
     `public-global-unicast-only`, the byte/time limits of
     research_linux_relay.py:57-69, request set = exactly one Messages
     POST, `preflight_entries=()` (empty by the deliberate blocker,
     research-local-agent.md:1439-1465).
2. **Launch spec** (`LinuxLaunchSpec` with `egress_policy=EGRESS_RELAY` =
   `'relay-fixed-origin'` and `relay_trust=<the config above>`; the closed
   two-value egress branch and the typed-trust requirement are enforced at
   admission — src/polymarket_alpha_lab/research_process_linux.py:74-91,
   src/polymarket_alpha_lab/research_claude_operator.py:104-111). Measured
   inputs per the W3 recipe (tests/test_research_process_linux.py:
   2400-2419): wrapper pin (path/sha256/size), helper digest, interpreter
   pin, `discover_runtime_closure` output, vendor guest path, expected
   version output `2.1.278 (Claude Code)\n` (CLAUDE_VERSION,
   research_claude_exec.py:23), fresh delegated cgroup root, memory/pids/
   scratch caps from the record.
3. **Process spec + profile** (vendor identity in argv[0] + sha; §62 L5
   semantics, DELIVERY_PLAN.md:2397-2409): `ResearchProcessSpec` with the
   official image as the vendor, the environment allowlist carrying
   `ANTHROPIC_BASE_URL` = the symbolic relay endpoint
   `http://127.0.0.1:0` (RELAY_SYMBOLIC_ENDPOINT,
   research_process_linux.py:91 — substituted with the per-call drawn port
   from the reviewed [20000, 32767] window), bounded timeouts/caps per the
   record; `ClaudeExecProfile(process=spec, linux_launch=launch)` with the
   v3 relay branch selected by the closed egress value.
4. Record the profile's `contract_sha256` and computed v3 digest into the
   record's `profile` field.

## 6. Step E — reviewed input assembly (WP-01 flow; two single-request batches)

1. Real candidate discovery/preview through the existing WP-01 entries
   (e.g. `scripts/discover_crypto_research.py` — "Discover BTC/ETH
   candidates; optionally preview inputs. Never a model or DB run." — and
   the docs under docs/research-crypto-*.md). One candidate per team
   (`crypto_btc`, `crypto_eth`) passing the existing contract/observation
   gates; unsupported rules or already-observed events never start research
   (§5 WP-01 stop conditions).
2. Operator review and approval of the exact request bytes per the existing
   preview flow; the prepared request's `model_id` must equal the profile's
   (binding enforced at assembly, research_claude_operator.py:134-138).
   Proven shape: `preview.request(approved_terms_sha256=…)` (recipe:
   tests/test_project_postgres_dispatch_native.py:37-45).
3. Two immutable single-request `ResearchBatch` objects, one per team, with
   distinct `batch_id`s (research_claude_operator.py:130-133).
4. The typed authorization binding the exact reviewed roster in reviewed
   order and the profile contract (recipe:
   tests/test_project_postgres_uncapped_native.py:34-41; binding enforced
   at research_claude_operator.py:143-149), with the record's
   `valid_window_utc` covering `approved_at`/`expires_at`.

## 7. Step F — session, credential boundary, and the one audited rotation

1. **Session**: the operator owns an already-open project-private research
   session (managed `ProjectPostgres`; every DSN through
   `validate_local_postgres_dsn`; §53's "授权创建及回执核对 → 顺序入库两个
   批次" order — authorization creation and receipt verification FIRST, then
   sequential batch intake).
2. **Credential boundary (D-4)**: the operator types each team's key ONCE
   through the private local channel on the dedicated principal into the
   explicit in-memory slots of `FiniteInMemoryApiKeySupplier` — construction
   requires the rotation stop token by identity; one shared lock covers both
   teams; admission is lock → stop check → permanent consume
   (research-local-agent.md:1525-1534; src/polymarket_alpha_lab/
   research_claude_profile.py:248). One slot per team. The key never enters
   the profile digest, the activation record, audit rows, relay logs, tests
   or handoffs. Delivery to the contained client happens only after the
   durable call-start audit commits and model-phase readiness, via the
   existing one-use anonymous pipe (L5 semantics, §62:2404-2407). **This
   runbook stops here at the boundary; the channel mechanics are the
   reviewed procedure's own text, not repeated here.**
3. **The rotation** — the single composition point (§53:1622-1625):
   ```python
   operator.run_claude_research_rotation(
       session,
       reviewed_batches=(btc_batch, eth_batch),
       profile=profile,                      # Step D output
       authorization=permission,             # Step E output
       api_key_supplier=supplier,            # Step F.2 output
       rotation_id=<recorded id>, turn_id=<recorded id>,
       stop=control,                         # SAME object as supplier binding
       max_tasks=2, max_workers=2,           # the reviewed first-run shape
   )                                         # (research_claude_operator.py:156-159)
   ```
   The same stored authorization object and the same stop token reach the
   factory and the runner (`claude_profile_factory` inert opt-in binding,
   research_claude_profile.py:307-313; §54-native identity assertions,
   tests/test_project_postgres_uncapped_audit_native.py:467-476). No
   `model_budget_id` is passed (uncapped-by-review semantics; §53:1624-1625).
   Stop is cooperative: after any stop, failure or interruption, preserve
   original IDs and inspect durable state; never retry or replace
   identities (research_claude_operator.py:191-196).
4. **Observation duty**: the operator (or an observer wrapper of the §54
   pass-through shape) records the rotation report and per-call evidence
   without altering it; the relay's only evidence is fixed outcome codes
   and byte/counter metadata (research-local-agent.md:1358-1362).

## 8. Step G — evidence capture and G2 real-half acceptance reconciliation

1. Capture: exact commands, outputs, first failures, retries, skipped and
   unexecuted steps — into the activation record's `evidence.commands_
   results` field; preserve originals/incomplete/failures (§61:2300-2301).
2. Reconciliation (the §61 G2 wording): per team, at least one reviewed
   real execution with (a) the authorization/identity/usage rows joinable
   per record (call-start/outcome/reply fingerprints — the §54-native
   per-record audit join), (b) the served identity matching the pinned
   CLI/model, (c) replay proven not to append provider calls, (d) unknown
   billing recorded as unknown.
3. Ledger: the coordinator appends the run record to DELIVERY_PLAN.md per
   the §57 single-writer rule; the G2 real-research half closes only on
   that recorded evidence (§63:2743-2751 keeps only the synthetic-probe
   subcondition closed today).
4. Post-run: a fresh read-only review of the run evidence (Project Iron
   Rule 4) before any G2/G3 statement; the G3 final combination that
   depends on it stays a separate authorized step (§61:2303-2305).

## 9. Command provenance (parse-only validation, §22/§58 precedent)

Per the §22 precedent (guide examples verified against the real parsers
without executing write/network actions), every command shape, environment
variable, test name, API signature and file:line cited above was verified
by READING the landed files at 67cad027 — nothing was executed. Table of
the load-bearing verifications:

| Cited item | Landed source (verified at 67cad027) |
|---|---|
| T8 opt-in env names | tests/test_research_claude_relay_native.py:61-64 |
| T8 fail-closed prerequisite gate | tests/test_research_claude_relay_native.py:106-163 |
| T8 test name + JSON line + activation false | tests/test_research_claude_relay_native.py:752-764 |
| Five mandatory probe vars incl. ISOLATED_HOST=1 | tests/claude_cli_probe.py:125-126, 146-157 |
| T1 env names (referenced for discipline) | tests/test_research_linux_relay_helper_gates.py:80-81 |
| Containment opt-in env | tests/test_research_process_linux.py:35 |
| W3 relay-launch recipe (launch + spec) | tests/test_research_process_linux.py:2380-2430 |
| Symbolic relay endpoint + egress constants | src/polymarket_alpha_lab/research_process_linux.py:74-91 |
| RelayTrustConfig / RelayCaBundlePin fields + caps | src/polymarket_alpha_lab/research_linux_relay.py:41-69, 1875-1914 |
| run_claude_research_rotation signature + 2/2 first-run shape | src/polymarket_alpha_lab/research_claude_operator.py:156-204 |
| Admission guard (typed trust, supplier identity) | src/polymarket_alpha_lab/research_claude_operator.py:83-115 |
| §54 native composition recipe (batches/authorization/supplier/rotation) | tests/test_project_postgres_uncapped_audit_native.py:347-476 |
| authorization() / prepared() recipes | tests/test_project_postgres_uncapped_native.py:34-41; tests/test_project_postgres_dispatch_native.py:37-45 |
| claude_profile_factory inert binding | src/polymarket_alpha_lab/research_claude_profile.py:248, 307-313 |
| CLAUDE_VERSION banner / MODEL_ID | src/polymarket_alpha_lab/research_claude_exec.py:23; research_claude_profile.py:27 |
| verify_local venv refusal + env stripping | scripts/verify_local.py:52-63, 131-134 |
| §65 five-file block files + proof lines (evidence, not re-run) | the five test files; proof lines tests/test_project_postgres_uncapped_audit_native.py:1385, 1784 |
| WP-01 entry scripts | scripts/discover_crypto_research.py (docstring: never a model or DB run); scripts/manage_research_tasks.py |
| Ledger citations | DELIVERY_PLAN.md §53 (1603-1686), §54 (1689+), §61 (2273-2369), §62 (2371-2488), §63 (2490-2751), §65 (2777-2799), §66 (2801-2834), §68 (2876-3042) |

Known non-verifications (honesty): the `<repo-on-runtime-host>`, `<measured
image path>`, `${PG18_PREFIX}` and `${CGROUP_ROOT}` placeholders are
deliberately unbound — they are measured on the runtime host at execution
time per §4; the `effort` value of the CLI invocation is not carried by any
landed profile surface and is left to the record (flagged in the readiness
pack §3); no shell command in this runbook was executed during authoring.

## 10. Labeled self-review (N1 implementer)

- Draft labeling: the header and Step 0 state the operative-only-after-
  authorization status; no step self-authorizes; activation_authorized
  appears only as false.
- Ordering fidelity: the gate chain (D-1 → T8 → D-2 → D-4 → run) matches
  §65's prerequisite list and the plan's sequencing (§4: "the pivotal gate
  is the activation decision"); T8's blocked state is stated before its
  command shape.
- Boundary compliance: no credential material; the supply step stops at the
  reviewed procedure's boundary; Phase 1 paper-only/report-only/readonly
  restated; PostgreSQL-only persistence; no order/execution paths; no new
  layer or CLI introduced (assembly stays inside the existing typed module
  surface).
- Provenance: every command shape traced to landed files (§9 table);
  W12/W15 facts appear only as re-verify pointers; no invented flags,
  digests, counts or URLs.
- No-rerun discipline: Step 0 pins the standing L9.1 evidence instead of
  re-running it; re-runs are conditioned on tree movement or affected
  surfaces.
- Known limits: (a) Step E's discovery/preview sub-steps reference the
  existing WP-01 entries by name and doc rather than enumerating flags —
  enumerating them would exceed verified territory; (b) the observer
  wrapper in Step F.4 is described at the §54 shape level only; (c) if the
  D-1 ruling names a host other than 154, Steps C-D host facts re-measure
  wholesale — the shapes hold.

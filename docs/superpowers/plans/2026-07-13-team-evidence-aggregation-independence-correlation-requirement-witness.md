# Team Evidence Aggregation Independence, Correlation, And Requirement Witness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the pure Node 2B allocation and requirement-witness modules that deterministically apply independence-then-correlation caps in integer micro-units and produce the globally severity-optimal, lexically canonical requirement b-matching.

**Architecture:** `team_evidence_aggregation_allocation.py` consumes only validated Node 2A records and configuration, performs exact largest-remainder apportionment first by independence key and then by correlation key, and returns one canonical allocation row per input record. `team_evidence_aggregation_witness.py` rematerializes that exact allocation, derives a bounded candidate graph, computes the blocked-first/watch-second global b-matching, and force/forbid canonicalizes the optimum edge set. Both modules remain pure, module-local, deterministic standard-library code with no persistence, external I/O, package-root export, or Node 2C dependency.

**Tech Stack:** Python 3.12, frozen/slotted Node 2A dataclasses, exact `Decimal`, integer micro-unit arithmetic, deterministic standard-library max flow, pytest, AST scope gates, CodeGraph, and local Claude Code `claude-opus-4-8` at effort `max`.

## Global Constraints

- This plan implements only Node 2B from `docs/superpowers/specs/2026-07-13-team-evidence-aggregation-core-design.md`; the approved design is normative and must not be reinterpreted.
- Start only from a clean `HEAD` equal to fetched `origin/main`, after validating the immutable Node 2A prerequisite commit and its content-addressed PASS receipt exactly as specified below.
- Production remains `paper_only=True`, `report_only=True`, and `readonly=True`; every emitted Node 2A-derived dataclass retains and validates all three exact hard flags.
- The child is pure over explicit immutable values. It performs no database access, project-data persistence, filesystem I/O, network I/O, CLI parsing, environment access, process execution, logging, ambient clock reads, or randomness.
- Any future persistence of data derived from this child is local Supabase/Postgres only. Every raw DSN must pass through `validate_local_postgres_dsn` before any connection, psycopg wrapper, persistence adapter, or store is constructed. This child imports neither that validator nor any persistence surface because it performs no persistence.
- No live trading, authentication, account, credential, private-key, wallet, signing, order, sizing, allocation-to-capital, execution, or exchange-mutation surface is permitted.
- Every probability, requested weight, allocation, cap, and threshold is canonical fixed-six exact-base `Decimal`; no public or private arithmetic path accepts or creates `float`.
- Every Decimal operation uses a local `Context(prec=64, rounding=ROUND_HALF_EVEN)`. Production never reads or mutates `decimal.getcontext()`.
- Allocation uses exact nonnegative integer micro-units. It never independently rounds rows with HALF_EVEN, applies per-row `min()`, reverses or merges stages, or substitutes a simultaneous optimizer.
- Witnesses consume only the one canonical allocation. They never search for a different cap-feasible vector and never use a per-requirement greedy assignment.
- There is no package-root export, Node 2C import, run identity, replay identity, complete evaluation-scope provenance, `tea:v1`, `tfr:v1`, `tfe:v1`, legacy projection, packet construction, DB row, CLI, network client, or persistence adapter in this child.
- No production dependency is added. Do not modify `pyproject.toml` or `src/polymarket_alpha_lab/__init__.py`.
- Fast mode is forbidden for implementation and review. Claude review is read-only with model `claude-opus-4-8`, effort `max`, `--safe-mode`, tools limited to `Read,Glob,Grep`, permission mode `dontAsk`, and no session persistence.

## Exact Sorted Implementation Allowlist

Only these four paths may be created or changed by the implementation node, in this exact sorted order:

```text
src/polymarket_alpha_lab/team_evidence_aggregation_allocation.py
src/polymarket_alpha_lab/team_evidence_aggregation_witness.py
tests/test_team_evidence_aggregation_allocation.py
tests/test_team_evidence_aggregation_witness.py
```

Use this immutable shell array throughout the node:

```bash
IMPLEMENTATION_ALLOWLIST=(
  src/polymarket_alpha_lab/team_evidence_aggregation_allocation.py
  src/polymarket_alpha_lab/team_evidence_aggregation_witness.py
  tests/test_team_evidence_aggregation_allocation.py
  tests/test_team_evidence_aggregation_witness.py
)
test "$(printf '%s\n' "${IMPLEMENTATION_ALLOWLIST[@]}")" = $'src/polymarket_alpha_lab/team_evidence_aggregation_allocation.py\nsrc/polymarket_alpha_lab/team_evidence_aggregation_witness.py\ntests/test_team_evidence_aggregation_allocation.py\ntests/test_team_evidence_aggregation_witness.py'
```

No broad `git add .`, `git add src`, or `git add tests` is allowed. The plan document is a reviewed planning artifact and is not part of the later implementation range.

## Immutable Base And Node 2A Handoff

The coordinator must export all three runtime handoff values before implementation:

```bash
export NODE2A_PREREQ_SHA
export NODE2A_PASS_RECEIPT_PATH
export NODE2A_PASS_RECEIPT_SHA256
```

`NODE2A_PREREQ_SHA` is the exact reviewed and pushed Node 2A commit. `NODE2A_PASS_RECEIPT_PATH` names a regular, non-symlink JSON receipt outside the repository. `NODE2A_PASS_RECEIPT_SHA256` is the exact lowercase SHA-256 of that immutable receipt. The receipt has exactly this closed JSON shape, with no additional keys:

```json
{
  "node": "team-evidence-aggregation-contracts-codec-temporal-eligibility",
  "head_sha": "$NODE2A_PREREQ_SHA",
  "review_model": "claude-opus-4-8",
  "review_effort": "max",
  "review_exit_status": 0,
  "review_final_nonblank_line": "VERDICT: PASS",
  "focused_tests": "pass",
  "full_pytest": "pass",
  "compileall": "pass",
  "codegraph_sync": "pass",
  "static_gates": "pass",
  "clean_worktree": "pass",
  "pushed_remote_main_sha": "$NODE2A_PREREQ_SHA"
}
```

The two `$NODE2A_PREREQ_SHA` strings above mean the exact runtime value, not literal dollar-prefixed text. Run this preflight in one shell and retain the exported readonly values and readonly receipt-validator function for every later command. The function is the only permitted receipt-validation path; do not precede or replace it with path-based `test`, `realpath`, `sha256sum`, `Path.read_text`, or a second JSON parser:

```bash
set -euo pipefail
test -n "${TMUX:-}"
: "${NODE2A_PREREQ_SHA:?NODE2A_PREREQ_SHA is required}"
: "${NODE2A_PASS_RECEIPT_PATH:?NODE2A_PASS_RECEIPT_PATH is required}"
: "${NODE2A_PASS_RECEIPT_SHA256:?NODE2A_PASS_RECEIPT_SHA256 is required}"

REPO_ROOT="$(git rev-parse --show-toplevel)"
export REPO_ROOT NODE2A_PREREQ_SHA NODE2A_PASS_RECEIPT_PATH NODE2A_PASS_RECEIPT_SHA256

validate_node2a_pass_receipt() {
  .venv/bin/python - <<'PY'
import hashlib
import json
import os
import re
import stat


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


receipt_path = os.environ["NODE2A_PASS_RECEIPT_PATH"]
expected_sha256 = os.environ["NODE2A_PASS_RECEIPT_SHA256"]
prereq_sha = os.environ["NODE2A_PREREQ_SHA"]
repo_root = os.path.realpath(os.environ["REPO_ROOT"])

if not os.path.isabs(receipt_path):
    raise SystemExit("Node 2A PASS receipt path must be absolute")
if re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None:
    raise SystemExit("Node 2A PASS receipt SHA-256 must be lowercase hexadecimal")
if re.fullmatch(r"[0-9a-f]{40}", prereq_sha) is None:
    raise SystemExit("NODE2A_PREREQ_SHA must be a lowercase 40-character commit SHA")
if not os.path.isabs(repo_root) or not os.path.isdir(repo_root):
    raise SystemExit("REPO_ROOT must resolve to a directory")

try:
    descriptor = os.open(
        receipt_path,
        os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW,
    )
except OSError:
    raise SystemExit("Node 2A PASS receipt open failed") from None

try:
    descriptor_stat = os.fstat(descriptor)
    if not stat.S_ISREG(descriptor_stat.st_mode):
        raise SystemExit("Node 2A PASS receipt must be a regular file")
    if descriptor_stat.st_size <= 0 or descriptor_stat.st_size > 65_536:
        raise SystemExit("Node 2A PASS receipt size is invalid")

    descriptor_link = os.readlink(f"/proc/self/fd/{descriptor}")
    if descriptor_link.endswith(" (deleted)"):
        raise SystemExit("Node 2A PASS receipt descriptor is deleted")
    descriptor_path = os.path.realpath(descriptor_link)
    try:
        inside_repo = os.path.commonpath((repo_root, descriptor_path)) == repo_root
    except ValueError:
        raise SystemExit("Node 2A PASS receipt descriptor path is invalid") from None
    if inside_repo:
        raise SystemExit("Node 2A PASS receipt descriptor must resolve outside REPO_ROOT")

    receipt_bytes = os.read(descriptor, descriptor_stat.st_size + 1)
    if len(receipt_bytes) != descriptor_stat.st_size:
        raise SystemExit("Node 2A PASS receipt changed while being read")
finally:
    os.close(descriptor)

actual_sha256 = hashlib.sha256(receipt_bytes).hexdigest()
if actual_sha256 != expected_sha256:
    raise SystemExit("Node 2A PASS receipt SHA-256 mismatch")

try:
    payload = json.loads(
        receipt_bytes.decode("utf-8"),
        object_pairs_hook=reject_duplicate_keys,
    )
except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
    raise SystemExit("Node 2A PASS receipt JSON is invalid or has duplicate keys") from None

expected_payload = {
    "node": "team-evidence-aggregation-contracts-codec-temporal-eligibility",
    "head_sha": prereq_sha,
    "review_model": "claude-opus-4-8",
    "review_effort": "max",
    "review_exit_status": 0,
    "review_final_nonblank_line": "VERDICT: PASS",
    "focused_tests": "pass",
    "full_pytest": "pass",
    "compileall": "pass",
    "codegraph_sync": "pass",
    "static_gates": "pass",
    "clean_worktree": "pass",
    "pushed_remote_main_sha": prereq_sha,
}
if type(payload) is not dict or set(payload) != set(expected_payload):
    raise SystemExit("Node 2A PASS receipt has the wrong closed shape")
if any(type(payload[key]) is not type(value) for key, value in expected_payload.items()):
    raise SystemExit("Node 2A PASS receipt value types are invalid")
if payload != expected_payload:
    raise SystemExit("Node 2A PASS receipt values do not match the required handoff")

evidence = {
    "node2a_prereq_sha": prereq_sha,
    "receipt_sha256": actual_sha256,
    "validated_payload": payload,
}
print(
    "NODE2A_RECEIPT_EVIDENCE="
    + json.dumps(evidence, ensure_ascii=True, separators=(",", ":"), sort_keys=True),
)
PY
}
export -f validate_node2a_pass_receipt
readonly -f validate_node2a_pass_receipt

INITIAL_NODE2A_RECEIPT_EVIDENCE="$(validate_node2a_pass_receipt)"
test -n "$INITIAL_NODE2A_RECEIPT_EVIDENCE"
export INITIAL_NODE2A_RECEIPT_EVIDENCE

test -z "$(git status --porcelain=v1 --untracked-files=all)"
COMMON_GIT_DIR="$(git rev-parse --git-common-dir)"
GIT_AUTH=(-c credential.helper= -c "credential.helper=store --file=$COMMON_GIT_DIR/github-credentials")
GIT_TERMINAL_PROMPT=0 git "${GIT_AUTH[@]}" fetch --no-tags origin refs/heads/main:refs/remotes/origin/main
NODE_BASE="$(git rev-parse refs/remotes/origin/main)"
export NODE_BASE
test "$(git rev-parse HEAD)" = "$NODE_BASE"
git cat-file -e "$NODE2A_PREREQ_SHA^{commit}"
git merge-base --is-ancestor "$NODE2A_PREREQ_SHA" "$NODE_BASE"
git merge-base --is-ancestor "$NODE_BASE" HEAD

NODE2A_PREREQ_PATHS=(
  src/polymarket_alpha_lab/team_evidence_aggregation_codec.py
  src/polymarket_alpha_lab/team_evidence_aggregation_temporal.py
  src/polymarket_alpha_lab/team_evidence_aggregation_types.py
  tests/test_team_evidence_aggregation_codec.py
  tests/test_team_evidence_aggregation_temporal.py
  tests/test_team_evidence_aggregation_types.py
)
readonly -a NODE2A_PREREQ_PATHS

for path in "${NODE2A_PREREQ_PATHS[@]}"
do
  git cat-file -e "$NODE2A_PREREQ_SHA:$path"
done
git diff --quiet "$NODE2A_PREREQ_SHA..$NODE_BASE" -- "${NODE2A_PREREQ_PATHS[@]}"

readonly NODE_BASE REPO_ROOT NODE2A_PREREQ_SHA NODE2A_PASS_RECEIPT_PATH NODE2A_PASS_RECEIPT_SHA256 INITIAL_NODE2A_RECEIPT_EVIDENCE
```

Expected outcome: every command exits `0`; the worktree is clean; local `HEAD`
equals fetched `origin/main`; the reviewed Node 2A commit is an ancestor of
`NODE_BASE`; one `os.open(..., os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)` descriptor is
fstat-checked, resolved outside `REPO_ROOT`, read once, and closed; the exact
bytes satisfy the handoff SHA-256 and duplicate-key-safe closed JSON contract;
the helper emits one canonical non-secret `INITIAL_NODE2A_RECEIPT_EVIDENCE`
line; all six Node 2A-owned paths exist at the prerequisite commit; and those
exact paths are byte-unchanged from `NODE2A_PREREQ_SHA` through `NODE_BASE`.
Any drift requires a reviewed Node 2A amendment, fresh PASS receipt, and new
base. Do not infer, substitute, or update `NODE2A_PREREQ_SHA` from a moving
branch.

## Outgoing Node 2B Handoff Receipt Contract

Node 2C may consume Node 2B only after Node 2B's complete committed range has passed every gate, local Claude review has exited `0` with exact final nonblank `VERDICT: PASS`, the non-force push has completed, and fetched remote `main` has been verified equal to the accepted local Node 2B `HEAD`. At that point, and not before, Node 2B creates one externally stored immutable PASS receipt.

The coordinator supplies one runtime destination before the push step:

```bash
export NODE2B_PASS_RECEIPT_PATH
```

The path must be absolute, must resolve outside `REPO_ROOT`, and must name a file that does not exist. The parent directory must already exist as a real non-symlink directory outside `REPO_ROOT`. The receipt creator never creates directories, follows a final-component or parent-directory symlink, truncates, replaces, or appends to a path. A collision is a hard failure and requires a different externally managed destination.

The outgoing receipt inherits every field from the incoming closed receipt schema and adds exact review-mode booleans. It has exactly these fifteen keys and no others:

```json
{
  "node": "team-evidence-aggregation-independence-correlation-requirement-witness",
  "head_sha": "$NODE2B_PREREQ_SHA",
  "review_model": "claude-opus-4-8",
  "review_effort": "max",
  "read_only": true,
  "fast_mode": false,
  "review_exit_status": 0,
  "review_final_nonblank_line": "VERDICT: PASS",
  "focused_tests": "pass",
  "full_pytest": "pass",
  "compileall": "pass",
  "codegraph_sync": "pass",
  "static_gates": "pass",
  "clean_worktree": "pass",
  "pushed_remote_main_sha": "$NODE2B_PREREQ_SHA"
}
```

Both `$NODE2B_PREREQ_SHA` values are the exact accepted and pushed Node 2B `HEAD`, not literal dollar-prefixed text. `read_only` and `fast_mode` are exact JSON booleans, not strings or integers. Canonical receipt bytes are exactly `json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")`: UTF-8, ASCII-escaped, key-sorted, compact, and with no BOM, indentation, trailing spaces, or trailing newline. `NODE2B_PASS_RECEIPT_SHA256` is the lowercase SHA-256 of those exact bytes.

The closed payload contains no path, prompt, model output, patch, source material, rationale, DSN, credential, token, account, wallet, order, or other secret-bearing/free-text field. The only variable payload value is the reviewed/pushed public Git commit SHA in the two specified fields. `NODE2B_PASS_RECEIPT_PATH` and `NODE2B_PASS_RECEIPT_SHA256` travel out of band and are not added to the JSON.

Node 2C receives exactly these three handoff environment values:

```bash
export NODE2B_PREREQ_SHA
export NODE2B_PASS_RECEIPT_PATH
export NODE2B_PASS_RECEIPT_SHA256
```

Before treating Node 2B as a dependency, Node 2C must apply the same security posture as Node 2B's incoming validator: one `os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)`, regular-file `fstat`, descriptor-resolved path proof outside `REPO_ROOT`, one read from that descriptor, SHA-256 over those same bytes, duplicate-key rejection through `object_pairs_hook`, exact key/type/value equality to the fifteen-field schema above, `head_sha == pushed_remote_main_sha == NODE2B_PREREQ_SHA`, and an ancestor check from `NODE2B_PREREQ_SHA` to Node 2C's fetched base. A path-only precheck, blocking open, second file read, permissive JSON parser, extra key, wrong boolean type/value, hash mismatch, or non-PASS field blocks Node 2C.

---

### Task 1: Implement Exact Two-Stage Micro-Unit Allocation With TDD

**Files:**
- Create: `tests/test_team_evidence_aggregation_allocation.py` (maximum 600 physical lines)
- Create: `src/polymarket_alpha_lab/team_evidence_aggregation_allocation.py` (maximum 450 physical lines)

**Interfaces:**
- Consumes: exact Node 2A `TeamEvidenceAggregationRecord`, `TeamEvidenceAggregationConfig`, and `TeamEvidenceWeightAllocation` values from `polymarket_alpha_lab.team_evidence_aggregation_types`.
- Produces:

```python
__all__ = ("allocate_team_evidence_weights",)

def allocate_team_evidence_weights(
    records: tuple[TeamEvidenceAggregationRecord, ...],
    *,
    config: TeamEvidenceAggregationConfig,
) -> tuple[TeamEvidenceWeightAllocation, ...]: ...
```

- Sort key: `(assessment_revision_id, evidence_revision_id, captured_at, capture_id, source_lineage_id)`.
- Stage 1 groups `requested_weight` by `independence_key`; stage 2 groups stage-one weight by `correlation_key`.
- Output identity and sort order are one-to-one with the canonical sorted input tuple.

- [ ] **Step 1: Write the complete failing allocation test module**

Import the defining Node 2A module directly, never the package root. Define deterministic `_digest`, `_record`, `_config`, `_allocation_by_assessment`, and constructor-bypass-copy helpers. `_config` supplies every required policy value, uses conspicuously generic publication bounds `Decimal("0.110000")` and `Decimal("0.890000")`, defaults both caps to `1.000000`, uses the five exact hard resource ceilings `32`, `128`, `32`, `1024`, and `256`, and uses `requirements=()` unless a test explicitly supplies requirements.

The record fixture must use UTC-aware times in this valid order:

```python
freshness_anchor_at = datetime(2026, 7, 13, 12, 0, tzinfo=UTC)
captured_at = datetime(2026, 7, 13, 12, 1, tzinfo=UTC)
recorded_at = datetime(2026, 7, 13, 12, 2, tzinfo=UTC)
assessed_at = datetime(2026, 7, 13, 12, 3, tzinfo=UTC)
```

Create these exact tests and assertions:

```python
def test_allocate_team_evidence_weights_returns_uncapped_rows_in_canonical_order() -> None:
    # Pass records in reverse order. Assert output assessment IDs are ("assessment-a", "assessment-b"),
    # requested == independence == effective for both rows, and both cap flags are False.
    pass

def test_empty_allocation_input_returns_empty_tuple() -> None:
    # Assert allocate_team_evidence_weights((), config=config) == ().
    pass

def test_allocate_team_evidence_weights_applies_independence_cap_only() -> None:
    # Same independence key, distinct correlation keys, weights 0.600000/0.400000, independence cap 0.500000.
    # Assert stage-one/effective weights are 0.300000/0.200000 and every row has only independence_cap_applied=True.
    pass

def test_allocate_team_evidence_weights_applies_correlation_cap_only() -> None:
    # Distinct independence keys, same correlation key, weights 0.600000/0.400000, correlation cap 0.500000.
    # Assert stage one is unchanged, effective weights are 0.300000/0.200000, and only correlation flags are true.
    pass

def test_allocate_team_evidence_weights_applies_independence_before_correlation() -> None:
    # A=(i1,c1,0.600000), B=(i1,c2,0.400000), C=(i2,c1,0.400000), both caps 0.500000.
    # Assert prescribed effective A/B/C = 0.214286/0.200000/0.285714.
    # Also compute the forbidden reversed-stage result A/B/C = 0.214286/0.285714/0.200000
    # in a test-only helper and assert the production tuple differs from it.
    pass

def test_largest_remainder_conserves_cap_and_breaks_equal_remainders_by_record_key() -> None:
    # Three equal 0.000001 requests under cap 0.000002.
    # Assert canonical first and second records receive 0.000001, third receives 0.000000,
    # and the exact sum is 0.000002.
    pass

def test_largest_remainder_preserves_the_alabama_paradox_regression() -> None:
    # Requests keyed A/B/C are 0.000001/0.000003/0.000003.
    # Assert cap 0.000003 -> 0.000001/0.000001/0.000001.
    # Assert cap 0.000004 -> 0.000000/0.000002/0.000002.
    # Assert each group sum equals its cap and A loses exactly one micro-unit as the cap increases.
    pass

def test_cap_smaller_than_positive_record_count_assigns_only_available_micro_units() -> None:
    # Three equal positive requests under a one-micro-unit cap.
    # Assert exact allocations 0.000001/0.000000/0.000000 in canonical key order.
    pass

def test_zero_stage_one_and_stage_two_allocations_remain_exact_zero() -> None:
    # Use A=(i-a,c-shared,0.000001), B=(i-b,c-shared,0.000001),
    # C=(i-c,c-c,0.000001), D=(i-c,c-d,0.000001), and both caps 0.000001.
    # Assert D is zero at stage one, B is positive after stage one but zero at stage two,
    # every zero is unsigned Decimal("0.000000"), and no later stage resurrects D.
    pass

def test_cap_flags_are_group_level_and_equality_does_not_activate_them() -> None:
    # Assert every row in a strict over-cap group is flagged even when a row's own weight is unchanged.
    # Assert every row in a group whose total equals its cap has the corresponding flag False.
    pass

def test_allocation_never_increases_weights_and_every_group_respects_its_cap() -> None:
    # For mixed groups, assert 0 <= effective <= independence <= requested per row,
    # exact stage-one group totals <= independence cap, and exact stage-two group totals <= correlation cap.
    pass

def test_allocation_rejects_wrong_exact_types_duplicate_keys_and_resource_overflow() -> None:
    # Reject list/generator records, record subclasses or mocks, config subclasses or mocks,
    # duplicate canonical record keys, bool/int/float/Decimal-subclass cap or requested-weight values,
    # zero/nonfinite/raw-out-of-range/noncanonical fixed-six bypassed requested weights, wrong-type or
    # noncanonical bypassed independence/correlation keys, false hard flags, maximum_records > 128,
    # and len(records) > config.maximum_records.
    pass

def test_allocation_is_permutation_and_hostile_decimal_context_invariant() -> None:
    # Evaluate every permutation under normal context and under Context(prec=4, rounding=ROUND_DOWN).
    # Assert typed outputs and every Decimal field are exactly equal and no ambient context value changes.
    pass
```

Use exact expected `Decimal` values in assertions. Assert exact tuples and flags, not approximate values, sets, or membership-only checks. For constructor-bypassed inputs, copy all dataclass fields with `dataclasses.fields` and `object.__setattr__`, changing only the named field; this proves the public allocation boundary revalidates values instead of trusting construction.

- [ ] **Step 2: Run the allocation tests and verify RED**

```bash
.venv/bin/python -m pytest -q tests/test_team_evidence_aggregation_allocation.py
```

Expected outcome: collection fails because `polymarket_alpha_lab.team_evidence_aggregation_allocation` does not exist. A different failure means the test fixture is inconsistent with the fixed Node 2A contract and must be corrected before production code is created.

- [ ] **Step 3: Implement the minimal exact allocation module**

Use only these normalized imports, with absolute sibling-module import syntax:

```text
__future__
decimal
typing
polymarket_alpha_lab.team_evidence_aggregation_types
```

Define these non-exported constants and private helpers; do not add another module:

```python
_WEIGHT_QUANTUM = Decimal("0.000001")
_MICRO_UNITS_PER_ONE = 1_000_000
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_IMPLEMENTATION_MAXIMUM_RECORDS = 128

def _record_key(record: TeamEvidenceAggregationRecord) -> tuple[object, ...]: ...
def _validate_group_key(field_name: str, value: object) -> str: ...
def _validate_allocation_inputs(records: object, config: object) -> tuple[TeamEvidenceAggregationRecord, ...]: ...
def _weight_to_micro_units(field_name: str, value: object) -> int: ...
def _micro_units_to_weight(value: int) -> Decimal: ...
def _apportion_micro_units(
    indexed_weights: tuple[tuple[int, int], ...],
    *,
    cap_micro_units: int,
    records: tuple[TeamEvidenceAggregationRecord, ...],
) -> tuple[tuple[int, int], ...]: ...
def _apply_cap_stage(
    input_micro_units: tuple[int, ...],
    *,
    group_keys: tuple[str, ...],
    cap_micro_units: int,
    records: tuple[TeamEvidenceAggregationRecord, ...],
) -> tuple[tuple[int, ...], tuple[bool, ...]]: ...
```

`_validate_allocation_inputs` must perform every semantic check before
arithmetic. Only validated canonical sort-key components may reach sorting:

1. Require an exact-base `tuple`, every element to be exactly `TeamEvidenceAggregationRecord`, and an exact `TeamEvidenceAggregationConfig`; reject bools, subclasses, mocks, and duck types.
2. Revalidate `paper_only is True`, `report_only is True`, and `readonly is True` on the config, every record, and every nested lineage/capture/evidence/assessment object used by the function.
3. Require `maximum_records` to be exact `int`, not `bool`, in `1..128`; require `len(records) <= maximum_records` and `len(records) <= 128`.
4. Require both group caps to be exact finite base `Decimal`, raw-bounded in `[0, 1]`, already canonical fixed-six, and unsigned when zero. Require every allocation-input requested weight to be exact finite base `Decimal`, raw-bounded in `(0, 1]`, and already canonical fixed-six. Zero requested weights are structurally valid in Node 2A but are excluded by Node 2C before this function and are invalid at this direct allocation boundary. Reject before conversion rather than rounding or clipping.
5. In original input order, require every canonical record-key component to have its Node 2A exact canonical scalar representation, including UTC-identity `captured_at`. Revalidate each assessment's `independence_key` and `correlation_key` as exact base strings satisfying the complete Node 2A canonical-identifier syntax and 160-byte bound before either key reaches grouping; implement this without an additional import. Sort only after these fields are safe, then require unique canonical record keys.
6. After the targeted resource, Decimal, hard-flag, and sort-key checks above, reconstruct the config and every canonically sorted record through their exact public constructors. Compare supplied and reconstructed values using the representation-sensitive equality below. Map reconstruction failure or inequality to the exact `config must be canonical` or canonical-sorted `records[index] must be canonical` error. Return the canonically sorted tuple.

Exact type and hard-flag checks are not sufficient for constructor-bypassed
instances. Reconstruct the config and every record through their exact public
constructors, then compare the supplied and reconstructed values recursively
with Node 2A-equivalent canonical equality: exact runtime type;
`Decimal.as_tuple()` equality; datetime value equality plus identical UTC
`tzinfo`; tuple element recursion; and slotted public-dataclass field
recursion. Reject before arithmetic when reconstruction fails or
canonical equality differs. This catches wrong Decimal exponents, non-UTC
datetime representations, unsorted tuples, malformed nested exact types, and
other bypassed noncanonical state without importing Node 2A private helpers.

Use these exact stable `ValueError` descriptions and assert them with escaped
exact matches in negative tests. Exact element-type and sort-key-component
errors use the original input index because canonical order is not yet safe.
In particular, `records[index] must be exactly
TeamEvidenceAggregationRecord` always reports the original tuple position;
pre-sort sort-key canonical failures use `records[index] must be canonical` at
that original input index. All post-sort canonical-record errors use the same
message at the canonical sorted index:

```text
records must be an exact tuple
config must be exactly TeamEvidenceAggregationConfig
config must be canonical
config.maximum_records must be an exact int in 1..128
records exceeds config.maximum_records
records[index] must be exactly TeamEvidenceAggregationRecord
records[index] must be canonical
records contains duplicate canonical record key
field_path must preserve paper_only=True, report_only=True, readonly=True
field_path must be an exact finite canonical fixed-six Decimal in [0, 1]
records[index].assessment_revision.requested_weight must be an exact finite canonical fixed-six Decimal in (0, 1]
records[index].assessment_revision.independence_key must be an exact canonical identifier
records[index].assessment_revision.correlation_key must be an exact canonical identifier
```

Replace `field_path` with the exact public field path being rejected; do not interpolate the rejected value or its repr. Empty input is valid and returns `()` before group construction, after exact config/resource validation.

Convert a validated fixed-six weight to integer micro-units exactly; no division through binary values and no independent Decimal rounding is permitted. Convert integer units back inside `localcontext(_DECIMAL_CONTEXT)` and canonicalize zero to `Decimal("0.000000")`.

For each strict over-cap group, `_apportion_micro_units` implements this exact integer equivalent of rational largest remainder:

```text
quota_numerator_i = input_micro_units_i * cap_micro_units
floor_i = quota_numerator_i // group_total_micro_units
remainder_i = quota_numerator_i % group_total_micro_units
remaining = cap_micro_units - sum(floor_i)
```

Add one unit to the first `remaining` rows sorted by descending `remainder_i`, then by ascending canonical record key. If the group total is at or below the cap, return inputs unchanged. Assert internal invariants before creating public rows: exact capped total on strict over-cap, no negative units, and no allocation above its input.

Call `_apply_cap_stage` exactly twice:

```text
requested micro-units --group independence_key--> independence micro-units
independence micro-units --group correlation_key--> effective micro-units
```

For each stage, set the group flag on every group row if and only if the pre-cap group total strictly exceeds the cap. Equality is false. A zero from stage one stays zero in stage two. Return exact `TeamEvidenceWeightAllocation` rows in canonical record-key order, explicitly supplying all identity fields, both group keys, all three weights, both flags, and all three hard flags.

- [ ] **Step 4: Run allocation tests and verify GREEN**

```bash
.venv/bin/python -m pytest -q tests/test_team_evidence_aggregation_allocation.py
```

Expected outcome: all allocation tests pass with exit `0`; the Alabama paradox vector, stage-order vector, cap sums, strict flag semantics, exact-type failures, permutation invariance, and hostile-context assertions all pass.

- [ ] **Step 5: Stage the exact Task 1 subset, scan it, and commit**

```bash
set -euo pipefail
git add -- \
  src/polymarket_alpha_lab/team_evidence_aggregation_allocation.py \
  tests/test_team_evidence_aggregation_allocation.py
test "$(git diff --cached --name-only | LC_ALL=C sort)" = $'src/polymarket_alpha_lab/team_evidence_aggregation_allocation.py\ntests/test_team_evidence_aggregation_allocation.py'
git diff --cached --check

for path in \
  src/polymarket_alpha_lab/team_evidence_aggregation_allocation.py \
  tests/test_team_evidence_aggregation_allocation.py
do
  ADDED_STAGED="$(git diff --cached --unified=0 -- "$path" | sed -n '/^+++ /d; /^+/s/^+//p')"
  if rg -q '(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|(^|[^[:alnum:]_])sk-[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}|postgres(ql)?://[^[:space:]/]+:[^[:space:]@]+@)' <<< "$ADDED_STAGED"; then
    RG_STATUS=0
  else
    RG_STATUS=$?
  fi
  case "$RG_STATUS" in
    0) printf 'credential-shaped staged addition in %s\n' "$path" >&2; exit 1 ;;
    1) ;;
    *) printf 'staged secret scan failed for %s with rg status %s\n' "$path" "$RG_STATUS" >&2; exit "$RG_STATUS" ;;
  esac
done

git commit -m "feat: add deterministic evidence weight allocation"
```

Expected outcome: the literal staged-path equality check passes, the high-confidence scan remains quiet and prints no matched values, and the commit succeeds. `rg` status `0` is a finding and fails, status `1` is clean, and any status greater than `1` is a command failure.

---

### Task 2: Implement Global Severity-Prioritized Requirement Witnesses With TDD

**Files:**
- Create: `tests/test_team_evidence_aggregation_witness.py` (maximum 900 physical lines, including the Node 2B child-local gate)
- Create: `src/polymarket_alpha_lab/team_evidence_aggregation_witness.py` (maximum 650 physical lines)

**Interfaces:**
- Consumes: exact Node 2A `TeamEvidenceAggregationRecord`, `TeamEvidenceAggregationConfig`, `TeamEvidenceRequirement`, `TeamEvidenceWeightAllocation`, `TeamEvidenceRequirementWitness`, and `TeamEvidenceRequirementCoverage`; Node 2B `allocate_team_evidence_weights`.
- Produces:

```python
__all__ = ("build_team_evidence_requirement_coverage",)

def build_team_evidence_requirement_coverage(
    allocation_input_records: tuple[TeamEvidenceAggregationRecord, ...],
    allocations: tuple[TeamEvidenceWeightAllocation, ...],
    *,
    config: TeamEvidenceAggregationConfig,
) -> tuple[TeamEvidenceRequirementCoverage, ...]: ...
```

- Exact record/allocation join key: `(source_lineage_id, capture_id, evidence_revision_id, assessment_revision_id)`.
- Exact candidate edge key: `(requirement_id, source_lineage_id, evidence_revision_id, assessment_revision_id, capture_id)`.
- Exact objective: maximize `(blocked_assignment_count, watch_assignment_count)` lexicographically, then select the lexicographically smallest sorted edge tuple at that vector.

The objective maximizes assignment counts inside each severity, not the number
of fully satisfied requirements. When total blocked demand is infeasible, the
lexical optimum may assign a scarce edge partially to a high-demand blocked
requirement even when another blocked requirement could be fully satisfied.
That is the approved deterministic policy: both outcomes remain blocked, and
coverage preserves the exact partial counts.

- [ ] **Step 1: Write the complete failing witness, oracle, and child-scope test module**

Repeat the deterministic Node 2A fixture constructors locally so this test file is independently executable. Use requested weight `0.010000`, caps `1.000000`, and unique correlation keys in matching tests unless a test explicitly needs a cap-zero row. Every configured requirement uses an exact positive `minimum_witness_count`, exact fixed-six `minimum_effective_weight`, and explicit `unmet_status` of `"blocked"` or `"watch"`. The default fixture threshold is positive; the required zero-threshold test below supplies exact `Decimal("0.000000")` explicitly.

Create these exact public-behavior tests:

```python
def test_witness_threshold_is_inclusive_and_rows_are_sorted_for_every_requirement() -> None:
    # Effective weight exactly equals minimum_effective_weight.
    # Assert it is a candidate, coverage IDs are sorted, all configured scalar fields are preserved,
    # and a zero-candidate requirement emits assigned_witness_count=0, witnesses=(), satisfied=False.
    pass

def test_zero_minimum_effective_weight_threshold_accepts_only_positive_effective_rows() -> None:
    # Configure minimum_effective_weight=0.000000. Supply one positive-effective row and one row
    # exhausted to exact 0.000000. Assert only the positive row becomes a witness and its exact
    # effective weight is preserved; zero-effective rows never create candidate edges.
    pass

def test_witness_enforces_evidence_assignment_and_requirement_independence_capacities() -> None:
    # One evidence listing two requirements with evidence capacity 1 gets one assignment.
    # Two evidence rows sharing an independence key cannot both witness the same demand-2 requirement.
    pass

def test_global_matching_solves_the_greedy_counterexample() -> None:
    # requirement-a accepts evidence-flexible and evidence-a-only; requirement-b accepts only evidence-flexible;
    # all capacities are 1. Assert the global result assigns a-only->a and flexible->b and satisfies both.
    pass

def test_partial_coverage_preserves_explicit_watch_and_blocked_policy() -> None:
    # Emit one unsatisfied watch row and one unsatisfied blocked row.
    # Assert exact assigned counts, satisfied=False, and unchanged unmet_status values.
    pass

def test_blocked_assignments_have_priority_over_lexically_earlier_watch_edges() -> None:
    # One evidence can serve either requirement "a-watch" or "z-blocked" with capacity 1.
    # Assert z-blocked receives the sole assignment and a-watch receives none.
    pass

def test_severity_optimum_uses_the_lexically_smallest_edge_set() -> None:
    # Two evidence rows and two blocked demand-1 requirements form K2,2 with unit evidence capacities.
    # Assert exact matching requirement-a/evidence-a and requirement-b/evidence-b.
    pass

def test_assignment_objective_does_not_maximize_fully_satisfied_requirements() -> None:
    # One evidence with capacity 1 can serve blocked requirement-a with demand 2 or blocked
    # requirement-b with demand 1. Both choices have objective (1, 0). Assert the lexical optimum
    # assigns requirement-a, leaving both requirements unsatisfied, and preserves exact partial counts.
    pass

def test_witness_recomputes_and_requires_the_exact_canonical_allocation(monkeypatch: pytest.MonkeyPatch) -> None:
    # Spy on the module-local allocate_team_evidence_weights binding and assert one call with the exact
    # allocation_input_records object and config. Reject missing, duplicate, extra, reordered, or altered rows.
    pass

def test_witness_rejects_join_and_assessment_projection_mismatches() -> None:
    # Constructor-bypass source/capture/evidence/assessment IDs, independence key, correlation key,
    # and requested weight one at a time. Assert failure before candidate construction.
    pass

def test_candidate_edge_resource_bound_is_checked_before_graph_construction(monkeypatch: pytest.MonkeyPatch) -> None:
    # Two valid threshold-passing candidates: maximum_witness_edges=2 passes; value 1 fails.
    # Replace private _canonical_optimum_edges with a test failure sentinel for the overflow call
    # and assert the sentinel is never reached.
    pass

def test_membership_count_deduplicates_repeated_evidence_revision_projections() -> None:
    # Build 32 distinct evidence revisions, each represented by two exact assessment records and all 32
    # configured requirement IDs. Set each 0.010000 effective weight below the 0.020000 thresholds.
    # Assert the distinct-revision membership count is exactly 32 * 32 == 1024 rather than 2048,
    # the call succeeds, and all 32 coverage rows have zero candidates/witnesses.
    pass

def test_witness_assignment_capacity_is_per_record_join_not_evidence_revision() -> None:
    # Represent one evidence_revision_id with two assessment records carrying distinct independence
    # keys and positive effective weights. With per-record capacity 1 and requirement demand 2,
    # assert both records are assigned despite sharing the evidence revision identity.
    pass

def test_33_by_32_threshold_filtered_memberships_fail_before_recomputation_or_candidates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Build 33 distinct evidence revisions, each listing all 32 configured requirement IDs:
    # 33 * 32 == 1056. Keep every 0.010000 effective weight below each 0.020000 threshold.
    # Compute the caller allocation before patching, then replace both the witness module's
    # allocate_team_evidence_weights binding and _build_candidate_edges with pytest.fail sentinels.
    # Assert the exact membership-limit ValueError and prove neither sentinel is reached.
    pass

def test_positive_effective_records_require_config_resident_requirement_ids() -> None:
    # Positive effective record with retired requirement ID fails.
    # A second record exhausted to exact zero by a one-micro-unit independence cap may retain the retired ID;
    # assert only configured coverage rows are emitted and the call succeeds.
    pass

def test_witness_is_input_requirement_and_adjacency_permutation_invariant() -> None:
    # Permute allocation_input_records, config.requirements, and each record's requirement_ids;
    # recompute canonical allocations for each input order and assert exact equal typed coverage.
    pass

def test_witness_rejects_wrong_types_hard_flags_and_resource_values() -> None:
    # Reject non-tuples, wrong exact record/allocation/config/requirement types, false hard flags,
    # bool/nonpositive/>32 assignment capacity, bool/nonpositive/>32 maximum requirements,
    # bool/nonpositive/>256 edge ceiling, malformed minimum counts/weights/statuses, and resource overflow.
    pass
```

Add a test-only exhaustive oracle with these exact helpers and search domain:

```python
def _restricted_growth_partitions(size: int) -> tuple[tuple[int, ...], ...]:
    # Return every canonical restricted-growth string: first item 0 and each next item <= 1 + max(prefix).
    pass

def _oracle_optimum_edges(
    candidate_edges: tuple[tuple[str, str, str, str, str], ...],
    *,
    evidence_capacity: int,
    independence_key_by_source: dict[str, str],
    requirement_by_id: dict[str, TeamEvidenceRequirement],
) -> tuple[tuple[int, int], tuple[tuple[str, str, str, str, str], ...]]:
    # Enumerate every edge subset. Keep only subsets satisfying evidence capacity,
    # one edge per (requirement_id, independence_key), and each requirement's witness-count capacity.
    # Maximize (blocked assignments, watch assignments), then choose min(sorted_edge_tuple).
    pass
```

The exhaustive test is exactly:

```python
def test_production_matching_equals_the_bruteforce_small_graph_oracle() -> None:
    # evidence_count in 1..3; requirement_count in 1..2;
    # every adjacency matrix; evidence capacity in (1, 2);
    # every restricted-growth independence partition;
    # each requirement demand in (1, 2), filtered to demand <= evidence_count;
    # every blocked/watch assignment.
    # Build public records/config/allocations, invoke the public witness builder,
    # derive its exact objective and edge tuple, and assert equality to both oracle outputs.
    pass
```

The oracle must be test-only and must not be imported by production. It enumerates edge subsets in integer-mask order but compares canonical sorted edge tuples, so enumeration order cannot become the tie-break.

Add these exact wider lexical cases:

```python
@pytest.mark.parametrize(
    ("adjacency", "expected_pairs"),
    (
        ("complete-k3-3", (("requirement-a", "source-a"), ("requirement-b", "source-b"), ("requirement-c", "source-c"))),
        ("six-edge-cycle", (("requirement-a", "source-a"), ("requirement-b", "source-b"), ("requirement-c", "source-c"))),
    ),
)
def test_three_by_three_unit_capacity_uses_wider_lexical_optimum(
    adjacency: str,
    expected_pairs: tuple[tuple[str, str], ...],
) -> None: ...
```

For `six-edge-cycle`, use edges `a->{a,b}`, `b->{b,c}`, and `c->{a,c}` when written source-to-requirement. All three requirements are blocked with demand 1, all sources have distinct independence keys, and evidence capacity is 1.

In the same test file, implement one child-local gate named exactly:

```python
def test_node_2b_child_local_ast_import_export_forbidden_surface_and_line_size_gate() -> None: ...
```

The gate must perform all of these assertions in one focused test:

1. Parse both production files with `ast.parse`.
2. Normalize `ast.Import` as each `alias.name`; normalize `ast.ImportFrom` only when `level == 0` and `module` is nonempty. Reject every relative import. Compare exact sets to:

```python
EXPECTED_IMPORTS = {
    "team_evidence_aggregation_allocation.py": {
        "__future__",
        "decimal",
        "typing",
        "polymarket_alpha_lab.team_evidence_aggregation_types",
    },
    "team_evidence_aggregation_witness.py": {
        "__future__",
        "collections",
        "typing",
        "polymarket_alpha_lab.team_evidence_aggregation_types",
        "polymarket_alpha_lab.team_evidence_aggregation_allocation",
    },
}
```

3. Require one literal tuple assignment to `__all__` and exact equality, including order and no duplicates:

```python
EXPECTED_EXPORTS = {
    "team_evidence_aggregation_allocation.py": ("allocate_team_evidence_weights",),
    "team_evidence_aggregation_witness.py": ("build_team_evidence_requirement_coverage",),
}
```

4. Reject an exact package-root module import or direct package-root export access, plus Node 2C, forecast-packet, DB-row, store, CLI, persistence, network, filesystem, process, logging, auth, account, credential, token, wallet, signing, order, sizing, allocation-to-capital, execution, exchange, and trading import/reference segments. The `polymarket_alpha_lab.` namespace prefix on the two allowlisted direct sibling imports is not itself a package-root violation.
5. Reject calls to `open`, `print`, `input`, `eval`, `exec`, `compile`, dynamic import, `repr`, built-in `hash`, `float`, `datetime.now`, `datetime.utcnow`, randomness, `timedelta.total_seconds()`, and `datetime.timestamp()`.
6. Reject float literals, float annotations, bare or broad `Exception`/`BaseException` handlers, and any call whose callee is an input callback parameter.
7. Reject source tokens for BTC policy, built-in `0.020000`/`0.980000`, `tea:v1`, `tfr:v1`, `tfe:v1`, legacy projections, and package-root exports.
8. Require an AST call from the public witness builder path to the imported `allocate_team_evidence_weights` binding.
9. Require exact non-exported integer assignments for Node 2B's relevant hard maxima: allocation records `128`; witness assignments per evidence `32`, requirements `32`, memberships `1024`, and witness edges `256`. Reject a missing, renamed, nonliteral, or different maximum.
10. Count physical lines with `len(path.read_text(encoding="utf-8").splitlines())` and enforce exactly:

```python
MAX_LINES = {
    "src/polymarket_alpha_lab/team_evidence_aggregation_allocation.py": 450,
    "src/polymarket_alpha_lab/team_evidence_aggregation_witness.py": 650,
    "tests/test_team_evidence_aggregation_allocation.py": 600,
    "tests/test_team_evidence_aggregation_witness.py": 900,
}
assert production_line_total <= 1_100
assert test_line_total <= 1_500
```

Use AST inspection as the primary gate. Source-text checks are limited to the explicit policy/identity tokens above so valid names such as `correlation_group_weight_cap` are not rejected incidentally.

- [ ] **Step 2: Run the witness tests and verify RED**

```bash
.venv/bin/python -m pytest -q tests/test_team_evidence_aggregation_witness.py
```

Expected outcome: collection fails because `polymarket_alpha_lab.team_evidence_aggregation_witness` does not exist. Do not create a temporary stub to change this failure mode.

- [ ] **Step 3: Implement exact validation, recomputation, and candidate generation**

Use only these normalized imports, with absolute sibling-module syntax:

```text
__future__
collections
typing
polymarket_alpha_lab.team_evidence_aggregation_types
polymarket_alpha_lab.team_evidence_aggregation_allocation
```

Define exact private tuple aliases for join and edge keys, `_IMPLEMENTATION_MAXIMUM_REQUIREMENT_ASSIGNMENTS = 32`, `_IMPLEMENTATION_MAXIMUM_REQUIREMENTS = 32`, `_IMPLEMENTATION_MAXIMUM_REQUIREMENT_MEMBERSHIPS = 1024`, and `_IMPLEMENTATION_MAXIMUM_WITNESS_EDGES = 256`. Define private helpers with these responsibilities and names:

```python
def _record_key(record: TeamEvidenceAggregationRecord) -> tuple[object, ...]: ...
def _join_key_from_record(record: TeamEvidenceAggregationRecord) -> tuple[str, str, str, str]: ...
def _join_key_from_allocation(allocation: TeamEvidenceWeightAllocation) -> tuple[str, str, str, str]: ...
def _candidate_edge_key(requirement_id: str, record: TeamEvidenceAggregationRecord) -> tuple[str, str, str, str, str]: ...
def _validate_witness_inputs(
    allocation_input_records: object,
    allocations: object,
    config: object,
) -> tuple[
    tuple[TeamEvidenceAggregationRecord, ...],
    tuple[TeamEvidenceWeightAllocation, ...],
]: ...
def _build_candidate_edges(
    allocation_input_records: tuple[TeamEvidenceAggregationRecord, ...],
    allocations: tuple[TeamEvidenceWeightAllocation, ...],
    *,
    config: TeamEvidenceAggregationConfig,
) -> tuple[tuple[str, str, str, str, str], ...]: ...
```

`_validate_witness_inputs` must execute this exact order:

1. Require exact record/allocation tuples, an exact config, and exact Node 2A record/allocation element types with all applicable hard flags exactly true. Wrong element types fail with their dedicated exact-type messages below before any constructor call.
2. Revalidate the five config resource ceilings as positive exact ints, reject `bool`, and enforce their absolute maxima `32`, `128`, `32`, `1024`, and `256` before collection work.
3. Require `config.requirements` to be an exact tuple of exact requirements with exact hard flags, require canonical unique sorted requirement IDs, and enforce `len(requirements) <= maximum_requirements`. These resource and structure checks intentionally precede config reconstruction so their dedicated stable errors remain reachable.
4. Reconstruct every received config, requirement, record, and allocation through its exact public constructor and compare recursively with the same representation-sensitive canonical equality required by Task 1. Map reconstruction failure or inequality to the corresponding exact canonical error below. Reject constructor-bypassed wrong Decimal exponents, non-UTC datetime representations, unsorted nested tuples, malformed exact scalar fields, or altered nested values before membership counting, recomputation, equality, arithmetic, or graph work.
5. Before allocation recomputation or candidate generation, deduplicate evidence revisions by exact `evidence_revision_id`. Every repeated ID must carry an exactly equal `TeamEvidenceRevision` projection, including the same digest and all owned fields. Sum `len(evidence_revision.requirement_ids)` once per distinct exact projection, incrementally, and require the sum to be no greater than both `config.maximum_requirement_memberships` and absolute `1024`. Both bounds are inclusive: an exact total of `1024` is valid when the configured bound is at least `1024`; raise only when the next incremental total is strictly greater than either bound.
6. Recompute `canonical_allocations = allocate_team_evidence_weights(allocation_input_records, config=config)` before candidate generation.
7. Require caller `allocations == canonical_allocations` exactly. Tuple order, identity, fields, flags, and values all participate; missing, extra, duplicate, reordered, or altered rows fail.
8. Join each canonical record and allocation exactly by the four-field join key. Require one-to-one key equality and require allocation independence key, correlation key, and requested weight to equal the assessment fields.
9. Preserve the complete allocation-input tuple. Do not reduce it to positive rows before recomputation or equality validation.

Use these exact stable `ValueError` descriptions and assert them with escaped exact matches in negative tests:

```text
allocation_input_records must be an exact tuple
allocations must be an exact tuple
config must be exactly TeamEvidenceAggregationConfig
allocation_input_records[index] must be exactly TeamEvidenceAggregationRecord
allocations[index] must be exactly TeamEvidenceWeightAllocation
config.requirements[index] must be exactly TeamEvidenceRequirement
field_path must preserve paper_only=True, report_only=True, readonly=True
config must be canonical
config.requirements[index] must be canonical
allocation_input_records[index] must be canonical
allocations[index] must be canonical
config.resource_field must be an exact int within its implementation maximum
config.requirements must contain exact unique requirements sorted by requirement_id
repeated evidence revision identity must have one exact projection
distinct evidence revision requirement memberships exceed config.maximum_requirement_memberships or 1024
allocations must equal canonical recomputation for allocation_input_records
record/allocation join keys must match exactly
allocation.independence_key must match assessment_revision.independence_key
allocation.correlation_key must match assessment_revision.correlation_key
allocation.requested_weight must match assessment_revision.requested_weight
positive-effective requirement ID must exist in config.requirements
candidate witness edge count exceeds config.maximum_witness_edges
internal witness matching invariant failed
```

Replace `resource_field` with the exact config field name. The membership overflow message is emitted immediately when the incremental distinct-revision total first exceeds either bound; threshold filtering cannot defer or erase this failure. Error text may include a canonical ID needed to locate an invalid relationship, but it must never include a rejected value's repr, raw source material, rationale, DSN, secret, or payload.

Candidate generation then considers only joined rows with positive canonical `effective_weight`. For every such row, require every `evidence_revision.requirement_ids` item to exist in config. For each configured membership, add a candidate exactly when `effective_weight >= minimum_effective_weight`; equality is included. Increment candidate count as each edge is admitted. If the next edge would exceed `maximum_witness_edges` or absolute `256`, raise `ValueError` before constructing a flow node, residual edge, or solver object. Canonically sort and return candidate edges.

Rows whose canonical effective weight is zero create no edges and may retain requirement IDs absent from the current config. This exception is only for zero-effective diagnostic records; a positive-effective record with any absent requirement ID fails the whole call.

- [ ] **Step 4: Implement deterministic integer max flow and the exact severity objective**

Implement a private iterative Dinic solver using only integer capacities and `collections.deque`. Node IDs are consecutive ints assigned from canonically sorted semantic keys. Adjacency insertion order is canonical, but correctness and lexical selection must not depend on augmenting-path order. The solver exposes only private `add_edge(source, target, capacity)` and `maximum_flow(source, sink)` behavior and uses no recursion or external graph library.

Define these exact private helpers:

```python
def _objective_is_feasible(
    candidate_edges: tuple[tuple[str, str, str, str, str], ...],
    *,
    forced_edges: frozenset[tuple[str, str, str, str, str]],
    forbidden_edges: frozenset[tuple[str, str, str, str, str]],
    blocked_target: int,
    watch_target: int,
    record_by_edge: dict[tuple[str, str, str, str, str], TeamEvidenceAggregationRecord],
    requirement_by_id: dict[str, TeamEvidenceRequirement],
    max_assignments_per_evidence: int,
) -> bool: ...

def _maximum_objective(
    candidate_edges: tuple[tuple[str, str, str, str, str], ...],
    *,
    record_by_edge: dict[
        tuple[str, str, str, str, str],
        TeamEvidenceAggregationRecord,
    ],
    requirement_by_id: dict[str, TeamEvidenceRequirement],
    max_assignments_per_evidence: int,
) -> tuple[int, int]: ...

def _canonical_optimum_edges(
    candidate_edges: tuple[tuple[str, str, str, str, str], ...],
    *,
    blocked_target: int,
    watch_target: int,
    record_by_edge: dict[
        tuple[str, str, str, str, str],
        TeamEvidenceAggregationRecord,
    ],
    requirement_by_id: dict[str, TeamEvidenceRequirement],
    max_assignments_per_evidence: int,
) -> tuple[tuple[str, str, str, str, str], ...]: ...
```

`_objective_is_feasible` first preconsumes every forced edge and rejects forced/forbidden overlap, a noncandidate forced edge, evidence-capacity overflow, duplicate `(requirement_id, independence_key)` contribution, requirement-demand overflow, or negative remaining severity target. Each evidence-capacity node is one exact four-field record/allocation join key, not a source lineage, independence group, evidence revision, or assessment revision projection. Build the exact residual network:

```text
source
  -> evidence node                          remaining evidence capacity
  -> (requirement_id, independence_key)    capacity 1 per remaining candidate edge
  -> requirement node                      remaining independence-pair capacity 0 or 1
  -> blocked/watch severity node           remaining requirement demand
  -> sink                                  exact remaining severity target
```

Despite the historical configuration-field name
`max_requirement_assignments_per_evidence`, the capacity is per exact
four-field record join. Two accepted assessment records sharing an
`evidence_revision_id` therefore receive independent capacities. The direct
regression above fixes this behavior; the small-graph oracle continues to model
one capacity per record node and is not evidence-revision-capacity coverage.

Enforce the two severity-to-sink edges with lower bound equal to upper bound equal to the respective remaining target. Convert this bounded flow to a feasible circulation exactly:

1. Add residual capacity `upper - lower` for every bounded edge.
2. For each lower bound `L` on `u -> v`, apply `balance[u] -= L` and `balance[v] += L`.
3. Add `sink -> source` with capacity equal to total remaining target.
4. For positive balance, add `super_source -> node` with that capacity; for negative balance, add `node -> super_sink` with `-balance`.
5. Run integer max flow from super source to super sink and return true if and only if every super-source edge is saturated.

This is a feasibility query only; no residual augmenting-path selection is exposed as the matching tie-break.

`_maximum_objective` uses monotone binary search over bounded integer demand. The search upper bound for either severity is the smaller of that severity's configured demand sum and the number of candidate edges for that severity, so hostile witness counts cannot enlarge runtime beyond the 256-edge hard bound:

1. Find the maximum feasible blocked target with watch target exactly zero.
2. Hold that blocked optimum fixed and find the maximum feasible watch target.
3. Return `(F_blocked, F_watch)`.

`_canonical_optimum_edges` sorts all candidates by the exact five-field edge key. Starting with empty forced and forbidden sets, iterate in that order. Tentatively force the current edge and call `_objective_is_feasible` for exactly `(F_blocked, F_watch)` while honoring all prior decisions. Keep the edge forced when feasible; otherwise mark it forbidden. At completion, require forced count `F_blocked + F_watch`, require exact severity counts, and return the sorted forced tuple. This force/forbid process, not solver adjacency order, produces the lexicographically smallest edge set among all severity-optimal matchings.

- [ ] **Step 5: Materialize exact coverage rows**

For every configured requirement sorted by `requirement_id`, gather assigned canonical edges for that ID and materialize one `TeamEvidenceRequirementWitness` per edge with exactly:

```text
requirement_id
source_lineage_id
capture_id
evidence_revision_id
assessment_revision_id
independence_key
effective_weight
paper_only=True
report_only=True
readonly=True
```

Sort witnesses by the same canonical edge key. Materialize exactly one `TeamEvidenceRequirementCoverage` per requirement, preserving `minimum_witness_count`, `minimum_effective_weight`, and `unmet_status`, setting `assigned_witness_count` to the exact base-int edge count, setting `satisfied = assigned_witness_count >= minimum_witness_count`, and explicitly supplying `paper_only=True`, `report_only=True`, and `readonly=True`. Because every valid requirement has `minimum_witness_count >= 1`, a zero-candidate requirement produces a row with `assigned_witness_count=0`, `witnesses=()`, and `satisfied=False`. Return the coverage tuple sorted by requirement ID, including an empty tuple when config has no requirements.

- [ ] **Step 6: Run Node 2B focused tests and the explicit child-local gate**

```bash
.venv/bin/python -m pytest -q \
  tests/test_team_evidence_aggregation_allocation.py \
  tests/test_team_evidence_aggregation_witness.py

.venv/bin/python -m pytest -q \
  tests/test_team_evidence_aggregation_witness.py::test_node_2b_child_local_ast_import_export_forbidden_surface_and_line_size_gate
```

Expected outcome: both commands exit `0`. The exhaustive oracle matches both the objective vector and exact edge set for every bounded graph; the three-by-three ties pass; the allocation recomputation, distinct-revision membership deduplication, 33-by-32 pre-recomputation overflow sentinel, threshold, edge-resource bound, retired-ID, severity, lexical, AST/import/export/forbidden-surface, and physical-line assertions all pass.

- [ ] **Step 7: Stage the exact Task 2 subset, scan it, and commit**

```bash
set -euo pipefail
git add -- \
  src/polymarket_alpha_lab/team_evidence_aggregation_witness.py \
  tests/test_team_evidence_aggregation_witness.py
test "$(git diff --cached --name-only | LC_ALL=C sort)" = $'src/polymarket_alpha_lab/team_evidence_aggregation_witness.py\ntests/test_team_evidence_aggregation_witness.py'
git diff --cached --check

for path in \
  src/polymarket_alpha_lab/team_evidence_aggregation_witness.py \
  tests/test_team_evidence_aggregation_witness.py
do
  ADDED_STAGED="$(git diff --cached --unified=0 -- "$path" | sed -n '/^+++ /d; /^+/s/^+//p')"
  if rg -q '(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|(^|[^[:alnum:]_])sk-[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}|postgres(ql)?://[^[:space:]/]+:[^[:space:]@]+@)' <<< "$ADDED_STAGED"; then
    RG_STATUS=0
  else
    RG_STATUS=$?
  fi
  case "$RG_STATUS" in
    0) printf 'credential-shaped staged addition in %s\n' "$path" >&2; exit 1 ;;
    1) ;;
    *) printf 'staged secret scan failed for %s with rg status %s\n' "$path" "$RG_STATUS" >&2; exit "$RG_STATUS" ;;
  esac
done

git commit -m "feat: add global evidence requirement witnesses"
```

Expected outcome: the literal staged-path equality check passes, no matched secret value is printed, and the second focused commit succeeds.

---

### Task 3: Re-Gate The Complete Node, Obtain Claude PASS, And Push

**Files:** All four exact implementation allowlist paths; no others.

**Interfaces:**
- Consumes: the two focused implementation commits above and immutable `NODE_BASE`/Node 2A handoff values.
- Produces: one fully gated, reviewed, clean committed range pushed non-force to `origin/main`.

Run the preflight and Task 3 Steps 1-6 in one persistent coordinator shell
inside a named `tmux` session using `bash --noprofile --norc`; executing one
shell per fenced block is forbidden. Require `test -n "${TMUX:-}"` before
preflight and do not terminate the session until the outgoing receipt has been
published and independently verified. If that shell or tmux session is lost
after the push begins and before receipt publication completes, do not rerun
preflight against the moved remote base; stop with a hard manual-publication
classification requirement. This hard stop applies only when the accepted
process state is lost. While the same coordinator shell remains alive,
transient receipt-only remote-observation failures retry every five seconds
without terminating that shell or attempting another push. A review-fix
commit invalidates every Task 3 marker; after such a commit, terminate that
shell, start a fresh coordinator shell, rerun the immutable preflight, and
repeat Task 3 from Step 1. No marker from an earlier `HEAD` may be reused.

- [ ] **Step 1: Verify the exact committed range and immutable prerequisite**

```bash
set -euo pipefail
test -n "${TMUX:-}"
: "${NODE_BASE:?NODE_BASE must remain exported from preflight}"
: "${NODE2A_PREREQ_SHA:?NODE2A_PREREQ_SHA must remain exported from preflight}"
: "${NODE2A_PASS_RECEIPT_PATH:?NODE2A_PASS_RECEIPT_PATH must remain exported from preflight}"
: "${NODE2A_PASS_RECEIPT_SHA256:?NODE2A_PASS_RECEIPT_SHA256 must remain exported from preflight}"
: "${INITIAL_NODE2A_RECEIPT_EVIDENCE:?initial receipt evidence must remain set from preflight}"

test "$(type -t validate_node2a_pass_receipt)" = function
NODE2A_RECEIPT_EVIDENCE="$(validate_node2a_pass_receipt)"
test "$NODE2A_RECEIPT_EVIDENCE" = "$INITIAL_NODE2A_RECEIPT_EVIDENCE"

declare -p NODE2A_PREREQ_PATHS 2>/dev/null | rg -q '^declare -ar NODE2A_PREREQ_PATHS='
test "$(printf '%s\n' "${NODE2A_PREREQ_PATHS[@]}")" = $'src/polymarket_alpha_lab/team_evidence_aggregation_codec.py\nsrc/polymarket_alpha_lab/team_evidence_aggregation_temporal.py\nsrc/polymarket_alpha_lab/team_evidence_aggregation_types.py\ntests/test_team_evidence_aggregation_codec.py\ntests/test_team_evidence_aggregation_temporal.py\ntests/test_team_evidence_aggregation_types.py'

git cat-file -e "$NODE2A_PREREQ_SHA^{commit}"
git merge-base --is-ancestor "$NODE2A_PREREQ_SHA" "$NODE_BASE"
git merge-base --is-ancestor "$NODE_BASE" HEAD
git diff --quiet "$NODE2A_PREREQ_SHA..$NODE_BASE" -- "${NODE2A_PREREQ_PATHS[@]}"
test "$(git rev-list --count "$NODE_BASE..HEAD")" -ge 2
test -z "$(git rev-list --merges "$NODE_BASE..HEAD")"

test "$(git diff --name-only "$NODE_BASE..HEAD" | LC_ALL=C sort)" = $'src/polymarket_alpha_lab/team_evidence_aggregation_allocation.py\nsrc/polymarket_alpha_lab/team_evidence_aggregation_witness.py\ntests/test_team_evidence_aggregation_allocation.py\ntests/test_team_evidence_aggregation_witness.py'
test "$(git diff --diff-filter=ACMR --name-only "$NODE_BASE..HEAD" | LC_ALL=C sort)" = $'src/polymarket_alpha_lab/team_evidence_aggregation_allocation.py\nsrc/polymarket_alpha_lab/team_evidence_aggregation_witness.py\ntests/test_team_evidence_aggregation_allocation.py\ntests/test_team_evidence_aggregation_witness.py'
test -z "$(git diff --diff-filter=DTUXB --name-only "$NODE_BASE..HEAD")"
git diff --check "$NODE_BASE..HEAD"
git diff --quiet
git diff --cached --quiet
test -z "$(git status --porcelain=v1 --untracked-files=all)"

NODE2B_RANGE_GATE_HEAD="$(git rev-parse HEAD)"
NODE2B_RANGE_GATE_STATUS=pass
export NODE2B_RANGE_GATE_HEAD NODE2B_RANGE_GATE_STATUS
readonly NODE2B_RANGE_GATE_HEAD NODE2B_RANGE_GATE_STATUS
```

Expected outcome: exact literal range equality succeeds, all four files are additions/modifications rather than deletions or type changes, the range has at least the two focused commits and no merge commit, diff hygiene passes, and the worktree/index are clean.

- [ ] **Step 2: Run exact static, focused, compile, full-suite, and CodeGraph gates**

Run in this exact order:

```bash
set -euo pipefail
: "${NODE2B_RANGE_GATE_HEAD:?Step 1 range-gate HEAD is required}"
: "${NODE2B_RANGE_GATE_STATUS:?Step 1 range-gate status is required}"
test "$NODE2B_RANGE_GATE_STATUS" = pass
test "$(git rev-parse HEAD)" = "$NODE2B_RANGE_GATE_HEAD"

.venv/bin/python -m pytest -q \
  tests/test_team_evidence_aggregation_witness.py::test_node_2b_child_local_ast_import_export_forbidden_surface_and_line_size_gate

.venv/bin/python -m pytest -q \
  tests/test_team_evidence_aggregation_allocation.py \
  tests/test_team_evidence_aggregation_witness.py

.venv/bin/python -m pytest -q \
  tests/test_phase1_live_surface_guard.py \
  tests/test_database_persistence_iron_rule.py \
  tests/test_supabase_durable_only_scope.py

.venv/bin/python -m compileall -q src tests
.venv/bin/python -m pytest -q
codegraph sync .
codegraph node src/polymarket_alpha_lab/team_evidence_aggregation_allocation.py >/dev/null
codegraph node src/polymarket_alpha_lab/team_evidence_aggregation_witness.py >/dev/null
git diff --check "$NODE_BASE..HEAD"
git diff --quiet
git diff --cached --quiet
test -z "$(git status --porcelain=v1 --untracked-files=all)"

NODE2B_TEST_GATE_HEAD="$(git rev-parse HEAD)"
test "$NODE2B_TEST_GATE_HEAD" = "$NODE2B_RANGE_GATE_HEAD"
NODE2B_FOCUSED_TESTS_STATUS=pass
NODE2B_FULL_PYTEST_STATUS=pass
NODE2B_COMPILEALL_STATUS=pass
NODE2B_CODEGRAPH_STATUS=pass
NODE2B_STATIC_GATES_STATUS=pass
export NODE2B_TEST_GATE_HEAD NODE2B_FOCUSED_TESTS_STATUS \
  NODE2B_FULL_PYTEST_STATUS NODE2B_COMPILEALL_STATUS \
  NODE2B_CODEGRAPH_STATUS NODE2B_STATIC_GATES_STATUS
readonly NODE2B_TEST_GATE_HEAD NODE2B_FOCUSED_TESTS_STATUS \
  NODE2B_FULL_PYTEST_STATUS NODE2B_COMPILEALL_STATUS \
  NODE2B_CODEGRAPH_STATUS NODE2B_STATIC_GATES_STATUS
```

Expected outcomes, all mandatory:

- child-local static gate exits `0` and enforces exact AST/import/export/forbidden-surface/line-size rules;
- both focused test modules exit `0`, including the exhaustive oracle;
- repository Phase 1 safety/persistence guards exit `0`;
- compileall exits `0` without syntax errors;
- full pytest exits `0` with no ignored unrelated failure;
- CodeGraph sync and both indexed-node reads exit `0`;
- committed diff hygiene passes and the worktree remains clean.

- [ ] **Step 3: Run exact full-range secret, readonly-boundary, and persistence scans**

These scans inspect only added lines in the exact committed range. All `rg` calls use explicit status semantics: `0` means a match that must be failed or classified, `1` means clean, and any status greater than `1` means the command failed and the gate fails. Quiet scans never print matched values.

```bash
set -euo pipefail
: "${NODE2B_TEST_GATE_HEAD:?Step 2 test-gate HEAD is required}"
: "${NODE2B_FOCUSED_TESTS_STATUS:?focused-test status is required}"
: "${NODE2B_FULL_PYTEST_STATUS:?full-pytest status is required}"
: "${NODE2B_COMPILEALL_STATUS:?compileall status is required}"
: "${NODE2B_CODEGRAPH_STATUS:?CodeGraph status is required}"
: "${NODE2B_STATIC_GATES_STATUS:?static-gate status is required}"
test "$NODE2B_FOCUSED_TESTS_STATUS" = pass
test "$NODE2B_FULL_PYTEST_STATUS" = pass
test "$NODE2B_COMPILEALL_STATUS" = pass
test "$NODE2B_CODEGRAPH_STATUS" = pass
test "$NODE2B_STATIC_GATES_STATUS" = pass
test "$(git rev-parse HEAD)" = "$NODE2B_TEST_GATE_HEAD"

RANGE_PATHS_TEXT="$(git diff --name-only "$NODE_BASE..$NODE2B_TEST_GATE_HEAD")"
test -n "$RANGE_PATHS_TEXT"
mapfile -t RANGE_PATHS <<< "$RANGE_PATHS_TEXT"
test "${#RANGE_PATHS[@]}" -eq 4

SENSITIVE_FIELD_PATHS=()
READONLY_CLASSIFICATION_PATHS=()
PERSISTENCE_CLASSIFICATION_PATHS=()

for path in "${RANGE_PATHS[@]}"; do
  ADDED_FOR_PATH="$(git diff --unified=0 "$NODE_BASE..$NODE2B_TEST_GATE_HEAD" -- "$path" | sed -n '/^+++ /d; /^+/s/^+//p')"

  if rg -q '(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|(^|[^[:alnum:]_])sk-[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}|postgres(ql)?://[^[:space:]/]+:[^[:space:]@]+@)' <<< "$ADDED_FOR_PATH"; then
    RG_STATUS=0
  else
    RG_STATUS=$?
  fi
  case "$RG_STATUS" in
    0) printf 'credential-shaped range addition in %s\n' "$path" >&2; exit 1 ;;
    1) ;;
    *) printf 'credential-shaped range scan failed for %s with rg status %s\n' "$path" "$RG_STATUS" >&2; exit "$RG_STATUS" ;;
  esac

  if rg -qi '\b(api[_-]?key|secret|token|password|passwd|cookie|authorization|bearer|private[_ -]?key|seed phrase|mnemonic|wallet|account[_ -]?(id|address))\b' <<< "$ADDED_FOR_PATH"; then
    RG_STATUS=0
  else
    RG_STATUS=$?
  fi
  case "$RG_STATUS" in
    0) SENSITIVE_FIELD_PATHS+=("$path") ;;
    1) ;;
    *) printf 'sensitive-field range scan failed for %s with rg status %s\n' "$path" "$RG_STATUS" >&2; exit "$RG_STATUS" ;;
  esac

  if rg -qi '\b(live trading|order submission|submit order|cancel order|replace order|sign order|wallet|private key|hosted account|account authentication|exchange mutation|order mutation)\b' <<< "$ADDED_FOR_PATH"; then
    RG_STATUS=0
  else
    RG_STATUS=$?
  fi
  case "$RG_STATUS" in
    0) READONLY_CLASSIFICATION_PATHS+=("$path") ;;
    1) ;;
    *) printf 'readonly-boundary range scan failed for %s with rg status %s\n' "$path" "$RG_STATUS" >&2; exit "$RG_STATUS" ;;
  esac

  if rg -qi '\b(sqlite|duckdb|redis|mongodb|sqlalchemy|jsonl|file-backed|postgres|supabase|dsn|validate_local_postgres_dsn)\b' <<< "$ADDED_FOR_PATH"; then
    RG_STATUS=0
  else
    RG_STATUS=$?
  fi
  case "$RG_STATUS" in
    0) PERSISTENCE_CLASSIFICATION_PATHS+=("$path") ;;
    1) ;;
    *) printf 'persistence range scan failed for %s with rg status %s\n' "$path" "$RG_STATUS" >&2; exit "$RG_STATUS" ;;
  esac
done

printf 'sensitive-field paths requiring redacted classification:\n'
printf '  %s\n' "${SENSITIVE_FIELD_PATHS[@]}"
printf 'readonly-boundary paths requiring negative-test classification:\n'
printf '  %s\n' "${READONLY_CLASSIFICATION_PATHS[@]}"
printf 'persistence paths requiring pure-node/negative-test classification:\n'
printf '  %s\n' "${PERSISTENCE_CLASSIFICATION_PATHS[@]}"

git diff --check "$NODE_BASE..$NODE2B_TEST_GATE_HEAD"
git diff --quiet
git diff --cached --quiet
test -z "$(git status --porcelain=v1 --untracked-files=all)"

SENSITIVE_FIELD_PATHS_TEXT='<none>'
if ((${#SENSITIVE_FIELD_PATHS[@]})); then
  SENSITIVE_FIELD_PATHS_TEXT="$(printf '%s\n' "${SENSITIVE_FIELD_PATHS[@]}")"
fi
READONLY_CLASSIFICATION_PATHS_TEXT='<none>'
if ((${#READONLY_CLASSIFICATION_PATHS[@]})); then
  READONLY_CLASSIFICATION_PATHS_TEXT="$(printf '%s\n' "${READONLY_CLASSIFICATION_PATHS[@]}")"
fi
PERSISTENCE_CLASSIFICATION_PATHS_TEXT='<none>'
if ((${#PERSISTENCE_CLASSIFICATION_PATHS[@]})); then
  PERSISTENCE_CLASSIFICATION_PATHS_TEXT="$(printf '%s\n' "${PERSISTENCE_CLASSIFICATION_PATHS[@]}")"
fi

GATED_HEAD="$(git rev-parse HEAD)"
test "$GATED_HEAD" = "$NODE2B_TEST_GATE_HEAD"
NODE2B_SECRET_SCAN_STATUS=pass
NODE2B_CLEAN_WORKTREE_STATUS=pass
NODE2B_GATE_EVIDENCE="$(
  printf '%s\n' \
    "gated_head=$GATED_HEAD" \
    "range_gate=$NODE2B_RANGE_GATE_STATUS" \
    "focused_tests=$NODE2B_FOCUSED_TESTS_STATUS" \
    "full_pytest=$NODE2B_FULL_PYTEST_STATUS" \
    "compileall=$NODE2B_COMPILEALL_STATUS" \
    "codegraph_sync=$NODE2B_CODEGRAPH_STATUS" \
    "static_gates=$NODE2B_STATIC_GATES_STATUS" \
    "secret_scan=$NODE2B_SECRET_SCAN_STATUS" \
    "clean_worktree=$NODE2B_CLEAN_WORKTREE_STATUS" \
    'exact_manifest_begin' \
    "$RANGE_PATHS_TEXT" \
    'exact_manifest_end' \
    'sensitive_field_paths_begin' \
    "$SENSITIVE_FIELD_PATHS_TEXT" \
    'sensitive_field_paths_end' \
    'readonly_classification_paths_begin' \
    "$READONLY_CLASSIFICATION_PATHS_TEXT" \
    'readonly_classification_paths_end' \
    'persistence_classification_paths_begin' \
    "$PERSISTENCE_CLASSIFICATION_PATHS_TEXT" \
    'persistence_classification_paths_end'
)"
export GATED_HEAD NODE2B_SECRET_SCAN_STATUS NODE2B_CLEAN_WORKTREE_STATUS \
  NODE2B_GATE_EVIDENCE
readonly GATED_HEAD NODE2B_SECRET_SCAN_STATUS NODE2B_CLEAN_WORKTREE_STATUS \
  NODE2B_GATE_EVIDENCE
```

Expected outcome: the high-confidence credential-shaped scan is clean and emits no matched value. Any sensitive, readonly, or persistence term appears only in child-scope negative assertions; classify each flagged path in the Claude packet. Any production behavior or positive authorization match fails and must be removed. Persistence classification must state that this child performs no persistence and that future persistence is local Supabase/Postgres-only with `validate_local_postgres_dsn` invoked before adapter/connection construction.

- [ ] **Step 4: Run the exact local Claude Code full-range review command**

The review packet must include the approved design, this plan, exact four-path manifest, complete `NODE_BASE..HEAD` patch, immutable Node 2A SHA/receipt validation, child-local gate, focused/static/full test results, compileall, CodeGraph sync, diff hygiene, clean-worktree result, and redacted scan classifications. The reviewer must assess integer largest remainder, stage order, Alabama regression, exact allocation recomputation, edge bound timing, global severity objective, lexical optimum, oracle coverage, hard flags, purity, and future local-Postgres wording.

Run exactly:

```bash
set -euo pipefail
: "${NODE_BASE:?NODE_BASE is required}"
: "${NODE2A_PREREQ_SHA:?NODE2A_PREREQ_SHA is required}"
: "${INITIAL_NODE2A_RECEIPT_EVIDENCE:?INITIAL_NODE2A_RECEIPT_EVIDENCE is required}"
: "${GATED_HEAD:?Step 3 GATED_HEAD is required}"
: "${NODE2B_GATE_EVIDENCE:?Step 3 gate evidence is required}"
: "${NODE2B_FOCUSED_TESTS_STATUS:?focused-test status is required}"
: "${NODE2B_FULL_PYTEST_STATUS:?full-pytest status is required}"
: "${NODE2B_COMPILEALL_STATUS:?compileall status is required}"
: "${NODE2B_CODEGRAPH_STATUS:?CodeGraph status is required}"
: "${NODE2B_STATIC_GATES_STATUS:?static-gate status is required}"
: "${NODE2B_CLEAN_WORKTREE_STATUS:?clean-worktree status is required}"
test "$NODE2B_FOCUSED_TESTS_STATUS" = pass
test "$NODE2B_FULL_PYTEST_STATUS" = pass
test "$NODE2B_COMPILEALL_STATUS" = pass
test "$NODE2B_CODEGRAPH_STATUS" = pass
test "$NODE2B_STATIC_GATES_STATUS" = pass
test "$NODE2B_CLEAN_WORKTREE_STATUS" = pass
test -z "${ACCEPTED_REVIEW_HEAD+x}"
test "$(type -t validate_node2a_pass_receipt)" = function
command -v claude >/dev/null
command -v jq >/dev/null
command -v tar >/dev/null
command -v timeout >/dev/null

NODE2A_RECEIPT_EVIDENCE="$(validate_node2a_pass_receipt)"
test "$NODE2A_RECEIPT_EVIDENCE" = "$INITIAL_NODE2A_RECEIPT_EVIDENCE"

declare -p NODE2A_PREREQ_PATHS 2>/dev/null | rg -q '^declare -ar NODE2A_PREREQ_PATHS='
test "$(printf '%s\n' "${NODE2A_PREREQ_PATHS[@]}")" = $'src/polymarket_alpha_lab/team_evidence_aggregation_codec.py\nsrc/polymarket_alpha_lab/team_evidence_aggregation_temporal.py\nsrc/polymarket_alpha_lab/team_evidence_aggregation_types.py\ntests/test_team_evidence_aggregation_codec.py\ntests/test_team_evidence_aggregation_temporal.py\ntests/test_team_evidence_aggregation_types.py'
git diff --quiet "$NODE2A_PREREQ_SHA..$NODE_BASE" -- "${NODE2A_PREREQ_PATHS[@]}"

EXPECTED_NODE2B_PATHS=$'src/polymarket_alpha_lab/team_evidence_aggregation_allocation.py\nsrc/polymarket_alpha_lab/team_evidence_aggregation_witness.py\ntests/test_team_evidence_aggregation_allocation.py\ntests/test_team_evidence_aggregation_witness.py'
REVIEW_HEAD="$GATED_HEAD"
test "$(git rev-parse HEAD)" = "$REVIEW_HEAD"
ACTUAL_NODE2B_PATHS="$(git diff --name-only "$NODE_BASE..$REVIEW_HEAD" | LC_ALL=C sort)"
test "$ACTUAL_NODE2B_PATHS" = "$EXPECTED_NODE2B_PATHS"
git diff --quiet
git diff --cached --quiet
test -z "$(git status --porcelain=v1 --untracked-files=all)"

REVIEW_TMP_DIR="$(mktemp -d /home/ubuntu/test-sandbox/tmp/node2b-claude-review.XXXXXX)"
readonly REVIEW_HEAD REVIEW_TMP_DIR
REVIEW_SNAPSHOT_DIR="$REVIEW_TMP_DIR/snapshot"
REVIEW_PROMPT_PATH="$REVIEW_TMP_DIR/prompt.txt"
REVIEW_STREAM_PATH="$REVIEW_TMP_DIR/stream.jsonl"
REVIEW_STDERR_PATH="$REVIEW_TMP_DIR/stderr.txt"
REVIEW_REPORT_PATH="$REVIEW_TMP_DIR/report.md"
readonly REVIEW_SNAPSHOT_DIR REVIEW_PROMPT_PATH REVIEW_STREAM_PATH REVIEW_STDERR_PATH REVIEW_REPORT_PATH

cleanup_node2b_review_tmp() {
  chmod -R u+w -- "$REVIEW_SNAPSHOT_DIR" 2>/dev/null || true
  rm -rf -- "$REVIEW_TMP_DIR"
}
trap cleanup_node2b_review_tmp EXIT

mkdir -- "$REVIEW_SNAPSHOT_DIR"
git archive "$REVIEW_HEAD" | tar -x -C "$REVIEW_SNAPSHOT_DIR"
chmod -R a-w -- "$REVIEW_SNAPSHOT_DIR"
test ! -w "$REVIEW_SNAPSHOT_DIR"

{
  printf '%s\n' \
    'Read-only Node 2B full-range review. Do not modify, create, or delete files.' \
    'Your current working directory is a read-only git-archive snapshot of REVIEW_HEAD. Read only this snapshot; never inspect the mutable implementation worktree.' \
    'Fast mode is forbidden.' \
    "NODE_BASE=$NODE_BASE" \
    "REVIEW_HEAD=$REVIEW_HEAD" \
    "NODE2A_PREREQ_SHA=$NODE2A_PREREQ_SHA" \
    'The exact six-path Node 2A surface is byte-unchanged from NODE2A_PREREQ_SHA through NODE_BASE.' \
    'Repository rules: AGENTS.md' \
    'Normative design: docs/superpowers/specs/2026-07-13-team-evidence-aggregation-core-design.md' \
    'Executable plan: docs/superpowers/plans/2026-07-13-team-evidence-aggregation-independence-correlation-requirement-witness.md' \
    'Quality gates: docs/quality/phase-1-development-node-quality-gates.md' \
    'Use only Read, Glob, and Grep to inspect those repository files. Do not use any write-capable tool.' \
    'Changed paths are exactly the four-path implementation allowlist.' \
    'Node 2A content-addressed PASS receipt validation evidence follows on the next line.' \
    "$NODE2A_RECEIPT_EVIDENCE" \
    'Actual Step 1-3 gate evidence and exact classification path sets follow.' \
    "$NODE2B_GATE_EVIDENCE" \
    'Assess every sensitive-field, readonly-boundary, and persistence classification; do not assume a flagged path is acceptable.' \
    'Phase 1 is paper_only=True, report_only=True, readonly=True with no live/auth/wallet/order surface.' \
    'This child performs no persistence. Future persistence is local Supabase/Postgres only, and every raw DSN must pass validate_local_postgres_dsn before any adapter or connection construction.' \
    'Review for correctness, design fidelity, deterministic arithmetic/matching, TDD coverage, safety, and regression risk.' \
    'Return findings first. The exact final nonblank line must be VERDICT: PASS or VERDICT: REVISE.' \
    '' \
    'Exact committed patch follows:'
  git diff --no-ext-diff --unified=80 "$NODE_BASE..$REVIEW_HEAD"
} > "$REVIEW_PROMPT_PATH"

set +e
(
  set -e
  cd -- "$REVIEW_SNAPSHOT_DIR"
  timeout --signal=TERM --kill-after=10s 330s \
    claude --print \
      --input-format text \
      --output-format stream-json \
      --include-partial-messages \
      --verbose \
      --bare \
      --safe-mode \
      --model claude-opus-4-8 \
      --effort max \
      --tools Read,Glob,Grep \
      --permission-mode dontAsk \
      --no-session-persistence \
      --system-prompt 'You are a read-only senior engineering reviewer. Use only Read, Glob, and Grep inside the immutable current-directory snapshot. Return findings first and the exact required verdict. Do not modify, create, or delete files.' \
      < "$REVIEW_PROMPT_PATH" \
      > "$REVIEW_STREAM_PATH" \
      2> "$REVIEW_STDERR_PATH"
)
REVIEW_STATUS=$?
set -e

REVIEW_PARSE_STATUS=0
if jq -j '
  select(
    .type == "stream_event"
    and .event.type == "content_block_delta"
    and .event.delta.type == "text_delta"
  ) | .event.delta.text
' "$REVIEW_STREAM_PATH" > "$REVIEW_REPORT_PATH"; then
  REVIEW_PARSE_STATUS=0
else
  REVIEW_PARSE_STATUS=$?
fi

if [ -s "$REVIEW_REPORT_PATH" ]; then
  cat "$REVIEW_REPORT_PATH"
fi
if [ -s "$REVIEW_STDERR_PATH" ]; then
  printf '\nClaude stderr diagnostics (credential shapes redacted):\n' >&2
  sed -E \
    -e 's/(gh[pousr]_|github_pat_|sk-)[A-Za-z0-9_-]{10,}/[REDACTED_TOKEN]/g' \
    -e 's#postgres(ql)?://[^[:space:]]+#[REDACTED_POSTGRES_DSN]#g' \
    -e 's#eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}#[REDACTED_JWT]#g' \
    "$REVIEW_STDERR_PATH" >&2
fi

NONBLANK_REVIEW_OUTPUT="$(sed -n '/[^[:space:]]/p' "$REVIEW_REPORT_PATH")"
FINAL_REVIEW_LINE=''
if [ -n "$NONBLANK_REVIEW_OUTPUT" ]; then
  FINAL_REVIEW_LINE="$(printf '%s\n' "$NONBLANK_REVIEW_OUTPUT" | tail -n 1)"
fi

REVIEW_GATE_RESULT=error
if [ "$REVIEW_STATUS" -ne 0 ]; then
  REVIEW_GATE_RESULT=error
elif [ "$REVIEW_PARSE_STATUS" -ne 0 ]; then
  REVIEW_GATE_RESULT=error
elif [ -z "$NONBLANK_REVIEW_OUTPUT" ]; then
  REVIEW_GATE_RESULT=error
elif [ "$FINAL_REVIEW_LINE" = 'VERDICT: REVISE' ]; then
  REVIEW_GATE_RESULT=revise
elif [ "$FINAL_REVIEW_LINE" != 'VERDICT: PASS' ]; then
  REVIEW_GATE_RESULT=error
elif [ "$(git rev-parse HEAD)" != "$REVIEW_HEAD" ]; then
  REVIEW_GATE_RESULT=error
elif ! git diff --quiet; then
  REVIEW_GATE_RESULT=error
elif ! git diff --cached --quiet; then
  REVIEW_GATE_RESULT=error
elif [ -n "$(git status --porcelain=v1 --untracked-files=all)" ]; then
  REVIEW_GATE_RESULT=error
else
  REVIEW_GATE_RESULT=pass
fi

cleanup_node2b_review_tmp
trap - EXIT

NODE2B_REVIEW_GATE_RESULT="$REVIEW_GATE_RESULT"
export NODE2B_REVIEW_GATE_RESULT
if [ "$NODE2B_REVIEW_GATE_RESULT" = pass ]; then
  ACCEPTED_REVIEW_HEAD="$REVIEW_HEAD"
  ACCEPTED_REVIEW_MODEL=claude-opus-4-8
  ACCEPTED_REVIEW_EFFORT=max
  ACCEPTED_REVIEW_READ_ONLY=true
  ACCEPTED_REVIEW_FAST_MODE=false
  ACCEPTED_REVIEW_EXIT_STATUS="$REVIEW_STATUS"
  ACCEPTED_REVIEW_FINAL_LINE="$FINAL_REVIEW_LINE"
  export ACCEPTED_REVIEW_HEAD ACCEPTED_REVIEW_MODEL ACCEPTED_REVIEW_EFFORT \
    ACCEPTED_REVIEW_READ_ONLY ACCEPTED_REVIEW_FAST_MODE \
    ACCEPTED_REVIEW_EXIT_STATUS ACCEPTED_REVIEW_FINAL_LINE
  readonly NODE2B_REVIEW_GATE_RESULT ACCEPTED_REVIEW_HEAD \
    ACCEPTED_REVIEW_MODEL ACCEPTED_REVIEW_EFFORT ACCEPTED_REVIEW_READ_ONLY \
    ACCEPTED_REVIEW_FAST_MODE ACCEPTED_REVIEW_EXIT_STATUS \
    ACCEPTED_REVIEW_FINAL_LINE
  printf 'accepted reviewed HEAD: %s\n' "$ACCEPTED_REVIEW_HEAD"
elif [ "$NODE2B_REVIEW_GATE_RESULT" = revise ]; then
  printf 'Claude returned VERDICT: REVISE; Step 5 is required and Step 6 remains blocked.\n' >&2
else
  printf 'Claude review errored or returned an invalid verdict; Step 6 remains blocked.\n' >&2
fi
```

Acceptance is strict: `NODE2B_REVIEW_GATE_RESULT=pass` is published only when
the timeout-wrapped Claude command exit status is `0`, the extracted text-delta
report is nonempty, its exact final nonblank line is `VERDICT: PASS`, the
reviewed SHA still equals `GATED_HEAD`, and the worktree/index remain clean.
The report is printed before classification, and stderr is printed only after
credential-shape redaction, so `VERDICT: REVISE` remains actionable without
authorizing Step 6. `PASS` elsewhere, malformed stream JSON, missing or trailing
verdict text, timeout, another model/effort/tool mode, unavailable Claude, or
post-review repository movement leaves every `ACCEPTED_REVIEW_*` variable
unset. There is no fallback reviewer.

- [ ] **Step 5: Handle any post-review fix as a new commit and restart the complete gate**

Do not amend or squash a reviewed commit. For every review finding:

1. Add or tighten a failing focused test first and run it to verify the intended RED failure. For a non-behavioral finding, first reproduce it with the narrowest executable static/gate command instead.
2. Make the smallest allowlisted production/test correction and run the focused test to GREEN.
3. Stage only explicit allowlisted fix paths, then run the exact subset, hygiene, and secret gate below.
4. Create a new commit with message `fix: address Node 2B review findings`.
5. Terminate the current coordinator shell. Start a fresh shell, re-export the immutable Node 2A handoff values, rerun the preflight, and restart Task 3 at Step 1. This invalidates every old range/test/scan/review marker.
6. Submit the complete updated `NODE_BASE..HEAD` range to a fresh Claude invocation using the exact Step 4 command. A review of only the fix commit is invalid. Do not enter Step 6 unless the fresh invocation publishes `NODE2B_REVIEW_GATE_RESULT=pass`, exact `ACCEPTED_REVIEW_HEAD`, exit status `0`, and exact final line `VERDICT: PASS`.

```bash
set -euo pipefail
STAGED_FIX_PATHS_TEXT="$(git diff --cached --name-only | LC_ALL=C sort)"
test -n "$STAGED_FIX_PATHS_TEXT"
while IFS= read -r path; do
  case "$path" in
    src/polymarket_alpha_lab/team_evidence_aggregation_allocation.py | \
    src/polymarket_alpha_lab/team_evidence_aggregation_witness.py | \
    tests/test_team_evidence_aggregation_allocation.py | \
    tests/test_team_evidence_aggregation_witness.py) ;;
    *) printf 'review fix staged outside Node 2B allowlist: %s\n' "$path" >&2; exit 1 ;;
  esac
done <<< "$STAGED_FIX_PATHS_TEXT"

git diff --cached --check
while IFS= read -r path; do
  STAGED_ADDED_FOR_PATH="$(git diff --cached --unified=0 -- "$path" | sed -n '/^+++ /d; /^+/s/^+//p')"
  if rg -q '(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|(^|[^[:alnum:]_])sk-[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}|postgres(ql)?://[^[:space:]/]+:[^[:space:]@]+@)' <<< "$STAGED_ADDED_FOR_PATH"; then
    RG_STATUS=0
  else
    RG_STATUS=$?
  fi
  case "$RG_STATUS" in
    0) printf 'credential-shaped review-fix addition in %s\n' "$path" >&2; exit 1 ;;
    1) ;;
    *) printf 'review-fix secret scan failed for %s with rg status %s\n' "$path" "$RG_STATUS" >&2; exit "$RG_STATUS" ;;
  esac
done <<< "$STAGED_FIX_PATHS_TEXT"

git commit -m "fix: address Node 2B review findings"
```

All findings from one Claude report may be corrected in one focused fix commit.
A later report that requests another correction requires another new commit and
another fresh-shell full-range gate.

No post-review modification may proceed to push without a new commit, a complete range re-gate, and a fresh exact-final-line PASS.

- [ ] **Step 6: Verify the remote race, push without force, and verify remote HEAD**

Run the publication phase immediately after the successful full-range review.
It uses one explicit push endpoint for observation, push, and verification, and
it never rebases or otherwise mutates the reviewed range:

```bash
set -euo pipefail
: "${NODE_BASE:?NODE_BASE is required before push}"
: "${GATED_HEAD:?GATED_HEAD is required before push}"
: "${NODE2B_REVIEW_GATE_RESULT:?review-gate result is required before push}"
: "${ACCEPTED_REVIEW_HEAD:?accepted reviewed HEAD is required before push}"
: "${ACCEPTED_REVIEW_MODEL:?accepted review model is required before push}"
: "${ACCEPTED_REVIEW_EFFORT:?accepted review effort is required before push}"
: "${ACCEPTED_REVIEW_READ_ONLY:?accepted read-only marker is required before push}"
: "${ACCEPTED_REVIEW_FAST_MODE:?accepted fast-mode marker is required before push}"
: "${ACCEPTED_REVIEW_EXIT_STATUS:?accepted review status is required before push}"
: "${ACCEPTED_REVIEW_FINAL_LINE:?accepted final verdict is required before push}"
test "$NODE2B_REVIEW_GATE_RESULT" = pass
test "$ACCEPTED_REVIEW_HEAD" = "$GATED_HEAD"
test "$ACCEPTED_REVIEW_MODEL" = claude-opus-4-8
test "$ACCEPTED_REVIEW_EFFORT" = max
test "$ACCEPTED_REVIEW_READ_ONLY" = true
test "$ACCEPTED_REVIEW_FAST_MODE" = false
test "$ACCEPTED_REVIEW_EXIT_STATUS" = 0
test "$ACCEPTED_REVIEW_FINAL_LINE" = 'VERDICT: PASS'
test "$NODE2B_FOCUSED_TESTS_STATUS" = pass
test "$NODE2B_FULL_PYTEST_STATUS" = pass
test "$NODE2B_COMPILEALL_STATUS" = pass
test "$NODE2B_CODEGRAPH_STATUS" = pass
test "$NODE2B_STATIC_GATES_STATUS" = pass
test "$NODE2B_CLEAN_WORKTREE_STATUS" = pass
test -z "${NODE2B_PREREQ_SHA+x}"
test -z "${NODE2B_PASS_RECEIPT_SHA256+x}"
test -z "$(git status --porcelain=v1 --untracked-files=all)"
git diff --quiet
git diff --cached --quiet
LOCAL_HEAD="$(git rev-parse HEAD)"
test "$LOCAL_HEAD" = "$ACCEPTED_REVIEW_HEAD"
test "$(git diff --name-only "$NODE_BASE..$LOCAL_HEAD" | LC_ALL=C sort)" = $'src/polymarket_alpha_lab/team_evidence_aggregation_allocation.py\nsrc/polymarket_alpha_lab/team_evidence_aggregation_witness.py\ntests/test_team_evidence_aggregation_allocation.py\ntests/test_team_evidence_aggregation_witness.py'

COMMON_GIT_DIR="$(git rev-parse --git-common-dir)"
GIT_AUTH=(-c credential.helper= -c "credential.helper=store --file=$COMMON_GIT_DIR/github-credentials")
REMOTE_ENDPOINT="$(git remote get-url --push --all origin)"
test -n "$REMOTE_ENDPOINT"
test "${REMOTE_ENDPOINT//$'\n'/}" = "$REMOTE_ENDPOINT"
readonly REMOTE_ENDPOINT

observe_remote_main() {
  local attempt first_line first_sha first_ref fetched_sha second_line second_sha second_ref
  for attempt in 1 2 3; do
    if ! first_line="$(GIT_TERMINAL_PROMPT=0 git "${GIT_AUTH[@]}" ls-remote --exit-code "$REMOTE_ENDPOINT" refs/heads/main)"; then
      continue
    fi
    if [ -z "$first_line" ] || [ "${first_line//$'\n'/}" != "$first_line" ] || [[ "$first_line" != *$'\t'* ]]; then
      continue
    fi
    first_sha="${first_line%%$'\t'*}"
    first_ref="${first_line#*$'\t'}"
    if [[ ! "$first_sha" =~ ^[0-9a-f]{40}$ ]] || [ "$first_ref" != refs/heads/main ]; then
      continue
    fi

    if ! GIT_TERMINAL_PROMPT=0 git "${GIT_AUTH[@]}" fetch --no-tags --no-recurse-submodules "$REMOTE_ENDPOINT" refs/heads/main >/dev/null; then
      continue
    fi
    if ! fetched_sha="$(git rev-parse 'FETCH_HEAD^{commit}')"; then
      continue
    fi
    if ! second_line="$(GIT_TERMINAL_PROMPT=0 git "${GIT_AUTH[@]}" ls-remote --exit-code "$REMOTE_ENDPOINT" refs/heads/main)"; then
      continue
    fi
    if [ -z "$second_line" ] || [ "${second_line//$'\n'/}" != "$second_line" ] || [[ "$second_line" != *$'\t'* ]]; then
      continue
    fi
    second_sha="${second_line%%$'\t'*}"
    second_ref="${second_line#*$'\t'}"
    if [[ ! "$second_sha" =~ ^[0-9a-f]{40}$ ]] || [ "$second_ref" != refs/heads/main ]; then
      continue
    fi
    if [ "$first_sha" = "$fetched_sha" ] && [ "$fetched_sha" = "$second_sha" ]; then
      printf '%s\n' "$second_sha"
      return 0
    fi
  done
  return 74
}
export -f observe_remote_main
readonly -f observe_remote_main

if ! CURRENT_REMOTE="$(observe_remote_main)"; then
  printf 'could not obtain a stable pre-push remote observation; no push was performed.\n' >&2
  exit 74
fi
if [ "$CURRENT_REMOTE" != "$NODE_BASE" ]; then
  printf 'stable remote main moved before push; no rebase or push was performed. Start a fresh reviewed gate from FETCH_HEAD.\n' >&2
  exit 75
fi

set +e
GIT_TERMINAL_PROMPT=0 git "${GIT_AUTH[@]}" push \
  --no-force --no-force-with-lease --no-force-if-includes --no-follow-tags \
  --no-recurse-submodules \
  "$REMOTE_ENDPOINT" "$LOCAL_HEAD:refs/heads/main"
PUSH_STATUS=$?
set -e
PUSH_ATTEMPTED=true

POST_PUSH_OBSERVATION_STATUS=0
if REMOTE_AFTER_PUSH="$(observe_remote_main)"; then
  POST_PUSH_OBSERVATION_STATUS=0
else
  POST_PUSH_OBSERVATION_STATUS=$?
  REMOTE_AFTER_PUSH=''
fi

if [ "$POST_PUSH_OBSERVATION_STATUS" -ne 0 ]; then
  REMOTE_PUBLICATION_STATUS=indeterminate
  printf 'post-push remote observation is indeterminate; do not push again. Use only the observation-recovery block.\n' >&2
elif [ "$REMOTE_AFTER_PUSH" = "$LOCAL_HEAD" ]; then
  REMOTE_PUBLICATION_STATUS=confirmed_exact
  CONFIRMED_REMOTE_MAIN_SHA="$REMOTE_AFTER_PUSH"
  NODE2B_PREREQ_SHA="$LOCAL_HEAD"
  printf 'stable remote main equals the accepted reviewed HEAD; publication is confirmed, including a possible lost client response.\n'
elif git merge-base --is-ancestor "$LOCAL_HEAD" "$REMOTE_AFTER_PUSH"; then
  REMOTE_PUBLICATION_STATUS=published_but_superseded
  printf 'remote main contains but no longer equals the accepted reviewed HEAD; current equality-based receipt publication is blocked.\n' >&2
elif [ "$REMOTE_AFTER_PUSH" = "$NODE_BASE" ] && [ "$PUSH_STATUS" -ne 0 ]; then
  REMOTE_PUBLICATION_STATUS=not_published_observed
  printf 'remote main remains NODE_BASE after the failed push; do not retry automatically.\n' >&2
elif [ "$REMOTE_AFTER_PUSH" = "$NODE_BASE" ]; then
  REMOTE_PUBLICATION_STATUS=inconsistent_success_response
  printf 'push returned success but stable remote main remains NODE_BASE; use only the observation-recovery block.\n' >&2
else
  REMOTE_PUBLICATION_STATUS=remote_moved_or_diverged
  printf 'stable remote main neither equals nor contains the accepted reviewed HEAD; a fresh base and full review are required.\n' >&2
fi

test "$(git rev-parse HEAD)" = "$LOCAL_HEAD"
export CURRENT_REMOTE LOCAL_HEAD PUSH_STATUS PUSH_ATTEMPTED \
  POST_PUSH_OBSERVATION_STATUS REMOTE_AFTER_PUSH REMOTE_PUBLICATION_STATUS
readonly CURRENT_REMOTE LOCAL_HEAD PUSH_STATUS PUSH_ATTEMPTED
if [ "$REMOTE_PUBLICATION_STATUS" = confirmed_exact ]; then
  export CONFIRMED_REMOTE_MAIN_SHA NODE2B_PREREQ_SHA
  readonly POST_PUSH_OBSERVATION_STATUS REMOTE_AFTER_PUSH \
    REMOTE_PUBLICATION_STATUS CONFIRMED_REMOTE_MAIN_SHA NODE2B_PREREQ_SHA
fi
```

If and only if the status is `indeterminate` or
`inconsistent_success_response`, the same shell may run this observation-only
recovery block. It contains no push and may be repeated until a stable
classification is available:

```bash
set -euo pipefail
: "${PUSH_ATTEMPTED:?push-attempt marker is required}"
: "${REMOTE_PUBLICATION_STATUS:?publication status is required}"
test "$PUSH_ATTEMPTED" = true
test -z "${NODE2B_PREREQ_SHA+x}"
case "$REMOTE_PUBLICATION_STATUS" in
  indeterminate | inconsistent_success_response) ;;
  *) printf 'observation-only recovery is not permitted from status %s\n' "$REMOTE_PUBLICATION_STATUS" >&2; exit 1 ;;
esac

if RECOVERED_REMOTE="$(observe_remote_main)"; then
  POST_PUSH_OBSERVATION_STATUS=0
  REMOTE_AFTER_PUSH="$RECOVERED_REMOTE"
  if [ "$REMOTE_AFTER_PUSH" = "$LOCAL_HEAD" ]; then
    REMOTE_PUBLICATION_STATUS=confirmed_exact
    CONFIRMED_REMOTE_MAIN_SHA="$REMOTE_AFTER_PUSH"
    NODE2B_PREREQ_SHA="$LOCAL_HEAD"
    export POST_PUSH_OBSERVATION_STATUS REMOTE_AFTER_PUSH \
      REMOTE_PUBLICATION_STATUS CONFIRMED_REMOTE_MAIN_SHA NODE2B_PREREQ_SHA
    readonly POST_PUSH_OBSERVATION_STATUS REMOTE_AFTER_PUSH \
      REMOTE_PUBLICATION_STATUS CONFIRMED_REMOTE_MAIN_SHA NODE2B_PREREQ_SHA
    printf 'observation recovery confirms exact remote equality; receipt publication is now eligible.\n'
  elif git merge-base --is-ancestor "$LOCAL_HEAD" "$REMOTE_AFTER_PUSH"; then
    REMOTE_PUBLICATION_STATUS=published_but_superseded
    export POST_PUSH_OBSERVATION_STATUS REMOTE_AFTER_PUSH REMOTE_PUBLICATION_STATUS
    printf 'observation recovery found a descendant remote; equality-based receipt publication remains blocked.\n' >&2
  elif [ "$REMOTE_AFTER_PUSH" = "$NODE_BASE" ]; then
    REMOTE_PUBLICATION_STATUS=not_published_observed
    export POST_PUSH_OBSERVATION_STATUS REMOTE_AFTER_PUSH REMOTE_PUBLICATION_STATUS
    printf 'observation recovery confirms that the reviewed commit was not published; do not retry automatically.\n' >&2
  else
    REMOTE_PUBLICATION_STATUS=remote_moved_or_diverged
    export POST_PUSH_OBSERVATION_STATUS REMOTE_AFTER_PUSH REMOTE_PUBLICATION_STATUS
    printf 'observation recovery found unrelated remote movement; a fresh full gate is required.\n' >&2
  fi
else
  POST_PUSH_OBSERVATION_STATUS=$?
  REMOTE_PUBLICATION_STATUS=indeterminate
  export POST_PUSH_OBSERVATION_STATUS REMOTE_PUBLICATION_STATUS
  printf 'remote observation remains indeterminate; no receipt and no second push are permitted.\n' >&2
fi
```

The pre-push equality is an observed race check, not an atomic lease claim.
The sole push is an ordinary non-force push. If the remote moves before that
attempt, the block exits `75` without rebasing or pushing. After the attempt,
only stable exact equality authorizes the current 15-field receipt. A descendant
is classified as published but superseded and remains receipt-ineligible under
the approved equality-based contract. Unrelated movement or unavailable stable
observation blocks publication without mutating local `HEAD` or authorizing a
second push.

Run the receipt-publication block only after
`REMOTE_PUBLICATION_STATUS=confirmed_exact`. `NODE2B_PASS_RECEIPT_PATH` must be a new
absolute path in a coordinator-controlled directory owned by the current user
and not writable by group or others. This block performs no push. If exclusive
creation fails after creating an artifact, assign a different absent path and
rerun only this block in the same accepted coordinator shell:

```bash
set -euo pipefail
: "${NODE2B_PASS_RECEIPT_PATH:?NODE2B_PASS_RECEIPT_PATH is required}"
: "${REPO_ROOT:?REPO_ROOT from immutable preflight is required}"
: "${REMOTE_ENDPOINT:?explicit remote endpoint is required}"
: "${REMOTE_PUBLICATION_STATUS:?remote publication status is required}"
: "${CONFIRMED_REMOTE_MAIN_SHA:?confirmed remote main SHA is required}"
: "${NODE2B_PREREQ_SHA:?Node 2B prerequisite SHA is required}"
test "$REMOTE_PUBLICATION_STATUS" = confirmed_exact
test "$(git rev-parse --show-toplevel)" = "$REPO_ROOT"
test "$CONFIRMED_REMOTE_MAIN_SHA" = "$NODE2B_PREREQ_SHA"
test "$NODE2B_PREREQ_SHA" = "$ACCEPTED_REVIEW_HEAD"
test "$(git rev-parse HEAD)" = "$NODE2B_PREREQ_SHA"
test "$NODE2B_REVIEW_GATE_RESULT" = pass
test "$ACCEPTED_REVIEW_EXIT_STATUS" = 0
test "$ACCEPTED_REVIEW_FINAL_LINE" = 'VERDICT: PASS'
test -z "$(git status --porcelain=v1 --untracked-files=all)"
git diff --quiet
git diff --cached --quiet

while true; do
  if RECEIPT_REMOTE_SHA="$(observe_remote_main)"; then
    if [ "$RECEIPT_REMOTE_SHA" = "$NODE2B_PREREQ_SHA" ]; then
      break
    fi
    printf 'receipt-only remote observation diverged from the accepted HEAD; retaining the coordinator shell and creating no receipt.\n' >&2
  else
    printf 'receipt-only remote observation is unstable; retaining the coordinator shell and creating no receipt.\n' >&2
  fi
  sleep 5
done

export REPO_ROOT CONFIRMED_REMOTE_MAIN_SHA NODE2B_PREREQ_SHA NODE2B_PASS_RECEIPT_PATH \
  ACCEPTED_REVIEW_HEAD ACCEPTED_REVIEW_MODEL ACCEPTED_REVIEW_EFFORT ACCEPTED_REVIEW_READ_ONLY \
  ACCEPTED_REVIEW_FAST_MODE ACCEPTED_REVIEW_EXIT_STATUS \
  ACCEPTED_REVIEW_FINAL_LINE NODE2B_FOCUSED_TESTS_STATUS \
  NODE2B_FULL_PYTEST_STATUS NODE2B_COMPILEALL_STATUS NODE2B_CODEGRAPH_STATUS \
  NODE2B_STATIC_GATES_STATUS NODE2B_CLEAN_WORKTREE_STATUS

if NODE2B_PASS_RECEIPT_SHA256="$(
  .venv/bin/python - <<'PY'
import hashlib
import json
import os
import re
import stat


def resolved_descriptor_path(descriptor: int, *, label: str) -> str:
    descriptor_link = os.readlink(f"/proc/self/fd/{descriptor}")
    if descriptor_link.endswith(" (deleted)"):
        raise SystemExit(f"Node 2B PASS receipt {label} descriptor is deleted")
    return os.path.realpath(descriptor_link)


def require_outside_repo(path: str, *, repo_root: str, label: str) -> None:
    try:
        inside_repo = os.path.commonpath((repo_root, path)) == repo_root
    except ValueError:
        raise SystemExit(f"Node 2B PASS receipt {label} path is invalid") from None
    if inside_repo:
        raise SystemExit(f"Node 2B PASS receipt {label} must resolve outside REPO_ROOT")


def open_directory_without_symlinks(path: str) -> int:
    if not os.path.isabs(path):
        raise SystemExit("Node 2B PASS receipt parent must be absolute")
    components = path.split("/")[1:]
    if not components or any(component in {"", ".", ".."} for component in components):
        raise SystemExit("Node 2B PASS receipt parent path is not canonical")

    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in components:
            next_descriptor = os.open(
                component,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=descriptor,
            )
            try:
                if not stat.S_ISDIR(os.fstat(next_descriptor).st_mode):
                    raise SystemExit(
                        "Node 2B PASS receipt parent component must be a directory",
                    )
            except BaseException:
                os.close(next_descriptor)
                raise
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def require_exact_env(name: str, expected: str) -> str:
    value = os.environ.get(name)
    if value != expected:
        raise SystemExit(f"{name} must equal {expected!r}")
    return value


def require_nonempty_env(name: str) -> str:
    value = os.environ.get(name)
    if value is None or value == "":
        raise SystemExit(f"{name} is required")
    return value


def read_exact(descriptor: int, expected_size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = expected_size
    while remaining:
        chunk = os.read(descriptor, remaining)
        if not chunk:
            raise SystemExit("Node 2B PASS receipt readback ended early")
        chunks.append(chunk)
        remaining -= len(chunk)
    if os.read(descriptor, 1) != b"":
        raise SystemExit("Node 2B PASS receipt readback has trailing bytes")
    return b"".join(chunks)


def create_receipt() -> str:
    receipt_path = require_nonempty_env("NODE2B_PASS_RECEIPT_PATH")
    node2b_head = require_nonempty_env("NODE2B_PREREQ_SHA")
    repo_root_raw = require_nonempty_env("REPO_ROOT")
    if not os.path.isabs(repo_root_raw):
        raise SystemExit("REPO_ROOT must be absolute")
    repo_root = os.path.realpath(repo_root_raw)

    accepted_head = require_exact_env("ACCEPTED_REVIEW_HEAD", node2b_head)
    confirmed_remote_main_sha = require_exact_env(
        "CONFIRMED_REMOTE_MAIN_SHA",
        node2b_head,
    )
    review_model = require_exact_env("ACCEPTED_REVIEW_MODEL", "claude-opus-4-8")
    review_effort = require_exact_env("ACCEPTED_REVIEW_EFFORT", "max")
    read_only = require_exact_env("ACCEPTED_REVIEW_READ_ONLY", "true") == "true"
    fast_mode = require_exact_env("ACCEPTED_REVIEW_FAST_MODE", "false") == "true"
    review_exit_status = int(require_exact_env("ACCEPTED_REVIEW_EXIT_STATUS", "0"))
    review_final_line = require_exact_env(
        "ACCEPTED_REVIEW_FINAL_LINE",
        "VERDICT: PASS",
    )
    focused_tests = require_exact_env("NODE2B_FOCUSED_TESTS_STATUS", "pass")
    full_pytest = require_exact_env("NODE2B_FULL_PYTEST_STATUS", "pass")
    compileall = require_exact_env("NODE2B_COMPILEALL_STATUS", "pass")
    codegraph_sync = require_exact_env("NODE2B_CODEGRAPH_STATUS", "pass")
    static_gates = require_exact_env("NODE2B_STATIC_GATES_STATUS", "pass")
    clean_worktree = require_exact_env("NODE2B_CLEAN_WORKTREE_STATUS", "pass")

    if re.fullmatch(r"[0-9a-f]{40}", node2b_head) is None:
        raise SystemExit("NODE2B_PREREQ_SHA must be a lowercase 40-character commit SHA")
    if accepted_head != node2b_head:
        raise SystemExit("accepted review HEAD must equal NODE2B_PREREQ_SHA")
    if not os.path.isabs(receipt_path):
        raise SystemExit("NODE2B_PASS_RECEIPT_PATH must be absolute")
    if not os.path.isdir(repo_root):
        raise SystemExit("REPO_ROOT must resolve to a directory")

    parent_path = os.path.dirname(receipt_path)
    receipt_name = os.path.basename(receipt_path)
    if not receipt_name or receipt_name in {".", ".."}:
        raise SystemExit("NODE2B_PASS_RECEIPT_PATH must name a file")

    payload = {
        "node": "team-evidence-aggregation-independence-correlation-requirement-witness",
        "head_sha": node2b_head,
        "review_model": review_model,
        "review_effort": review_effort,
        "read_only": read_only,
        "fast_mode": fast_mode,
        "review_exit_status": review_exit_status,
        "review_final_nonblank_line": review_final_line,
        "focused_tests": focused_tests,
        "full_pytest": full_pytest,
        "compileall": compileall,
        "codegraph_sync": codegraph_sync,
        "static_gates": static_gates,
        "clean_worktree": clean_worktree,
        "pushed_remote_main_sha": confirmed_remote_main_sha,
    }
    receipt_bytes = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    receipt_sha256 = hashlib.sha256(receipt_bytes).hexdigest()

    parent_descriptor: int | None = None
    receipt_descriptor: int | None = None
    verification_descriptor: int | None = None
    created_stat: os.stat_result | None = None
    try:
        parent_descriptor = open_directory_without_symlinks(parent_path)
        parent_stat = os.fstat(parent_descriptor)
        if not stat.S_ISDIR(parent_stat.st_mode):
            raise SystemExit("Node 2B PASS receipt parent must be a directory")
        if parent_stat.st_uid != os.geteuid():
            raise SystemExit("Node 2B PASS receipt parent must be owned by current user")
        if parent_stat.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            raise SystemExit(
                "Node 2B PASS receipt parent must not be writable by group or others",
            )
        require_outside_repo(
            resolved_descriptor_path(parent_descriptor, label="parent"),
            repo_root=repo_root,
            label="parent",
        )

        receipt_descriptor = os.open(
            receipt_name,
            os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=parent_descriptor,
        )
        created_stat = os.fstat(receipt_descriptor)
        if not stat.S_ISREG(created_stat.st_mode):
            raise SystemExit("Node 2B PASS receipt must be a regular file")
        require_outside_repo(
            resolved_descriptor_path(receipt_descriptor, label="file"),
            repo_root=repo_root,
            label="file",
        )
        os.fchmod(receipt_descriptor, 0o600)

        remaining = memoryview(receipt_bytes)
        while remaining:
            written = os.write(receipt_descriptor, remaining)
            if written <= 0:
                raise SystemExit("Node 2B PASS receipt write did not progress")
            remaining = remaining[written:]

        final_stat = os.fstat(receipt_descriptor)
        if not stat.S_ISREG(final_stat.st_mode):
            raise SystemExit("Node 2B PASS receipt changed file type")
        if final_stat.st_size != len(receipt_bytes):
            raise SystemExit("Node 2B PASS receipt byte count mismatch")
        if stat.S_IMODE(final_stat.st_mode) != 0o600:
            raise SystemExit("Node 2B PASS receipt mode must be 0600")
        os.fsync(receipt_descriptor)

        os.lseek(receipt_descriptor, 0, os.SEEK_SET)
        descriptor_bytes = read_exact(receipt_descriptor, len(receipt_bytes))
        if descriptor_bytes != receipt_bytes:
            raise SystemExit("Node 2B PASS receipt descriptor readback mismatch")
        if hashlib.sha256(descriptor_bytes).hexdigest() != receipt_sha256:
            raise SystemExit("Node 2B PASS receipt descriptor SHA-256 mismatch")

        os.fsync(parent_descriptor)

        named_stat = os.stat(
            receipt_name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
        if (
            not stat.S_ISREG(named_stat.st_mode)
            or (named_stat.st_dev, named_stat.st_ino)
            != (created_stat.st_dev, created_stat.st_ino)
        ):
            raise SystemExit("Node 2B PASS receipt name changed during creation")

        verification_descriptor = os.open(
            receipt_name,
            os.O_RDONLY | os.O_NOFOLLOW,
            dir_fd=parent_descriptor,
        )
        verification_stat = os.fstat(verification_descriptor)
        if (
            not stat.S_ISREG(verification_stat.st_mode)
            or (verification_stat.st_dev, verification_stat.st_ino)
            != (created_stat.st_dev, created_stat.st_ino)
            or verification_stat.st_size != len(receipt_bytes)
            or stat.S_IMODE(verification_stat.st_mode) != 0o600
        ):
            raise SystemExit("Node 2B PASS receipt reopen verification failed")
        verification_bytes = read_exact(verification_descriptor, len(receipt_bytes))
        if verification_bytes != receipt_bytes:
            raise SystemExit("Node 2B PASS receipt pathname readback mismatch")
        if hashlib.sha256(verification_bytes).hexdigest() != receipt_sha256:
            raise SystemExit("Node 2B PASS receipt pathname SHA-256 mismatch")

        os.fsync(parent_descriptor)
        final_named_stat = os.stat(
            receipt_name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
        if (
            not stat.S_ISREG(final_named_stat.st_mode)
            or (final_named_stat.st_dev, final_named_stat.st_ino)
            != (created_stat.st_dev, created_stat.st_ino)
            or final_named_stat.st_size != len(receipt_bytes)
            or stat.S_IMODE(final_named_stat.st_mode) != 0o600
        ):
            raise SystemExit("Node 2B PASS receipt final pathname verification failed")

        os.close(verification_descriptor)
        verification_descriptor = None
        os.close(receipt_descriptor)
        receipt_descriptor = None
    finally:
        if verification_descriptor is not None:
            os.close(verification_descriptor)
        if receipt_descriptor is not None:
            os.close(receipt_descriptor)
        if parent_descriptor is not None:
            os.close(parent_descriptor)

    return receipt_sha256


try:
    print(create_receipt())
except OSError:
    raise SystemExit("Node 2B PASS receipt exclusive creation failed") from None
PY
)"; then
  if [[ "$NODE2B_PASS_RECEIPT_SHA256" =~ ^[0-9a-f]{64}$ ]]; then
    NODE2B_RECEIPT_PUBLICATION_RESULT=pass
    export NODE2B_PASS_RECEIPT_PATH NODE2B_PASS_RECEIPT_SHA256 \
      NODE2B_RECEIPT_PUBLICATION_RESULT
    readonly NODE2B_PASS_RECEIPT_PATH NODE2B_PASS_RECEIPT_SHA256 \
      NODE2B_RECEIPT_PUBLICATION_RESULT
    printf 'NODE2B_PREREQ_SHA=%s\n' "$NODE2B_PREREQ_SHA"
    printf 'NODE2B_PASS_RECEIPT_PATH=%s\n' "$NODE2B_PASS_RECEIPT_PATH"
    printf 'NODE2B_PASS_RECEIPT_SHA256=%s\n' "$NODE2B_PASS_RECEIPT_SHA256"
  else
    unset NODE2B_PASS_RECEIPT_SHA256
    NODE2B_RECEIPT_PUBLICATION_RESULT=error
    export NODE2B_RECEIPT_PUBLICATION_RESULT
    printf 'receipt creator returned a non-canonical SHA-256; use a new absent path for receipt-only retry.\n' >&2
  fi
else
  RECEIPT_CREATOR_STATUS=$?
  unset NODE2B_PASS_RECEIPT_SHA256
  NODE2B_RECEIPT_PUBLICATION_RESULT=error
  export NODE2B_RECEIPT_PUBLICATION_RESULT
  printf 'receipt creation failed with status %s; do not push again, and use a new absent path for receipt-only retry.\n' "$RECEIPT_CREATOR_STATUS" >&2
fi
```

Expected outcome: the observed pre-push remote equals immutable `NODE_BASE`,
the sole real push is non-force, and a stable post-attempt observation proves
that remote `main` exactly equals `ACCEPTED_REVIEW_HEAD`. No race branch rebases
or changes local `HEAD`. Receipt publication then re-verifies exact equality,
derives every 15-field payload value from accepted gate variables, creates a
new external `0600` file, fsyncs it and its private parent, and verifies exact
bytes/SHA/inode/mode through both the original descriptor and a reopened path.
A receipt failure blocks Node 2C but leaves the accepted shell available for a
receipt-only retry at a new path. Force push, a second push, and non-protective
dry runs are forbidden.

Automatic pathname cleanup is forbidden. A failure after exclusive creation
may leave only that newly created `0600` artifact in place; the plan closes its
descriptors but never calls `unlink`. The operator must use a new externally
managed destination for a receipt-only retry after the block re-verifies the
unchanged reviewed `HEAD` and exact equality on current remote `main`. This avoids
deleting a raced replacement from an external directory.

## Completion Evidence

After `NODE2B_RECEIPT_PUBLICATION_RESULT=pass`, the coordinator records the
observed values below. Replace every angle-bracket value with the actual runtime
value; do not retain alternatives such as "none, or each." When the fix count
is zero, record literal `POST_REVIEW_FIX_SHAS=none`. Otherwise record the exact
ordered comma-separated fix SHAs and a matching count. Any durable copy beyond
the externally mandated content-addressed PASS receipt must be stored only in
local Supabase/Postgres through approved project infrastructure, never in a new
file-backed journal.

```text
NODE_BASE=<40-character fetched base SHA>
NODE2A_PREREQ_SHA=<validated reviewed/pushed Node 2A ancestor SHA>
NODE2A_PASS_RECEIPT_SHA256=<validated lowercase receipt SHA-256>
NODE2A_RECEIPT_VALIDATION_STATUS=pass
NODE2B_RANGE_GATE_HEAD=<40-character range-gated SHA>
NODE2B_TEST_GATE_HEAD=<same 40-character test-gated SHA>
GATED_HEAD=<same 40-character scan-gated SHA>
NODE2B_GATE_EVIDENCE=<exact Step 1-3 evidence and classification text>
NODE2B_REVIEW_GATE_RESULT=pass
ACCEPTED_REVIEW_HEAD=<same GATED_HEAD SHA>
ACCEPTED_REVIEW_MODEL=claude-opus-4-8
ACCEPTED_REVIEW_EFFORT=max
ACCEPTED_REVIEW_READ_ONLY=true
ACCEPTED_REVIEW_FAST_MODE=false
ACCEPTED_REVIEW_EXIT_STATUS=0
ACCEPTED_REVIEW_FINAL_LINE=VERDICT: PASS
POST_REVIEW_FIX_COUNT=<nonnegative integer>
POST_REVIEW_FIX_SHAS=<none or exact ordered comma-separated 40-character SHAs>
CURRENT_REMOTE=<observed pre-push 40-character SHA equal to NODE_BASE>
LOCAL_HEAD=<accepted reviewed 40-character SHA>
PUSH_STATUS=<actual ordinary non-force git push exit status>
POST_PUSH_OBSERVATION_STATUS=0
REMOTE_AFTER_PUSH=<stable post-attempt SHA equal to ACCEPTED_REVIEW_HEAD>
REMOTE_PUBLICATION_STATUS=confirmed_exact
REMOTE_EQUALS_ACCEPTED_REVIEW_HEAD=pass
CONFIRMED_REMOTE_MAIN_SHA=<same exact ACCEPTED_REVIEW_HEAD SHA>
NODE2B_RECEIPT_PUBLICATION_RESULT=pass
NODE2B_RECEIPT_DESCRIPTOR_READBACK=pass
NODE2B_RECEIPT_PATHNAME_READBACK=pass
NODE2B_RECEIPT_MODE=0600
NODE2B_RECEIPT_PARENT_FSYNC=pass
NODE2B_PREREQ_SHA=<exact accepted reviewed Node 2B SHA>
NODE2B_PASS_RECEIPT_PATH=<exact external immutable receipt path for Node 2C>
NODE2B_PASS_RECEIPT_SHA256=<lowercase SHA-256 of exact read-back canonical bytes>
```

Completion does not authorize persistence or execution. Node 2B remains a pure, transient, paper-only/report-only/readonly child and becomes a valid Node 2C dependency only after every gate above, the verified non-force push, and successful publication of all three outgoing handoff values.

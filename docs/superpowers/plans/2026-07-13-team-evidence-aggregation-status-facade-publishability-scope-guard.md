# Team Evidence Aggregation Status Facade, Publishability, And Scope Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the pure Node 2C reducer that composes the reviewed Node 2A and Node 2B contracts into deterministic diagnostics, capped arithmetic `P(YES)`, requirement coverage, contradiction, readiness, reasons, ready-only publication, and tamper-evident result validation, then enforce the complete six-module Node 2 boundary with one unified scope guard.

**Architecture:** `team_evidence_aggregation.py` enters through both Node 2A canonical-record selectors, evaluates every supplied input record, passes the exact eligible tuple through Node 2B allocation and witness APIs, and materializes one immutable `TeamEvidenceAggregationResult`. The public builder and validator share one private semantic materializer. The validator rejects a wrong outer result type with its dedicated exact error, then asks the codec to validate the supplied exact result's complete recursive shape before rematerialization or any supplied semantic access. Codec failure maps immediately to the generic mismatch and does not rematerialize. Only after codec success does exact input/config rematerialization run, so malformed dependency errors remain unchanged; subsequent supplied-result shape or semantic mismatches map to the generic mismatch. The codec remains the sole owner of config/core digest encoding. `tests/test_team_evidence_aggregation_scope.py` parses all six production modules and the package root, enforces the approved import/export and forbidden-surface contract, and applies every individual and aggregate physical-line ceiling.

**Tech Stack:** Python 3.12, exact frozen/slotted dataclasses from Node 2A, fixed-six `Decimal` under an isolated `Context(prec=64, rounding=ROUND_HALF_EVEN)`, Node 2A canonical selectors and temporal API, Node 2B largest-remainder allocation and canonical global witness matching, canonical SHA-256 codec helpers, pytest, Python `ast`, CodeGraph, git, and local Claude Code `claude-fable-5` at effort `max`.

## Global Constraints

- The governance candidate retains exactly two runtime/design clarifications in `docs/superpowers/specs/2026-07-13-team-evidence-aggregation-core-design.md`: Node 2B witness validation must run before Node 2C inspects allocation output, and the terminal handoff section must mirror the closed `pal.governance-candidate-publication.v1` bootstrap boundary without creating a third child receipt. Separately, this governance candidate performs three governance-only corrections that are not runtime semantic changes: (1) the historical receipt correction restoring accepted Node 2A/2B `review_model` facts to `claude-opus-4-8`; (2) the future Node 2C review-policy correction that applies `claude-fable-5`/`max` only to the future Node 2C review while preserving already accepted Node 2A/2B review identities; and (3) the derived design-blob-pin reconciliation that rebinds every active design-blob assertion to the final design Git blob. The later three-file implementation range preserves the candidate's reviewed design blob byte-for-byte and does not revise any other policy or contract.
- Every Node 2 value remains `paper_only=True`, `report_only=True`, and `readonly=True`. No hard flag may be weakened, inferred, or caller-overridden.
- Every probability is canonical `P(YES)`. There is no selected-side complement, `P(NO)` alias, hidden prior, market-price term, log-odds pooling, float path, or BTC-specific policy.
- The Node 2C production module is pure over explicit immutable caller values.
  It performs no database or Supabase/Postgres access, project-data persistence,
  filesystem access, network access, CLI parsing, environment access, process
  execution, logging, ambient clock read, randomness, or built-in `hash()` use.
  Governance, Git, test, review, and publication gates run outside the production
  child; their explicitly scoped external files are operational evidence only
  and must never contain or serve as persisted project data.
- Future project-data persistence derived from this result is local Supabase/Postgres only. In every future persistence node, each raw DSN from environment, config, CLI plumbing, fixture, or helper construction must be passed to `validate_local_postgres_dsn` before constructing a connection, psycopg wrapper, adapter, repository, or store. Node 2C neither accepts a DSN nor constructs any persistence surface.
- Add no live trading, authentication, hosted-account read, credential, private-key, wallet, signing, order submission, order cancellation, order replacement, execution, exchange mutation, sizing, or allocation-to-capital surface.
- Add no run identity, complete evaluation-scope provenance, accepted/rejected evaluator receipts, `tea:v1`, `tfr:v1`, `tfe:v1`, forecast/evidence IDs, packet construction, legacy projection, decoder, service, CLI, DB row, store, or package-root export.
- Node 3 alone will bind config/input/full-result fragments into complete replay scope. Node 2C's `core_digest` is not a run, forecast, evidence, deduplication, or complete replay identity.
- Use only the exact public Node 2A/2B interfaces fixed below. If either predecessor contract differs, stop and amend/re-review that predecessor; do not adapt Node 2C around a drifted interface.
- Production Decimal operations run only inside a local copy of `Context(prec=64, rounding=ROUND_HALF_EVEN)`. Do not read or mutate `decimal.getcontext()`, quantize products or running sums early, or create a float.
- Error messages are stable contract descriptions containing canonical field paths or IDs only. They do not interpolate raw payloads, object representations, source text, rationale text, DSNs, or secret-bearing values.
- Every governance and implementation endpoint lookup, `ls-remote`, `fetch`, and
  `push` captures the stdout required for validation, suppresses all other raw
  stdout and stderr, records the command status before restoring `errexit`, and
  returns or exits with that exact status. Terminal diagnostics are fixed,
  non-sensitive categories; no endpoint value is ever interpolated or replayed.
- Every Claude invocation uses a private mode-`0700` directory and a minimal
  `env -i` allowlist. Raw stream JSON, extracted report, and stderr exist only as
  mode-`0600`, size-bounded files used for structured parsing, byte counts, and
  SHA-256 evidence. Their contents are never replayed to stdout or stderr; the
  terminal receives only fixed `pass`, `revise`, or `error` categories. If the
  local Claude installation is incompatible with the allowlist, stop for a
  reviewed allowlist amendment rather than retrying with the inherited
  environment.
- Every secret scan uses quiet matching. A finding or scanner failure emits at
  most the canonical affected path, or the fixed `commit-message` category for
  a commit-message finding; it never emits a matched line, matched value,
  commit object ID, endpoint, or raw tool diagnostic.
- No dependency or `pyproject.toml` change is permitted.
- Fast mode is forbidden for implementation and review.
- Every independently started governance or Node 2C gate shell repeats the
  complete plan-defined `assert_node2c_git_controls` definition before its
  first repository-aware Git command. The function is readonly in that shell,
  is never exported with `export -f`, and no function, option, trap, working
  directory, environment normalization, or successful result is inherited as
  evidence across a fresh-shell boundary.
- Each fresh shell exports readonly `GIT_NO_REPLACE_OBJECTS=1` and invokes
  `assert_node2c_git_controls` as a standalone command under `set -e`. A caller
  must not place the invocation in `if`, `!`, `&&`, or `||`; policy violations
  return `1`, while a failing Git producer's exact nonzero status propagates.
- No shell may clear, unset, or overwrite `GIT_GRAFT_FILE` or
  `GIT_REPLACE_REF_BASE` before a helper call. An inherited nonempty value is
  rejection evidence, not state that the gate may normalize.
- The Git-control helper has no fast mode, cached pass, timestamp shortcut,
  environment opt-out, or boundary coalescing. Every required boundary call
  freshly enumerates replacement refs, resolves and checks the common-directory
  `info/grafts` path including a dangling symlink, and queries shallow state.

## Exact Sorted Implementation Allowlist

Only these repository paths may change in Node 2C, in this literal `LC_ALL=C` order:

```text
src/polymarket_alpha_lab/team_evidence_aggregation.py
tests/test_team_evidence_aggregation.py
tests/test_team_evidence_aggregation_scope.py
```

Use this exact shell array in every staging/range gate:

```bash
set -euo pipefail
NODE_PATHS=(
  src/polymarket_alpha_lab/team_evidence_aggregation.py
  tests/test_team_evidence_aggregation.py
  tests/test_team_evidence_aggregation_scope.py
)
EXPECTED_NODE_PATHS="$(printf '%s\n' "${NODE_PATHS[@]}")"
SORTED_NODE_PATHS="$(printf '%s\n' "${NODE_PATHS[@]}" | LC_ALL=C sort)"
test "$SORTED_NODE_PATHS" = "$EXPECTED_NODE_PATHS"
```

No other source, test, package-root, configuration, migration, documentation, or generated path is part of the implementation range.

## Reviewed Governance Base

Node 2C starts only after one local, unpublished hardened-governance candidate
commit has received a read-only Claude Code `claude-fable-5`, effort `max`,
final `VERDICT: PASS` and that exact commit has been non-force published to
`main`. Its fixed published import-governance parent is
`e31c3951b06f06e995c0c8f6f8fe2f22320a38da`. That parent's sole parent is the
reviewed Node 2B SHA `2be280b5a3194a83191753bfc1deb227a3d2dc31`; it changes
exactly this plan and has exact subject
`docs: align Node 2C module import governance`. The new candidate's sole parent
is `e31c3951b06f06e995c0c8f6f8fe2f22320a38da`; its exact subject is
`docs: align Node 2C witness ownership governance`, and it changes exactly this
plan followed by the core design spec under `LC_ALL=C`. The candidate plan and
amended-design blob IDs, parent, tree, commit SHA, and complete two-document
range are fixed before review. Claude runs from a separate
clean detached worktree at that literal candidate SHA. A correction creates a
new candidate directly from the same fixed import-governance parent and requires
a fresh review; no reviewed candidate or published parent is amended or
extended.

Here, the coordinator is the parent orchestration shell that creates the clean
candidate worktree, invokes the reviewer, publishes only the reviewed literal
SHA, writes the closed governance-candidate publication record, and starts implementation or
review-fix shells. A PASS authorizes no post-review staging, commit construction,
amend, tree change, or candidate substitution. Immediately before publication,
the coordinator rechecks the candidate's parent, one-commit range, exact paths,
plan/design blobs, and review report binding. It then performs one explicit
non-force push and stable two-advertisement/fetched-object observations. This is
a point-in-time publication proof, not a claim that a remote can never advance.

Every governance, Task 1, staged-state, history, review, publication, recovery,
and completion boundary uses the plan-defined helper. Each independently
started shell repeats its complete definition inline, exports readonly
`GIT_NO_REPLACE_OBJECTS=1`, and invokes it directly before its first
repository-aware Git command. The helper rejects `refs/replace`, a present
`$GIT_COMMON_DIR/info/grafts` path including a dangling symlink, nonempty
`GIT_GRAFT_FILE` or `GIT_REPLACE_REF_BASE`, and a shallow repository before
commits or blobs are trusted. The plan blob is not self-embedded: embedding a file's own Git
blob ID would change its preimage. Instead, the governance-candidate publication record is
read exactly once through a bounded no-follow descriptor and is independently
handed off by absolute path plus SHA-256. Its closed payload binds the fixed
published import-governance parent as `predecessor_sha`, the governance candidate
SHA, plan/design blobs, exact plan path, Claude
model/effort/read-only/no-fast/exit/verdict evidence, review report SHA-256,
frozen remote endpoint SHA-256, and confirmed remote `main` SHA. Task 1 derives
`NODE2C_EXPECTED_BASE`, `NODE2C_REVIEWED_PLAN_BLOB`, and
`NODE2C_REVIEWED_DESIGN_BLOB` only from that descriptor-validated publication
record.
`review_report_sha256` is a trusted coordinator attestation computed from the
actual Claude report bytes before publication-record creation. Its trust root is
the independently handed-off publication-record path plus SHA-256; Task 1
validates the closed field and digest shape but does not reopen the temporary
review report.

The same trusted-coordinator boundary applies to later gate, review,
publication-matrix, checkpoint, and completion manifests. Canonical bytes,
descriptor-safe reads, sidecars, and separately carried expected digests bind
an honest coordinator's cross-process handoff and detect corruption,
substitution, noncanonical state, and stale generations. They are not a
signature, MAC, PKI, or defense against a malicious same-user coordinator that
controls both evidence bytes and the out-of-band expected digest; this node adds
no signing key or publication broker. After Node 2C's accepted SHA is known, the
future Node 3 fixed predecessor plan pins that literal SHA and the accepted
manifest digests as successor-side trust anchors, then independently revalidates
the retained review bytes and fresh exact remote equality.

The closed nineteen-key governance-candidate publication record is bootstrap provenance only. Task 1
uses it to establish the reviewed governance base and exact plan/design blobs,
then its consumer role terminates. It is not a Node 2C child-completion receipt,
does not create a third child receipt schema, and is never a Node 3 input. The
implementation gate/review manifests bind its SHA-256 only to preserve the
auditable `NODE_BASE` provenance chain; they do not embed its path or payload.
Node 3 consumes the literal accepted Node 2C SHA plus the implementation review
and exact-publication manifest pins and uses schema-specific manifest validators,
not the governance-candidate publication record or a generic receipt parser.
Node 3 receives no separately handed governance-publication digest. A
`governance_candidate_publication_sha256` value nested in either retained
manifest is nested audit-provenance continuity only; it cannot select the Node 2C implementation SHA and
cannot satisfy accepted-review, fixed-predecessor, or exact-publication validation.

Neither published governance-document commit, the plan-only import-governance
parent nor its two-document hardened-governance child, is part of the later
three-file implementation range.
The hardened candidate becomes the immutable implementation `NODE_BASE`, so
`NODE_BASE..HEAD` starts strictly after both governance-document commits. Any
predecessor child-receipt or governance-publication mismatch, documentation
drift, replacement mechanism, parent with the wrong provenance or path, or
implementation descendant that touches either governance document blocks Node
2C. Task 1 performs one initial and one final validation pass; each pass opens,
reads, hashes, and parses each inbound artifact exactly once through its own
bounded no-follow descriptor.

### Governance Candidate Procedure

Run the candidate construction in a dedicated worktree whose `HEAD` is the
fixed published import-governance parent
`e31c3951b06f06e995c0c8f6f8fe2f22320a38da`. Exactly the plan and core design
paths fixed below may be modified, staged, or committed; no other tracked or
untracked path is permitted. These checks occur before the first governance
Claude invocation:

```bash
set -Eeuo pipefail
umask 077

assert_node2c_git_controls() {
    # Keep xtrace from exposing checked values and restore caller options on
    # every return from this function.
    local -
    set +x

    local node2c_refs=''
    local node2c_common_dir=''
    local node2c_shallow_state=''
    local node2c_producer_status=0
    local node2c_no_replace_declaration=''

    if [[ ${GIT_NO_REPLACE_OBJECTS-} != '1' ]]; then
        printf '%s\n' \
            'node2c git controls: GIT_NO_REPLACE_OBJECTS must equal 1' >&2 || :
        return 1
    fi

    if node2c_no_replace_declaration=$(builtin declare -p \
        GIT_NO_REPLACE_OBJECTS 2>/dev/null); then
        :
    else
        printf '%s\n' \
            'node2c git controls: GIT_NO_REPLACE_OBJECTS must equal 1 and be exported' >&2 || :
        return 1
    fi

    if [[ $node2c_no_replace_declaration \
        != declare\ -*x*\ GIT_NO_REPLACE_OBJECTS=* ]]; then
        printf '%s\n' \
            'node2c git controls: GIT_NO_REPLACE_OBJECTS must equal 1 and be exported' >&2 || :
        return 1
    fi

    if [[ -n ${GIT_GRAFT_FILE-} ]]; then
        printf '%s\n' \
            'node2c git controls: GIT_GRAFT_FILE must be unset or empty' >&2 || :
        return 1
    fi

    if [[ -n ${GIT_REPLACE_REF_BASE-} ]]; then
        printf '%s\n' \
            'node2c git controls: GIT_REPLACE_REF_BASE must be unset or empty' >&2 || :
        return 1
    fi

    if node2c_refs=$(command git for-each-ref \
        '--format=%(refname)' 'refs/replace/' 2>/dev/null); then
        :
    else
        node2c_producer_status=$?
        printf '%s\n' \
            'node2c git controls: could not enumerate replacement refs' >&2 || :
        return "$node2c_producer_status"
    fi

    if [[ -n $node2c_refs ]]; then
        printf '%s\n' \
            'node2c git controls: replacement refs are present' >&2 || :
        return 1
    fi

    if node2c_common_dir=$(command git rev-parse \
        '--path-format=absolute' '--git-common-dir' 2>/dev/null); then
        :
    else
        node2c_producer_status=$?
        printf '%s\n' \
            'node2c git controls: could not resolve the Git common directory' >&2 || :
        return "$node2c_producer_status"
    fi

    if [[ -z $node2c_common_dir || $node2c_common_dir != /* \
        || $node2c_common_dir == *$'\n'* ]]; then
        printf '%s\n' \
            'node2c git controls: Git common-directory result is invalid' >&2 || :
        return 1
    fi

    if [[ -e $node2c_common_dir/info/grafts \
        || -L $node2c_common_dir/info/grafts ]]; then
        printf '%s\n' \
            'node2c git controls: common-directory info/grafts is present' >&2 || :
        return 1
    fi

    if node2c_shallow_state=$(command git rev-parse \
        '--is-shallow-repository' 2>/dev/null); then
        :
    else
        node2c_producer_status=$?
        printf '%s\n' \
            'node2c git controls: could not determine shallow state' >&2 || :
        return "$node2c_producer_status"
    fi

    case "$node2c_shallow_state" in
        false)
            ;;
        true)
            printf '%s\n' \
                'node2c git controls: repository is shallow' >&2 || :
            return 1
            ;;
        *)
            printf '%s\n' \
                'node2c git controls: shallow-state query returned an invalid result' >&2 || :
            return 1
            ;;
    esac

    return 0
}
readonly -f assert_node2c_git_controls

export GIT_NO_REPLACE_OBJECTS=1
readonly GIT_NO_REPLACE_OBJECTS
assert_node2c_git_controls
: "${NODE2B_PREREQ_SHA:?reviewed Node 2B SHA is required}"
NODE2B_REVIEWED_SHA=2be280b5a3194a83191753bfc1deb227a3d2dc31
NODE2C_IMPORT_GOVERNANCE_PARENT_SHA=e31c3951b06f06e995c0c8f6f8fe2f22320a38da
test "$NODE2B_PREREQ_SHA" = "$NODE2B_REVIEWED_SHA"
export NODE2B_REVIEWED_SHA NODE2C_IMPORT_GOVERNANCE_PARENT_SHA
readonly NODE2B_REVIEWED_SHA NODE2C_IMPORT_GOVERNANCE_PARENT_SHA
GOVERNANCE_PLAN_PATH=docs/superpowers/plans/2026-07-13-team-evidence-aggregation-status-facade-publishability-scope-guard.md
GOVERNANCE_DESIGN_PATH=docs/superpowers/specs/2026-07-13-team-evidence-aggregation-core-design.md
GOVERNANCE_AMENDED_DESIGN_BLOB=f1ac9a517725ccdc7740108db82f89cd74d0e33f
GOVERNANCE_EXPECTED_DOC_PATHS="$(
  printf '%s\n' "$GOVERNANCE_PLAN_PATH" "$GOVERNANCE_DESIGN_PATH" |
    LC_ALL=C sort
)"
test "$GOVERNANCE_EXPECTED_DOC_PATHS" = "$(
  printf '%s\n' "$GOVERNANCE_PLAN_PATH" "$GOVERNANCE_DESIGN_PATH"
)"
GOVERNANCE_COMMON_GIT_DIR="$(
  git rev-parse --path-format=absolute --git-common-dir 2>/dev/null
)"
GOVERNANCE_REMOTE_CAPTURE_LIMIT_BYTES=4096
GOVERNANCE_REMOTE_CAPTURE_LIMIT_BLOCKS=4
GOVERNANCE_REMOTE_REF=refs/heads/main
readonly GOVERNANCE_REMOTE_CAPTURE_LIMIT_BYTES \
  GOVERNANCE_REMOTE_CAPTURE_LIMIT_BLOCKS GOVERNANCE_REMOTE_REF

capture_governance_output_bounded() {
  local -
  local output_name=$1
  local capture_file capture_size captured_text
  local capture_status producer_status remove_status
  shift
  set +e

  capture_file="$(
    mktemp \
      "$GOVERNANCE_COMMON_GIT_DIR/.node2c-governance-observer.XXXXXX" \
      2>/dev/null
  )"
  capture_status=$?
  ((capture_status == 0)) || return "$capture_status"
  chmod 600 "$capture_file" >/dev/null 2>&1
  capture_status=$?
  if ((capture_status != 0)); then
    rm -f -- "$capture_file" >/dev/null 2>&1 || :
    return 70
  fi

  (
    ulimit -f "$GOVERNANCE_REMOTE_CAPTURE_LIMIT_BLOCKS"
    capture_status=$?
    ((capture_status == 0)) || exit "$capture_status"
    "$@" > "$capture_file" 2>/dev/null
  )
  producer_status=$?
  if ((producer_status != 0)); then
    rm -f -- "$capture_file" >/dev/null 2>&1 || :
    return "$producer_status"
  fi

  capture_size="$(stat -c '%s' -- "$capture_file" 2>/dev/null)"
  capture_status=$?
  if ((capture_status != 0)); then
    rm -f -- "$capture_file" >/dev/null 2>&1 || :
    return "$capture_status"
  fi
  if [[ ! "$capture_size" =~ ^[0-9]+$ ]] ||
    ((capture_size > GOVERNANCE_REMOTE_CAPTURE_LIMIT_BYTES)); then
    rm -f -- "$capture_file" >/dev/null 2>&1 || :
    return 74
  fi

  captured_text="$(
    command cat -- "$capture_file" 2>/dev/null
    capture_status=$?
    printf '\036'
    exit "$capture_status"
  )"
  capture_status=$?
  rm -f -- "$capture_file" >/dev/null 2>&1
  remove_status=$?
  ((capture_status == 0)) || return "$capture_status"
  ((remove_status == 0)) || return 70
  captured_text=${captured_text%$'\036'}
  printf -v "$output_name" '%s' "$captured_text"
}

retry_capture_governance_output() {
  local -
  local output_name=$1
  local attempt captured_output producer_status=74
  shift
  set +e
  for attempt in 1 2 3; do
    capture_governance_output_bounded captured_output "$@"
    producer_status=$?
    if ((producer_status == 0)); then
      printf -v "$output_name" '%s' "$captured_output"
      return 0
    fi
  done
  return "$producer_status"
}

retry_governance_producer() {
  local -
  local attempt producer_status=74
  set +e
  for attempt in 1 2 3; do
    "$@"
    producer_status=$?
    ((producer_status == 0)) && return 0
  done
  return "$producer_status"
}

governance_get_remote_endpoint() {
  git remote get-url --push --all origin 2>/dev/null
}

governance_ls_remote_main() {
  GIT_TERMINAL_PROMPT=0 git "${GOVERNANCE_GIT_AUTH[@]}" ls-remote \
    --exit-code "$GOVERNANCE_REMOTE_ENDPOINT" "$GOVERNANCE_REMOTE_REF" \
    2>/dev/null
}

governance_fetch_remote_main() {
  GIT_TERMINAL_PROMPT=0 git "${GOVERNANCE_GIT_AUTH[@]}" fetch --no-tags \
    --no-recurse-submodules "$GOVERNANCE_REMOTE_ENDPOINT" \
    "$GOVERNANCE_REMOTE_REF" >/dev/null 2>&1
}

governance_resolve_fetch_head() {
  git rev-parse --verify 'FETCH_HEAD^{commit}' 2>/dev/null
}

parse_governance_ls_remote() {
  local output=$1
  local output_name=$2
  local record ref sha
  [[ "$output" == *$'\n' ]] || return 74
  record=${output%$'\n'}
  [[ "$record" != *$'\n'* && "$record" == *$'\t'* ]] || return 74
  sha=${record%%$'\t'*}
  ref=${record#*$'\t'}
  [[ "$sha" =~ ^([0-9a-f]{40}|[0-9a-f]{64})$ &&
     "$ref" == "$GOVERNANCE_REMOTE_REF" ]] || return 74
  printf -v "$output_name" '%s' "$sha"
}

observe_governance_remote_main() {
  local first_output first_sha fetched_output fetched_sha
  local second_output second_sha producer_status parse_status

  retry_capture_governance_output first_output governance_ls_remote_main
  producer_status=$?
  ((producer_status == 0)) || return "$producer_status"
  parse_governance_ls_remote "$first_output" first_sha
  parse_status=$?
  ((parse_status == 0)) || return 74

  retry_governance_producer governance_fetch_remote_main
  producer_status=$?
  ((producer_status == 0)) || return "$producer_status"

  retry_capture_governance_output fetched_output governance_resolve_fetch_head
  producer_status=$?
  ((producer_status == 0)) || return "$producer_status"
  [[ "$fetched_output" == *$'\n' ]] || return 74
  fetched_sha=${fetched_output%$'\n'}
  [[ "$fetched_sha" != *$'\n'* &&
     "$fetched_sha" =~ ^([0-9a-f]{40}|[0-9a-f]{64})$ &&
     "$fetched_sha" == "$first_sha" ]] || return 74

  retry_capture_governance_output second_output governance_ls_remote_main
  producer_status=$?
  ((producer_status == 0)) || return "$producer_status"
  parse_governance_ls_remote "$second_output" second_sha
  parse_status=$?
  ((parse_status == 0)) || return 74
  [[ "$second_sha" == "$first_sha" ]] || return 74
  printf '%s\n' "$second_sha"
}

GOVERNANCE_REMOTE_ENDPOINT_OUTPUT=''
set +e
capture_governance_output_bounded \
  GOVERNANCE_REMOTE_ENDPOINT_OUTPUT governance_get_remote_endpoint
GOVERNANCE_ENDPOINT_STATUS=$?
set -e
if [ "$GOVERNANCE_ENDPOINT_STATUS" -ne 0 ]; then
  printf 'governance remote endpoint lookup failed\n' >&2
  exit "$GOVERNANCE_ENDPOINT_STATUS"
fi
[[ "$GOVERNANCE_REMOTE_ENDPOINT_OUTPUT" == *$'\n' ]]
GOVERNANCE_REMOTE_ENDPOINT=${GOVERNANCE_REMOTE_ENDPOINT_OUTPUT%$'\n'}
test -n "$GOVERNANCE_REMOTE_ENDPOINT"
test "${GOVERNANCE_REMOTE_ENDPOINT//$'\n'/}" = "$GOVERNANCE_REMOTE_ENDPOINT"
GOVERNANCE_REMOTE_ENDPOINT_SHA256="$(
  GOVERNANCE_REMOTE_ENDPOINT_VALUE="$GOVERNANCE_REMOTE_ENDPOINT" \
    .venv/bin/python - <<'PY'
import hashlib
import os

print(
    hashlib.sha256(
        os.environ["GOVERNANCE_REMOTE_ENDPOINT_VALUE"].encode("utf-8"),
    ).hexdigest(),
)
PY
)"
GOVERNANCE_GIT_AUTH=(
  -c credential.helper=
  -c "credential.helper=store --file=$GOVERNANCE_COMMON_GIT_DIR/github-credentials"
)
set +e
GOVERNANCE_REMOTE_FIRST_SHA="$(observe_governance_remote_main)"
GOVERNANCE_REMOTE_FIRST_STATUS=$?
set -e
if [ "$GOVERNANCE_REMOTE_FIRST_STATUS" -ne 0 ]; then
  printf 'governance remote observation failed\n' >&2
  exit "$GOVERNANCE_REMOTE_FIRST_STATUS"
fi
test "$GOVERNANCE_REMOTE_FIRST_SHA" = \
  "$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA"
assert_node2c_git_controls
GOVERNANCE_PARENT_HEAD="$(git rev-parse HEAD)"
test "$GOVERNANCE_PARENT_HEAD" = "$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA"
GOVERNANCE_IMPORT_PARENT_TEXT="$(
  git rev-list --parents -n 1 "$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA"
)"
read -r -a GOVERNANCE_IMPORT_PARENT_AND_PARENT <<< \
  "$GOVERNANCE_IMPORT_PARENT_TEXT"
test "${#GOVERNANCE_IMPORT_PARENT_AND_PARENT[@]}" -eq 2
test "${GOVERNANCE_IMPORT_PARENT_AND_PARENT[0]}" = \
  "$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA"
test "${GOVERNANCE_IMPORT_PARENT_AND_PARENT[1]}" = "$NODE2B_REVIEWED_SHA"
GOVERNANCE_IMPORT_PARENT_COUNT="$(
  git rev-list --count \
    "$NODE2B_REVIEWED_SHA..$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA"
)"
test "$GOVERNANCE_IMPORT_PARENT_COUNT" -eq 1
GOVERNANCE_IMPORT_PARENT_PATHS="$(
  git diff-tree --no-commit-id --name-only -r --no-renames \
    "$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA"
)"
test "$GOVERNANCE_IMPORT_PARENT_PATHS" = "$GOVERNANCE_PLAN_PATH"
GOVERNANCE_IMPORT_PARENT_SUBJECT="$(
  git show -s --format=%s "$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA"
)"
test "$GOVERNANCE_IMPORT_PARENT_SUBJECT" = \
  'docs: align Node 2C module import governance'
git diff --cached --quiet
GOVERNANCE_UNSTAGED_PATHS="$(git diff --name-only)"
test "$GOVERNANCE_UNSTAGED_PATHS" = "$GOVERNANCE_EXPECTED_DOC_PATHS"
GOVERNANCE_UNTRACKED="$(git ls-files --others --exclude-standard)"
test -z "$GOVERNANCE_UNTRACKED"
assert_node2c_git_controls
git add -- "$GOVERNANCE_PLAN_PATH" "$GOVERNANCE_DESIGN_PATH"
GOVERNANCE_STAGED_PATHS="$(git diff --cached --name-only)"
test "$GOVERNANCE_STAGED_PATHS" = "$GOVERNANCE_EXPECTED_DOC_PATHS"
git diff --cached --check
assert_node2c_git_controls
git commit -m "docs: align Node 2C witness ownership governance"
assert_node2c_git_controls
GOVERNANCE_CANDIDATE_SHA="$(git rev-parse HEAD)"
GOVERNANCE_CANDIDATE_SUBJECT="$(
  git show -s --format=%s "$GOVERNANCE_CANDIDATE_SHA"
)"
test "$GOVERNANCE_CANDIDATE_SUBJECT" = \
  'docs: align Node 2C witness ownership governance'
GOVERNANCE_PARENT_TEXT="$(git rev-list --parents -n 1 "$GOVERNANCE_CANDIDATE_SHA")"
read -r -a GOVERNANCE_COMMIT_AND_PARENT <<< "$GOVERNANCE_PARENT_TEXT"
test "${#GOVERNANCE_COMMIT_AND_PARENT[@]}" -eq 2
test "${GOVERNANCE_COMMIT_AND_PARENT[0]}" = "$GOVERNANCE_CANDIDATE_SHA"
test "${GOVERNANCE_COMMIT_AND_PARENT[1]}" = \
  "$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA"
GOVERNANCE_COMMIT_COUNT="$(
  git rev-list --count \
    "$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA..$GOVERNANCE_CANDIDATE_SHA"
)"
test "$GOVERNANCE_COMMIT_COUNT" -eq 1
GOVERNANCE_COMMITTED_PATHS="$(
  git diff-tree --no-commit-id --name-only -r --no-renames \
    "$GOVERNANCE_CANDIDATE_SHA"
)"
test "$GOVERNANCE_COMMITTED_PATHS" = "$GOVERNANCE_EXPECTED_DOC_PATHS"
NODE2C_REVIEWED_PLAN_BLOB="$(
  git rev-parse "$GOVERNANCE_CANDIDATE_SHA:$GOVERNANCE_PLAN_PATH"
)"
NODE2C_REVIEWED_DESIGN_BLOB="$(
  git rev-parse "$GOVERNANCE_CANDIDATE_SHA:$GOVERNANCE_DESIGN_PATH"
)"
GOVERNANCE_IMPORT_PARENT_PLAN_BLOB="$(
  git rev-parse \
    "$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA:$GOVERNANCE_PLAN_PATH"
)"
GOVERNANCE_IMPORT_PARENT_DESIGN_BLOB="$(
  git rev-parse \
    "$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA:$GOVERNANCE_DESIGN_PATH"
)"
test "$NODE2C_REVIEWED_PLAN_BLOB" != "$GOVERNANCE_IMPORT_PARENT_PLAN_BLOB"
test "$NODE2C_REVIEWED_DESIGN_BLOB" = "$GOVERNANCE_AMENDED_DESIGN_BLOB"
test "$NODE2C_REVIEWED_DESIGN_BLOB" != \
  "$GOVERNANCE_IMPORT_PARENT_DESIGN_BLOB"
GOVERNANCE_DOC_CHAIN="$(
  git rev-list --reverse "$NODE2B_REVIEWED_SHA..$GOVERNANCE_CANDIDATE_SHA"
)"
GOVERNANCE_EXPECTED_DOC_CHAIN="$(
  printf '%s\n' \
    "$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA" \
    "$GOVERNANCE_CANDIDATE_SHA"
)"
test "$GOVERNANCE_DOC_CHAIN" = "$GOVERNANCE_EXPECTED_DOC_CHAIN"
GOVERNANCE_POST_COMMIT_STATUS="$(
  git status --porcelain --untracked-files=all
)"
test -z "$GOVERNANCE_POST_COMMIT_STATUS"
assert_node2c_git_controls
readonly GOVERNANCE_PLAN_PATH GOVERNANCE_DESIGN_PATH \
  GOVERNANCE_AMENDED_DESIGN_BLOB GOVERNANCE_EXPECTED_DOC_PATHS \
  NODE2B_REVIEWED_SHA NODE2C_IMPORT_GOVERNANCE_PARENT_SHA \
  GOVERNANCE_CANDIDATE_SHA GOVERNANCE_CANDIDATE_SUBJECT \
  NODE2C_REVIEWED_PLAN_BLOB \
  NODE2C_REVIEWED_DESIGN_BLOB GOVERNANCE_REMOTE_ENDPOINT \
  GOVERNANCE_REMOTE_ENDPOINT_SHA256 GOVERNANCE_IMPORT_PARENT_PLAN_BLOB \
  GOVERNANCE_IMPORT_PARENT_DESIGN_BLOB
```

#### Executable post-construction governance lifecycle

The Bash fence below is the sole normative post-construction governance
authority. Its exact extracted UTF-8 bytes, including its final LF, have
SHA-256 `9f2617f3863f5fdc53d26e8c87fef67d2c93793106e6adc441c1416931bf2354`. The candidate-construction fence above remains
the only constructor. Every older inline governance reviewer, push, recovery,
and receipt-writer block is superseded and removed; prose is not an alternate
authority. Static audit must find exactly one `git_repo push` site in this
lifecycle and no push site in `recover_lifecycle`.

This is a self-hosting governance bootstrap, not a cryptographic proof against
an adversarial coordinator. Before executing the candidate-controlled
lifecycle, the user-authorized external coordinator independently binds the
candidate SHA, parent, subject, changed paths, plan/design blobs, extracted
lifecycle hash, CommonMark fence results, shell failure harness, and lifecycle
matrix. The lifecycle then obtains the required independent Claude decision.
The candidate cannot authorize itself merely by containing this text or by
claiming its own hash.

```bash
#!/usr/bin/env bash
set -euo pipefail

umask 077
export LC_ALL=C

PLAN_PATH=docs/superpowers/plans/2026-07-13-team-evidence-aggregation-status-facade-publishability-scope-guard.md
DESIGN_PATH=docs/superpowers/specs/2026-07-13-team-evidence-aggregation-core-design.md
ALLOCATION_PATH=src/polymarket_alpha_lab/team_evidence_aggregation_allocation.py
WITNESS_PATH=src/polymarket_alpha_lab/team_evidence_aggregation_witness.py
TYPES_PATH=src/polymarket_alpha_lab/team_evidence_aggregation_types.py
REVIEW_MODEL=claude-fable-5
REVIEW_EFFORT=max
REVIEW_FINAL_PASS='VERDICT: PASS'
REVIEW_FINAL_REVISE='VERDICT: REVISE'
REVIEW_TIMEOUT_SECONDS=900

usage() {
  cat >&2 <<'EOF'
usage:
  governance-lifecycle.sh run \
    --repo PATH \
    --predecessor-sha SHA \
    --candidate-sha SHA \
    --plan-blob SHA \
    --design-blob SHA \
    --remote-endpoint-sha256 SHA256 \
    --producer-checks-evidence PATH \
    --producer-checks-evidence-sha256 SHA256 \
    --output-dir PATH \
    --reviewer-bin PATH \
    --codegraph-bin PATH \
    --git-credential-file PATH \
    [--git-bin PATH]

  governance-lifecycle.sh recover \
    --repo PATH \
    --output-dir PATH \
    --git-credential-file PATH \
    [--git-bin PATH]

  governance-lifecycle.sh validate-revise \
    --output-dir PATH
EOF
  exit 64
}

die() {
  local message="$1"
  local status="${2:-1}"
  printf 'error: %s\n' "$message" >&2
  exit "$status"
}

require_value() {
  local name="$1"
  local value="$2"
  test -n "$value" || die "$name is required" 64
}

require_lower_hex() {
  local name="$1"
  local value="$2"
  local width="$3"
  if [[ ! "$value" =~ ^[0-9a-f]+$ ]] || [ "${#value}" -ne "$width" ]; then
    die "$name must be exactly $width lowercase hexadecimal characters" 64
  fi
}

reject_forbidden_path() {
  local path="$1"
  case "/$path/" in
    */.review/*) die 'paths containing a .review segment are forbidden' 64 ;;
  esac
}

reject_git_environment_controls() {
  local name
  for name in \
    GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
    GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_GRAFT_FILE GIT_REPLACE_REF_BASE \
    GIT_CONFIG_PARAMETERS GIT_CONFIG_COUNT; do
    if [[ -v $name ]]; then
      die "inherited Git control $name is forbidden" 64
    fi
  done
  if [[ -v GIT_NO_REPLACE_OBJECTS ]] && [ "$GIT_NO_REPLACE_OBJECTS" != 1 ]; then
    die 'GIT_NO_REPLACE_OBJECTS must be unset or exactly 1' 64
  fi
  export GIT_NO_REPLACE_OBJECTS=1
}

MODE="${1-}"
case "$MODE" in
  run | recover | validate-revise) shift ;;
  *) usage ;;
esac

REPO_INPUT=''
PREDECESSOR_SHA=''
CANDIDATE_SHA=''
PLAN_BLOB=''
DESIGN_BLOB=''
REMOTE_ENDPOINT_SHA256=''
PRODUCER_CHECKS_EVIDENCE_INPUT=''
PRODUCER_CHECKS_EVIDENCE_SHA256=''
OUTPUT_INPUT=''
REVIEWER_BIN=''
CODEGRAPH_BIN=''
GIT_CREDENTIAL_INPUT=''
GIT_BIN=/usr/bin/git

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo) REPO_INPUT="${2-}"; shift 2 ;;
    --predecessor-sha) PREDECESSOR_SHA="${2-}"; shift 2 ;;
    --candidate-sha) CANDIDATE_SHA="${2-}"; shift 2 ;;
    --plan-blob) PLAN_BLOB="${2-}"; shift 2 ;;
    --design-blob) DESIGN_BLOB="${2-}"; shift 2 ;;
    --remote-endpoint-sha256) REMOTE_ENDPOINT_SHA256="${2-}"; shift 2 ;;
    --producer-checks-evidence) PRODUCER_CHECKS_EVIDENCE_INPUT="${2-}"; shift 2 ;;
    --producer-checks-evidence-sha256) PRODUCER_CHECKS_EVIDENCE_SHA256="${2-}"; shift 2 ;;
    --output-dir) OUTPUT_INPUT="${2-}"; shift 2 ;;
    --reviewer-bin) REVIEWER_BIN="${2-}"; shift 2 ;;
    --codegraph-bin) CODEGRAPH_BIN="${2-}"; shift 2 ;;
    --git-credential-file) GIT_CREDENTIAL_INPUT="${2-}"; shift 2 ;;
    --git-bin) GIT_BIN="${2-}"; shift 2 ;;
    *) usage ;;
  esac
done

if [ "${NODE2C_FAST_MODE:-false}" != false ]; then
  die 'fast mode is forbidden; NODE2C_FAST_MODE must be false' 64
fi

require_value --output-dir "$OUTPUT_INPUT"
reject_forbidden_path "$OUTPUT_INPUT"
reject_git_environment_controls

REPO_ROOT=''
GIT_CREDENTIAL_FILE=''
GIT_CREDENTIAL_MODE=''
if [ "$MODE" != validate-revise ]; then
  require_value --repo "$REPO_INPUT"
  require_value --git-bin "$GIT_BIN"
  require_value --git-credential-file "$GIT_CREDENTIAL_INPUT"
  test -x "$GIT_BIN" || die "Git binary is not executable: $GIT_BIN" 64
  reject_forbidden_path "$REPO_INPUT"
  reject_forbidden_path "$GIT_CREDENTIAL_INPUT"

  case "$GIT_CREDENTIAL_INPUT" in
    /*) ;;
    *) die 'Git credential file path must be absolute' 64 ;;
  esac
  test -f "$GIT_CREDENTIAL_INPUT" || die 'Git credential file is not a regular file' 64
  test ! -L "$GIT_CREDENTIAL_INPUT" || die 'Git credential file must not be a symlink' 64
  GIT_CREDENTIAL_FILE="$(/usr/bin/realpath -e -- "$GIT_CREDENTIAL_INPUT")"
  GIT_CREDENTIAL_MODE="$(/usr/bin/stat -c '%a' -- "$GIT_CREDENTIAL_FILE")"
  case "$GIT_CREDENTIAL_MODE" in
    400 | 600) ;;
    *) die 'Git credential file must have owner-only mode 0400 or 0600' 64 ;;
  esac
  readonly GIT_CREDENTIAL_FILE GIT_CREDENTIAL_MODE

  REPO_ROOT="$(/usr/bin/realpath -e -- "$REPO_INPUT")"
  test -d "$REPO_ROOT" || die 'repository path is not a directory' 64
fi

case "$OUTPUT_INPUT" in
  /*) ;;
  *) die 'output directory must be absolute' 64 ;;
esac

if [ "$MODE" = run ]; then
  require_value --predecessor-sha "$PREDECESSOR_SHA"
  require_value --candidate-sha "$CANDIDATE_SHA"
  require_value --plan-blob "$PLAN_BLOB"
  require_value --design-blob "$DESIGN_BLOB"
  require_value --remote-endpoint-sha256 "$REMOTE_ENDPOINT_SHA256"
  require_value --producer-checks-evidence "$PRODUCER_CHECKS_EVIDENCE_INPUT"
  require_value --producer-checks-evidence-sha256 "$PRODUCER_CHECKS_EVIDENCE_SHA256"
  require_value --reviewer-bin "$REVIEWER_BIN"
  require_value --codegraph-bin "$CODEGRAPH_BIN"
  require_lower_hex predecessor-sha "$PREDECESSOR_SHA" 40
  require_lower_hex candidate-sha "$CANDIDATE_SHA" 40
  require_lower_hex plan-blob "$PLAN_BLOB" 40
  require_lower_hex design-blob "$DESIGN_BLOB" 40
  require_lower_hex remote-endpoint-sha256 "$REMOTE_ENDPOINT_SHA256" 64
  require_lower_hex producer-checks-evidence-sha256 "$PRODUCER_CHECKS_EVIDENCE_SHA256" 64
  test -x "$REVIEWER_BIN" || die "reviewer binary is not executable: $REVIEWER_BIN" 64
  test -x "$CODEGRAPH_BIN" || die "CodeGraph binary is not executable: $CODEGRAPH_BIN" 64
  reject_forbidden_path "$PRODUCER_CHECKS_EVIDENCE_INPUT"
  case "$PRODUCER_CHECKS_EVIDENCE_INPUT" in
    /*) ;;
    *) die 'producer checks evidence path must be absolute' 64 ;;
  esac
  test ! -L "$PRODUCER_CHECKS_EVIDENCE_INPUT" ||
    die 'producer checks evidence must not be a symlink' 64
  PRODUCER_CHECKS_EVIDENCE_INPUT="$(
    /usr/bin/realpath -e -- "$PRODUCER_CHECKS_EVIDENCE_INPUT"
  )"
  test -f "$PRODUCER_CHECKS_EVIDENCE_INPUT" ||
    die 'producer checks evidence is not a regular file' 64

  OUTPUT_PARENT="$(/usr/bin/realpath -e -- "$(dirname "$OUTPUT_INPUT")")"
  OUTPUT_DIR="$OUTPUT_PARENT/$(basename "$OUTPUT_INPUT")"
  test ! -e "$OUTPUT_DIR" || die "output directory already exists: $OUTPUT_DIR" 73
else
  test ! -L "$OUTPUT_INPUT" || die 'recovery output directory must not be a symlink' 64
  OUTPUT_DIR="$(/usr/bin/realpath -e -- "$OUTPUT_INPUT")"
  test -d "$OUTPUT_DIR" || die 'existing output directory is not a directory' 64
fi

if [ -n "$REPO_ROOT" ]; then
  case "$OUTPUT_DIR/" in
    "$REPO_ROOT"/*) die 'output directory must be outside the repository worktree' 64 ;;
  esac
fi

git_at() {
  local worktree="$1"
  shift
  GIT_CONFIG_NOSYSTEM=1 \
  GIT_CONFIG_GLOBAL=/dev/null \
  GIT_TERMINAL_PROMPT=0 \
  GIT_ASKPASS=/bin/false \
  SSH_ASKPASS=/bin/false \
    "$GIT_BIN" -c credential.helper= \
      -c "credential.helper=store --file=$GIT_CREDENTIAL_FILE" \
      -C "$worktree" "$@"
}

git_repo() {
  git_at "$REPO_ROOT" "$@"
}

hash_text() {
  printf '%s' "$1" | sha256sum | awk '{print $1}'
}

fsync_output_directory() {
  OUTPUT_DIR="$OUTPUT_DIR" /usr/bin/python3 - <<'PY'
import os

if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
    raise SystemExit("output durability requires O_NOFOLLOW and O_DIRECTORY")
descriptor = os.open(
    os.environ["OUTPUT_DIR"],
    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
)
try:
    os.fsync(descriptor)
finally:
    os.close(descriptor)
PY
}

fsync_output_parent() {
  OUTPUT_PARENT="$OUTPUT_PARENT" /usr/bin/python3 - <<'PY'
import os
import stat

if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
    raise SystemExit("output parent durability requires O_NOFOLLOW and O_DIRECTORY")
descriptor = os.open(
    os.environ["OUTPUT_PARENT"],
    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
)
try:
    metadata = os.fstat(descriptor)
    if not stat.S_ISDIR(metadata.st_mode):
        raise SystemExit("output parent is not a directory")
    os.fsync(descriptor)
finally:
    os.close(descriptor)
PY
}

COMMON_GIT_DIR=''
REMOTE_ENDPOINT=''

assert_repository_controls() {
  local current_common replacement_refs shallow
  current_common="$(git_repo rev-parse --path-format=absolute --git-common-dir)"
  test -n "$current_common" || die 'Git common directory lookup returned empty output' 66
  test "${current_common//$'\n'/}" = "$current_common" ||
    die 'Git common directory lookup returned multiple lines' 66
  if [ -n "$COMMON_GIT_DIR" ]; then
    test "$current_common" = "$COMMON_GIT_DIR" || die 'Git common directory changed' 66
  else
    COMMON_GIT_DIR="$current_common"
  fi

  replacement_refs="$(git_repo for-each-ref --format='%(refname)' refs/replace/)"
  test -z "$replacement_refs" || die 'replacement refs are forbidden' 66
  if test -e "$COMMON_GIT_DIR/info/grafts" || test -L "$COMMON_GIT_DIR/info/grafts"; then
    die 'common Git graft file is forbidden' 66
  fi
  shallow="$(git_repo rev-parse --is-shallow-repository)"
  test "$shallow" = false || die 'shallow repositories are forbidden' 66
}

capture_and_validate_remote_endpoint() {
  local endpoint endpoint_hash
  endpoint="$(git_repo remote get-url --push --all origin 2>/dev/null)"
  test -n "$endpoint" || die 'origin push endpoint is empty' 66
  test "${endpoint//$'\n'/}" = "$endpoint" || die 'origin must have exactly one push endpoint' 66
  endpoint_hash="$(hash_text "$endpoint")"
  test "$endpoint_hash" = "$REMOTE_ENDPOINT_SHA256" ||
    die 'origin push endpoint digest does not match the candidate-construction handoff' 66
  if [ -n "$REMOTE_ENDPOINT" ]; then
    test "$endpoint" = "$REMOTE_ENDPOINT" || die 'origin push endpoint changed' 66
  else
    REMOTE_ENDPOINT="$endpoint"
  fi
}

assert_candidate_invariants() {
  local parent_text commit_count changed_paths current_plan_blob current_design_blob
  local coordinator_head coordinator_status
  local -a commit_and_parent

  assert_repository_controls
  capture_and_validate_remote_endpoint
  git_repo cat-file -e "$CANDIDATE_SHA^{commit}"
  parent_text="$(git_repo rev-list --parents -n 1 "$CANDIDATE_SHA")"
  read -r -a commit_and_parent <<< "$parent_text"
  test "${#commit_and_parent[@]}" -eq 2 || die 'candidate must have exactly one parent' 66
  test "${commit_and_parent[0]}" = "$CANDIDATE_SHA" || die 'candidate identity changed' 66
  test "${commit_and_parent[1]}" = "$PREDECESSOR_SHA" ||
    die 'candidate parent is not the immutable predecessor' 66
  commit_count="$(git_repo rev-list --count "$PREDECESSOR_SHA..$CANDIDATE_SHA")"
  test "$commit_count" -eq 1 || die 'candidate range must contain exactly one commit' 66
  changed_paths="$(
    git_repo diff-tree --no-commit-id --name-only -r --no-renames "$CANDIDATE_SHA"
  )"
  test "$changed_paths" = "$PLAN_PATH"$'\n'"$DESIGN_PATH" ||
    die 'candidate must change exactly the governance plan and core design paths' 66
  current_plan_blob="$(git_repo rev-parse "$CANDIDATE_SHA:$PLAN_PATH")"
  current_design_blob="$(git_repo rev-parse "$CANDIDATE_SHA:$DESIGN_PATH")"
  test "$current_plan_blob" = "$PLAN_BLOB" || die 'candidate plan blob changed' 66
  test "$current_design_blob" = "$DESIGN_BLOB" || die 'candidate design blob changed' 66
  coordinator_head="$(git_repo rev-parse HEAD)"
  test "$coordinator_head" = "$CANDIDATE_SHA" || die 'coordinator HEAD is not the candidate' 66
  git_repo diff --quiet || die 'coordinator has unstaged tracked changes' 66
  git_repo diff --cached --quiet || die 'coordinator has staged changes' 66
  coordinator_status="$(git_repo status --porcelain --untracked-files=all)"
  test -z "$coordinator_status" || die 'coordinator worktree is not clean' 66
}

validate_codegraph_evidence() {
  /usr/bin/python3 - "$@" <<'PY'
import os
import re
import stat
import sys

diagnostic = re.compile(
    r"^(?:no indexed file matches\b|symbol(?: .*)? not found(?: in (?:the )?(?:index|codebase))?\b|"
    r"file not found(?: in (?:the )?(?:index|codebase))?\b|.*not found in (?:the )?(?:index|codebase)\b)",
    re.IGNORECASE | re.MULTILINE,
)

for raw_path in sys.argv[1:]:
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(raw_path, flags)
    except OSError as error:
        print(f"CodeGraph evidence open failed for {raw_path}: {error}", file=sys.stderr)
        raise SystemExit(os.EX_DATAERR)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size <= 0 or metadata.st_size > 8_388_608:
            print(f"CodeGraph evidence size/type invalid for {raw_path}", file=sys.stderr)
            raise SystemExit(os.EX_DATAERR)
        source = os.read(descriptor, metadata.st_size + 1)
        if len(source) != metadata.st_size:
            print(f"CodeGraph evidence changed while reading: {raw_path}", file=sys.stderr)
            raise SystemExit(os.EX_DATAERR)
    finally:
        os.close(descriptor)
    try:
        text = source.decode("utf-8")
    except UnicodeDecodeError:
        print(f"CodeGraph evidence is not UTF-8: {raw_path}", file=sys.stderr)
        raise SystemExit(os.EX_DATAERR)
    if "\x00" in text or diagnostic.search(text):
        print(f"CodeGraph evidence contains a lookup diagnostic: {raw_path}", file=sys.stderr)
        raise SystemExit(os.EX_DATAERR)
PY
}

validate_codegraph_query_semantics() {
  local evidence_path="$1"
  local query_kind="$2"
  local project_path="$3"
  shift 3
  /usr/bin/python3 - "$evidence_path" "$query_kind" "$project_path" "$@" <<'PY'
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
kind = sys.argv[2]
project = Path(sys.argv[3])
expected_paths = sys.argv[4:]
try:
    text = path.read_text(encoding="utf-8")
except (OSError, UnicodeError) as error:
    print(f"CodeGraph semantic validation read failed: {error}", file=sys.stderr)
    raise SystemExit(65)

negative_status = re.compile(
    r"(?im)^(?:source|call path|file|symbol)\s*:.*\b(?:unavailable|failed|"
    r"could not|cannot|no usable|no result)\b"
)
if negative_status.search(text):
    print("CodeGraph query output contains a negative semantic status", file=sys.stderr)
    raise SystemExit(65)

def source_anchors(relative_path):
    source_path = project / relative_path
    try:
        lines = source_path.read_text(encoding="utf-8").split("\n")
    except (OSError, UnicodeError) as error:
        print(f"cannot read CodeGraph source anchor file {relative_path}: {error}", file=sys.stderr)
        raise SystemExit(65)
    candidates = [line.strip() for line in lines if len(line.strip()) >= 12]
    if not candidates:
        print(f"CodeGraph source anchor file has no usable lines: {relative_path}", file=sys.stderr)
        raise SystemExit(65)
    indexes = sorted({0, len(candidates) // 2, len(candidates) - 1})
    return [candidates[index] for index in indexes]

if kind == "explore":
    if not expected_paths or not any(relative in text for relative in expected_paths):
        print("CodeGraph explore output identifies no requested Node 2C path", file=sys.stderr)
        raise SystemExit(65)
    anchors = [anchor for relative in expected_paths for anchor in source_anchors(relative)]
    if not any(anchor in text for anchor in anchors):
        print("CodeGraph explore output contains no verbatim source anchor", file=sys.stderr)
        raise SystemExit(65)
    if "->" not in text:
        print("CodeGraph explore output contains no concrete call-path edge", file=sys.stderr)
        raise SystemExit(65)
elif kind == "node":
    if len(expected_paths) != 1:
        print("CodeGraph node validation requires exactly one requested path", file=sys.stderr)
        raise SystemExit(65)
    expected = expected_paths[0]
    if expected not in text:
        print(
            f"CodeGraph node output does not identify requested path: {expected}",
            file=sys.stderr,
        )
        raise SystemExit(65)
    for anchor in source_anchors(expected):
        if anchor not in text:
            print(
                f"CodeGraph node output lacks verbatim source anchor for {expected}: {anchor!r}",
                file=sys.stderr,
            )
            raise SystemExit(65)
else:
    print(f"unknown CodeGraph semantic validation kind: {kind}", file=sys.stderr)
    raise SystemExit(65)
PY
}

snapshot_worktree_tree() {
  local worktree="$1"
  local output="$2"
  /usr/bin/python3 - "$worktree" "$output" <<'PY'
import hashlib
import json
import os
import stat
import sys

root = os.path.realpath(sys.argv[1])
output = sys.argv[2]
try:
    root_metadata = os.stat(root, follow_symlinks=False)
except OSError as error:
    print(f"worktree snapshot root stat failed: {error}", file=sys.stderr)
    raise SystemExit(66)
if not stat.S_ISDIR(root_metadata.st_mode):
    print("worktree snapshot root is not a directory", file=sys.stderr)
    raise SystemExit(66)
entries = [
    {
        "mode": stat.S_IMODE(root_metadata.st_mode),
        "path": ".",
        "type": "directory",
    }
]

def walk(directory, relative_parent=""):
    try:
        children = sorted(os.scandir(directory), key=lambda entry: entry.name.encode("utf-8"))
    except OSError as error:
        print(f"worktree snapshot scan failed: {error}", file=sys.stderr)
        raise SystemExit(66)
    for entry in children:
        relative = entry.name if not relative_parent else f"{relative_parent}/{entry.name}"
        try:
            metadata = entry.stat(follow_symlinks=False)
        except OSError as error:
            print(f"worktree snapshot stat failed for {relative}: {error}", file=sys.stderr)
            raise SystemExit(66)
        mode = stat.S_IMODE(metadata.st_mode)
        if stat.S_ISDIR(metadata.st_mode):
            entries.append({"mode": mode, "path": relative, "type": "directory"})
            walk(entry.path, relative)
        elif stat.S_ISREG(metadata.st_mode):
            digest = hashlib.sha256()
            try:
                with open(entry.path, "rb", buffering=0) as handle:
                    while True:
                        block = handle.read(1_048_576)
                        if not block:
                            break
                        digest.update(block)
            except OSError as error:
                print(f"worktree snapshot read failed for {relative}: {error}", file=sys.stderr)
                raise SystemExit(66)
            entries.append(
                {
                    "mode": mode,
                    "path": relative,
                    "sha256": digest.hexdigest(),
                    "size": metadata.st_size,
                    "type": "regular",
                }
            )
        elif stat.S_ISLNK(metadata.st_mode):
            try:
                target = os.readlink(entry.path)
            except OSError as error:
                print(f"worktree snapshot symlink read failed for {relative}: {error}", file=sys.stderr)
                raise SystemExit(66)
            entries.append(
                {"mode": mode, "path": relative, "target": target, "type": "symlink"}
            )
        else:
            print(f"worktree snapshot rejects special path: {relative}", file=sys.stderr)
            raise SystemExit(66)

walk(root)
source = json.dumps(
    entries,
    ensure_ascii=True,
    allow_nan=False,
    separators=(",", ":"),
    sort_keys=True,
).encode("ascii") + b"\n"
flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
if hasattr(os, "O_NOFOLLOW"):
    flags |= os.O_NOFOLLOW
try:
    descriptor = os.open(output, flags, 0o600)
except OSError as error:
    print(f"worktree snapshot output open failed: {error}", file=sys.stderr)
    raise SystemExit(73)
try:
    offset = 0
    while offset < len(source):
        written = os.write(descriptor, source[offset:])
        if written <= 0:
            print("worktree snapshot output short write", file=sys.stderr)
            raise SystemExit(73)
        offset += written
    os.fsync(descriptor)
finally:
    os.close(descriptor)
PY
}

parse_review_stream() {
  local stream_path="$1"
  local report_path="$2"
  /usr/bin/python3 - "$stream_path" "$report_path" <<'PY'
import hashlib
import json
import os
import stat
import sys

stream_path, report_path = sys.argv[1:]
forbidden_separators = {"\r", "\v", "\f", "\x85", "\u2028", "\u2029"}

def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result

if not hasattr(os, "O_NOFOLLOW"):
    raise SystemExit("review stream parser requires O_NOFOLLOW")
flags = os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW
try:
    descriptor = os.open(stream_path, flags)
except OSError as error:
    print(f"review stream open failed: {error}", file=sys.stderr)
    raise SystemExit(os.EX_DATAERR)
try:
    metadata = os.fstat(descriptor)
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_nlink != 1
        or metadata.st_mode & 0o777 != 0o600
        or metadata.st_size <= 0
        or metadata.st_size >= 16_777_216
    ):
        print("review stream size/type is invalid", file=sys.stderr)
        raise SystemExit(os.EX_DATAERR)
    stream_bytes = os.read(descriptor, metadata.st_size + 1)
    if len(stream_bytes) != metadata.st_size:
        print("review stream changed while reading", file=sys.stderr)
        raise SystemExit(os.EX_DATAERR)
finally:
    os.close(descriptor)

try:
    stream_text = stream_bytes.decode("utf-8")
except UnicodeDecodeError:
    print("review stream is not UTF-8", file=sys.stderr)
    raise SystemExit(os.EX_DATAERR)
if any(separator in stream_text for separator in forbidden_separators):
    print("review stream contains a forbidden non-LF line separator", file=sys.stderr)
    raise SystemExit(os.EX_DATAERR)
if not stream_text.endswith("\n"):
    print("review stream must end with one literal LF-delimited record", file=sys.stderr)
    raise SystemExit(os.EX_DATAERR)
record_lines = stream_text[:-1].split("\n")
if not record_lines or any(not line for line in record_lines):
    print("review stream contains an empty JSONL record", file=sys.stderr)
    raise SystemExit(os.EX_DATAERR)

assistant_messages = []
current_message = None
terminal_results = []
event_count = 0
try:
    for line_number, line in enumerate(record_lines, 1):
        event = json.loads(line, object_pairs_hook=reject_duplicates)
        if type(event) is not dict:
            raise ValueError(f"line {line_number} is not an object")
        event_count += 1
        if event.get("type") == "stream_event":
            nested = event.get("event")
            if type(nested) is not dict:
                raise ValueError(f"line {line_number} has a non-object stream event")
            nested_type = nested.get("type")
            if nested_type == "message_start":
                if current_message is not None:
                    raise ValueError(f"line {line_number} starts a nested assistant message")
                message = nested.get("message")
                if type(message) is not dict or message.get("role") != "assistant":
                    raise ValueError(f"line {line_number} does not start an assistant message")
                current_message = []
            elif nested_type == "content_block_delta":
                delta = nested.get("delta")
                if type(delta) is dict and delta.get("type") == "text_delta":
                    if current_message is None:
                        raise ValueError(f"line {line_number} has text outside an assistant message")
                    text = delta.get("text")
                    if type(text) is not str:
                        raise ValueError(f"line {line_number} has non-string text delta")
                    current_message.append(text)
            elif nested_type == "message_stop":
                if current_message is None:
                    raise ValueError(f"line {line_number} stops no assistant message")
                assistant_messages.append("".join(current_message))
                current_message = None
        if event.get("type") == "result":
            terminal_results.append((event_count, event))
except (json.JSONDecodeError, ValueError) as error:
    print(f"review stream parse failed: {error}", file=sys.stderr)
    raise SystemExit(os.EX_DATAERR)

if current_message is not None:
    print("review stream ended inside an assistant message", file=sys.stderr)
    raise SystemExit(os.EX_DATAERR)
if len(terminal_results) != 1:
    print("review stream must contain exactly one terminal result", file=sys.stderr)
    raise SystemExit(os.EX_DATAERR)
terminal_position, terminal = terminal_results[0]
terminal_text = terminal.get("result")
if (
    terminal_position != event_count
    or terminal.get("subtype") != "success"
    or type(terminal_text) is not str
    or not terminal_text
):
    print("review stream terminal result is not one final success", file=sys.stderr)
    raise SystemExit(os.EX_DATAERR)

text_messages = [message for message in assistant_messages if message]
if text_messages:
    report_text = text_messages[-1]
    if report_text != terminal_text:
        print("final assistant message disagrees with terminal result bytes", file=sys.stderr)
        raise SystemExit(os.EX_DATAERR)
else:
    report_text = terminal_text

if not report_text:
    print("parsed review report is empty", file=sys.stderr)
    raise SystemExit(os.EX_DATAERR)
if any(separator in report_text for separator in forbidden_separators):
    print("parsed review report contains a forbidden non-LF line separator", file=sys.stderr)
    raise SystemExit(os.EX_DATAERR)

nonblank_lines = [line for line in report_text.split("\n") if line.strip()]
if not nonblank_lines:
    print("parsed review report has no nonblank lines", file=sys.stderr)
    raise SystemExit(os.EX_DATAERR)
final_line = nonblank_lines[-1]
if final_line not in {"VERDICT: PASS", "VERDICT: REVISE"}:
    print("invalid final review line", file=sys.stderr)
    raise SystemExit(os.EX_DATAERR)

report_bytes = report_text.encode("utf-8")
if len(report_bytes) > 1_048_576:
    print("parsed review report exceeds the size limit", file=sys.stderr)
    raise SystemExit(os.EX_DATAERR)
digest = hashlib.sha256(report_bytes).hexdigest()

if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
    raise SystemExit("review report output requires O_NOFOLLOW and O_DIRECTORY")
output_dir = os.path.dirname(report_path)
directory_descriptor = os.open(
    output_dir,
    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
)

def write_exclusive(name, data):
    descriptor = os.open(
        name,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600,
        dir_fd=directory_descriptor,
    )
    try:
        offset = 0
        while offset < len(data):
            written = os.write(descriptor, data[offset:])
            if written <= 0:
                raise OSError("short write")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)

try:
    write_exclusive(os.path.basename(report_path), report_bytes)
    os.fsync(directory_descriptor)
except FileExistsError:
    print("review report output already exists", file=sys.stderr)
    raise SystemExit(os.EX_CANTCREAT)
except OSError as error:
    print(f"review report output failed: {error}", file=sys.stderr)
    raise SystemExit(os.EX_CANTCREAT)
finally:
    os.close(directory_descriptor)

print(digest)
print(final_line)
PY
}

validate_review_raw_artifacts() {
  local stream_path="$1"
  local stderr_path="$2"
  /usr/bin/python3 - "$stream_path" "$stderr_path" <<'PY'
import os
import stat
import sys

if not hasattr(os, "O_NOFOLLOW"):
    raise SystemExit("review artifact validation requires O_NOFOLLOW")
limit = 16_777_216
try:
    for index, path in enumerate(sys.argv[1:]):
        descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
        try:
            metadata = os.fstat(descriptor)
            minimum = 1 if index == 0 else 0
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_nlink != 1
                or metadata.st_mode & 0o777 != 0o600
                or metadata.st_size < minimum
                or metadata.st_size >= limit
            ):
                raise ValueError("review artifact size, type, link count, or mode is invalid")
            source = os.read(descriptor, metadata.st_size + 1)
            if len(source) != metadata.st_size:
                raise ValueError("review artifact changed while reading")
        finally:
            os.close(descriptor)
except (OSError, ValueError) as error:
    print(f"review artifact validation failed: {error}", file=sys.stderr)
    raise SystemExit(os.EX_DATAERR)
PY
}

seal_review_artifacts() {
  local seal_mode="$1"
  /usr/bin/python3 - "$seal_mode" "$OUTPUT_DIR" <<'PY'
import hashlib
import os
import stat
import sys


class ArtifactValidationError(Exception):
    pass


class ArtifactRetentionError(Exception):
    pass


mode, output_dir = sys.argv[1:]
complete_specs = [
    ("review-report.md", "review-report.sha256", 1, 1_048_576),
    ("review-stream.jsonl", "review-stream.sha256", 1, 16_777_215),
    ("reviewer-stderr.txt", "reviewer-stderr.sha256", 0, 16_777_215),
]
if mode == "complete":
    specs = complete_specs
elif mode == "diagnostics":
    specs = complete_specs[1:]
else:
    raise SystemExit("unknown review artifact sealing mode")

if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
    raise SystemExit("review artifact sealing requires O_NOFOLLOW and O_DIRECTORY")


def metadata_signature(metadata):
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_nlink,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def validate_metadata(metadata, minimum, maximum, label):
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_nlink != 1
        or stat.S_IMODE(metadata.st_mode) != 0o600
        or metadata.st_size < minimum
        or metadata.st_size > maximum
    ):
        raise ArtifactValidationError(
            f"{label} must be a single-link mode-0600 regular file within bounds"
        )


def read_artifact(directory_descriptor, basename, minimum, maximum):
    try:
        descriptor = os.open(
            basename,
            os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW,
            dir_fd=directory_descriptor,
        )
    except OSError as error:
        raise ArtifactValidationError(f"{basename} open failed: {error}") from error
    try:
        before = os.fstat(descriptor)
        validate_metadata(before, minimum, maximum, basename)
        chunks = []
        remaining = before.st_size + 1
        while remaining:
            block = os.read(descriptor, min(1_048_576, remaining))
            if not block:
                break
            chunks.append(block)
            remaining -= len(block)
        source = b"".join(chunks)
        if len(source) != before.st_size:
            raise ArtifactValidationError(f"{basename} changed while reading")
        try:
            os.fsync(descriptor)
        except OSError as error:
            raise ArtifactRetentionError(f"{basename} fsync failed: {error}") from error
        after = os.fstat(descriptor)
        validate_metadata(after, minimum, maximum, basename)
        if metadata_signature(after) != metadata_signature(before):
            raise ArtifactValidationError(f"{basename} metadata changed while sealing")
        return descriptor, before, source
    except BaseException:
        os.close(descriptor)
        raise


def write_sidecar(directory_descriptor, basename, source):
    descriptor = None
    keep = False
    try:
        descriptor = os.open(
            basename,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory_descriptor,
        )
    except FileExistsError as error:
        raise ArtifactRetentionError(f"{basename} already exists") from error
    except OSError as error:
        raise ArtifactRetentionError(f"{basename} creation failed: {error}") from error
    try:
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or stat.S_IMODE(metadata.st_mode) != 0o600
        ):
            raise ArtifactRetentionError(f"{basename} output metadata is invalid")
        offset = 0
        while offset < len(source):
            written = os.write(descriptor, source[offset:])
            if written <= 0:
                raise ArtifactRetentionError(f"{basename} short write")
            offset += written
        os.fsync(descriptor)
        final_metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(final_metadata.st_mode)
            or final_metadata.st_nlink != 1
            or stat.S_IMODE(final_metadata.st_mode) != 0o600
            or final_metadata.st_size != len(source)
        ):
            raise ArtifactRetentionError(f"{basename} output changed while writing")
        keep = True
    except OSError as error:
        raise ArtifactRetentionError(f"{basename} write/fsync failed: {error}") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if descriptor is not None and not keep:
            try:
                os.unlink(basename, dir_fd=directory_descriptor)
            except OSError:
                pass
            try:
                os.fsync(directory_descriptor)
            except OSError:
                pass


directory_descriptor = None
artifact_descriptors = []
created_sidecars = []
sealed = []
try:
    try:
        directory_descriptor = os.open(
            output_dir,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        )
    except OSError as error:
        raise ArtifactValidationError(f"review artifact directory open failed: {error}") from error
    for basename, sidecar_basename, minimum, maximum in specs:
        descriptor, metadata, source = read_artifact(
            directory_descriptor, basename, minimum, maximum
        )
        artifact_descriptors.append((basename, descriptor, metadata, minimum, maximum))
        sealed.append((basename, sidecar_basename, source, hashlib.sha256(source).hexdigest()))

    for _, sidecar_basename, _, digest in sealed:
        write_sidecar(
            directory_descriptor,
            sidecar_basename,
            (digest + "\n").encode("ascii"),
        )
        created_sidecars.append(sidecar_basename)

    for basename, descriptor, before, minimum, maximum in artifact_descriptors:
        descriptor_metadata = os.fstat(descriptor)
        path_metadata = os.stat(
            basename,
            dir_fd=directory_descriptor,
            follow_symlinks=False,
        )
        validate_metadata(descriptor_metadata, minimum, maximum, basename)
        validate_metadata(path_metadata, minimum, maximum, basename)
        if (
            metadata_signature(descriptor_metadata) != metadata_signature(before)
            or metadata_signature(path_metadata) != metadata_signature(before)
        ):
            raise ArtifactValidationError(f"{basename} path changed while sealing")

    for _, sidecar_basename, _, digest in sealed:
        sidecar_metadata = os.stat(
            sidecar_basename,
            dir_fd=directory_descriptor,
            follow_symlinks=False,
        )
        validate_metadata(sidecar_metadata, 65, 65, sidecar_basename)

    try:
        os.fsync(directory_descriptor)
    except OSError as error:
        raise ArtifactRetentionError(f"review artifact directory fsync failed: {error}") from error
except ArtifactRetentionError as error:
    if directory_descriptor is not None:
        for sidecar_basename in reversed(created_sidecars):
            try:
                os.unlink(sidecar_basename, dir_fd=directory_descriptor)
            except OSError:
                pass
        try:
            os.fsync(directory_descriptor)
        except OSError:
            pass
    print(f"review artifact retention failed: {error}", file=sys.stderr)
    raise SystemExit(os.EX_CANTCREAT)
except (ArtifactValidationError, OSError) as error:
    if directory_descriptor is not None:
        for sidecar_basename in reversed(created_sidecars):
            try:
                os.unlink(sidecar_basename, dir_fd=directory_descriptor)
            except OSError:
                pass
        try:
            os.fsync(directory_descriptor)
        except OSError:
            pass
    print(f"review artifact sealing rejected retained bytes: {error}", file=sys.stderr)
    raise SystemExit(os.EX_DATAERR)
finally:
    for _, descriptor, _, _, _ in artifact_descriptors:
        os.close(descriptor)
    if directory_descriptor is not None:
        os.close(directory_descriptor)

for _, _, source, digest in sealed:
    print(digest)
    print(len(source))
PY
}

verify_report_attestation() {
  local expected_digest="$1"
  EXPECTED_DIGEST="$expected_digest" \
  OUTPUT_DIR="$OUTPUT_DIR" \
    /usr/bin/python3 - <<'PY'
import hashlib
import os
import stat

def read_regular(path, minimum, maximum):
    if not hasattr(os, "O_NOFOLLOW"):
        raise ValueError("O_NOFOLLOW is unavailable")
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    try:
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or stat.S_IMODE(metadata.st_mode) != 0o600
            or metadata.st_size < minimum
            or metadata.st_size > maximum
        ):
            raise ValueError("invalid regular-file size, type, links, or mode")
        source = os.read(descriptor, metadata.st_size + 1)
        if len(source) != metadata.st_size:
            raise ValueError("file changed while reading")
        return source
    finally:
        os.close(descriptor)

output_dir = os.environ["OUTPUT_DIR"]
specs = [
    ("review-report.md", "review-report.sha256", 1, 1_048_576),
    ("review-stream.jsonl", "review-stream.sha256", 1, 16_777_215),
    ("reviewer-stderr.txt", "reviewer-stderr.sha256", 0, 16_777_215),
]
try:
    digests = {}
    for basename, sidecar_basename, minimum, maximum in specs:
        source = read_regular(os.path.join(output_dir, basename), minimum, maximum)
        sidecar = read_regular(os.path.join(output_dir, sidecar_basename), 65, 65)
        digest = hashlib.sha256(source).hexdigest()
        if sidecar != (digest + "\n").encode("ascii"):
            raise ValueError(f"{basename} SHA-256 sidecar mismatch")
        digests[basename] = digest
except (OSError, ValueError) as error:
    print(f"review artifact attestation failed: {error}", file=os.sys.stderr)
    raise SystemExit(os.EX_DATAERR)

expected = os.environ["EXPECTED_DIGEST"]
if digests["review-report.md"] != expected:
    print("review report bytes do not match the coordinator attestation", file=os.sys.stderr)
    raise SystemExit(os.EX_DATAERR)
PY
}

write_review_revise_manifest() {
  PREDECESSOR_SHA="$PREDECESSOR_SHA" \
  CANDIDATE_SHA="$CANDIDATE_SHA" \
  REVIEW_HEAD_SHA="$REVIEW_HEAD_SHA" \
  REVIEW_REPORT_SHA256="$REVIEW_REPORT_SHA256" \
  REVIEW_REPORT_BYTE_COUNT="$REVIEW_REPORT_BYTE_COUNT" \
  REVIEW_STREAM_SHA256="$REVIEW_STREAM_SHA256" \
  REVIEW_STREAM_BYTE_COUNT="$REVIEW_STREAM_BYTE_COUNT" \
  REVIEW_STDERR_SHA256="$REVIEW_STDERR_SHA256" \
  REVIEW_STDERR_BYTE_COUNT="$REVIEW_STDERR_BYTE_COUNT" \
  OUTPUT_DIR="$OUTPUT_DIR" \
    /usr/bin/python3 - <<'PY'
import hashlib
import json
import os
import stat


def byte_count(name):
    value = os.environ[name]
    if not value.isascii() or not value.isdecimal():
        raise ValueError(f"{name} is not a decimal byte count")
    return int(value)


artifacts = [
    {
        "basename": "review-report.md",
        "byte_count": byte_count("REVIEW_REPORT_BYTE_COUNT"),
        "sha256": os.environ["REVIEW_REPORT_SHA256"],
    },
    {
        "basename": "review-stream.jsonl",
        "byte_count": byte_count("REVIEW_STREAM_BYTE_COUNT"),
        "sha256": os.environ["REVIEW_STREAM_SHA256"],
    },
    {
        "basename": "reviewer-stderr.txt",
        "byte_count": byte_count("REVIEW_STDERR_BYTE_COUNT"),
        "sha256": os.environ["REVIEW_STDERR_SHA256"],
    },
]
payload = {
    "artifact_count": 3,
    "artifacts": artifacts,
    "candidate_sha": os.environ["CANDIDATE_SHA"],
    "predecessor_sha": os.environ["PREDECESSOR_SHA"],
    "review_effort": "max",
    "review_exit_status": 0,
    "review_final_nonblank_line": "VERDICT: REVISE",
    "review_head_sha": os.environ["REVIEW_HEAD_SHA"],
    "review_model": "claude-fable-5",
    "state_version": 2,
}
source = json.dumps(
    payload,
    ensure_ascii=True,
    allow_nan=False,
    separators=(",", ":"),
    sort_keys=True,
).encode("ascii") + b"\n"
digest = hashlib.sha256(source).hexdigest()

if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
    raise SystemExit("REVISE manifest retention requires O_NOFOLLOW and O_DIRECTORY")

directory_descriptor = None


def write_exclusive(basename, data):
    descriptor = os.open(
        basename,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600,
        dir_fd=directory_descriptor,
    )
    keep = False
    try:
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or stat.S_IMODE(metadata.st_mode) != 0o600
        ):
            raise OSError(f"{basename} output metadata is invalid")
        offset = 0
        while offset < len(data):
            written = os.write(descriptor, data[offset:])
            if written <= 0:
                raise OSError(f"{basename} short write")
            offset += written
        os.fsync(descriptor)
        final_metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(final_metadata.st_mode)
            or final_metadata.st_nlink != 1
            or stat.S_IMODE(final_metadata.st_mode) != 0o600
            or final_metadata.st_size != len(data)
        ):
            raise OSError(f"{basename} changed while writing")
        keep = True
    finally:
        os.close(descriptor)
        if not keep:
            try:
                os.unlink(basename, dir_fd=directory_descriptor)
            finally:
                os.fsync(directory_descriptor)


try:
    directory_descriptor = os.open(
        os.environ["OUTPUT_DIR"],
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
    )
    write_exclusive("review-revise.json", source)
    try:
        write_exclusive("review-revise.sha256", (digest + "\n").encode("ascii"))
    except BaseException:
        os.unlink("review-revise.json", dir_fd=directory_descriptor)
        os.fsync(directory_descriptor)
        raise
    os.fsync(directory_descriptor)
except FileExistsError:
    print("REVISE manifest or SHA sidecar already exists", file=os.sys.stderr)
    raise SystemExit(os.EX_CANTCREAT)
except (OSError, ValueError) as error:
    print(f"REVISE manifest durable creation failed: {error}", file=os.sys.stderr)
    raise SystemExit(os.EX_CANTCREAT)
finally:
    if directory_descriptor is not None:
        os.close(directory_descriptor)

print(digest)
PY
}

validate_revise_handoff() {
  OUTPUT_DIR="$OUTPUT_DIR" /usr/bin/python3 - <<'PY'
import hashlib
import json
import os
import re
import stat


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f"non-finite JSON number is forbidden: {value}")


def metadata_signature(metadata):
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_nlink,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def read_regular(directory_descriptor, basename, minimum, maximum):
    descriptor = os.open(
        basename,
        os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW,
        dir_fd=directory_descriptor,
    )
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or stat.S_IMODE(before.st_mode) != 0o600
            or before.st_size < minimum
            or before.st_size > maximum
        ):
            raise ValueError(
                f"{basename} must be a single-link mode-0600 regular file within bounds"
            )
        chunks = []
        remaining = before.st_size + 1
        while remaining:
            block = os.read(descriptor, min(1_048_576, remaining))
            if not block:
                break
            chunks.append(block)
            remaining -= len(block)
        source = b"".join(chunks)
        after = os.fstat(descriptor)
        path_metadata = os.stat(
            basename,
            dir_fd=directory_descriptor,
            follow_symlinks=False,
        )
        if (
            len(source) != before.st_size
            or metadata_signature(after) != metadata_signature(before)
            or metadata_signature(path_metadata) != metadata_signature(before)
        ):
            raise ValueError(f"{basename} changed while reading")
        return source
    finally:
        os.close(descriptor)


def parse_review_stream(source):
    forbidden = {"\r", "\v", "\f", "\x85", "\u2028", "\u2029"}
    text = source.decode("utf-8")
    if any(separator in text for separator in forbidden):
        raise ValueError("review stream contains a forbidden non-LF line separator")
    if not text.endswith("\n"):
        raise ValueError("review stream lacks its final literal LF")
    records = text[:-1].split("\n")
    if not records or any(not record for record in records):
        raise ValueError("review stream contains an empty JSONL record")

    assistant_messages = []
    current_message = None
    terminal_results = []
    for position, record in enumerate(records, 1):
        event = json.loads(
            record,
            object_pairs_hook=reject_duplicates,
            parse_constant=reject_constant,
        )
        if type(event) is not dict:
            raise ValueError("review stream record is not an object")
        if event.get("type") == "stream_event":
            nested = event.get("event")
            if type(nested) is not dict:
                raise ValueError("review stream event is not an object")
            nested_type = nested.get("type")
            if nested_type == "message_start":
                message = nested.get("message")
                if (
                    current_message is not None
                    or type(message) is not dict
                    or message.get("role") != "assistant"
                ):
                    raise ValueError("invalid assistant message start")
                current_message = []
            elif nested_type == "content_block_delta":
                delta = nested.get("delta")
                if type(delta) is dict and delta.get("type") == "text_delta":
                    value = delta.get("text")
                    if current_message is None or type(value) is not str:
                        raise ValueError("invalid assistant text delta")
                    current_message.append(value)
            elif nested_type == "message_stop":
                if current_message is None:
                    raise ValueError("assistant message stop has no start")
                assistant_messages.append("".join(current_message))
                current_message = None
        if event.get("type") == "result":
            terminal_results.append((position, event))

    if current_message is not None or len(terminal_results) != 1:
        raise ValueError("review stream has an incomplete or non-unique terminal result")
    terminal_position, terminal = terminal_results[0]
    terminal_text = terminal.get("result")
    if (
        terminal_position != len(records)
        or terminal.get("subtype") != "success"
        or type(terminal_text) is not str
        or not terminal_text
    ):
        raise ValueError("review stream terminal result is invalid")
    text_messages = [message for message in assistant_messages if message]
    if text_messages and text_messages[-1] != terminal_text:
        raise ValueError("review stream deltas disagree with terminal result")
    return text_messages[-1] if text_messages else terminal_text


if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
    raise SystemExit("REVISE handoff validation requires O_NOFOLLOW and O_DIRECTORY")

directory_descriptor = None
try:
    directory_descriptor = os.open(
        os.environ["OUTPUT_DIR"],
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
    )
    manifest_source = read_regular(directory_descriptor, "review-revise.json", 1, 65_536)
    manifest_sidecar = read_regular(directory_descriptor, "review-revise.sha256", 65, 65)
    manifest_digest = hashlib.sha256(manifest_source).hexdigest()
    if manifest_sidecar != (manifest_digest + "\n").encode("ascii"):
        raise ValueError("REVISE manifest SHA-256 mismatch")
    payload = json.loads(
        manifest_source.decode("ascii"),
        object_pairs_hook=reject_duplicates,
        parse_constant=reject_constant,
    )

    expected_keys = {
        "artifact_count", "artifacts", "candidate_sha", "predecessor_sha",
        "review_effort", "review_exit_status", "review_final_nonblank_line",
        "review_head_sha", "review_model", "state_version",
    }
    if type(payload) is not dict or set(payload) != expected_keys:
        raise ValueError("REVISE manifest has the wrong closed shape")
    fixed = {
        "artifact_count": 3,
        "review_effort": "max",
        "review_exit_status": 0,
        "review_final_nonblank_line": "VERDICT: REVISE",
        "review_model": "claude-fable-5",
        "state_version": 2,
    }
    if any(payload[key] != value or type(payload[key]) is not type(value) for key, value in fixed.items()):
        raise ValueError("REVISE manifest fixed policy fields drifted")
    lower_hex = lambda value, width: (
        type(value) is str and re.fullmatch(rf"[0-9a-f]{{{width}}}", value) is not None
    )
    for key in ("candidate_sha", "predecessor_sha", "review_head_sha"):
        if not lower_hex(payload[key], 40):
            raise ValueError(f"REVISE manifest {key} is invalid")
    if payload["review_head_sha"] != payload["candidate_sha"]:
        raise ValueError("REVISE manifest review head is not the rejected candidate")

    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii") + b"\n"
    if manifest_source != canonical:
        raise ValueError("REVISE manifest bytes are not canonical")

    artifact_specs = [
        ("review-report.md", "review-report.sha256", 1, 1_048_576),
        ("review-stream.jsonl", "review-stream.sha256", 1, 16_777_215),
        ("reviewer-stderr.txt", "reviewer-stderr.sha256", 0, 16_777_215),
    ]
    artifacts = payload["artifacts"]
    if type(artifacts) is not list or len(artifacts) != payload["artifact_count"]:
        raise ValueError("REVISE manifest artifact count is invalid")
    retained = {}
    for index, (basename, sidecar_basename, minimum, maximum) in enumerate(artifact_specs):
        artifact = artifacts[index]
        if type(artifact) is not dict or set(artifact) != {"basename", "byte_count", "sha256"}:
            raise ValueError("REVISE manifest artifact entry has the wrong closed shape")
        if artifact["basename"] != basename:
            raise ValueError("REVISE manifest artifact basename/order drifted")
        if type(artifact["byte_count"]) is not int or artifact["byte_count"] < minimum:
            raise ValueError("REVISE manifest artifact byte count is invalid")
        if not lower_hex(artifact["sha256"], 64):
            raise ValueError("REVISE manifest artifact SHA-256 is invalid")
        source = read_regular(directory_descriptor, basename, minimum, maximum)
        sidecar = read_regular(directory_descriptor, sidecar_basename, 65, 65)
        digest = hashlib.sha256(source).hexdigest()
        if (
            artifact["byte_count"] != len(source)
            or artifact["sha256"] != digest
            or sidecar != (digest + "\n").encode("ascii")
        ):
            raise ValueError(f"REVISE manifest artifact binding failed for {basename}")
        retained[basename] = source

    report_text = retained["review-report.md"].decode("utf-8")
    forbidden = {"\r", "\v", "\f", "\x85", "\u2028", "\u2029"}
    if any(separator in report_text for separator in forbidden):
        raise ValueError("retained REVISE report contains a forbidden line separator")
    nonblank = [line for line in report_text.split("\n") if line.strip()]
    if not nonblank or nonblank[-1] != "VERDICT: REVISE":
        raise ValueError("retained report is not a terminal REVISE")
    if parse_review_stream(retained["review-stream.jsonl"]) != report_text:
        raise ValueError("retained stream does not reconstruct the retained report")
except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
    print(f"REVISE repair handoff validation failed: {error}", file=os.sys.stderr)
    raise SystemExit(os.EX_DATAERR)
finally:
    if directory_descriptor is not None:
        os.close(directory_descriptor)

print(f"REPAIR_PREDECESSOR_SHA={payload['predecessor_sha']}")
print(f"REPAIR_REJECTED_CANDIDATE_SHA={payload['candidate_sha']}")
print(f"REPAIR_REVIEW_HEAD_SHA={payload['review_head_sha']}")
PY
}

producer_checks_evidence() {
  local mode="$1"
  local source_path="$2"
  local sidecar_path="$3"
  PRODUCER_EVIDENCE_MODE="$mode" \
  PRODUCER_EVIDENCE_PATH="$source_path" \
  PRODUCER_EVIDENCE_SIDECAR="$sidecar_path" \
  PRODUCER_EVIDENCE_EXPECTED_SHA256="$PRODUCER_CHECKS_EVIDENCE_SHA256" \
  PRODUCER_EVIDENCE_CANDIDATE_SHA="$CANDIDATE_SHA" \
    /usr/bin/python3 - <<'PY'
import hashlib
import json
import os
import re
import stat

def read_regular(path, maximum):
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size <= 0 or metadata.st_size > maximum:
            raise ValueError("invalid regular-file size/type")
        source = os.read(descriptor, metadata.st_size + 1)
        if len(source) != metadata.st_size:
            raise ValueError("file changed while reading")
        return source
    finally:
        os.close(descriptor)

def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result

def write_exclusive(path, data):
    if not hasattr(os, "O_NOFOLLOW"):
        raise ValueError("O_NOFOLLOW is unavailable")
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600,
    )
    try:
        offset = 0
        while offset < len(data):
            written = os.write(descriptor, data[offset:])
            if written <= 0:
                raise OSError("short write")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)

mode = os.environ["PRODUCER_EVIDENCE_MODE"]
path = os.environ["PRODUCER_EVIDENCE_PATH"]
sidecar_path = os.environ["PRODUCER_EVIDENCE_SIDECAR"]
expected_digest = os.environ["PRODUCER_EVIDENCE_EXPECTED_SHA256"]
candidate_sha = os.environ["PRODUCER_EVIDENCE_CANDIDATE_SHA"]
if re.fullmatch(r"[0-9a-f]{64}", expected_digest) is None:
    print("producer evidence expected digest is invalid", file=os.sys.stderr)
    raise SystemExit(os.EX_DATAERR)

try:
    source = read_regular(path, 65_536)
    digest = hashlib.sha256(source).hexdigest()
    if digest != expected_digest:
        raise ValueError("exact-byte SHA-256 mismatch")
    payload = json.loads(source.decode("utf-8"), object_pairs_hook=reject_duplicates)
    expected_payload = {
        "bash_fences": "pass",
        "candidate_sha": candidate_sha,
        "shell_failure_harness": "pass",
    }
    if type(payload) is not dict or payload != expected_payload:
        raise ValueError("closed payload does not bind both PASS checks to the candidate")
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii") + b"\n"
    if source != canonical:
        raise ValueError("evidence bytes are not canonical")
    if mode == "verify":
        sidecar = read_regular(sidecar_path, 128)
        if sidecar != (digest + "\n").encode("ascii"):
            raise ValueError("retained evidence sidecar mismatch")
    elif mode == "install":
        write_exclusive(sidecar_path, (digest + "\n").encode("ascii"))
    else:
        raise ValueError("unknown producer evidence mode")
except FileExistsError:
    print("producer evidence output already exists", file=os.sys.stderr)
    raise SystemExit(os.EX_CANTCREAT)
except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
    print(f"producer evidence validation failed: {error}", file=os.sys.stderr)
    raise SystemExit(os.EX_DATAERR)
PY
}

install_producer_checks_evidence() {
  local retained_path="$OUTPUT_DIR/producer-checks-evidence.json"
  local retained_sha_path="$OUTPUT_DIR/producer-checks-evidence.sha256"
  /usr/bin/python3 - \
    "$PRODUCER_CHECKS_EVIDENCE_INPUT" \
    "$retained_path" <<'PY'
import os
import stat
import sys

source_path, output_path = sys.argv[1:]
if not hasattr(os, "O_NOFOLLOW"):
    raise SystemExit("producer evidence retention requires O_NOFOLLOW")
flags = os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW
try:
    descriptor = os.open(source_path, flags)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size <= 0 or metadata.st_size > 65_536:
            raise ValueError("invalid source size/type")
        source = os.read(descriptor, metadata.st_size + 1)
        if len(source) != metadata.st_size:
            raise ValueError("source changed while reading")
    finally:
        os.close(descriptor)
    output_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    output_descriptor = os.open(output_path, output_flags, 0o600)
    try:
        offset = 0
        while offset < len(source):
            written = os.write(output_descriptor, source[offset:])
            if written <= 0:
                raise OSError("short write")
            offset += written
        os.fsync(output_descriptor)
    finally:
        os.close(output_descriptor)
except FileExistsError:
    print("producer evidence retained output already exists", file=sys.stderr)
    raise SystemExit(os.EX_CANTCREAT)
except (OSError, ValueError) as error:
    print(f"producer evidence retention failed: {error}", file=sys.stderr)
    raise SystemExit(os.EX_DATAERR)
PY
  if producer_checks_evidence install "$retained_path" "$retained_sha_path"; then
    fsync_output_directory
  else
    local status=$?
    /bin/rm -f -- "$retained_path"
    fsync_output_directory || :
    return "$status"
  fi
}

verify_producer_checks_evidence() {
  producer_checks_evidence \
    verify \
    "$OUTPUT_DIR/producer-checks-evidence.json" \
    "$OUTPUT_DIR/producer-checks-evidence.sha256"
}

write_publication_attempt_state() {
  local output_dir="$OUTPUT_DIR"
  verify_producer_checks_evidence
  verify_report_attestation "$REVIEW_REPORT_SHA256"
  OUTPUT_DIR="$output_dir" \
  PREDECESSOR_SHA="$PREDECESSOR_SHA" \
  CANDIDATE_SHA="$CANDIDATE_SHA" \
  PLAN_BLOB="$PLAN_BLOB" \
  DESIGN_BLOB="$DESIGN_BLOB" \
  REMOTE_ENDPOINT_SHA256="$REMOTE_ENDPOINT_SHA256" \
  REVIEW_REPORT_SHA256="$REVIEW_REPORT_SHA256" \
  PRODUCER_CHECKS_EVIDENCE_SHA256="$PRODUCER_CHECKS_EVIDENCE_SHA256" \
    /usr/bin/python3 - <<'PY'
import hashlib
import json
import os

payload = {
    "candidate_sha": os.environ["CANDIDATE_SHA"],
    "design_blob": os.environ["DESIGN_BLOB"],
    "fast_mode": False,
    "node": "team-evidence-aggregation-status-facade-governance-attempt",
    "plan_blob": os.environ["PLAN_BLOB"],
    "predecessor_sha": os.environ["PREDECESSOR_SHA"],
    "producer_checks_evidence_sha256": os.environ["PRODUCER_CHECKS_EVIDENCE_SHA256"],
    "push_attempted": True,
    "read_only": True,
    "remote_endpoint_sha256": os.environ["REMOTE_ENDPOINT_SHA256"],
    "review_effort": "max",
    "review_exit_status": 0,
    "review_final_nonblank_line": "VERDICT: PASS",
    "review_model": "claude-fable-5",
    "review_report_sha256": os.environ["REVIEW_REPORT_SHA256"],
    "state_version": 2,
}
source = json.dumps(
    payload,
    ensure_ascii=True,
    allow_nan=False,
    separators=(",", ":"),
    sort_keys=True,
).encode("ascii") + b"\n"
digest = hashlib.sha256(source).hexdigest()

if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
    raise SystemExit("publication attempt requires O_NOFOLLOW and O_DIRECTORY")
output_dir = os.environ["OUTPUT_DIR"]
directory_descriptor = os.open(
    output_dir,
    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
)

def write_exclusive(name, data):
    descriptor = os.open(
        name,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600,
        dir_fd=directory_descriptor,
    )
    try:
        if os.fstat(descriptor).st_mode & 0o777 != 0o600:
            raise OSError("publication attempt output mode is not 0600")
        offset = 0
        while offset < len(data):
            written = os.write(descriptor, data[offset:])
            if written <= 0:
                raise OSError("short write")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)

try:
    write_exclusive("publication-attempt.json", source)
    try:
        write_exclusive("publication-attempt.sha256", (digest + "\n").encode("ascii"))
    except BaseException:
        os.unlink("publication-attempt.json", dir_fd=directory_descriptor)
        os.fsync(directory_descriptor)
        raise
    os.fsync(directory_descriptor)
except FileExistsError:
    print("publication attempt output already exists", file=os.sys.stderr)
    raise SystemExit(os.EX_CANTCREAT)
except OSError as error:
    print(f"publication attempt output failed: {error}", file=os.sys.stderr)
    raise SystemExit(os.EX_CANTCREAT)
finally:
    os.close(directory_descriptor)
PY
}

read_publication_attempt_state() {
  STATE_PATH="$OUTPUT_DIR/publication-attempt.json" \
  STATE_SHA_PATH="$OUTPUT_DIR/publication-attempt.sha256" \
    /usr/bin/python3 - <<'PY'
import hashlib
import json
import os
import re
import stat

def read_regular(path, maximum):
    if not hasattr(os, "O_NOFOLLOW"):
        raise ValueError("O_NOFOLLOW is unavailable")
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size <= 0 or metadata.st_size > maximum:
            raise ValueError("invalid regular-file size/type")
        source = os.read(descriptor, metadata.st_size + 1)
        if len(source) != metadata.st_size:
            raise ValueError("file changed while reading")
        return source
    finally:
        os.close(descriptor)

def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result

try:
    source = read_regular(os.environ["STATE_PATH"], 65_536)
    sidecar = read_regular(os.environ["STATE_SHA_PATH"], 128)
    digest = hashlib.sha256(source).hexdigest()
    if sidecar != (digest + "\n").encode("ascii"):
        raise ValueError("publication attempt SHA-256 mismatch")
    payload = json.loads(source.decode("utf-8"), object_pairs_hook=reject_duplicates)
except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
    print(f"publication attempt validation failed: {error}", file=os.sys.stderr)
    raise SystemExit(os.EX_DATAERR)

keys = {
    "candidate_sha", "design_blob", "fast_mode", "node", "plan_blob",
    "predecessor_sha", "producer_checks_evidence_sha256", "push_attempted",
    "read_only", "remote_endpoint_sha256",
    "review_effort", "review_exit_status", "review_final_nonblank_line",
    "review_model", "review_report_sha256", "state_version",
}
if type(payload) is not dict or set(payload) != keys:
    print("publication attempt has the wrong closed shape", file=os.sys.stderr)
    raise SystemExit(os.EX_DATAERR)

lower_hex = lambda value, width: type(value) is str and re.fullmatch(rf"[0-9a-f]{{{width}}}", value)
if not all(lower_hex(payload[key], 40) for key in ("candidate_sha", "design_blob", "plan_blob", "predecessor_sha")):
    print("publication attempt contains an invalid Git identity", file=os.sys.stderr)
    raise SystemExit(os.EX_DATAERR)
if not all(
    lower_hex(payload[key], 64)
    for key in (
        "producer_checks_evidence_sha256",
        "remote_endpoint_sha256",
        "review_report_sha256",
    )
):
    print("publication attempt contains an invalid SHA-256", file=os.sys.stderr)
    raise SystemExit(os.EX_DATAERR)
fixed = {
    "node": "team-evidence-aggregation-status-facade-governance-attempt",
    "fast_mode": False,
    "push_attempted": True,
    "read_only": True,
    "review_effort": "max",
    "review_exit_status": 0,
    "review_final_nonblank_line": "VERDICT: PASS",
    "review_model": "claude-fable-5",
    "state_version": 2,
}
if any(payload[key] != value for key, value in fixed.items()):
    print("publication attempt fixed policy fields drifted", file=os.sys.stderr)
    raise SystemExit(os.EX_DATAERR)
canonical = json.dumps(
    payload,
    ensure_ascii=True,
    allow_nan=False,
    separators=(",", ":"),
    sort_keys=True,
).encode("ascii") + b"\n"
if source != canonical:
    print("publication attempt bytes are not canonical", file=os.sys.stderr)
    raise SystemExit(os.EX_DATAERR)

for key in (
    "predecessor_sha", "candidate_sha", "plan_blob", "design_blob",
    "producer_checks_evidence_sha256", "remote_endpoint_sha256",
    "review_report_sha256",
):
    print(payload[key])
PY
}

emit_governance_candidate_publication() {
  local output_dir="$OUTPUT_DIR"
  verify_producer_checks_evidence
  PUBLICATION_PATH="$output_dir/governance-candidate-publication.json" \
  PUBLICATION_SHA_PATH="$output_dir/governance-candidate-publication.sha256" \
  PREDECESSOR_SHA="$PREDECESSOR_SHA" \
  CANDIDATE_SHA="$CANDIDATE_SHA" \
  PLAN_BLOB="$PLAN_BLOB" \
  DESIGN_BLOB="$DESIGN_BLOB" \
  REVIEW_REPORT_SHA256="$REVIEW_REPORT_SHA256" \
  REMOTE_ENDPOINT_SHA256="$REMOTE_ENDPOINT_SHA256" \
  PLAN_PATH="$PLAN_PATH" \
  DESIGN_PATH="$DESIGN_PATH" \
  OUTPUT_DIR="$output_dir" \
    /usr/bin/python3 - <<'PY'
import hashlib
import json
import os

payload = {
    "bash_fences": "pass",
    "changed_paths": [os.environ["PLAN_PATH"], os.environ["DESIGN_PATH"]],
    "codegraph_full_index": "pass",
    "confirmed_remote_main_sha": os.environ["CANDIDATE_SHA"],
    "design_blob": os.environ["DESIGN_BLOB"],
    "fast_mode": False,
    "governance_candidate_sha": os.environ["CANDIDATE_SHA"],
    "schema": "pal.governance-candidate-publication.v1",
    "plan_blob": os.environ["PLAN_BLOB"],
    "plan_path": os.environ["PLAN_PATH"],
    "predecessor_sha": os.environ["PREDECESSOR_SHA"],
    "read_only": True,
    "remote_endpoint_sha256": os.environ["REMOTE_ENDPOINT_SHA256"],
    "review_effort": "max",
    "review_exit_status": 0,
    "review_final_nonblank_line": "VERDICT: PASS",
    "review_model": "claude-fable-5",
    "review_report_sha256": os.environ["REVIEW_REPORT_SHA256"],
    "shell_failure_harness": "pass",
}
if len(payload) != 19:
    raise SystemExit("internal governance-publication shape is not exactly 19 keys")
source = json.dumps(
    payload,
    ensure_ascii=True,
    allow_nan=False,
    separators=(",", ":"),
    sort_keys=True,
).encode("ascii") + b"\n"
digest = hashlib.sha256(source).hexdigest()

if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
    raise SystemExit("governance-publication output requires O_NOFOLLOW and O_DIRECTORY")

output_dir = os.environ["OUTPUT_DIR"]
publication_path = os.environ["PUBLICATION_PATH"]
publication_sha_path = os.environ["PUBLICATION_SHA_PATH"]
if os.path.dirname(publication_path) != output_dir or os.path.basename(publication_path) != "governance-candidate-publication.json":
    raise SystemExit("governance-publication output path is outside the fixed output directory")
if os.path.dirname(publication_sha_path) != output_dir or os.path.basename(publication_sha_path) != "governance-candidate-publication.sha256":
    raise SystemExit("governance-publication SHA output path is outside the fixed output directory")

directory_descriptor = os.open(
    output_dir,
    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
)

def write_exclusive(name, data):
    descriptor = os.open(
        name,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600,
        dir_fd=directory_descriptor,
    )
    try:
        metadata = os.fstat(descriptor)
        if metadata.st_mode & 0o777 != 0o600:
            raise OSError("governance-publication output mode is not 0600")
        offset = 0
        while offset < len(data):
            written = os.write(descriptor, data[offset:])
            if written <= 0:
                raise OSError("short write")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)

try:
    write_exclusive("governance-candidate-publication.json", source)
    try:
        write_exclusive("governance-candidate-publication.sha256", (digest + "\n").encode("ascii"))
    except BaseException:
        os.unlink("governance-candidate-publication.json", dir_fd=directory_descriptor)
        os.fsync(directory_descriptor)
        raise
    os.fsync(directory_descriptor)
except FileExistsError:
    print("governance-publication or SHA output already exists", file=os.sys.stderr)
    raise SystemExit(os.EX_CANTCREAT)
except OSError as error:
    print(f"governance-publication output failed: {error}", file=os.sys.stderr)
    raise SystemExit(os.EX_CANTCREAT)
finally:
    os.close(directory_descriptor)

print(f"GOVERNANCE_CANDIDATE_PUBLICATION_PATH={os.environ['PUBLICATION_PATH']}")
print(f"GOVERNANCE_CANDIDATE_PUBLICATION_SHA256={digest}")
PY
}

observe_remote_main() {
  local first_line first_sha first_ref fetched_sha second_line second_sha second_ref
  local command_status last_status=74
  for _ in 1 2 3; do
    if first_line="$(
      git_repo ls-remote --exit-code "$REMOTE_ENDPOINT" refs/heads/main 2>/dev/null
    )"; then
      :
    else
      command_status=$?
      last_status="$command_status"
      continue
    fi
    if [ -z "$first_line" ] ||
       [ "${first_line//$'\n'/}" != "$first_line" ] ||
       [[ "$first_line" != *$'\t'* ]]; then
      last_status=74
      continue
    fi
    first_sha="${first_line%%$'\t'*}"
    first_ref="${first_line#*$'\t'}"
    if [[ ! "$first_sha" =~ ^[0-9a-f]{40}$ ]] || [ "$first_ref" != refs/heads/main ]; then
      last_status=74
      continue
    fi
    if git_repo fetch --no-tags --no-recurse-submodules \
      "$REMOTE_ENDPOINT" refs/heads/main >/dev/null 2>&1; then
      :
    else
      command_status=$?
      last_status="$command_status"
      continue
    fi
    if fetched_sha="$(git_repo rev-parse 'FETCH_HEAD^{commit}' 2>/dev/null)"; then
      :
    else
      command_status=$?
      last_status="$command_status"
      continue
    fi
    if second_line="$(
      git_repo ls-remote --exit-code "$REMOTE_ENDPOINT" refs/heads/main 2>/dev/null
    )"; then
      :
    else
      command_status=$?
      last_status="$command_status"
      continue
    fi
    if [ -z "$second_line" ] ||
       [ "${second_line//$'\n'/}" != "$second_line" ] ||
       [[ "$second_line" != *$'\t'* ]]; then
      last_status=74
      continue
    fi
    second_sha="${second_line%%$'\t'*}"
    second_ref="${second_line#*$'\t'}"
    if [[ ! "$second_sha" =~ ^[0-9a-f]{40}$ ]] || [ "$second_ref" != refs/heads/main ]; then
      last_status=74
      continue
    fi
    if [ "$first_sha" = "$fetched_sha" ] && [ "$fetched_sha" = "$second_sha" ]; then
      printf '%s\n' "$second_sha"
      return 0
    fi
    last_status=74
  done
  return "$last_status"
}

classify_nonexact_remote() {
  local remote_sha="$1"
  local ancestry_status
  if git_repo merge-base --is-ancestor "$CANDIDATE_SHA" "$remote_sha"; then
    printf 'published_but_superseded\n'
    return 0
  else
    ancestry_status=$?
  fi
  case "$ancestry_status" in
    1) printf 'remote_moved_or_diverged\n'; return 0 ;;
    *) return "$ancestry_status" ;;
  esac
}

REVIEW_WORKTREE=''
CODEGRAPH_WORKTREE=''
WORKTREE_ROOT=''

cleanup_review_worktrees() {
  local cleanup_status=0 command_status
  if [ -n "$CODEGRAPH_WORKTREE" ] && test -d "$CODEGRAPH_WORKTREE"; then
    if git_repo worktree remove --force "$CODEGRAPH_WORKTREE" >/dev/null 2>&1; then
      command_status=0
    else
      command_status=$?
    fi
    if [ "$command_status" -ne 0 ]; then
      cleanup_status="$command_status"
    fi
  fi
  if [ -n "$REVIEW_WORKTREE" ] && test -d "$REVIEW_WORKTREE"; then
    if git_repo worktree remove --force "$REVIEW_WORKTREE" >/dev/null 2>&1; then
      command_status=0
    else
      command_status=$?
    fi
    if [ "$cleanup_status" -eq 0 ] && [ "$command_status" -ne 0 ]; then
      cleanup_status="$command_status"
    fi
  fi
  if [ -n "$WORKTREE_ROOT" ] && test -d "$WORKTREE_ROOT"; then
    if /bin/rm -rf -- "$WORKTREE_ROOT"; then
      command_status=0
    else
      command_status=$?
    fi
    if [ "$cleanup_status" -eq 0 ] && [ "$command_status" -ne 0 ]; then
      cleanup_status="$command_status"
    fi
  fi
  return "$cleanup_status"
}

cleanup_review_worktrees_on_exit() {
  local original_status=$? cleanup_status durability_status
  trap - EXIT
  set +e
  cleanup_review_worktrees
  cleanup_status=$?
  fsync_output_directory
  durability_status=$?
  set -e
  if [ "$original_status" -ne 0 ]; then
    exit "$original_status"
  fi
  if [ "$cleanup_status" -ne 0 ]; then
    exit "$cleanup_status"
  fi
  if [ "$durability_status" -ne 0 ]; then
    exit 73
  fi
  exit 0
}

finish_review_worktrees() {
  local cleanup_status durability_status
  set +e
  cleanup_review_worktrees
  cleanup_status=$?
  fsync_output_directory
  durability_status=$?
  set -e
  trap - EXIT
  test "$cleanup_status" -eq 0 || die 'detached worktree cleanup failed' "$cleanup_status"
  test "$durability_status" -eq 0 || die 'output directory fsync after cleanup failed' 73
  REVIEW_WORKTREE=''
  CODEGRAPH_WORKTREE=''
  WORKTREE_ROOT=''
}

run_lifecycle() {
  local codegraph_setup codegraph_explore codegraph_allocation codegraph_witness
  local codegraph_types codegraph_evidence
  local prompt_path stream_path stderr_path report_path parser_output seal_output
  local revise_manifest_digest
  local review_tree_before review_tree_after graph_tree_before graph_tree_after
  local tool_home_before tool_home_after
  local review_status parse_status seal_status manifest_status
  local review_head review_status_text graph_head graph_status_text
  local -a parsed_review sealed_review
  local current_remote observation_status push_status remote_after classification classification_status

  assert_candidate_invariants
  if ! mkdir -- "$OUTPUT_DIR"; then
    die "could not create exclusive output directory: $OUTPUT_DIR" 73
  fi
  fsync_output_parent || die 'could not fsync the pre-existing output parent' 73
  install_producer_checks_evidence
  verify_producer_checks_evidence
  mkdir -- "$OUTPUT_DIR/tool-home" "$OUTPUT_DIR/worktrees"
  WORKTREE_ROOT="$OUTPUT_DIR/worktrees"
  REVIEW_WORKTREE="$WORKTREE_ROOT/reviewer"
  CODEGRAPH_WORKTREE="$WORKTREE_ROOT/codegraph"
  trap cleanup_review_worktrees_on_exit EXIT

  git_repo worktree add --detach "$REVIEW_WORKTREE" "$CANDIDATE_SHA" >/dev/null
  git_repo worktree add --detach "$CODEGRAPH_WORKTREE" "$CANDIDATE_SHA" >/dev/null
  test ! -e "$CODEGRAPH_WORKTREE/.codegraph" ||
    die 'CodeGraph worktree was not fresh before initialization' 65

  codegraph_setup="$OUTPUT_DIR/codegraph-setup.txt"
  codegraph_explore="$OUTPUT_DIR/codegraph-explore.txt"
  codegraph_allocation="$OUTPUT_DIR/codegraph-allocation-node.txt"
  codegraph_witness="$OUTPUT_DIR/codegraph-witness-node.txt"
  codegraph_types="$OUTPUT_DIR/codegraph-types-node.txt"
  codegraph_evidence="$OUTPUT_DIR/codegraph-evidence.txt"

  /usr/bin/env -i HOME="$OUTPUT_DIR/tool-home" PATH=/usr/bin:/bin LC_ALL=C \
    "$CODEGRAPH_BIN" init -i "$CODEGRAPH_WORKTREE" > "$codegraph_setup"
  /usr/bin/env -i HOME="$OUTPUT_DIR/tool-home" PATH=/usr/bin:/bin LC_ALL=C \
    "$CODEGRAPH_BIN" index -f -q "$CODEGRAPH_WORKTREE" >> "$codegraph_setup"
  /usr/bin/env -i HOME="$OUTPUT_DIR/tool-home" PATH=/usr/bin:/bin LC_ALL=C \
    "$CODEGRAPH_BIN" explore -p "$CODEGRAPH_WORKTREE" \
    'Node 2C governance design allocator witness coverage types and trust boundary' \
    > "$codegraph_explore"
  /usr/bin/env -i HOME="$OUTPUT_DIR/tool-home" PATH=/usr/bin:/bin LC_ALL=C \
    "$CODEGRAPH_BIN" node -p "$CODEGRAPH_WORKTREE" "$ALLOCATION_PATH" \
    > "$codegraph_allocation"
  /usr/bin/env -i HOME="$OUTPUT_DIR/tool-home" PATH=/usr/bin:/bin LC_ALL=C \
    "$CODEGRAPH_BIN" node -p "$CODEGRAPH_WORKTREE" "$WITNESS_PATH" \
    > "$codegraph_witness"
  /usr/bin/env -i HOME="$OUTPUT_DIR/tool-home" PATH=/usr/bin:/bin LC_ALL=C \
    "$CODEGRAPH_BIN" node -p "$CODEGRAPH_WORKTREE" "$TYPES_PATH" \
    > "$codegraph_types"
  validate_codegraph_evidence \
    "$codegraph_setup" "$codegraph_explore" "$codegraph_allocation" \
    "$codegraph_witness" "$codegraph_types"
  validate_codegraph_query_semantics \
    "$codegraph_explore" explore "$CODEGRAPH_WORKTREE" \
    "$ALLOCATION_PATH" "$WITNESS_PATH" "$TYPES_PATH"
  validate_codegraph_query_semantics \
    "$codegraph_allocation" node "$CODEGRAPH_WORKTREE" "$ALLOCATION_PATH"
  validate_codegraph_query_semantics \
    "$codegraph_witness" node "$CODEGRAPH_WORKTREE" "$WITNESS_PATH"
  validate_codegraph_query_semantics \
    "$codegraph_types" node "$CODEGRAPH_WORKTREE" "$TYPES_PATH"

  {
    printf '%s\n' 'CODEGRAPH_SETUP:'
    /bin/cat "$codegraph_setup"
    printf '%s\n' 'CODEGRAPH_EXPLORE:'
    /bin/cat "$codegraph_explore"
    printf '%s\n' 'CODEGRAPH_ALLOCATION_NODE:'
    /bin/cat "$codegraph_allocation"
    printf '%s\n' 'CODEGRAPH_WITNESS_NODE:'
    /bin/cat "$codegraph_witness"
    printf '%s\n' 'CODEGRAPH_TYPES_NODE:'
    /bin/cat "$codegraph_types"
  } > "$codegraph_evidence"

  review_head="$(git_at "$REVIEW_WORKTREE" rev-parse HEAD)"
  graph_head="$(git_at "$CODEGRAPH_WORKTREE" rev-parse HEAD)"
  review_status_text="$(git_at "$REVIEW_WORKTREE" status --porcelain --untracked-files=all)"
  graph_status_text="$(git_at "$CODEGRAPH_WORKTREE" status --porcelain --untracked-files=all)"
  test "$review_head" = "$CANDIDATE_SHA" || die 'reviewer worktree HEAD drifted before review' 66
  test "$graph_head" = "$CANDIDATE_SHA" || die 'CodeGraph worktree HEAD drifted before review' 66
  test -z "$review_status_text" || die 'reviewer worktree is dirty before review' 66
  test -z "$graph_status_text" || die 'CodeGraph worktree is dirty after indexing' 66

  review_tree_before="$OUTPUT_DIR/reviewer-tree-before.json"
  review_tree_after="$OUTPUT_DIR/reviewer-tree-after.json"
  graph_tree_before="$OUTPUT_DIR/codegraph-tree-before.json"
  graph_tree_after="$OUTPUT_DIR/codegraph-tree-after.json"
  tool_home_before="$OUTPUT_DIR/tool-home-before.json"
  tool_home_after="$OUTPUT_DIR/tool-home-after.json"
  snapshot_worktree_tree "$REVIEW_WORKTREE" "$review_tree_before"
  snapshot_worktree_tree "$CODEGRAPH_WORKTREE" "$graph_tree_before"
  snapshot_worktree_tree "$OUTPUT_DIR/tool-home" "$tool_home_before"

  prompt_path="$OUTPUT_DIR/review-prompt.txt"
  stream_path="$OUTPUT_DIR/review-stream.jsonl"
  stderr_path="$OUTPUT_DIR/reviewer-stderr.txt"
  report_path="$OUTPUT_DIR/review-report.md"
  : > "$stream_path"
  : > "$stderr_path"
  chmod 0600 "$stream_path" "$stderr_path"

  {
    printf '%s\n' \
      'Read-only Node 2C governance-candidate review. Do not modify, create, or delete files.' \
      'Fast mode is forbidden.' \
      'Use only Read, Glob, and Grep.' \
      'Review the exact predecessor-to-candidate plan-and-design-only patch and the retained CodeGraph evidence.' \
      'Treat docs/superpowers/plans/2026-07-13-btc-domain-evidence-aggregation-foundation.md as the highest-authority reviewer input, pinned to SHA-256 af91080df318fb322a2bc387a800d50757963c221262f286facdd145fbbe5200 and Git blob f0ae5a3d73023f3d6f972d467669adc628c3f06a.' \
      'The Node 2C facade and its tests are intentionally absent at this governance candidate; do not reject their planned tests-only RED state.' \
      'Verify the allocator return is passed by identity to the Node 2B witness before facade inspection, and the witness return is authoritative coverage.' \
      'Verify the closed 19-key pal.governance-candidate-publication.v1 record is inbound Node 2C implementation-base authorization only, is not a Node 2A/2B child PASS receipt or Node 2C completion, and its path/payload never reaches Node 3.' \
      'Verify Node 3 receives no separately handed governance-publication digest; a digest nested in retained implementation manifests is audit provenance only and cannot satisfy accepted-review, fixed-predecessor, or exact-publication validation.' \
      'Verify the executable review, one-push, exact-remote, observation-only recovery, canonical governance-publication record, and local Supabase/paper-only boundaries.' \
      'Return findings first with file:line references.' \
      'Your exact final nonblank line must be VERDICT: PASS or VERDICT: REVISE.' \
      "PREDECESSOR_SHA=$PREDECESSOR_SHA" \
      "CANDIDATE_SHA=$CANDIDATE_SHA" \
      "PLAN_BLOB=$PLAN_BLOB" \
      "DESIGN_BLOB=$DESIGN_BLOB" \
      'CODEGRAPH_EVIDENCE:'
    /bin/cat "$codegraph_evidence"
    printf '%s\n' 'COMPLETE_PATCH:'
    git_repo diff --no-ext-diff --no-textconv --unified=80 \
      "$PREDECESSOR_SHA..$CANDIDATE_SHA"
  } > "$prompt_path"

  set +e
  (
    cd -- "$REVIEW_WORKTREE" || exit 76
    ulimit -f 32767
    /usr/bin/env -i HOME="$OUTPUT_DIR/tool-home" PATH=/usr/bin:/bin LC_ALL=C \
      /usr/bin/timeout --signal=TERM --kill-after=10s "${REVIEW_TIMEOUT_SECONDS}s" \
      "$REVIEWER_BIN" --print \
        --bare \
        --input-format text \
        --output-format stream-json \
        --include-partial-messages \
        --verbose \
        --safe-mode \
        --model "$REVIEW_MODEL" \
        --effort "$REVIEW_EFFORT" \
        --tools Read,Glob,Grep \
        --permission-mode dontAsk \
        --no-session-persistence \
        --system-prompt 'You are a read-only senior engineering reviewer. Use only Read, Glob, and Grep. Return findings first and the exact required verdict. Do not modify, create, or delete files.' \
        < "$prompt_path" \
        > "$stream_path" \
        2> "$stderr_path"
  )
  review_status=$?
  set -e

  validate_review_raw_artifacts "$stream_path" "$stderr_path"
  if [ "$review_status" -ne 0 ]; then
    set +e
    seal_review_artifacts diagnostics >/dev/null
    seal_status=$?
    set -e
    if [ "$seal_status" -ne 0 ]; then
      die 'reviewer diagnostics could not be durably retained' "$seal_status"
    fi
    die "reviewer command failed with status $review_status" "$review_status"
  fi

  set +e
  parser_output="$(parse_review_stream "$stream_path" "$report_path" 2>> "$stderr_path")"
  parse_status=$?
  set -e
  if [ "$parse_status" -ne 0 ]; then
    set +e
    seal_review_artifacts diagnostics >/dev/null
    seal_status=$?
    set -e
    if [ "$seal_status" -ne 0 ]; then
      die 'review parser diagnostics could not be durably retained' "$seal_status"
    fi
    die 'review stream parsing failed' "$parse_status"
  fi
  mapfile -t parsed_review <<< "$parser_output"
  test "${#parsed_review[@]}" -eq 2 || die 'review parser returned the wrong summary shape' 65
  REVIEW_FINAL_LINE="${parsed_review[1]}"

  set +e
  seal_output="$(seal_review_artifacts complete)"
  seal_status=$?
  set -e
  if [ "$seal_status" -ne 0 ]; then
    die 'review artifacts could not be durably sealed' "$seal_status"
  fi
  mapfile -t sealed_review <<< "$seal_output"
  test "${#sealed_review[@]}" -eq 6 || die 'review artifact sealer returned the wrong summary shape' 65
  REVIEW_REPORT_SHA256="${sealed_review[0]}"
  REVIEW_REPORT_BYTE_COUNT="${sealed_review[1]}"
  REVIEW_STREAM_SHA256="${sealed_review[2]}"
  REVIEW_STREAM_BYTE_COUNT="${sealed_review[3]}"
  REVIEW_STDERR_SHA256="${sealed_review[4]}"
  REVIEW_STDERR_BYTE_COUNT="${sealed_review[5]}"
  test "${parsed_review[0]}" = "$REVIEW_REPORT_SHA256" ||
    die 'review parser and artifact sealer report digests disagree' 65
  require_lower_hex review-report-sha256 "$REVIEW_REPORT_SHA256" 64

  review_head="$(git_at "$REVIEW_WORKTREE" rev-parse HEAD)"
  graph_head="$(git_at "$CODEGRAPH_WORKTREE" rev-parse HEAD)"
  review_status_text="$(git_at "$REVIEW_WORKTREE" status --porcelain --untracked-files=all)"
  graph_status_text="$(git_at "$CODEGRAPH_WORKTREE" status --porcelain --untracked-files=all)"
  test "$review_head" = "$CANDIDATE_SHA" || die 'reviewer worktree HEAD changed during review' 66
  test "$graph_head" = "$CANDIDATE_SHA" || die 'CodeGraph worktree HEAD changed during review' 66
  test -z "$review_status_text" || die 'reviewer violated the read-only worktree contract' 66
  test -z "$graph_status_text" || die 'CodeGraph worktree changed after validated indexing' 66
  snapshot_worktree_tree "$REVIEW_WORKTREE" "$review_tree_after"
  snapshot_worktree_tree "$CODEGRAPH_WORKTREE" "$graph_tree_after"
  snapshot_worktree_tree "$OUTPUT_DIR/tool-home" "$tool_home_after"
  cmp -s -- "$review_tree_before" "$review_tree_after" ||
    die 'reviewer changed worktree bytes, modes, links, or ignored paths' 66
  cmp -s -- "$graph_tree_before" "$graph_tree_after" ||
    die 'CodeGraph worktree changed after evidence capture' 66
  cmp -s -- "$tool_home_before" "$tool_home_after" ||
    die 'reviewer changed the isolated tool home' 66
  REVIEW_HEAD_SHA="$review_head"

  assert_candidate_invariants
  verify_report_attestation "$REVIEW_REPORT_SHA256"
  verify_producer_checks_evidence
  finish_review_worktrees

  if [ "$REVIEW_FINAL_LINE" = "$REVIEW_FINAL_REVISE" ]; then
    set +e
    revise_manifest_digest="$(write_review_revise_manifest)"
    manifest_status=$?
    set -e
    if [ "$manifest_status" -ne 0 ]; then
      die 'terminal REVISE could not create its durable repair handoff' "$manifest_status"
    fi
    require_lower_hex review-revise-sha256 "$revise_manifest_digest" 64
    if ! validate_revise_handoff >/dev/null; then
      die 'terminal REVISE durable repair handoff failed validation' 73
    fi
    printf 'REVIEW_RESULT=REVISE\n'
    printf 'REVIEW_REPORT_PATH=%s\n' "$report_path"
    printf 'REVIEW_REPORT_SHA256=%s\n' "$REVIEW_REPORT_SHA256"
    printf 'REVIEW_REVISE_PATH=%s\n' "$OUTPUT_DIR/review-revise.json"
    printf 'REVIEW_REVISE_SHA256=%s\n' "$revise_manifest_digest"
    printf 'A replacement candidate must be rebuilt as a sibling from %s; publication remains blocked.\n' \
      "$PREDECESSOR_SHA" >&2
    exit 2
  fi
  test "$REVIEW_FINAL_LINE" = "$REVIEW_FINAL_PASS" || die 'review verdict is invalid' 65

  # Trust boundary: the coordinator hashes the exact parsed report bytes it
  # retained. The publication record carries that coordinator attestation; a downstream
  # consumer without those report bytes cannot independently prove semantics.
  assert_candidate_invariants
  verify_report_attestation "$REVIEW_REPORT_SHA256"
  verify_producer_checks_evidence

  set +e
  current_remote="$(observe_remote_main)"
  observation_status=$?
  set -e
  if [ "$observation_status" -ne 0 ]; then
    printf 'pre-push remote observation failed; no push was attempted.\n' >&2
    exit "$observation_status"
  fi
  if [ "$current_remote" != "$PREDECESSOR_SHA" ]; then
    printf 'stable remote main moved before publication; no push was attempted.\n' >&2
    exit 76
  fi

  write_publication_attempt_state
  assert_candidate_invariants
  verify_report_attestation "$REVIEW_REPORT_SHA256"
  verify_producer_checks_evidence

  set +e
  git_repo push \
    --no-force --no-force-with-lease --no-force-if-includes --no-follow-tags \
    --no-recurse-submodules \
    "$REMOTE_ENDPOINT" "$CANDIDATE_SHA:refs/heads/main" \
    >/dev/null 2>&1
  push_status=$?
  set -e

  set +e
  remote_after="$(observe_remote_main)"
  observation_status=$?
  set -e
  if [ "$observation_status" -ne 0 ]; then
    printf 'post-push observation is indeterminate; no second push is permitted.\n' >&2
    exit "$observation_status"
  fi

  if [ "$remote_after" = "$CANDIDATE_SHA" ]; then
    verify_report_attestation "$REVIEW_REPORT_SHA256"
    emit_governance_candidate_publication
    return 0
  fi

  if [ "$remote_after" = "$PREDECESSOR_SHA" ]; then
    if [ "$push_status" -eq 0 ]; then
      printf 'push returned success but remote equality is absent; use observation-only recovery.\n' >&2
      exit 75
    fi
    printf 'the failed push is stably observed as unpublished; no automatic retry is permitted.\n' >&2
    exit "$push_status"
  fi

  set +e
  classification="$(classify_nonexact_remote "$remote_after")"
  classification_status=$?
  set -e
  if [ "$classification_status" -ne 0 ]; then
    printf 'remote ancestry classification failed; use observation-only recovery.\n' >&2
    exit "$classification_status"
  fi
  case "$classification" in
    published_but_superseded)
      printf 'remote main contains but no longer equals the reviewed candidate; governance-publication emission is blocked.\n' >&2
      ;;
    remote_moved_or_diverged)
      printf 'remote main moved or diverged; a fresh candidate and full review are required.\n' >&2
      ;;
    *) die 'internal remote classification error' 70 ;;
  esac
  exit 76
}

recover_lifecycle() {
  local state_output state_status observed observation_status classification classification_status
  local -a state_values

  set +e
  state_output="$(read_publication_attempt_state)"
  state_status=$?
  set -e
  if [ "$state_status" -ne 0 ]; then
    die 'recovery state validation failed' "$state_status"
  fi
  mapfile -t state_values <<< "$state_output"
  test "${#state_values[@]}" -eq 7 || die 'publication attempt parser returned the wrong summary shape' 65
  PREDECESSOR_SHA="${state_values[0]}"
  CANDIDATE_SHA="${state_values[1]}"
  PLAN_BLOB="${state_values[2]}"
  DESIGN_BLOB="${state_values[3]}"
  PRODUCER_CHECKS_EVIDENCE_SHA256="${state_values[4]}"
  REMOTE_ENDPOINT_SHA256="${state_values[5]}"
  REVIEW_REPORT_SHA256="${state_values[6]}"

  require_lower_hex predecessor-sha "$PREDECESSOR_SHA" 40
  require_lower_hex candidate-sha "$CANDIDATE_SHA" 40
  require_lower_hex plan-blob "$PLAN_BLOB" 40
  require_lower_hex design-blob "$DESIGN_BLOB" 40
  require_lower_hex producer-checks-evidence-sha256 "$PRODUCER_CHECKS_EVIDENCE_SHA256" 64
  require_lower_hex remote-endpoint-sha256 "$REMOTE_ENDPOINT_SHA256" 64
  require_lower_hex review-report-sha256 "$REVIEW_REPORT_SHA256" 64
  verify_producer_checks_evidence
  verify_report_attestation "$REVIEW_REPORT_SHA256"
  assert_candidate_invariants

  set +e
  observed="$(observe_remote_main)"
  observation_status=$?
  set -e
  if [ "$observation_status" -ne 0 ]; then
    printf 'remote observation remains indeterminate; no second push is permitted.\n' >&2
    exit "$observation_status"
  fi

  if [ "$observed" = "$CANDIDATE_SHA" ]; then
    verify_report_attestation "$REVIEW_REPORT_SHA256"
    emit_governance_candidate_publication
    return 0
  fi
  if [ "$observed" = "$PREDECESSOR_SHA" ]; then
    printf 'observation recovery confirms the candidate is not published; no retry is permitted.\n' >&2
    exit 76
  fi

  set +e
  classification="$(classify_nonexact_remote "$observed")"
  classification_status=$?
  set -e
  if [ "$classification_status" -ne 0 ]; then
    printf 'observation recovery ancestry classification failed.\n' >&2
    exit "$classification_status"
  fi
  case "$classification" in
    published_but_superseded)
      printf 'observation recovery found a descendant remote; exact-equality governance-publication emission remains blocked.\n' >&2
      ;;
    remote_moved_or_diverged)
      printf 'observation recovery found unrelated remote movement; a fresh full gate is required.\n' >&2
      ;;
    *) die 'internal recovery classification error' 70 ;;
  esac
  exit 76
}

case "$MODE" in
  run) run_lifecycle ;;
  recover) recover_lifecycle ;;
  validate-revise) validate_revise_handoff ;;
esac
```

#### Candidate-bound producer evidence

After CommonMark extraction, `bash -n`, Python compilation, ShellCheck error
checking, the exact Git-control failure harness, and the complete lifecycle
matrix all pass for the literal candidate, run this fence. The lifecycle path
is the privately extracted fence above, not an unpinned sibling artifact.

```bash
set -euo pipefail
umask 077
: "${GOVERNANCE_CANDIDATE_SHA:?governance candidate SHA is required}"
: "${NODE2C_GOVERNANCE_LIFECYCLE:?extracted lifecycle path is required}"
: "${NODE2C_PRODUCER_CHECKS_EVIDENCE_PATH:?producer evidence path is required}"
[[ "$GOVERNANCE_CANDIDATE_SHA" =~ ^[0-9a-f]{40}$ ]]
case "$NODE2C_GOVERNANCE_LIFECYCLE" in /*) ;; *) exit 64 ;; esac
case "$NODE2C_PRODUCER_CHECKS_EVIDENCE_PATH" in /*) ;; *) exit 64 ;; esac
test -f "$NODE2C_GOVERNANCE_LIFECYCLE"
test ! -L "$NODE2C_GOVERNANCE_LIFECYCLE"
test ! -e "$NODE2C_PRODUCER_CHECKS_EVIDENCE_PATH"
test "$(sha256sum "$NODE2C_GOVERNANCE_LIFECYCLE" | awk '{print $1}')" =   9f2617f3863f5fdc53d26e8c87fef67d2c93793106e6adc441c1416931bf2354

PRODUCER_CANDIDATE_SHA="$GOVERNANCE_CANDIDATE_SHA" PRODUCER_EVIDENCE_PATH="$NODE2C_PRODUCER_CHECKS_EVIDENCE_PATH"   /usr/bin/python3 - <<'PY'
import hashlib
import json
import os
import re

candidate = os.environ["PRODUCER_CANDIDATE_SHA"]
path = os.environ["PRODUCER_EVIDENCE_PATH"]
if re.fullmatch(r"[0-9a-f]{40}", candidate) is None:
    raise SystemExit("producer candidate SHA is invalid")
if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
    raise SystemExit("producer evidence requires O_NOFOLLOW and O_DIRECTORY")
parent, name = os.path.split(path)
if not parent or name in {"", ".", ".."} or "/" in name:
    raise SystemExit("producer evidence path is invalid")
source = json.dumps(
    {
        "bash_fences": "pass",
        "candidate_sha": candidate,
        "shell_failure_harness": "pass",
    },
    ensure_ascii=True,
    allow_nan=False,
    separators=(",", ":"),
    sort_keys=True,
).encode("ascii") + b"\n"
directory = os.open(parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
try:
    descriptor = os.open(
        name,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600,
        dir_fd=directory,
    )
    try:
        offset = 0
        while offset < len(source):
            written = os.write(descriptor, source[offset:])
            if written <= 0:
                raise OSError("short producer evidence write")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.fsync(directory)
finally:
    os.close(directory)
print(hashlib.sha256(source).hexdigest())
PY
NODE2C_PRODUCER_CHECKS_EVIDENCE_SHA256="$(
  sha256sum "$NODE2C_PRODUCER_CHECKS_EVIDENCE_PATH" | awk '{print $1}'
)"
[[ "$NODE2C_PRODUCER_CHECKS_EVIDENCE_SHA256" =~ ^[0-9a-f]{64}$ ]]
export NODE2C_PRODUCER_CHECKS_EVIDENCE_PATH   NODE2C_PRODUCER_CHECKS_EVIDENCE_SHA256
readonly NODE2C_PRODUCER_CHECKS_EVIDENCE_PATH   NODE2C_PRODUCER_CHECKS_EVIDENCE_SHA256
```

#### Lifecycle invocation and terminal REVISE

The `run` command below is the only governance review/publication entry point.
`NODE2C_REVIEWER_BIN` resolves to local Claude Code; the lifecycle fixes model
`claude-fable-5`, effort `max`, safe/read-only tools, no fast mode, no
fallback, strict stream parsing, and no session persistence. Exit `2` is a
terminal REVISE for that candidate: retain its mode-`0600` report and digest,
perform no push, create no PASS receipt, and construct a distinct sibling from
the unchanged `E31_PREREQ_SHA`. Never amend or descend from the rejected
candidate and never reuse its output directory or CodeGraph evidence.

```bash
set -euo pipefail
: "${GOVERNANCE_CANDIDATE_SHA:?governance candidate SHA is required}"
: "${NODE2C_REVIEWED_PLAN_BLOB:?reviewed plan blob is required}"
: "${NODE2C_REVIEWED_DESIGN_BLOB:?reviewed design blob is required}"
: "${GOVERNANCE_REMOTE_ENDPOINT_SHA256:?remote endpoint digest is required}"
: "${NODE2C_PRODUCER_CHECKS_EVIDENCE_PATH:?producer evidence path is required}"
: "${NODE2C_PRODUCER_CHECKS_EVIDENCE_SHA256:?producer evidence digest is required}"
: "${NODE2C_GOVERNANCE_LIFECYCLE:?pinned lifecycle executable is required}"
: "${NODE2C_GOVERNANCE_OUTPUT_DIR:?exclusive output directory is required}"
: "${NODE2C_REVIEWER_BIN:?Claude reviewer executable is required}"
: "${NODE2C_CODEGRAPH_BIN:?CodeGraph executable is required}"
: "${NODE2C_GOVERNANCE_GIT_CREDENTIAL_FILE:?approved Git credential file is required}"
test "${NODE2C_FAST_MODE:-false}" = false
E31_PREREQ_SHA="$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA"
test "$E31_PREREQ_SHA" = e31c3951b06f06e995c0c8f6f8fe2f22320a38da
NODE2C_FAST_MODE=false "$NODE2C_GOVERNANCE_LIFECYCLE" run   --repo "$(pwd -P)"   --predecessor-sha "$E31_PREREQ_SHA"   --candidate-sha "$GOVERNANCE_CANDIDATE_SHA"   --plan-blob "$NODE2C_REVIEWED_PLAN_BLOB"   --design-blob "$NODE2C_REVIEWED_DESIGN_BLOB"   --remote-endpoint-sha256 "$GOVERNANCE_REMOTE_ENDPOINT_SHA256"   --producer-checks-evidence "$NODE2C_PRODUCER_CHECKS_EVIDENCE_PATH"   --producer-checks-evidence-sha256 "$NODE2C_PRODUCER_CHECKS_EVIDENCE_SHA256"   --output-dir "$NODE2C_GOVERNANCE_OUTPUT_DIR"   --reviewer-bin "$NODE2C_REVIEWER_BIN"   --codegraph-bin "$NODE2C_CODEGRAPH_BIN"   --git-credential-file "$NODE2C_GOVERNANCE_GIT_CREDENTIAL_FILE"
```

If a sole push was attempted but post-push observation was indeterminate, an
operator may select this exact observation-only recovery. It validates the
hash-protected state, retained report, candidate-bound producer evidence, and
candidate invariants; it contains no push and exact remote equality is required
before governance-publication creation.

```bash
set -euo pipefail
: "${NODE2C_GOVERNANCE_LIFECYCLE:?pinned lifecycle executable is required}"
: "${NODE2C_GOVERNANCE_OUTPUT_DIR:?existing governance output directory is required}"
: "${NODE2C_GOVERNANCE_GIT_CREDENTIAL_FILE:?approved Git credential file is required}"
test "${NODE2C_FAST_MODE:-false}" = false
NODE2C_FAST_MODE=false "$NODE2C_GOVERNANCE_LIFECYCLE" recover   --repo "$(pwd -P)"   --output-dir "$NODE2C_GOVERNANCE_OUTPUT_DIR"   --git-credential-file "$NODE2C_GOVERNANCE_GIT_CREDENTIAL_FILE"
```

Only `run` or `recover` exit `0` permits this descriptor-bound handoff. The
sidecar is an independently retained trust pin; Task 1 reopens the publication record
itself through one bounded no-follow descriptor and requires canonical bytes.

```bash
NODE2C_GOVERNANCE_CANDIDATE_PUBLICATION_PATH="$NODE2C_GOVERNANCE_OUTPUT_DIR/governance-candidate-publication.json"
NODE2C_GOVERNANCE_CANDIDATE_PUBLICATION_SHA256="$(
  PUBLICATION_SHA_PATH="$NODE2C_GOVERNANCE_OUTPUT_DIR/governance-candidate-publication.sha256"     /usr/bin/python3 - <<'PY'
import os
import re
import stat

path = os.environ["PUBLICATION_SHA_PATH"]
if not hasattr(os, "O_NOFOLLOW"):
    raise SystemExit("governance-publication handoff requires O_NOFOLLOW")
descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
try:
    metadata = os.fstat(descriptor)
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_size != 65:
        raise SystemExit("governance-publication SHA sidecar shape is invalid")
    source = os.read(descriptor, 66)
    if len(source) != metadata.st_size:
        raise SystemExit("governance-publication SHA sidecar changed while reading")
finally:
    os.close(descriptor)
text = source.decode("ascii")
if re.fullmatch(r"[0-9a-f]{64}\n", text) is None:
    raise SystemExit("governance-publication SHA sidecar value is invalid")
print(text[:-1])
PY
)"
[[ "$NODE2C_GOVERNANCE_CANDIDATE_PUBLICATION_SHA256" =~ ^[0-9a-f]{64}$ ]]
export NODE2C_GOVERNANCE_CANDIDATE_PUBLICATION_PATH   NODE2C_GOVERNANCE_CANDIDATE_PUBLICATION_SHA256
readonly NODE2C_GOVERNANCE_CANDIDATE_PUBLICATION_PATH   NODE2C_GOVERNANCE_CANDIDATE_PUBLICATION_SHA256
```

`review_report_sha256` is the governance coordinator's attestation over the
exact report bytes parsed from the accepted reviewer stream and retained as
`review-report.md`. The governance-publication consumer validates the digest shape and
publication record bytes; it does not independently prove report semantics without those
report bytes or another trusted attestation. Likewise, `bash_fences=pass` and
`shell_failure_harness=pass` are coordinator attestations backed by retained
canonical producer evidence. The lifecycle revalidates its exact digest,
closed shape, PASS values, and candidate binding before review, recovery, and
governance-publication creation; it does not rerun those external checks during publication.

## Fixed Predecessor Interfaces

Node 2C consumes these exact public functions and no predecessor private helper:

```text
select_team_evidence_canonical_current_records(
    aggregation_input: TeamEvidenceAggregationInput,
    *,
    config: TeamEvidenceAggregationConfig,
) -> tuple[TeamEvidenceAggregationRecord, ...]

select_team_evidence_canonical_capture_records(
    aggregation_input: TeamEvidenceAggregationInput,
    *,
    config: TeamEvidenceAggregationConfig,
) -> tuple[TeamEvidenceAggregationRecord, ...]

assess_team_evidence_temporal(
    record: TeamEvidenceAggregationRecord,
    *,
    evaluated_at: datetime,
    config: TeamEvidenceAggregationConfig,
) -> TeamEvidenceTemporalAssessment

allocate_team_evidence_weights(
    records: tuple[TeamEvidenceAggregationRecord, ...],
    *,
    config: TeamEvidenceAggregationConfig,
) -> tuple[TeamEvidenceWeightAllocation, ...]

build_team_evidence_requirement_coverage(
    allocation_input_records: tuple[TeamEvidenceAggregationRecord, ...],
    allocations: tuple[TeamEvidenceWeightAllocation, ...],
    *,
    config: TeamEvidenceAggregationConfig,
) -> tuple[TeamEvidenceRequirementCoverage, ...]

team_evidence_aggregation_config_digest(
    config: TeamEvidenceAggregationConfig,
) -> str

team_evidence_aggregation_core_digest(
    result: TeamEvidenceAggregationResult,
) -> str

team_evidence_aggregation_payload(
    result: TeamEvidenceAggregationResult,
) -> dict[str, object]

validate_team_evidence_aggregation_core_digest(
    result: TeamEvidenceAggregationResult,
) -> None
```

Node 2C does not rematerialize or revalidate Node 2B's allocation, coverage, or
witness algorithms. Node 2C tests and review statements verify only that the
allocator's exact returned object reaches the real Node 2B witness API by
identity before any facade consumption, and that the facade subsequently
passes through authoritative coverage and consumes it for status. Candidate-edge
ordering and every allocation/coverage/witness validity rule remain exclusively
in the Node 2B plan and tests.

Node 2C produces exactly:

```text
build_team_evidence_aggregation_result(
    aggregation_input: TeamEvidenceAggregationInput,
    *,
    config: TeamEvidenceAggregationConfig,
) -> TeamEvidenceAggregationResult

validate_team_evidence_aggregation_result(
    result: TeamEvidenceAggregationResult,
    *,
    aggregation_input: TeamEvidenceAggregationInput,
    config: TeamEvidenceAggregationConfig,
) -> None
```

The production module's literal export tuple is exactly:

```python
__all__ = (
    "build_team_evidence_aggregation_result",
    "validate_team_evidence_aggregation_result",
)
```

The two selector-derived identity sets are fixed:

```python
CanonicalRecordIdentity = tuple[str, str, str, str]
# (source_lineage_id, capture_id, evidence_revision_id, assessment_revision_id)

SelectedRevisionPairIdentity = tuple[str, str, str]
# (source_lineage_id, evidence_revision_id, assessment_revision_id)
```

- The canonical-capture set contains the exact four-field identities returned by `select_team_evidence_canonical_capture_records`.
- The canonical-current set contains the exact four-field identities returned by `select_team_evidence_canonical_current_records`.
- The selected-current pair set is the canonical-current set projected to the three fields above. `selected_current_revision` is pair-level: every recapture of that exact selected pair is `True`, even when its four-field identity is absent from the canonical-current and canonical-capture sets.
- `canonical_capture` is four-field membership in the canonical-capture set, including canonical records belonging to wholly non-current revisions.

---

### Task 1: Validate Node 2A/2B, Fixed-Parent, Candidate, And Blob Handoffs

**Files:** No repository files change in this task.

**Interfaces:**
- Consumes: runtime environment values `NODE2A_PREREQ_SHA`, `NODE2B_PREREQ_SHA`, `NODE2A_PASS_RECEIPT_PATH`, `NODE2B_PASS_RECEIPT_PATH`, `NODE2A_PASS_RECEIPT_SHA256`, `NODE2B_PASS_RECEIPT_SHA256`, `NODE2C_GOVERNANCE_CANDIDATE_PUBLICATION_PATH`, and `NODE2C_GOVERNANCE_CANDIDATE_PUBLICATION_SHA256`; a fresh review-fix shell reuses the same values with `NODE2C_PREFLIGHT_MODE=resume`.
- Produces: canonical non-secret `INITIAL_NODE2A_RECEIPT_EVIDENCE`, `INITIAL_NODE2B_RECEIPT_EVIDENCE`, and `INITIAL_GOVERNANCE_CANDIDATE_PUBLICATION_EVIDENCE`; independently binds the Node 2B receipt to `2be280b5a3194a83191753bfc1deb227a3d2dc31`; proves fixed published import-governance parent `e31c3951b06f06e995c0c8f6f8fe2f22320a38da`, hardened candidate, and reviewed plan/design blobs as separate checks; then captures only the hardened candidate as immutable implementation `NODE_BASE`.

- [ ] **Step 1: Validate the Node 2A/2B receipts and separate governance-candidate publication record**

The Node 2A receipt has exactly these thirteen keys and values; the two SHA values are the runtime `NODE2A_PREREQ_SHA`:

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

The Node 2B receipt has exactly these fifteen keys and values; `read_only` and `fast_mode` are JSON booleans, and both SHA values are the runtime `NODE2B_PREREQ_SHA`:

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

The governance-candidate publication record has exactly these nineteen keys. The candidate,
plan/design blobs, report/endpoint digests, and confirmed remote SHA are literal
lowercase hexadecimal values captured by the governance publication shell;
`predecessor_sha` is the fixed published import-governance parent
`e31c3951b06f06e995c0c8f6f8fe2f22320a38da`, not the Node 2B SHA. Node 2B
remains independently bound by its own closed receipt and the fixed-parent
topology gate:

```json
{
  "schema": "pal.governance-candidate-publication.v1",
  "predecessor_sha": "e31c3951b06f06e995c0c8f6f8fe2f22320a38da",
  "governance_candidate_sha": "$GOVERNANCE_CANDIDATE_SHA",
  "plan_path": "docs/superpowers/plans/2026-07-13-team-evidence-aggregation-status-facade-publishability-scope-guard.md",
  "changed_paths": [
    "docs/superpowers/plans/2026-07-13-team-evidence-aggregation-status-facade-publishability-scope-guard.md",
    "docs/superpowers/specs/2026-07-13-team-evidence-aggregation-core-design.md"
  ],
  "plan_blob": "$NODE2C_REVIEWED_PLAN_BLOB",
  "design_blob": "$NODE2C_REVIEWED_DESIGN_BLOB",
  "review_model": "claude-fable-5",
  "review_effort": "max",
  "read_only": true,
  "fast_mode": false,
  "review_exit_status": 0,
  "review_final_nonblank_line": "VERDICT: PASS",
  "review_report_sha256": "$GOVERNANCE_REVIEW_REPORT_SHA256",
  "remote_endpoint_sha256": "$GOVERNANCE_REMOTE_ENDPOINT_SHA256",
  "bash_fences": "pass",
  "shell_failure_harness": "pass",
  "codegraph_full_index": "pass",
  "confirmed_remote_main_sha": "$GOVERNANCE_CANDIDATE_SHA"
}
```

Run from the repository root in one persistent Bash gate session. The generic
function below is the only permitted receipt-validation path. Each invocation is
one validation pass and must use exactly one descriptor read and one JSON parser;
do not precede or replace it within that pass with path-based `test`, `realpath`,
`sha256sum`, `Path.read_text`, another descriptor read, or another JSON parser.
Task 1 invokes each receipt validator once initially and once after all
Git/path gates:

The Git-control definition at the start of this block is byte-identical to the
governance definition and is self-contained in every initial or resume Task 1
shell. It is not sourced from the candidate worktree and is not inherited from
the governance, implementation, or prior review-fix shell.

```bash
set -Eeuo pipefail

assert_node2c_git_controls() {
    # Keep xtrace from exposing checked values and restore caller options on
    # every return from this function.
    local -
    set +x

    local node2c_refs=''
    local node2c_common_dir=''
    local node2c_shallow_state=''
    local node2c_producer_status=0
    local node2c_no_replace_declaration=''

    if [[ ${GIT_NO_REPLACE_OBJECTS-} != '1' ]]; then
        printf '%s\n' \
            'node2c git controls: GIT_NO_REPLACE_OBJECTS must equal 1' >&2 || :
        return 1
    fi

    if node2c_no_replace_declaration=$(builtin declare -p \
        GIT_NO_REPLACE_OBJECTS 2>/dev/null); then
        :
    else
        printf '%s\n' \
            'node2c git controls: GIT_NO_REPLACE_OBJECTS must equal 1 and be exported' >&2 || :
        return 1
    fi

    if [[ $node2c_no_replace_declaration \
        != declare\ -*x*\ GIT_NO_REPLACE_OBJECTS=* ]]; then
        printf '%s\n' \
            'node2c git controls: GIT_NO_REPLACE_OBJECTS must equal 1 and be exported' >&2 || :
        return 1
    fi

    if [[ -n ${GIT_GRAFT_FILE-} ]]; then
        printf '%s\n' \
            'node2c git controls: GIT_GRAFT_FILE must be unset or empty' >&2 || :
        return 1
    fi

    if [[ -n ${GIT_REPLACE_REF_BASE-} ]]; then
        printf '%s\n' \
            'node2c git controls: GIT_REPLACE_REF_BASE must be unset or empty' >&2 || :
        return 1
    fi

    if node2c_refs=$(command git for-each-ref \
        '--format=%(refname)' 'refs/replace/' 2>/dev/null); then
        :
    else
        node2c_producer_status=$?
        printf '%s\n' \
            'node2c git controls: could not enumerate replacement refs' >&2 || :
        return "$node2c_producer_status"
    fi

    if [[ -n $node2c_refs ]]; then
        printf '%s\n' \
            'node2c git controls: replacement refs are present' >&2 || :
        return 1
    fi

    if node2c_common_dir=$(command git rev-parse \
        '--path-format=absolute' '--git-common-dir' 2>/dev/null); then
        :
    else
        node2c_producer_status=$?
        printf '%s\n' \
            'node2c git controls: could not resolve the Git common directory' >&2 || :
        return "$node2c_producer_status"
    fi

    if [[ -z $node2c_common_dir || $node2c_common_dir != /* \
        || $node2c_common_dir == *$'\n'* ]]; then
        printf '%s\n' \
            'node2c git controls: Git common-directory result is invalid' >&2 || :
        return 1
    fi

    if [[ -e $node2c_common_dir/info/grafts \
        || -L $node2c_common_dir/info/grafts ]]; then
        printf '%s\n' \
            'node2c git controls: common-directory info/grafts is present' >&2 || :
        return 1
    fi

    if node2c_shallow_state=$(command git rev-parse \
        '--is-shallow-repository' 2>/dev/null); then
        :
    else
        node2c_producer_status=$?
        printf '%s\n' \
            'node2c git controls: could not determine shallow state' >&2 || :
        return "$node2c_producer_status"
    fi

    case "$node2c_shallow_state" in
        false)
            ;;
        true)
            printf '%s\n' \
                'node2c git controls: repository is shallow' >&2 || :
            return 1
            ;;
        *)
            printf '%s\n' \
                'node2c git controls: shallow-state query returned an invalid result' >&2 || :
            return 1
            ;;
    esac

    return 0
}
readonly -f assert_node2c_git_controls

export GIT_NO_REPLACE_OBJECTS=1
readonly GIT_NO_REPLACE_OBJECTS
assert_node2c_git_controls

: "${NODE2A_PREREQ_SHA:?NODE2A_PREREQ_SHA is required}"
: "${NODE2B_PREREQ_SHA:?NODE2B_PREREQ_SHA is required}"
: "${NODE2A_PASS_RECEIPT_PATH:?NODE2A_PASS_RECEIPT_PATH is required}"
: "${NODE2B_PASS_RECEIPT_PATH:?NODE2B_PASS_RECEIPT_PATH is required}"
: "${NODE2A_PASS_RECEIPT_SHA256:?NODE2A_PASS_RECEIPT_SHA256 is required}"
: "${NODE2B_PASS_RECEIPT_SHA256:?NODE2B_PASS_RECEIPT_SHA256 is required}"
: "${NODE2C_GOVERNANCE_CANDIDATE_PUBLICATION_PATH:?governance-candidate publication record path is required}"
: "${NODE2C_GOVERNANCE_CANDIDATE_PUBLICATION_SHA256:?governance-candidate publication record SHA-256 is required}"

NODE2C_PREFLIGHT_MODE="${NODE2C_PREFLIGHT_MODE:-initial}"
case "$NODE2C_PREFLIGHT_MODE" in
  initial | resume) ;;
  *) printf 'NODE2C_PREFLIGHT_MODE must be initial or resume\n' >&2; exit 1 ;;
esac
[[ "$NODE2C_GOVERNANCE_CANDIDATE_PUBLICATION_SHA256" =~ ^[0-9a-f]{64}$ ]]
NODE2B_REVIEWED_SHA=2be280b5a3194a83191753bfc1deb227a3d2dc31
NODE2C_IMPORT_GOVERNANCE_PARENT_SHA=e31c3951b06f06e995c0c8f6f8fe2f22320a38da
NODE2C_AMENDED_DESIGN_BLOB=f1ac9a517725ccdc7740108db82f89cd74d0e33f
test "$NODE2B_PREREQ_SHA" = "$NODE2B_REVIEWED_SHA"
export NODE2B_REVIEWED_SHA NODE2C_IMPORT_GOVERNANCE_PARENT_SHA \
  NODE2C_AMENDED_DESIGN_BLOB
readonly NODE2B_REVIEWED_SHA NODE2C_IMPORT_GOVERNANCE_PARENT_SHA \
  NODE2C_AMENDED_DESIGN_BLOB

NODE_PATHS=(
  src/polymarket_alpha_lab/team_evidence_aggregation.py
  tests/test_team_evidence_aggregation.py
  tests/test_team_evidence_aggregation_scope.py
)
EXPECTED_NODE_PATHS="$(printf '%s\n' "${NODE_PATHS[@]}")"
SORTED_NODE_PATHS="$(printf '%s\n' "${NODE_PATHS[@]}" | LC_ALL=C sort)"
test "$SORTED_NODE_PATHS" = "$EXPECTED_NODE_PATHS"
readonly -a NODE_PATHS
readonly EXPECTED_NODE_PATHS SORTED_NODE_PATHS

REPO_ROOT="$(git rev-parse --show-toplevel)"
COMMON_GIT_DIR="$(git rev-parse --path-format=absolute --git-common-dir)"
export REPO_ROOT NODE2A_PREREQ_SHA NODE2B_PREREQ_SHA
export NODE2A_PASS_RECEIPT_PATH NODE2B_PASS_RECEIPT_PATH
export NODE2A_PASS_RECEIPT_SHA256 NODE2B_PASS_RECEIPT_SHA256
export NODE2C_GOVERNANCE_CANDIDATE_PUBLICATION_PATH \
  NODE2C_GOVERNANCE_CANDIDATE_PUBLICATION_SHA256 NODE2C_PREFLIGHT_MODE
readonly COMMON_GIT_DIR

validate_predecessor_pass_receipt() {
  local evidence_name="$1"
  local expected_node="$2"
  local prereq_sha="$3"
  local receipt_path="$4"
  local expected_sha256="$5"
  local schema_variant="$6"

  RECEIPT_EVIDENCE_NAME="$evidence_name" \
  RECEIPT_EXPECTED_NODE="$expected_node" \
  RECEIPT_PREREQ_SHA="$prereq_sha" \
  RECEIPT_PATH="$receipt_path" \
  RECEIPT_EXPECTED_SHA256="$expected_sha256" \
  RECEIPT_SCHEMA_VARIANT="$schema_variant" \
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


evidence_name = os.environ["RECEIPT_EVIDENCE_NAME"]
expected_node = os.environ["RECEIPT_EXPECTED_NODE"]
prereq_sha = os.environ["RECEIPT_PREREQ_SHA"]
receipt_path = os.environ["RECEIPT_PATH"]
expected_sha256 = os.environ["RECEIPT_EXPECTED_SHA256"]
schema_variant = os.environ["RECEIPT_SCHEMA_VARIANT"]
repo_root = os.path.realpath(os.environ["REPO_ROOT"])

if re.fullmatch(r"NODE2[AB]_RECEIPT_EVIDENCE", evidence_name) is None:
    raise SystemExit("PASS receipt evidence name is invalid")
if expected_node not in {
    "team-evidence-aggregation-contracts-codec-temporal-eligibility",
    "team-evidence-aggregation-independence-correlation-requirement-witness",
}:
    raise SystemExit("PASS receipt expected node is invalid")
if schema_variant not in {"node2a-13", "node2b-15"}:
    raise SystemExit("PASS receipt schema variant is invalid")
if re.fullmatch(r"[0-9a-f]{40}", prereq_sha) is None:
    raise SystemExit("PASS receipt prerequisite SHA must be lowercase hexadecimal")
if re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None:
    raise SystemExit("PASS receipt SHA-256 must be lowercase hexadecimal")
if not os.path.isabs(receipt_path):
    raise SystemExit("PASS receipt path must be absolute")
if not os.path.isabs(repo_root) or not os.path.isdir(repo_root):
    raise SystemExit("REPO_ROOT must resolve to a directory")

try:
    descriptor = os.open(
        receipt_path,
        os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW,
    )
except OSError:
    raise SystemExit("PASS receipt descriptor open failed") from None

try:
    descriptor_stat = os.fstat(descriptor)
    if not stat.S_ISREG(descriptor_stat.st_mode):
        raise SystemExit("PASS receipt must be a regular file")
    if descriptor_stat.st_size <= 0 or descriptor_stat.st_size > 65_536:
        raise SystemExit("PASS receipt size is invalid")

    descriptor_link = os.readlink(f"/proc/self/fd/{descriptor}")
    if descriptor_link.endswith(" (deleted)"):
        raise SystemExit("PASS receipt descriptor is deleted")
    descriptor_path = os.path.realpath(descriptor_link)
    try:
        inside_repo = os.path.commonpath((repo_root, descriptor_path)) == repo_root
    except ValueError:
        raise SystemExit("PASS receipt descriptor path is invalid") from None
    if inside_repo:
        raise SystemExit("PASS receipt descriptor must resolve outside REPO_ROOT")

    receipt_bytes = os.read(descriptor, descriptor_stat.st_size + 1)
    if len(receipt_bytes) != descriptor_stat.st_size:
        raise SystemExit("PASS receipt changed while being read")
finally:
    os.close(descriptor)

actual_sha256 = hashlib.sha256(receipt_bytes).hexdigest()
if actual_sha256 != expected_sha256:
    raise SystemExit("PASS receipt SHA-256 mismatch")

try:
    payload = json.loads(
        receipt_bytes.decode("utf-8"),
        object_pairs_hook=reject_duplicate_keys,
    )
except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
    raise SystemExit("PASS receipt JSON is invalid or has duplicate keys") from None

expected_payload: dict[str, object] = {
    "node": expected_node,
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
if schema_variant == "node2a-13":
    if expected_node != "team-evidence-aggregation-contracts-codec-temporal-eligibility":
        raise SystemExit("Node 2A receipt descriptor is inconsistent")
else:
    if expected_node != "team-evidence-aggregation-independence-correlation-requirement-witness":
        raise SystemExit("Node 2B receipt descriptor is inconsistent")
    expected_payload["read_only"] = True
    expected_payload["fast_mode"] = False

if type(payload) is not dict or set(payload) != set(expected_payload):
    raise SystemExit("PASS receipt has the wrong closed shape")
if any(type(payload[key]) is not type(value) for key, value in expected_payload.items()):
    raise SystemExit("PASS receipt value types are invalid")
if payload != expected_payload:
    raise SystemExit("PASS receipt values do not match the required handoff")
canonical_bytes = json.dumps(
    payload,
    ensure_ascii=True,
    allow_nan=False,
    separators=(",", ":"),
    sort_keys=True,
).encode("ascii")
if receipt_bytes != canonical_bytes:
    raise SystemExit("PASS receipt bytes are not canonical")

evidence = {
    "prereq_sha": prereq_sha,
    "receipt_sha256": actual_sha256,
    "validated_payload": payload,
}
print(
    evidence_name
    + "="
    + json.dumps(evidence, ensure_ascii=True, separators=(",", ":"), sort_keys=True),
)
PY
}
readonly -f validate_predecessor_pass_receipt

validate_governance_candidate_publication() {
  GOVERNANCE_PUBLICATION_PATH="$NODE2C_GOVERNANCE_CANDIDATE_PUBLICATION_PATH" \
  GOVERNANCE_PUBLICATION_EXPECTED_SHA256="$NODE2C_GOVERNANCE_CANDIDATE_PUBLICATION_SHA256" \
  GOVERNANCE_PUBLICATION_PREDECESSOR_SHA="$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA" \
  GOVERNANCE_PUBLICATION_AMENDED_DESIGN_BLOB="$NODE2C_AMENDED_DESIGN_BLOB" \
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


publication_path = os.environ["GOVERNANCE_PUBLICATION_PATH"]
expected_sha256 = os.environ["GOVERNANCE_PUBLICATION_EXPECTED_SHA256"]
predecessor_sha = os.environ["GOVERNANCE_PUBLICATION_PREDECESSOR_SHA"]
amended_design_blob = os.environ["GOVERNANCE_PUBLICATION_AMENDED_DESIGN_BLOB"]
repo_root = os.path.realpath(os.environ["REPO_ROOT"])
plan_path = (
    "docs/superpowers/plans/"
    "2026-07-13-team-evidence-aggregation-status-facade-publishability-scope-guard.md"
)
design_path = (
    "docs/superpowers/specs/"
    "2026-07-13-team-evidence-aggregation-core-design.md"
)

if re.fullmatch(r"[0-9a-f]{40}", predecessor_sha) is None:
    raise SystemExit("governance predecessor SHA must be lowercase hexadecimal")
if re.fullmatch(r"[0-9a-f]{40}", amended_design_blob) is None:
    raise SystemExit("amended design blob must be lowercase hexadecimal")
if re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None:
    raise SystemExit("governance-candidate publication record SHA-256 must be lowercase hexadecimal")
if not os.path.isabs(publication_path):
    raise SystemExit("governance-candidate publication record path must be absolute")
if not os.path.isabs(repo_root) or not os.path.isdir(repo_root):
    raise SystemExit("REPO_ROOT must resolve to a directory")

try:
    descriptor = os.open(
        publication_path,
        os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW,
    )
except OSError:
    raise SystemExit("governance-candidate publication record descriptor open failed") from None

try:
    descriptor_stat = os.fstat(descriptor)
    if not stat.S_ISREG(descriptor_stat.st_mode):
        raise SystemExit("governance-candidate publication record must be a regular file")
    if descriptor_stat.st_size <= 0 or descriptor_stat.st_size > 65_536:
        raise SystemExit("governance-candidate publication record size is invalid")
    descriptor_link = os.readlink(f"/proc/self/fd/{descriptor}")
    if descriptor_link.endswith(" (deleted)"):
        raise SystemExit("governance-candidate publication record descriptor is deleted")
    descriptor_path = os.path.realpath(descriptor_link)
    try:
        inside_repo = os.path.commonpath((repo_root, descriptor_path)) == repo_root
    except ValueError:
        raise SystemExit("governance-candidate publication record descriptor path is invalid") from None
    if inside_repo:
        raise SystemExit("governance-candidate publication record must resolve outside REPO_ROOT")
    publication_bytes = os.read(descriptor, descriptor_stat.st_size + 1)
    if len(publication_bytes) != descriptor_stat.st_size:
        raise SystemExit("governance-candidate publication record changed while being read")
finally:
    os.close(descriptor)

actual_sha256 = hashlib.sha256(publication_bytes).hexdigest()
if actual_sha256 != expected_sha256:
    raise SystemExit("governance-candidate publication record SHA-256 mismatch")
try:
    payload = json.loads(
        publication_bytes.decode("utf-8"),
        object_pairs_hook=reject_duplicate_keys,
    )
except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
    raise SystemExit(
        "governance-candidate publication record JSON is invalid or has duplicate keys",
    ) from None

expected_keys = {
    "schema",
    "predecessor_sha",
    "governance_candidate_sha",
    "plan_path",
    "changed_paths",
    "plan_blob",
    "design_blob",
    "review_model",
    "review_effort",
    "read_only",
    "fast_mode",
    "review_exit_status",
    "review_final_nonblank_line",
    "review_report_sha256",
    "remote_endpoint_sha256",
    "bash_fences",
    "shell_failure_harness",
    "codegraph_full_index",
    "confirmed_remote_main_sha",
}
if len(expected_keys) != 19:
    raise SystemExit("governance-candidate publication record schema must remain exactly nineteen keys")
if type(payload) is not dict or set(payload) != expected_keys:
    raise SystemExit("governance-candidate publication record has the wrong closed shape")
string_keys = expected_keys - {
    "changed_paths",
    "read_only",
    "fast_mode",
    "review_exit_status",
}
if any(type(payload[key]) is not str for key in string_keys):
    raise SystemExit("governance-candidate publication record string value types are invalid")
if type(payload["changed_paths"]) is not list or any(
    type(value) is not str for value in payload["changed_paths"]
):
    raise SystemExit("governance changed_paths must be a JSON string list")
if type(payload["read_only"]) is not bool or type(payload["fast_mode"]) is not bool:
    raise SystemExit("governance-candidate publication record boolean value types are invalid")
if type(payload["review_exit_status"]) is not int:
    raise SystemExit("governance review_exit_status must be an exact int")

candidate_sha = payload["governance_candidate_sha"]
plan_blob = payload["plan_blob"]
design_blob = payload["design_blob"]
for name, value, width in (
    ("governance_candidate_sha", candidate_sha, 40),
    ("plan_blob", plan_blob, 40),
    ("design_blob", design_blob, 40),
    ("review_report_sha256", payload["review_report_sha256"], 64),
    ("remote_endpoint_sha256", payload["remote_endpoint_sha256"], 64),
):
    if re.fullmatch(rf"[0-9a-f]{{{width}}}", value) is None:
        raise SystemExit(f"governance {name} must be lowercase hexadecimal")

required_values: dict[str, object] = {
    "schema": "pal.governance-candidate-publication.v1",
    "predecessor_sha": predecessor_sha,
    "plan_path": plan_path,
    "changed_paths": [plan_path, design_path],
    "design_blob": amended_design_blob,
    "review_model": "claude-fable-5",
    "review_effort": "max",
    "read_only": True,
    "fast_mode": False,
    "review_exit_status": 0,
    "review_final_nonblank_line": "VERDICT: PASS",
    "bash_fences": "pass",
    "shell_failure_harness": "pass",
    "codegraph_full_index": "pass",
    "confirmed_remote_main_sha": candidate_sha,
}
for key, expected in required_values.items():
    if payload[key] != expected:
        raise SystemExit(f"governance-candidate publication record {key} does not match handoff")
canonical_bytes = json.dumps(
    payload,
    ensure_ascii=True,
    allow_nan=False,
    separators=(",", ":"),
    sort_keys=True,
).encode("ascii") + b"\n"
if publication_bytes != canonical_bytes:
    raise SystemExit("governance-candidate publication record bytes are not canonical")

evidence = {
    "governance_candidate_publication_sha256": actual_sha256,
    "validated_payload": payload,
}
print(
    "GOVERNANCE_CANDIDATE_PUBLICATION_EVIDENCE="
    + json.dumps(evidence, ensure_ascii=True, separators=(",", ":"), sort_keys=True),
)
print(candidate_sha)
print(plan_blob)
print(design_blob)
print(payload["remote_endpoint_sha256"])
print(payload["review_report_sha256"])
PY
}
readonly -f validate_governance_candidate_publication

INITIAL_NODE2A_RECEIPT_EVIDENCE="$(
  validate_predecessor_pass_receipt \
    NODE2A_RECEIPT_EVIDENCE \
    team-evidence-aggregation-contracts-codec-temporal-eligibility \
    "$NODE2A_PREREQ_SHA" \
    "$NODE2A_PASS_RECEIPT_PATH" \
    "$NODE2A_PASS_RECEIPT_SHA256" \
    node2a-13
)"
INITIAL_NODE2B_RECEIPT_EVIDENCE="$(
  validate_predecessor_pass_receipt \
    NODE2B_RECEIPT_EVIDENCE \
    team-evidence-aggregation-independence-correlation-requirement-witness \
    "$NODE2B_PREREQ_SHA" \
    "$NODE2B_PASS_RECEIPT_PATH" \
    "$NODE2B_PASS_RECEIPT_SHA256" \
    node2b-15
)"
GOVERNANCE_CANDIDATE_PUBLICATION_OUTPUT="$(
  validate_governance_candidate_publication
)"
mapfile -t GOVERNANCE_CANDIDATE_PUBLICATION_LINES <<< \
  "$GOVERNANCE_CANDIDATE_PUBLICATION_OUTPUT"
test "${#GOVERNANCE_CANDIDATE_PUBLICATION_LINES[@]}" -eq 6
INITIAL_GOVERNANCE_CANDIDATE_PUBLICATION_EVIDENCE="${GOVERNANCE_CANDIDATE_PUBLICATION_LINES[0]}"
NODE2C_EXPECTED_BASE="${GOVERNANCE_CANDIDATE_PUBLICATION_LINES[1]}"
NODE2C_REVIEWED_PLAN_BLOB="${GOVERNANCE_CANDIDATE_PUBLICATION_LINES[2]}"
NODE2C_REVIEWED_DESIGN_BLOB="${GOVERNANCE_CANDIDATE_PUBLICATION_LINES[3]}"
NODE2C_GOVERNANCE_REMOTE_ENDPOINT_SHA256="${GOVERNANCE_CANDIDATE_PUBLICATION_LINES[4]}"
NODE2C_GOVERNANCE_REVIEW_REPORT_SHA256="${GOVERNANCE_CANDIDATE_PUBLICATION_LINES[5]}"
test -n "$INITIAL_NODE2A_RECEIPT_EVIDENCE"
test -n "$INITIAL_NODE2B_RECEIPT_EVIDENCE"
test -n "$INITIAL_GOVERNANCE_CANDIDATE_PUBLICATION_EVIDENCE"
[[ "$NODE2C_EXPECTED_BASE" =~ ^[0-9a-f]{40}$ ]]
[[ "$NODE2C_REVIEWED_PLAN_BLOB" =~ ^[0-9a-f]{40}$ ]]
[[ "$NODE2C_REVIEWED_DESIGN_BLOB" =~ ^[0-9a-f]{40}$ ]]
test "$NODE2C_REVIEWED_DESIGN_BLOB" = "$NODE2C_AMENDED_DESIGN_BLOB"
[[ "$NODE2C_GOVERNANCE_REMOTE_ENDPOINT_SHA256" =~ ^[0-9a-f]{64}$ ]]
[[ "$NODE2C_GOVERNANCE_REVIEW_REPORT_SHA256" =~ ^[0-9a-f]{64}$ ]]
export INITIAL_NODE2A_RECEIPT_EVIDENCE INITIAL_NODE2B_RECEIPT_EVIDENCE \
  INITIAL_GOVERNANCE_CANDIDATE_PUBLICATION_EVIDENCE NODE2C_EXPECTED_BASE \
  NODE2C_REVIEWED_PLAN_BLOB NODE2C_REVIEWED_DESIGN_BLOB \
  NODE2C_GOVERNANCE_REMOTE_ENDPOINT_SHA256 \
  NODE2C_GOVERNANCE_REVIEW_REPORT_SHA256
readonly GOVERNANCE_CANDIDATE_PUBLICATION_OUTPUT \
  INITIAL_GOVERNANCE_CANDIDATE_PUBLICATION_EVIDENCE NODE2C_EXPECTED_BASE \
  NODE2C_REVIEWED_PLAN_BLOB NODE2C_REVIEWED_DESIGN_BLOB \
  NODE2C_GOVERNANCE_REMOTE_ENDPOINT_SHA256 \
  NODE2C_GOVERNANCE_REVIEW_REPORT_SHA256
```

Expected: every command exits `0`. The Node 2B receipt independently and exactly
binds `NODE2B_PREREQ_SHA` to the fixed reviewed Node 2B commit; the governance
publication record separately binds `predecessor_sha` to the fixed published
import-governance parent and remains closed at exactly nineteen keys. In each of
the initial and final validation passes, each of the two predecessor receipts
and the governance-candidate publication record uses
exactly one
`os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)` descriptor. That
descriptor is `fstat`-checked as a bounded nonempty regular file, so a FIFO cannot block before
the nonregular-file rejection. The descriptor is resolved through
`/proc/self/fd` outside `REPO_ROOT`, read exactly once, hashed over those same
bytes, parsed with duplicate-key rejection, and compared by exact key set,
exact base value types, and exact values. The canonical JSON evidence contains
no artifact path or free text and binds the node-specific name, predecessor or
candidate SHA, artifact SHA-256, and validated closed payload. The governance
payload alone derives the expected base and reviewed blobs. A path precheck, symlink,
in-repository target, nonregular/oversized file, partial read, hash mismatch,
duplicate/extra/missing key, wrong boolean type, wrong node/SHA, or non-PASS
value blocks Node 2C.

- [ ] **Step 2: Fetch `origin/main`; separately prove parent, candidate, and blobs**

Continue in the same shell session:

```bash
assert_node2c_git_controls
NODE2C_PLAN_PATH=docs/superpowers/plans/2026-07-13-team-evidence-aggregation-status-facade-publishability-scope-guard.md
NODE2C_DESIGN_PATH=docs/superpowers/specs/2026-07-13-team-evidence-aggregation-core-design.md
NODE2C_EXPECTED_GOVERNANCE_PATHS="$(
  printf '%s\n' "$NODE2C_PLAN_PATH" "$NODE2C_DESIGN_PATH" |
    LC_ALL=C sort
)"
test "$NODE2C_EXPECTED_GOVERNANCE_PATHS" = "$(
  printf '%s\n' "$NODE2C_PLAN_PATH" "$NODE2C_DESIGN_PATH"
)"
set +e
NODE2C_REMOTE_ENDPOINT="$(
  git remote get-url --push --all origin 2>/dev/null
)"
NODE2C_ENDPOINT_STATUS=$?
set -e
if [ "$NODE2C_ENDPOINT_STATUS" -ne 0 ]; then
  printf 'Node 2C remote endpoint lookup failed\n' >&2
  exit "$NODE2C_ENDPOINT_STATUS"
fi
test -n "$NODE2C_REMOTE_ENDPOINT"
test "${NODE2C_REMOTE_ENDPOINT//$'\n'/}" = "$NODE2C_REMOTE_ENDPOINT"
NODE2C_REMOTE_ENDPOINT_SHA256="$(
  NODE2C_REMOTE_ENDPOINT_VALUE="$NODE2C_REMOTE_ENDPOINT" \
    .venv/bin/python - <<'PY'
import hashlib
import os

print(
    hashlib.sha256(
        os.environ["NODE2C_REMOTE_ENDPOINT_VALUE"].encode("utf-8"),
    ).hexdigest(),
)
PY
)"
test "$NODE2C_REMOTE_ENDPOINT_SHA256" = \
  "$NODE2C_GOVERNANCE_REMOTE_ENDPOINT_SHA256"
GIT_AUTH=(-c credential.helper= -c "credential.helper=store --file=$COMMON_GIT_DIR/github-credentials")
set +e
GIT_TERMINAL_PROMPT=0 git "${GIT_AUTH[@]}" fetch --no-tags \
  "$NODE2C_REMOTE_ENDPOINT" \
  refs/heads/main:refs/remotes/origin/main >/dev/null 2>&1
NODE2C_FETCH_STATUS=$?
set -e
if [ "$NODE2C_FETCH_STATUS" -ne 0 ]; then
  printf 'Node 2C remote fetch failed\n' >&2
  exit "$NODE2C_FETCH_STATUS"
fi
assert_node2c_git_controls

REMOTE_NODE_BASE="$(git rev-parse refs/remotes/origin/main)"
test "$REMOTE_NODE_BASE" = "$NODE2C_EXPECTED_BASE"

# Fixed published import-governance parent provenance.
NODE2C_IMPORT_PARENT_TEXT="$(
  git rev-list --parents -n 1 "$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA"
)"
read -r -a NODE2C_IMPORT_PARENT_AND_PARENT <<< \
  "$NODE2C_IMPORT_PARENT_TEXT"
test "${#NODE2C_IMPORT_PARENT_AND_PARENT[@]}" -eq 2
test "${NODE2C_IMPORT_PARENT_AND_PARENT[0]}" = \
  "$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA"
test "${NODE2C_IMPORT_PARENT_AND_PARENT[1]}" = "$NODE2B_REVIEWED_SHA"
NODE2C_IMPORT_PARENT_COMMIT_COUNT="$(
  git rev-list --count \
    "$NODE2B_REVIEWED_SHA..$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA"
)"
test "$NODE2C_IMPORT_PARENT_COMMIT_COUNT" -eq 1
NODE2C_IMPORT_PARENT_CHANGED_PATHS="$(
  git diff-tree --no-commit-id --name-only -r --no-renames \
    "$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA"
)"
test "$NODE2C_IMPORT_PARENT_CHANGED_PATHS" = "$NODE2C_PLAN_PATH"
NODE2C_IMPORT_PARENT_SUBJECT="$(
  git show -s --format=%s "$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA"
)"
test "$NODE2C_IMPORT_PARENT_SUBJECT" = \
  'docs: align Node 2C module import governance'

# Hardened governance candidate provenance.
NODE2C_CANDIDATE_PARENT_TEXT="$(
  git rev-list --parents -n 1 "$NODE2C_EXPECTED_BASE"
)"
read -r -a NODE2C_CANDIDATE_AND_PARENT <<< \
  "$NODE2C_CANDIDATE_PARENT_TEXT"
test "${#NODE2C_CANDIDATE_AND_PARENT[@]}" -eq 2
test "${NODE2C_CANDIDATE_AND_PARENT[0]}" = "$NODE2C_EXPECTED_BASE"
test "${NODE2C_CANDIDATE_AND_PARENT[1]}" = \
  "$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA"
NODE2C_CANDIDATE_COMMIT_COUNT="$(
  git rev-list --count \
    "$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA..$NODE2C_EXPECTED_BASE"
)"
test "$NODE2C_CANDIDATE_COMMIT_COUNT" -eq 1
NODE2C_CANDIDATE_CHANGED_PATHS="$(
  git diff-tree --no-commit-id --name-only -r --no-renames \
    "$NODE2C_EXPECTED_BASE"
)"
test "$NODE2C_CANDIDATE_CHANGED_PATHS" = \
  "$NODE2C_EXPECTED_GOVERNANCE_PATHS"
NODE2C_CANDIDATE_SUBJECT="$(
  git show -s --format=%s "$NODE2C_EXPECTED_BASE"
)"
test "$NODE2C_CANDIDATE_SUBJECT" = \
  'docs: align Node 2C witness ownership governance'
NODE2C_GOVERNANCE_CHAIN="$(
  git rev-list --reverse "$NODE2B_REVIEWED_SHA..$NODE2C_EXPECTED_BASE"
)"
NODE2C_EXPECTED_GOVERNANCE_CHAIN="$(
  printf '%s\n' \
    "$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA" \
    "$NODE2C_EXPECTED_BASE"
)"
test "$NODE2C_GOVERNANCE_CHAIN" = "$NODE2C_EXPECTED_GOVERNANCE_CHAIN"
NODE2C_PREFLIGHT_HEAD="$(git rev-parse HEAD)"
readonly NODE2C_PREFLIGHT_HEAD
if [ "$NODE2C_PREFLIGHT_MODE" = initial ]; then
  test "$NODE2C_PREFLIGHT_HEAD" = "$NODE2C_EXPECTED_BASE"
else
  git merge-base --is-ancestor \
    "$NODE2C_EXPECTED_BASE" "$NODE2C_PREFLIGHT_HEAD"
  NODE2C_DESCENDANT_MERGES="$(
    git rev-list --merges \
      "$NODE2C_EXPECTED_BASE..$NODE2C_PREFLIGHT_HEAD"
  )"
  test -z "$NODE2C_DESCENDANT_MERGES"
  if NODE2C_ENDPOINT_PATHS_TEXT="$(
    git diff --no-renames --name-only \
      "$NODE2C_EXPECTED_BASE..$NODE2C_PREFLIGHT_HEAD"
  )"; then
    NODE2C_ENDPOINT_PATHS_STATUS=0
  else
    NODE2C_ENDPOINT_PATHS_STATUS=$?
  fi
  if [ "$NODE2C_ENDPOINT_PATHS_STATUS" -ne 0 ]; then
    printf 'endpoint path diff failed with status %s\n' \
      "$NODE2C_ENDPOINT_PATHS_STATUS" >&2
    exit "$NODE2C_ENDPOINT_PATHS_STATUS"
  fi
  NODE2C_ENDPOINT_PATHS_SORTED="$(
    LC_ALL=C sort <<< "$NODE2C_ENDPOINT_PATHS_TEXT"
  )"
  test "$NODE2C_ENDPOINT_PATHS_SORTED" = "$EXPECTED_NODE_PATHS"
  if NODE2C_ENDPOINT_ACM_PATHS_TEXT="$(
    git diff --no-renames --diff-filter=ACM --name-only \
      "$NODE2C_EXPECTED_BASE..$NODE2C_PREFLIGHT_HEAD"
  )"; then
    NODE2C_ENDPOINT_ACM_PATHS_STATUS=0
  else
    NODE2C_ENDPOINT_ACM_PATHS_STATUS=$?
  fi
  if [ "$NODE2C_ENDPOINT_ACM_PATHS_STATUS" -ne 0 ]; then
    printf 'endpoint ACM path diff failed with status %s\n' \
      "$NODE2C_ENDPOINT_ACM_PATHS_STATUS" >&2
    exit "$NODE2C_ENDPOINT_ACM_PATHS_STATUS"
  fi
  NODE2C_ENDPOINT_ACM_PATHS_SORTED="$(
    LC_ALL=C sort <<< "$NODE2C_ENDPOINT_ACM_PATHS_TEXT"
  )"
  test "$NODE2C_ENDPOINT_ACM_PATHS_SORTED" = "$EXPECTED_NODE_PATHS"
  NODE2C_FORBIDDEN_ENDPOINT_PATHS="$(
    git diff --no-renames --diff-filter=DRTUXB --name-only \
      "$NODE2C_EXPECTED_BASE..$NODE2C_PREFLIGHT_HEAD"
  )"
  test -z "$NODE2C_FORBIDDEN_ENDPOINT_PATHS"

  NODE2C_DESCENDANT_COMMITS_TEXT="$(
    git rev-list --reverse \
      "$NODE2C_EXPECTED_BASE..$NODE2C_PREFLIGHT_HEAD"
  )"
  mapfile -t NODE2C_DESCENDANT_COMMITS <<< "$NODE2C_DESCENDANT_COMMITS_TEXT"
  test "${#NODE2C_DESCENDANT_COMMITS[@]}" -ge 1
  NODE2C_PREFLIGHT_TMP_DIR="$(
    mktemp -d /home/ubuntu/test-sandbox/tmp/node2c-preflight.XXXXXX
  )"
  cleanup_node2c_preflight_tmp() {
    rm -rf -- "$NODE2C_PREFLIGHT_TMP_DIR"
  }
  trap cleanup_node2c_preflight_tmp EXIT
  COMMIT_PATHS_FILE="$NODE2C_PREFLIGHT_TMP_DIR/commit-paths"
  for commit in "${NODE2C_DESCENDANT_COMMITS[@]}"; do
    COMMIT_PARENTS_TEXT="$(git show -s --format=%P "$commit")"
    read -r -a COMMIT_PARENTS <<< "$COMMIT_PARENTS_TEXT"
    test "${#COMMIT_PARENTS[@]}" -eq 1
    git diff-tree --no-commit-id --name-only -r --no-renames -z \
      "$commit" > "$COMMIT_PATHS_FILE"
    mapfile -d '' -t COMMIT_PATHS < "$COMMIT_PATHS_FILE"
    test "${#COMMIT_PATHS[@]}" -ge 1
    for path in "${COMMIT_PATHS[@]}"; do
      case "$path" in
        src/polymarket_alpha_lab/team_evidence_aggregation.py | \
        tests/test_team_evidence_aggregation.py | \
        tests/test_team_evidence_aggregation_scope.py) ;;
        *) printf 'non-allowlisted descendant path: %s\n' "$path" >&2; exit 1 ;;
      esac
    done
    COMMIT_FORBIDDEN_PATHS="$(
      git diff-tree --no-commit-id --name-only -r --no-renames \
        --diff-filter=DRTUXB "$commit"
    )"
    test -z "$COMMIT_FORBIDDEN_PATHS"
  done
  cleanup_node2c_preflight_tmp
  trap - EXIT
fi
assert_node2c_git_controls
NODE2C_PREFLIGHT_POST_HISTORY_HEAD="$(git rev-parse HEAD)"
test "$NODE2C_PREFLIGHT_POST_HISTORY_HEAD" = "$NODE2C_PREFLIGHT_HEAD"

# Receipt-reviewed plan and design blobs.
NODE2C_IMPORT_PLAN_BLOB="$(
  git rev-parse \
    "$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA:$NODE2C_PLAN_PATH"
)"
NODE2C_IMPORT_DESIGN_BLOB="$(
  git rev-parse \
    "$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA:$NODE2C_DESIGN_PATH"
)"
NODE2C_PLAN_BLOB_AT_BASE="$(
  git rev-parse "$NODE2C_EXPECTED_BASE:$NODE2C_PLAN_PATH"
)"
test "$NODE2C_PLAN_BLOB_AT_BASE" = "$NODE2C_REVIEWED_PLAN_BLOB"
test "$NODE2C_PLAN_BLOB_AT_BASE" != "$NODE2C_IMPORT_PLAN_BLOB"
NODE2C_DESIGN_BLOB_AT_BASE="$(
  git rev-parse "$NODE2C_EXPECTED_BASE:$NODE2C_DESIGN_PATH"
)"
test "$NODE2C_DESIGN_BLOB_AT_BASE" = "$NODE2C_REVIEWED_DESIGN_BLOB"
test "$NODE2C_DESIGN_BLOB_AT_BASE" = "$NODE2C_AMENDED_DESIGN_BLOB"
test "$NODE2C_DESIGN_BLOB_AT_BASE" != "$NODE2C_IMPORT_DESIGN_BLOB"
readonly REMOTE_NODE_BASE NODE2C_PLAN_PATH NODE2C_DESIGN_PATH \
  REPLACEMENT_REFS_AFTER_FETCH SHALLOW_REPOSITORY_AFTER_FETCH \
  NODE2C_IMPORT_PLAN_BLOB NODE2C_IMPORT_DESIGN_BLOB \
  NODE2C_PLAN_BLOB_AT_BASE NODE2C_DESIGN_BLOB_AT_BASE

NODE_BASE="$NODE2C_EXPECTED_BASE"
export NODE_BASE NODE2C_EXPECTED_BASE
readonly NODE_BASE NODE2C_EXPECTED_BASE
test "$REMOTE_NODE_BASE" = "$NODE_BASE"
git merge-base --is-ancestor "$NODE2A_PREREQ_SHA" "$NODE2B_PREREQ_SHA"
test "${NODE2C_IMPORT_PARENT_AND_PARENT[1]}" = "$NODE2B_PREREQ_SHA"
test "${NODE2C_CANDIDATE_AND_PARENT[1]}" = \
  "$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA"
git merge-base --is-ancestor \
  "$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA" "$NODE_BASE"
git merge-base --is-ancestor "$NODE_BASE" "$NODE2C_PREFLIGHT_HEAD"
git cat-file -e "$NODE2A_PREREQ_SHA^{commit}"
git cat-file -e "$NODE2B_PREREQ_SHA^{commit}"
git cat-file -e "$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA^{commit}"
git cat-file -e "$NODE_BASE^{commit}"

NODE2C_TRACKED_STATUS="$(git status --porcelain --untracked-files=no)"
test -z "$NODE2C_TRACKED_STATUS"
git diff --quiet
git diff --cached --quiet
NODE2C_OWNED_UNTRACKED="$(git ls-files --others --exclude-standard -- \
  src/polymarket_alpha_lab/team_evidence_aggregation.py \
  tests/test_team_evidence_aggregation.py \
  tests/test_team_evidence_aggregation_scope.py)"
test -z "$NODE2C_OWNED_UNTRACKED"
assert_node2c_git_controls

readonly REPO_ROOT NODE2A_PREREQ_SHA NODE2B_PREREQ_SHA
readonly NODE2A_PASS_RECEIPT_PATH NODE2B_PASS_RECEIPT_PATH
readonly NODE2A_PASS_RECEIPT_SHA256 NODE2B_PASS_RECEIPT_SHA256
readonly NODE2C_GOVERNANCE_CANDIDATE_PUBLICATION_PATH \
  NODE2C_GOVERNANCE_CANDIDATE_PUBLICATION_SHA256
readonly INITIAL_NODE2A_RECEIPT_EVIDENCE INITIAL_NODE2B_RECEIPT_EVIDENCE
readonly INITIAL_GOVERNANCE_CANDIDATE_PUBLICATION_EVIDENCE
readonly NODE2C_PREFLIGHT_MODE NODE2C_REVIEWED_PLAN_BLOB \
  NODE2C_REVIEWED_DESIGN_BLOB
```

Expected: both modes require fetched
`origin/main == NODE2C_EXPECTED_BASE == NODE_BASE`, where only the hardened
candidate SHA and reviewed plan/design blobs were derived from the validated
governance-candidate publication record. The four trust checks remain separate: the Node 2B receipt
binds exact reviewed SHA `2be280b5a3194a83191753bfc1deb227a3d2dc31`; fixed
parent `e31c3951b06f06e995c0c8f6f8fe2f22320a38da` has Node 2B as its sole
parent, the exact import-governance subject, and exactly one changed plan path;
the hardened candidate has `e31c3951` as its sole parent, the exact
`docs: align Node 2C witness ownership governance` subject, and exactly the plan
then core design paths; and the candidate's plan/design blobs equal the
receipt-reviewed blobs, with design blob
`f1ac9a517725ccdc7740108db82f89cd74d0e33f` distinct from `e31c3951`. The exact
Node 2B-to-candidate chain contains the plan-only parent followed by the
two-document candidate.
Replacements, grafts, and shallow history remain disabled. Initial mode
additionally requires
`HEAD == NODE_BASE`; resume mode requires fetched `origin/main == NODE_BASE`,
descendant local `HEAD`, no merge commit, and the exact three-path
implementation range. In both modes Node 2A is an ancestor of Node 2B, the
tracked worktree and index are clean, and none of the three owned paths is an
unrelated untracked file. `NODE_BASE` is readonly and is never derived from the
descendant local `HEAD`; because `NODE_BASE` is the hardened candidate,
`NODE_BASE..HEAD` excludes both governance-document commits.

- [ ] **Step 3: Validate the exact predecessor path surfaces and immutability**

```bash
NODE2A_PATHS=(
  src/polymarket_alpha_lab/team_evidence_aggregation_codec.py
  src/polymarket_alpha_lab/team_evidence_aggregation_temporal.py
  src/polymarket_alpha_lab/team_evidence_aggregation_types.py
  tests/test_team_evidence_aggregation_codec.py
  tests/test_team_evidence_aggregation_temporal.py
  tests/test_team_evidence_aggregation_types.py
)
NODE2B_PATHS=(
  src/polymarket_alpha_lab/team_evidence_aggregation_allocation.py
  src/polymarket_alpha_lab/team_evidence_aggregation_witness.py
  tests/test_team_evidence_aggregation_allocation.py
  tests/test_team_evidence_aggregation_witness.py
)

NODE2A_PATHS_TEXT="$(printf '%s\n' "${NODE2A_PATHS[@]}")"
NODE2A_PATHS_SORTED="$(printf '%s\n' "${NODE2A_PATHS[@]}" | LC_ALL=C sort)"
test "$NODE2A_PATHS_SORTED" = "$NODE2A_PATHS_TEXT"
NODE2B_PATHS_TEXT="$(printf '%s\n' "${NODE2B_PATHS[@]}")"
NODE2B_PATHS_SORTED="$(printf '%s\n' "${NODE2B_PATHS[@]}" | LC_ALL=C sort)"
test "$NODE2B_PATHS_SORTED" = "$NODE2B_PATHS_TEXT"

assert_node2c_git_controls
for path in "${NODE2A_PATHS[@]}"; do
  git cat-file -e "$NODE2A_PREREQ_SHA:$path"
done
for path in "${NODE2B_PATHS[@]}"; do
  git cat-file -e "$NODE2B_PREREQ_SHA:$path"
done

git diff --quiet "$NODE2A_PREREQ_SHA..$NODE_BASE" -- "${NODE2A_PATHS[@]}"
git diff --quiet "$NODE2B_PREREQ_SHA..$NODE_BASE" -- "${NODE2B_PATHS[@]}"
NODE2A_HISTORY_TOUCHES="$(
  git log --format=%H "$NODE2A_PREREQ_SHA..$NODE_BASE" -- \
    "${NODE2A_PATHS[@]}"
)"
test -z "$NODE2A_HISTORY_TOUCHES"
NODE2B_HISTORY_TOUCHES="$(
  git log --format=%H "$NODE2B_PREREQ_SHA..$NODE_BASE" -- \
    "${NODE2B_PATHS[@]}"
)"
test -z "$NODE2B_HISTORY_TOUCHES"

NODE2A_RECEIPT_EVIDENCE_CURRENT="$(
  validate_predecessor_pass_receipt \
    NODE2A_RECEIPT_EVIDENCE \
    team-evidence-aggregation-contracts-codec-temporal-eligibility \
    "$NODE2A_PREREQ_SHA" \
    "$NODE2A_PASS_RECEIPT_PATH" \
    "$NODE2A_PASS_RECEIPT_SHA256" \
    node2a-13
)"
NODE2B_RECEIPT_EVIDENCE_CURRENT="$(
  validate_predecessor_pass_receipt \
    NODE2B_RECEIPT_EVIDENCE \
    team-evidence-aggregation-independence-correlation-requirement-witness \
    "$NODE2B_PREREQ_SHA" \
    "$NODE2B_PASS_RECEIPT_PATH" \
    "$NODE2B_PASS_RECEIPT_SHA256" \
    node2b-15
)"
GOVERNANCE_CANDIDATE_PUBLICATION_OUTPUT_CURRENT="$(
  validate_governance_candidate_publication
)"
test "$NODE2A_RECEIPT_EVIDENCE_CURRENT" = \
  "$INITIAL_NODE2A_RECEIPT_EVIDENCE"
test "$NODE2B_RECEIPT_EVIDENCE_CURRENT" = \
  "$INITIAL_NODE2B_RECEIPT_EVIDENCE"
test "$GOVERNANCE_CANDIDATE_PUBLICATION_OUTPUT_CURRENT" = \
  "$GOVERNANCE_CANDIDATE_PUBLICATION_OUTPUT"
assert_node2c_git_controls
NODE2C_PREFLIGHT_FINAL_HEAD="$(git rev-parse HEAD)"
test "$NODE2C_PREFLIGHT_FINAL_HEAD" = "$NODE2C_PREFLIGHT_HEAD"
assert_node2c_git_controls

printf '%s\n' \
  "$INITIAL_NODE2A_RECEIPT_EVIDENCE" \
  "$INITIAL_NODE2B_RECEIPT_EVIDENCE" \
  "$INITIAL_GOVERNANCE_CANDIDATE_PUBLICATION_EVIDENCE" \
  "NODE2C_IMPORT_GOVERNANCE_PARENT_SHA=$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA" \
  "NODE2C_EXPECTED_BASE=$NODE2C_EXPECTED_BASE" \
  "NODE2C_REVIEWED_PLAN_BLOB=$NODE2C_REVIEWED_PLAN_BLOB" \
  "NODE2C_REVIEWED_DESIGN_BLOB=$NODE2C_REVIEWED_DESIGN_BLOB" \
  "NODE2C_GOVERNANCE_REMOTE_ENDPOINT_SHA256=$NODE2C_GOVERNANCE_REMOTE_ENDPOINT_SHA256" \
  "NODE2C_GOVERNANCE_REVIEW_REPORT_SHA256=$NODE2C_GOVERNANCE_REVIEW_REPORT_SHA256" \
  "NODE_BASE=$NODE_BASE"
```

Expected: every predecessor path exists at its reviewed commit and is
byte-unchanged from that commit through `NODE_BASE`. The final validation pass
reproduces all three initial canonical receipt results byte-for-byte. Success
emits exactly ten newline-delimited, non-secret records shown above. A caller
parses each record at its first `=` and must never `source` or `eval` this output.
Any receipt replacement or path drift requires predecessor amendment and a fresh
PASS receipt; Node 2C does not proceed.

---

### Task 2: Drive The Reducer Through Both Selector Identity Sets And All Dispositions

**Files:**
- Create: `tests/test_team_evidence_aggregation.py`
- Create: `src/polymarket_alpha_lab/team_evidence_aggregation.py`

**Interfaces:**
- Consumes: all fixed predecessor interfaces above and exact Node 2A dataclasses.
- Produces: the private canonical reduction path, one diagnostic per supplied input record, exact allocation/witness handoff, all thirteen dispositions, arithmetic universes and totals, and the public builder signature.

- [ ] **Step 1: Add deterministic fixture builders before production code**

In `tests/test_team_evidence_aggregation.py`, import public types from their defining modules, never the package root. Use this fixed fixture policy:

```python
BASE_TIME = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
EVALUATED_AT = BASE_TIME + timedelta(seconds=100)


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(label: str) -> str:
    return sha256(label.encode("ascii")).hexdigest()


BASE_CONFIG_VALUES: dict[str, object] = {
    "config_version": "generic-test-v1",
    "max_evidence_age_seconds": d("60.000000"),
    "max_capture_lag_seconds": d("20.000000"),
    "independence_group_weight_cap": d("1.000000"),
    "correlation_group_weight_cap": d("1.000000"),
    "max_requirement_assignments_per_evidence": 2,
    "contradiction_no_probability_max": d("0.250000"),
    "contradiction_yes_probability_min": d("0.750000"),
    "contradiction_watch_score": d("0.250000"),
    "contradiction_block_score": d("0.750000"),
    "publish_probability_floor": d("0.110000"),
    "publish_probability_ceiling": d("0.890000"),
    "maximum_records": 128,
    "maximum_requirements": 32,
    "maximum_requirement_memberships": 1024,
    "maximum_witness_edges": 256,
    "requirements": (),
}
```

Define these exact test helpers:

```python
def config(**changes: object) -> TeamEvidenceAggregationConfig:
    values = dict(BASE_CONFIG_VALUES)
    values.update(changes)
    return TeamEvidenceAggregationConfig(**values)


def root_record(
    stem: str,
    *,
    freshness_anchor_offset: int = 50,
    captured_offset: int = 55,
    recorded_offset: int = 60,
    assessed_offset: int = 65,
    probability_yes: Decimal = d("0.600000"),
    requested_weight: Decimal = d("0.200000"),
    requirement_ids: tuple[str, ...] = (),
    independence_key: str | None = None,
    correlation_key: str | None = None,
) -> TeamEvidenceAggregationRecord:
    source_lineage_id = f"lineage:{stem}"
    source_lineage_digest = digest(f"lineage-digest:{stem}")
    content_digest = digest(f"content:{stem}")
    evidence_revision_id = f"evidence:{stem}"
    evidence_revision_digest = digest(f"evidence-digest:{stem}")
    lineage = TeamEvidenceSourceLineage(
        source_lineage_id=source_lineage_id,
        source_lineage_digest=source_lineage_digest,
    )
    capture = TeamEvidenceCapture(
        capture_id=f"capture:{stem}",
        capture_digest=digest(f"capture-digest:{stem}"),
        source_lineage_id=source_lineage_id,
        source_lineage_digest=source_lineage_digest,
        content_digest=content_digest,
        captured_at=BASE_TIME + timedelta(seconds=captured_offset),
    )
    evidence_revision = TeamEvidenceRevision(
        evidence_revision_id=evidence_revision_id,
        evidence_revision_digest=evidence_revision_digest,
        previous_evidence_revision_id=None,
        previous_evidence_revision_digest=None,
        source_lineage_id=source_lineage_id,
        source_lineage_digest=source_lineage_digest,
        content_digest=content_digest,
        requirement_ids=requirement_ids,
        freshness_anchor_at=BASE_TIME + timedelta(seconds=freshness_anchor_offset),
        recorded_at=BASE_TIME + timedelta(seconds=recorded_offset),
    )
    assessment_revision = TeamEvidenceAssessmentRevision(
        assessment_revision_id=f"assessment:{stem}",
        assessment_revision_digest=digest(f"assessment-digest:{stem}"),
        previous_assessment_revision_id=None,
        previous_assessment_revision_digest=None,
        evidence_revision_id=evidence_revision_id,
        evidence_revision_digest=evidence_revision_digest,
        assessed_at=BASE_TIME + timedelta(seconds=assessed_offset),
        probability_yes=probability_yes,
        requested_weight=requested_weight,
        rationale_digest=digest(f"rationale:{stem}"),
        independence_key=independence_key or f"ind:{stem}",
        correlation_key=correlation_key or f"corr:{stem}",
    )
    return TeamEvidenceAggregationRecord(
        source_lineage=lineage,
        capture=capture,
        evidence_revision=evidence_revision,
        assessment_revision=assessment_revision,
    )


def recapture(
    record: TeamEvidenceAggregationRecord,
    *,
    stem: str,
    captured_offset: int,
) -> TeamEvidenceAggregationRecord:
    capture = TeamEvidenceCapture(
        capture_id=f"capture:{stem}",
        capture_digest=digest(f"capture-digest:{stem}"),
        source_lineage_id=record.capture.source_lineage_id,
        source_lineage_digest=record.capture.source_lineage_digest,
        content_digest=record.capture.content_digest,
        captured_at=BASE_TIME + timedelta(seconds=captured_offset),
    )
    return replace(record, capture=capture)


def selection(
    record: TeamEvidenceAggregationRecord,
) -> TeamEvidenceCurrentRevisionSelection:
    return TeamEvidenceCurrentRevisionSelection(
        evidence_revision_id=record.evidence_revision.evidence_revision_id,
        evidence_revision_digest=record.evidence_revision.evidence_revision_digest,
        assessment_revision_id=record.assessment_revision.assessment_revision_id,
        assessment_revision_digest=record.assessment_revision.assessment_revision_digest,
    )


def aggregation_input(
    records: tuple[TeamEvidenceAggregationRecord, ...],
    *,
    current_records: tuple[TeamEvidenceAggregationRecord, ...],
    evaluated_at: datetime = EVALUATED_AT,
) -> TeamEvidenceAggregationInput:
    return TeamEvidenceAggregationInput(
        evaluated_at=evaluated_at,
        records=records,
        current_revisions=tuple(selection(record) for record in current_records),
    )


def diagnostic_key(row: TeamEvidenceDiagnosticRow) -> tuple[object, ...]:
    return (
        row.assessment_revision_id,
        row.evidence_revision_id,
        row.captured_at,
        row.capture_id,
        row.source_lineage_id,
    )


def diagnostic_row_for_record(
    result: TeamEvidenceAggregationResult,
    record: TeamEvidenceAggregationRecord,
) -> TeamEvidenceDiagnosticRow:
    expected_identity = (
        record.source_lineage.source_lineage_id,
        record.capture.capture_id,
        record.evidence_revision.evidence_revision_id,
        record.assessment_revision.assessment_revision_id,
    )
    matches = tuple(
        row
        for row in result.diagnostics
        if (
            row.source_lineage_id,
            row.capture_id,
            row.evidence_revision_id,
            row.assessment_revision_id,
        )
        == expected_identity
    )
    assert len(matches) == 1
    return matches[0]
```

`recapture` changes only capture ID, capture digest, and `captured_at`; it preserves the exact lineage, evidence revision, and assessment revision objects. `aggregation_input` emits one exact selection per `current_records` item. All helpers rely on Node 2A constructors to canonicalize tuples and validate hard flags.

Expected: fixtures use conspicuously non-BTC publication bounds `0.110000` and `0.890000`, exact aware datetimes, exact `Decimal`, and no ambient time, DB, network, CLI, filesystem data, auth, account, wallet, order, or execution input.

- [ ] **Step 2: Write failing selector-boundary and diagnostic-universe tests**

Add the exact tests `test_builder_calls_both_canonical_selectors_with_exact_input_and_config`, `test_canonical_capture_is_true_for_a_wholly_noncurrent_revision`, `test_selected_current_revision_is_pair_level_across_recaptures`, and `test_every_supplied_record_has_exactly_one_sorted_diagnostic_row`. Their decisive assertions are:

```python
assert calls == [
    ("capture", aggregation_input_value, config_value),
    ("current", aggregation_input_value, config_value),
]
assert [(row.canonical_capture, row.selected_current_revision, row.disposition)] == [
    (True, False, "not_current_revision"),
]
assert [
    (
        row.capture_id,
        row.selected_current_revision,
        row.canonical_capture,
        row.disposition,
    )
    for row in result.diagnostics
] == [
    (canonical.capture.capture_id, True, True, "included"),
    (duplicate.capture.capture_id, True, False, "duplicate_capture"),
]
assert result.diagnostic_record_count == len(input_value.records)
assert len(result.diagnostics) == len(input_value.records)
assert tuple(diagnostic_key(row) for row in result.diagnostics) == tuple(
    sorted(diagnostic_key(row) for row in result.diagnostics)
)
assert tuple(
    (
        row.source_lineage_id,
        row.capture_id,
        row.evidence_revision_id,
        row.assessment_revision_id,
    )
    for row in result.diagnostics
) == tuple(
    (
        record.source_lineage.source_lineage_id,
        record.capture.capture_id,
        record.evidence_revision.evidence_revision_id,
        record.assessment_revision.assessment_revision_id,
    )
    for record in input_value.records
)
```

For at least one excluded row, also assert exact preservation of probability,
requested weight, capture timestamp, temporal deltas and availability flags,
plus unsigned fixed-six zero independence/effective weights. A same-length
diagnostic tuple with a missing or invented record identity must fail.

The selector spy wrappers must call the real predecessor functions after recording `(selector_name, aggregation_input, config)`. This proves both public selectors remain the validation and identity boundary; do not mock their outputs into invented identities.

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/test_team_evidence_aggregation.py::test_builder_calls_both_canonical_selectors_with_exact_input_and_config \
  tests/test_team_evidence_aggregation.py::test_canonical_capture_is_true_for_a_wholly_noncurrent_revision \
  tests/test_team_evidence_aggregation.py::test_selected_current_revision_is_pair_level_across_recaptures \
  tests/test_team_evidence_aggregation.py::test_every_supplied_record_has_exactly_one_sorted_diagnostic_row
```

Expected: FAIL during collection because `polymarket_alpha_lab.team_evidence_aggregation` does not exist.

- [ ] **Step 3: Write failing disposition-precedence tests for all thirteen values**

Use one scenario per row in `test_preallocation_dispositions_follow_exact_precedence` so each failure identifies one contract. The parameter IDs and expected disposition tuple are exact:

```python
DISPOSITION_CASES = (
    ("not_current_revision", "not_current_revision"),
    ("duplicate_capture", "duplicate_capture"),
    ("freshness_anchor_after_evaluation", "freshness_anchor_after_evaluation"),
    ("capture_after_evaluation", "capture_after_evaluation"),
    ("evidence_revision_after_evaluation", "evidence_revision_after_evaluation"),
    ("assessment_revision_after_evaluation", "assessment_revision_after_evaluation"),
    ("stale", "stale"),
    ("capture_before_freshness_anchor", "capture_before_freshness_anchor"),
    ("capture_lag_exceeded", "capture_lag_exceeded"),
    ("zero_requested_weight", "zero_requested_weight"),
    ("included", "included"),
)
```

For every parameter row, build the single decisive scenario from the table below and assert:

```python
assert len(result.diagnostics) == 1
assert result.diagnostics[0].disposition == expected_disposition
```

Build the cases with these exact decisive values:

| Case | Exact decisive condition |
| --- | --- |
| `not_current_revision` | canonical root record, `current_records=()` |
| `duplicate_capture` | selected exact pair, later recapture at offset `56`; assert the canonical row separately remains `included` |
| `freshness_anchor_after_evaluation` | anchor `101`, capture `101`, recorded `101`, assessed `101`, evaluated `100` |
| `capture_after_evaluation` | anchor `90`, capture `101`, recorded `101`, assessed `101`, evaluated `100` |
| `evidence_revision_after_evaluation` | anchor `50`, capture `55`, recorded `101`, assessed `101`, evaluated `100` |
| `assessment_revision_after_evaluation` | anchor `50`, capture `55`, recorded `60`, assessed `101`, evaluated `100` |
| `stale` | anchor `39`, capture `40`, recorded `41`, assessed `42`, evaluated `100`, max age `60` |
| `capture_before_freshness_anchor` | anchor `50`, capture `49`, recorded `50`, assessed `51` |
| `capture_lag_exceeded` | anchor `50`, capture `71`, recorded `71`, assessed `72`, max lag `20` |
| `zero_requested_weight` | otherwise eligible with requested weight `0.000000` |
| `included` | the default root record |

Add `test_independence_cap_exhausted_is_distinct_from_zero_request` and `test_correlation_cap_exhausted_requires_positive_stage_one_weight` with these exact assertions:

```python
independence_exhausted = diagnostic_row_for_record(
    result,
    independence_exhausted_record,
)
assert independence_exhausted.requested_weight == d("0.000001")
assert independence_exhausted.independence_allocated_weight == d("0.000000")
assert independence_exhausted.effective_weight == d("0.000000")
assert independence_exhausted.disposition == "independence_cap_exhausted"

correlation_exhausted = diagnostic_row_for_record(
    result,
    correlation_exhausted_record,
)
assert correlation_exhausted.requested_weight > d("0.000000")
assert correlation_exhausted.independence_allocated_weight > d("0.000000")
assert correlation_exhausted.effective_weight == d("0.000000")
assert correlation_exhausted.disposition == "correlation_cap_exhausted"
```

For the independence fixture, bind the `z-independence-exhausted` record as
`independence_exhausted_record`; use stems `a-independence-kept` and
`z-independence-exhausted`, requested weight `0.000001` on both, shared
independence key `ind:shared`, distinct correlation keys, and independence cap
`0.000001`. For the correlation fixture, bind the `z-correlation-exhausted`
record as `correlation_exhausted_record`; use stems `a-correlation-kept` and
`z-correlation-exhausted`, requested weight `0.000001` on both, distinct
independence keys, shared correlation key `corr:shared`, independence cap
`1.000000`, and correlation cap `0.000001`. The exact assessment-ID-first
canonical key gives the `a-` row the one remainder micro-unit and the `z-` row
zero. Assert the companion row is `included` and the applicable group sum is
exactly `0.000001`.

Add one precedence regression with a later recapture that is also future/stale/zero-weight and assert only `duplicate_capture`; add one non-current future/stale record and assert only `not_current_revision`. This proves earlier dispositions dominate all later gates.

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/test_team_evidence_aggregation.py::test_preallocation_dispositions_follow_exact_precedence \
  tests/test_team_evidence_aggregation.py::test_independence_cap_exhausted_is_distinct_from_zero_request \
  tests/test_team_evidence_aggregation.py::test_correlation_cap_exhausted_requires_positive_stage_one_weight
```

Expected: FAIL because the builder and disposition pipeline are not implemented.

- [ ] **Step 4: Write failing allocation/witness trust-boundary and historical-selection tests**

Add the exact tests
`test_allocation_and_witness_receive_the_exact_same_candidate_tuple`,
`test_old_exact_pair_remains_current_while_successors_are_present`,
`test_recapture_cannot_repair_freshness_lag_or_availability`,
`test_future_evidence_or_assessment_revision_never_leaks_into_historical_arithmetic`,
`test_malformed_allocator_output_reaches_real_witness_once_with_exact_objects`,
`test_retired_requirement_ids_reject_only_positive_effective_candidates`, and
`test_empty_input_is_typed_blocked_no_arithmetic_result`.
Their decisive assertions are:

```python
assert calls == [
    ("allocation", expected_candidates, policy),
    ("witness", expected_candidates, canonical_allocations, policy),
]
assert calls[1][1] is owned[0]
assert calls[1][2] is owned[1]
assert len(allocation_calls) == len(witness_calls) == 1
assert candidate_tuple is allocation_calls[0][0]
assert allocations is malformed
assert malformed.callback_count == 0
assert selected_old_row.selected_current_revision is True
assert selected_old_row.disposition == "included"
assert successor_rows
assert all(row.disposition == "not_current_revision" for row in successor_rows)
assert canonical_row.disposition == "capture_lag_exceeded"
assert duplicate_row.disposition == "duplicate_capture"
assert result.arithmetic_record_count == 0
assert tuple(row.disposition for row in historical_result.diagnostics) == (
    "evidence_revision_after_evaluation",
    "assessment_revision_after_evaluation",
)
assert historical_result.arithmetic_record_count == 0
assert historical_result.effective_weight_total == d("0.000000")
```

`expected_candidates` is the canonical-record-key-sorted tuple of records that
are selected-current by the three-field pair identity, canonical by the exact
four-field capture identity, effective and available at all four temporal
layers, fresh, timely, and strictly positive requested weight. It includes rows
later exhausted by either cap. The spy wraps and invokes the real Node 2B
allocator and witness functions. It retains the allocation-input tuple and the
allocator's exact returned object, asserts with `is` that both cross the witness
boundary unchanged, records the real witness return, and records the first
facade allocation consumption only afterward. It does not recompute, compare,
sort, project, or otherwise validate allocation or coverage semantics.

Parameterize recapture non-repair over canonical dispositions `stale`,
`capture_lag_exceeded`, `evidence_revision_after_evaluation`, and
`assessment_revision_after_evaluation`; the corresponding later recapture is
always `duplicate_capture`. Add one integration test that substitutes a
non-tuple allocator return, proves the exact object reaches the real Node 2B
witness boundary unchanged, and asserts its owner error
`allocations must be an exact tuple` propagates unchanged before any facade
consumer runs. This is an ownership assertion, not a second allocation
validator. Empty input must call allocation with `()` and witness coverage with
exact `(), (), config`. Do not add Node 2C assertions for witness field order,
candidate-edge order, coverage construction, allocation recomputation, or any
other Node 2B-owned validity rule.

Also add exact end-to-end rejection tests named:

```text
test_builder_rejects_conflicting_functional_dependencies_through_selectors
test_builder_rejects_nonclosed_revision_chains_through_selectors
test_builder_rejects_invalid_local_time_order_through_selectors
test_builder_rejects_two_current_pairs_in_one_lineage_through_selectors
test_builder_rejects_anchor_only_noop_successor_through_selectors
test_builder_rejects_recapture_that_changes_revision_owned_fields
```

Assert these six complete literal descriptions, in the test order above:
`capture.capture_id must determine one complete projection`,
`evidence_revision graph must be one connected linear chain`,
`evidence_revision canonical capture.captured_at must be at or before recorded_at`,
`current_revisions permits at most one current pair per source lineage`,
`evidence_revision successor must contain a semantic change`, and
`evidence_revision.evidence_revision_id must determine one complete projection`.
These are the runtime-verified Node 2A public errors; Node 2C must not catch and
translate them. Use exact `str(error.value)` equality, not an unanchored regex,
and prove every exception occurs before allocation. Do not duplicate Node 2A
graph or selection validation in Node 2C.

Run the named tests. Expected: FAIL until the reducer composes the predecessor APIs exactly.

- [ ] **Step 5: Implement the minimal canonical diagnostic/allocation/witness pipeline**

Create `src/polymarket_alpha_lab/team_evidence_aggregation.py` with only the approved imports and literal `__all__`. Use these exact private keys and branch order:

```python
def _record_key(record: TeamEvidenceAggregationRecord) -> tuple[object, ...]:
    return (
        record.assessment_revision.assessment_revision_id,
        record.evidence_revision.evidence_revision_id,
        record.capture.captured_at,
        record.capture.capture_id,
        record.source_lineage.source_lineage_id,
    )


def _record_identity(
    record: TeamEvidenceAggregationRecord,
) -> tuple[str, str, str, str]:
    return (
        record.source_lineage.source_lineage_id,
        record.capture.capture_id,
        record.evidence_revision.evidence_revision_id,
        record.assessment_revision.assessment_revision_id,
    )


def _selected_pair_identity(
    record: TeamEvidenceAggregationRecord,
) -> tuple[str, str, str]:
    return (
        record.source_lineage.source_lineage_id,
        record.evidence_revision.evidence_revision_id,
        record.assessment_revision.assessment_revision_id,
    )
```

Define these child-private arithmetic constants and helper in
`team_evidence_aggregation.py`; they are not imported from a predecessor module
and are not public exports:

```python
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_TWO = Decimal("2")
_SIX_PLACES = Decimal("0.000001")
_ARITHMETIC_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


def _quantize_once(value: Decimal) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError("aggregation arithmetic must be finite Decimal")
    try:
        with localcontext(_ARITHMETIC_CONTEXT):
            quantized = value.quantize(_SIX_PLACES)
            return _ZERO if quantized.is_zero() else quantized
    except DecimalException:
        raise ValueError("aggregation arithmetic must be quantizable") from None
```

Every product, running sum, division, ratio, comparison, and call to
`_quantize_once` executes under a local copy of `_ARITHMETIC_CONTEXT`; no code
reads or mutates the ambient Decimal context. The shared private materializer
then performs this exact sequence:

1. Call `select_team_evidence_canonical_capture_records(aggregation_input, config=config)`.
2. Call `select_team_evidence_canonical_current_records(aggregation_input, config=config)`.
3. Sort `aggregation_input.records` by `_record_key` and build both exact four-field sets plus the three-field selected-pair projection.
4. Call `assess_team_evidence_temporal` for every sorted record, including non-current and duplicate rows.
5. Assign each row's first applicable pre-allocation disposition in this exact order:

```python
if selected_pair_identity not in selected_pair_identities:
    disposition = "not_current_revision"
elif record_identity not in canonical_current_identities:
    disposition = "duplicate_capture"
elif not temporal.effective_at_evaluation:
    disposition = "freshness_anchor_after_evaluation"
elif not temporal.captured_at_evaluation:
    disposition = "capture_after_evaluation"
elif not temporal.evidence_revision_available_at_evaluation:
    disposition = "evidence_revision_after_evaluation"
elif not temporal.assessment_revision_available_at_evaluation:
    disposition = "assessment_revision_after_evaluation"
elif not temporal.fresh:
    disposition = "stale"
elif temporal.capture_lag_seconds < _ZERO:
    disposition = "capture_before_freshness_anchor"
elif not temporal.timely:
    disposition = "capture_lag_exceeded"
elif record.assessment_revision.requested_weight == _ZERO:
    disposition = "zero_requested_weight"
else:
    disposition = None
```

6. Pass the exact sorted `disposition is None` record tuple to `allocate_team_evidence_weights`.
7. Immediately call the public Node 2B `build_team_evidence_requirement_coverage` boundary with that exact allocation-input tuple and the allocator's exact returned object by identity, even when both canonical tuples are empty. Do not inspect, copy, sort, map, reconstruct, compare, or otherwise consume allocations first.
8. Treat a successful Node 2B witness return as the authoritative validation of both canonical allocation recomputation and coverage construction. Only after that call returns successfully may Node 2C read validated allocation rows for diagnostics and use the exact returned coverage tuple for status.
9. Finalize candidate dispositions: stage-one zero is `independence_cap_exhausted`; positive stage one plus stage-two zero is `correlation_cap_exhausted`; positive effective weight is `included`.
10. Build one `TeamEvidenceDiagnosticRow` per sorted input record. Pre-allocation exclusions have zero independence/effective weight. Allocation candidates expose the canonical allocated values. Every row preserves the capture's exact canonical `captured_at`, raw probability, raw requested weight, temporal deltas/availability, the three-field selected flag, and four-field canonical-capture flag. The diagnostic tuple is therefore locally ordered and verifiable by the complete canonical record key.

Node 2C does not duplicate Node 2B's allocation, coverage, witness, or
global-matching validation. The witness API owns exact allocation type/resource
checks, canonical recomputation, join/projection precedence, candidate
generation, witness ordering, and canonical coverage construction. Node 2C
preserves exact object identity through that boundary, passes authoritative
coverage through to the result, and consumes only the returned values needed for
facade diagnostics and status. For an externally supplied final result, a wrong
outer type first maps to exact
`result must be exactly TeamEvidenceAggregationResult`. The codec then proves
canonical recursive shape without invoking supplied field callbacks. Codec
failure immediately maps to `aggregation result must equal rematerialized
result` and does not rematerialize. Only after codec success may dependency
rematerialization run; malformed input/config errors therefore retain their
exact predecessor descriptions. Once rematerialization succeeds, every
supplied-result shape, coverage, witness, digest, or other semantic mismatch
maps to the same generic mismatch.

Totals are exact:

```text
diagnostic_record_count = len(all sorted records)
arithmetic_record_count = count(disposition == "included")
requested_weight_total = sum(requested weight over the allocation-input tuple)
independence_allocated_weight_total = sum(stage-one weight over all allocations)
effective_weight_total = sum(effective weight over included allocations)
```

Use local-context unquantized sums and fixed-six quantization only at the final total boundary. Canonicalize every zero to unsigned `Decimal("0.000000")`. Catch only `DecimalException` subclasses needed to convert invalid Decimal arithmetic into field-specific `ValueError`; do not catch `Exception` or `BaseException`.

At this point the materializer may also compute the final status fields exactly as Task 3 specifies; do not add a temporary public API, alternate materializer, or policy default. The public builder returns the materializer result directly.

- [ ] **Step 6: Run the focused reducer tests**

```bash
.venv/bin/python -m pytest -q tests/test_team_evidence_aggregation.py
```

Expected: selector, diagnostic, disposition, allocation/witness-flow, old-selection, recapture, temporal replay, and malformed-input tests pass. Probability/status tests added in Task 3 remain the next red step, not skipped or weakened.

---

### Task 3: Derive Probability, Contradiction, Status, Reasons, And Ready-Only Publication

**Files:**
- Modify: `tests/test_team_evidence_aggregation.py`
- Modify: `src/polymarket_alpha_lab/team_evidence_aggregation.py`

**Interfaces:**
- Consumes: exact included diagnostics, effective allocations, and requirement coverage from Task 2.
- Produces: exact weighted arithmetic `P(YES)`, contradiction result, strict readiness precedence, complete static reason tuples, and ready-only bounded publication.

- [ ] **Step 1: Write failing arithmetic and universe tests**

Add the exact tests `test_weighted_probability_uses_included_effective_weights_and_one_final_quantization`, `test_diagnostic_and_arithmetic_universes_have_exact_counts_and_weights`, and `test_probability_is_canonical_pyes_without_complement_prior_market_or_log_odds`. Their decisive assertions are:

```python
assert result.requested_weight_total == d("1.000000")
assert result.independence_allocated_weight_total == d("1.000000")
assert result.effective_weight_total == d("1.000000")
assert result.arithmetic_record_count == 2
assert result.arithmetic_probability_yes == d("0.620000")
assert mixed_result.diagnostic_record_count == 5
assert mixed_result.arithmetic_record_count == 2
assert tuple(row.disposition for row in mixed_result.diagnostics) == expected_dispositions
assert mixed_result.effective_weight_total == sum(
    (
        row.effective_weight
        for row in mixed_result.diagnostics
        if row.disposition == "included"
    ),
    d("0.000000"),
)
assert canonical_result.arithmetic_probability_yes == d("0.200000")
assert canonical_result.arithmetic_probability_yes != d("0.800000")
```

The `0.620000` vector is two included records: `P(YES)=0.200000` at effective weight `0.300000` and `P(YES)=0.800000` at effective weight `0.700000`. Add `test_weighted_probability_does_not_quantize_products_before_sum` with two included records, each having `P(YES)=0.000001` and effective weight `0.500000`; assert exact arithmetic probability `0.000001`. Independently quantizing each `0.0000005` product would incorrectly produce zero under HALF_EVEN, so this vector proves one final quantization. Add `test_hostile_ambient_decimal_context_preserves_result_payload_and_digest`; set ambient precision to `6`, rounding to `ROUND_UP`, and the `Inexact` trap to true inside `try/finally`, then assert the typed result, `team_evidence_aggregation_payload`, and `core_digest` equal their baseline values byte for byte.

Run the three tests. Expected: FAIL until arithmetic is derived from included rows.

- [ ] **Step 2: Write failing contradiction boundary tests**

Add `test_one_sided_support_has_no_contradiction_even_when_watch_threshold_is_zero`, parameterized `test_contradiction_thresholds_are_inclusive_and_block_is_checked_first`, and `test_neutral_weight_is_reported_but_does_not_dilute_opposing_support`. Use the exact boundary vectors and assertions:

```python
CONTRADICTION_BOUNDARY_CASES = (
    (d("0.700000"), d("0.100000"), d("0.250000"), "watch"),
    (d("0.500000"), d("0.300000"), d("0.750000"), "blocked"),
)

assert one_sided_result.contradiction == TeamEvidenceContradictionResult(
    yes_support_weight=d("0.700000"),
    no_support_weight=d("0.000000"),
    neutral_weight=d("0.300000"),
    contradiction_score=d("0.000000"),
    status="none",
)
assert boundary_result.contradiction.contradiction_score == expected_score
assert boundary_result.contradiction.status == expected_status
assert neutral_result.contradiction.neutral_weight == d("0.900000")
assert neutral_result.contradiction.contradiction_score == d("1.000000")
```

Use `P(YES)=0.750000` for inclusive yes support, `0.250000` for inclusive no support, and `0.500000` for neutral. Configure per-record cap groups so the asserted effective weights survive unchanged.

Expected: FAIL until contradiction uses `2 * min(Y, N) / (Y + N)`, quantized once, with the explicit both-sides check before thresholds.

- [ ] **Step 3: Write failing readiness, exact-reason, and publication tests**

Assert that the facade passes through the authoritative Node 2B coverage tuple
and consumes its `satisfied`/`unmet_status` fields for status and exact reasons;
do not re-test witness construction or ordering here. Also assert
rematerialized-result mismatch handling, then use this literal parameter value in
`test_status_precedence_and_mixed_reason_tuples_are_exact`:

```python
STATUS_REASON_CASES = (
        (
            "no_arithmetic_plus_block_and_watch_requirements",
            "blocked",
            (
                "blocking_requirement_unmet",
                "no_arithmetic_evidence",
                "watch_requirement_unmet",
            ),
        ),
        (
            "contradiction_blocked_plus_watch_requirement",
            "blocked",
            ("contradiction_blocked", "watch_requirement_unmet"),
        ),
        (
            "blocking_requirement_plus_contradiction_watch",
            "blocked",
            ("blocking_requirement_unmet", "contradiction_watch"),
        ),
        (
            "watch_requirement_plus_contradiction_watch",
            "watch",
            ("contradiction_watch", "watch_requirement_unmet"),
        ),
)

assert result.status == expected_status
assert result.reason_codes == expected_reasons
assert result.publishable_probability_yes is None
```

Use this literal parameter value in `test_ready_publication_uses_only_supplied_nonbtc_bounds`:

```python
READY_PUBLICATION_CASES = (
        (
            d("0.050000"),
            d("0.110000"),
            ("aggregation_ready", "publish_probability_floor_applied"),
        ),
        (
            d("0.950000"),
            d("0.890000"),
            ("aggregation_ready", "publish_probability_ceiling_applied"),
        ),
        (d("0.110000"), d("0.110000"), ("aggregation_ready",)),
        (d("0.890000"), d("0.890000"), ("aggregation_ready",)),
        (d("0.500000"), d("0.500000"), ("aggregation_ready",)),
)

assert result.status == "ready"
assert result.arithmetic_probability_yes == probability
assert result.publishable_probability_yes == expected_publishable
assert result.reason_codes == expected_reasons
```

Add:

```text
test_nonready_result_retains_arithmetic_probability_but_never_publishes
test_empty_input_is_typed_blocked_no_arithmetic_result
test_all_excluded_input_is_blocked_without_erasing_diagnostics
test_result_contains_exactly_one_coverage_row_per_config_requirement
test_zero_candidate_requirement_preserves_every_configured_coverage_field
```

The empty-input assertions are exact: zero diagnostic/arithmetic counts, all three weight totals `0.000000`, both probabilities `None`, zero contradiction weights/score with status `none`, one coverage row per configured requirement, top-level status `blocked`, and reason tuple containing `no_arithmetic_evidence` plus each independently applicable static requirement reason.

Run these tests. Expected: FAIL until readiness and publication are derived.

- [ ] **Step 4: Implement exact probability, contradiction, status, and reasons**

Inside the private materializer, sort included record/allocation pairs by `_record_key` and compute under the isolated local context:

```text
numerator = sum(probability_yes * effective_weight without intermediate quantization)
denominator = sum(effective_weight without intermediate quantization)
arithmetic_probability_yes = None when denominator == 0
otherwise raw_probability = numerator / denominator
require _ZERO <= raw_probability <= _ONE before quantization
arithmetic_probability_yes = _quantize_once(raw_probability)
```

Partition included effective weights exactly:

```text
no: probability_yes <= config.contradiction_no_probability_max
yes: probability_yes >= config.contradiction_yes_probability_min
neutral: strict interior
```

If either opposing side is zero, contradiction score/status is `0.000000`/`none`. Otherwise compute `_quantize_once(2 * min(Y, N) / (Y + N))`, classify `blocked` first at `>= contradiction_block_score`, then `watch` at `>= contradiction_watch_score`, else `none`.

Derive top-level status in this exact precedence:

```python
blocked = (
    arithmetic_probability_yes is None
    or any(not row.satisfied and row.unmet_status == "blocked" for row in coverage)
    or contradiction.status == "blocked"
)
watch = (
    any(not row.satisfied and row.unmet_status == "watch" for row in coverage)
    or contradiction.status == "watch"
)
status = "blocked" if blocked else "watch" if watch else "ready"
```

Build a set from only these static codes, then emit `tuple(sorted(codes))`:

```text
aggregation_ready
blocking_requirement_unmet
contradiction_blocked
contradiction_watch
no_arithmetic_evidence
publish_probability_ceiling_applied
publish_probability_floor_applied
watch_requirement_unmet
```

Add each applicable requirement and contradiction code independently, even when a blocker already determines status. Add `aggregation_ready` only when ready. For ready status, clamp publication to exact supplied bounds without changing arithmetic probability and add a floor/ceiling code only for a strict change. For watch/blocked, publication is always `None`.

- [ ] **Step 5: Run all reducer tests under normal and hostile Decimal contexts**

```bash
.venv/bin/python -m pytest -q tests/test_team_evidence_aggregation.py
```

Expected: every Task 2/3 test passes; no skip, xfail, relaxed membership-only reason assertion, or broad exception assertion remains.

---

### Task 4: Share One Private Materializer And Validate Config/Core Digests

**Files:**
- Modify: `tests/test_team_evidence_aggregation.py`
- Modify: `src/polymarket_alpha_lab/team_evidence_aggregation.py`

**Interfaces:**
- Consumes: `team_evidence_aggregation_config_digest`, `team_evidence_aggregation_core_digest`, and `validate_team_evidence_aggregation_core_digest` from the Node 2A codec.
- Produces: a builder and independent public validator over one private semantic materializer, with exact field equality and digest validation.

- [ ] **Step 1: Write failing rematerialization and tamper tests**

Add:

```python
def test_result_validator_returns_exact_none_for_builder_result() -> None:
    result = build_team_evidence_aggregation_result(input_value, config=config_value)

    assert validate_team_evidence_aggregation_result(
        result,
        aggregation_input=input_value,
        config=config_value,
    ) is None


def bypassed_result(
    result: TeamEvidenceAggregationResult,
    **changes: object,
) -> TeamEvidenceAggregationResult:
    forged = object.__new__(TeamEvidenceAggregationResult)
    for field in fields(TeamEvidenceAggregationResult):
        object.__setattr__(
            forged,
            field.name,
            changes.get(field.name, getattr(result, field.name)),
        )
    return forged


@pytest.mark.parametrize(
    "field_change",
    (
        {"status": "watch"},
        {"diagnostic_record_count": 999},
        {"arithmetic_probability_yes": d("0.123456")},
        {"publishable_probability_yes": None},
        {"reason_codes": ("aggregation_ready", "contradiction_watch")},
        {"core_digest": "f" * 64},
        {"config_digest": "e" * 64},
    ),
)
def test_result_validator_rejects_every_tampered_top_level_field(
    field_change: dict[str, object],
) -> None:
    result = build_team_evidence_aggregation_result(input_value, config=config_value)
    tampered = bypassed_result(result, **field_change)
    with pytest.raises(ValueError, match="aggregation result must equal rematerialized result"):
        validate_team_evidence_aggregation_result(
            tampered,
            aggregation_input=input_value,
            config=config_value,
        )
```

Also add exact tests:

```text
test_result_validator_rejects_tampered_nested_contradiction
test_result_validator_rejects_tampered_diagnostic
test_result_validator_rejects_missing_extra_duplicate_or_reordered_requirement_coverage
test_facade_rejects_raw_witness_requirement_id_projection_drift
test_result_validator_rejects_wrong_exact_result_type_and_constructor_bypass
test_result_validator_rejects_constructor_bypassed_snan_with_stable_mismatch_error
test_result_validator_maps_self_referential_exact_result_to_stable_mismatch
test_result_validator_rejects_unchanged_valid_result_for_different_input_or_config
test_result_validator_rejects_constructor_valid_semantic_result_with_recomputed_digest
test_result_validator_codec_precedes_rematerialization_and_supplied_callbacks
test_result_validator_preserves_malformed_input_and_config_errors
test_result_validator_rejects_self_digested_nested_semantic_tampers
test_result_validator_is_hostile_decimal_context_invariant
test_materializer_uses_codec_helpers_in_exact_sequence
test_result_validator_maps_bypassed_wrong_field_type
test_builder_config_digest_equals_exact_codec_digest
test_builder_core_digest_equals_exact_codec_digest
test_core_digest_changes_when_any_semantic_result_field_changes
test_semantic_tuple_permutations_produce_equal_results_payloads_and_digests
```

For supplied-result defensive validation, retain this facade-owned projection
invariant after codec canonicality succeeds:

```python
tuple(row.requirement_id for row in result.requirement_coverage) == tuple(requirement.requirement_id for requirement in config.requirements)
```

Separately, exercise missing, extra, duplicate, reordered, and omitted zero-candidate requirement IDs
by substituting validly typed raw witness-return tuples at the facade boundary,
and assert every configured zero-candidate row is preserved. This matrix is
separate from supplied-result codec canonicality and constructor-bypass tests.
For status consumption, assert the facade derives status and reasons from the
authoritative coverage fields. These tests do not reconstruct or validate Node
2B allocation, coverage-field, witness, matching, or candidate-edge semantics;
the projection check verifies only the facade-owned one-row-per-configured-ID
shape and order. The validator must reject forged/reordered supplied coverage
even if its top-level status and reasons look plausible. The
different-input/config test passes an unchanged, validly
digested result so digest-only validation cannot satisfy the test. The
rehashed-tamper test changes a constructor-valid semantic field, recomputes its
canonical core digest, and still requires rejection against the original input
and config. Self-digested nested diagnostic, contradiction, and coverage
forgeries must first pass the public codec validator and then fail only the
public rematerializing validator. In
`test_result_validator_codec_precedes_rematerialization_and_supplied_callbacks`,
trace exact successful events `("supplied-codec", "rematerialize")`. Then put an
equality tripwire in a constructor-bypassed exact result's `config_version`,
require the generic mismatch, prove the tripwire callback never runs, and prove
the only event is `"supplied-codec"`; codec failure must not rematerialize.
Malformed input/config cases use a codec-valid supplied result and must retain
the exact predecessor errors because dependency rematerialization runs only
after supplied codec success and outside supplied-result failure mapping. Trace the
module-local config-digest, core-digest, and core-validator calls so construction
proves the exact sibling sequence and exactly one final codec validation. Run
successful and forged result validation while a hostile Decimal context is
active and prove caller context preservation. For the constructor-bypass
regression, create an exact
`TeamEvidenceAggregationResult` with `object.__new__`, copy every slot from a
valid builder result with `object.__setattr__`, replace one Decimal total with
`Decimal("sNaN")`, and require exact
`ValueError("aggregation result must equal rematerialized result")`; no
`decimal.InvalidOperation` may escape. Wrong top-level exact type alone keeps
`ValueError("result must be exactly TeamEvidenceAggregationResult")`. Incomplete
exact shape, nested wrong shape, wrong field type, digest mismatch, and every
semantic mismatch map to the generic error; a codec-invalid supplied result does
so immediately, without rematerializing.
Self-referential and recursion-depth constructor-bypass cases must map
`RecursionError` to the same generic mismatch
without changing malformed input/config error precedence.

Run the named tests. Expected: FAIL until the public validator rematerializes through the shared private path and the builder fills both digests exactly.

- [ ] **Step 2: Implement the shared private materializer and non-recursive final checks**

Use one private function with this exact role:

```python
def _materialize_team_evidence_aggregation_result(
    aggregation_input: TeamEvidenceAggregationInput,
    *,
    config: TeamEvidenceAggregationConfig,
) -> TeamEvidenceAggregationResult:
    """Build the one canonical semantic result from exact input and config."""
```

The raw successful Node 2B witness return is checked in this exact order:

1. Bind `coverage = build_team_evidence_requirement_coverage(...)` without
   copying, sorting, or constructing a result.
2. Require
   `tuple(row.requirement_id for row in coverage) == tuple(requirement.requirement_id for requirement in config.requirements)`.
   Missing, extra, duplicate, reordered, and omitted zero-candidate IDs fail
   through exact
   `ValueError("materialized aggregation result violates canonical invariants")`.
   This inspects only the ID
   projection and does not repeat Node 2B coverage-field, matching, or witness
   semantics.
3. Only after that projection succeeds may `_derive_status_fields` consume the
   authoritative coverage tuple.
4. Only after status derivation and before constructing `TeamEvidenceAggregationResult`
   is the raw coverage tuple eligible to enter the result. The result dataclass
   canonicalizes coverage, so a post-construction projection is insufficient
   and cannot satisfy this boundary.

Therefore the projection runs before status derivation and before constructing `TeamEvidenceAggregationResult`.

The final construction sequence is exact:

1. After the raw witness-return projection passes, compute every remaining
   semantic field, diagnostic tuple, status, reason, and
   `config_digest=team_evidence_aggregation_config_digest(config)` while
   retaining the identical authoritative coverage tuple.
2. Instantiate a local provisional exact `TeamEvidenceAggregationResult` with `core_digest="0" * 64`.
3. Compute `core_digest=team_evidence_aggregation_core_digest(provisional)`. The core payload omits only `core_digest`, so the provisional zero digest cannot affect the preimage.
4. Create the final frozen result with `dataclasses.replace(provisional, core_digest=core_digest)`.
5. Run a private non-rematerializing invariant checker over exact facade counts,
   totals, status/reasons/publication relationships, config digest equality, and
   a defensive post-construction requirement-ID projection. That recheck cannot
   replace the mandatory raw pre-construction projection shown above. It may consume authoritative
   coverage for status but does not revalidate Node 2B coverage-field, witness,
   matching, allocation, or candidate-edge semantics. The checker does not call
   the codec validator.
6. Call `validate_team_evidence_aggregation_core_digest(final)` exactly once
   as the sibling final digest check.
7. Return the final result. The provisional object never escapes.

Public functions are thin and exact:

```python
def build_team_evidence_aggregation_result(
    aggregation_input: TeamEvidenceAggregationInput,
    *,
    config: TeamEvidenceAggregationConfig,
) -> TeamEvidenceAggregationResult:
    return _materialize_team_evidence_aggregation_result(
        aggregation_input,
        config=config,
    )


def validate_team_evidence_aggregation_result(
    result: TeamEvidenceAggregationResult,
    *,
    aggregation_input: TeamEvidenceAggregationInput,
    config: TeamEvidenceAggregationConfig,
) -> None:
    if type(result) is not TeamEvidenceAggregationResult:
        raise ValueError("result must be exactly TeamEvidenceAggregationResult")
    with localcontext(_ARITHMETIC_CONTEXT):
        try:
            validate_team_evidence_aggregation_core_digest(result)
        except (
            AttributeError,
            DecimalException,
            RecursionError,
            TypeError,
            UnicodeError,
            ValueError,
        ):
            raise ValueError(
                "aggregation result must equal rematerialized result",
            ) from None

        expected = _materialize_team_evidence_aggregation_result(
            aggregation_input,
            config=config,
        )
        try:
            _validate_materialized_result_invariants(
                result,
                config=config,
                expected_config_digest=expected.config_digest,
            )
            matches_expected = result == expected
        except (
            AttributeError,
            DecimalException,
            RecursionError,
            TypeError,
            UnicodeError,
            ValueError,
        ):
            raise ValueError(
                "aggregation result must equal rematerialized result",
            ) from None
    if not matches_expected:
        raise ValueError("aggregation result must equal rematerialized result")
    return None
```

The validator never calls the public builder, and the builder never calls the
public validator. Neither implements a second reduction algorithm. The exact
outer-type guard is first. The supplied codec call is next and recursively
rejects missing slots, wrong nested shape, noncanonical scalars/tuples, or an
invalid digest without calling supplied equality or other field callbacks. Its
narrow expected failures map immediately to the exact generic mismatch, and the
rematerializer is not called. Only codec success reaches exact dependency
rematerialization, which runs outside supplied-result failure mapping so malformed
`aggregation_input` or `config` values retain their stable predecessor errors.
After successful rematerialization, an invariant failure or unequal field maps
to the exact generic mismatch. Exact dataclass equality covers every nested
field and digest only after codec shape validation has succeeded.

The complete validator, including supplied codec recursion, rematerialization,
invariant checks, and equality, executes inside a local copy of
`_ARITHMETIC_CONTEXT`. It neither reads nor mutates ambient Decimal precision,
rounding, traps, or flags, and caller context is byte-for-byte unchanged on both
success and generic-mismatch paths.

- [ ] **Step 3: Run digest, validator, permutation, and full reducer tests**

```bash
.venv/bin/python -m pytest -q tests/test_team_evidence_aggregation.py
```

Expected: all tests pass; successful validation returns exact `None`; any semantic/config/core tampering fails closed; permutation and hostile-context results, canonical payloads, and digests are equal.

---

### Task 5: Add The Child-Local Unified Six-Module AST And Package-Root Guard

**Files:**
- Create: `tests/test_team_evidence_aggregation_scope.py`
- Verify only: all six Node 2 production modules, all seven Node 2 test modules, and `src/polymarket_alpha_lab/__init__.py`

**Interfaces:**
- Consumes: checked-in source text solely for AST and physical-line inspection.
- Produces: Node 2C's child-local unified import/export/forbidden-surface/size gate over the complete Node 2 implementation and package root.

- [ ] **Step 1: Write the exact production/test path and line-limit tables**

Use literal mappings with these entries:

```python
PRODUCTION_LINE_LIMITS = {
    "team_evidence_aggregation_types.py": 900,
    "team_evidence_aggregation_codec.py": 500,
    "team_evidence_aggregation_temporal.py": 300,
    "team_evidence_aggregation_allocation.py": 450,
    "team_evidence_aggregation_witness.py": 650,
    "team_evidence_aggregation.py": 700,
}
TEST_LINE_LIMITS = {
    "test_team_evidence_aggregation_types.py": 900,
    "test_team_evidence_aggregation_codec.py": 600,
    "test_team_evidence_aggregation_temporal.py": 450,
    "test_team_evidence_aggregation_allocation.py": 600,
    "test_team_evidence_aggregation_witness.py": 900,
    "test_team_evidence_aggregation.py": 900,
    "test_team_evidence_aggregation_scope.py": 500,
}
PRODUCTION_TOTAL_LINE_LIMIT = 3_500
TEST_TOTAL_LINE_LIMIT = 4_850
```

Count exactly with `len(path.read_text(encoding="utf-8").splitlines())`; comments and blank lines count. Assert every individual ceiling, production total `<= 3_500`, test total `<= 4_850`, and this scope file `<= 500`.

- [ ] **Step 2: Encode the exact normalized import allowlists**

Use this literal mapping:

```python
IMPORT_ALLOWLISTS = {
    "team_evidence_aggregation_types": {
        "__future__", "collections", "dataclasses", "datetime", "decimal", "re", "typing",
    },
    "team_evidence_aggregation_codec": {
        "__future__", "dataclasses", "datetime", "decimal", "hashlib", "json", "typing",
        "polymarket_alpha_lab.team_evidence_aggregation_types",
    },
    "team_evidence_aggregation_temporal": {
        "__future__", "datetime", "decimal", "typing",
        "polymarket_alpha_lab.team_evidence_aggregation_types",
    },
    "team_evidence_aggregation_allocation": {
        "__future__", "decimal", "typing",
        "polymarket_alpha_lab.team_evidence_aggregation_types",
    },
    "team_evidence_aggregation_witness": {
        "__future__", "collections", "datetime", "decimal", "typing",
        "polymarket_alpha_lab.team_evidence_aggregation_types",
        "polymarket_alpha_lab.team_evidence_aggregation_allocation",
    },
    "team_evidence_aggregation": {
        "__future__", "dataclasses", "decimal", "typing",
        "polymarket_alpha_lab.team_evidence_aggregation_types",
        "polymarket_alpha_lab.team_evidence_aggregation_codec",
        "polymarket_alpha_lab.team_evidence_aggregation_temporal",
        "polymarket_alpha_lab.team_evidence_aggregation_allocation",
        "polymarket_alpha_lab.team_evidence_aggregation_witness",
    },
}
```

Normalization is exact and module-only. Each `ast.Import` alias contributes
`alias.name`. Every `ast.ImportFrom` requires `level == 0` and a nonempty
`module`, then contributes that absolute `module`; imported member names and
local aliases do not change the normalized module. Reject every relative import
and every normalized module not in the consumer module's allowlist.
Independently reject wildcard syntax in every `ImportFrom`. The gate otherwise
enforces no second member-name or alias allowlist: it does not force sibling
modules to use `ImportFrom`, prohibit `asname`, or restrict an allowed module to
an exact imported-member set. A member is not rejected merely because its spelling begins with `_`;
this import-gate rule does not authorize Node 2C to
consume a predecessor private helper, which remains prohibited by the public-
interface boundary above. Imported members and local aliases remain subject to
the forbidden-name and forbidden-call scans specified below.

- [ ] **Step 3: Encode all six exact literal `__all__` tuples**

Use these exact tuples and order:

```python
PUBLIC_EXPORTS = {
    "team_evidence_aggregation_types": (
        "TeamEvidenceSourceLineage",
        "TeamEvidenceCapture",
        "TeamEvidenceRevision",
        "TeamEvidenceAssessmentRevision",
        "TeamEvidenceAggregationRecord",
        "TeamEvidenceCurrentRevisionSelection",
        "TeamEvidenceAggregationInput",
        "TeamEvidenceRequirement",
        "TeamEvidenceAggregationConfig",
        "TeamEvidenceTemporalAssessment",
        "TeamEvidenceWeightAllocation",
        "TeamEvidenceRequirementWitness",
        "TeamEvidenceRequirementCoverage",
        "TeamEvidenceDiagnosticRow",
        "TeamEvidenceContradictionResult",
        "TeamEvidenceAggregationResult",
        "validate_team_evidence_aggregation_input_contract",
        "select_team_evidence_canonical_current_records",
        "select_team_evidence_canonical_capture_records",
    ),
    "team_evidence_aggregation_codec": (
        "team_evidence_aggregation_config_payload",
        "team_evidence_aggregation_input_payload",
        "team_evidence_aggregation_config_digest",
        "team_evidence_aggregation_core_payload",
        "team_evidence_aggregation_payload",
        "team_evidence_aggregation_core_digest",
        "validate_team_evidence_aggregation_core_digest",
    ),
    "team_evidence_aggregation_temporal": (
        "assess_team_evidence_temporal",
    ),
    "team_evidence_aggregation_allocation": (
        "allocate_team_evidence_weights",
    ),
    "team_evidence_aggregation_witness": (
        "build_team_evidence_requirement_coverage",
    ),
    "team_evidence_aggregation": (
        "build_team_evidence_aggregation_result",
        "validate_team_evidence_aggregation_result",
    ),
}
```

AST assertions require one direct assignment to `__all__`, an `ast.Tuple` of
string constants, exact tuple equality including order, and no duplicates.
Every exported name must have exactly one definition among the direct children of
`ast.Module.body`, with its documented node kind: `ClassDef` for the sixteen
public types and `FunctionDef` for every public function.
No import, assignment, named-expression target, nested or async definition,
or other binding may satisfy or rebind an exported name; reject every missing, duplicate, rebound, or
wrong-kind export. Private graph, validation, apportionment, materialization,
and serialization helpers must remain absent from `__all__`.

The export-binding collector is deliberately fail-closed over all descendant AST
nodes and every string-valued binding field, rather than pruning whole function,
class, lambda, or comprehension subtrees. It includes `ast.Name` with either `Store` or `Del` context,
import names and aliases, function/class/argument names, named-expression and
comprehension targets, exception/with targets, every nested `ast.Global.names`
entry, `ast.MatchAs.name`, `ast.MatchStar.name`, and `ast.MatchMapping.rest`.
Import aliases that bind `__all__` are rebindings and must fail.
Nested local shadowing of an exported name remains fail-closed under the e31 contract,
even when Python lexical scope
would make that shadowing harmless. This conservative rule also ensures the
collector does not miss module-evaluated
decorators, defaults, annotations, class bases, class keywords, and named-expression targets
merely because they
are attached to a nested syntax node.

Calls to `globals`, `locals`, and `vars` are forbidden in every production
module so dynamic namespace dictionaries cannot assign, delete, update, or
replace an export or `__all__` outside the binding collector. The negative
matrix includes `del ExportedName`, `del __all__`,
`globals()["ExportedName"] = replacement`, deletion through the returned
namespace, and dictionary `update` for an exported-name key. At package root,
every nested `Global` declaration naming a Node 2 public export or `__all__`
fails even when it appears inside a function or class body. Class-body mutation
of a global `__all__` also fails. These checks do not treat `Nonlocal` as a
module binding.

- [ ] **Step 4: Write the unified AST, hard-maxima, and package-root tests**

Create these exact tests:

```text
test_node_2_unified_ast_import_export_forbidden_surface_and_line_size_gate
test_node_2_public_dataclasses_are_frozen_slotted_final_and_hard_flagged
test_node_2_config_policy_fields_have_no_defaults_and_hard_maxima_fail_closed
test_node_2_package_root_has_no_node_2_public_exports
test_node_2_has_no_outer_identity_packet_legacy_or_persistence_surface
```

The unified AST test must reject:

- unlisted and relative imports;
- DB, Supabase, PostgreSQL, SQL, migration, persistence, store, filesystem, JSONL, CSV, cache, temporary-file, network, HTTP, socket, browser, scraper, public-client, external API, CLI, environment, subprocess, process, or logging imports/references;
- auth, hosted-account, credential, token, private-key, wallet, signing, order, sizing, allocation-to-capital, execution, exchange mutation, and live-trading surfaces, using token-aware AST name/attribute checks so legitimate `correlation_group_weight_cap` does not fail;
- calls to `open`, `print`, `input`, `eval`, `exec`, `compile`, `__import__`, dynamic import, `datetime.now`, `datetime.utcnow`, `timedelta.total_seconds`, `datetime.timestamp`, randomness, or built-in `hash`;
- float literals, `float(...)`, and float annotations;
- broad `except Exception`, broad `except BaseException`, callback invocation from input, or object `repr` in payload/error construction;
- embedded `btc`, `bitcoin`, `0.020000`, or `0.980000` production constants;
- `tea:v1`, `tfr:v1`, `tfe:v1`, forecast-packet construction, legacy projection, decoder, persistence API, or outer replay/run/forecast/evidence identity.

Table-driven snippets exercising the six production-module import gates must
prove the module-only boundary directly. An allowlisted absolute module imported
with either `Import` or `ImportFrom` keeps the same normalized module when benign
imported-member names or local aliases change. Exact-prefix extensions, relative
forms, empty `ImportFrom.module` values, and wildcards fail. The exact normalized
module `polymarket_alpha_lab` also fails because it is absent from every
production-module allowlist. Benign member and alias variants include a leading-underscore member spelling
and do not create a second allowlist, while
forbidden semantic identifiers in those same AST positions still fail the scans
below. These assertions do not govern imports in test modules and are separate
from the package-root `__init__.py` assertion below, which verifies that the
documented Node 2 public names are not re-exported there.

Forbidden-name matching is lexical, not substring-based. Normalize identifier
values from `ast.Name.id`, each `ast.Attribute.attr`,
`ast.FunctionDef.name`, `ast.AsyncFunctionDef.name`, `ast.ClassDef.name`,
every `ast.arg.arg`, each non-`None` `ast.keyword.arg`, string-valued
`ast.ExceptHandler.name`, and every `ast.Global.names`/`ast.Nonlocal.names`
entry, plus non-`None` `ast.MatchAs.name`, `ast.MatchStar.name`,
`ast.MatchMapping.rest`, and every `ast.MatchClass.kwd_attrs` entry, into
snake-case and CamelCase components. The unified test also parses
table-driven synthetic snippets that place one forbidden identifier in every
one of those AST fields and requires the scanner to reject each snippet. Compare
whole components or an explicitly forbidden adjacent component sequence. The
capital-allocation prohibition matches only
an explicit `capital_allocation` or `allocation_to_capital` sequence;
standalone `allocation` remains valid evidence-aggregation terminology.
Normalized `ast.Import` and `ast.ImportFrom` module strings are governed only by
the exact import allowlist and must not be fed through the forbidden semantic
name scan after that check. For `ast.ImportFrom`, scan every `alias.name` member
and optional `alias.asname` separately as semantic identifiers; for
`ast.Import`, scan every optional `alias.asname` separately while retaining
`alias.name` as the allowlisted module string. Consequently the allowlisted
sibling modules
`polymarket_alpha_lab.team_evidence_aggregation_types` and
`polymarket_alpha_lab.team_evidence_aggregation_allocation`, together with
legitimate domain names such as `TeamEvidenceWeightAllocation` and
`allocate_team_evidence_weights`, must pass without a false forbidden-name
finding.

The ordinary lexical scan of `ast.Call` targets is qualifier-independent.
Table-driven failures include both
`import datetime as clock; clock.now()` and
`from datetime import datetime as clock; clock.utcnow()`, plus the same calls
through benign leading-underscore aliases. Terminal call components `now`,
`utcnow`, `timestamp`, and `total_seconds` are forbidden regardless of their
qualifier; this does not create a positive imported-member or alias allowlist.

Reflective attribute names are not a bypass. Builtin `setattr`, `delattr`, and
`hasattr` are forbidden in production; this does not prohibit the separately
governed `object.__setattr__` calls in frozen dataclass construction. For
`getattr`, scan a literal attribute-name argument through the same forbidden
semantic-component policy. Reject any `getattr` result used directly as
`ast.Call.func` or flowing through simple aliases to a called value, including
when its attribute name is assembled dynamically. Reject every new nonliteral
`getattr` terminal in the Node 2C facade. Frozen predecessor compatibility is
limited to an exact count-sensitive manifest of the reviewed baseline's `48`
dynamic getter calls in `23` distinct `(object, terminal, default)` AST forms.
The scope test pins those forms literally; any new or changed predecessor form requires predecessor
amendment and review, not a general dynamic-reflection exemption. The
table-driven negative matrix includes
`getattr(d.sys.modules["os"], "system")("true")`, isolated
`getattr(d, "system")("true")`, forbidden pattern captures including
`case {**wallet}`, `MatchClass.kwd_attrs`, and exported-name bindings through
`MatchMapping.rest`. It also includes an assembled nonliteral chain that resolves
to a forbidden process callable but is never executed by the test.
It also includes an import alias that rebinds `__all__`, and exported-name
named expressions in a module-level function default, decorator, and
comprehension. Each must fail without weakening the positive module-only import
and benign leading-underscore cases.

The v4 negative and positive fixtures must be consolidated within the existing
`test_team_evidence_aggregation_scope.py <= 500` ceiling. That ceiling may not
be raised to accommodate the added reflection, pattern, unbinding, or package-
global cases.

The dataclass test parses every exported public class in the types module and requires `@final`, `@dataclass(frozen=True, slots=True)`, exact hard-flag fields with literal `True` defaults, and explicit non-subclassability. The config-default test inspects `TeamEvidenceAggregationConfig` and requires no defaults on any policy field; then constructs values above each hard maximum and asserts `ValueError` for `33`, `129`, `33`, `1025`, and `257` respectively, while the exact maxima `32`, `128`, `32`, `1024`, and `256` remain structurally admissible when all other invariants hold. No implementation-max name may appear in any `__all__`.

The package-root test parses `src/polymarket_alpha_lab/__init__.py` and asserts that no name in the union of `PUBLIC_EXPORTS.values()` is imported, assigned, or listed in package-root `__all__`. It does not edit the package root.

- [ ] **Step 5: Run the child-local unified scope gate and fix only owned files**

```bash
.venv/bin/python -m pytest -q \
  tests/test_team_evidence_aggregation_scope.py::test_node_2_unified_ast_import_export_forbidden_surface_and_line_size_gate \
  tests/test_team_evidence_aggregation_scope.py::test_node_2_public_dataclasses_are_frozen_slotted_final_and_hard_flagged \
  tests/test_team_evidence_aggregation_scope.py::test_node_2_config_policy_fields_have_no_defaults_and_hard_maxima_fail_closed \
  tests/test_team_evidence_aggregation_scope.py::test_node_2_package_root_has_no_node_2_public_exports \
  tests/test_team_evidence_aggregation_scope.py::test_node_2_has_no_outer_identity_packet_legacy_or_persistence_surface
```

Expected: all five tests pass. If a predecessor module violates its reviewed child-local contract, stop and amend/re-review that predecessor. Node 2C may only fix its own reducer or scope-test files and may not conceal predecessor drift.

- [ ] **Step 6: Run the exact Node 2C focused command**

```bash
.venv/bin/python -m pytest -q \
  tests/test_team_evidence_aggregation.py \
  tests/test_team_evidence_aggregation_scope.py
```

Expected: both files pass; the run executes reducer behavior plus the final unified six-module/package-root gate, with `team_evidence_aggregation_scope.py <= 500` lines and all seven Node 2 tests `<= 4,850` lines total.

---

### Task 6: Gate, Commit, Review The Full Range, And Publish Without Force

**Files:** Exactly the three paths in `NODE_PATHS`; no others.

**Interfaces:**
- Consumes: immutable `NODE_BASE` equal to the hardened governance candidate, fixed import-governance parent `e31c3951b06f06e995c0c8f6f8fe2f22320a38da`, validated predecessor environment values/receipts, completed Node 2C files, and all quality-gate evidence.
- Produces: an exact allowlisted implementation commit range strictly after both governance-document commits, reviewed by local Claude Code, and a race-checked non-force update of remote `main`.

Steps 1 through 6 continue in the persistent Task 1 gate shell, so they use the
readonly helper defined there. A Step 7 review fix terminates that shell and
reruns all of Task 1 in a fresh shell; the fresh Task 1 block repeats the helper
definition and obtains a new pass before Steps 5 and 6 repeat. Each Step 8
`publish`, `recover`, or `complete` invocation is an independently started shell
and repeats the complete helper definition before its first Git command. No Task
6 block may import an exported function or reuse a Git-control result from a
prior shell.

- [ ] **Step 1: Run focused, compile, full, CodeGraph, and diff gates before staging**

```bash
set -euo pipefail
: "${NODE_BASE:?run Task 1 in this gate session first}"
assert_node2c_git_controls

.venv/bin/python -m pytest -q \
  tests/test_team_evidence_aggregation.py \
  tests/test_team_evidence_aggregation_scope.py
.venv/bin/python -m compileall -q src tests
.venv/bin/python -m pytest --collect-only -q
.venv/bin/python -m pytest -q
codegraph sync .
codegraph index -f .
assert_node2c_git_controls
git diff --check -- "${NODE_PATHS[@]}"
assert_node2c_git_controls
```

Expected: each command exits `0`; focused tests pass; compilation reports no syntax errors; collection succeeds; the full suite passes without live/network/account/wallet/order dependencies; a forced full CodeGraph index succeeds; file-level diff hygiene is clean.

- [ ] **Step 2: Stage the literal allowlist and prove exact staged equality**

```bash
assert_node2c_git_controls
git add -- "${NODE_PATHS[@]}"
assert_node2c_git_controls
if STAGED_NODE_PATHS_TEXT="$(git diff --cached --name-only)"; then
  STAGED_NODE_PATHS_STATUS=0
else
  STAGED_NODE_PATHS_STATUS=$?
fi
if [ "$STAGED_NODE_PATHS_STATUS" -ne 0 ]; then
  printf 'staged path diff failed with status %s\n' \
    "$STAGED_NODE_PATHS_STATUS" >&2
  exit "$STAGED_NODE_PATHS_STATUS"
fi
STAGED_NODE_PATHS_SORTED="$(
  LC_ALL=C sort <<< "$STAGED_NODE_PATHS_TEXT"
)"
test "$STAGED_NODE_PATHS_SORTED" = "$EXPECTED_NODE_PATHS"
STAGED_NODE_PATHS="$(git diff --cached --name-only)"
test "$STAGED_NODE_PATHS" = "$EXPECTED_NODE_PATHS"
git diff --cached --check
assert_node2c_git_controls
```

Expected: the staged path string equals the literal sorted allowlist byte for byte, both before and after sorting. No broad `git add` command is permitted.

- [ ] **Step 3: Run staged high-confidence secret and Phase 1 surface scans**

Run exactly this status-aware scan. The high-confidence scan is quiet and prints only an affected path, never a matched value:

```bash
set -euo pipefail
assert_node2c_git_controls
HIGH_CONFIDENCE_SECRET_PATTERN='(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|(^|[^[:alnum:]_])sk-[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}|postgres(ql)?://[^[:space:]/]+:[^[:space:]@]+@)'
SENSITIVE_FIELD_PATTERN='\b(api[_-]?key|secret|token|password|passwd|cookie|authorization|bearer|private[_ -]?key|seed phrase|mnemonic|wallet|account[_ -]?(id|address))\b'
READONLY_PATTERN='\b(live[_ -]?trading|order[_ -]?submission|submit[_ -]?order|cancel[_ -]?order|replace[_ -]?order|sign[_ -]?order|wallet|private[_ -]?key|hosted[_ -]?account|account[_ -]?authentication|exchange[_ -]?mutation|order[_ -]?mutation)\b'
PERSISTENCE_PATTERN='\b(sqlite|duckdb|redis|mongodb|sqlalchemy|jsonl|file[_ -]?backed|postgres|supabase|dsn|validate_local_postgres_dsn|migration|persistence|store)\b'

SENSITIVE_PATHS=()
READONLY_PATHS=()
PERSISTENCE_PATHS=()

for path in "${NODE_PATHS[@]}"; do
  ADDED_STAGED="$({
    git diff --cached --unified=0 -- "$path" |
      sed -n '/^+++ /d; /^+/s/^+//p'
  })"

  if rg -q "$HIGH_CONFIDENCE_SECRET_PATTERN" <<< "$ADDED_STAGED"; then
    RG_STATUS=0
  else
    RG_STATUS=$?
  fi
  case "$RG_STATUS" in
    0)
      printf '%s\n' "$path" >&2
      exit 1
      ;;
    1)
      ;;
    *)
      printf '%s\n' "$path" >&2
      exit "$RG_STATUS"
      ;;
  esac

  for scan_name in sensitive readonly persistence; do
    case "$scan_name" in
      sensitive) pattern="$SENSITIVE_FIELD_PATTERN" ;;
      readonly) pattern="$READONLY_PATTERN" ;;
      persistence) pattern="$PERSISTENCE_PATTERN" ;;
    esac
    if rg -qi "$pattern" <<< "$ADDED_STAGED"; then
      RG_STATUS=0
    else
      RG_STATUS=$?
    fi
    case "$RG_STATUS" in
      0)
        case "$scan_name" in
          sensitive) SENSITIVE_PATHS+=("$path") ;;
          readonly) READONLY_PATHS+=("$path") ;;
          persistence) PERSISTENCE_PATHS+=("$path") ;;
        esac
        ;;
      1)
        ;;
      *)
        printf '%s scan command failed for %s with rg status %s\n' "$scan_name" "$path" "$RG_STATUS" >&2
        exit "$RG_STATUS"
        ;;
    esac
  done
done

SENSITIVE_PATHS_TEXT="$(
  printf '%s\n' "${SENSITIVE_PATHS[@]}" | sed '/^$/d' | LC_ALL=C sort
)"
test "$SENSITIVE_PATHS_TEXT" = 'tests/test_team_evidence_aggregation_scope.py'
READONLY_PATHS_TEXT="$(
  printf '%s\n' "${READONLY_PATHS[@]}" | sed '/^$/d' | LC_ALL=C sort
)"
test "$READONLY_PATHS_TEXT" = 'tests/test_team_evidence_aggregation_scope.py'
PERSISTENCE_PATHS_TEXT="$(
  printf '%s\n' "${PERSISTENCE_PATHS[@]}" | sed '/^$/d' | LC_ALL=C sort
)"
test "$PERSISTENCE_PATHS_TEXT" = 'tests/test_team_evidence_aggregation_scope.py'
assert_node2c_git_controls
```

Exact `rg` semantics for every scan are mandatory: status `0` means a match and therefore either immediate failure (high-confidence secret) or explicit path classification (sensitive/readonly/persistence); status `1` means clean; any status greater than `1` is a command failure. The sole classified path is the AST scope test because it names forbidden surfaces only as negative assertions. A match in production or reducer behavior tests fails the exact classification equality. No unconditional success fallback may mask `rg`, `git diff`, or `sed` failure.

- [ ] **Step 4: Commit the complete initial implementation and prove the range manifest**

```bash
assert_node2c_git_controls
git commit -m "Add team evidence aggregation status facade"
assert_node2c_git_controls
NODE2C_GATE_COMMON_GIT_DIR="$(
  git rev-parse --path-format=absolute --git-common-dir
)"
NODE2C_GATE_HEAD="$(git rev-parse HEAD)"
readonly NODE2C_GATE_HEAD NODE2C_GATE_COMMON_GIT_DIR
test "$NODE_BASE" = "$NODE2C_EXPECTED_BASE"
test "$NODE_BASE" != "$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA"
NODE2C_GATE_BASE_PARENT="$(git show -s --format=%P "$NODE_BASE")"
test "$NODE2C_GATE_BASE_PARENT" = "$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA"
NODE2C_GATE_GOVERNANCE_CHAIN="$(
  git rev-list --reverse "$NODE2B_REVIEWED_SHA..$NODE_BASE"
)"
NODE2C_GATE_EXPECTED_GOVERNANCE_CHAIN="$(
  printf '%s\n' "$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA" "$NODE_BASE"
)"
test "$NODE2C_GATE_GOVERNANCE_CHAIN" = \
  "$NODE2C_GATE_EXPECTED_GOVERNANCE_CHAIN"
NODE2C_GATE_BASE_SUBJECT="$(git show -s --format=%s "$NODE_BASE")"
test "$NODE2C_GATE_BASE_SUBJECT" = \
  'docs: align Node 2C witness ownership governance'
NODE2C_GATE_GOVERNANCE_PATHS="$(
  git diff-tree --no-commit-id --name-only -r --no-renames "$NODE_BASE"
)"
test "$NODE2C_GATE_GOVERNANCE_PATHS" = \
  "$NODE2C_EXPECTED_GOVERNANCE_PATHS"
NODE2C_GATE_BASE_DESIGN_BLOB="$(
  git rev-parse "$NODE_BASE:$NODE2C_DESIGN_PATH"
)"
test "$NODE2C_GATE_BASE_DESIGN_BLOB" = \
  "$NODE2C_AMENDED_DESIGN_BLOB"
git merge-base --is-ancestor "$NODE_BASE" "$NODE2C_GATE_HEAD"
NODE2C_RANGE_COMMIT_COUNT="$(
  git rev-list --count "$NODE_BASE..$NODE2C_GATE_HEAD"
)"
test "$NODE2C_RANGE_COMMIT_COUNT" -ge 1
NODE2C_RANGE_MERGES="$(
  git rev-list --merges "$NODE_BASE..$NODE2C_GATE_HEAD"
)"
test -z "$NODE2C_RANGE_MERGES"
if NODE2C_RANGE_PATHS_TEXT="$(
  git diff --name-only "$NODE_BASE..$NODE2C_GATE_HEAD"
)"; then
  NODE2C_RANGE_PATHS_STATUS=0
else
  NODE2C_RANGE_PATHS_STATUS=$?
fi
if [ "$NODE2C_RANGE_PATHS_STATUS" -ne 0 ]; then
  printf 'committed-range path diff failed with status %s\n' \
    "$NODE2C_RANGE_PATHS_STATUS" >&2
  exit "$NODE2C_RANGE_PATHS_STATUS"
fi
NODE2C_RANGE_PATHS_SORTED="$(
  LC_ALL=C sort <<< "$NODE2C_RANGE_PATHS_TEXT"
)"
test "$NODE2C_RANGE_PATHS_SORTED" = "$EXPECTED_NODE_PATHS"
NODE2C_RANGE_PATHS="$(
  git diff --name-only "$NODE_BASE..$NODE2C_GATE_HEAD"
)"
test "$NODE2C_RANGE_PATHS" = "$EXPECTED_NODE_PATHS"
NODE2C_RANGE_GOVERNANCE_TOUCHES="$(
  git log --format=%H "$NODE_BASE..$NODE2C_GATE_HEAD" -- \
    "$NODE2C_PLAN_PATH" "$NODE2C_DESIGN_PATH"
)"
test -z "$NODE2C_RANGE_GOVERNANCE_TOUCHES"
git diff --check "$NODE_BASE..$NODE2C_GATE_HEAD"
git diff --cached --quiet
NODE2C_POST_COMMIT_TRACKED_STATUS="$(git status --porcelain --untracked-files=no)"
test -z "$NODE2C_POST_COMMIT_TRACKED_STATUS"
NODE2C_POST_COMMIT_OWNED_UNTRACKED="$(
  git ls-files --others --exclude-standard -- "${NODE_PATHS[@]}"
)"
test -z "$NODE2C_POST_COMMIT_OWNED_UNTRACKED"
assert_node2c_git_controls
```

Expected: `NODE_BASE` is the hardened two-document candidate whose sole parent
is the fixed plan-only import-governance commit, and the exact two-commit
governance-document chain above Node 2B ends at `NODE_BASE`. At least one
non-merge implementation commit
exists strictly above that base; neither governance document is touched anywhere
in `NODE_BASE..NODE2C_GATE_HEAD`; literal committed-range path equality passes in
sorted and native output; the index and tracked worktree are clean; no owned path
remains untracked.

- [ ] **Step 5: Re-gate the complete committed range**

Run all commands again against the committed state:

```bash
assert_node2c_git_controls
NODE2C_REGATE_START_HEAD="$(git rev-parse HEAD)"
test "$NODE2C_REGATE_START_HEAD" = "$NODE2C_GATE_HEAD"
.venv/bin/python -m pytest -q \
  tests/test_team_evidence_aggregation.py \
  tests/test_team_evidence_aggregation_scope.py
.venv/bin/python -m compileall -q src tests
.venv/bin/python -m pytest --collect-only -q
.venv/bin/python -m pytest -q
codegraph sync .
codegraph index -f .
assert_node2c_git_controls
NODE2C_REGATE_POST_TEST_HEAD="$(git rev-parse HEAD)"
test "$NODE2C_REGATE_POST_TEST_HEAD" = "$NODE2C_GATE_HEAD"
git diff --check "$NODE_BASE..$NODE2C_GATE_HEAD"
if NODE2C_REGATE_PATHS_TEXT="$(
  git diff --name-only "$NODE_BASE..$NODE2C_GATE_HEAD"
)"; then
  NODE2C_REGATE_PATHS_STATUS=0
else
  NODE2C_REGATE_PATHS_STATUS=$?
fi
if [ "$NODE2C_REGATE_PATHS_STATUS" -ne 0 ]; then
  printf 'regate path diff failed with status %s\n' \
    "$NODE2C_REGATE_PATHS_STATUS" >&2
  exit "$NODE2C_REGATE_PATHS_STATUS"
fi
NODE2C_REGATE_PATHS_SORTED="$(
  LC_ALL=C sort <<< "$NODE2C_REGATE_PATHS_TEXT"
)"
test "$NODE2C_REGATE_PATHS_SORTED" = "$EXPECTED_NODE_PATHS"
NODE2C_REGATE_PATHS="$(
  git diff --name-only "$NODE_BASE..$NODE2C_GATE_HEAD"
)"
test "$NODE2C_REGATE_PATHS" = "$EXPECTED_NODE_PATHS"
NODE2C_REGATE_GOVERNANCE_TOUCHES="$(
  git log --format=%H "$NODE_BASE..$NODE2C_GATE_HEAD" -- \
    "$NODE2C_PLAN_PATH" "$NODE2C_DESIGN_PATH"
)"
test -z "$NODE2C_REGATE_GOVERNANCE_TOUCHES"
git diff --cached --quiet
NODE2C_REGATE_TRACKED_STATUS="$(git status --porcelain --untracked-files=no)"
test -z "$NODE2C_REGATE_TRACKED_STATUS"

assert_node2c_git_controls
HISTORY_SECRET_PATTERN='(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|(^|[^[:alnum:]_])sk-[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}|postgres(ql)?://[^[:space:]/]+:[^[:space:]@]+@)'
NODE2C_HISTORY_COMMITS_TEXT="$(
  git rev-list --reverse "$NODE_BASE..$NODE2C_GATE_HEAD"
)"
test -n "$NODE2C_HISTORY_COMMITS_TEXT"
mapfile -t NODE2C_HISTORY_COMMITS <<< "$NODE2C_HISTORY_COMMITS_TEXT"
HISTORY_PATHS=()
NODE2C_REVIEW_FIX_SHAS=()
COMMIT_INDEX=0
for commit in "${NODE2C_HISTORY_COMMITS[@]}"; do
  COMMIT_INDEX=$((COMMIT_INDEX + 1))
  COMMIT_PARENT_TEXT="$(git rev-list --parents -n 1 "$commit")"
  read -r -a COMMIT_AND_PARENT <<< "$COMMIT_PARENT_TEXT"
  test "${#COMMIT_AND_PARENT[@]}" -eq 2
  test "${COMMIT_AND_PARENT[0]}" = "$commit"

  COMMIT_SUBJECT="$(git log -1 --format=%s "$commit")"
  if [ "$COMMIT_INDEX" -eq 1 ]; then
    test "$COMMIT_SUBJECT" = 'Add team evidence aggregation status facade'
  else
    test "$COMMIT_SUBJECT" = 'Fix Node 2C review findings'
    NODE2C_REVIEW_FIX_SHAS+=("$commit")
  fi

  if COMMIT_MESSAGE="$(git log -1 --format=%B "$commit")"; then
    COMMIT_MESSAGE_STATUS=0
  else
    COMMIT_MESSAGE_STATUS=$?
  fi
  if [ "$COMMIT_MESSAGE_STATUS" -ne 0 ]; then
    printf '%s\n' 'commit-message' >&2
    exit "$COMMIT_MESSAGE_STATUS"
  fi
  if rg -q "$HISTORY_SECRET_PATTERN" <<< "$COMMIT_MESSAGE"; then
    RG_STATUS=0
  else
    RG_STATUS=$?
  fi
  case "$RG_STATUS" in
    0) printf '%s\n' 'commit-message' >&2; exit 1 ;;
    1) ;;
    *) printf '%s\n' 'commit-message' >&2; exit "$RG_STATUS" ;;
  esac

  if COMMIT_PATHS_UNSORTED="$(
    git diff-tree --no-commit-id --name-only -r "$commit"
  )"; then
    COMMIT_PATHS_STATUS=0
  else
    COMMIT_PATHS_STATUS=$?
  fi
  if [ "$COMMIT_PATHS_STATUS" -ne 0 ]; then
    printf 'commit path diff failed for %s with status %s\n' \
      "$commit" "$COMMIT_PATHS_STATUS" >&2
    exit "$COMMIT_PATHS_STATUS"
  fi
  COMMIT_PATHS_TEXT="$(
    LC_ALL=C sort <<< "$COMMIT_PATHS_UNSORTED"
  )"
  test -n "$COMMIT_PATHS_TEXT"
  mapfile -t COMMIT_PATHS <<< "$COMMIT_PATHS_TEXT"
  for path in "${COMMIT_PATHS[@]}"; do
    case "$path" in
      src/polymarket_alpha_lab/team_evidence_aggregation.py | \
      tests/test_team_evidence_aggregation.py | \
      tests/test_team_evidence_aggregation_scope.py) ;;
      *) printf 'commit %s changes non-allowlisted path %s\n' "$commit" "$path" >&2; exit 1 ;;
    esac
    HISTORY_PATHS+=("$path")
    if COMMIT_PATCH_TEXT="$(
      git show --format= --no-ext-diff --no-textconv --unified=0 \
        "$commit" -- "$path"
    )"; then
      COMMIT_SHOW_STATUS=0
    else
      COMMIT_SHOW_STATUS=$?
    fi
    if [ "$COMMIT_SHOW_STATUS" -ne 0 ]; then
      printf '%s\n' "$path" >&2
      exit "$COMMIT_SHOW_STATUS"
    fi
    COMMIT_ADDED_LINES="$(
      sed -n '/^+++ /d; /^+/s/^+//p' <<< "$COMMIT_PATCH_TEXT"
    )"
    if rg -q "$HISTORY_SECRET_PATTERN" <<< "$COMMIT_ADDED_LINES"; then
      RG_STATUS=0
    else
      RG_STATUS=$?
    fi
    case "$RG_STATUS" in
      0) printf '%s\n' "$path" >&2; exit 1 ;;
      1) ;;
      *) printf '%s\n' "$path" >&2; exit "$RG_STATUS" ;;
    esac
  done
  if COMMIT_PATCH_TEXT="$(
    git show --format= --no-ext-diff --no-textconv --unified=0 "$commit"
  )"; then
    COMMIT_SHOW_STATUS=0
  else
    COMMIT_SHOW_STATUS=$?
  fi
  if [ "$COMMIT_SHOW_STATUS" -ne 0 ]; then
    printf 'commit patch read failed for %s with status %s\n' \
      "$commit" "$COMMIT_SHOW_STATUS" >&2
    exit "$COMMIT_SHOW_STATUS"
  fi
  COMMIT_ADDED_LINES="$(
    sed -n '/^+++ /d; /^+/s/^+//p' <<< "$COMMIT_PATCH_TEXT"
  )"
  COMMIT_MESSAGE="$(git log -1 --format=%B "$commit")"
  if rg -q "$HISTORY_SECRET_PATTERN" <<< "$COMMIT_MESSAGE"$'\n'"$COMMIT_ADDED_LINES"; then
    RG_STATUS=0
  else
    RG_STATUS=$?
  fi
  case "$RG_STATUS" in
    0) printf 'high-confidence credential shape in commit %s\n' "$commit" >&2; exit 1 ;;
    1) ;;
    *) printf 'history secret scan failed for commit %s with rg status %s\n' "$commit" "$RG_STATUS" >&2; exit "$RG_STATUS" ;;
  esac
done

NODE2C_HISTORY_POST_LOOP_HEAD="$(git rev-parse HEAD)"
test "$NODE2C_HISTORY_POST_LOOP_HEAD" = "$NODE2C_GATE_HEAD"
assert_node2c_git_controls

HISTORY_PATH_UNION="$(printf '%s\n' "${HISTORY_PATHS[@]}" | LC_ALL=C sort -u)"
test "$HISTORY_PATH_UNION" = "$EXPECTED_NODE_PATHS"
NODE2C_REVIEW_FIX_COUNT="${#NODE2C_REVIEW_FIX_SHAS[@]}"
test "$NODE2C_REVIEW_FIX_COUNT" -eq "$((${#NODE2C_HISTORY_COMMITS[@]} - 1))"
if [ "$NODE2C_REVIEW_FIX_COUNT" -eq 0 ]; then
  NODE2C_REVIEW_FIX_SHAS_TEXT=''
else
  if NODE2C_REVIEW_FIX_SHAS_TEXT="$(
    printf '%s\n' "${NODE2C_REVIEW_FIX_SHAS[@]}"
  )"; then
    NODE2C_REVIEW_FIX_TEXT_STATUS=0
  else
    NODE2C_REVIEW_FIX_TEXT_STATUS=$?
  fi
  if [ "$NODE2C_REVIEW_FIX_TEXT_STATUS" -ne 0 ]; then
    printf 'review-fix SHA formatting failed with status %s\n' \
      "$NODE2C_REVIEW_FIX_TEXT_STATUS" >&2
    exit "$NODE2C_REVIEW_FIX_TEXT_STATUS"
  fi
  if NODE2C_REVIEW_FIX_SHAS_FILTERED="$(
    sed '/^$/d' <<< "$NODE2C_REVIEW_FIX_SHAS_TEXT"
  )"; then
    NODE2C_REVIEW_FIX_FILTER_STATUS=0
  else
    NODE2C_REVIEW_FIX_FILTER_STATUS=$?
  fi
  if [ "$NODE2C_REVIEW_FIX_FILTER_STATUS" -ne 0 ]; then
    printf 'review-fix SHA filtering failed with status %s\n' \
      "$NODE2C_REVIEW_FIX_FILTER_STATUS" >&2
    exit "$NODE2C_REVIEW_FIX_FILTER_STATUS"
  fi
  if [ -z "$NODE2C_REVIEW_FIX_SHAS_FILTERED" ]; then
    NODE2C_REVIEW_FIX_TEXT_COUNT=0
  else
    NODE2C_REVIEW_FIX_TEXT_COUNT="$(
      wc -l <<< "$NODE2C_REVIEW_FIX_SHAS_FILTERED"
    )"
  fi
  test "$NODE2C_REVIEW_FIX_TEXT_COUNT" -eq "$NODE2C_REVIEW_FIX_COUNT"
fi
NODE2C_HISTORY_HEAD="$NODE2C_GATE_HEAD"
NODE2C_HISTORY_STATUS=pass
NODE2C_FOCUSED_TESTS_STATUS=pass
NODE2C_COMPILEALL_STATUS=pass
NODE2C_COLLECT_STATUS=pass
NODE2C_FULL_PYTEST_STATUS=pass
NODE2C_CODEGRAPH_SYNC_STATUS=pass
NODE2C_CODEGRAPH_FULL_INDEX_STATUS=pass
NODE2C_CLEAN_WORKTREE_STATUS=pass
export HISTORY_PATH_UNION NODE2C_REVIEW_FIX_COUNT NODE2C_REVIEW_FIX_SHAS_TEXT \
  NODE2C_HISTORY_HEAD NODE2C_HISTORY_STATUS NODE2C_FOCUSED_TESTS_STATUS \
  NODE2C_COMPILEALL_STATUS NODE2C_COLLECT_STATUS NODE2C_FULL_PYTEST_STATUS \
  NODE2C_CODEGRAPH_SYNC_STATUS NODE2C_CODEGRAPH_FULL_INDEX_STATUS \
  NODE2C_CLEAN_WORKTREE_STATUS
readonly HISTORY_PATH_UNION NODE2C_REVIEW_FIX_COUNT NODE2C_REVIEW_FIX_SHAS_TEXT \
  NODE2C_HISTORY_HEAD NODE2C_HISTORY_STATUS NODE2C_FOCUSED_TESTS_STATUS \
  NODE2C_COMPILEALL_STATUS NODE2C_COLLECT_STATUS NODE2C_FULL_PYTEST_STATUS \
  NODE2C_CODEGRAPH_SYNC_STATUS NODE2C_CODEGRAPH_FULL_INDEX_STATUS \
  NODE2C_CLEAN_WORKTREE_STATUS
```

Run the complete committed-range scan without referring to index state:

```bash
set -euo pipefail
: "${NODE2C_HISTORY_HEAD:?per-commit history-gate HEAD is required}"
: "${NODE2C_HISTORY_STATUS:?per-commit history status is required}"
test "$NODE2C_HISTORY_STATUS" = pass
assert_node2c_git_controls
NODE2C_RANGE_SCAN_HEAD="$(git rev-parse HEAD)"
test "$NODE2C_RANGE_SCAN_HEAD" = "$NODE2C_HISTORY_HEAD"
test "$NODE2C_RANGE_SCAN_HEAD" = "$NODE2C_GATE_HEAD"
HIGH_CONFIDENCE_SECRET_PATTERN='(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|(^|[^[:alnum:]_])sk-[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}|postgres(ql)?://[^[:space:]/]+:[^[:space:]@]+@)'
SENSITIVE_FIELD_PATTERN='\b(api[_-]?key|secret|token|password|passwd|cookie|authorization|bearer|private[_ -]?key|seed phrase|mnemonic|wallet|account[_ -]?(id|address))\b'
READONLY_PATTERN='\b(live[_ -]?trading|order[_ -]?submission|submit[_ -]?order|cancel[_ -]?order|replace[_ -]?order|sign[_ -]?order|wallet|private[_ -]?key|hosted[_ -]?account|account[_ -]?authentication|exchange[_ -]?mutation|order[_ -]?mutation)\b'
PERSISTENCE_PATTERN='\b(sqlite|duckdb|redis|mongodb|sqlalchemy|jsonl|file[_ -]?backed|postgres|supabase|dsn|validate_local_postgres_dsn|migration|persistence|store)\b'

SENSITIVE_RANGE_PATHS=()
READONLY_RANGE_PATHS=()
PERSISTENCE_RANGE_PATHS=()

for path in "${NODE_PATHS[@]}"; do
  ADDED_RANGE="$({
    git diff --unified=0 "$NODE_BASE..$NODE2C_HISTORY_HEAD" -- "$path" |
      sed -n '/^+++ /d; /^+/s/^+//p'
  })"

  if rg -q "$HIGH_CONFIDENCE_SECRET_PATTERN" <<< "$ADDED_RANGE"; then
    RG_STATUS=0
  else
    RG_STATUS=$?
  fi
  case "$RG_STATUS" in
    0)
      printf '%s\n' "$path" >&2
      exit 1
      ;;
    1)
      ;;
    *)
      printf '%s\n' "$path" >&2
      exit "$RG_STATUS"
      ;;
  esac

  for scan_name in sensitive readonly persistence; do
    case "$scan_name" in
      sensitive) pattern="$SENSITIVE_FIELD_PATTERN" ;;
      readonly) pattern="$READONLY_PATTERN" ;;
      persistence) pattern="$PERSISTENCE_PATTERN" ;;
    esac
    if rg -qi "$pattern" <<< "$ADDED_RANGE"; then
      RG_STATUS=0
    else
      RG_STATUS=$?
    fi
    case "$RG_STATUS" in
      0)
        case "$scan_name" in
          sensitive) SENSITIVE_RANGE_PATHS+=("$path") ;;
          readonly) READONLY_RANGE_PATHS+=("$path") ;;
          persistence) PERSISTENCE_RANGE_PATHS+=("$path") ;;
        esac
        ;;
      1)
        ;;
      *)
        printf '%s range scan command failed for %s with rg status %s\n' "$scan_name" "$path" "$RG_STATUS" >&2
        exit "$RG_STATUS"
        ;;
    esac
  done
done

SENSITIVE_RANGE_PATHS_TEXT="$(
  printf '%s\n' "${SENSITIVE_RANGE_PATHS[@]}" | sed '/^$/d' | LC_ALL=C sort
)"
test "$SENSITIVE_RANGE_PATHS_TEXT" = \
  'tests/test_team_evidence_aggregation_scope.py'
READONLY_RANGE_PATHS_TEXT="$(
  printf '%s\n' "${READONLY_RANGE_PATHS[@]}" | sed '/^$/d' | LC_ALL=C sort
)"
test "$READONLY_RANGE_PATHS_TEXT" = \
  'tests/test_team_evidence_aggregation_scope.py'
PERSISTENCE_RANGE_PATHS_TEXT="$(
  printf '%s\n' "${PERSISTENCE_RANGE_PATHS[@]}" | sed '/^$/d' | LC_ALL=C sort
)"
test "$PERSISTENCE_RANGE_PATHS_TEXT" = \
  'tests/test_team_evidence_aggregation_scope.py'

git diff --check "$NODE_BASE..$NODE2C_HISTORY_HEAD"
git diff --quiet
git diff --cached --quiet
NODE2C_RANGE_TRACKED_STATUS="$(git status --porcelain --untracked-files=no)"
test -z "$NODE2C_RANGE_TRACKED_STATUS"

assert_node2c_git_controls
NODE2C_RANGE_SCAN_FINAL_HEAD="$(git rev-parse HEAD)"
test "$NODE2C_RANGE_SCAN_FINAL_HEAD" = "$NODE2C_GATE_HEAD"
assert_node2c_git_controls
GATED_HEAD="$NODE2C_GATE_HEAD"
test "$GATED_HEAD" = "$NODE2C_HISTORY_HEAD"
SENSITIVE_RANGE_PATHS_TEXT="$(printf '%s\n' "${SENSITIVE_RANGE_PATHS[@]}" | sed '/^$/d' | LC_ALL=C sort)"
READONLY_RANGE_PATHS_TEXT="$(printf '%s\n' "${READONLY_RANGE_PATHS[@]}" | sed '/^$/d' | LC_ALL=C sort)"
PERSISTENCE_RANGE_PATHS_TEXT="$(printf '%s\n' "${PERSISTENCE_RANGE_PATHS[@]}" | sed '/^$/d' | LC_ALL=C sort)"
NODE2C_RANGE_SCAN_STATUS=pass
NODE2C_GATE_EVIDENCE="$(
  printf '%s\n' \
    "gated_head=$GATED_HEAD" \
    "history_gate=$NODE2C_HISTORY_STATUS" \
    "focused_tests=$NODE2C_FOCUSED_TESTS_STATUS" \
    "compileall=$NODE2C_COMPILEALL_STATUS" \
    "collect_only=$NODE2C_COLLECT_STATUS" \
    "full_pytest=$NODE2C_FULL_PYTEST_STATUS" \
    "codegraph_sync=$NODE2C_CODEGRAPH_SYNC_STATUS" \
    "codegraph_full_index=$NODE2C_CODEGRAPH_FULL_INDEX_STATUS" \
    "clean_worktree=$NODE2C_CLEAN_WORKTREE_STATUS" \
    "range_scan=$NODE2C_RANGE_SCAN_STATUS" \
    'head_stable=pass' \
    'replacement_refs=absent' \
    'grafts=absent' \
    'shallow_repository=false' \
    "review_fix_count=$NODE2C_REVIEW_FIX_COUNT" \
    'review_fix_shas_begin' \
    "$NODE2C_REVIEW_FIX_SHAS_TEXT" \
    'review_fix_shas_end' \
    'history_path_union_begin' \
    "$HISTORY_PATH_UNION" \
    'history_path_union_end' \
    'sensitive_paths_begin' \
    "$SENSITIVE_RANGE_PATHS_TEXT" \
    'sensitive_paths_end' \
    'readonly_paths_begin' \
    "$READONLY_RANGE_PATHS_TEXT" \
    'readonly_paths_end' \
    'persistence_paths_begin' \
    "$PERSISTENCE_RANGE_PATHS_TEXT" \
    'persistence_paths_end'
)"
export GATED_HEAD NODE2C_RANGE_SCAN_STATUS NODE2C_GATE_EVIDENCE
readonly GATED_HEAD NODE2C_RANGE_SCAN_STATUS NODE2C_GATE_EVIDENCE
```

Expected: focused/full/static gates all exit `0`; CodeGraph receives a forced full index; range hygiene and exact manifest pass; the first range commit has the exact initial subject and every later commit has the exact review-fix subject; the zero-or-more review-fix SHAs are preserved in oldest-first order with an exact count; high-confidence secret scan is clean without printing matched values; the three broader scans classify only the negative scope-test path. As in the staged scan, `rg` status `0` is a match to classify or fail, `1` is clean, and every status greater than `1` is a command failure.

- [ ] **Step 6: Obtain the mandatory local Claude Code full-range PASS**

Run this exact local command. It has no fallback model, no write-capable tool,
no session persistence, and no fast mode. The report parser accepts a nonempty
regular stream file strictly below `16,777,216` bytes and an extracted report of at
most `1,048,576` UTF-8 bytes. It opens inputs and exclusive outputs with
`O_NOFOLLOW`, uses literal LF JSONL framing, requires every record to be an
object with a string `type`, rejects duplicate keys, non-standard JSON
constants, malformed UTF-8, NUL, surrogates, and every C0/C1 control except HT
and LF, and never places report bytes in a Bash variable.

For the actual Claude `stream-json` envelope, the final completed
`stream_event` assistant message must contain exactly one report-bearing
top-level `assistant.message` record and end immediately before exactly one final
successful `result`; concatenated `text_delta`, assistant text, and
`result.result` UTF-8 bytes must agree exactly. A result-only stream remains a
strict fallback, but it must contain exactly one final successful result. The
last LF-delimited line containing a byte other than ASCII space or HT must be
exactly `VERDICT: PASS` or `VERDICT: REVISE`. The parser exclusively writes the
exact report bytes and a SHA-256 sidecar. A separate descriptor-bound read
revalidates that byte/hash binding before classification. Parser diagnostics are
appended to the private stderr artifact. Neither those diagnostics nor the raw
Claude stream, report, or stderr are replayed to a terminal. A nonzero reviewer
exit always classifies as an error even if parsing produced a valid verdict.

On the PASS branch, create the retained review handoff before removing the
review worktree and parser directory. The handoff is an independent private
`0700` directory with a closed file set. It contains byte-for-byte copies of
the report, stream, and stderr plus their validator-created sidecars, the
descriptor-validated 19-key governance publication and its sidecar, the
candidate-bound post-implementation evidence, and the v6 checkpoint manifest
and sidecar. Raw review bytes are retained for integrity validation even though
they may contain secrets; this step makes no claim that they are secret-free and
never scans or prints them. The package is not project-data persistence, a
Node 2 child receipt, or a Node 3 attestation.

The v6 validator path, governance-publication path, and post-implementation
evidence path are explicit absolute no-follow inputs. Review artifact digests
are recomputed from the retained bytes after copying; caller-provided review
digest scalars are not a trust root. On success, export readonly absolute paths
and recomputed digests for the package directory, each raw artifact, and the
v6 checkpoint manifest. A failure before the package is marked retained removes
only the identity-checked private handoff directory; successful temporary
review cleanup never traverses into the retained directory.

```bash
set -euo pipefail
umask 077
: "${GATED_HEAD:?complete committed-range GATED_HEAD is required}"
: "${NODE2C_GATE_EVIDENCE:?complete committed-range gate evidence is required}"
: "${NODE2C_HISTORY_STATUS:?per-commit history status is required}"
: "${NODE2C_FOCUSED_TESTS_STATUS:?focused-test status is required}"
: "${NODE2C_COMPILEALL_STATUS:?compileall status is required}"
: "${NODE2C_COLLECT_STATUS:?collect-only status is required}"
: "${NODE2C_FULL_PYTEST_STATUS:?full-pytest status is required}"
: "${NODE2C_CODEGRAPH_SYNC_STATUS:?CodeGraph sync status is required}"
: "${NODE2C_CODEGRAPH_FULL_INDEX_STATUS:?CodeGraph full-index status is required}"
: "${NODE2C_CLEAN_WORKTREE_STATUS:?clean-worktree status is required}"
: "${NODE2C_REVIEW_FIX_COUNT:?review-fix count is required}"
: "${NODE2C_REVIEWED_PLAN_BLOB:?reviewed plan blob is required}"
: "${NODE2C_REVIEWED_DESIGN_BLOB:?reviewed design blob is required}"
: "${NODE2C_IMPORT_GOVERNANCE_PARENT_SHA:?fixed import-governance parent is required}"
test -n "${NODE2C_REVIEW_FIX_SHAS_TEXT+x}"
test "$NODE2C_HISTORY_STATUS" = pass
test "$NODE2C_FOCUSED_TESTS_STATUS" = pass
test "$NODE2C_COMPILEALL_STATUS" = pass
test "$NODE2C_COLLECT_STATUS" = pass
test "$NODE2C_FULL_PYTEST_STATUS" = pass
test "$NODE2C_CODEGRAPH_SYNC_STATUS" = pass
test "$NODE2C_CODEGRAPH_FULL_INDEX_STATUS" = pass
test "$NODE2C_CLEAN_WORKTREE_STATUS" = pass
test "$NODE2C_REVIEW_FIX_COUNT" -ge 0
assert_node2c_git_controls
test "$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA" = \
  e31c3951b06f06e995c0c8f6f8fe2f22320a38da
REVIEW_IMPORT_PARENT_PARENT="$(
  git show -s --format=%P "$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA"
)"
test "$REVIEW_IMPORT_PARENT_PARENT" = "$NODE2B_REVIEWED_SHA"
REVIEW_BASE_PARENT="$(git show -s --format=%P "$NODE_BASE")"
test "$REVIEW_BASE_PARENT" = "$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA"
REVIEW_PLAN_BLOB_AT_BASE="$(git rev-parse "$NODE_BASE:$NODE2C_PLAN_PATH")"
test "$REVIEW_PLAN_BLOB_AT_BASE" = "$NODE2C_REVIEWED_PLAN_BLOB"
REVIEW_DESIGN_BLOB_AT_BASE="$(git rev-parse "$NODE_BASE:$NODE2C_DESIGN_PATH")"
test "$REVIEW_DESIGN_BLOB_AT_BASE" = "$NODE2C_REVIEWED_DESIGN_BLOB"
test "$REVIEW_DESIGN_BLOB_AT_BASE" = "$NODE2C_AMENDED_DESIGN_BLOB"
REVIEW_GOVERNANCE_TOUCHES="$(
  git log --format=%H "$NODE_BASE..$GATED_HEAD" -- \
    "$NODE2C_PLAN_PATH" "$NODE2C_DESIGN_PATH"
)"
test -z "$REVIEW_GOVERNANCE_TOUCHES"
test -z "${NODE2C_ACCEPTED_REVIEW_HEAD+x}"
command -v claude >/dev/null
command -v codegraph >/dev/null
command -v env >/dev/null
command -v sha256sum >/dev/null
command -v stat >/dev/null
command -v timeout >/dev/null
test -x /usr/bin/python3

NODE2A_RECEIPT_EVIDENCE="$(
  validate_predecessor_pass_receipt \
    NODE2A_RECEIPT_EVIDENCE \
    team-evidence-aggregation-contracts-codec-temporal-eligibility \
    "$NODE2A_PREREQ_SHA" \
    "$NODE2A_PASS_RECEIPT_PATH" \
    "$NODE2A_PASS_RECEIPT_SHA256" \
    node2a-13
)"
NODE2B_RECEIPT_EVIDENCE="$(
  validate_predecessor_pass_receipt \
    NODE2B_RECEIPT_EVIDENCE \
    team-evidence-aggregation-independence-correlation-requirement-witness \
    "$NODE2B_PREREQ_SHA" \
    "$NODE2B_PASS_RECEIPT_PATH" \
    "$NODE2B_PASS_RECEIPT_SHA256" \
    node2b-15
)"
GOVERNANCE_CANDIDATE_PUBLICATION_OUTPUT_CURRENT="$(
  validate_governance_candidate_publication
)"
test "$NODE2A_RECEIPT_EVIDENCE" = "$INITIAL_NODE2A_RECEIPT_EVIDENCE"
test "$NODE2B_RECEIPT_EVIDENCE" = "$INITIAL_NODE2B_RECEIPT_EVIDENCE"
test "$GOVERNANCE_CANDIDATE_PUBLICATION_OUTPUT_CURRENT" = \
  "$GOVERNANCE_CANDIDATE_PUBLICATION_OUTPUT"

REVIEW_HEAD="$GATED_HEAD"
REVIEW_FOUNDATION_PATH=docs/superpowers/plans/2026-07-13-btc-domain-evidence-aggregation-foundation.md
REVIEW_FOUNDATION_SHA256=af91080df318fb322a2bc387a800d50757963c221262f286facdd145fbbe5200
REVIEW_FOUNDATION_BLOB=f0ae5a3d73023f3d6f972d467669adc628c3f06a
REVIEW_COORDINATOR_HEAD="$(git rev-parse HEAD)"
test "$REVIEW_COORDINATOR_HEAD" = "$REVIEW_HEAD"
test "$(git rev-parse "$REVIEW_HEAD:$REVIEW_FOUNDATION_PATH")" = \
  "$REVIEW_FOUNDATION_BLOB"
REVIEW_RANGE_PATHS_SORTED="$(
  git diff --name-only "$NODE_BASE..$REVIEW_HEAD" | LC_ALL=C sort
)"
test "$REVIEW_RANGE_PATHS_SORTED" = "$EXPECTED_NODE_PATHS"
git diff --quiet
git diff --cached --quiet
REVIEW_COORDINATOR_STATUS="$(git status --porcelain --untracked-files=no)"
test -z "$REVIEW_COORDINATOR_STATUS"

REVIEW_RAW_FILE_LIMIT_BYTES=16777216
REVIEW_RAW_FILE_LIMIT_KIB=16384
REVIEW_REPORT_FILE_LIMIT_BYTES=1048576
readonly REVIEW_RAW_FILE_LIMIT_BYTES REVIEW_RAW_FILE_LIMIT_KIB \
  REVIEW_REPORT_FILE_LIMIT_BYTES
REVIEW_TMP_DIR="$(mktemp -d /home/ubuntu/test-sandbox/tmp/node2c-claude-review.XXXXXX)"
REVIEW_TMP_DIR_MODE="$(stat -c '%a' -- "$REVIEW_TMP_DIR")"
test "$REVIEW_TMP_DIR_MODE" = 700
readonly REVIEW_HEAD REVIEW_FOUNDATION_PATH REVIEW_FOUNDATION_SHA256 \
  REVIEW_FOUNDATION_BLOB REVIEW_TMP_DIR
REVIEW_PROMPT_PATH="$REVIEW_TMP_DIR/prompt.txt"
REVIEW_STREAM_PATH="$REVIEW_TMP_DIR/stream.jsonl"
REVIEW_STDERR_PATH="$REVIEW_TMP_DIR/stderr.txt"
REVIEW_REPORT_PATH="$REVIEW_TMP_DIR/report.md"
REVIEW_REPORT_SHA256_PATH="$REVIEW_TMP_DIR/report.md.sha256"
REVIEW_CODEGRAPH_PATH="$REVIEW_TMP_DIR/codegraph.txt"
REVIEW_SNAPSHOT_DIR="$REVIEW_TMP_DIR/review-worktree"
REVIEW_CODEGRAPH_DIR="$REVIEW_TMP_DIR/codegraph-worktree"
REVIEW_CODEGRAPH_EXPLORE_PATH="$REVIEW_TMP_DIR/codegraph-explore.txt"
REVIEW_CODEGRAPH_PRODUCTION_PATH="$REVIEW_TMP_DIR/codegraph-production.txt"
REVIEW_CODEGRAPH_TEST_PATH="$REVIEW_TMP_DIR/codegraph-test.txt"
REVIEW_CODEGRAPH_SCOPE_PATH="$REVIEW_TMP_DIR/codegraph-scope.txt"
readonly REVIEW_PROMPT_PATH REVIEW_STREAM_PATH REVIEW_STDERR_PATH \
  REVIEW_REPORT_PATH REVIEW_REPORT_SHA256_PATH REVIEW_CODEGRAPH_PATH \
  REVIEW_SNAPSHOT_DIR \
  REVIEW_CODEGRAPH_DIR REVIEW_CODEGRAPH_EXPLORE_PATH \
  REVIEW_CODEGRAPH_PRODUCTION_PATH REVIEW_CODEGRAPH_TEST_PATH \
  REVIEW_CODEGRAPH_SCOPE_PATH
for review_raw_path in \
  "$REVIEW_STREAM_PATH" \
  "$REVIEW_STDERR_PATH"; do
  : > "$review_raw_path"
  chmod 0600 "$review_raw_path"
  review_raw_mode="$(stat -c '%a' -- "$review_raw_path")"
  test "$review_raw_mode" = 600
done

NODE2C_REVIEW_PACKAGE_RETAINED=false
NODE2C_REVIEW_PACKAGE_SEALED=false
NODE2C_REVIEW_HANDOFF_DIR="$(mktemp -d /home/ubuntu/test-sandbox/tmp/node2c-review-handoff.XXXXXX)"
chmod 0700 -- "$NODE2C_REVIEW_HANDOFF_DIR"
test "$(stat -c '%a' -- "$NODE2C_REVIEW_HANDOFF_DIR")" = 700
NODE2C_REVIEW_PACKAGE_DIR="$NODE2C_REVIEW_HANDOFF_DIR/checkpoint"
mkdir -- "$NODE2C_REVIEW_PACKAGE_DIR"
chmod 0700 -- "$NODE2C_REVIEW_PACKAGE_DIR"
test "$(stat -c '%a' -- "$NODE2C_REVIEW_PACKAGE_DIR")" = 700
NODE2C_REVIEW_PACKAGE_REPORT_PATH="$NODE2C_REVIEW_PACKAGE_DIR/review-report.md"
NODE2C_REVIEW_PACKAGE_STREAM_PATH="$NODE2C_REVIEW_PACKAGE_DIR/review-stream.jsonl"
NODE2C_REVIEW_PACKAGE_STDERR_PATH="$NODE2C_REVIEW_PACKAGE_DIR/reviewer-stderr.txt"
NODE2C_ACCEPTED_REVIEW_OUTPUT_DIR="$NODE2C_REVIEW_PACKAGE_DIR"
NODE2C_ACCEPTED_REVIEW_MANIFEST_PATH="$NODE2C_REVIEW_PACKAGE_DIR/node2c-governance-accepted-review-checkpoint.json"
NODE2C_ACCEPTED_REVIEW_MANIFEST_SHA256=
NODE2C_REVIEW_PACKAGE_REPORT_SHA256=
NODE2C_REVIEW_PACKAGE_STREAM_SHA256=
NODE2C_REVIEW_PACKAGE_STDERR_SHA256=
NODE2C_REVIEW_PACKAGE_IDENTITY="$(stat -c '%d:%i' -- "$NODE2C_REVIEW_HANDOFF_DIR")"
readonly NODE2C_REVIEW_HANDOFF_DIR NODE2C_REVIEW_PACKAGE_DIR \
  NODE2C_REVIEW_PACKAGE_REPORT_PATH NODE2C_REVIEW_PACKAGE_STREAM_PATH \
  NODE2C_REVIEW_PACKAGE_STDERR_PATH NODE2C_ACCEPTED_REVIEW_OUTPUT_DIR \
  NODE2C_ACCEPTED_REVIEW_MANIFEST_PATH NODE2C_REVIEW_PACKAGE_IDENTITY
readonly NODE2C_REVIEW_PACKAGE_DIR

retain_node2c_review_package() {
  : "${NODE2C_ACCEPTED_REVIEW_MANIFEST_BIN:?v6 manifest validator path is required}"
  : "${NODE2C_GOVERNANCE_CANDIDATE_PUBLICATION_PATH:?governance publication path is required}"
  : "${NODE2C_GOVERNANCE_CANDIDATE_PUBLICATION_SHA256:?governance publication digest is required}"
  : "${NODE2C_POST_IMPLEMENTATION_EVIDENCE_PATH:?post-implementation evidence path is required}"
  for review_handoff_input in \
    "$NODE2C_ACCEPTED_REVIEW_MANIFEST_BIN" \
    "$NODE2C_GOVERNANCE_CANDIDATE_PUBLICATION_PATH" \
    "$NODE2C_POST_IMPLEMENTATION_EVIDENCE_PATH"; do
    case "$review_handoff_input" in
      /*) ;;
      *) printf 'review handoff path must be absolute\n' >&2; return 64 ;;
    esac
    [ -f "$review_handoff_input" ] && [ ! -L "$review_handoff_input" ] || return 64
  done

  REVIEW_HANDOFF_REPORT_SOURCE="$REVIEW_REPORT_PATH" \
  REVIEW_HANDOFF_STREAM_SOURCE="$REVIEW_STREAM_PATH" \
  REVIEW_HANDOFF_STDERR_SOURCE="$REVIEW_STDERR_PATH" \
  REVIEW_HANDOFF_GOVERNANCE_SOURCE="$NODE2C_GOVERNANCE_CANDIDATE_PUBLICATION_PATH" \
  REVIEW_HANDOFF_EVIDENCE_SOURCE="$NODE2C_POST_IMPLEMENTATION_EVIDENCE_PATH" \
  REVIEW_HANDOFF_PACKAGE_DIR="$NODE2C_REVIEW_PACKAGE_DIR" \
    /usr/bin/python3 - <<'PY'
import hashlib
import os
import stat


def read_private(path, maximum, *, allow_empty=False):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or before.st_uid != os.geteuid()
            or stat.S_IMODE(before.st_mode) != 0o600
            or before.st_size < (0 if allow_empty else 1)
            or before.st_size > maximum
        ):
            raise SystemExit("review handoff input metadata is invalid")
        source = os.read(descriptor, before.st_size + 1)
        after = os.fstat(descriptor)
        if len(source) != before.st_size or (after.st_dev, after.st_ino, after.st_size) != (
            before.st_dev, before.st_ino, before.st_size
        ):
            raise SystemExit("review handoff input changed while reading")
        return source
    finally:
        os.close(descriptor)


def write_private(directory, basename, source):
    descriptor = os.open(
        basename,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
        0o600,
        dir_fd=directory,
    )
    try:
        os.fchmod(descriptor, 0o600)
        offset = 0
        while offset < len(source):
            written = os.write(descriptor, source[offset:])
            if written <= 0:
                raise SystemExit("review handoff short write")
            offset += written
        os.fsync(descriptor)
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or metadata.st_uid != os.geteuid()
            or stat.S_IMODE(metadata.st_mode) != 0o600
            or metadata.st_size != len(source)
        ):
            raise SystemExit("review handoff output metadata is invalid")
    finally:
        os.close(descriptor)


directory = os.open(
    os.environ["REVIEW_HANDOFF_PACKAGE_DIR"],
    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
)
try:
    metadata = os.fstat(directory)
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != os.geteuid()
        or stat.S_IMODE(metadata.st_mode) != 0o700
        or metadata.st_nlink != 2
    ):
        raise SystemExit("review handoff package directory metadata is invalid")
    sources = (
        (os.environ["REVIEW_HANDOFF_REPORT_SOURCE"], "review-report.md", 1_048_576),
        (os.environ["REVIEW_HANDOFF_STREAM_SOURCE"], "review-stream.jsonl", 16_777_215),
        (
            os.environ["REVIEW_HANDOFF_GOVERNANCE_SOURCE"],
            "governance-candidate-publication.json",
            65_536,
        ),
        (
            os.environ["REVIEW_HANDOFF_EVIDENCE_SOURCE"],
            "producer-checks-evidence.json",
            65_536,
        ),
    )
    for source_path, basename, maximum in sources:
        write_private(directory, basename, read_private(source_path, maximum))
    write_private(
        directory,
        "reviewer-stderr.txt",
        read_private(
            os.environ["REVIEW_HANDOFF_STDERR_SOURCE"],
            16_777_215,
            allow_empty=True,
        ),
    )
    governance = read_private(
        os.environ["REVIEW_HANDOFF_GOVERNANCE_SOURCE"],
        65_536,
    )
    write_private(
        directory,
        "governance-candidate-publication.sha256",
        (hashlib.sha256(governance).hexdigest() + "\n").encode("ascii"),
    )
    os.fsync(directory)
finally:
    os.close(directory)
PY

  NODE2C_REVIEW_PACKAGE_REPORT_SHA256="$(sha256sum -- "$NODE2C_REVIEW_PACKAGE_REPORT_PATH" | awk '{print $1}')"
  NODE2C_REVIEW_PACKAGE_STREAM_SHA256="$(sha256sum -- "$NODE2C_REVIEW_PACKAGE_STREAM_PATH" | awk '{print $1}')"
  NODE2C_REVIEW_PACKAGE_STDERR_SHA256="$(sha256sum -- "$NODE2C_REVIEW_PACKAGE_STDERR_PATH" | awk '{print $1}')"
  [[ "$NODE2C_REVIEW_PACKAGE_REPORT_SHA256" =~ ^[0-9a-f]{64}$ ]]
  [[ "$NODE2C_REVIEW_PACKAGE_STREAM_SHA256" =~ ^[0-9a-f]{64}$ ]]
  [[ "$NODE2C_REVIEW_PACKAGE_STDERR_SHA256" =~ ^[0-9a-f]{64}$ ]]
  NODE2C_POST_IMPLEMENTATION_EVIDENCE_SHA256="$(
    sha256sum -- "$NODE2C_REVIEW_PACKAGE_DIR/producer-checks-evidence.json" | awk '{print $1}'
  )"
  NODE2C_RETAINED_GOVERNANCE_SHA256="$(
    sha256sum -- "$NODE2C_REVIEW_PACKAGE_DIR/governance-candidate-publication.json" | awk '{print $1}'
  )"
  test "$NODE2C_RETAINED_GOVERNANCE_SHA256" = \
    "$NODE2C_GOVERNANCE_CANDIDATE_PUBLICATION_SHA256"

  NODE2C_ACCEPTED_REVIEW_CREATE_SHA256="$(
    /usr/bin/python3 "$NODE2C_ACCEPTED_REVIEW_MANIFEST_BIN" create \
      --output-dir "$NODE2C_ACCEPTED_REVIEW_OUTPUT_DIR" \
      --candidate-sha "$REVIEW_HEAD" \
      --node-base "$NODE_BASE" \
      --predecessor-sha "$NODE_BASE" \
      --governance-publication-sha256 \
        "$NODE2C_RETAINED_GOVERNANCE_SHA256" \
      --producer-evidence-sha256 \
        "$NODE2C_POST_IMPLEMENTATION_EVIDENCE_SHA256" \
      --review-report-sha256 "$NODE2C_REVIEW_PACKAGE_REPORT_SHA256" \
      --review-stream-sha256 "$NODE2C_REVIEW_PACKAGE_STREAM_SHA256" \
      --reviewer-stderr-sha256 "$NODE2C_REVIEW_PACKAGE_STDERR_SHA256"
  )"
  /usr/bin/python3 "$NODE2C_ACCEPTED_REVIEW_MANIFEST_BIN" verify \
    --output-dir "$NODE2C_ACCEPTED_REVIEW_OUTPUT_DIR" >/dev/null
  NODE2C_ACCEPTED_REVIEW_MANIFEST_SHA256="$(
    sha256sum -- "$NODE2C_ACCEPTED_REVIEW_MANIFEST_PATH" | awk '{print $1}'
  )"
  test "$NODE2C_ACCEPTED_REVIEW_MANIFEST_SHA256" = \
    "$NODE2C_ACCEPTED_REVIEW_CREATE_SHA256"
  [[ "$NODE2C_ACCEPTED_REVIEW_MANIFEST_SHA256" =~ ^[0-9a-f]{64}$ ]]

  REVIEW_HANDOFF_PACKAGE_DIR="$NODE2C_REVIEW_PACKAGE_DIR" \
    /usr/bin/python3 - <<'PY'
import os
import stat

directory = os.environ["REVIEW_HANDOFF_PACKAGE_DIR"]
expected = {
    "governance-candidate-publication.json",
    "governance-candidate-publication.sha256",
    "producer-checks-evidence.json",
    "review-report.md",
    "review-report.md.sha256",
    "review-stream.jsonl",
    "review-stream.jsonl.sha256",
    "reviewer-stderr.txt",
    "reviewer-stderr.txt.sha256",
    "node2c-governance-accepted-review-checkpoint.json",
    "node2c-governance-accepted-review-checkpoint.sha256",
}
if set(os.listdir(directory)) != expected:
    raise SystemExit("review handoff package file set is not closed")
metadata = os.stat(directory, follow_symlinks=False)
if stat.S_IMODE(metadata.st_mode) != 0o700 or metadata.st_uid != os.geteuid():
    raise SystemExit("review handoff package directory mode is invalid")
for basename in expected:
    path = os.path.join(directory, basename)
    item = os.stat(path, follow_symlinks=False)
    if (
        not stat.S_ISREG(item.st_mode)
        or item.st_nlink != 1
        or item.st_uid != os.geteuid()
        or stat.S_IMODE(item.st_mode) != 0o600
    ):
        raise SystemExit("review handoff package file metadata is invalid")
PY
  NODE2C_REVIEW_PACKAGE_SEALED=true
}

cleanup_node2c_review_handoff() {
  if [ "$NODE2C_REVIEW_PACKAGE_RETAINED" = true ]; then
    return 0
  fi
  if [ ! -d "$NODE2C_REVIEW_HANDOFF_DIR" ]; then
    return 0
  fi
  case "$NODE2C_REVIEW_HANDOFF_DIR" in
    /*/node2c-review-handoff.*) ;;
    *) return 64 ;;
  esac
  local current_identity
  current_identity="$(stat -c '%d:%i' -- "$NODE2C_REVIEW_HANDOFF_DIR" 2>/dev/null)" ||
    return 73
  [ "$current_identity" = "$NODE2C_REVIEW_PACKAGE_IDENTITY" ] || return 73
  HANDOFF_DIR="$NODE2C_REVIEW_HANDOFF_DIR" \
    /usr/bin/python3 - <<'PY'
import os
import shutil
import stat

path = os.environ["HANDOFF_DIR"]
metadata = os.lstat(path)
if (
    not stat.S_ISDIR(metadata.st_mode)
    or metadata.st_uid != os.geteuid()
    or stat.S_IMODE(metadata.st_mode) != 0o700
):
    raise SystemExit("review handoff cleanup identity is not a private directory")
shutil.rmtree(path)
PY
}

cleanup_node2c_review_tmp() {
  local cleanup_status=0 command_status
  if test -d "$REVIEW_CODEGRAPH_DIR"; then
    if git worktree remove --force "$REVIEW_CODEGRAPH_DIR" >/dev/null 2>&1; then
      :
    else
      cleanup_status=$?
    fi
  fi
  if test -d "$REVIEW_SNAPSHOT_DIR"; then
    if git worktree remove --force "$REVIEW_SNAPSHOT_DIR" >/dev/null 2>&1; then
      :
    else
      command_status=$?
      if [ "$cleanup_status" -eq 0 ]; then
        cleanup_status="$command_status"
      fi
    fi
  fi
  if rm -rf -- "$REVIEW_TMP_DIR" >/dev/null 2>&1; then
    :
  else
    command_status=$?
    if [ "$cleanup_status" -eq 0 ]; then
      cleanup_status="$command_status"
    fi
  fi
  return "$cleanup_status"
}
cleanup_node2c_review_tmp_on_exit() {
  local original_status=$? cleanup_status handoff_status
  trap - EXIT
  set +e
  cleanup_node2c_review_tmp
  cleanup_status=$?
  cleanup_node2c_review_handoff
  handoff_status=$?
  set -e
  if [ "$cleanup_status" -eq 0 ] && [ "$handoff_status" -ne 0 ]; then
    cleanup_status="$handoff_status"
  fi
  if [ "$original_status" -ne 0 ]; then
    printf 'Claude review category: error\n' >&2
    exit "$original_status"
  fi
  if [ "$cleanup_status" -ne 0 ]; then
    printf 'Claude review category: error\n' >&2
  fi
  exit "$cleanup_status"
}
trap cleanup_node2c_review_tmp_on_exit EXIT

git worktree add --detach "$REVIEW_SNAPSHOT_DIR" "$REVIEW_HEAD"
REVIEW_SNAPSHOT_HEAD="$(git -C "$REVIEW_SNAPSHOT_DIR" rev-parse HEAD)"
test "$REVIEW_SNAPSHOT_HEAD" = "$REVIEW_HEAD"
test "$(sha256sum "$REVIEW_SNAPSHOT_DIR/$REVIEW_FOUNDATION_PATH" | awk '{print $1}')" = \
  "$REVIEW_FOUNDATION_SHA256"
REVIEW_SNAPSHOT_STATUS="$(
  git -C "$REVIEW_SNAPSHOT_DIR" status --porcelain --untracked-files=all
)"
test -z "$REVIEW_SNAPSHOT_STATUS"

git worktree add --detach "$REVIEW_CODEGRAPH_DIR" "$REVIEW_HEAD"
REVIEW_CODEGRAPH_HEAD="$(git -C "$REVIEW_CODEGRAPH_DIR" rev-parse HEAD)"
test "$REVIEW_CODEGRAPH_HEAD" = "$REVIEW_HEAD"
REVIEW_CODEGRAPH_STATUS_BEFORE="$(
  git -C "$REVIEW_CODEGRAPH_DIR" status --porcelain --untracked-files=all
)"
test -z "$REVIEW_CODEGRAPH_STATUS_BEFORE"
assert_node2c_git_controls
codegraph init -i "$REVIEW_CODEGRAPH_DIR"
(cd "$REVIEW_CODEGRAPH_DIR" && codegraph sync .)
codegraph index -f -q "$REVIEW_CODEGRAPH_DIR"
codegraph explore -p "$REVIEW_CODEGRAPH_DIR" \
  "Node 2C team evidence aggregation builder validator predecessor calls scope guard and tests" \
  > "$REVIEW_CODEGRAPH_EXPLORE_PATH"
codegraph node -p "$REVIEW_CODEGRAPH_DIR" \
  src/polymarket_alpha_lab/team_evidence_aggregation.py \
  > "$REVIEW_CODEGRAPH_PRODUCTION_PATH"
codegraph node -p "$REVIEW_CODEGRAPH_DIR" \
  tests/test_team_evidence_aggregation.py \
  > "$REVIEW_CODEGRAPH_TEST_PATH"
codegraph node -p "$REVIEW_CODEGRAPH_DIR" \
  tests/test_team_evidence_aggregation_scope.py \
  > "$REVIEW_CODEGRAPH_SCOPE_PATH"
for evidence_path in \
  "$REVIEW_CODEGRAPH_EXPLORE_PATH" \
  "$REVIEW_CODEGRAPH_PRODUCTION_PATH" \
  "$REVIEW_CODEGRAPH_TEST_PATH" \
  "$REVIEW_CODEGRAPH_SCOPE_PATH"; do
  test -s "$evidence_path"
  if rg -qi \
    '^(no indexed file matches|symbol( .*)? not found( in (the )?(index|codebase))?|file not found|.*not found in (the )?(index|codebase))' \
    "$evidence_path"; then
    printf 'CodeGraph evidence lookup failed for %s\n' "$evidence_path" >&2
    exit 1
  else
    RG_STATUS=$?
  fi
  case "$RG_STATUS" in
    1) ;;
    *) printf 'CodeGraph evidence error scan failed with status %s\n' "$RG_STATUS" >&2; exit "$RG_STATUS" ;;
  esac
done
{
  printf '%s\n' 'EXPLORE:'
  cat "$REVIEW_CODEGRAPH_EXPLORE_PATH"
  printf '%s\n' 'PRODUCTION_NODE:'
  cat "$REVIEW_CODEGRAPH_PRODUCTION_PATH"
  printf '%s\n' 'REDUCER_TEST_NODE:'
  cat "$REVIEW_CODEGRAPH_TEST_PATH"
  printf '%s\n' 'SCOPE_TEST_NODE:'
  cat "$REVIEW_CODEGRAPH_SCOPE_PATH"
} > "$REVIEW_CODEGRAPH_PATH"
test -s "$REVIEW_CODEGRAPH_PATH"
assert_node2c_git_controls

{
  printf '%s\n' \
    'Read-only Node 2C full-range review. Do not modify, create, or delete files.' \
    'Fast mode is forbidden.' \
    'Read exactly AGENTS.md and these six normative documents:' \
    'docs/superpowers/plans/2026-07-13-btc-domain-evidence-aggregation-foundation.md' \
    'docs/superpowers/specs/2026-07-13-team-evidence-aggregation-core-design.md' \
    'docs/quality/phase-1-development-node-quality-gates.md' \
    'docs/superpowers/plans/2026-07-13-team-evidence-aggregation-contracts-codec-temporal-eligibility.md' \
    'docs/superpowers/plans/2026-07-13-team-evidence-aggregation-independence-correlation-requirement-witness.md' \
    'docs/superpowers/plans/2026-07-13-team-evidence-aggregation-status-facade-publishability-scope-guard.md' \
    'CodeGraph exploration and node evidence was captured from a second detached worktree at exact REVIEW_HEAD after a fresh initialization and forced full index. The separate clean detached read-only-tool review worktree is the same commit and is used only as Claude cwd. Use the included evidence before any Read, Glob, or Grep call.' \
    'Use only Read, Glob, and Grep. Do not search for unnamed planning documents or use a write-capable tool.' \
    'Inspect the complete unrestricted NODE_BASE..REVIEW_HEAD patch and exact three-path allowlist printed below.' \
    'Verify both selector identity sets, pair-level selected_current_revision, all thirteen disposition precedence branches, exact allocator-result identity into the real Node 2B witness before any facade consumption, no duplication of Node 2B allocation/coverage-field/witness/matching semantics, the raw pre-construction requirement-ID projection with all five failure classes before authoritative coverage status consumption, weighted canonical P(YES), contradiction boundaries, blocked > watch > ready, complete exact reasons, and ready-only supplied-bound publication.' \
    'Verify a wrong outer result type keeps exact result must be exactly TeamEvidenceAggregationResult; for an exact outer type, supplied-result codec recursive-shape validation runs before rematerialization and before any supplied field callback or semantic comparison, codec failure maps immediately to the exact generic mismatch without rematerializing, malformed input/config errors remain exact after codec success, subsequent supplied-result shape/semantic mismatches map to the generic mismatch, and the complete validator isolates ambient Decimal context.' \
    'Verify every individual production and test line ceiling and every corresponding producer-observed physical-line count from the single NODE2C_GATE_EVIDENCE input; reject missing, duplicate, reordered, caller-substituted, aggregate-only, or scope-flag-only records.' \
    'Verify the unified six-module AST/import/export/forbidden-surface/package-root/line-size gate, including direct export ownership and the binding, unbinding, and dynamic namespace-mutation export matrix. Require retained observed counts for every production ceiling: team_evidence_aggregation_types.py <= 900, team_evidence_aggregation_codec.py <= 500, team_evidence_aggregation_temporal.py <= 300, team_evidence_aggregation_allocation.py <= 450, team_evidence_aggregation_witness.py <= 650, and team_evidence_aggregation.py <= 700.' \
    'Require retained observed counts for every test ceiling: test_team_evidence_aggregation_types.py <= 900, test_team_evidence_aggregation_codec.py <= 600, test_team_evidence_aggregation_temporal.py <= 450, test_team_evidence_aggregation_allocation.py <= 600, test_team_evidence_aggregation_witness.py <= 900, test_team_evidence_aggregation.py <= 900, and test_team_evidence_aggregation_scope.py <= 500; also verify production total <= 3,500 and test total <= 4,850.' \
    'Verify import normalization is module-only: a leading-underscore member or alias is not rejected merely by spelling; relative, empty-module, unallowlisted, package-root, exact-prefix-extension, and wildcard imports are rejected; every member and alias remains subject to the forbidden semantic-name and exact ordinary and reflective forbidden-call matrices, including module/member aliases, dynamic called-getattr flow, pattern fields, and nested Global package bindings.' \
    'Verify every __all__ export has exactly one direct module-body definition of the documented kind (ClassDef or FunctionDef); imports, assignments, walrus/named-expression, nested, async, wrong-kind, duplicates, unbinding, and dynamic namespace mutation cannot satisfy or rebind it.' \
    'Verify the fixed governance-document chain is reviewed Node 2B -> e31c3951b06f06e995c0c8f6f8fe2f22320a38da -> NODE_BASE, each arrow is a sole-parent edge, e31 changes exactly the Node 2C plan, NODE_BASE has exact subject docs: align Node 2C witness ownership governance and changes exactly the plan then core design under LC_ALL=C, the candidate design blob is f1ac9a517725ccdc7740108db82f89cd74d0e33f and differs from e31, NODE_BASE contains the publication-record-reviewed plan/design blobs, and neither governance-document commit is included in NODE_BASE..REVIEW_HEAD.' \
    'Verify initial and resume preflight modes preserve candidate NODE_BASE as the one remote implementation publication base while allowing only the exact three-path descendant review-fix range and no governance-document touch.' \
    'Verify paper_only=True, report_only=True, readonly=True and absence of persistence, DB, network, CLI, live/auth/account/private-key/wallet/signing/order/execution surfaces.' \
    'Confirm future persistence wording remains local Supabase/Postgres only and requires validate_local_postgres_dsn before any connection, wrapper, adapter, repository, or store construction; this pure child performs no persistence.' \
    'Actual focused/compile/collect/full/CodeGraph/history/range/clean/classification evidence follows; assess every classified path rather than assuming it is acceptable.' \
    'Return findings first with file:line references. Your exact final nonblank line must be VERDICT: PASS or VERDICT: REVISE.' \
    "NODE_BASE=$NODE_BASE" \
    "REVIEW_HEAD=$REVIEW_HEAD" \
    "NODE2A_PREREQ_SHA=$NODE2A_PREREQ_SHA" \
    "NODE2B_PREREQ_SHA=$NODE2B_PREREQ_SHA" \
    "NODE2C_IMPORT_GOVERNANCE_PARENT_SHA=$NODE2C_IMPORT_GOVERNANCE_PARENT_SHA" \
    "NODE2C_REVIEWED_PLAN_BLOB=$NODE2C_REVIEWED_PLAN_BLOB" \
    "NODE2C_REVIEWED_DESIGN_BLOB=$NODE2C_REVIEWED_DESIGN_BLOB" \
    "FOUNDATION_AUTHORITY_PATH=$REVIEW_FOUNDATION_PATH" \
    "FOUNDATION_AUTHORITY_SHA256=$REVIEW_FOUNDATION_SHA256" \
    "FOUNDATION_AUTHORITY_GIT_BLOB=$REVIEW_FOUNDATION_BLOB" \
    "$NODE2A_RECEIPT_EVIDENCE" \
    "$NODE2B_RECEIPT_EVIDENCE" \
    "$INITIAL_GOVERNANCE_CANDIDATE_PUBLICATION_EVIDENCE" \
    "$NODE2C_GATE_EVIDENCE" \
    'CODEGRAPH_EVIDENCE:'
  cat "$REVIEW_CODEGRAPH_PATH"
  printf '%s\n' \
    'EXACT_CHANGED_PATHS:' \
    "$EXPECTED_NODE_PATHS" \
    'COMPLETE_PATCH:'
  git diff --no-ext-diff --no-textconv --unified=80 "$NODE_BASE..$REVIEW_HEAD"
} > "$REVIEW_PROMPT_PATH"

REVIEW_CLAUDE_ENV=(
  -i
  "HOME=$HOME"
  "PATH=$PATH"
  'LANG=C.UTF-8'
  'LC_ALL=C.UTF-8'
  "TMPDIR=$REVIEW_TMP_DIR"
  'GIT_NO_REPLACE_OBJECTS=1'
  "USER=${USER:-node2c-review}"
  'SHELL=/bin/bash'
  'TERM=dumb'
)
for review_env_name in \
  CLAUDE_CONFIG_DIR \
  XDG_CACHE_HOME \
  XDG_CONFIG_HOME \
  XDG_DATA_HOME; do
  if [[ -v "$review_env_name" ]]; then
    REVIEW_CLAUDE_ENV+=("$review_env_name=${!review_env_name}")
  fi
done

set +e
(
  cd "$REVIEW_SNAPSHOT_DIR" || exit 76
  ulimit -f "$REVIEW_RAW_FILE_LIMIT_KIB"
  env "${REVIEW_CLAUDE_ENV[@]}" \
    timeout --signal=TERM --kill-after=10s 900s \
      claude --print \
      --bare \
      --input-format text \
      --output-format stream-json \
      --include-partial-messages \
      --verbose \
      --safe-mode \
      --model claude-fable-5 \
      --effort max \
      --tools Read,Glob,Grep \
      --permission-mode dontAsk \
      --no-session-persistence \
      --system-prompt 'You are a read-only senior engineering reviewer. Use only Read, Glob, and Grep. Return findings first and the exact required verdict. Do not modify, create, or delete files.' \
      < "$REVIEW_PROMPT_PATH"
) > "$REVIEW_STREAM_PATH" 2> "$REVIEW_STDERR_PATH"
REVIEW_STATUS=$?
set -e

REVIEW_PARSE_OUTPUT=''
set +e
REVIEW_PARSE_OUTPUT="$(
  (
    ulimit -f "$REVIEW_RAW_FILE_LIMIT_KIB"
    /usr/bin/python3 -       "$REVIEW_STREAM_PATH"       "$REVIEW_REPORT_PATH"       "$REVIEW_REPORT_SHA256_PATH" <<'PY'
# NODE2C_REVIEW_STREAM_PARSER_BEGIN
import hashlib
import json
import os
import stat
import sys

MAX_STREAM_BYTES = 16_777_216
MAX_REPORT_BYTES = 1_048_576
MAX_JSONL_RECORDS = 100_000
DATA_ERROR = 65
CREATE_ERROR = 73

stream_path, report_path, report_sha256_path = sys.argv[1:]


def fail(message, status=DATA_ERROR):
    print(f"review stream parse failed: {message}", file=sys.stderr)
    raise SystemExit(status)


def nofollow_flag():
    if not hasattr(os, "O_NOFOLLOW"):
        fail("this platform does not provide O_NOFOLLOW")
    return os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)


def read_regular_nofollow(path, maximum):
    try:
        descriptor = os.open(path, os.O_RDONLY | nofollow_flag())
    except OSError as error:
        fail(f"could not open regular input: {error}")
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_size <= 0
            or before.st_size > maximum
        ):
            fail(f"regular input size/type must be within 1..{maximum} bytes")
        chunks = []
        remaining = before.st_size
        while remaining:
            block = os.read(descriptor, min(remaining, 131_072))
            if not block:
                fail("regular input became shorter while reading")
            chunks.append(block)
            remaining -= len(block)
        if os.read(descriptor, 1):
            fail("regular input became longer while reading")
        after = os.fstat(descriptor)
        identity_before = (
            before.st_dev,
            before.st_ino,
            before.st_mode,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        )
        identity_after = (
            after.st_dev,
            after.st_ino,
            after.st_mode,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        )
        if identity_before != identity_after:
            fail("regular input metadata changed while reading")
        return b"".join(chunks)
    except OSError as error:
        fail(f"regular input read failed: {error}")
    finally:
        os.close(descriptor)


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f"non-standard JSON constant {value}")


def validate_decoded_strings(value):
    if type(value) is str:
        for character in value:
            codepoint = ord(character)
            if (
                (codepoint < 0x20 and character not in "\t\n")
                or 0x7F <= codepoint <= 0x9F
                or 0xD800 <= codepoint <= 0xDFFF
            ):
                raise ValueError(
                    f"forbidden decoded control/surrogate U+{codepoint:04X}",
                )
    elif type(value) is list:
        for item in value:
            validate_decoded_strings(item)
    elif type(value) is dict:
        for key, item in value.items():
            validate_decoded_strings(key)
            validate_decoded_strings(item)


def require_object(value, message):
    if type(value) is not dict:
        raise ValueError(message)
    return value


def require_string(value, message, *, nonempty=False):
    if type(value) is not str or (nonempty and not value):
        raise ValueError(message)
    return value


def require_index(event, message):
    index = event.get("index")
    if type(index) is not int or index < 0:
        raise ValueError(message)
    return index


def write_exclusive_nofollow(path, source):
    descriptor = None
    created = False
    try:
        descriptor = os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | nofollow_flag(),
            0o600,
        )
        created = True
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise OSError("exclusive output is not one regular link")
        offset = 0
        while offset < len(source):
            written = os.write(descriptor, source[offset:])
            if written <= 0:
                raise OSError("exclusive output short write")
            offset += written
        os.fsync(descriptor)
    except BaseException:
        if descriptor is not None:
            os.close(descriptor)
            descriptor = None
        if created:
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass
        raise
    finally:
        if descriptor is not None:
            os.close(descriptor)


stream_bytes = read_regular_nofollow(stream_path, MAX_STREAM_BYTES)
for byte in stream_bytes:
    if byte < 0x20 and byte != 0x0A:
        fail(f"raw JSONL contains forbidden control byte 0x{byte:02x}")
try:
    stream_text = stream_bytes.decode("utf-8", errors="strict")
except UnicodeDecodeError as error:
    fail(f"stream is not strict UTF-8: {error}")

records = stream_text.split("\n")
if records[-1] == "":
    records.pop()
if not records or len(records) > MAX_JSONL_RECORDS:
    fail("JSONL record count is outside the accepted range")

events = []
try:
    for line_number, line in enumerate(records, 1):
        if not line:
            raise ValueError(f"line {line_number} is an empty JSONL record")
        event = json.loads(
            line,
            object_pairs_hook=reject_duplicates,
            parse_constant=reject_constant,
        )
        require_object(event, f"line {line_number} is not a JSON object")
        require_string(
            event.get("type"),
            f"line {line_number} has no string top-level type",
            nonempty=True,
        )
        validate_decoded_strings(event)
        events.append(event)
except (json.JSONDecodeError, RecursionError, ValueError) as error:
    fail(str(error))

messages = []
current_message = None
terminal_results = []
try:
    for position, event in enumerate(events, 1):
        event_type = event["type"]
        if event_type == "system":
            require_string(
                event.get("subtype"),
                f"event {position} system subtype is not a string",
                nonempty=True,
            )
        elif event_type == "stream_event":
            nested = require_object(
                event.get("event"),
                f"event {position} stream event is not an object",
            )
            nested_type = require_string(
                nested.get("type"),
                f"event {position} nested event type is not a string",
                nonempty=True,
            )
            if nested_type == "message_start":
                if current_message is not None:
                    raise ValueError(f"event {position} starts a nested message")
                message = require_object(
                    nested.get("message"),
                    f"event {position} message_start message is not an object",
                )
                if (
                    message.get("type") != "message"
                    or message.get("role") != "assistant"
                    or type(message.get("content")) is not list
                ):
                    raise ValueError(
                        f"event {position} does not start an assistant message",
                    )
                message_id = require_string(
                    message.get("id"),
                    f"event {position} assistant message id is invalid",
                    nonempty=True,
                )
                current_message = {
                    "id": message_id,
                    "delta_parts": [],
                    "assistant_parts": [],
                    "assistant_text_records": 0,
                    "open_blocks": set(),
                    "stop_position": 0,
                }
            elif nested_type == "content_block_start":
                if current_message is None:
                    raise ValueError(f"event {position} starts a block outside a message")
                index = require_index(
                    nested,
                    f"event {position} content block index is invalid",
                )
                block = require_object(
                    nested.get("content_block"),
                    f"event {position} content block is not an object",
                )
                require_string(
                    block.get("type"),
                    f"event {position} content block type is invalid",
                    nonempty=True,
                )
                if index in current_message["open_blocks"]:
                    raise ValueError(f"event {position} repeats an open content block")
                current_message["open_blocks"].add(index)
            elif nested_type == "content_block_delta":
                if current_message is None:
                    raise ValueError(f"event {position} has a delta outside a message")
                index = require_index(
                    nested,
                    f"event {position} content delta index is invalid",
                )
                if index not in current_message["open_blocks"]:
                    raise ValueError(f"event {position} targets no open content block")
                delta = require_object(
                    nested.get("delta"),
                    f"event {position} content delta is not an object",
                )
                delta_type = require_string(
                    delta.get("type"),
                    f"event {position} content delta type is invalid",
                    nonempty=True,
                )
                if delta_type == "text_delta":
                    text = require_string(
                        delta.get("text"),
                        f"event {position} text delta is not a string",
                    )
                    current_message["delta_parts"].append(text)
            elif nested_type == "content_block_stop":
                if current_message is None:
                    raise ValueError(f"event {position} stops a block outside a message")
                index = require_index(
                    nested,
                    f"event {position} stopped content block index is invalid",
                )
                if index not in current_message["open_blocks"]:
                    raise ValueError(f"event {position} stops no open content block")
                current_message["open_blocks"].remove(index)
            elif nested_type == "message_delta":
                if current_message is None:
                    raise ValueError(f"event {position} has message_delta outside a message")
                require_object(
                    nested.get("delta"),
                    f"event {position} message_delta delta is not an object",
                )
            elif nested_type == "message_stop":
                if current_message is None:
                    raise ValueError(f"event {position} stops no assistant message")
                if current_message["open_blocks"]:
                    raise ValueError(f"event {position} stops with open content blocks")
                current_message["stop_position"] = position
                messages.append(current_message)
                current_message = None
            else:
                raise ValueError(
                    f"event {position} has unsupported nested type {nested_type!r}",
                )
        elif event_type == "assistant":
            if current_message is None:
                raise ValueError(f"event {position} assistant payload is outside a message")
            message = require_object(
                event.get("message"),
                f"event {position} assistant payload message is not an object",
            )
            if (
                message.get("type") != "message"
                or message.get("role") != "assistant"
                or message.get("id") != current_message["id"]
                or type(message.get("content")) is not list
            ):
                raise ValueError(f"event {position} assistant payload shape is invalid")
            assistant_event_parts = []
            for block in message["content"]:
                require_object(
                    block,
                    f"event {position} assistant content block is not an object",
                )
                block_type = require_string(
                    block.get("type"),
                    f"event {position} assistant content block type is invalid",
                    nonempty=True,
                )
                if block_type == "text":
                    text = require_string(
                        block.get("text"),
                        f"event {position} assistant text block is not a string",
                    )
                    assistant_event_parts.append(text)
            if assistant_event_parts:
                current_message["assistant_text_records"] += 1
                current_message["assistant_parts"].extend(assistant_event_parts)
        elif event_type == "result":
            if current_message is not None:
                raise ValueError(f"event {position} result precedes message_stop")
            terminal_results.append((position, event))
        else:
            raise ValueError(f"event {position} has unsupported top-level type {event_type!r}")
except ValueError as error:
    fail(str(error))

if current_message is not None:
    fail("stream ended inside an assistant message")
if len(terminal_results) != 1:
    fail("stream must contain exactly one terminal result")
terminal_position, terminal = terminal_results[0]
terminal_text = terminal.get("result")
if (
    terminal_position != len(events)
    or terminal.get("subtype") != "success"
    or terminal.get("is_error") is not False
    or terminal.get("stop_reason") != "end_turn"
    or terminal.get("terminal_reason") != "completed"
    or type(terminal_text) is not str
    or not terminal_text
):
    fail("terminal result is not one final completed success")

if messages:
    terminal_message = messages[-1]
    if terminal_message["stop_position"] != terminal_position - 1:
        fail("terminal assistant message does not end immediately before result")
    if terminal_message["assistant_text_records"] != 1:
        fail("terminal assistant message must have exactly one report-bearing record")
    delta_text = "".join(terminal_message["delta_parts"])
    assistant_text = "".join(terminal_message["assistant_parts"])
    if not delta_text or not assistant_text:
        fail("terminal assistant message has no report text")
    delta_bytes = delta_text.encode("utf-8")
    assistant_bytes = assistant_text.encode("utf-8")
    terminal_bytes = terminal_text.encode("utf-8")
    if delta_bytes != assistant_bytes or assistant_bytes != terminal_bytes:
        fail("text_delta, assistant message, and result report bytes disagree")
    report_bytes = assistant_bytes
else:
    report_bytes = terminal_text.encode("utf-8")

if not 0 < len(report_bytes) <= MAX_REPORT_BYTES:
    fail(f"report size must be within 1..{MAX_REPORT_BYTES} UTF-8 bytes")
report_text = report_bytes.decode("utf-8")
nonblank_lines = [
    line
    for line in report_text.split("\n")
    if any(character not in " \t" for character in line)
]
if not nonblank_lines:
    fail("report has no LF-delimited nonblank line")
final_line = nonblank_lines[-1]
if final_line not in {"VERDICT: PASS", "VERDICT: REVISE"}:
    fail(f"invalid exact final review line: {final_line!r}")

digest = hashlib.sha256(report_bytes).hexdigest()
if os.path.abspath(report_path) == os.path.abspath(report_sha256_path):
    fail("report and SHA-256 sidecar paths must differ", CREATE_ERROR)
try:
    write_exclusive_nofollow(report_path, report_bytes)
    try:
        write_exclusive_nofollow(
            report_sha256_path,
            (digest + "\n").encode("ascii"),
        )
    except BaseException:
        os.unlink(report_path)
        raise
except FileExistsError as error:
    fail(f"exclusive report output already exists: {error}", CREATE_ERROR)
except OSError as error:
    fail(f"exclusive report output failed: {error}", CREATE_ERROR)

print(digest)
print(final_line)
# NODE2C_REVIEW_STREAM_PARSER_END
PY
  ) 2>> "$REVIEW_STDERR_PATH"
)"
REVIEW_PARSE_STATUS=$?
set -e

REVIEW_PARSER_REPORT_SHA256=''
REVIEW_FINAL_LINE=''
REVIEW_PARSE_LINES=()
if [ "$REVIEW_PARSE_STATUS" -eq 0 ]; then
  mapfile -t REVIEW_PARSE_LINES <<< "$REVIEW_PARSE_OUTPUT"
  if [ "${#REVIEW_PARSE_LINES[@]}" -ne 2 ] ||     [[ ! "${REVIEW_PARSE_LINES[0]}" =~ ^[0-9a-f]{64}$ ]] ||     { [ "${REVIEW_PARSE_LINES[1]}" != 'VERDICT: PASS' ] &&       [ "${REVIEW_PARSE_LINES[1]}" != 'VERDICT: REVISE' ]; }; then
    REVIEW_PARSE_STATUS=65
  else
    REVIEW_PARSER_REPORT_SHA256="${REVIEW_PARSE_LINES[0]}"
    REVIEW_FINAL_LINE="${REVIEW_PARSE_LINES[1]}"
  fi
fi

verify_node2c_review_report_attestation() {
  local expected_digest="$1"
  EXPECTED_DIGEST="$expected_digest" \
  REPORT_PATH="$REVIEW_REPORT_PATH" \
  SIDECAR_PATH="$REVIEW_REPORT_SHA256_PATH" \
    /usr/bin/python3 - <<'PY'
import hashlib
import os
import stat
import sys

MAX_REPORT_BYTES = 1_048_576


def read_regular_nofollow(path, maximum, *, exact_size=None):
    if not hasattr(os, "O_NOFOLLOW"):
        raise ValueError("O_NOFOLLOW is unavailable")
    flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size <= 0:
            raise ValueError("attested input is not a nonempty regular file")
        if exact_size is not None:
            if before.st_size != exact_size:
                raise ValueError("attested input has the wrong exact size")
        elif before.st_size > maximum:
            raise ValueError("attested input exceeds its byte limit")
        chunks = []
        remaining = before.st_size
        while remaining:
            block = os.read(descriptor, min(remaining, 131_072))
            if not block:
                raise ValueError("attested input became shorter while reading")
            chunks.append(block)
            remaining -= len(block)
        if os.read(descriptor, 1):
            raise ValueError("attested input became longer while reading")
        after = os.fstat(descriptor)
        before_identity = (
            before.st_dev,
            before.st_ino,
            before.st_mode,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        )
        after_identity = (
            after.st_dev,
            after.st_ino,
            after.st_mode,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        )
        if before_identity != after_identity:
            raise ValueError("attested input metadata changed while reading")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


try:
    report = read_regular_nofollow(
        os.environ["REPORT_PATH"],
        MAX_REPORT_BYTES,
    )
    sidecar = read_regular_nofollow(
        os.environ["SIDECAR_PATH"],
        65,
        exact_size=65,
    )
    expected = os.environ["EXPECTED_DIGEST"]
    if len(expected) != 64 or any(character not in "0123456789abcdef" for character in expected):
        raise ValueError("expected report digest is not lowercase SHA-256")
    if hashlib.sha256(report).hexdigest() != expected:
        raise ValueError("report bytes do not match the expected SHA-256")
    if sidecar != (expected + "\n").encode("ascii"):
        raise ValueError("report SHA-256 sidecar bytes disagree")
except (OSError, ValueError) as error:
    print(f"review report attestation failed: {error}", file=sys.stderr)
    raise SystemExit(65)
PY
}

REVIEW_ATTEST_STATUS=65
if [ "$REVIEW_PARSE_STATUS" -eq 0 ]; then
  set +e
  REVIEW_REPORT_SIDECAR_MODE="$(
    stat -c '%a' -- "$REVIEW_REPORT_SHA256_PATH" 2>/dev/null
  )"
  REVIEW_REPORT_SIDECAR_MODE_STATUS=$?
  set -e
  if [ "$REVIEW_REPORT_SIDECAR_MODE_STATUS" -eq 0 ] &&     [ "$REVIEW_REPORT_SIDECAR_MODE" = 600 ]; then
    set +e
    verify_node2c_review_report_attestation       "$REVIEW_PARSER_REPORT_SHA256" 2>> "$REVIEW_STDERR_PATH"
    REVIEW_ATTEST_STATUS=$?
    set -e
  fi
fi

REVIEW_ARTIFACT_STATUS=0
REVIEW_STREAM_BYTES=0
REVIEW_REPORT_BYTES=0
REVIEW_STDERR_BYTES=0
REVIEW_STREAM_SHA256=''
REVIEW_REPORT_SHA256=''
REVIEW_STDERR_SHA256=''
for review_artifact_name in stream report stderr; do
  case "$review_artifact_name" in
    stream) review_artifact_path="$REVIEW_STREAM_PATH" ;;
    report) review_artifact_path="$REVIEW_REPORT_PATH" ;;
    stderr) review_artifact_path="$REVIEW_STDERR_PATH" ;;
  esac
  set +e
  review_artifact_mode="$(
    stat -c '%a' -- "$review_artifact_path" 2>/dev/null
  )"
  review_artifact_mode_status=$?
  review_artifact_bytes="$(
    stat -c '%s' -- "$review_artifact_path" 2>/dev/null
  )"
  review_artifact_bytes_status=$?
  review_artifact_hash_line="$(
    sha256sum -- "$review_artifact_path" 2>/dev/null
  )"
  review_artifact_hash_status=$?
  set -e
  review_artifact_hash="${review_artifact_hash_line%% *}"
  if [ "$review_artifact_mode_status" -ne 0 ] || \
    [ "$review_artifact_bytes_status" -ne 0 ] || \
    [ "$review_artifact_hash_status" -ne 0 ] || \
    [ "$review_artifact_mode" != 600 ] || \
    [[ ! "$review_artifact_bytes" =~ ^[0-9]+$ ]] || \
    [ "$review_artifact_bytes" -ge "$REVIEW_RAW_FILE_LIMIT_BYTES" ] || \
    [[ ! "$review_artifact_hash" =~ ^[0-9a-f]{64}$ ]]; then
    REVIEW_ARTIFACT_STATUS=1
    continue
  fi
  case "$review_artifact_name" in
    stream)
      REVIEW_STREAM_BYTES="$review_artifact_bytes"
      REVIEW_STREAM_SHA256="$review_artifact_hash"
      ;;
    report)
      REVIEW_REPORT_BYTES="$review_artifact_bytes"
      REVIEW_REPORT_SHA256="$review_artifact_hash"
      ;;
    stderr)
      REVIEW_STDERR_BYTES="$review_artifact_bytes"
      REVIEW_STDERR_SHA256="$review_artifact_hash"
      ;;
  esac
done

if [ "$REVIEW_PARSE_STATUS" -eq 0 ] &&   [ "$REVIEW_ARTIFACT_STATUS" -eq 0 ] &&   { [ "$REVIEW_REPORT_BYTES" -le 0 ] ||     [ "$REVIEW_REPORT_BYTES" -gt "$REVIEW_REPORT_FILE_LIMIT_BYTES" ] ||     [ "$REVIEW_REPORT_SHA256" != "$REVIEW_PARSER_REPORT_SHA256" ]; }; then
  REVIEW_ARTIFACT_STATUS=1
fi

REVIEW_REPORT_TEXT_STATUS=74
REVIEW_VERDICT_CATEGORY=error
if [ "$REVIEW_PARSE_STATUS" -eq 0 ] &&   [ "$REVIEW_ATTEST_STATUS" -eq 0 ] &&   [ "$REVIEW_ARTIFACT_STATUS" -eq 0 ]; then
  REVIEW_REPORT_TEXT_STATUS=0
  case "$REVIEW_FINAL_LINE" in
    'VERDICT: PASS') REVIEW_VERDICT_CATEGORY=pass ;;
    'VERDICT: REVISE') REVIEW_VERDICT_CATEGORY=revise ;;
    *)
      REVIEW_REPORT_TEXT_STATUS=65
      REVIEW_VERDICT_CATEGORY=error
      ;;
  esac
fi

assert_node2c_git_controls
REVIEW_POST_HEAD="$(git rev-parse HEAD)"
REVIEW_SNAPSHOT_POST_HEAD="$(git -C "$REVIEW_SNAPSHOT_DIR" rev-parse HEAD)"
REVIEW_SNAPSHOT_POST_STATUS="$(
  git -C "$REVIEW_SNAPSHOT_DIR" status --porcelain --untracked-files=all
)"
REVIEW_CODEGRAPH_POST_HEAD="$(git -C "$REVIEW_CODEGRAPH_DIR" rev-parse HEAD)"
REVIEW_CODEGRAPH_POST_STATUS="$(
  git -C "$REVIEW_CODEGRAPH_DIR" status --porcelain --untracked-files=all
)"
REVIEW_COORDINATOR_POST_STATUS="$(git status --porcelain --untracked-files=no)"

REVIEW_GATE_RESULT=error
if [ "$REVIEW_STATUS" -ne 0 ]; then
  REVIEW_GATE_RESULT=error
elif [ "$REVIEW_PARSE_STATUS" -ne 0 ]; then
  REVIEW_GATE_RESULT=error
elif [ "$REVIEW_ARTIFACT_STATUS" -ne 0 ]; then
  REVIEW_GATE_RESULT=error
elif [ "$REVIEW_REPORT_TEXT_STATUS" -ne 0 ]; then
  REVIEW_GATE_RESULT=error
elif [ "$REVIEW_VERDICT_CATEGORY" = revise ]; then
  REVIEW_GATE_RESULT=revise
elif [ "$REVIEW_VERDICT_CATEGORY" != pass ]; then
  REVIEW_GATE_RESULT=error
elif [ "$REVIEW_POST_HEAD" != "$REVIEW_HEAD" ]; then
  REVIEW_GATE_RESULT=error
elif [ "$REVIEW_SNAPSHOT_POST_HEAD" != "$REVIEW_HEAD" ]; then
  REVIEW_GATE_RESULT=error
elif [ -n "$REVIEW_SNAPSHOT_POST_STATUS" ]; then
  REVIEW_GATE_RESULT=error
elif [ "$REVIEW_CODEGRAPH_POST_HEAD" != "$REVIEW_HEAD" ]; then
  REVIEW_GATE_RESULT=error
elif [ -n "$REVIEW_CODEGRAPH_POST_STATUS" ]; then
  REVIEW_GATE_RESULT=error
elif ! git diff --quiet; then
  REVIEW_GATE_RESULT=error
elif ! git diff --cached --quiet; then
  REVIEW_GATE_RESULT=error
elif [ -n "$REVIEW_COORDINATOR_POST_STATUS" ]; then
  REVIEW_GATE_RESULT=error
else
  REVIEW_GATE_RESULT=pass
fi

if [ "$REVIEW_GATE_RESULT" = pass ]; then
  set +e
  retain_node2c_review_package
  REVIEW_PACKAGE_STATUS=$?
  set -e
  if [ "$REVIEW_PACKAGE_STATUS" -ne 0 ]; then
    REVIEW_GATE_RESULT=error
  fi
fi

set +e
cleanup_node2c_review_tmp
REVIEW_CLEANUP_STATUS=$?
set -e
if [ "$REVIEW_CLEANUP_STATUS" -ne 0 ]; then
  REVIEW_GATE_RESULT=error
fi
if [ "$REVIEW_GATE_RESULT" = pass ] && \
   [ "$REVIEW_CLEANUP_STATUS" -eq 0 ] && \
   [ "$NODE2C_REVIEW_PACKAGE_SEALED" = true ]; then
  NODE2C_REVIEW_PACKAGE_RETAINED=true
else
  set +e
  cleanup_node2c_review_handoff
  REVIEW_HANDOFF_CLEANUP_STATUS=$?
  set -e
  if [ "$REVIEW_HANDOFF_CLEANUP_STATUS" -ne 0 ]; then
    REVIEW_GATE_RESULT=error
  fi
fi
trap - EXIT
assert_node2c_git_controls

NODE2C_REVIEW_GATE_RESULT="$REVIEW_GATE_RESULT"
export NODE2C_REVIEW_GATE_RESULT
if [ "$NODE2C_REVIEW_GATE_RESULT" = pass ]; then
  NODE2C_ACCEPTED_REVIEW_HEAD="$REVIEW_HEAD"
  NODE2C_ACCEPTED_REVIEW_MODEL=claude-fable-5
  NODE2C_ACCEPTED_REVIEW_EFFORT=max
  NODE2C_ACCEPTED_REVIEW_READ_ONLY=true
  NODE2C_ACCEPTED_REVIEW_FAST_MODE=false
  NODE2C_ACCEPTED_REVIEW_EXIT_STATUS="$REVIEW_STATUS"
  NODE2C_ACCEPTED_REVIEW_FINAL_LINE="$REVIEW_FINAL_LINE"
  NODE2C_ACCEPTED_REVIEW_STREAM_SHA256="$REVIEW_STREAM_SHA256"
  NODE2C_ACCEPTED_REVIEW_REPORT_SHA256="$REVIEW_REPORT_SHA256"
  NODE2C_ACCEPTED_REVIEW_STDERR_SHA256="$REVIEW_STDERR_SHA256"
  NODE2C_ACCEPTED_REVIEW_STREAM_BYTES="$REVIEW_STREAM_BYTES"
  NODE2C_ACCEPTED_REVIEW_REPORT_BYTES="$REVIEW_REPORT_BYTES"
  NODE2C_ACCEPTED_REVIEW_STDERR_BYTES="$REVIEW_STDERR_BYTES"
  export NODE2C_ACCEPTED_REVIEW_HEAD NODE2C_ACCEPTED_REVIEW_MODEL \
    NODE2C_ACCEPTED_REVIEW_EFFORT NODE2C_ACCEPTED_REVIEW_READ_ONLY \
    NODE2C_ACCEPTED_REVIEW_FAST_MODE NODE2C_ACCEPTED_REVIEW_EXIT_STATUS \
    NODE2C_ACCEPTED_REVIEW_FINAL_LINE \
    NODE2C_ACCEPTED_REVIEW_STREAM_SHA256 \
    NODE2C_ACCEPTED_REVIEW_REPORT_SHA256 \
    NODE2C_ACCEPTED_REVIEW_STDERR_SHA256 \
    NODE2C_ACCEPTED_REVIEW_STREAM_BYTES \
    NODE2C_ACCEPTED_REVIEW_REPORT_BYTES \
    NODE2C_ACCEPTED_REVIEW_STDERR_BYTES
  export NODE2C_REVIEW_PACKAGE_DIR NODE2C_REVIEW_PACKAGE_REPORT_PATH \
    NODE2C_REVIEW_PACKAGE_STREAM_PATH NODE2C_REVIEW_PACKAGE_STDERR_PATH \
    NODE2C_REVIEW_PACKAGE_REPORT_SHA256 NODE2C_REVIEW_PACKAGE_STREAM_SHA256 \
    NODE2C_REVIEW_PACKAGE_STDERR_SHA256 NODE2C_ACCEPTED_REVIEW_MANIFEST_PATH \
    NODE2C_ACCEPTED_REVIEW_MANIFEST_SHA256 NODE2C_ACCEPTED_REVIEW_OUTPUT_DIR
  readonly NODE2C_REVIEW_GATE_RESULT NODE2C_ACCEPTED_REVIEW_HEAD \
    NODE2C_ACCEPTED_REVIEW_MODEL NODE2C_ACCEPTED_REVIEW_EFFORT \
    NODE2C_ACCEPTED_REVIEW_READ_ONLY NODE2C_ACCEPTED_REVIEW_FAST_MODE \
    NODE2C_ACCEPTED_REVIEW_EXIT_STATUS NODE2C_ACCEPTED_REVIEW_FINAL_LINE \
    NODE2C_ACCEPTED_REVIEW_STREAM_SHA256 \
    NODE2C_ACCEPTED_REVIEW_REPORT_SHA256 \
    NODE2C_ACCEPTED_REVIEW_STDERR_SHA256 \
    NODE2C_ACCEPTED_REVIEW_STREAM_BYTES \
    NODE2C_ACCEPTED_REVIEW_REPORT_BYTES \
    NODE2C_ACCEPTED_REVIEW_STDERR_BYTES NODE2C_REVIEW_PACKAGE_RETAINED \
    NODE2C_REVIEW_PACKAGE_DIR NODE2C_REVIEW_PACKAGE_REPORT_PATH \
    NODE2C_REVIEW_PACKAGE_STREAM_PATH NODE2C_REVIEW_PACKAGE_STDERR_PATH \
    NODE2C_REVIEW_PACKAGE_REPORT_SHA256 NODE2C_REVIEW_PACKAGE_STREAM_SHA256 \
    NODE2C_REVIEW_PACKAGE_STDERR_SHA256 NODE2C_ACCEPTED_REVIEW_MANIFEST_PATH \
    NODE2C_ACCEPTED_REVIEW_MANIFEST_SHA256 NODE2C_ACCEPTED_REVIEW_OUTPUT_DIR
  printf 'Claude review category: pass\n'
elif [ "$NODE2C_REVIEW_GATE_RESULT" = revise ]; then
  printf 'Claude review category: revise\n' >&2
  exit 2
else
  printf 'Claude review category: error\n' >&2
  exit 1
fi
```

Expected: all three descriptor-bound receipt revalidations reproduce their
exact initial canonical evidence. `NODE2C_REVIEW_GATE_RESULT=pass` and the
readonly `NODE2C_ACCEPTED_REVIEW_*` values are published only for review exit
`0`, a bounded strict-UTF-8 JSONL stream, one final completed-success result, an
exact matching terminal assistant envelope when streamed output exists, an
attested report byte/hash pair, exact final `VERDICT: PASS`, unchanged
`GATED_HEAD`, and a clean tracked worktree/index. A result-only fallback is
accepted only when it is the sole final completed-success result.

The raw stream, report, combined reviewer/parser stderr, and report-digest
sidecar are never printed. The stream, report, and stderr remain mode `0600`
within their explicit limits until byte counts and SHA-256 values are captured;
the temporary copies are then removed while the accepted hashes and counts
remain readonly formal evidence. `VERDICT: REVISE` maps to the fixed `revise`
category and exit `2`; review/tool/parse/attestation/artifact errors map to the
fixed `error` category and exit `1`. Receipt replacement, allowlist
incompatibility, timeout, duplicate keys, incomplete message boundaries,
multiple or non-final results, non-success results, malformed UTF-8, forbidden
controls, oversized or empty output, assistant/result disagreement, any other
final line, repository movement, or unavailable local Claude blocks
publication. There is no inherited-environment retry and no fallback reviewer.

- [ ] **Step 7: Apply any review fix as a new commit, then repeat the entire range gate and review**

For every requested change:

1. Invoke `assert_node2c_git_controls` directly, then record
   `PRE_FIX_HEAD="$(git rev-parse HEAD)"`.
2. Add or strengthen a failing focused test first and run it to observe the expected failure. For a non-behavioral finding, first reproduce it with the narrowest executable static/gate command.
3. Make the smallest owned-file fix and run the focused command to green.
4. Derive the exact changed fix subset, prove every path is in `NODE_PATHS`, stage only that subset, and prove staged equality with the subset.
5. Run the dedicated subset-aware staged hygiene and scan block below. Do not reuse Step 3's initial-commit expectation that all broader classifications equal the scope-test path.
6. Commit with a new focused commit; assert `HEAD != PRE_FIX_HEAD`.
7. Before terminating the current gate shell, record the literal governance-
   candidate publication path and SHA-256 already used by Task 1. Start a fresh
   shell, export `NODE2C_PREFLIGHT_MODE=resume`, restore the Node 2A/2B receipt
   handoffs and governance-candidate publication path/digest handoff, and rerun
   Task 1. The fresh shell repeats the complete
   inline helper definition, marks it readonly, exports readonly
   `GIT_NO_REPLACE_OBJECTS=1`, and calls it directly; it does not import the
   prior shell's function or pass. Do not directly restore or override
   `NODE_BASE`, `NODE2C_EXPECTED_BASE`, or either reviewed blob; they must be
   re-derived from the same descriptor-bound governance-candidate publication
   record. Resume mode must observe fetched remote `main` still equal to that
   publication-bound base
   while re-proving its sole parent is fixed `e31c3951`, both
   governance-document commits precede and are excluded from the implementation
   range, and only the exact
   three-path descendant range is accepted. Then repeat
   Step 5 over the complete immutable `NODE_BASE..HEAD` range, including
   focused tests, compileall, collect-only, full pytest, a forced full CodeGraph
   index, exact endpoint manifest, per-commit path/secret history, diff hygiene,
   clean-worktree checks, and every range scan.
8. Repeat Step 6 with a fresh full-range Claude invocation. Do not enter Step 8 unless it publishes `NODE2C_REVIEW_GATE_RESULT=pass`, exact `NODE2C_ACCEPTED_REVIEW_HEAD`, exit status `0`, and exact final `VERDICT: PASS`.

Use this exact subset check before each fix commit:

```bash
set -euo pipefail
assert_node2c_git_controls
FIX_PATHS_TEXT="$(git diff --name-only | LC_ALL=C sort)"
test -n "$FIX_PATHS_TEXT"
mapfile -t FIX_PATHS <<< "$FIX_PATHS_TEXT"
test "${#FIX_PATHS[@]}" -gt 0
for path in "${FIX_PATHS[@]}"; do
  case "$path" in
    src/polymarket_alpha_lab/team_evidence_aggregation.py | \
    tests/test_team_evidence_aggregation.py | \
    tests/test_team_evidence_aggregation_scope.py) ;;
    *) printf 'non-allowlisted fix path: %s\n' "$path" >&2; exit 1 ;;
  esac
done
git add -- "${FIX_PATHS[@]}"
assert_node2c_git_controls
STAGED_FIX_PATHS_TEXT="$(git diff --cached --name-only | LC_ALL=C sort)"
test "$STAGED_FIX_PATHS_TEXT" = "$FIX_PATHS_TEXT"
git diff --cached --check

HIGH_CONFIDENCE_SECRET_PATTERN='(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|(^|[^[:alnum:]_])sk-[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}|postgres(ql)?://[^[:space:]/]+:[^[:space:]@]+@)'
SENSITIVE_FIELD_PATTERN='\b(api[_-]?key|secret|token|password|passwd|cookie|authorization|bearer|private[_ -]?key|seed phrase|mnemonic|wallet|account[_ -]?(id|address))\b'
READONLY_PATTERN='\b(live[_ -]?trading|order[_ -]?submission|submit[_ -]?order|cancel[_ -]?order|replace[_ -]?order|sign[_ -]?order|wallet|private[_ -]?key|hosted[_ -]?account|account[_ -]?authentication|exchange[_ -]?mutation|order[_ -]?mutation)\b'
PERSISTENCE_PATTERN='\b(sqlite|duckdb|redis|mongodb|sqlalchemy|jsonl|file[_ -]?backed|postgres|supabase|dsn|validate_local_postgres_dsn|migration|persistence|store)\b'
FIX_SENSITIVE_PATHS=()
FIX_READONLY_PATHS=()
FIX_PERSISTENCE_PATHS=()

for path in "${FIX_PATHS[@]}"; do
  STAGED_ADDED_FOR_PATH="$(git diff --cached --unified=0 -- "$path" | sed -n '/^+++ /d; /^+/s/^+//p')"
  if rg -q "$HIGH_CONFIDENCE_SECRET_PATTERN" <<< "$STAGED_ADDED_FOR_PATH"; then
    RG_STATUS=0
  else
    RG_STATUS=$?
  fi
  case "$RG_STATUS" in
    0) printf '%s\n' "$path" >&2; exit 1 ;;
    1) ;;
    *) printf '%s\n' "$path" >&2; exit "$RG_STATUS" ;;
  esac

  for scan_name in sensitive readonly persistence; do
    case "$scan_name" in
      sensitive) pattern="$SENSITIVE_FIELD_PATTERN" ;;
      readonly) pattern="$READONLY_PATTERN" ;;
      persistence) pattern="$PERSISTENCE_PATTERN" ;;
    esac
    if rg -qi "$pattern" <<< "$STAGED_ADDED_FOR_PATH"; then
      case "$scan_name" in
        sensitive) FIX_SENSITIVE_PATHS+=("$path") ;;
        readonly) FIX_READONLY_PATHS+=("$path") ;;
        persistence) FIX_PERSISTENCE_PATHS+=("$path") ;;
      esac
    else
      RG_STATUS=$?
      test "$RG_STATUS" -eq 1
    fi
  done
done

printf 'fix sensitive classifications:\n  %s\n' "${FIX_SENSITIVE_PATHS[@]}"
printf 'fix readonly classifications:\n  %s\n' "${FIX_READONLY_PATHS[@]}"
printf 'fix persistence classifications:\n  %s\n' "${FIX_PERSISTENCE_PATHS[@]}"
assert_node2c_git_controls
git commit -m "Fix Node 2C review findings"
assert_node2c_git_controls
FIX_COMMIT_SHA="$(git rev-parse HEAD)"
test "$FIX_COMMIT_SHA" != "$PRE_FIX_HEAD"
assert_node2c_git_controls
printf 'created Node 2C review-fix commit: %s\n' "$FIX_COMMIT_SHA"
```

All findings from one Claude report may be corrected in one focused fix commit.
A later report requiring another correction requires another new commit and
fresh-shell full-range gate. No amended commit is allowed after review. Every
post-review change invalidates all prior gate and review evidence until the
complete range passes again.

- [ ] **Step 8: Durably checkpoint the sole push and classify publication by observation**

Run this gate only after the final PASS. Materialize this single Bash fence
unchanged outside the tracked worktree and invoke it with exactly one
`NODE2C_PUBLICATION_ACTION` value: `publish` for the sole mutation attempt,
`recover` from a fresh shell for observation-only recovery, or
`complete` for the mandatory completion assertion. The fixed checkpoint path is
inside the repository's common Git directory, so a fresh worktree shell finds
the same control record without deriving an endpoint or commit from ambient
state.

Bind the extracted fence's absolute path as `NODE2C_PUBLICATION_GATE_SCRIPT`.
Invoke every action with a new Bash process from the repository root. The final
PASS shell exports the accepted scalar evidence and the descriptor-bound
governance-candidate publication record validator, then runs
`NODE2C_PUBLICATION_ACTION=publish bash "$NODE2C_PUBLICATION_GATE_SCRIPT"`
exactly once. After that process returns or is lost, never invoke `publish`
again. Run observation-only recovery and mandatory completion as
`NODE2C_PUBLICATION_ACTION=recover bash "$NODE2C_PUBLICATION_GATE_SCRIPT"` and
`NODE2C_PUBLICATION_ACTION=complete bash "$NODE2C_PUBLICATION_GATE_SCRIPT"`.
No action sources the fence into an existing shell or imports a Git-control
function or prior Git-control pass.

Each action receives only explicit absolute handoff variables for the local v6
checkpoint and the independent split accepted-review package:
`NODE2C_ACCEPTED_REVIEW_MANIFEST_BIN`,
`NODE2C_ACCEPTED_REVIEW_OUTPUT_DIR`,
`NODE2C_ACCEPTED_REVIEW_MANIFEST_PATH`,
`NODE2C_ACCEPTED_REVIEW_MANIFEST_SHA256`,
`NODE2C_SPLIT_REVIEW_VALIDATOR`,
`NODE2C_SPLIT_REVIEW_MANIFEST_PATH`,
`NODE2C_SPLIT_REVIEW_MANIFEST_SHA256`, and
`NODE2C_SPLIT_REVIEW_BUNDLE_SHA256SUMS_PATH`. Step 8 recomputes the local
checkpoint digest from its bytes, runs the v6 checkpoint validator, verifies the
sealed split validator source (`SHA256SUMS` seal
`bb7f92076e3c242cf1bfc8e1f741d4c40b4eb202079576e637f6023ce3491794`), and
calls `validate_review_manifest(..., require_pass=True)` on the split package.
Neither package path nor digest is inferred from ambient state, a review
scalar, or a caller-supplied digest without re-reading the named bytes. The
split package is coordinator-side operational evidence and remains distinct
from the local v6 checkpoint; it is not a third Node 2 receipt.

```bash
set -Eeuo pipefail
umask 077

reject_node2c_git_environment_controls() {
    local name
    for name in \
        GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE \
        GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES \
        GIT_GRAFT_FILE GIT_REPLACE_REF_BASE GIT_CONFIG_PARAMETERS \
        GIT_CONFIG_COUNT
    do
        if [[ -v $name ]]; then
            printf 'node2c git controls: inherited %s is forbidden\n' \
                "$name" >&2 || :
            return 64
        fi
    done
    if [[ -v GIT_NO_REPLACE_OBJECTS && \
          ${GIT_NO_REPLACE_OBJECTS-} != 1 ]]; then
        printf '%s\n' \
            'node2c git controls: GIT_NO_REPLACE_OBJECTS must be unset or exactly 1' \
            >&2 || :
        return 64
    fi
}
readonly -f reject_node2c_git_environment_controls

assert_node2c_git_controls() {
    # Keep xtrace from exposing checked values and restore caller options on
    # every return from this function.
    local -
    set +x

    local node2c_refs=''
    local node2c_common_dir=''
    local node2c_shallow_state=''
    local node2c_producer_status=0
    local node2c_no_replace_declaration=''

    if [[ ${GIT_NO_REPLACE_OBJECTS-} != '1' ]]; then
        printf '%s\n' \
            'node2c git controls: GIT_NO_REPLACE_OBJECTS must equal 1' >&2 || :
        return 1
    fi

    if node2c_no_replace_declaration=$(builtin declare -p \
        GIT_NO_REPLACE_OBJECTS 2>/dev/null); then
        :
    else
        printf '%s\n' \
            'node2c git controls: GIT_NO_REPLACE_OBJECTS must equal 1 and be exported' >&2 || :
        return 1
    fi

    if [[ $node2c_no_replace_declaration \
        != declare\ -*x*\ GIT_NO_REPLACE_OBJECTS=* ]]; then
        printf '%s\n' \
            'node2c git controls: GIT_NO_REPLACE_OBJECTS must equal 1 and be exported' >&2 || :
        return 1
    fi

    if [[ -n ${GIT_GRAFT_FILE-} ]]; then
        printf '%s\n' \
            'node2c git controls: GIT_GRAFT_FILE must be unset or empty' >&2 || :
        return 1
    fi

    if [[ -n ${GIT_REPLACE_REF_BASE-} ]]; then
        printf '%s\n' \
            'node2c git controls: GIT_REPLACE_REF_BASE must be unset or empty' >&2 || :
        return 1
    fi

    if node2c_refs=$(command git for-each-ref \
        '--format=%(refname)' 'refs/replace/' 2>/dev/null); then
        :
    else
        node2c_producer_status=$?
        printf '%s\n' \
            'node2c git controls: could not enumerate replacement refs' >&2 || :
        return "$node2c_producer_status"
    fi

    if [[ -n $node2c_refs ]]; then
        printf '%s\n' \
            'node2c git controls: replacement refs are present' >&2 || :
        return 1
    fi

    if node2c_common_dir=$(command git rev-parse \
        '--path-format=absolute' '--git-common-dir' 2>/dev/null); then
        :
    else
        node2c_producer_status=$?
        printf '%s\n' \
            'node2c git controls: could not resolve the Git common directory' >&2 || :
        return "$node2c_producer_status"
    fi

    if [[ -z $node2c_common_dir || $node2c_common_dir != /* \
        || $node2c_common_dir == *$'\n'* ]]; then
        printf '%s\n' \
            'node2c git controls: Git common-directory result is invalid' >&2 || :
        return 1
    fi

    if [[ -e $node2c_common_dir/info/grafts \
        || -L $node2c_common_dir/info/grafts ]]; then
        printf '%s\n' \
            'node2c git controls: common-directory info/grafts is present' >&2 || :
        return 1
    fi

    if node2c_shallow_state=$(command git rev-parse \
        '--is-shallow-repository' 2>/dev/null); then
        :
    else
        node2c_producer_status=$?
        printf '%s\n' \
            'node2c git controls: could not determine shallow state' >&2 || :
        return "$node2c_producer_status"
    fi

    case "$node2c_shallow_state" in
        false)
            ;;
        true)
            printf '%s\n' \
                'node2c git controls: repository is shallow' >&2 || :
            return 1
            ;;
        *)
            printf '%s\n' \
                'node2c git controls: shallow-state query returned an invalid result' >&2 || :
            return 1
            ;;
    esac

    return 0
}
readonly -f assert_node2c_git_controls

reject_node2c_git_environment_controls
export GIT_NO_REPLACE_OBJECTS=1
readonly GIT_NO_REPLACE_OBJECTS
assert_node2c_git_controls

NODE2C_PUBLICATION_ACTION="${NODE2C_PUBLICATION_ACTION:?set NODE2C_PUBLICATION_ACTION to publish, recover, or complete}"
case "$NODE2C_PUBLICATION_ACTION" in
  publish | recover | complete) ;;
  *) printf 'invalid Node 2C publication action: %s\n' "$NODE2C_PUBLICATION_ACTION" >&2; exit 64 ;;
esac
readonly NODE2C_PUBLICATION_ACTION

NODE_PATHS=(
  src/polymarket_alpha_lab/team_evidence_aggregation.py
  tests/test_team_evidence_aggregation.py
  tests/test_team_evidence_aggregation_scope.py
)
EXPECTED_NODE_PATHS="$(printf '%s\n' "${NODE_PATHS[@]}")"
SORTED_NODE_PATHS="$(printf '%s\n' "${NODE_PATHS[@]}" | LC_ALL=C sort)"
test "$SORTED_NODE_PATHS" = "$EXPECTED_NODE_PATHS"
readonly -a NODE_PATHS
readonly EXPECTED_NODE_PATHS SORTED_NODE_PATHS

NODE2C_ENTRY_REPO="$(git rev-parse --show-toplevel 2>/dev/null)"
NODE2C_ENTRY_COMMON_GIT_DIR="$(
  git -C "$NODE2C_ENTRY_REPO" rev-parse \
    --path-format=absolute --git-common-dir 2>/dev/null
)"
NODE2C_PUBLICATION_STATE_FILE="$NODE2C_ENTRY_COMMON_GIT_DIR/node2c-publication.state"
NODE2C_OBSERVER_CAPTURE_LIMIT_BYTES=4096
NODE2C_OBSERVER_CAPTURE_LIMIT_BLOCKS=4
readonly NODE2C_ENTRY_REPO NODE2C_ENTRY_COMMON_GIT_DIR \
  NODE2C_PUBLICATION_STATE_FILE NODE2C_OBSERVER_CAPTURE_LIMIT_BYTES \
  NODE2C_OBSERVER_CAPTURE_LIMIT_BLOCKS

persist_node2c_state_durably() {
  local -
  local mode=${1:-replace}
  local link_status state_dir state_tmp state_field state_value

  case "$mode" in
    create | replace) ;;
    *) return 64 ;;
  esac

  if [[ "$mode" == replace && -f "$NODE2C_PUBLICATION_STATE_FILE" &&
        ! -L "$NODE2C_PUBLICATION_STATE_FILE" ]]; then
    local previous_publication_status
    previous_publication_status="$(
      read_node2c_state_field REMOTE_PUBLICATION_STATUS
    )" || return 74
    case "$previous_publication_status" in
      superseded | not_published | divergent)
        [[ "$REMOTE_PUBLICATION_STATUS" == "$previous_publication_status" ]] ||
          return 76
        ;;
    esac
  fi

  for state_field in \
    LOCAL_HEAD NODE2C_REPO NODE2C_REMOTE NODE2C_REMOTE_REF NODE_BASE \
    PRE_PUSH_REMOTE_SHA PUSH_ATTEMPTED PUSH_STATUS \
    REMOTE_PUBLICATION_STATUS OBSERVED_LOCAL_HEAD OBSERVED_ENDPOINT_SHA \
    OBSERVATION_RESULT OBSERVER_STATUS OBSERVER_FAILURE_STAGE \
    FORWARD_MERGE_BASE_STATUS REVERSE_MERGE_BASE_STATUS
  do
    state_value=${!state_field}
    [[ "$state_value" != *$'\n'* && "$state_value" != *$'\t'* ]] || return 74
  done

  state_dir=${NODE2C_PUBLICATION_STATE_FILE%/*}
  state_tmp="$(mktemp "$state_dir/.node2c-publication.state.XXXXXX")" || return 70
  chmod 600 "$state_tmp" || {
    rm -f -- "$state_tmp"
    return 70
  }
  {
    printf 'STATE_VERSION\t1\n'
    printf 'LOCAL_HEAD\t%s\n' "$LOCAL_HEAD"
    printf 'NODE2C_REPO\t%s\n' "$NODE2C_REPO"
    printf 'NODE2C_REMOTE\t%s\n' "$NODE2C_REMOTE"
    printf 'NODE2C_REMOTE_REF\t%s\n' "$NODE2C_REMOTE_REF"
    printf 'NODE_BASE\t%s\n' "$NODE_BASE"
    printf 'PRE_PUSH_REMOTE_SHA\t%s\n' "$PRE_PUSH_REMOTE_SHA"
    printf 'PUSH_ATTEMPTED\t%s\n' "$PUSH_ATTEMPTED"
    printf 'PUSH_STATUS\t%s\n' "$PUSH_STATUS"
    printf 'REMOTE_PUBLICATION_STATUS\t%s\n' "$REMOTE_PUBLICATION_STATUS"
    printf 'OBSERVED_LOCAL_HEAD\t%s\n' "$OBSERVED_LOCAL_HEAD"
    printf 'OBSERVED_ENDPOINT_SHA\t%s\n' "$OBSERVED_ENDPOINT_SHA"
    printf 'OBSERVATION_RESULT\t%s\n' "$OBSERVATION_RESULT"
    printf 'OBSERVER_STATUS\t%s\n' "$OBSERVER_STATUS"
    printf 'OBSERVER_FAILURE_STAGE\t%s\n' "$OBSERVER_FAILURE_STAGE"
    printf 'FORWARD_MERGE_BASE_STATUS\t%s\n' "$FORWARD_MERGE_BASE_STATUS"
    printf 'REVERSE_MERGE_BASE_STATUS\t%s\n' "$REVERSE_MERGE_BASE_STATUS"
  } > "$state_tmp" || {
    rm -f -- "$state_tmp"
    return 70
  }
  sync -f "$state_tmp" || {
    rm -f -- "$state_tmp"
    return 70
  }
  if [[ "$mode" == create ]]; then
    set +e
    ln -- "$state_tmp" "$NODE2C_PUBLICATION_STATE_FILE" \
      >/dev/null 2>&1
    link_status=$?
    set -e
    if ((link_status != 0)); then
      rm -f -- "$state_tmp" >/dev/null 2>&1 || :
      if [[ -e "$NODE2C_PUBLICATION_STATE_FILE" ||
            -L "$NODE2C_PUBLICATION_STATE_FILE" ]]; then
        return 73
      fi
      return "$link_status"
    fi
    sync -f "$state_dir" || return 70
    rm -f -- "$state_tmp" >/dev/null 2>&1 || return 70
    sync -f "$state_dir" || return 70
  else
    mv -f -- "$state_tmp" "$NODE2C_PUBLICATION_STATE_FILE" \
      >/dev/null 2>&1 || {
      rm -f -- "$state_tmp" >/dev/null 2>&1 || :
      return 70
    }
    sync -f "$state_dir" || return 70
  fi
}

read_node2c_state_field() {
  local wanted=$1
  local line key value found=0

  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ "$line" == *$'\t'* ]] || return 74
    key=${line%%$'\t'*}
    value=${line#*$'\t'}
    if [[ "$key" == "$wanted" ]]; then
      ((found == 0)) || return 74
      [[ "$value" != *$'\n'* && "$value" != *$'\t'* ]] || return 74
      printf '%s\n' "$value"
      found=1
    fi
  done < "$NODE2C_PUBLICATION_STATE_FILE"
  ((found == 1))
}

load_node2c_state() {
  local state_field state_value read_status persisted_common_git_dir

  [[ -f "$NODE2C_PUBLICATION_STATE_FILE" &&
     ! -L "$NODE2C_PUBLICATION_STATE_FILE" ]] || return 74
  for state_field in \
    STATE_VERSION LOCAL_HEAD NODE2C_REPO NODE2C_REMOTE NODE2C_REMOTE_REF \
    NODE_BASE PRE_PUSH_REMOTE_SHA PUSH_ATTEMPTED PUSH_STATUS \
    REMOTE_PUBLICATION_STATUS OBSERVED_LOCAL_HEAD OBSERVED_ENDPOINT_SHA \
    OBSERVATION_RESULT OBSERVER_STATUS OBSERVER_FAILURE_STAGE \
    FORWARD_MERGE_BASE_STATUS REVERSE_MERGE_BASE_STATUS
  do
    state_value="$(read_node2c_state_field "$state_field")"
    read_status=$?
    ((read_status == 0)) || return 74
    printf -v "$state_field" '%s' "$state_value"
  done

  [[ "$STATE_VERSION" == 1 ]] || return 74
  [[ "$LOCAL_HEAD" =~ ^([0-9a-f]{40}|[0-9a-f]{64})$ ]] || return 74
  [[ "$NODE_BASE" =~ ^([0-9a-f]{40}|[0-9a-f]{64})$ ]] || return 74
  [[ "$PRE_PUSH_REMOTE_SHA" =~ ^([0-9a-f]{40}|[0-9a-f]{64})$ ]] || return 74
  [[ -n "$NODE2C_REPO" && -d "$NODE2C_REPO" ]] || return 74
  [[ -n "$NODE2C_REMOTE" && "$NODE2C_REMOTE_REF" == refs/heads/main ]] || return 74
  [[ "$PUSH_ATTEMPTED" == true ]] || return 74
  case "$REMOTE_PUBLICATION_STATUS" in
    indeterminate | published | superseded | not_published | divergent) ;;
    *) return 74 ;;
  esac

  persisted_common_git_dir="$(
    git -C "$NODE2C_REPO" rev-parse \
      --path-format=absolute --git-common-dir 2>/dev/null
  )"
  read_status=$?
  ((read_status == 0)) || return 74
  [[ "$persisted_common_git_dir" == "$NODE2C_ENTRY_COMMON_GIT_DIR" ]] || return 74
  git -C "$NODE2C_REPO" cat-file -e "$LOCAL_HEAD^{commit}" 2>/dev/null
  read_status=$?
  ((read_status == 0)) || return 74
}

configure_node2c_git_auth() {
  local auth_status

  NODE2C_COMMON_GIT_DIR="$(
    git -C "$NODE2C_REPO" rev-parse \
      --path-format=absolute --git-common-dir 2>/dev/null
  )"
  auth_status=$?
  ((auth_status == 0)) || return "$auth_status"
  GIT_AUTH=(
    -c credential.helper=
    -c "credential.helper=store --file=$NODE2C_COMMON_GIT_DIR/github-credentials"
  )
}

capture_node2c_bounded() {
  local -
  local output_name=$1
  local capture_file capture_size captured_text
  local capture_status producer_status remove_status
  shift
  set +e

  capture_file="$(
    mktemp \
      "$NODE2C_ENTRY_COMMON_GIT_DIR/.node2c-observer-output.XXXXXX" \
      2>/dev/null
  )"
  capture_status=$?
  if ((capture_status != 0)); then
    return "$capture_status"
  fi
  chmod 600 "$capture_file" >/dev/null 2>&1
  capture_status=$?
  if ((capture_status != 0)); then
    rm -f -- "$capture_file" >/dev/null 2>&1 || :
    return 70
  fi

  (
    ulimit -f "$NODE2C_OBSERVER_CAPTURE_LIMIT_BLOCKS"
    capture_status=$?
    ((capture_status == 0)) || exit "$capture_status"
    "$@" > "$capture_file" 2>/dev/null
  )
  producer_status=$?
  if ((producer_status != 0)); then
    rm -f -- "$capture_file" >/dev/null 2>&1 || :
    return "$producer_status"
  fi

  capture_size="$(stat -c '%s' -- "$capture_file" 2>/dev/null)"
  capture_status=$?
  if ((capture_status != 0)); then
    rm -f -- "$capture_file" >/dev/null 2>&1 || :
    return "$capture_status"
  fi
  if [[ ! "$capture_size" =~ ^[0-9]+$ ]] ||
    ((capture_size > NODE2C_OBSERVER_CAPTURE_LIMIT_BYTES)); then
    rm -f -- "$capture_file" >/dev/null 2>&1 || :
    return 74
  fi

  captured_text="$(
    command cat -- "$capture_file" 2>/dev/null
    capture_status=$?
    printf '\036'
    exit "$capture_status"
  )"
  capture_status=$?
  rm -f -- "$capture_file" >/dev/null 2>&1
  remove_status=$?
  ((capture_status == 0)) || return "$capture_status"
  ((remove_status == 0)) || return 70
  captured_text=${captured_text%$'\036'}
  printf -v "$output_name" '%s' "$captured_text"
}

retry_capture_node2c() {
  local -
  local output_name=$1
  local output producer_status=74
  local attempt
  shift
  set +e

  for attempt in 1 2 3; do
    : "$attempt"
    capture_node2c_bounded output "$@"
    producer_status=$?
    if ((producer_status == 0)); then
      printf -v "$output_name" '%s' "$output"
      return 0
    fi
  done
  return "$producer_status"
}

retry_node2c() {
  local -
  local producer_status=74
  local attempt
  set +e

  for attempt in 1 2 3; do
    : "$attempt"
    "$@"
    producer_status=$?
    if ((producer_status == 0)); then
      return 0
    fi
  done
  return "$producer_status"
}

node2c_get_remote_endpoint() {
  git -C "$NODE2C_REPO" remote get-url --push --all origin 2>/dev/null
}

node2c_ls_remote_main() {
  GIT_TERMINAL_PROMPT=0 git -C "$NODE2C_REPO" "${GIT_AUTH[@]}" \
    ls-remote --exit-code "$NODE2C_REMOTE" "$NODE2C_REMOTE_REF" \
    2>/dev/null
}

node2c_fetch_remote_main() {
  GIT_TERMINAL_PROMPT=0 git -C "$NODE2C_REPO" "${GIT_AUTH[@]}" \
    fetch --no-tags --no-recurse-submodules --quiet \
    "$NODE2C_REMOTE" "$NODE2C_REMOTE_REF" >/dev/null 2>&1
}

node2c_resolve_fetch_head() {
  git -C "$NODE2C_REPO" rev-parse --verify 'FETCH_HEAD^{commit}' \
    2>/dev/null
}

parse_node2c_ls_remote() {
  local output=$1
  local expected_ref=$2
  local output_name=$3
  local record sha ref

  [[ "$output" == *$'\n' ]] || return 74
  record=${output%$'\n'}
  [[ "$record" != *$'\n'* && "$record" == *$'\t'* ]] || return 74
  sha=${record%%$'\t'*}
  ref=${record#*$'\t'}
  [[ "$sha" =~ ^([0-9a-f]{40}|[0-9a-f]{64})$ &&
     "$ref" == "$expected_ref" ]] || return 74
  printf -v "$output_name" '%s' "$sha"
}

observe_node2c_remote_main() {
  local first_output first_sha fetched_output fetched_sha
  local second_output second_sha producer_status parse_status
  local bound_local_head=$LOCAL_HEAD

  OBSERVED_LOCAL_HEAD=
  OBSERVED_ENDPOINT_SHA=
  OBSERVER_FAILURE_STAGE=

  retry_capture_node2c first_output node2c_ls_remote_main
  producer_status=$?
  if ((producer_status != 0)); then
    OBSERVER_FAILURE_STAGE=first-ls-remote
    return "$producer_status"
  fi
  parse_node2c_ls_remote "$first_output" "$NODE2C_REMOTE_REF" first_sha
  parse_status=$?
  if ((parse_status != 0)); then
    OBSERVER_FAILURE_STAGE=first-ls-remote-output
    return 74
  fi

  retry_node2c node2c_fetch_remote_main
  producer_status=$?
  if ((producer_status != 0)); then
    OBSERVER_FAILURE_STAGE=fetch
    return "$producer_status"
  fi

  retry_capture_node2c fetched_output node2c_resolve_fetch_head
  producer_status=$?
  if ((producer_status != 0)); then
    OBSERVER_FAILURE_STAGE=fetch-head-rev-parse
    return "$producer_status"
  fi
  if [[ "$fetched_output" != *$'\n' ]]; then
    OBSERVER_FAILURE_STAGE=fetch-head-rev-parse-output
    return 74
  fi
  fetched_sha=${fetched_output%$'\n'}
  if [[ "$fetched_sha" == *$'\n'* ||
        ! "$fetched_sha" =~ ^([0-9a-f]{40}|[0-9a-f]{64})$ ||
        "$fetched_sha" != "$first_sha" ]]; then
    OBSERVER_FAILURE_STAGE=fetch-head-rev-parse-output
    return 74
  fi

  retry_capture_node2c second_output node2c_ls_remote_main
  producer_status=$?
  if ((producer_status != 0)); then
    OBSERVER_FAILURE_STAGE=second-ls-remote
    return "$producer_status"
  fi
  parse_node2c_ls_remote "$second_output" "$NODE2C_REMOTE_REF" second_sha
  parse_status=$?
  if ((parse_status != 0)); then
    OBSERVER_FAILURE_STAGE=second-ls-remote-output
    return 74
  fi
  if [[ "$second_sha" != "$first_sha" ]]; then
    OBSERVER_FAILURE_STAGE=second-ls-remote-output
    return 74
  fi

  OBSERVED_LOCAL_HEAD=$bound_local_head
  OBSERVED_ENDPOINT_SHA=$second_sha
}

node2c_merge_base_is_ancestor() {
  local direction=$1
  local left=$2
  local right=$3
  : "$direction"
  git -C "$NODE2C_REPO" merge-base --is-ancestor "$left" "$right" \
    2>/dev/null
}

classify_node2c_observation() {
  local merge_status

  FORWARD_MERGE_BASE_STATUS=
  REVERSE_MERGE_BASE_STATUS=

  node2c_merge_base_is_ancestor \
    forward "$OBSERVED_LOCAL_HEAD" "$OBSERVED_ENDPOINT_SHA"
  merge_status=$?
  FORWARD_MERGE_BASE_STATUS=$merge_status
  case "$merge_status" in
    0)
      OBSERVER_STATUS=0
      OBSERVER_FAILURE_STAGE=
      if [[ "$OBSERVED_LOCAL_HEAD" == "$OBSERVED_ENDPOINT_SHA" ]]; then
        REMOTE_PUBLICATION_STATUS=published
        OBSERVATION_RESULT=published-exact
      else
        REMOTE_PUBLICATION_STATUS=superseded
        OBSERVATION_RESULT=superseded
      fi
      return 0
      ;;
    1) ;;
    *)
      REMOTE_PUBLICATION_STATUS=indeterminate
      OBSERVATION_RESULT=forward-merge-base-error
      OBSERVER_STATUS=$merge_status
      OBSERVER_FAILURE_STAGE=forward-merge-base
      return "$merge_status"
      ;;
  esac

  node2c_merge_base_is_ancestor \
    reverse "$OBSERVED_ENDPOINT_SHA" "$OBSERVED_LOCAL_HEAD"
  merge_status=$?
  REVERSE_MERGE_BASE_STATUS=$merge_status
  case "$merge_status" in
    0)
      REMOTE_PUBLICATION_STATUS=not_published
      OBSERVATION_RESULT=remote-ancestor
      OBSERVER_STATUS=0
      OBSERVER_FAILURE_STAGE=
      return 0
      ;;
    1)
      REMOTE_PUBLICATION_STATUS=divergent
      OBSERVATION_RESULT=divergent
      OBSERVER_STATUS=0
      OBSERVER_FAILURE_STAGE=
      return 0
      ;;
    *)
      REMOTE_PUBLICATION_STATUS=indeterminate
      OBSERVATION_RESULT=reverse-merge-base-error
      OBSERVER_STATUS=$merge_status
      OBSERVER_FAILURE_STAGE=reverse-merge-base
      return "$merge_status"
      ;;
  esac
}

persist_node2c_observer_failure() {
  local observer_status=$1
  local persistence_status

  persist_node2c_state_durably
  persistence_status=$?
  if ((persistence_status != 0)); then
    printf 'failed to persist Node 2C observer status %s\n' \
      "$observer_status" >&2
  fi
  return "$observer_status"
}

verify_node2c_accepted_review_manifest() {
  : "${NODE2C_ACCEPTED_REVIEW_MANIFEST_BIN:?manifest validator path is required}"
  : "${NODE2C_ACCEPTED_REVIEW_OUTPUT_DIR:?manifest output directory is required}"
  /usr/bin/python3 "$NODE2C_ACCEPTED_REVIEW_MANIFEST_BIN" verify \
    --output-dir "$NODE2C_ACCEPTED_REVIEW_OUTPUT_DIR" >/dev/null
}

verify_node2c_accepted_review_manifest_handoff() {
  : "${NODE2C_ACCEPTED_REVIEW_MANIFEST_BIN:?manifest validator path is required}"
  : "${NODE2C_ACCEPTED_REVIEW_OUTPUT_DIR:?checkpoint output directory is required}"
  : "${NODE2C_ACCEPTED_REVIEW_MANIFEST_PATH:?checkpoint manifest path is required}"
  : "${NODE2C_ACCEPTED_REVIEW_MANIFEST_SHA256:?checkpoint manifest digest is required}"
  for checkpoint_path in \
    "$NODE2C_ACCEPTED_REVIEW_MANIFEST_BIN" \
    "$NODE2C_ACCEPTED_REVIEW_OUTPUT_DIR" \
    "$NODE2C_ACCEPTED_REVIEW_MANIFEST_PATH"; do
    case "$checkpoint_path" in
      /*) ;;
      *) printf 'checkpoint handoff path must be absolute\n' >&2; return 64 ;;
    esac
  done
  [ -d "$NODE2C_ACCEPTED_REVIEW_OUTPUT_DIR" ] || return 64
  [ -f "$NODE2C_ACCEPTED_REVIEW_MANIFEST_PATH" ] || return 64
  [ ! -L "$NODE2C_ACCEPTED_REVIEW_MANIFEST_PATH" ] || return 64
  NODE2C_CHECKPOINT_MANIFEST_DIGEST="$(
    sha256sum -- "$NODE2C_ACCEPTED_REVIEW_MANIFEST_PATH" | awk '{print $1}'
  )"
  [[ "$NODE2C_CHECKPOINT_MANIFEST_DIGEST" =~ ^[0-9a-f]{64}$ ]] || return 64
  [ "$NODE2C_CHECKPOINT_MANIFEST_DIGEST" = \
    "$NODE2C_ACCEPTED_REVIEW_MANIFEST_SHA256" ] || return 65
  verify_node2c_accepted_review_manifest
}

verify_node2c_split_review_manifest_handoff() {
  : "${NODE2C_SPLIT_REVIEW_VALIDATOR:?split review validator path is required}"
  : "${NODE2C_SPLIT_REVIEW_MANIFEST_PATH:?split review manifest path is required}"
  : "${NODE2C_SPLIT_REVIEW_MANIFEST_SHA256:?split review manifest digest is required}"
  : "${NODE2C_SPLIT_REVIEW_BUNDLE_SHA256SUMS_PATH:?split review seal path is required}"
  for split_path in \
    "$NODE2C_SPLIT_REVIEW_VALIDATOR" \
    "$NODE2C_SPLIT_REVIEW_MANIFEST_PATH" \
    "$NODE2C_SPLIT_REVIEW_BUNDLE_SHA256SUMS_PATH"; do
    case "$split_path" in
      /*) ;;
      *) printf 'split review handoff path must be absolute\n' >&2; return 64 ;;
    esac
  done
  [ -f "$NODE2C_SPLIT_REVIEW_VALIDATOR" ] &&
    [ ! -L "$NODE2C_SPLIT_REVIEW_VALIDATOR" ] || return 64
  [ -f "$NODE2C_SPLIT_REVIEW_MANIFEST_PATH" ] &&
    [ ! -L "$NODE2C_SPLIT_REVIEW_MANIFEST_PATH" ] || return 64
  [ "$(sha256sum -- "$NODE2C_SPLIT_REVIEW_BUNDLE_SHA256SUMS_PATH" | awk '{print $1}')" = \
    bb7f92076e3c242cf1bfc8e1f741d4c40b4eb202079576e637f6023ce3491794 ] || return 65
  NODE2C_SPLIT_REVIEW_SOURCE_SHA256="$(sha256sum -- "$NODE2C_SPLIT_REVIEW_VALIDATOR" | awk '{print $1}')"
  [ "$NODE2C_SPLIT_REVIEW_SOURCE_SHA256" = \
    e72270afc736abaa601e2e917a6c90755e547e0b12c812ce5c12c8049e93d09c ] || return 65
  NODE2C_SPLIT_REVIEW_PACKAGE_DIR="$(dirname -- "$NODE2C_SPLIT_REVIEW_MANIFEST_PATH")"
  NODE2C_SPLIT_REVIEW_EXPECTED_HEAD="${LOCAL_HEAD:?local review head is required}"
  NODE2C_SPLIT_REVIEW_VALIDATOR="$NODE2C_SPLIT_REVIEW_VALIDATOR" \
  NODE2C_SPLIT_REVIEW_PACKAGE_DIR="$NODE2C_SPLIT_REVIEW_PACKAGE_DIR" \
  NODE2C_SPLIT_REVIEW_MANIFEST_PATH="$NODE2C_SPLIT_REVIEW_MANIFEST_PATH" \
  NODE2C_SPLIT_REVIEW_MANIFEST_SHA256="$NODE2C_SPLIT_REVIEW_MANIFEST_SHA256" \
  NODE2C_SPLIT_REVIEW_EXPECTED_BASE="${NODE_BASE:?immutable base is required}" \
  NODE2C_SPLIT_REVIEW_EXPECTED_HEAD="$NODE2C_SPLIT_REVIEW_EXPECTED_HEAD" \
    /usr/bin/python3 - <<'PY'
import hashlib
import importlib.util
import os
import sys
from pathlib import Path

validator_path = Path(os.environ["NODE2C_SPLIT_REVIEW_VALIDATOR"])
spec = importlib.util.spec_from_file_location("node2c_split_manifest", validator_path)
if spec is None or spec.loader is None:
    raise SystemExit("split review validator could not be loaded")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
manifest_path = Path(os.environ["NODE2C_SPLIT_REVIEW_MANIFEST_PATH"])
source = manifest_path.read_bytes()
if hashlib.sha256(source).hexdigest() != os.environ["NODE2C_SPLIT_REVIEW_MANIFEST_SHA256"]:
    raise SystemExit("split review manifest digest does not match retained bytes")
module.validate_review_manifest(
    package_dir=Path(os.environ["NODE2C_SPLIT_REVIEW_PACKAGE_DIR"]),
    expected_manifest_sha256=os.environ["NODE2C_SPLIT_REVIEW_MANIFEST_SHA256"],
    expected_node_base=os.environ["NODE2C_SPLIT_REVIEW_EXPECTED_BASE"],
    expected_gated_head=os.environ["NODE2C_SPLIT_REVIEW_EXPECTED_HEAD"],
    require_pass=True,
)
PY
}

publish_node2c_main() {
  local push_status state_status

  [[ "$LOCAL_HEAD" =~ ^([0-9a-f]{40}|[0-9a-f]{64})$ ]] || return 74
  PUSH_ATTEMPTED=true
  PUSH_STATUS=
  REMOTE_PUBLICATION_STATUS=indeterminate
  OBSERVED_LOCAL_HEAD=
  OBSERVED_ENDPOINT_SHA=
  OBSERVATION_RESULT=
  OBSERVER_STATUS=
  OBSERVER_FAILURE_STAGE=
  FORWARD_MERGE_BASE_STATUS=
  REVERSE_MERGE_BASE_STATUS=

  persist_node2c_state_durably create
  state_status=$?
  ((state_status == 0)) || return "$state_status"

  set -e
  assert_node2c_git_controls
  set +e
  GIT_TERMINAL_PROMPT=0 git -C "$NODE2C_REPO" "${GIT_AUTH[@]}" push \
    --no-force --no-force-with-lease --no-force-if-includes --no-follow-tags \
    --no-recurse-submodules \
    "$NODE2C_REMOTE" "$LOCAL_HEAD:$NODE2C_REMOTE_REF" \
    >/dev/null 2>&1
  push_status=$?
  PUSH_STATUS=$push_status
  REMOTE_PUBLICATION_STATUS=indeterminate
  OBSERVATION_RESULT=push-returned-unobserved

  persist_node2c_state_durably
  state_status=$?
  if ((state_status != 0)); then
    printf 'Node 2C publication category: push_status_persistence_error\n' >&2
    ((push_status != 0)) && return "$push_status"
    return "$state_status"
  fi
  return "$push_status"
}

recover_node2c_publication() {
  local load_status auth_status observer_status classification_status
  local persistence_status

  load_node2c_state
  load_status=$?
  ((load_status == 0)) || return "$load_status"
  verify_node2c_accepted_review_manifest_handoff || return $?
  verify_node2c_split_review_manifest_handoff || return $?
  case "$REMOTE_PUBLICATION_STATUS" in
    superseded | not_published | divergent)
      printf 'Node 2C publication classification is terminal: %s\n' \
        "$REMOTE_PUBLICATION_STATUS" >&2
      return 76
      ;;
    indeterminate | published) ;;
    *) return 74 ;;
  esac
  configure_node2c_git_auth
  auth_status=$?
  ((auth_status == 0)) || return "$auth_status"
  set -e
  assert_node2c_git_controls
  set +e

  trap 'exit 130' INT
  trap 'exit 143' TERM
  trap 'exit 129' HUP

  REMOTE_PUBLICATION_STATUS=indeterminate
  OBSERVED_LOCAL_HEAD=
  OBSERVED_ENDPOINT_SHA=
  OBSERVATION_RESULT=
  OBSERVER_STATUS=
  OBSERVER_FAILURE_STAGE=
  FORWARD_MERGE_BASE_STATUS=
  REVERSE_MERGE_BASE_STATUS=

  observe_node2c_remote_main
  observer_status=$?
  if ((observer_status != 0)); then
    REMOTE_PUBLICATION_STATUS=indeterminate
    OBSERVATION_RESULT=observer-producer-or-output-failure
    OBSERVER_STATUS=$observer_status
    persist_node2c_observer_failure "$observer_status"
    return $?
  fi

  classify_node2c_observation
  classification_status=$?
  if ((classification_status != 0)); then
    persist_node2c_observer_failure "$classification_status"
    return $?
  fi

  persist_node2c_state_durably
  persistence_status=$?
  ((persistence_status == 0)) || return "$persistence_status"
  set -e
  assert_node2c_git_controls
  set +e
  printf 'Node 2C publication observation category: %s\n' \
    "$OBSERVATION_RESULT"
}

complete_node2c_publication() {
  local load_status auth_status observer_status classification_status
  local persistence_status

  load_node2c_state
  load_status=$?
  ((load_status == 0)) || return "$load_status"
  verify_node2c_accepted_review_manifest_handoff || return $?
  verify_node2c_split_review_manifest_handoff || return $?
  [[ "$PRE_PUSH_REMOTE_SHA" == "$NODE_BASE" ]] || return 1
  [[ "$PUSH_ATTEMPTED" == true ]] || return 1
  [[ "$REMOTE_PUBLICATION_STATUS" == published ]] || return 1
  configure_node2c_git_auth
  auth_status=$?
  ((auth_status == 0)) || return "$auth_status"
  set -e
  assert_node2c_git_controls
  set +e

  OBSERVED_LOCAL_HEAD=
  OBSERVED_ENDPOINT_SHA=
  OBSERVATION_RESULT=
  OBSERVER_STATUS=
  OBSERVER_FAILURE_STAGE=
  FORWARD_MERGE_BASE_STATUS=
  REVERSE_MERGE_BASE_STATUS=

  observe_node2c_remote_main
  observer_status=$?
  if ((observer_status != 0)); then
    REMOTE_PUBLICATION_STATUS=indeterminate
    OBSERVATION_RESULT=observer-producer-or-output-failure
    OBSERVER_STATUS=$observer_status
    persist_node2c_observer_failure "$observer_status"
    return $?
  fi

  classify_node2c_observation
  classification_status=$?
  if ((classification_status != 0)); then
    persist_node2c_observer_failure "$classification_status"
    return $?
  fi

  persist_node2c_state_durably
  persistence_status=$?
  ((persistence_status == 0)) || return "$persistence_status"
  if [[ "$REMOTE_PUBLICATION_STATUS" != published ||
        "$OBSERVATION_RESULT" != published-exact ||
        "$OBSERVED_LOCAL_HEAD" != "$LOCAL_HEAD" ||
        "$OBSERVED_ENDPOINT_SHA" != "$LOCAL_HEAD" ]]; then
    return 76
  fi
  verify_node2c_accepted_review_manifest_handoff || return $?
  verify_node2c_split_review_manifest_handoff || return $?
  printf 'Node 2C publication category: complete\n'
}

case "$NODE2C_PUBLICATION_ACTION" in
  publish)
    : "${GATED_HEAD:?final GATED_HEAD is required}"
    : "${NODE2C_REVIEW_FIX_COUNT:?review-fix count is required}"
    : "${NODE_BASE:?immutable Node 2C base is required}"
    : "${NODE2C_REVIEWED_PLAN_BLOB:?reviewed plan blob is required}"
    : "${NODE2C_REVIEWED_DESIGN_BLOB:?reviewed design blob is required}"
    : "${NODE2C_GOVERNANCE_REMOTE_ENDPOINT_SHA256:?governance endpoint digest is required}"
    : "${NODE2C_GOVERNANCE_REVIEW_REPORT_SHA256:?governance report digest is required}"
    : "${NODE2C_ACCEPTED_REVIEW_MANIFEST_BIN:?accepted-review manifest validator is required}"
    : "${NODE2C_ACCEPTED_REVIEW_OUTPUT_DIR:?checkpoint output directory is required}"
    : "${NODE2C_ACCEPTED_REVIEW_MANIFEST_PATH:?checkpoint manifest path is required}"
    : "${NODE2C_ACCEPTED_REVIEW_MANIFEST_SHA256:?checkpoint manifest digest is required}"
    : "${NODE2C_SPLIT_REVIEW_VALIDATOR:?split review validator is required}"
    : "${NODE2C_SPLIT_REVIEW_MANIFEST_PATH:?split review manifest path is required}"
    : "${NODE2C_SPLIT_REVIEW_MANIFEST_SHA256:?split review manifest digest is required}"
    : "${NODE2C_SPLIT_REVIEW_BUNDLE_SHA256SUMS_PATH:?split review seal is required}"
    test -n "${NODE2C_REVIEW_FIX_SHAS_TEXT+x}"
    test "$NODE2C_REVIEW_FIX_COUNT" -ge 0
    test "$GIT_NO_REPLACE_OBJECTS" = 1

    declare -F validate_governance_candidate_publication >/dev/null
    NODE2C_PREPUSH_GOVERNANCE_CANDIDATE_PUBLICATION_OUTPUT="$(
      validate_governance_candidate_publication
    )"
    mapfile -t NODE2C_PREPUSH_GOVERNANCE_CANDIDATE_PUBLICATION_LINES <<< \
      "$NODE2C_PREPUSH_GOVERNANCE_CANDIDATE_PUBLICATION_OUTPUT"
    test "${#NODE2C_PREPUSH_GOVERNANCE_CANDIDATE_PUBLICATION_LINES[@]}" -eq 6
    [[ "${NODE2C_PREPUSH_GOVERNANCE_CANDIDATE_PUBLICATION_LINES[0]}" == \
      GOVERNANCE_CANDIDATE_PUBLICATION_EVIDENCE=* ]]
    test "${NODE2C_PREPUSH_GOVERNANCE_CANDIDATE_PUBLICATION_LINES[1]}" = "$NODE_BASE"
    test "${NODE2C_PREPUSH_GOVERNANCE_CANDIDATE_PUBLICATION_LINES[2]}" = \
      "$NODE2C_REVIEWED_PLAN_BLOB"
    test "${NODE2C_PREPUSH_GOVERNANCE_CANDIDATE_PUBLICATION_LINES[3]}" = \
      "$NODE2C_REVIEWED_DESIGN_BLOB"
    test "${NODE2C_PREPUSH_GOVERNANCE_CANDIDATE_PUBLICATION_LINES[4]}" = \
      "$NODE2C_GOVERNANCE_REMOTE_ENDPOINT_SHA256"
    test "${NODE2C_PREPUSH_GOVERNANCE_CANDIDATE_PUBLICATION_LINES[5]}" = \
      "$NODE2C_GOVERNANCE_REVIEW_REPORT_SHA256"

    NODE2C_REPO=$NODE2C_ENTRY_REPO
    LOCAL_HEAD="$(
      git -C "$NODE2C_REPO" rev-parse --verify 'HEAD^{commit}' 2>/dev/null
    )"
    verify_node2c_accepted_review_manifest_handoff
    verify_node2c_split_review_manifest_handoff
    test "$LOCAL_HEAD" = "$NODE2C_SPLIT_REVIEW_EXPECTED_HEAD"
    # NODE2C_LOCAL_HEAD_FROZEN
    [[ "$LOCAL_HEAD" =~ ^([0-9a-f]{40}|[0-9a-f]{64})$ ]]
    set +e
    NODE2C_PREPUSH_PATHS="$(
      git -C "$NODE2C_REPO" diff --name-only "$NODE_BASE..$LOCAL_HEAD"
    )"
    NODE2C_PREPUSH_PATHS_STATUS=$?
    set -e
    if ((NODE2C_PREPUSH_PATHS_STATUS != 0)); then
      printf 'Node 2C publication category: range_path_error\n' >&2
      exit "$NODE2C_PREPUSH_PATHS_STATUS"
    fi
    test "$NODE2C_PREPUSH_PATHS" = "$EXPECTED_NODE_PATHS"
    NODE2C_PREPUSH_PATHS_SORTED="$(
      LC_ALL=C sort <<< "$NODE2C_PREPUSH_PATHS"
    )"
    test "$NODE2C_PREPUSH_PATHS_SORTED" = "$EXPECTED_NODE_PATHS"
    git -C "$NODE2C_REPO" diff --cached --quiet
    NODE2C_PREPUSH_TRACKED_STATUS="$(
      git -C "$NODE2C_REPO" status --porcelain --untracked-files=no
    )"
    test -z "$NODE2C_PREPUSH_TRACKED_STATUS"
    NODE2C_PREPUSH_OWNED_UNTRACKED="$(
      git -C "$NODE2C_REPO" ls-files --others --exclude-standard -- "${NODE_PATHS[@]}"
    )"
    test -z "$NODE2C_PREPUSH_OWNED_UNTRACKED"
    assert_node2c_git_controls

    NODE2C_REMOTE_OUTPUT=''
    set +e
    capture_node2c_bounded NODE2C_REMOTE_OUTPUT node2c_get_remote_endpoint
    NODE2C_ENDPOINT_STATUS=$?
    set -e
    if ((NODE2C_ENDPOINT_STATUS != 0)); then
      printf 'Node 2C publication category: endpoint_lookup_error\n' >&2
      exit "$NODE2C_ENDPOINT_STATUS"
    fi
    [[ "$NODE2C_REMOTE_OUTPUT" == *$'\n' ]]
    NODE2C_REMOTE=${NODE2C_REMOTE_OUTPUT%$'\n'}
    test -n "$NODE2C_REMOTE"
    test "${NODE2C_REMOTE//$'\n'/}" = "$NODE2C_REMOTE"
    NODE2C_REMOTE_REF=refs/heads/main
    NODE2C_REMOTE_SHA256="$(
      NODE2C_REMOTE_VALUE="$NODE2C_REMOTE" .venv/bin/python - <<'PY'
import hashlib
import os

print(hashlib.sha256(os.environ["NODE2C_REMOTE_VALUE"].encode("utf-8")).hexdigest())
PY
    )"
    test "$NODE2C_REMOTE_SHA256" = \
      "$NODE2C_GOVERNANCE_REMOTE_ENDPOINT_SHA256"
    [[ "$NODE_BASE" =~ ^([0-9a-f]{40}|[0-9a-f]{64})$ ]]
    if [[ -e "$NODE2C_PUBLICATION_STATE_FILE" ||
          -L "$NODE2C_PUBLICATION_STATE_FILE" ]]; then
      printf 'Node 2C publication checkpoint already exists; no additional push is permitted.\n' >&2
      exit 73
    fi

    PRE_PUSH_REMOTE_SHA=
    PUSH_ATTEMPTED=false
    PUSH_STATUS=
    REMOTE_PUBLICATION_STATUS=indeterminate
    OBSERVED_LOCAL_HEAD=
    OBSERVED_ENDPOINT_SHA=
    OBSERVATION_RESULT=
    OBSERVER_STATUS=
    OBSERVER_FAILURE_STAGE=
    FORWARD_MERGE_BASE_STATUS=
    REVERSE_MERGE_BASE_STATUS=
    configure_node2c_git_auth
    assert_node2c_git_controls

    trap 'exit 130' INT
    trap 'exit 143' TERM
    trap 'exit 129' HUP

    set +e
    observe_node2c_remote_main
    NODE2C_PREPUSH_OBSERVER_STATUS=$?
    set -e
    if ((NODE2C_PREPUSH_OBSERVER_STATUS != 0)); then
      printf 'stable pre-push observation failed at %s with status %s; no push was performed.\n' \
        "$OBSERVER_FAILURE_STAGE" "$NODE2C_PREPUSH_OBSERVER_STATUS" >&2
      exit "$NODE2C_PREPUSH_OBSERVER_STATUS"
    fi
    if [[ "$OBSERVED_ENDPOINT_SHA" != "$NODE_BASE" ]]; then
      printf 'stable remote main moved before push; start a fresh full gate.\n' >&2
      exit 75
    fi
    PRE_PUSH_REMOTE_SHA=$OBSERVED_ENDPOINT_SHA
    assert_node2c_git_controls
    readonly LOCAL_HEAD NODE2C_REPO NODE2C_REMOTE NODE2C_REMOTE_REF \
      NODE_BASE PRE_PUSH_REMOTE_SHA

    set +e
    publish_node2c_main
    NODE2C_PUBLISH_STATUS=$?
    set -e
    exit "$NODE2C_PUBLISH_STATUS"
    ;;
  recover)
    set +e
    recover_node2c_publication
    NODE2C_RECOVERY_STATUS=$?
    set -e
    exit "$NODE2C_RECOVERY_STATUS"
    ;;
  complete)
    set +e
    complete_node2c_publication
    NODE2C_COMPLETION_STATUS=$?
    set -e
    exit "$NODE2C_COMPLETION_STATUS"
    ;;
esac
```

Before the only push command, `publish` stores the literal commit, repository,
endpoint, exact endpoint ref, immutable base, stable pre-push endpoint SHA,
`PUSH_ATTEMPTED=true`, empty push/observer diagnostics, and
`REMOTE_PUBLICATION_STATUS=indeterminate`. The writer creates a temporary file
in the checkpoint directory, flushes it, atomically hard-links it to the absent
checkpoint name without replacement, flushes the directory, removes the
temporary name, and flushes the directory again. Later observation updates use
flush-then-atomic-replace. Any initial checkpoint failure returns before the
push. Every push return leaves durable publication status `indeterminate` until
fresh observation; a nonzero client return is never treated as proof of
rejection, and a zero return is never treated as publication proof.

After every push return, signal interruption, or process loss, start a fresh
shell and run the unchanged fence with `NODE2C_PUBLICATION_ACTION=recover`.
Recovery loads all identities from the checkpoint; it never resolves symbolic
`HEAD`, recalculates the endpoint, or calls publication. Each of first
`ls-remote`, fetch, `FETCH_HEAD^{commit}` resolution, and second
`ls-remote` receives three attempts. Producer failure returns its exact final
status. Endpoint lookup and captured observer stdout are stderr-suppressed,
mode-`0600`, and physically bounded before entering a shell variable; the
non-newline sentinel preserves exact trailing-LF evidence. Only zero-return
malformed, oversized, or inconsistent output maps to `74`.
Every observation clears both bound SHAs first, so a failed repeat cannot
retain a prior successful binding.

The observation decision is independent of the push client's result:

| Forward local-to-endpoint | Reverse endpoint-to-local | Durable result | Recovery status |
|---:|---:|---|---:|
| `0`, exact SHA equality | not run | `published` / `published-exact` | `0` |
| `0`, unequal SHA (endpoint descendant) | not run | `superseded` / `superseded` | `0` |
| `1` | `0` | `not_published` | `0` |
| `1` | `1` | `divergent` | `0` |
| greater than `1` | not run | `indeterminate` | exact forward status |
| `1` | greater than `1` | `indeterminate` | exact reverse status |

A diagnostic persistence failure is reported separately and does not replace
the observer's exact return status. Run `complete` only after a successful
observation. It accepts only `published` / `published-exact` with the persisted
literal local SHA exactly equal to the independently observed endpoint SHA and
forward ancestry status `0`. A descendant endpoint is always `superseded` and
never completes the child, even when the descendant changes only documentation.
`indeterminate` is the only unresolved classification from which observation-
only recovery may enter. `superseded`, `not_published`, and `divergent` are
terminal and can never be overwritten by a later exact observation. A recorded
`published` result must still accept a fresh stable completion observation; if
that observation sees a strict descendant, the durable result becomes terminal
`superseded`. No classification permits checkpoint removal, a repeated
`publish`, or a second push.

The recovery partition is exact: allowed classifications are `indeterminate`,
`published`, `superseded`, `not_published`, and `divergent`; unresolved is
exactly `indeterminate`; terminal classifications are exactly `superseded`,
`not_published`, and `divergent`; `published` remains observable and may become
terminal `superseded` after a fresh stable observation, but never authorizes a
second push.

The mandatory descendant-negative matrix constructs four independent endpoint
descendants after `LOCAL_HEAD`: one source-path commit, one test-path commit, one
governance-document commit, and one merge commit. Every case must produce
`REMOTE_PUBLICATION_STATUS=superseded`, `OBSERVATION_RESULT=superseded`, and a
nonzero `complete` result. The exact-equality control must still produce
`published` / `published-exact` and complete successfully. No path allowlist,
unchanged-blob proof, ancestry containment, or general concurrency policy may
upgrade a descendant to completion because the foundation contract requires
stable exact remote equality.

This checkpoint is operational publication-control state in the common Git
directory, not project data, child output, or durable completion evidence. It
does not widen the Node 2C production persistence surface.

## Completion Evidence

The implementation handoff records these exact outcomes:

```text
Node 2A prerequisite SHA and pinned PASS receipt: validated
Node 2B prerequisite SHA and pinned PASS receipt: validated
inbound governance-candidate publication record and digest: validated
governance-candidate publication record predecessor_sha == e31c3951b06f06e995c0c8f6f8fe2f22320a38da: pass
fixed import-governance parent sole parent == 2be280b5a3194a83191753bfc1deb227a3d2dc31: pass
fixed import-governance parent subject and exact one-plan-path commit: pass
governance candidate was committed before review: pass
governance candidate subject == docs: align Node 2C witness ownership governance: pass
governance candidate sole parent == e31c3951b06f06e995c0c8f6f8fe2f22320a38da: pass
governance candidate exact e31c3951-to-candidate one-commit/two-document range: pass
governance candidate changed paths == plan then core design under LC_ALL=C: pass
candidate design blob == f1ac9a517725ccdc7740108db82f89cd74d0e33f and differs from e31: pass
governance/Task 1/publication inline Git-control helper definitions: byte-identical
Git-control shell failure harness and exact producer-status matrix: pass
replacement refs/regular-or-dangling grafts/shallow history rejected with exported GIT_NO_REPLACE_OBJECTS=1
fresh-shell helper definition/export/direct-call and no-cached-pass constraints: pass
governance candidate SHA == NODE2C_EXPECTED_BASE == NODE_BASE: pass
NODE2C_REVIEWED_PLAN_BLOB: recorded and exact at NODE_BASE
NODE2C_REVIEWED_DESIGN_BLOB: recorded and exact at NODE_BASE
governance documentation review model=claude-fable-5, effort=max, read-only, fast mode=false
governance documentation review exit status=0 and final line=VERDICT: PASS
governance review report SHA-256 and frozen remote endpoint SHA-256: governance-publication-record-bound
stable remote main == e31c3951b06f06e995c0c8f6f8fe2f22320a38da immediately before candidate push: pass
governance exact-candidate non-force remote publication: confirmed
candidate NODE_BASE from origin/main: recorded and immutable for the gate run
HEAD/origin/main and exact two-document-governance chain checks: pass
exact staged allowlist equality: pass
focused Node 2C tests: pass
unified six-module/package-root child-local gate: pass
team_evidence_aggregation_types.py observed physical lines: recorded and <= 900
team_evidence_aggregation_codec.py observed physical lines: recorded and <= 500
team_evidence_aggregation_temporal.py observed physical lines: recorded and <= 300
team_evidence_aggregation_allocation.py observed physical lines: recorded and <= 450
team_evidence_aggregation_witness.py observed physical lines: recorded and <= 650
team_evidence_aggregation.py observed physical lines: recorded and <= 700
test_team_evidence_aggregation_types.py observed physical lines: recorded and <= 900
test_team_evidence_aggregation_codec.py observed physical lines: recorded and <= 600
test_team_evidence_aggregation_temporal.py observed physical lines: recorded and <= 450
test_team_evidence_aggregation_allocation.py observed physical lines: recorded and <= 600
test_team_evidence_aggregation_witness.py observed physical lines: recorded and <= 900
test_team_evidence_aggregation.py observed physical lines: recorded and <= 900
test_team_evidence_aggregation_scope.py observed physical lines: recorded and <= 500
all seven Node 2 tests observed total physical lines: recorded and <= 4,850
all six Node 2 production modules observed total physical lines: recorded and <= 3,500
compileall: pass
pytest collect-only: pass
full pytest: pass
CodeGraph sync .: pass
CodeGraph forced full index: pass
diff hygiene: pass
clean tracked worktree and index: pass
high-confidence secret scan: clean without matched-value output
readonly/persistence/sensitive scans: only negative scope-test assertions classified
exact committed NODE_BASE..HEAD range equality: pass
NODE_BASE..HEAD excludes both governance-document commits and all governance-document touches: pass
GATED_HEAD: recorded from the complete committed-range gate
v6 retained review package: absolute path, mode 0700, closed file set, and all files mode 0600/nlink=1
NODE2C_ACCEPTED_REVIEW_MANIFEST_PATH and recomputed SHA-256: validated
split accepted-review package path/digest: validated by sealed split_manifest.py
split_manifest.py SHA-256 and SHA256SUMS seal bb7f92076e3c242cf1bfc8e1f741d4c40b4eb202079576e637f6023ce3491794: pass
Claude exact command includes --bare: pass
foundation authority SHA-256 == af91080df318fb322a2bc387a800d50757963c221262f286facdd145fbbe5200
foundation authority Git blob == f0ae5a3d73023f3d6f972d467669adc628c3f06a
NODE2C_ACCEPTED_REVIEW_READ_ONLY=true
NODE2C_ACCEPTED_REVIEW_FAST_MODE=false
NODE2C_ACCEPTED_REVIEW_EXIT_STATUS=0
NODE2C_ACCEPTED_REVIEW_FINAL_LINE=VERDICT: PASS
NODE2C accepted raw stream/report/stderr SHA-256 values: recorded
NODE2C accepted raw stream/report/stderr byte counts: recorded and bounded
review-fix count and ordered fix-commit SHAs: recorded, including zero fixes
PRE_PUSH_REMOTE_SHA == NODE_BASE immediately before the sole push: pass
LOCAL_HEAD == local checkpoint candidate_sha and split manifest gated_head: pass
NODE2C_REMOTE and NODE2C_REMOTE_REF: loaded from the durable push checkpoint
PUSH_ATTEMPTED=true was durable before the sole push
PUSH_STATUS: exact when the client returned; empty only when process loss prevented capture
OBSERVER_STATUS=0
OBSERVER_FAILURE_STAGE: empty
OBSERVED_LOCAL_HEAD == LOCAL_HEAD: pass
OBSERVED_ENDPOINT_SHA: exact 40- or 64-character lowercase object ID
FORWARD_MERGE_BASE_STATUS=0
REVERSE_MERGE_BASE_STATUS: empty because reverse ancestry was not run
OBSERVATION_RESULT: published-exact
REMOTE_PUBLICATION_STATUS=published
OBSERVED_ENDPOINT_SHA == LOCAL_HEAD: pass
source/test/governance/merge descendant-negative matrix: superseded and completion rejected
publication push count=1; recovery push count=0
```

Node 2C is complete only when every line above is true for the same final
committed range and the stable publication classification is exactly
`published` / `published-exact` with exact endpoint equality. A nonzero or
unavailable `PUSH_STATUS` is not itself disqualifying when the stable three-SHA
observation proves exact publication. It remains diagnostic only and never
authorizes another push. A descendant observation is `superseded`, is not
completion evidence, and still never authorizes another push.
Any review report, gate manifest, test matrix, remote-observation artifact,
receipt, or publication-control checkpoint retained by this plan is operational
Git/review evidence, not project data. Such evidence may remain in controlled
external files. It must not be used as a project-data store, history, index,
replay source, or persistence fallback.

The common-Git-directory checkpoint is operational crash-control state, not
child output or a Node 3 data handoff; its existence or contents alone are not
completion evidence. The current Node 2C production child remains pure and
transient and persists no project data. A separately reviewed later node that
persists project data derived from Node 2 domain values or results must use only
local Supabase/Postgres and must validate every raw DSN through
`validate_local_postgres_dsn` before connection construction. No package-root
surface or live/auth/account/private-key/wallet/signing/order/execution authority
is introduced.

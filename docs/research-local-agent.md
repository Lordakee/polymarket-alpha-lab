# Local-agent protocol and explicit uncapped research (WP-02 / WP-03)

## Delivered boundary, not a ready-to-run Codex launcher

The strict **Codex 0.155.1 event-protocol adapter** and explicit
**no-business-monetary-cap execution path** cover one task, a batch and a
rotation. They reuse the original managed PostgreSQL session, immutable requests,
claim-before-model ordering and result capture. No second queue, backend,
monetary reservation or reporting subsystem is introduced.

**No default subprocess transport or real Codex activation is shipped.**
`CodexExecModel` requires an application-supplied `CodexExecTransport`. CLI
isolation/persistence/output-bound behavior remains an activation blocker, not
permission to supply a naive subprocess wrapper or silently use the legacy API.
The standalone task script still has no configured real client. G2/G3 remain open.

## Permission without a fictitious budget

`UncappedResearchAuthorization` is a copied, canonical application value: ID,
model label, reviewed adapter-contract digest, UTC approval/expiry, 1..100 exact
original `(record_id, request_sha256)` pairs, and explicit true approvals for
research transmission and no monetary ceiling. The finite roster is a resource
bound per intake, not a cumulative business event/cost limit. The original
per-task message/output/call limits remain.

`monetary_cap` and `actual_billed_micros` are **null**, not zero. There is no price,
currency, all-inclusive fee attestation, fake huge allowance or refund. Existing
capped `ModelCallBudget` behavior is unchanged. Selecting both modes, missing an
explicit opt-in, or mismatching a task/model/hash fails closed.

The value is **not signed authorization or a durable approval ledger**. Its
digest is a reviewed reference, not executable/provider identity attestation.
Only the original execution requests/results are written durably by this path;
authorization metadata and raw Codex streams are not automatically persisted.
Independent historical approval/usage/invoice audit remains an acceptance gap.
Real activation must resolve it, not claim that a Boolean certifies approval.

The explicitly configured owning application supplies the reviewed values below,
not a model response, guessed credential or implicit environment scan:

```python
from pathlib import Path
from polymarket_alpha_lab.project_postgres.server import ProjectPostgres
from polymarket_alpha_lab.research_uncapped import UncappedResearchAuthorization
from polymarket_alpha_lab.research_codex_exec import CodexExecModel

permission = UncappedResearchAuthorization(
    authorization_id=reviewed_authorization_id,
    model_id=reviewed_model_id,
    adapter_contract_sha256=reviewed_adapter_contract_sha256,
    approved_at=reviewed_approval_time,
    expires_at=reviewed_expiry_time,
    request_keys=tuple((r.record_id, r.content_sha256) for r in reviewed_requests),
    no_monetary_cap_approved=True,
    research_data_send_approved=True,
)

def inert_factory(team_id):
    return CodexExecModel(model_id=reviewed_model_id,
                          transport=approved_transport_factory(team_id))

with ProjectPostgres(Path(actual_project_root)).session() as research:
    receipt = research.run_uncapped_research(
        request=reviewed_requests[0], authorization=permission,
        model_factory=inert_factory,
        allow_model_calls=True, allow_uncapped_costs=True,
    )
```

This is an integration example requiring reviewed values and a separately proven
transport, **not an executable real-model setup command**. Managed sessions retain
DSN validation, instance binding and lifecycle draining. No user instance is
opened, migrated or upgraded by this source change.

Existing batch/rotation methods accept `uncapped_authorization=permission` and
`allow_uncapped_costs=True` with `allow_model_calls=True`, the inert factory and
original limits/stop token. Omit `model_budget_id`. Batch scope validates the
selected pending prefix; rotation scope validates every pending roster member
before reserving a new turn. Permission already expired at that preflight
rejects a new reservation. It may expire during/after a committed reservation;
then task admission fails without a model call and the original turn remains.
Same-turn replay remains inert. The standalone CLI is unchanged.

## Execution, expiry and uncertain outcomes

A new original execution claim commits before real factory/client entry. No
monetary permit is appropriate here. The wrapper checks permission time, cutoff,
stop, messages, output request and call count; it rechecks time/stop after factory
construction. A zero-model evidence rejection never constructs a real client.
Callbacks remain trusted in-process code, not malicious-code sandboxes.

Permission expiry uses the application UTC clock. The original DB claim also
checks its task window with the DB clock. This is not a new DB approval clock,
hard process deadline, universal cancellation or actual provider-request counter.
In-flight responses may arrive later; the transport must separately enforce I/O,
cleanup and absence of hidden retries/tools/fallback.

Every client/decoder error closes that wrapper. Ordinary errors become fixed
codes; interrupts propagate. No automatic resend, repair, resume, refund or task-ID
substitution. Original failures are captured normally. Process loss after claim
leaves **incomplete**, never age-based reclaim. Exact original histories replay
under expired permission without model entry; lookup errors do not create work.

## Codex protocol contract

`CodexExecInput` preserves exact message text, explicit model label, unchanged
output request and closed action schema. Its prompt encloses the transcript plus
existing research tool definitions. Those are action **data**, not executable
CLI tools. The adapter does not read files, launch a process or perform I/O.

The decoder requires one successful thread/turn, supported complete items, one
final action object and the pinned five-field usage schema. Unknown/tool/error
events, nonzero exits, missing/duplicate terminal events, unfinished items,
invalid usage/UTF-8/JSON/arguments and excess bytes/events fail closed. LF/CRLF
separate records; Unicode within JSON does not. Generated tool IDs do not collide
across calls. The original agent still verifies citations against read evidence.

Returned `total_tokens` is reported input plus output; cached-input and reasoning
subsets are not double counted. It is not independent token or invoice verification.
Failed streams have no validated usage receipt: zero original counters must not
be interpreted as proof of no outside usage/charge. Reported output overrun is
rejected **after** the operation, not a pre-request provider cap. Raw stderr and
reasoning are not copied to the research result or a new durable store.

## Actual upstream investigation and remaining activation blockers

Checked 2026-09-19 against official **0.155.1**, source
`be2951ea34f0d295ed0becf97079f92fa5f6950e`. A separately exported official Linux
binary matched its release size/digest. Probes used new private home/work
folders, synthetic prompts and a loopback in-memory Responses service. No real
provider, API token, user login/database or market input was used. These are
experiments, not a production launcher or Windows CLI acceptance.

- `--ephemeral` still created local SQLite state files in the observed process.
  Pinned source initializes state storage separately from rollout persistence;
  `sqlite` is a removed feature. No test-only in-memory flag or unsafe bypass is
  adopted as a product persistence solution.
- Disabling shell left other tools in the initial request. Additional settings
  yielded an empty tool list in one sample, not proof of ancestor-config,
  hooks/plugins/MCP or filesystem isolation.
- A corrected probe exited zero and completed but also emitted a Code Mode error
  item. The decoder rejects it: exit zero alone is not sufficient. That probe
  does not certify an admissible host.
- Pinned request construction did not establish a provider-enforced output limit
  matching this project's interface. No undocumented flag is invented. Default
  documented HTTP/SSE retries cannot be counted as one request per CLI start.

Host persistence/context isolation, no-hidden-operation evidence, resource and
cleanup enforcement, actual model identity and authorization/usage audit remain
required before a launcher can be enabled. No user-local task is delegated to
bypass these unresolved contracts.

Primary references (checked 2026-09-19):
- https://developers.openai.com/codex/noninteractive/
- https://developers.openai.com/codex/config-reference/
- https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/exec/src/exec_events.rs
- https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/client.rs
- https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/rollout/src/state_db.rs

## Evidence and separate review

Initial focused **2 failed / 175 passed**: an authorization model lone surrogate
was incorrectly accepted (fixed); one stale-evidence fixture was incorrectly
constructed (corrected, same zero-call expectation). Related tests then passed570.

Separate same-assistant review first reproduced **8 failed / 9 passed**:
Unicode/CR-only framing, reported output overrun, empty messages entering a
factory, expired permission consuming a rotation. Original counterexamples remain.
An intermediate **1 failed / 586 passed** used an unpatched static-time fixture;
after providing its clock, the unchanged expectations passed **587** tests.
This is not external/fresh-agent review or a guarantee of no defects.

The native proof `tests/test_project_postgres_uncapped_native.py` uses current67
migrations, BTC/ETH synthetic Codex events, stop/two turns/restart, duplicate claims,
expired replay, zero fake permits, real child-process loss and older/incomplete
history preservation. Windows dispatch appends this and three new unit modules;
all original selectors/deadlines/permissions remain. Exact final tree, full/hosted
results, first failures and unexecuted checks belong in the implementation PR.

A subsequent packaging review reproduced one omitted integration-guide test, then
added the guide to the existing optional distribution list. Older kits remain
verifiable; the counterexample is retained in the review test module. A third
synthetic CLI probe still emitted the missing Code Mode companion error despite
an explicit feature setting; the decoder rejected it without stripping the error.
This is an incomplete probe runtime, not proof every Codex installation fails.


### Additional separate self-review: nested Unicode (2026-09-19)

A fresh review of PR #60 head `61b260dd41285e59b5587381bacd025f1bbf6385`
reproduced **12 failing / 3 passing** counterexamples: UTF-8-valid JSON can contain
an escaped unpaired surrogate that becomes invalid text only after a nested
parse. Validating only the message/stream envelope admitted four invalid input
forms and eight invalid evidence-action argument forms. The protocol now checks
all decoded input strings/keys and the original validator's decoded action
arguments before a host call or valid reply. No character replacement, transcript
re-encoding, precision conversion or relaxation of the action schema is used.
Valid Chinese text, emoji, surrogate pairs and Decimal-bearing original input
remain byte-for-byte unchanged. These cases stay in the existing review module
already selected by Windows native CI. No host, database codec or migration changes.

This is another separate same-assistant source/negative-test review, not external
certification. The earlier local exploratory full run overlapped review edits and
is NOT final-tree acceptance evidence. Final frozen-tree local and hosted results,
source hashes and any remaining failures are recorded in the PR before merge.
Four additional BTC/ETH capture/replay checks retain the original failed result
without invalid summary text or a second host entry. Nineteen added regressions
cover this correction in total. All real-host/persistence/usage acceptance limits
above remain open.

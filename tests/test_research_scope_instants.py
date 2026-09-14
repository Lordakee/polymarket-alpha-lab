"""Bind nested research timestamps by instant, not Python wall-clock equality.

Use original synthetic runs and vary only the representation of one boundary.
No public HTTP, database, model credentials or environment time zone lookup.
"""
from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone
from importlib import resources
from zoneinfo import ZoneInfo

import pytest

from polymarket_alpha_lab.research_capture_codec import (
    decode_research_capture, encode_research_capture, payload_sha256,
)
from polymarket_alpha_lab.research_execution import CapturedResearchRequest, bind_execution_run
from polymarket_alpha_lab.team_research_evaluation import ResearchEvaluationRecord
from tests.test_research_evidence_timezones import Model, args, evidence, snapshot
from polymarket_alpha_lab.team_research_market_pipeline import run_team_research_from_market_snapshot

CASES = (
    ('America/New_York', '2026-11-01T05:30:00+00:00'),
    ('America/New_York', '2026-11-01T06:30:00+00:00'),
    ('Australia/Lord_Howe', '2026-04-04T14:45:00+00:00'),
    ('Australia/Lord_Howe', '2026-04-04T15:15:00+00:00'),
)
EDGES = ('intake_task', 'source_receipt', 'run_result')


def zone(key):
    with resources.files('tzdata.zoneinfo').joinpath(*key.split('/')).open('rb') as f:
        return ZoneInfo.from_file(f, key=key)


def make_run(case):
    key, stamp = case
    at = datetime.fromisoformat(stamp).astimezone(zone(key))
    return run_team_research_from_market_snapshot(snapshot(at, at),
        **args(at, (evidence(at),)), model_factory=lambda _: Model())


def boundary(run, edge, when):
    if edge == 'intake_task':
        return replace(run, intake=replace(run.intake, task=replace(run.intake.task, as_of=when)))
    if edge == 'source_receipt':
        return replace(run, intake=replace(run.intake, source_receipts=(
            replace(run.intake.source_receipts[0], observed_at=when),)))
    return replace(run, research=replace(run.research, as_of=when))


def encode(run):
    return encode_research_capture(record_id='time-binding', model_id='synthetic-model',
        protocol_version='binding-v1', run=run)


@pytest.mark.parametrize('case', CASES)
@pytest.mark.parametrize('edge', EDGES)
def test_repeated_wall_label_cannot_bind_a_different_instant(case, edge):
    run = make_run(case)
    original = run.intake.as_of
    wrong = original.replace(fold=1-original.fold)
    assert wrong == original  # Documents the Python equality trap, not domain equality.
    assert wrong.astimezone(UTC) != original.astimezone(UTC)
    with pytest.raises(ValueError, match='scope|receipts'):
        boundary(run, edge, wrong)


@pytest.mark.parametrize('case', CASES)
@pytest.mark.parametrize('edge', EDGES)
@pytest.mark.parametrize('representation', ('utc', 'fixed_offset', 'distinct_zone'))
def test_equivalent_instants_are_accepted_and_keep_canonical_wire(case, edge, representation):
    run = make_run(case)
    original = run.intake.as_of
    target_zone = {'utc': UTC, 'fixed_offset': timezone(original.utcoffset()),
                   'distinct_zone': zone(case[0])}[representation]
    equivalent = original.astimezone(target_zone)
    assert equivalent.astimezone(UTC) == original.astimezone(UTC)
    changed = boundary(run, edge, equivalent)
    assert encode(changed) == encode(run)
    recorded = original.astimezone(UTC) + timedelta(seconds=1)
    old = ResearchEvaluationRecord('time-binding', 'synthetic-model', 'binding-v1', recorded, run)
    new = ResearchEvaluationRecord('time-binding', 'synthetic-model', 'binding-v1', recorded, changed)
    assert new.content_sha256 == old.content_sha256
    # Source fields and the caller's chosen timezone objects are not normalized in place.
    assert run.intake.as_of is original
    selected = (changed.intake.task.as_of if edge == 'intake_task' else
        changed.intake.source_receipts[0].observed_at if edge == 'source_receipt' else changed.research.as_of)
    assert selected is equivalent
    assert selected.fold == equivalent.fold
    assert selected.isoformat() == equivalent.isoformat()


@pytest.mark.parametrize('edge', EDGES)
@pytest.mark.parametrize('delta', (-1, 1))
def test_one_microsecond_mismatch_is_not_rounded_away(edge, delta):
    run = make_run(CASES[0])
    different = run.intake.as_of.astimezone(UTC) + timedelta(microseconds=delta)
    with pytest.raises(ValueError, match='scope|receipts'):
        boundary(run, edge, different)


@pytest.mark.parametrize('field,value', (
    ('source_id', 'different'), ('content_sha256', '0'*64), ('reference', 'synthetic:different'),
    ('paper_only', False), ('report_only', False), ('readonly', False),
))
def test_timestamp_fix_does_not_weaken_other_receipt_fields(field, value):
    run = make_run(CASES[0])
    with pytest.raises(ValueError):
        modified = replace(run.intake.source_receipts[0], **{field: value})
        replace(run.intake, source_receipts=(modified,))


@pytest.mark.parametrize('edge', EDGES)
def test_deep_mutation_is_rechecked_before_evaluation_and_capture(edge):
    run = make_run(CASES[0])
    wrong = run.intake.as_of.replace(fold=1)
    if edge == 'intake_task':
        object.__setattr__(run.intake.task, 'as_of', wrong)
    elif edge == 'source_receipt':
        object.__setattr__(run.intake.source_receipts[0], 'observed_at', wrong)
    else:
        object.__setattr__(run.research, 'as_of', wrong)
    with pytest.raises(ValueError):
        run.__post_init__()
    with pytest.raises(ValueError):
        ResearchEvaluationRecord('time-binding', 'synthetic-model', 'binding-v1',
            run.intake.as_of.astimezone(UTC) + timedelta(seconds=1), run)
    with pytest.raises(ValueError):
        encode(run)


@pytest.mark.parametrize('case', CASES)
def test_mixed_representations_survive_request_binding_and_decode(case):
    run = make_run(case)
    utc = run.intake.as_of.astimezone(UTC)
    mixed = boundary(boundary(boundary(run, 'intake_task', utc), 'source_receipt', utc), 'run_result', utc)
    request = CapturedResearchRequest('time-binding', 'synthetic-model', 'binding-v1',
        utc + timedelta(minutes=10), mixed.intake, required_source_ids=('source-1',))
    bound = bind_execution_run(request, mixed)
    assert bound.intake.as_of.tzinfo is UTC
    assert bound.research.as_of == utc
    payload = encode(mixed)
    decoded = decode_research_capture(payload, recorded_at=utc+timedelta(seconds=1),
        expected_sha256=payload_sha256(payload))
    assert encode(decoded.run) == payload


@pytest.mark.parametrize('edge', EDGES)
def test_invalid_fold_does_not_reach_capture_transaction(monkeypatch, edge):
    from polymarket_alpha_lab import research_capture_psycopg as storage
    run = make_run(CASES[0])
    wrong = run.intake.as_of.replace(fold=1)
    target, field = ((run.intake.task, 'as_of') if edge == 'intake_task' else
                     (run.intake.source_receipts[0], 'observed_at') if edge == 'source_receipt' else
                     (run.research, 'as_of'))
    object.__setattr__(target, field, wrong)
    monkeypatch.setattr(storage, '_local_transaction',
        lambda *a, **k: pytest.fail('invalid scope must not open a transaction'))
    with pytest.raises(ValueError, match='invalid research capture input'):
        storage.capture_research_with_psycopg('not-a-connection', record_id='time-binding',
            model_id='synthetic-model', protocol_version='binding-v1', run=run)


@pytest.mark.parametrize('field', ('task_id', 'team_id', 'condition_id', 'market_slug'))
def test_non_time_result_scope_remains_bound(field):
    run = make_run(CASES[0])
    replacement = 'crypto_btc' if field == 'team_id' else 'different'
    with pytest.raises(ValueError, match='scope'):
        replace(run, research=replace(run.research, **{field: replacement}))


@pytest.mark.parametrize('kind', ('missing', 'extra', 'reverse'))
def test_receipt_cardinality_and_order_remain_bound(kind):
    from polymarket_alpha_lab.team_research_intake import ResearchSourceReceipt, evidence_content_sha256
    run = make_run(CASES[0])
    source = replace(run.intake.task.evidence[0], source_id='source-2')
    receipt = ResearchSourceReceipt(source.source_id, evidence_content_sha256(source),
        source.reference, source.observed_at)
    complete = replace(run.intake, task=replace(run.intake.task, evidence=(*run.intake.task.evidence, source)),
        source_receipts=(*run.intake.source_receipts, receipt))
    modified = {'missing': complete.source_receipts[:1],
                'extra': (*complete.source_receipts, receipt),
                'reverse': tuple(reversed(complete.source_receipts))}[kind]
    with pytest.raises(ValueError, match='receipts'):
        replace(complete, source_receipts=modified)

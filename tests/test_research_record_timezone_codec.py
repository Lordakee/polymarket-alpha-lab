"""Same canonical record bytes for stream-loaded, fixed-offset and UTC clocks."""
from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone

import pytest

from polymarket_alpha_lab.research_capture_codec import encode_research_capture, decode_research_capture, payload_sha256
from polymarket_alpha_lab.research_execution import CapturedResearchRequest, decode_execution_request
from polymarket_alpha_lab.team_research_evaluation import ResearchEvaluationRecord, ResearchEvaluationReport
from tests.test_research_capture_codec import make_run
from tests.test_research_evidence_timezones import zone

INSTANTS = (
    ('America/New_York', '2026-11-01T05:30:00+00:00'),
    ('America/New_York', '2026-11-01T06:30:00+00:00'),
    ('America/New_York', '2026-03-08T07:01:00+00:00'),
    ('Australia/Lord_Howe', '2026-04-04T15:15:00+00:00'),
)
STATUSES = ('completed', 'failed', 'intake_blocked')


def pair(instant, status):
    key, iso = instant
    now = datetime.fromisoformat(iso).astimezone(zone(key))
    stream = make_run(now=now, status=status)
    def fixed_time(value):
        return value.astimezone(timezone(value.utcoffset()))
    intake = stream.intake
    task = intake.task
    if task is not None:
        task = replace(task, as_of=fixed_time(task.as_of), evidence=tuple(
            replace(row, observed_at=fixed_time(row.observed_at)) for row in task.evidence))
    fixed_intake = replace(intake, as_of=fixed_time(intake.as_of),
        fetched_at=fixed_time(intake.fetched_at), task=task, source_receipts=tuple(
            replace(row, observed_at=fixed_time(row.observed_at)) for row in intake.source_receipts))
    result = stream.research
    if result is not None:
        result = replace(result, as_of=fixed_time(result.as_of))
    # Same original market/evidence bytes/hashes, only an equivalent time representation.
    fixed = replace(stream, intake=fixed_intake, research=result)
    return now, stream, fixed


def encode(run):
    return encode_research_capture(record_id='record', model_id='synthetic', protocol_version='codec-v1', run=run)


@pytest.mark.parametrize('instant', INSTANTS)
@pytest.mark.parametrize('status', STATUSES)
def test_capture_stream_zone_matches_unchanged_fixed_offset_wire(instant, status):
    now, stream, fixed = pair(instant, status)
    original_tz = stream.intake.as_of.tzinfo
    expected = encode(fixed)
    actual = encode(stream)
    assert actual == expected
    decoded = decode_research_capture(actual, recorded_at=now.astimezone(UTC), expected_sha256=payload_sha256(actual))
    assert decoded.run.intake.as_of.tzinfo is UTC
    assert encode(decoded.run) == actual
    assert stream.intake.as_of.tzinfo is original_tz
    assert stream.intake.as_of.fold == now.fold
    assert stream.intake.as_of.isoformat() == now.isoformat()


@pytest.mark.parametrize('instant', INSTANTS)
@pytest.mark.parametrize('status', STATUSES)
def test_evaluation_stream_zone_preserves_hash_and_decisions(instant, status):
    now, stream, fixed = pair(instant, status)
    def record(run):
        return ResearchEvaluationRecord('record', 'synthetic', 'codec-v1', now, run)
    left, right = record(stream), record(fixed)
    assert left.content_sha256 == right.content_sha256
    assert ResearchEvaluationReport((left,), (), now).to_dict() == ResearchEvaluationReport((right,), (), now).to_dict()
    assert left.run.intake.as_of.tzinfo is stream.intake.as_of.tzinfo
    assert left.run.intake.as_of.fold == now.fold


@pytest.mark.parametrize('instant', INSTANTS)
@pytest.mark.parametrize('status', STATUSES)
def test_execution_stream_zone_matches_existing_utc_request_wire(instant, status):
    now, stream, fixed = pair(instant, status)
    cutoff = now.astimezone(UTC) + timedelta(hours=1)
    def request(run):
        return CapturedResearchRequest('record', 'synthetic', 'codec-v1', cutoff, run.intake)
    actual, expected = request(stream), request(fixed)
    assert actual.payload == expected.payload
    assert actual.content_sha256 == expected.content_sha256
    assert actual.intake.as_of.tzinfo is UTC
    assert decode_execution_request(actual.payload, actual.content_sha256).payload == actual.payload
    assert stream.intake.as_of.tzinfo is now.tzinfo
    assert stream.intake.as_of.fold == now.fold


@pytest.mark.parametrize('operation', ('capture', 'evaluation', 'request'))
def test_copy_support_does_not_relax_input_flag_checks(operation):
    now, stream, _ = pair(INSTANTS[1], 'completed')
    object.__setattr__(stream.intake.task.evidence[0], 'readonly', False)
    with pytest.raises(ValueError):
        if operation == 'capture':
            encode(stream)
        elif operation == 'evaluation':
            ResearchEvaluationRecord('record', 'synthetic', 'codec-v1', now, stream)
        else:
            CapturedResearchRequest('record', 'synthetic', 'codec-v1', now.astimezone(UTC) + timedelta(hours=1), stream.intake)


def test_folded_wall_hour_remains_distinct_in_all_record_fingerprints():
    pairs = [pair(instant, 'completed') for instant in INSTANTS[:2]]
    (early, left, _), (late, right, _) = pairs
    assert early.replace(tzinfo=None) == late.replace(tzinfo=None)
    assert encode(left) != encode(right)
    left_record = ResearchEvaluationRecord('record', 'synthetic', 'codec-v1', early, left)
    right_record = ResearchEvaluationRecord('record', 'synthetic', 'codec-v1', late, right)
    assert left_record.content_sha256 != right_record.content_sha256


@pytest.mark.parametrize('bad', (1.5, object(), b'payload', {1: 'not a record key'}, datetime(2026, 1, 1)))
def test_record_projection_rejects_non_schema_values(bad):
    from dataclasses import dataclass
    from polymarket_alpha_lab.research_record_values import record_dict
    @dataclass
    class Fixture:
        value: object
    with pytest.raises(ValueError):
        record_dict(Fixture(bad))


def test_record_projection_copies_containers_without_deepcopy_hooks():
    from dataclasses import dataclass
    from polymarket_alpha_lab.research_record_values import record_dict
    @dataclass
    class Fixture:
        values: object
    source = Fixture({'items': [1, True, None, ('a', 'b')]})
    copied = record_dict(source)
    copied['values']['items'].append('new')
    assert len(source.values['items']) == 4
    class NoCopy:
        def __deepcopy__(self, memo):
            pytest.fail('arbitrary deepcopy hook must not execute')
    with pytest.raises(ValueError):
        record_dict(Fixture(NoCopy()))


@pytest.mark.parametrize('value', ({}, type))
def test_record_projection_requires_dataclass_instance(value):
    from polymarket_alpha_lab.research_record_values import record_dict
    with pytest.raises(ValueError):
        record_dict(value)

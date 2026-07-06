from __future__ import annotations

import ast
import importlib
from collections.abc import Mapping
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType
from typing import Any, get_args, get_origin, get_type_hints

import pytest


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "market_research_policy_ballot_access_litigation_shift_digest.py",
)
GENERATED_AT = datetime(2026, 7, 6, 16, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_policy_ballot_access_litigation_shift_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str = "source-alpha",
    litigation_id: str = "litigation-alpha",
    *,
    contest_id: str = "presidential-general",
    jurisdiction: str = "colorado",
    candidate_id: str = "candidate-alpha",
    observed_at: datetime = datetime(2026, 7, 6, 15, 45, tzinfo=UTC),
    ruling_shift_count: str | Decimal = "0.000000",
    adverse_ruling_count: str | Decimal = "0.000000",
    appeal_pending_count: str | Decimal = "0.000000",
    injunction_pending_count: str | Decimal = "0.000000",
    ballot_deadline_days: str | Decimal = "45.000000",
    source_count: str | Decimal = "2.000000",
    confidence: str | Decimal = "0.840000",
    source_config_version: str = "source-config-v0",
):
    module = api()
    return module.PolicyBallotAccessLitigationShiftObservation(
        source_id=source_id,
        litigation_id=litigation_id,
        contest_id=contest_id,
        jurisdiction=jurisdiction,
        candidate_id=candidate_id,
        observed_at=observed_at,
        ruling_shift_count=(
            ruling_shift_count
            if isinstance(ruling_shift_count, Decimal)
            else d(ruling_shift_count)
        ),
        adverse_ruling_count=(
            adverse_ruling_count
            if isinstance(adverse_ruling_count, Decimal)
            else d(adverse_ruling_count)
        ),
        appeal_pending_count=(
            appeal_pending_count
            if isinstance(appeal_pending_count, Decimal)
            else d(appeal_pending_count)
        ),
        injunction_pending_count=(
            injunction_pending_count
            if isinstance(injunction_pending_count, Decimal)
            else d(injunction_pending_count)
        ),
        ballot_deadline_days=(
            ballot_deadline_days
            if isinstance(ballot_deadline_days, Decimal)
            else d(ballot_deadline_days)
        ),
        source_count=source_count if isinstance(source_count, Decimal) else d(source_count),
        confidence=confidence if isinstance(confidence, Decimal) else d(confidence),
        source_config_version=source_config_version,
    )


def config(**overrides: object):
    module = api()
    return module.PolicyBallotAccessLitigationShiftDigestConfig(**overrides)


def report(*rows: object, cfg: object | None = None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_market_research_policy_ballot_access_litigation_shift_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at.astimezone(timezone(timedelta(hours=-4))),
    )


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    module = api()

    digest = report()

    assert isinstance(digest, module.PolicyBallotAccessLitigationShiftDigestReport)
    assert is_dataclass(digest)
    assert digest.__dataclass_params__.frozen
    assert digest.generated_at == GENERATED_AT
    assert digest.generated_at.tzinfo is UTC
    assert digest.config_version == (
        "market-research-policy-ballot-access-litigation-shift-digest-v0"
    )
    assert digest.digest_status == "blocked"
    assert digest.recommended_next_step == (
        "block_report_only_market_research_policy_ballot_access_litigation_shift_digest"
    )
    assert digest.observation_count == d("0.000000")
    assert digest.ready_observation_count == d("0.000000")
    assert digest.watch_observation_count == d("0.000000")
    assert digest.blocked_observation_count == d("0.000000")
    assert digest.ruling_shift_observation_count == d("0.000000")
    assert digest.adverse_ruling_observation_count == d("0.000000")
    assert digest.appeal_pending_observation_count == d("0.000000")
    assert digest.injunction_pending_observation_count == d("0.000000")
    assert digest.near_deadline_observation_count == d("0.000000")
    assert digest.source_gap_observation_count == d("0.000000")
    assert digest.confidence_gap_observation_count == d("0.000000")
    assert digest.stale_source_observation_count == d("0.000000")
    assert digest.max_litigation_shift_score == d("0.000000")
    assert digest.average_litigation_shift_score == d("0.000000")
    assert digest.max_observation_age_seconds == d("0.000000")
    assert digest.rows == ()
    assert digest.source_config_versions == ()
    assert digest.reason_codes == (
        "market_research_policy_ballot_access_litigation_shift_digest_no_inputs",
    )
    assert digest.reason_code_counts == (
        module.PolicyBallotAccessLitigationShiftReasonCodeCount(
            reason_code=(
                "market_research_policy_ballot_access_litigation_shift_digest_no_inputs"
            ),
            count=d("1.000000"),
            observation_ratio=d("0.000000"),
        ),
    )
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True


def test_high_risk_litigation_shift_blocks_probability_event_screening() -> None:
    digest = report(
        observation(
            "source-blocked",
            "litigation-blocked",
            ruling_shift_count="2.000000",
            adverse_ruling_count="1.000000",
            appeal_pending_count="1.000000",
            injunction_pending_count="1.000000",
            ballot_deadline_days="3.000000",
            confidence="0.920000",
            observed_at=datetime(2026, 7, 6, 11, 45, tzinfo=timezone(timedelta(hours=-4))),
        ),
        observation(
            "source-watch",
            "litigation-watch",
            contest_id="senate-primary",
            jurisdiction="maine",
            candidate_id="candidate-beta",
            ruling_shift_count="1.000000",
            appeal_pending_count="1.000000",
            ballot_deadline_days="7.000000",
        ),
        observation(
            "source-ready",
            "litigation-ready",
            contest_id="house-primary",
            jurisdiction="new-hampshire",
            candidate_id="candidate-gamma",
        ),
    )

    assert digest.digest_status == "blocked"
    assert digest.recommended_next_step == (
        "block_report_only_market_research_policy_ballot_access_litigation_shift_digest"
    )
    assert digest.observation_count == d("3.000000")
    assert digest.blocked_observation_count == d("1.000000")
    assert digest.watch_observation_count == d("1.000000")
    assert digest.ready_observation_count == d("1.000000")
    assert digest.ruling_shift_observation_count == d("2.000000")
    assert digest.adverse_ruling_observation_count == d("1.000000")
    assert digest.appeal_pending_observation_count == d("2.000000")
    assert digest.injunction_pending_observation_count == d("1.000000")
    assert digest.near_deadline_observation_count == d("2.000000")
    assert digest.max_litigation_shift_score == d("1.000000")
    assert digest.average_litigation_shift_score == d("0.475000")
    assert tuple(row.litigation_id for row in digest.rows) == (
        "litigation-blocked",
        "litigation-watch",
        "litigation-ready",
    )

    blocked, watched, ready = digest.rows
    assert blocked.digest_status == "blocked"
    assert blocked.observed_at == datetime(2026, 7, 6, 15, 45, tzinfo=UTC)
    assert blocked.observation_age_seconds == d("900.000000")
    assert blocked.litigation_shift_score == d("1.000000")
    assert blocked.reason_codes == (
        "market_research_policy_ballot_access_litigation_shift_digest_adverse_ruling",
        "market_research_policy_ballot_access_litigation_shift_digest_appeal_pending",
        "market_research_policy_ballot_access_litigation_shift_digest_high_ruling_shift",
        "market_research_policy_ballot_access_litigation_shift_digest_injunction_pending",
        "market_research_policy_ballot_access_litigation_shift_digest_near_deadline",
        "market_research_policy_ballot_access_litigation_shift_digest_ruling_shift",
    )
    assert watched.digest_status == "watch"
    assert watched.litigation_shift_score == d("0.425000")
    assert watched.reason_codes == (
        "market_research_policy_ballot_access_litigation_shift_digest_appeal_pending",
        "market_research_policy_ballot_access_litigation_shift_digest_near_deadline",
        "market_research_policy_ballot_access_litigation_shift_digest_ruling_shift",
    )
    assert ready.digest_status == "ready"
    assert ready.reason_codes == (
        "market_research_policy_ballot_access_litigation_shift_digest_ready",
    )


def test_rows_and_reason_codes_are_sorted_deterministically() -> None:
    first = observation(
        "source-watch-b",
        "litigation-watch-b",
        ruling_shift_count="1.000000",
        appeal_pending_count="1.000000",
        ballot_deadline_days="7.000000",
    )
    second = observation(
        "source-blocked",
        "litigation-blocked",
        ruling_shift_count="2.000000",
        adverse_ruling_count="1.000000",
        appeal_pending_count="1.000000",
        injunction_pending_count="1.000000",
        ballot_deadline_days="7.000000",
    )
    third = observation(
        "source-watch-a",
        "litigation-watch-a",
        ruling_shift_count="1.000000",
        appeal_pending_count="1.000000",
        ballot_deadline_days="7.000000",
    )

    forward = report(first, second, third)
    reverse = report(third, second, first)

    assert forward == reverse
    assert tuple(row.litigation_id for row in forward.rows) == (
        "litigation-blocked",
        "litigation-watch-a",
        "litigation-watch-b",
    )
    for row in forward.rows:
        assert row.reason_codes == tuple(sorted(row.reason_codes))
    assert forward.reason_codes == tuple(sorted(forward.reason_codes))
    assert tuple(item.reason_code for item in forward.reason_code_counts) == tuple(
        sorted(item.reason_code for item in forward.reason_code_counts),
    )


def test_non_default_thresholds_can_downgrade_moderate_litigation_shift() -> None:
    cfg = config(
        watch_litigation_shift_score=d("0.500000"),
        blocked_litigation_shift_score=d("0.900000"),
        material_ruling_shift_count=d("2.000000"),
        high_ruling_shift_count=d("4.000000"),
    )

    digest = report(
        observation(
            "source-moderate",
            "litigation-moderate",
            ruling_shift_count="1.000000",
            ballot_deadline_days="45.000000",
        ),
        cfg=cfg,
    )

    assert digest.digest_status == "ready"
    assert digest.recommended_next_step == (
        "allow_report_only_market_research_policy_ballot_access_litigation_shift_digest"
    )
    assert digest.rows[0].digest_status == "ready"
    assert digest.rows[0].litigation_shift_score == d("0.087500")
    assert digest.rows[0].reason_codes == (
        "market_research_policy_ballot_access_litigation_shift_digest_ready",
    )


def test_validation_rejects_bad_inputs_and_inconsistent_public_records() -> None:
    module = api()

    with pytest.raises(ValueError, match="ruling_shift_count must be a Decimal"):
        observation(ruling_shift_count=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="ruling_shift_count must be nonnegative"):
        observation(ruling_shift_count="-1.000000")
    with pytest.raises(ValueError, match="source_count must be integral"):
        observation(source_count="1.500000")
    with pytest.raises(ValueError, match="observed_at must be UTC-aware"):
        observation(observed_at=datetime(2026, 7, 6, 15, 45))
    with pytest.raises(ValueError, match="observed_at must be UTC-aware"):
        observation(observed_at=datetime(2026, 7, 6, 15, 45, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report(generated_at=_DateTimeSubclass(2026, 7, 6, 16, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at must not be in the future"):
        report(observation("source-future", "litigation-future", observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="observations must contain"):
        report("not-an-observation")
    with pytest.raises(ValueError, match="litigation_id values must be unique"):
        report(
            observation("source-dupe-a", "litigation-dupe"),
            observation("source-dupe-b", "litigation-dupe"),
        )
    with pytest.raises(ValueError, match="watch_litigation_shift_score"):
        config(
            watch_litigation_shift_score=d("0.900000"),
            blocked_litigation_shift_score=d("0.500000"),
        )
    with pytest.raises(TypeError, match="does not support subclassing"):
        class BadConfig(module.PolicyBallotAccessLitigationShiftDigestConfig):
            pass

    valid_row = report(observation("source-valid", "litigation-valid")).rows[0]
    with pytest.raises(ValueError, match="litigation_shift_score"):
        replace(valid_row, litigation_shift_score=d("0.990000"))
    risky_row = report(
        observation(
            "source-reason",
            "litigation-reason",
            ruling_shift_count="2.000000",
            adverse_ruling_count="1.000000",
        ),
    ).rows[0]
    with pytest.raises(ValueError, match="reason_codes must use canonical sequence"):
        replace(risky_row, reason_codes=tuple(reversed(risky_row.reason_codes)))

    frozen_observation = observation("source-frozen", "litigation-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.source_id = "changed"  # type: ignore[misc]


def test_reason_counts_reject_zero_fractional_and_must_reconcile_with_rows() -> None:
    module = api()
    digest = report(observation("source-reason-counts", "litigation-reason-counts"))
    ready_reason = (
        "market_research_policy_ballot_access_litigation_shift_digest_ready"
    )

    with pytest.raises(ValueError, match="count must be positive"):
        module.PolicyBallotAccessLitigationShiftReasonCodeCount(
            reason_code=ready_reason,
            count=d("0.000000"),
            observation_ratio=d("0.000000"),
        )
    with pytest.raises(ValueError, match="count must be integral"):
        module.PolicyBallotAccessLitigationShiftReasonCodeCount(
            reason_code=ready_reason,
            count=d("1.500000"),
            observation_ratio=d("1.000000"),
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            digest,
            reason_code_counts=(
                replace(digest.reason_code_counts[0], count=d("2.000000")),
            ),
        )
    with pytest.raises(ValueError, match="reason_code_counts must be a tuple"):
        replace(digest, reason_code_counts=list(digest.reason_code_counts))


def test_hard_flags_are_enforced_on_all_public_records() -> None:
    digest = report(observation("source-flags", "litigation-flags"))
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in digest.rows)
    assert all(
        item.paper_only and item.report_only and item.readonly
        for item in digest.reason_code_counts
    )

    with pytest.raises(ValueError, match="config paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="observation report_only must be True"):
        replace(observation("source-report-only", "litigation-report-only"), report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(digest.rows[0], readonly=False)
    with pytest.raises(ValueError, match="reason code count paper_only must be True"):
        replace(digest.reason_code_counts[0], paper_only=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(digest, paper_only=False)


def test_public_numerics_payload_serialization_and_tamper_revalidation() -> None:
    module = api()
    digest = report(observation("source-payload", "litigation-payload"))

    payload = module.market_research_policy_ballot_access_litigation_shift_digest_payload(
        digest,
    )
    payload_text = repr(payload).lower()
    for forbidden in (
        "as" + "dict",
        "market" + "_" + "slug",
        "ques" + "tion",
        "payload" + "_" + "json",
        "wa" + "llet",
        "or" + "der",
        "au" + "th",
        "pri" + "vate",
        "k" + "ey",
    ):
        assert forbidden not in payload_text
    assert isinstance(payload, MappingProxyType)
    assert payload["generated_at"] == "2026-07-06T16:00:00+00:00"
    assert payload["observation_count"] == "1.000000"
    assert payload["average_litigation_shift_score"] == "0.000000"
    assert payload["rows"][0]["observed_at"] == "2026-07-06T15:45:00+00:00"
    assert payload["rows"][0]["litigation_shift_score"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert {"market_slug", "question", "payload_json"}.isdisjoint(payload)
    assert {"market_slug", "question", "payload_json"}.isdisjoint(payload["rows"][0])
    assert not any(isinstance(item, Decimal | datetime | float) for item in walk_payload(payload))
    with pytest.raises(TypeError):
        payload["observation_count"] = "0.000000"  # type: ignore[index]
    with pytest.raises(TypeError):
        payload["rows"][0]["litigation_shift_score"] = "1.000000"  # type: ignore[index]

    for public_record in (
        config(),
        observation("source-numeric", "litigation-numeric"),
        digest.rows[0],
        digest.reason_code_counts[0],
        digest,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        assert {"market_slug", "question", "payload_json"}.isdisjoint(
            {field.name for field in fields(public_record)},
        )
        for hint in get_type_hints(type(public_record)).values():
            assert not type_uses_float(hint)
        for field in fields(public_record):
            value = getattr(public_record, field.name)
            if type(value) is Decimal:
                assert value.as_tuple().exponent == -6, field.name

    tampered_numeric = report(observation("source-bad-numeric", "litigation-bad-numeric"))
    object.__setattr__(tampered_numeric, "observation_count", 1)
    with pytest.raises(ValueError, match="observation_count must be a Decimal"):
        module.market_research_policy_ballot_access_litigation_shift_digest_payload(
            tampered_numeric,
        )

    tampered_time = report(observation("source-bad-time", "litigation-bad-time"))
    object.__setattr__(
        tampered_time,
        "generated_at",
        datetime(2026, 7, 6, 12, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    with pytest.raises(ValueError, match="generated_at must be UTC"):
        module.market_research_policy_ballot_access_litigation_shift_digest_payload(
            tampered_time,
        )

    tampered_decimal = report(
        observation(
            "source-bad-decimal",
            "litigation-bad-decimal",
            ruling_shift_count="1.000000",
            appeal_pending_count="1.000000",
        ),
    )
    object.__setattr__(tampered_decimal.rows[0], "litigation_shift_score", d("0.4250000"))
    with pytest.raises(ValueError, match="six-decimal"):
        module.market_research_policy_ballot_access_litigation_shift_digest_payload(
            tampered_decimal,
        )

    tampered_reason = report(
        observation(
            "source-bad-reason",
            "litigation-bad-reason",
            ruling_shift_count="2.000000",
            adverse_ruling_count="1.000000",
        ),
    )
    object.__setattr__(
        tampered_reason.rows[0],
        "reason_codes",
        tuple(reversed(tampered_reason.rows[0].reason_codes)),
    )
    with pytest.raises(ValueError, match="reason_codes must use canonical sequence"):
        module.market_research_policy_ballot_access_litigation_shift_digest_payload(
            tampered_reason,
        )

    tampered_flag = report(observation("source-bad-flag", "litigation-bad-flag"))
    object.__setattr__(tampered_flag.reason_code_counts[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        module.market_research_policy_ballot_access_litigation_shift_digest_payload(
            tampered_flag,
        )

    tampered_rows = report(observation("source-bad-rows", "litigation-bad-rows"))
    object.__setattr__(tampered_rows, "rows", ({"not": "a row"},))
    with pytest.raises(ValueError, match="rows"):
        module.market_research_policy_ballot_access_litigation_shift_digest_payload(
            tampered_rows,
        )


def test_module_scope_excludes_forbidden_surfaces_and_io() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    tree = ast.parse(source)

    for forbidden in (
        "as" + "dict",
        "market" + "_" + "slug",
        "ques" + "tion",
        "payload" + "_" + "json",
        "wa" + "llet",
        "or" + "der",
        "au" + "th",
        "pri" + "vate",
        "database",
        "supabase",
        "persist",
        "sqlite",
        "broker",
        "signing",
        "submit",
        "cancel",
    ):
        assert forbidden not in lowered

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            callee_name = ""
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in {
                "open",
                "read",
                "write",
                "submit",
                "cancel",
                "replace",
                "connect",
                "execute",
                "getenv",
            }
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_fragments = (
        "db",
        "env",
        "cli",
        "psycopg",
        "requests",
        "socket",
        "urllib",
        "sqlite",
        "subprocess",
        "httpx",
        "pathlib",
        "os",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def walk_payload(value: object):
    if isinstance(value, Mapping):
        for item in value.values():
            yield from walk_payload(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk_payload(item)
    else:
        yield value


def type_uses_float(hint: object) -> bool:
    if hint is float:
        return True
    return any(type_uses_float(arg) for arg in get_args(hint))

from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timezone, timedelta, tzinfo
from decimal import ROUND_DOWN, Decimal, localcontext
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_team_domain_signal_review_backlog_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_team_domain_signal_review_backlog_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "pending_load_watch_threshold": d("0.500000"),
        "pending_load_block_threshold": d("1.000000"),
        "stale_signal_watch_threshold": d("0.250000"),
        "stale_signal_block_threshold": d("0.500000"),
        "conflict_signal_watch_threshold": d("0.100000"),
        "conflict_signal_block_threshold": d("0.300000"),
        "review_age_watch_hours": d("24.000000"),
        "review_age_block_hours": d("72.000000"),
        "memory_gap_watch_threshold": d("0.250000"),
        "memory_gap_block_threshold": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainSignalReviewBacklogConfig(**values)


def backlog_item(backlog_key: str = "private-backlog-alpha", **overrides: object) -> Any:
    module = api()
    values = {
        "backlog_key": backlog_key,
        "domain_key": "private-domain-alpha",
        "team_key": "private-team-alpha",
        "source_key": "private-source-alpha",
        "reviewer_capacity_points": d("10.000000"),
        "pending_signal_count": d("2"),
        "stale_signal_count": d("0"),
        "conflict_signal_count": d("0"),
        "oldest_unreviewed_age_hours": d("6.000000"),
        "memory_gap_ratio": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainSignalReviewBacklogInput(**values)


def report(
    *values: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_team_domain_signal_review_backlog_report(
        values,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert all(character in "0123456789abcdef" for character in value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned_payload = dict(payload)
    unsigned_payload.pop("validation_digest", None)
    encoded = json.dumps(
        unsigned_payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    resigned = json.loads(json.dumps(payload))
    rows = resigned.get("rows")
    if type(rows) is list:
        for row in rows:
            if type(row) is dict and "validation_digest" in row:
                row["validation_digest"] = canonical_digest(row)
    resigned["validation_digest"] = canonical_digest(resigned)
    return resigned


def assert_public_numeric_payload(value: Any) -> None:
    assert type(value) is not float
    assert type(value) is not int
    assert type(value) is not Decimal
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_payload(item)
    elif isinstance(value, list):
        for item in value:
            assert_public_numeric_payload(item)


def assert_dataclass_numeric_fields_are_decimal(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if type(item) is bool or item is None or type(item) is str:
            continue
        if isinstance(item, datetime):
            assert type(item) is datetime
            continue
        if isinstance(item, tuple):
            for nested in item:
                if is_dataclass(nested):
                    assert_dataclass_numeric_fields_are_decimal(nested)
            continue
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        raise AssertionError(f"{field.name} is not Decimal-only: {item!r}")


def test_signal_review_backlog_report_rolls_up_statuses_sorts_and_hashes() -> None:
    passing = backlog_item(
        "pass-backlog-secret",
        domain_key="pass-domain-secret",
        team_key="pass-team-secret",
        source_key="pass-source-secret",
        reviewer_capacity_points=d("10.000000"),
        pending_signal_count=d("2"),
        stale_signal_count=d("0"),
        conflict_signal_count=d("0"),
        oldest_unreviewed_age_hours=d("6.000000"),
        memory_gap_ratio=d("0.100000"),
    )
    watched = backlog_item(
        "watch-backlog-secret",
        domain_key="watch-domain-secret",
        team_key="watch-team-secret",
        source_key="watch-source-secret",
        reviewer_capacity_points=d("10.000000"),
        pending_signal_count=d("6"),
        stale_signal_count=d("2"),
        conflict_signal_count=d("1"),
        oldest_unreviewed_age_hours=d("36.000000"),
        memory_gap_ratio=d("0.300000"),
    )
    blocked = backlog_item(
        "block-backlog-secret",
        domain_key="block-domain-secret",
        team_key="block-team-secret",
        source_key="block-source-secret",
        reviewer_capacity_points=d("10.000000"),
        pending_signal_count=d("12"),
        stale_signal_count=d("6"),
        conflict_signal_count=d("4"),
        oldest_unreviewed_age_hours=d("96.000000"),
        memory_gap_ratio=d("0.600000"),
    )

    result = report(passing, blocked, watched)
    rebuilt = report(watched, passing, blocked)
    changed = report(
        passing,
        watched,
        backlog_item(
            "block-backlog-secret",
            domain_key="block-domain-secret",
            team_key="block-team-secret",
            source_key="block-source-secret",
            reviewer_capacity_points=d("10.000000"),
            pending_signal_count=d("12"),
            stale_signal_count=d("5"),
            conflict_signal_count=d("4"),
            oldest_unreviewed_age_hours=d("96.000000"),
            memory_gap_ratio=d("0.600000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == (
        "research-team-domain-signal-review-backlog-report-v1"
    )
    assert result.backlog_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.total_pending_signal_count == d("20")
    assert result.total_stale_signal_count == d("8")
    assert result.total_conflict_signal_count == d("5")
    assert result.report_status == "block"
    assert result.max_backlog_score == d("1.000000")
    assert result.reason_codes == (
        "pending_load_block",
        "pending_load_watch",
        "stale_signal_block",
        "stale_signal_watch",
        "conflict_signal_block",
        "conflict_signal_watch",
        "review_age_block",
        "review_age_watch",
        "memory_gap_block",
        "memory_gap_watch",
        "domain_signal_review_backlog_pass",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.validation_digest)
    assert_dataclass_numeric_fields_are_decimal(result)

    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")
    blocked_row = result.rows[0]
    assert blocked_row.backlog_fingerprint == hashlib.sha256(
        b"block-backlog-secret",
    ).hexdigest()
    assert blocked_row.domain_fingerprint == hashlib.sha256(
        b"block-domain-secret",
    ).hexdigest()
    assert blocked_row.team_fingerprint == hashlib.sha256(
        b"block-team-secret",
    ).hexdigest()
    assert blocked_row.source_fingerprint == hashlib.sha256(
        b"block-source-secret",
    ).hexdigest()
    assert not hasattr(blocked_row, "backlog_key")
    assert not hasattr(blocked_row, "team_key")
    assert not hasattr(blocked_row, "source_key")
    assert blocked_row.pending_load_ratio == d("1.200000")
    assert blocked_row.stale_signal_ratio == d("0.500000")
    assert blocked_row.conflict_signal_ratio == d("0.333333")
    assert blocked_row.backlog_score == d("1.000000")
    assert blocked_row.manual_review_priority_score == d("1.000000")
    assert blocked_row.priority_rank == d("1")
    assert blocked_row.status == "block"
    assert blocked_row.reason_codes == (
        "pending_load_block",
        "stale_signal_block",
        "conflict_signal_block",
        "review_age_block",
        "memory_gap_block",
    )

    watched_row = result.rows[1]
    assert watched_row.pending_load_ratio == d("0.600000")
    assert watched_row.backlog_score == d("0.584445")
    assert watched_row.manual_review_priority_score == watched_row.backlog_score
    assert watched_row.priority_rank == d("2")
    assert watched_row.status == "watch"

    pass_row = result.rows[2]
    assert pass_row.backlog_score == d("0.096667")
    assert pass_row.manual_review_priority_score == pass_row.backlog_score
    assert pass_row.priority_rank == d("3")
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == ("domain_signal_review_backlog_pass",)

    assert rebuilt.validation_digest == result.validation_digest
    assert changed.validation_digest != result.validation_digest


def test_manual_review_priority_uses_stable_private_fingerprint_tie_breaks() -> None:
    items = (
        backlog_item(
            "private-backlog-zeta",
            domain_key="private-domain-shared",
            team_key="private-team-zeta",
            source_key="private-source-alpha",
        ),
        backlog_item(
            "private-backlog-alpha",
            domain_key="private-domain-shared",
            team_key="private-team-alpha",
            source_key="private-source-zeta",
        ),
        backlog_item(
            "private-backlog-beta",
            domain_key="private-domain-shared",
            team_key="private-team-alpha",
            source_key="private-source-alpha",
        ),
    )

    result = report(*reversed(items))
    expected = tuple(
        sorted(
            items,
            key=lambda item: (
                hashlib.sha256(item.team_key.encode("utf-8")).hexdigest(),
                hashlib.sha256(item.domain_key.encode("utf-8")).hexdigest(),
                hashlib.sha256(item.source_key.encode("utf-8")).hexdigest(),
                hashlib.sha256(item.backlog_key.encode("utf-8")).hexdigest(),
            ),
        ),
    )

    assert tuple(row.priority_rank for row in result.rows) == (
        d("1"),
        d("2"),
        d("3"),
    )
    assert tuple(row.team_fingerprint for row in result.rows) == tuple(
        hashlib.sha256(item.team_key.encode("utf-8")).hexdigest()
        for item in expected
    )
    assert tuple(row.source_fingerprint for row in result.rows) == tuple(
        hashlib.sha256(item.source_key.encode("utf-8")).hexdigest()
        for item in expected
    )
    assert tuple(row.backlog_fingerprint for row in result.rows) == tuple(
        hashlib.sha256(item.backlog_key.encode("utf-8")).hexdigest()
        for item in expected
    )


def test_empty_report_blocks_with_decimal_zeroes() -> None:
    module = api()
    result = report()

    assert result.backlog_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.block_count == d("0")
    assert result.total_pending_signal_count == d("0")
    assert result.total_stale_signal_count == d("0")
    assert result.total_conflict_signal_count == d("0")
    assert result.max_backlog_score is None
    assert result.report_status == "block"
    assert result.reason_codes == (
        "research_team_domain_signal_review_backlog_report_empty",
    )
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.validation_digest)

    payload = module.research_team_domain_signal_review_backlog_report_payload(result)
    assert payload["backlog_count"] == "0"
    assert payload["rows"] == []
    assert_public_numeric_payload(payload)


def test_payload_is_json_ready_deterministic_and_rejects_private_surfaces() -> None:
    module = api()
    private_team = "private-team-with-human-reviewers"
    private_source = "private-source-with-internal-routing"
    private_value = (
        "candidate-alpha|market-123|event-slug|Will this happen?|"
        "https://example.test/feed?token=secret|dsn|table|wallet|order|trade"
    )
    result = report(
        backlog_item(
            private_value,
            domain_key="domain-with-source-url-and-question-private",
            team_key=private_team,
            source_key=private_source,
        ),
    )

    payload = module.research_team_domain_signal_review_backlog_report_payload(result)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)

    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["config_version"] == (
        "research-team-domain-signal-review-backlog-report-v1"
    )
    assert payload["rows"][0]["backlog_fingerprint"] == result.rows[0].backlog_fingerprint
    assert payload["validation_digest"] == result.validation_digest
    assert private_value not in encoded
    assert "candidate-alpha" not in encoded
    assert "market-123" not in encoded
    assert "event-slug" not in encoded
    assert "Will this happen?" not in encoded
    assert "https://example.test" not in encoded
    assert "token=secret" not in encoded
    assert "source-url" not in encoded
    assert "question-private" not in encoded
    assert "wallet" not in encoded
    assert "order" not in encoded
    assert "trade" not in encoded
    assert private_team not in encoded
    assert private_source not in encoded
    assert payload["rows"][0]["team_fingerprint"] == hashlib.sha256(
        private_team.encode("utf-8"),
    ).hexdigest()
    assert payload["rows"][0]["source_fingerprint"] == hashlib.sha256(
        private_source.encode("utf-8"),
    ).hexdigest()
    assert_public_numeric_payload(payload)
    assert module.research_team_domain_signal_review_backlog_report_payload(payload) == payload

    with pytest.raises(ValueError, match="readonly"):
        module.research_team_domain_signal_review_backlog_report_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="unsafe"):
        module.research_team_domain_signal_review_backlog_report_payload(
            {**payload, "candidate_id": "raw-candidate"},
        )
    with pytest.raises(ValueError, match="numeric"):
        module.research_team_domain_signal_review_backlog_report_payload(
            {**payload, "backlog_count": 1},
        )
    with pytest.raises(ValueError, match="numeric"):
        module.research_team_domain_signal_review_backlog_report_payload(
            {**payload, "pass_count": 1.0},
        )
    with pytest.raises(ValueError, match="validation_digest"):
        module.research_team_domain_signal_review_backlog_report_payload(
            {**payload, "block_count": "1"},
        )


def test_public_mapping_rejects_raw_decimal_and_nested_dataclass_values() -> None:
    module = api()
    result = report(backlog_item())
    payload = module.research_team_domain_signal_review_backlog_report_payload(result)

    with pytest.raises(ValueError, match="Decimal string|public schema"):
        module.research_team_domain_signal_review_backlog_report_payload(
            {**payload, "backlog_count": d("1")},
        )

    with pytest.raises(ValueError, match="rows\\[0\\].*object|public schema"):
        module.research_team_domain_signal_review_backlog_report_payload(
            {**payload, "rows": [result.rows[0]]},
        )


def test_invalid_inputs_config_flags_and_datetimes_are_rejected() -> None:
    module = api()

    assert module.DOMAIN_SIGNAL_REVIEW_BACKLOG_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    with pytest.raises(ValueError, match="reviewer_capacity_points"):
        backlog_item(reviewer_capacity_points=d("0"))
    with pytest.raises(ValueError, match="pending_signal_count"):
        backlog_item(pending_signal_count=d("2.500000"))
    with pytest.raises(ValueError, match="stale_signal_count"):
        backlog_item(stale_signal_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="memory_gap_ratio"):
        backlog_item(memory_gap_ratio=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="stale_signal_count"):
        backlog_item(pending_signal_count=d("2"), stale_signal_count=d("3"))
    with pytest.raises(ValueError, match="conflict_signal_count"):
        backlog_item(pending_signal_count=d("2"), conflict_signal_count=d("3"))
    with pytest.raises(ValueError, match="memory_gap_ratio"):
        backlog_item(memory_gap_ratio=d("1.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(backlog_item(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            backlog_item(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(
            backlog_item(),
            generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="paper_only"):
        backlog_item(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report(backlog_item()), readonly=False)
    with pytest.raises(ValueError, match="watch threshold must not exceed block threshold"):
        config(
            memory_gap_watch_threshold=d("0.600000"),
            memory_gap_block_threshold=d("0.500000"),
        )

    shifted = report(
        backlog_item(),
        generated_at=datetime(2026, 7, 8, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )
    assert shifted.generated_at == GENERATED_AT


@pytest.mark.parametrize(
    ("watch_field", "block_field"),
    (
        ("pending_load_watch_threshold", "pending_load_block_threshold"),
        ("stale_signal_watch_threshold", "stale_signal_block_threshold"),
        ("conflict_signal_watch_threshold", "conflict_signal_block_threshold"),
        ("review_age_watch_hours", "review_age_block_hours"),
        ("memory_gap_watch_threshold", "memory_gap_block_threshold"),
    ),
)
def test_config_rejects_raw_threshold_inversions_before_quantization(
    watch_field: str,
    block_field: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="watch threshold must not exceed block threshold",
    ):
        config(
            **{
                watch_field: d("0.50000049"),
                block_field: d("0.50000040"),
            },
        )


@pytest.mark.parametrize(
    ("watch_field", "block_field"),
    (
        ("pending_load_watch_threshold", "pending_load_block_threshold"),
        ("stale_signal_watch_threshold", "stale_signal_block_threshold"),
        ("conflict_signal_watch_threshold", "conflict_signal_block_threshold"),
        ("memory_gap_watch_threshold", "memory_gap_block_threshold"),
    ),
)
@pytest.mark.parametrize("block_value", (d("0"), d("0.0000004")))
def test_config_score_denominators_must_remain_positive(
    watch_field: str,
    block_field: str,
    block_value: Decimal,
) -> None:
    with pytest.raises(ValueError, match=block_field):
        config(
            **{
                watch_field: d("0"),
                block_field: block_value,
            },
        )


def test_datetime_normalization_rejects_values_outside_utc_range() -> None:
    module = api()
    before_utc_range = datetime(
        1,
        1,
        1,
        tzinfo=timezone(timedelta(hours=14)),
    )
    after_utc_range = datetime(
        9999,
        12,
        31,
        23,
        59,
        59,
        tzinfo=timezone(timedelta(hours=-14)),
    )

    for generated_at in (before_utc_range, after_utc_range):
        with pytest.raises(ValueError, match="generated_at.*UTC"):
            report(generated_at=generated_at)

    payload = module.research_team_domain_signal_review_backlog_report_payload(
        report(),
    )
    forged = {**payload, "generated_at": "0001-01-01T00:00:00+14:00"}
    with pytest.raises(ValueError, match="generated_at.*UTC"):
        module.research_team_domain_signal_review_backlog_report_payload(
            resign_payload(forged),
        )


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    (
        ("backlog_key", "private-backlog\nalpha"),
        ("domain_key", "private-domain\ud800alpha"),
        ("team_key", "t" * 2049),
        ("source_key", "private-source\x7falpha"),
    ),
)
def test_private_keys_require_bounded_canonical_utf8(
    field_name: str,
    invalid_value: str,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        backlog_item(**{field_name: invalid_value})


@pytest.mark.parametrize(
    "invalid_value",
    (
        "custom\nversion",
        "custom-\ud800-version",
        "v" * 2049,
    ),
)
def test_public_text_requires_bounded_canonical_utf8(invalid_value: str) -> None:
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=invalid_value)


def test_build_revalidates_config_after_object_setattr_escape() -> None:
    escaped_config = config()
    object.__setattr__(
        escaped_config,
        "pending_load_watch_threshold",
        d("0.900000"),
    )
    object.__setattr__(
        escaped_config,
        "pending_load_block_threshold",
        d("0.800000"),
    )

    with pytest.raises(ValueError, match="watch threshold must not exceed block threshold"):
        report(
            backlog_item(pending_signal_count=d("8")),
            cfg=escaped_config,
        )


def test_validation_digest_and_report_validation_recompute_fields() -> None:
    result = report(backlog_item())
    row = result.rows[0]

    with pytest.raises(FrozenInstanceError):
        row.status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="backlog_score must match"):
        replace(row, backlog_score=row.backlog_score + d("0.000001"))
    with pytest.raises(ValueError, match="status must match"):
        replace(row, status="block")
    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(row, validation_digest="0" * 64)
    with pytest.raises(ValueError, match="pass_count must match"):
        replace(result, pass_count=result.pass_count + d("1"))
    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(
            result,
            backlog_count=d("2"),
            pass_count=d("2"),
            max_backlog_score=d("0.096667"),
            total_pending_signal_count=d("4"),
            rows=(
                backlog_row("backlog-zeta"),
                backlog_row("backlog-alpha"),
            ),
        )
    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(result, validation_digest="0" * 64)


def test_report_revalidates_rows_and_reason_codes_after_object_setattr_escape() -> None:
    module = api()
    escaped_rows = report(backlog_item())
    object.__setattr__(escaped_rows, "rows", list(escaped_rows.rows))
    object.__setattr__(
        escaped_rows,
        "validation_digest",
        module._validation_digest(module._report_digest_values(escaped_rows)),
    )
    with pytest.raises(ValueError, match="rows"):
        module.research_team_domain_signal_review_backlog_report_payload(escaped_rows)

    escaped_reason_codes = report(
        backlog_item(
            pending_signal_count=d("6"),
            stale_signal_count=d("2"),
            conflict_signal_count=d("1"),
            oldest_unreviewed_age_hours=d("36.000000"),
            memory_gap_ratio=d("0.300000"),
        ),
    )
    escaped_row = escaped_reason_codes.rows[0]
    object.__setattr__(escaped_row, "reason_codes", list(escaped_row.reason_codes))
    object.__setattr__(
        escaped_row,
        "validation_digest",
        module._validation_digest(module._row_digest_values(escaped_row)),
    )
    object.__setattr__(
        escaped_reason_codes,
        "validation_digest",
        module._validation_digest(module._report_digest_values(escaped_reason_codes)),
    )
    with pytest.raises(ValueError, match="reason_codes"):
        module.research_team_domain_signal_review_backlog_report_payload(
            escaped_reason_codes,
        )


@pytest.mark.parametrize(
    "forged_generated_at",
    (
        GENERATED_AT.astimezone(timezone(timedelta(hours=-7))),
        datetime(1, 1, 1, tzinfo=timezone(timedelta(hours=14))),
    ),
)
def test_payload_revalidates_escaped_report_as_canonical_utc(
    forged_generated_at: datetime,
) -> None:
    module = api()
    result = report(backlog_item())
    object.__setattr__(result, "generated_at", forged_generated_at)

    with pytest.raises(ValueError, match="generated_at.*UTC"):
        module.research_team_domain_signal_review_backlog_report_payload(result)


@pytest.mark.parametrize(
    ("field_name", "forged_value"),
    (
        ("backlog_count", d("1.0")),
        ("max_backlog_score", d("0.0966670")),
    ),
)
def test_payload_revalidates_canonical_report_decimals(
    field_name: str,
    forged_value: Decimal,
) -> None:
    module = api()
    result = report(backlog_item())
    object.__setattr__(result, field_name, forged_value)
    object.__setattr__(
        result,
        "validation_digest",
        module._validation_digest(module._report_digest_values(result)),
    )

    with pytest.raises(ValueError, match=rf"{field_name}.*canonical"):
        module.research_team_domain_signal_review_backlog_report_payload(result)


@pytest.mark.parametrize(
    ("field_name", "forged_value", "match"),
    (
        ("status", "forged", "status"),
        (
            "manual_review_priority_score",
            1,
            "manual_review_priority_score.*Decimal",
        ),
        ("team_fingerprint", "not-a-digest", "team_fingerprint"),
    ),
)
def test_direct_report_revalidates_nested_rows_before_sorting(
    field_name: str,
    forged_value: object,
    match: str,
) -> None:
    result = report(backlog_item())
    object.__setattr__(result.rows[0], field_name, forged_value)

    with pytest.raises(ValueError, match=match):
        replace(result)


def test_public_payload_rejects_forged_resigned_derived_fields() -> None:
    module = api()
    payload = module.research_team_domain_signal_review_backlog_report_payload(
        report(backlog_item()),
    )

    forged_reason = json.loads(json.dumps(payload))
    forged_reason["rows"][0]["status"] = "watch"
    forged_reason["rows"][0]["reason_codes"] = ["pending_load_watch"]
    forged_reason["pass_count"] = "0"
    forged_reason["watch_count"] = "1"
    forged_reason["report_status"] = "watch"
    forged_reason["reason_codes"] = ["pending_load_watch"]
    with pytest.raises(ValueError, match="reason_codes|status"):
        module.research_team_domain_signal_review_backlog_report_payload(
            resign_payload(forged_reason),
        )

    forged_score = json.loads(json.dumps(payload))
    forged_score["rows"][0]["pending_load_score"] = "0.300000"
    forged_score["rows"][0]["backlog_score"] = "0.116667"
    forged_score["rows"][0]["manual_review_priority_score"] = "0.116667"
    forged_score["max_backlog_score"] = "0.116667"
    with pytest.raises(ValueError, match="pending_load_score"):
        module.research_team_domain_signal_review_backlog_report_payload(
            resign_payload(forged_score),
        )

    forged_count = {**payload, "backlog_count": "2"}
    with pytest.raises(ValueError, match="backlog_count"):
        module.research_team_domain_signal_review_backlog_report_payload(
            resign_payload(forged_count),
        )

    forged_manual_priority = json.loads(json.dumps(payload))
    forged_manual_priority["rows"][0]["manual_review_priority_score"] = "0.999999"
    with pytest.raises(ValueError, match="manual_review_priority_score"):
        module.research_team_domain_signal_review_backlog_report_payload(
            resign_payload(forged_manual_priority),
        )

    forged_priority_rank = json.loads(json.dumps(payload))
    forged_priority_rank["rows"][0]["priority_rank"] = "2"
    with pytest.raises(ValueError, match="priority_rank"):
        module.research_team_domain_signal_review_backlog_report_payload(
            resign_payload(forged_priority_rank),
        )


def test_public_payload_requires_exact_report_and_row_schemas_when_resigned() -> None:
    module = api()
    payload = module.research_team_domain_signal_review_backlog_report_payload(
        report(backlog_item()),
    )

    extra_report_field = {**payload, "public_note": "backlog"}
    with pytest.raises(ValueError, match="schema"):
        module.research_team_domain_signal_review_backlog_report_payload(
            resign_payload(extra_report_field),
        )

    missing_report_field = dict(payload)
    missing_report_field.pop("report_status")
    with pytest.raises(ValueError, match="schema"):
        module.research_team_domain_signal_review_backlog_report_payload(
            resign_payload(missing_report_field),
        )

    extra_row_field = json.loads(json.dumps(payload))
    extra_row_field["rows"][0]["public_note"] = "backlog"
    with pytest.raises(ValueError, match="schema"):
        module.research_team_domain_signal_review_backlog_report_payload(
            resign_payload(extra_row_field),
        )

    missing_row_field = json.loads(json.dumps(payload))
    missing_row_field["rows"][0].pop("status")
    with pytest.raises(ValueError, match="schema"):
        module.research_team_domain_signal_review_backlog_report_payload(
            resign_payload(missing_row_field),
        )


def test_public_payload_requires_canonical_report_and_row_key_order_when_resigned() -> None:
    module = api()
    payload = module.research_team_domain_signal_review_backlog_report_payload(
        report(backlog_item()),
    )

    reordered_report = {
        key: payload[key]
        for key in reversed(tuple(payload))
    }
    with pytest.raises(ValueError, match="schema"):
        module.research_team_domain_signal_review_backlog_report_payload(
            resign_payload(reordered_report),
        )

    reordered_row = json.loads(json.dumps(payload))
    reordered_row["rows"][0] = {
        key: reordered_row["rows"][0][key]
        for key in reversed(tuple(reordered_row["rows"][0]))
    }
    with pytest.raises(ValueError, match="schema"):
        module.research_team_domain_signal_review_backlog_report_payload(
            resign_payload(reordered_row),
        )


def test_resigned_payload_rejects_duplicate_backlog_fingerprints() -> None:
    module = api()
    payload = module.research_team_domain_signal_review_backlog_report_payload(
        report(backlog_item()),
    )
    duplicated = json.loads(json.dumps(payload))
    second_row = dict(duplicated["rows"][0])
    second_row["priority_rank"] = "2"
    duplicated.update(
        {
            "backlog_count": "2",
            "pass_count": "2",
            "total_pending_signal_count": "4",
            "total_stale_signal_count": "0",
            "total_conflict_signal_count": "0",
            "rows": [duplicated["rows"][0], second_row],
        },
    )

    with pytest.raises(ValueError, match="backlog_fingerprint.*unique"):
        module.research_team_domain_signal_review_backlog_report_payload(
            resign_payload(duplicated),
        )


def test_decimal_validation_rejects_signed_zero_and_quantized_zero_aliases() -> None:
    with pytest.raises(ValueError, match="reviewer_capacity_points"):
        backlog_item(reviewer_capacity_points=d("0.0000004"))
    with pytest.raises(ValueError, match="pending_signal_count"):
        backlog_item(pending_signal_count=d("-0"))
    with pytest.raises(ValueError, match="memory_gap_ratio"):
        backlog_item(memory_gap_ratio=d("-0.000000"))
    with pytest.raises(ValueError, match="memory_gap_watch_threshold"):
        config(memory_gap_watch_threshold=d("-0.000000"))

    with pytest.raises(ValueError, match="oldest_unreviewed_age_hours"):
        backlog_item(oldest_unreviewed_age_hours=d("-0.0000004"))
    with pytest.raises(ValueError, match="memory_gap_ratio"):
        backlog_item(memory_gap_ratio=d("1.0000004"))


def test_zero_pending_count_requires_zero_oldest_unreviewed_age() -> None:
    with pytest.raises(ValueError, match="oldest_unreviewed_age_hours"):
        backlog_item(
            pending_signal_count=d("0"),
            oldest_unreviewed_age_hours=d("0.000001"),
        )


def test_resigned_row_rejects_age_without_pending_signals() -> None:
    module = api()
    row_values = module._row_digest_values(report(backlog_item()).rows[0])
    row_values.update(
        {
            "pending_signal_count": d("0"),
            "pending_load_ratio": d("0.000000"),
            "pending_load_score": d("0.000000"),
            "backlog_score": d("0.056667"),
            "manual_review_priority_score": d("0.056667"),
        },
    )

    with pytest.raises(ValueError, match="oldest_unreviewed_age_hours"):
        module.ResearchTeamDomainSignalReviewBacklogRow(
            **row_values,
            validation_digest=module._validation_digest(row_values),
        )


def test_decimal_math_is_independent_of_ambient_context() -> None:
    values = {
        "reviewer_capacity_points": d("1000000000.000000"),
        "pending_signal_count": d("123456789"),
        "stale_signal_count": d("12345678"),
        "conflict_signal_count": d("1234567"),
        "oldest_unreviewed_age_hours": d("71.999999"),
        "memory_gap_ratio": d("0.499999"),
    }
    expected = report(backlog_item(**values))

    with localcontext() as hostile_context:
        hostile_context.prec = 4
        hostile_context.rounding = ROUND_DOWN
        actual = report(backlog_item(**values))

    assert actual == expected
    assert actual.validation_digest == expected.validation_digest


def test_decimal_values_and_arithmetic_must_fit_the_fixed_context() -> None:
    with pytest.raises(ValueError, match="reviewer_capacity_points.*fixed context"):
        backlog_item(reviewer_capacity_points=d("1E+1000000"))

    maximum_context_count = d("9" * 64)
    oversized_ratio_item = backlog_item(
        reviewer_capacity_points=d("0.000001"),
        pending_signal_count=maximum_context_count,
    )
    with pytest.raises(ValueError, match="ratio.*fixed context"):
        report(oversized_ratio_item)


@pytest.mark.parametrize(
    ("field_name", "forged_value"),
    (
        ("pending_signal_count", "-0"),
        ("pending_signal_count", "NaN"),
        ("stale_signal_count", "Infinity"),
        ("oldest_unreviewed_age_hours", "-0.000000"),
        ("memory_gap_ratio", "1.0000004"),
        ("manual_review_priority_score", "sNaN"),
    ),
)
def test_resigned_payload_rejects_raw_bounds_signed_zero_and_non_finite(
    field_name: str,
    forged_value: str,
) -> None:
    module = api()
    payload = module.research_team_domain_signal_review_backlog_report_payload(
        report(backlog_item()),
    )
    forged = json.loads(json.dumps(payload))
    forged["rows"][0][field_name] = forged_value

    with pytest.raises(ValueError, match=field_name):
        module.research_team_domain_signal_review_backlog_report_payload(
            resign_payload(forged),
        )


def test_public_dataclasses_are_frozen_and_final() -> None:
    module = api()
    public_dataclasses = (
        module.ResearchTeamDomainSignalReviewBacklogConfig,
        module.ResearchTeamDomainSignalReviewBacklogInput,
        module.ResearchTeamDomainSignalReviewBacklogRow,
        module.ResearchTeamDomainSignalReviewBacklogReport,
    )

    for public_dataclass in public_dataclasses:
        assert is_dataclass(public_dataclass)
        assert public_dataclass.__dataclass_params__.frozen is True
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Forged{public_dataclass.__name__}", (public_dataclass,), {})


def backlog_row(backlog_key: str) -> Any:
    return report(backlog_item(backlog_key)).rows[0]


def test_module_is_pure_readonly_report_only_and_contains_no_io_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "private_token",
        "wallet",
        "auth",
        "order",
        "live",
        "trading",
        "execution",
        "position_size",
        "sizing",
        "buy",
        "sell",
        "recommend",
        "persist",
        "database",
        "sqlite",
        "sqlalchemy",
        "psycopg",
        "supabase",
        "web3",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
        "network",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {
                    "__import__",
                    "commit",
                    "connect",
                    "execute",
                    "float",
                    "open",
                    "persist",
                    "request",
                    "save",
                    "send",
                    "urlopen",
                    "write",
                }
            elif isinstance(func, ast.Attribute):
                assert func.attr not in {
                    "commit",
                    "connect",
                    "execute",
                    "persist",
                    "post",
                    "put",
                    "request",
                    "save",
                    "send",
                    "urlopen",
                    "write",
                    "write_bytes",
                    "write_text",
                }

    assert imported_roots <= {
        "__future__",
        "collections",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "polymarket_alpha_lab",
        "typing",
    }

from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timezone, timedelta, tzinfo
from decimal import Context, Decimal, localcontext
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_team_domain_review_disagreement_queue_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_team_domain_review_disagreement_queue_report.py",
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
        "reviewer_disagreement_watch_threshold": d("0.250000"),
        "reviewer_disagreement_block_threshold": d("0.500000"),
        "probability_spread_watch_threshold": d("0.100000"),
        "probability_spread_block_threshold": d("0.250000"),
        "evidence_conflict_watch_threshold": d("0.250000"),
        "evidence_conflict_block_threshold": d("0.500000"),
        "unresolved_blocker_watch_threshold": d("1"),
        "unresolved_blocker_block_threshold": d("2"),
        "queue_age_watch_hours": d("24.000000"),
        "queue_age_block_hours": d("72.000000"),
        "prior_resolution_miss_watch_threshold": d("1"),
        "prior_resolution_miss_block_threshold": d("2"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainReviewDisagreementQueueConfig(**values)


def queue_item(queue_key: str = "private-queue-alpha", **overrides: object) -> Any:
    module = api()
    values = {
        "queue_key": queue_key,
        "domain_key": "private-domain-alpha",
        "reviewer_count": d("4"),
        "disagreeing_reviewer_count": d("0"),
        "probability_spread": d("0.050000"),
        "evidence_conflict_ratio": d("0.100000"),
        "unresolved_blocker_count": d("0"),
        "queued_at": GENERATED_AT - timedelta(hours=6),
        "prior_resolution_miss_count": d("0"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainReviewDisagreementQueueInput(**values)


def report(
    *values: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_team_domain_review_disagreement_queue_report(
        values,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert all(character in "0123456789abcdef" for character in value)


def payload_digest(value: dict[str, Any]) -> str:
    unsigned = {key: item for key, item in value.items() if key != "validation_digest"}
    encoded = json.dumps(
        unsigned,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def recompute_validation_digests(payload: dict[str, Any]) -> dict[str, Any]:
    recomputed = dict(payload)
    recomputed_rows: list[dict[str, Any]] = []
    for row in recomputed.get("rows", []):
        recomputed_row = dict(row)
        recomputed_row["validation_digest"] = payload_digest(recomputed_row)
        recomputed_rows.append(recomputed_row)
    recomputed["rows"] = recomputed_rows
    recomputed["validation_digest"] = payload_digest(recomputed)
    return recomputed


def resign_report_object(value: Any) -> None:
    module = api()
    for row in value.rows:
        object.__setattr__(
            row,
            "validation_digest",
            module._validation_digest(module._row_digest_values(row)),
        )
    object.__setattr__(
        value,
        "validation_digest",
        module._validation_digest(module._report_digest_values(value)),
    )


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


def test_disagreement_queue_report_rolls_up_statuses_sorts_and_hashes() -> None:
    passing = queue_item(
        "pass-queue-secret",
        domain_key="pass-domain-secret",
        disagreeing_reviewer_count=d("0"),
        probability_spread=d("0.050000"),
        evidence_conflict_ratio=d("0.100000"),
        unresolved_blocker_count=d("0"),
        queued_at=GENERATED_AT - timedelta(hours=6),
        prior_resolution_miss_count=d("0"),
    )
    watched = queue_item(
        "watch-queue-secret",
        domain_key="watch-domain-secret",
        disagreeing_reviewer_count=d("1"),
        probability_spread=d("0.150000"),
        evidence_conflict_ratio=d("0.300000"),
        unresolved_blocker_count=d("1"),
        queued_at=GENERATED_AT - timedelta(hours=36),
        prior_resolution_miss_count=d("1"),
    )
    blocked = queue_item(
        "block-queue-secret",
        domain_key="block-domain-secret",
        disagreeing_reviewer_count=d("2"),
        probability_spread=d("0.300000"),
        evidence_conflict_ratio=d("0.600000"),
        unresolved_blocker_count=d("2"),
        queued_at=GENERATED_AT - timedelta(hours=96),
        prior_resolution_miss_count=d("2"),
    )

    result = report(passing, blocked, watched)
    rebuilt = report(watched, passing, blocked)
    changed = report(
        passing,
        watched,
        queue_item(
            "block-queue-secret",
            domain_key="block-domain-secret",
            disagreeing_reviewer_count=d("2"),
            probability_spread=d("0.240000"),
            evidence_conflict_ratio=d("0.600000"),
            unresolved_blocker_count=d("2"),
            queued_at=GENERATED_AT - timedelta(hours=96),
            prior_resolution_miss_count=d("2"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == (
        "research-team-domain-review-disagreement-queue-report-v1"
    )
    assert result.queue_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.report_status == "block"
    assert result.max_disagreement_queue_score == d("1.000000")
    assert result.reason_codes == (
        "reviewer_disagreement_block",
        "reviewer_disagreement_watch",
        "probability_spread_block",
        "probability_spread_watch",
        "evidence_conflict_block",
        "evidence_conflict_watch",
        "unresolved_blocker_block",
        "unresolved_blocker_watch",
        "queue_age_block",
        "queue_age_watch",
        "prior_resolution_miss_block",
        "prior_resolution_miss_watch",
        "domain_review_disagreement_queue_pass",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.validation_digest)
    assert_dataclass_numeric_fields_are_decimal(result)

    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")
    blocked_row = result.rows[0]
    assert blocked_row.queue_fingerprint == hashlib.sha256(
        b"block-queue-secret",
    ).hexdigest()
    assert blocked_row.domain_fingerprint == hashlib.sha256(
        b"block-domain-secret",
    ).hexdigest()
    assert not hasattr(blocked_row, "queue_key")
    assert blocked_row.reviewer_disagreement_ratio == d("0.500000")
    assert blocked_row.disagreement_queue_score == d("1.000000")
    assert blocked_row.status == "block"
    assert blocked_row.reason_codes == (
        "reviewer_disagreement_block",
        "probability_spread_block",
        "evidence_conflict_block",
        "unresolved_blocker_block",
        "queue_age_block",
        "prior_resolution_miss_block",
    )

    watched_row = result.rows[1]
    assert watched_row.reviewer_disagreement_ratio == d("0.250000")
    assert watched_row.disagreement_queue_score == d("0.533333")
    assert watched_row.status == "watch"

    pass_row = result.rows[2]
    assert pass_row.disagreement_queue_score == d("0.080556")
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == ("domain_review_disagreement_queue_pass",)

    assert rebuilt.validation_digest == result.validation_digest
    assert changed.validation_digest != result.validation_digest


def test_empty_report_blocks_with_decimal_zeroes() -> None:
    module = api()
    result = report()

    assert result.queue_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.block_count == d("0")
    assert result.max_disagreement_queue_score is None
    assert result.report_status == "block"
    assert result.reason_codes == (
        "research_team_domain_review_disagreement_queue_report_empty",
    )
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.validation_digest)

    payload = module.research_team_domain_review_disagreement_queue_report_payload(result)
    assert payload["queue_count"] == "0"
    assert payload["rows"] == []
    assert_public_numeric_payload(payload)


def test_payload_is_json_ready_deterministic_and_redacts_private_surfaces() -> None:
    module = api()
    private_value = (
        "private-team-omega|private-source-alpha|"
        "candidate-alpha|market-123|event-slug|Will this happen?|"
        "https://example.test/feed?token=secret|dsn|table|wallet|order|trade"
    )
    result = report(
        queue_item(
            private_value,
            domain_key="domain-with-source-url-and-question-private",
        ),
    )

    payload = module.research_team_domain_review_disagreement_queue_report_payload(result)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)

    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["config_version"] == (
        "research-team-domain-review-disagreement-queue-report-v1"
    )
    assert payload["rows"][0]["queue_fingerprint"] == result.rows[0].queue_fingerprint
    assert payload["validation_digest"] == result.validation_digest
    assert private_value not in encoded
    assert "candidate-alpha" not in encoded
    assert "private-team-omega" not in encoded
    assert "private-source-alpha" not in encoded
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
    assert_public_numeric_payload(payload)
    assert payload["rows"][0]["validation_digest"] == payload_digest(payload["rows"][0])
    assert payload["validation_digest"] == payload_digest(payload)
    assert module.research_team_domain_review_disagreement_queue_report_payload(payload) == payload

    with pytest.raises(ValueError, match="readonly"):
        module.research_team_domain_review_disagreement_queue_report_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="unsafe"):
        module.research_team_domain_review_disagreement_queue_report_payload(
            {**payload, "candidate_id": "raw-candidate"},
        )
    with pytest.raises(ValueError, match="numeric"):
        module.research_team_domain_review_disagreement_queue_report_payload(
            {**payload, "queue_count": 1},
        )
    with pytest.raises(ValueError, match="numeric"):
        module.research_team_domain_review_disagreement_queue_report_payload(
            {**payload, "pass_count": 1.0},
        )


def test_invalid_inputs_config_flags_and_datetimes_are_rejected() -> None:
    module = api()

    assert module.DOMAIN_REVIEW_DISAGREEMENT_QUEUE_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    with pytest.raises(ValueError, match="reviewer_count"):
        queue_item(reviewer_count=d("0"))
    with pytest.raises(ValueError, match="reviewer_count"):
        queue_item(reviewer_count=d("2.500000"))
    with pytest.raises(ValueError, match="disagreeing_reviewer_count"):
        queue_item(disagreeing_reviewer_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="probability_spread"):
        queue_item(probability_spread=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="disagreeing_reviewer_count"):
        queue_item(reviewer_count=d("2"), disagreeing_reviewer_count=d("3"))
    with pytest.raises(ValueError, match="evidence_conflict_ratio"):
        queue_item(evidence_conflict_ratio=d("1.100000"))
    with pytest.raises(ValueError, match="queued_at"):
        queue_item(queued_at=datetime(2026, 7, 8, 11, 0))
    with pytest.raises(ValueError, match="queued_at"):
        queue_item(queued_at=_DatetimeSubclass(2026, 7, 8, 11, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="queued_at"):
        queue_item(
            queued_at=datetime(2026, 7, 8, 11, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(queue_item(queued_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="generated_at"):
        report(queue_item(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="paper_only"):
        queue_item(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report(queue_item()), readonly=False)
    with pytest.raises(ValueError, match="watch threshold must not exceed block threshold"):
        config(
            probability_spread_watch_threshold=d("0.300000"),
            probability_spread_block_threshold=d("0.250000"),
        )

    shifted = report(
        queue_item(
            "shifted-time",
            queued_at=datetime(2026, 7, 8, 7, 0, tzinfo=timezone(timedelta(hours=-4))),
        ),
        generated_at=datetime(2026, 7, 8, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )
    assert shifted.generated_at == GENERATED_AT
    assert shifted.rows[0].queued_at == datetime(2026, 7, 8, 11, 0, tzinfo=UTC)
    assert shifted.rows[0].queue_age_hours == d("1.000000")


def test_datetime_normalization_rejects_values_outside_utc_range() -> None:
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

    with pytest.raises(ValueError, match="queued_at.*UTC"):
        queue_item(queued_at=before_utc_range)
    with pytest.raises(ValueError, match="generated_at.*UTC"):
        report(generated_at=after_utc_range)


@pytest.mark.parametrize(
    ("watch_field", "block_field", "watch_value", "block_value"),
    (
        (
            "reviewer_disagreement_watch_threshold",
            "reviewer_disagreement_block_threshold",
            d("0.25000049"),
            d("0.25000040"),
        ),
        (
            "probability_spread_watch_threshold",
            "probability_spread_block_threshold",
            d("0.10000049"),
            d("0.10000040"),
        ),
        (
            "evidence_conflict_watch_threshold",
            "evidence_conflict_block_threshold",
            d("0.25000049"),
            d("0.25000040"),
        ),
        (
            "unresolved_blocker_watch_threshold",
            "unresolved_blocker_block_threshold",
            d("2"),
            d("1"),
        ),
        (
            "queue_age_watch_hours",
            "queue_age_block_hours",
            d("24.00000049"),
            d("24.00000040"),
        ),
        (
            "prior_resolution_miss_watch_threshold",
            "prior_resolution_miss_block_threshold",
            d("2"),
            d("1"),
        ),
    ),
)
def test_config_rejects_raw_watch_block_inversion_before_quantization(
    watch_field: str,
    block_field: str,
    watch_value: Decimal,
    block_value: Decimal,
) -> None:
    with pytest.raises(
        ValueError,
        match="watch threshold must not exceed block threshold",
    ):
        config(
            **{
                watch_field: watch_value,
                block_field: block_value,
            },
        )


def test_public_row_requires_generated_at_for_root_age_validation() -> None:
    module = api()
    row = report(queue_item()).rows[0]
    constructor_values = {
        field.name: getattr(row, field.name)
        for field in fields(row)
    }

    with pytest.raises(TypeError, match="generated_at"):
        module.ResearchTeamDomainReviewDisagreementQueueRow(**constructor_values)


def test_validation_digest_and_report_validation_recompute_fields() -> None:
    result = report(queue_item())
    row = result.rows[0]

    with pytest.raises(FrozenInstanceError):
        row.status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="disagreement_queue_score must match"):
        replace(
            row,
            disagreement_queue_score=row.disagreement_queue_score + d("0.000001"),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="status must match"):
        replace(row, status="block", generated_at=GENERATED_AT)
    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(row, validation_digest="0" * 64, generated_at=GENERATED_AT)
    with pytest.raises(ValueError, match="pass_count must match"):
        replace(result, pass_count=result.pass_count + d("1"))
    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(
            result,
            queue_count=d("2"),
            pass_count=d("2"),
            max_disagreement_queue_score=d("0.080556"),
            rows=(
                domain_queue_row("queue-alpha"),
                domain_queue_row("queue-zeta"),
            ),
        )
    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(result, validation_digest="0" * 64)


def test_object_setattr_report_tampering_revalidates_nested_rows() -> None:
    module = api()
    result = report(
        queue_item("pass-queue-secret"),
        queue_item(
            "watch-queue-secret",
            disagreeing_reviewer_count=d("1"),
            probability_spread=d("0.150000"),
            evidence_conflict_ratio=d("0.300000"),
            unresolved_blocker_count=d("1"),
            queued_at=GENERATED_AT - timedelta(hours=36),
            prior_resolution_miss_count=d("1"),
        ),
    )

    object.__setattr__(result, "rows", list(result.rows))
    object.__setattr__(
        result,
        "validation_digest",
        module._validation_digest(module._report_digest_values(result)),
    )
    with pytest.raises(ValueError, match="rows.*tuple"):
        module.research_team_domain_review_disagreement_queue_report_payload(result)

    result = report(
        queue_item("pass-queue-secret"),
        queue_item(
            "watch-queue-secret",
            disagreeing_reviewer_count=d("1"),
            probability_spread=d("0.150000"),
            evidence_conflict_ratio=d("0.300000"),
            unresolved_blocker_count=d("1"),
            queued_at=GENERATED_AT - timedelta(hours=36),
            prior_resolution_miss_count=d("1"),
        ),
    )
    object.__setattr__(result, "rows", tuple(reversed(result.rows)))
    object.__setattr__(
        result,
        "validation_digest",
        module._validation_digest(module._report_digest_values(result)),
    )
    with pytest.raises(ValueError, match="sorted deterministically"):
        module.research_team_domain_review_disagreement_queue_report_payload(result)


def test_build_revalidates_frozen_config_after_object_setattr_tampering() -> None:
    cfg = config()
    object.__setattr__(
        cfg,
        "probability_spread_watch_threshold",
        d("0.900000"),
    )

    with pytest.raises(
        ValueError,
        match="watch threshold must not exceed block threshold",
    ):
        report(queue_item(), cfg=cfg)


def test_resigned_frozen_report_rejects_unsupported_config_version() -> None:
    module = api()
    result = report(queue_item())
    object.__setattr__(result, "config_version", "forged-safe-version")
    resign_report_object(result)

    with pytest.raises(ValueError, match="config_version"):
        module.research_team_domain_review_disagreement_queue_report_payload(result)


def test_resigned_frozen_row_rejects_non_digest_fingerprint() -> None:
    module = api()
    result = report(queue_item())
    object.__setattr__(result.rows[0], "domain_fingerprint", "not-a-digest")
    resign_report_object(result)

    with pytest.raises(ValueError, match="domain_fingerprint"):
        module.research_team_domain_review_disagreement_queue_report_payload(result)


def test_resigned_frozen_row_rejects_noncanonical_positive_zero() -> None:
    module = api()
    result = report(queue_item())
    object.__setattr__(result.rows[0], "reviewer_disagreement_ratio", d("0"))
    resign_report_object(result)

    with pytest.raises(
        ValueError,
        match="reviewer_disagreement_ratio.*canonical",
    ):
        module.research_team_domain_review_disagreement_queue_report_payload(result)


@pytest.mark.parametrize(
    ("field_name", "value", "match"),
    (
        ("status", "forged", "status"),
        ("disagreement_queue_score", 1, "disagreement_queue_score.*Decimal"),
    ),
)
def test_direct_report_revalidates_nested_sort_fields_before_sorting(
    field_name: str,
    value: object,
    match: str,
) -> None:
    result = report(queue_item())
    object.__setattr__(result.rows[0], field_name, value)

    with pytest.raises(ValueError, match=match):
        replace(result)


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("queue_key", "private\x00queue"),
        ("domain_key", "private\nqueue"),
        ("queue_key", "x" * 2049),
        ("domain_key", "\ud800"),
    ),
)
def test_private_keys_reject_controls_oversize_and_invalid_unicode(
    field_name: str,
    value: str,
) -> None:
    with pytest.raises(ValueError, match=rf"{field_name}.*canonical"):
        queue_item(**{field_name: value})


@pytest.mark.parametrize(
    "class_name",
    (
        "ResearchTeamDomainReviewDisagreementQueueConfig",
        "ResearchTeamDomainReviewDisagreementQueueInput",
        "ResearchTeamDomainReviewDisagreementQueueRow",
        "ResearchTeamDomainReviewDisagreementQueueReport",
    ),
)
def test_public_dataclasses_are_frozen_and_non_subclassable(class_name: str) -> None:
    public_type = getattr(api(), class_name)

    assert is_dataclass(public_type)
    assert public_type.__dataclass_params__.frozen is True
    with pytest.raises(TypeError, match="subclass"):
        type(f"Derived{class_name}", (public_type,), {})


def test_public_export_surface_is_exact() -> None:
    assert api().__all__ == (
        "DEFAULT_RESEARCH_TEAM_DOMAIN_REVIEW_DISAGREEMENT_QUEUE_REPORT_CONFIG_VERSION",
        "DOMAIN_REVIEW_DISAGREEMENT_QUEUE_STATUSES",
        "ResearchTeamDomainReviewDisagreementQueueConfig",
        "ResearchTeamDomainReviewDisagreementQueueInput",
        "ResearchTeamDomainReviewDisagreementQueueReport",
        "ResearchTeamDomainReviewDisagreementQueueRow",
        "build_research_team_domain_review_disagreement_queue_report",
        "research_team_domain_review_disagreement_queue_report_payload",
    )


def test_report_math_is_independent_of_ambient_decimal_context() -> None:
    item = queue_item(
        reviewer_count=d("7"),
        disagreeing_reviewer_count=d("2"),
        probability_spread=d("0.123456"),
        evidence_conflict_ratio=d("0.345678"),
        unresolved_blocker_count=d("1"),
        queued_at=GENERATED_AT - timedelta(hours=35),
        prior_resolution_miss_count=d("1"),
    )
    expected = report(item)

    with localcontext(Context(prec=2)):
        actual = report(item)

    assert actual == expected
    assert actual.validation_digest == expected.validation_digest


@pytest.mark.parametrize(
    "field_name",
    (
        "reviewer_count",
        "disagreeing_reviewer_count",
        "probability_spread",
        "evidence_conflict_ratio",
        "unresolved_blocker_count",
        "prior_resolution_miss_count",
    ),
)
def test_signed_zero_is_rejected_before_normalization(field_name: str) -> None:
    with pytest.raises(ValueError, match="signed zero"):
        queue_item(**{field_name: d("-0")})


@pytest.mark.parametrize("value", (d("NaN"), d("Infinity"), d("-Infinity")))
def test_nonfinite_decimals_are_rejected(value: Decimal) -> None:
    with pytest.raises(ValueError, match="finite"):
        queue_item(probability_spread=value)


def test_raw_decimal_bounds_survive_quantization_and_context_limits() -> None:
    with pytest.raises(ValueError, match="positive after quantization"):
        config(queue_age_watch_hours=d("0.0000001"))
    with pytest.raises(ValueError, match="decimal context"):
        queue_item(reviewer_count=d("1E+100"))


def test_manual_review_priority_precedes_stable_hash_tie_breaks() -> None:
    reviewer_priority = queue_item(
        "reviewer-priority",
        reviewer_count=d("2"),
        disagreeing_reviewer_count=d("1"),
        probability_spread=d("0"),
        evidence_conflict_ratio=d("0"),
        queued_at=GENERATED_AT,
    )
    age_priority = queue_item(
        "age-priority",
        reviewer_count=d("2"),
        disagreeing_reviewer_count=d("0"),
        probability_spread=d("0"),
        evidence_conflict_ratio=d("0"),
        queued_at=GENERATED_AT - timedelta(hours=72),
    )

    first = report(age_priority, reviewer_priority)
    second = report(reviewer_priority, age_priority)

    assert first == second
    assert tuple(row.queue_fingerprint for row in first.rows) == (
        hashlib.sha256(b"reviewer-priority").hexdigest(),
        hashlib.sha256(b"age-priority").hexdigest(),
    )


def test_complete_sort_tie_break_reverses_input_by_final_queue_fingerprint() -> None:
    first_key = "complete-tie-alpha"
    second_key = "complete-tie-omega"
    first_item = queue_item(first_key, domain_key="complete-tie-domain")
    second_item = queue_item(second_key, domain_key="complete-tie-domain")

    forward = report(first_item, second_item)
    reversed_input = report(second_item, first_item)
    expected_fingerprints = tuple(
        sorted(
            (
                hashlib.sha256(first_key.encode("utf-8")).hexdigest(),
                hashlib.sha256(second_key.encode("utf-8")).hexdigest(),
            ),
        ),
    )

    assert forward == reversed_input
    assert tuple(row.queue_fingerprint for row in forward.rows) == expected_fingerprints


def test_payload_requires_exact_canonical_report_and_row_schema() -> None:
    module = api()
    payload = module.research_team_domain_review_disagreement_queue_report_payload(
        report(queue_item()),
    )
    expected_report_fields = (
        "generated_at",
        "config_version",
        "queue_count",
        "pass_count",
        "watch_count",
        "block_count",
        "max_disagreement_queue_score",
        "report_status",
        "reason_codes",
        "rows",
        "validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )
    expected_row_fields = (
        "queue_fingerprint",
        "domain_fingerprint",
        "reviewer_count",
        "disagreeing_reviewer_count",
        "reviewer_disagreement_ratio",
        "probability_spread",
        "evidence_conflict_ratio",
        "unresolved_blocker_count",
        "queued_at",
        "queue_age_hours",
        "prior_resolution_miss_count",
        "reviewer_disagreement_score",
        "probability_spread_score",
        "evidence_conflict_score",
        "unresolved_blocker_score",
        "queue_age_score",
        "prior_resolution_miss_score",
        "disagreement_queue_score",
        "status",
        "reason_codes",
        "validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )

    assert module._REPORT_PAYLOAD_SCHEMA == expected_report_fields
    assert module._ROW_PAYLOAD_SCHEMA == expected_row_fields
    assert tuple(payload) == expected_report_fields
    assert tuple(payload["rows"][0]) == expected_row_fields

    extra_report_field = dict(payload)
    extra_report_field["team_key"] = "redacted-but-not-schema"
    with pytest.raises(ValueError, match="schema"):
        module.research_team_domain_review_disagreement_queue_report_payload(
            recompute_validation_digests(extra_report_field),
        )

    for missing_field in expected_report_fields:
        missing_report_field = dict(payload)
        missing_report_field.pop(missing_field)
        with pytest.raises(ValueError, match="schema"):
            module.research_team_domain_review_disagreement_queue_report_payload(
                missing_report_field,
            )

    extra_row_field = dict(payload)
    row = dict(payload["rows"][0])
    row["team_key"] = "redacted-but-not-schema"
    extra_row_field["rows"] = [row]
    with pytest.raises(ValueError, match="schema"):
        module.research_team_domain_review_disagreement_queue_report_payload(
            recompute_validation_digests(extra_row_field),
        )

    for missing_field in expected_row_fields:
        missing_row_field = dict(payload)
        row = dict(payload["rows"][0])
        row.pop(missing_field)
        missing_row_field["rows"] = [row]
        with pytest.raises(ValueError, match="schema"):
            module.research_team_domain_review_disagreement_queue_report_payload(
                missing_row_field,
            )

    noncanonical_decimal = dict(payload)
    noncanonical_decimal["queue_count"] = "1.0"
    with pytest.raises(ValueError, match="canonical Decimal"):
        module.research_team_domain_review_disagreement_queue_report_payload(
            recompute_validation_digests(noncanonical_decimal),
        )

    tuple_rows = dict(payload)
    tuple_rows["rows"] = tuple(payload["rows"])
    with pytest.raises(ValueError, match="JSON array"):
        module.research_team_domain_review_disagreement_queue_report_payload(tuple_rows)


def test_payload_rejects_noncanonical_report_field_order() -> None:
    module = api()
    payload = module.research_team_domain_review_disagreement_queue_report_payload(
        report(queue_item()),
    )
    reordered = dict(reversed(tuple(payload.items())))

    with pytest.raises(ValueError, match="schema"):
        module.research_team_domain_review_disagreement_queue_report_payload(
            recompute_validation_digests(reordered),
        )


def test_payload_rejects_noncanonical_row_field_order() -> None:
    module = api()
    payload = module.research_team_domain_review_disagreement_queue_report_payload(
        report(queue_item()),
    )
    reordered = dict(payload)
    reordered["rows"] = [
        dict(reversed(tuple(payload["rows"][0].items()))),
    ]

    with pytest.raises(ValueError, match="schema"):
        module.research_team_domain_review_disagreement_queue_report_payload(
            recompute_validation_digests(reordered),
        )


def test_recomputed_digest_payload_rejects_duplicate_queue_fingerprints() -> None:
    module = api()
    payload = module.research_team_domain_review_disagreement_queue_report_payload(
        report(queue_item()),
    )
    duplicated = dict(payload)
    duplicated["queue_count"] = "2"
    duplicated["pass_count"] = "2"
    duplicated["rows"] = [
        dict(payload["rows"][0]),
        dict(payload["rows"][0]),
    ]

    with pytest.raises(ValueError, match="queue_fingerprint.*unique"):
        module.research_team_domain_review_disagreement_queue_report_payload(
            recompute_validation_digests(duplicated),
        )


def test_recomputed_digest_payload_rejects_nondeterministic_row_order() -> None:
    module = api()
    payload = module.research_team_domain_review_disagreement_queue_report_payload(
        report(
            queue_item("pass-queue-secret"),
            queue_item(
                "block-queue-secret",
                disagreeing_reviewer_count=d("2"),
                probability_spread=d("0.300000"),
                evidence_conflict_ratio=d("0.600000"),
                unresolved_blocker_count=d("2"),
                queued_at=GENERATED_AT - timedelta(hours=96),
                prior_resolution_miss_count=d("2"),
            ),
        ),
    )
    reordered = dict(payload)
    reordered["rows"] = list(reversed(payload["rows"]))

    with pytest.raises(ValueError, match="sorted deterministically"):
        module.research_team_domain_review_disagreement_queue_report_payload(
            recompute_validation_digests(reordered),
        )


def test_direct_report_rejects_duplicate_queue_fingerprints() -> None:
    module = api()
    cfg = config()
    result = report(queue_item(), cfg=cfg)
    row = result.rows[0]
    payload = module.research_team_domain_review_disagreement_queue_report_payload(
        result,
    )
    duplicated = dict(payload)
    duplicated["queue_count"] = "2"
    duplicated["pass_count"] = "2"
    duplicated["rows"] = [
        dict(payload["rows"][0]),
        dict(payload["rows"][0]),
    ]
    recomputed = recompute_validation_digests(duplicated)

    with pytest.raises(ValueError, match="queue_fingerprint.*unique"):
        module.ResearchTeamDomainReviewDisagreementQueueReport(
            generated_at=result.generated_at,
            config_version=result.config_version,
            queue_count=d("2"),
            pass_count=d("2"),
            watch_count=result.watch_count,
            block_count=result.block_count,
            max_disagreement_queue_score=result.max_disagreement_queue_score,
            report_status=result.report_status,
            reason_codes=result.reason_codes,
            rows=(row, row),
            validation_digest=recomputed["validation_digest"],
            validation_config=cfg,
        )


@pytest.mark.parametrize(
    "field_name",
    (
        "reviewer_disagreement_score",
        "probability_spread_score",
        "evidence_conflict_score",
        "unresolved_blocker_score",
        "queue_age_score",
        "prior_resolution_miss_score",
    ),
)
def test_recomputed_digests_do_not_bypass_component_score_validation(
    field_name: str,
) -> None:
    module = api()
    payload = module.research_team_domain_review_disagreement_queue_report_payload(
        report(queue_item()),
    )
    tampered = dict(payload)
    row = dict(payload["rows"][0])
    row[field_name] = "0.900000"
    component_fields = (
        "reviewer_disagreement_score",
        "probability_spread_score",
        "evidence_conflict_score",
        "unresolved_blocker_score",
        "queue_age_score",
        "prior_resolution_miss_score",
    )
    row["disagreement_queue_score"] = format(
        (
            sum((Decimal(row[name]) for name in component_fields), d("0"))
            / d("6")
        ).quantize(d("0.000001")),
        "f",
    )
    tampered["rows"] = [row]
    tampered["max_disagreement_queue_score"] = row["disagreement_queue_score"]

    with pytest.raises(ValueError, match=field_name):
        module.research_team_domain_review_disagreement_queue_report_payload(
            recompute_validation_digests(tampered),
        )


def test_recomputed_digests_do_not_bypass_other_derived_field_validation() -> None:
    module = api()
    payload = module.research_team_domain_review_disagreement_queue_report_payload(
        report(queue_item()),
    )

    ratio_tamper = dict(payload)
    ratio_row = dict(payload["rows"][0])
    ratio_row["reviewer_disagreement_ratio"] = "0.250000"
    ratio_tamper["rows"] = [ratio_row]
    with pytest.raises(ValueError, match="reviewer_disagreement_ratio"):
        module.research_team_domain_review_disagreement_queue_report_payload(
            recompute_validation_digests(ratio_tamper),
        )

    aggregate_tamper = dict(payload)
    aggregate_row = dict(payload["rows"][0])
    aggregate_row["disagreement_queue_score"] = "0.900000"
    aggregate_tamper["rows"] = [aggregate_row]
    aggregate_tamper["max_disagreement_queue_score"] = "0.900000"
    with pytest.raises(ValueError, match="disagreement_queue_score"):
        module.research_team_domain_review_disagreement_queue_report_payload(
            recompute_validation_digests(aggregate_tamper),
        )

    for field_name, tampered_value in (
        ("queue_count", "2"),
        ("pass_count", "0"),
        ("watch_count", "1"),
        ("block_count", "1"),
        ("max_disagreement_queue_score", "0.900000"),
        ("report_status", "watch"),
        ("reason_codes", ["probability_spread_watch"]),
    ):
        report_tamper = dict(payload)
        report_tamper[field_name] = tampered_value
        with pytest.raises(ValueError, match=field_name):
            module.research_team_domain_review_disagreement_queue_report_payload(
                recompute_validation_digests(report_tamper),
            )


def test_recomputed_digest_payload_recomputes_all_row_derivations() -> None:
    module = api()
    payload = module.research_team_domain_review_disagreement_queue_report_payload(
        report(queue_item()),
    )

    score_tamper = dict(payload)
    score_row = dict(payload["rows"][0])
    score_row["probability_spread_score"] = "0.900000"
    components = (
        "reviewer_disagreement_score",
        "probability_spread_score",
        "evidence_conflict_score",
        "unresolved_blocker_score",
        "queue_age_score",
        "prior_resolution_miss_score",
    )
    score_row["disagreement_queue_score"] = format(
        (sum((Decimal(score_row[name]) for name in components), d("0")) / d("6")).quantize(
            d("0.000001"),
        ),
        "f",
    )
    score_tamper["rows"] = [score_row]
    score_tamper["max_disagreement_queue_score"] = score_row[
        "disagreement_queue_score"
    ]
    with pytest.raises(ValueError, match="probability_spread_score"):
        module.research_team_domain_review_disagreement_queue_report_payload(
            recompute_validation_digests(score_tamper),
        )

    reason_tamper = dict(payload)
    reason_row = dict(payload["rows"][0])
    reason_row["status"] = "watch"
    reason_row["reason_codes"] = ["probability_spread_watch"]
    reason_tamper["rows"] = [reason_row]
    reason_tamper["pass_count"] = "0"
    reason_tamper["watch_count"] = "1"
    reason_tamper["report_status"] = "watch"
    reason_tamper["reason_codes"] = ["probability_spread_watch"]
    with pytest.raises(ValueError, match="reason_codes"):
        module.research_team_domain_review_disagreement_queue_report_payload(
            recompute_validation_digests(reason_tamper),
        )

    age_tamper = dict(payload)
    age_row = dict(payload["rows"][0])
    age_row["queue_age_hours"] = "7.000000"
    age_row["queue_age_score"] = "0.097222"
    age_row["disagreement_queue_score"] = "0.082870"
    age_tamper["rows"] = [age_row]
    age_tamper["max_disagreement_queue_score"] = "0.082870"
    with pytest.raises(ValueError, match="queue_age_hours"):
        module.research_team_domain_review_disagreement_queue_report_payload(
            recompute_validation_digests(age_tamper),
        )


def domain_queue_row(queue_key: str) -> Any:
    return report(queue_item(queue_key)).rows[0]


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
        "position_size",
        "buy",
        "sell",
        "recommend",
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
                assert func.id not in {"__import__", "float", "open", "request", "write"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in {
                    "connect",
                    "execute",
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

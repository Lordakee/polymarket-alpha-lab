from __future__ import annotations

from dataclasses import FrozenInstanceError, asdict, dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import importlib

import pytest

from polymarket_alpha_lab.research_source_refresh_failure_digest import (
    DEFAULT_RESEARCH_SOURCE_REFRESH_FAILURE_DIGEST_CONFIG_VERSION,
    ResearchSourceRefreshFailureDigestConfig,
    ResearchSourceRefreshFailureDigestInputRow,
    ResearchSourceRefreshFailureDigestReport,
    build_research_source_refresh_failure_digest,
    research_source_refresh_failure_digest_json,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
_DEFAULT_LAST_SUCCESS = object()


@dataclass(frozen=True)
class _ForeignPublicDataclass:
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object) -> ResearchSourceRefreshFailureDigestConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_SOURCE_REFRESH_FAILURE_DIGEST_CONFIG_VERSION,
        "watch_failure_count": d("2"),
        "block_failure_count": d("4"),
        "watch_failure_age_minutes": d("60.000000"),
        "block_failure_age_minutes": d("360.000000"),
        "stale_success_watch_minutes": d("720.000000"),
        "stale_success_block_minutes": d("1440.000000"),
    }
    values.update(overrides)
    return ResearchSourceRefreshFailureDigestConfig(**values)


def _row(
    source_group: str,
    *,
    source_family: str = "weather",
    failure_kind: str = "timeout",
    first_failed_at: datetime | None = None,
    last_failed_at: datetime | None = None,
    last_success_at: datetime | None | object = _DEFAULT_LAST_SUCCESS,
    failure_count: Decimal = d("1"),
    consecutive_failure_count: Decimal = d("1"),
) -> ResearchSourceRefreshFailureDigestInputRow:
    last_failed = last_failed_at or GENERATED_AT - timedelta(minutes=20)
    if last_success_at is _DEFAULT_LAST_SUCCESS:
        normalized_last_success_at = GENERATED_AT - timedelta(minutes=30)
    else:
        normalized_last_success_at = last_success_at
    return ResearchSourceRefreshFailureDigestInputRow(
        source_group=source_group,
        source_family=source_family,
        failure_kind=failure_kind,
        first_failed_at=first_failed_at or last_failed - timedelta(minutes=5),
        last_failed_at=last_failed,
        last_success_at=normalized_last_success_at,  # type: ignore[arg-type]
        failure_count=failure_count,
        consecutive_failure_count=consecutive_failure_count,
    )


def test_refresh_failure_digest_reduces_pass_watch_block_rows() -> None:
    report = build_research_source_refresh_failure_digest(
        (
            _row("beta", consecutive_failure_count=d("2")),
            _row(
                "gamma",
                failure_kind="schema_mismatch",
                last_failed_at=GENERATED_AT - timedelta(minutes=400),
                last_success_at=None,
                failure_count=d("5"),
                consecutive_failure_count=d("4"),
            ),
            _row("alpha", consecutive_failure_count=d("1")),
        ),
        config=_config(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )

    assert isinstance(report, ResearchSourceRefreshFailureDigestReport)
    assert report.generated_at == GENERATED_AT
    assert report.digest_status == "block"
    assert report.source_group_count == d("3.000000")
    assert report.pass_source_group_count == d("1.000000")
    assert report.watch_source_group_count == d("1.000000")
    assert report.block_source_group_count == d("1.000000")
    assert report.hard_failure_count == d("1.000000")
    assert report.max_retry_priority_score == d("1.000000")
    assert tuple(row.source_group for row in report.rows) == ("alpha", "beta", "gamma")

    rows = {row.source_group: row for row in report.rows}
    assert rows["alpha"].refresh_status == "pass"
    assert rows["alpha"].reason_codes == (
        "refresh_failure_digest_pass",
    )
    assert rows["beta"].refresh_status == "watch"
    assert rows["beta"].reason_codes == (
        "refresh_failure_digest_watch_failure_volume",
    )
    assert rows["gamma"].refresh_status == "block"
    assert rows["gamma"].reason_codes == (
        "refresh_failure_digest_block_failure_age",
        "refresh_failure_digest_block_failure_volume",
        "refresh_failure_digest_block_hard_failure_kind",
        "refresh_failure_digest_block_never_succeeded",
    )
    assert rows["gamma"].last_success_age_minutes is None
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_refresh_failure_digest_rejects_non_public_types() -> None:
    with pytest.raises(ValueError, match="watch_failure_count"):
        _config(watch_failure_count=2)
    with pytest.raises(ValueError, match="block_failure_count"):
        _config(block_failure_count=_DecimalSubclass("4"))
    with pytest.raises(ValueError, match="failure_count"):
        _row("float-count", failure_count=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="consecutive_failure_count"):
        _row("fractional-count", consecutive_failure_count=d("1.5"))
    with pytest.raises(ValueError, match="generated_at"):
        build_research_source_refresh_failure_digest(
            (),
            config=_config(),
            generated_at="2026-07-02",  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="input rows"):
        build_research_source_refresh_failure_digest(
            (object(),),  # type: ignore[arg-type]
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        build_research_source_refresh_failure_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="ResearchSourceRefreshFailureDigestReport"):
        research_source_refresh_failure_digest_json(asdict(_empty_report()))  # type: ignore[arg-type]


def test_refresh_failure_digest_rejects_public_leaks() -> None:
    report = build_research_source_refresh_failure_digest(
        (_row("alpha"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    public = repr(asdict(report)).lower()
    for token in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "https://",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    ):
        assert token not in public

    with pytest.raises(ValueError, match="source_group"):
        _row("market_slug:will-it-rain")
    with pytest.raises(ValueError, match="source_group"):
        _row("https://source.example/path?token=secret")

    object.__setattr__(report.rows[0], "source_group", "candidate_id:raw-123")
    with pytest.raises(ValueError, match="disallowed"):
        research_source_refresh_failure_digest_json(report)


def test_refresh_failure_digest_enforces_hard_flags_and_frozen_rows() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        replace(_config(), paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(_row("alpha"), readonly=False)

    report = build_research_source_refresh_failure_digest(
        (_row("alpha"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    with pytest.raises(FrozenInstanceError):
        report.rows[0].refresh_status = "block"

    object.__setattr__(report, "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        research_source_refresh_failure_digest_json(report)


def test_refresh_failure_digest_serializes_deterministically_without_public_numerics() -> None:
    rows = (
        _row(
            "zeta",
            last_failed_at=GENERATED_AT - timedelta(minutes=90, microseconds=500000),
            last_success_at=GENERATED_AT - timedelta(minutes=800),
            consecutive_failure_count=d("2"),
        ),
        _row(
            "alpha",
            last_failed_at=GENERATED_AT - timedelta(minutes=10),
            last_success_at=GENERATED_AT - timedelta(minutes=15),
            consecutive_failure_count=d("1"),
        ),
    )
    first = build_research_source_refresh_failure_digest(
        rows,
        config=_config(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=3))),
    )
    second = build_research_source_refresh_failure_digest(
        tuple(reversed(rows)),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    first_json = research_source_refresh_failure_digest_json(first)
    second_json = research_source_refresh_failure_digest_json(second)

    assert first_json == second_json
    assert first_json["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert first_json["source_group_count"] == "2.000000"
    assert first_json["watch_source_group_count"] == "1.000000"
    assert first_json["digest_status"] == "watch"
    assert first_json["rows"][0]["source_group"] == "alpha"  # type: ignore[index]
    assert first_json["rows"][1]["failure_age_minutes"] == "90.008333"  # type: ignore[index]

    def walk(value: object) -> tuple[object, ...]:
        if isinstance(value, dict):
            return tuple(item for nested in value.values() for item in walk(nested))
        if isinstance(value, list):
            return tuple(item for nested in value for item in walk(nested))
        return (value,)

    assert not any(isinstance(value, Decimal) for value in walk(first_json))
    assert not any(type(value) is int for value in walk(first_json))
    assert not any(type(value) is float for value in walk(first_json))


def test_refresh_failure_digest_report_and_digest_are_consistent() -> None:
    report = build_research_source_refresh_failure_digest(
        (_row("alpha"), _row("beta", consecutive_failure_count=d("2"))),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    digest = research_source_refresh_failure_digest_json(report)
    assert report.digest == digest
    assert digest["digest_status"] == report.digest_status
    assert digest["reason_codes"] == list(report.reason_codes)
    assert digest["reason_code_counts"] == [
        {
            "reason_code": count.reason_code,
            "count": str(count.count),
            "source_group_ratio": str(count.source_group_ratio),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        }
        for count in report.reason_code_counts
    ]


def test_refresh_failure_digest_json_revalidates_nested_public_dataclasses() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.research_source_refresh_failure_digest",
    )
    report = build_research_source_refresh_failure_digest(
        (_row("alpha"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    object.__setattr__(report.rows[0], "retry_priority_score", d("1.0000001"))
    with pytest.raises(ValueError, match="six decimal"):
        research_source_refresh_failure_digest_json(report)

    clean_report = build_research_source_refresh_failure_digest(
        (_row("alpha"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    object.__setattr__(clean_report, "rows", (_ForeignPublicDataclass(),))
    with pytest.raises(ValueError, match="supported public dataclass"):
        research_source_refresh_failure_digest_json(clean_report)

    with pytest.raises(ValueError, match="raw collection"):
        module._json_ready([d("1.000000")])


def _empty_report() -> ResearchSourceRefreshFailureDigestReport:
    return build_research_source_refresh_failure_digest(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

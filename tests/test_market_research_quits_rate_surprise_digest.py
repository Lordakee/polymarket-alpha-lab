from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_quits_rate_surprise_digest import (
    DEFAULT_MARKET_RESEARCH_QUITS_RATE_SURPRISE_DIGEST_CONFIG_VERSION,
    MarketResearchQuitsRateSurpriseDigestConfig,
    MarketResearchQuitsRateSurpriseDigestObservation,
    MarketResearchQuitsRateSurpriseDigestReasonCodeCount,
    MarketResearchQuitsRateSurpriseDigestReport,
    build_market_research_quits_rate_surprise_digest,
    market_research_quits_rate_surprise_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 15, 0, tzinfo=UTC)
SOURCE_TZ = timezone(timedelta(hours=-4))
SOURCE_OBSERVED_AT = datetime(2026, 7, 3, 10, 15, tzinfo=SOURCE_TZ)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None

    def tzname(self, dt: datetime | None) -> str:
        return "none-offset"


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchQuitsRateSurpriseDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_QUITS_RATE_SURPRISE_DIGEST_CONFIG_VERSION
        ),
        "material_surprise_threshold": d("0.100000"),
        "max_observation_age_seconds": d("7200.000000"),
        "min_source_count": d("2.000000"),
    }
    values.update(overrides)
    return MarketResearchQuitsRateSurpriseDigestConfig(**values)


def observation(
    release_id: str,
    *,
    actual: str,
    consensus: str,
    previous: str,
    market_slug: str | None = None,
    observed_at: datetime = SOURCE_OBSERVED_AT,
    source_count: Decimal = d("2.000000"),
    release_reference: str = "public-bls-jolts-release",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchQuitsRateSurpriseDigestObservation:
    return MarketResearchQuitsRateSurpriseDigestObservation(
        release_id=release_id,
        market_slug=market_slug or f"us-jolts-quits-rate-{release_id}",
        observed_at=observed_at,
        actual_quits_rate=Decimal(actual),
        consensus_quits_rate=Decimal(consensus),
        previous_quits_rate=Decimal(previous),
        source_count=source_count,
        release_reference=release_reference,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: MarketResearchQuitsRateSurpriseDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchQuitsRateSurpriseDigestReport:
    return build_market_research_quits_rate_surprise_digest(
        rows,
        generated_at=generated_at,
        config=cfg or config(),
    )


def test_quits_rate_surprise_digest_reduces_inputs_deterministically() -> None:
    summary = report(
        (
            observation(
                "2026-06",
                actual="2.400000",
                consensus="2.100000",
                previous="2.000000",
                observed_at=GENERATED_AT - timedelta(hours=3),
                release_reference="https://vendor.example/feed?token=secret-123",
            ),
            observation(
                "2026-05",
                actual="1.850000",
                consensus="2.000000",
                previous="1.950000",
                observed_at=GENERATED_AT - timedelta(hours=3),
                source_count=d("1.000000"),
                release_reference="private-labor-feed",
            ),
            observation(
                "2026-04",
                actual="2.030000",
                consensus="2.000000",
                previous="2.010000",
                observed_at=GENERATED_AT.astimezone(SOURCE_TZ),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(SOURCE_TZ),
    )

    assert isinstance(summary, MarketResearchQuitsRateSurpriseDigestReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_QUITS_RATE_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "watch"
    assert summary.recommended_next_step == "watch_report_only_quits_rate_surprise"
    assert tuple(row.release_id for row in summary.observations) == (
        "2026-04",
        "2026-05",
        "2026-06",
    )
    assert all(row.observed_at.tzinfo is UTC for row in summary.observations)
    assert summary.observation_count == d("3.000000")
    assert summary.material_surprise_count == d("2.000000")
    assert summary.positive_surprise_count == d("1.000000")
    assert summary.negative_surprise_count == d("1.000000")
    assert summary.stale_observation_count == d("2.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.largest_abs_surprise_ratio == d("0.142857")
    assert summary.average_surprise_ratio == d("0.077619")
    assert summary.average_source_count == d("1.666667")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert summary.reason_codes == (
        "market_research_quits_rate_surprise_digest_material_positive_surprise",
        "market_research_quits_rate_surprise_digest_material_negative_surprise",
        "market_research_quits_rate_surprise_digest_stale_observation",
        "market_research_quits_rate_surprise_digest_thin_sources",
        "market_research_quits_rate_surprise_digest_watch",
    )
    assert summary.reason_code_counts == (
        MarketResearchQuitsRateSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_quits_rate_surprise_digest_"
                "material_positive_surprise"
            ),
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        MarketResearchQuitsRateSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_quits_rate_surprise_digest_"
                "material_negative_surprise"
            ),
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        MarketResearchQuitsRateSurpriseDigestReasonCodeCount(
            reason_code="market_research_quits_rate_surprise_digest_stale_observation",
            count=d("2.000000"),
            observation_ratio=d("0.666667"),
        ),
        MarketResearchQuitsRateSurpriseDigestReasonCodeCount(
            reason_code="market_research_quits_rate_surprise_digest_thin_sources",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        MarketResearchQuitsRateSurpriseDigestReasonCodeCount(
            reason_code="market_research_quits_rate_surprise_digest_watch",
            count=d("2.000000"),
            observation_ratio=d("0.666667"),
        ),
    )

    neutral, negative, positive = summary.observations
    assert neutral.digest_status == "ready"
    assert neutral.surprise_ratio == d("0.015000")
    assert neutral.observation_age_seconds == ZERO
    assert neutral.redacted_release_reference == "public-bls-jolts-release"
    assert neutral.reason_codes == (
        "market_research_quits_rate_surprise_digest_no_material_surprise",
    )
    assert negative.digest_status == "watch"
    assert negative.surprise_ratio == d("-0.075000")
    assert negative.observation_age_seconds == d("10800.000000")
    assert negative.redacted_release_reference == "sha256:dcd9eea73513"
    assert negative.reason_codes == (
        "market_research_quits_rate_surprise_digest_material_negative_surprise",
        "market_research_quits_rate_surprise_digest_stale_observation",
        "market_research_quits_rate_surprise_digest_thin_sources",
    )
    assert positive.digest_status == "watch"
    assert positive.surprise_ratio == d("0.142857")
    assert positive.quits_rate_surprise == d("0.300000")
    assert positive.redacted_release_reference == "sha256:f1b9cf4094c0"
    assert positive.reason_codes == (
        "market_research_quits_rate_surprise_digest_material_positive_surprise",
        "market_research_quits_rate_surprise_digest_stale_observation",
    )

    serialized = repr(asdict(summary)).lower()
    for token in (
        "secret-123",
        "vendor.example",
        "https://",
        "private-labor-feed",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "token",
    ):
        assert token not in serialized


def test_quits_rate_surprise_digest_ready_when_surprises_are_immaterial() -> None:
    summary = report(
        (
            observation(
                "2026-06",
                actual="2.080000",
                consensus="2.000000",
                previous="1.990000",
                observed_at=GENERATED_AT,
            ),
        ),
    )

    assert summary.digest_status == "ready"
    assert summary.recommended_next_step == "allow_report_only_quits_rate_surprise"
    assert summary.reason_codes == (
        "market_research_quits_rate_surprise_digest_no_material_surprise",
    )
    assert summary.reason_code_counts == (
        MarketResearchQuitsRateSurpriseDigestReasonCodeCount(
            reason_code="market_research_quits_rate_surprise_digest_no_material_surprise",
            count=d("1.000000"),
            observation_ratio=d("1.000000"),
        ),
    )


def test_quits_rate_surprise_digest_blocks_on_missing_consensus() -> None:
    summary = report(
        (
            observation(
                "2026-06",
                actual="1.900000",
                consensus="0.000000",
                previous="2.100000",
            ),
        ),
    )

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == "block_report_only_quits_rate_surprise"
    assert summary.observation_count == d("1.000000")
    assert summary.material_surprise_count == ZERO
    assert summary.missing_consensus_count == d("1.000000")
    assert summary.largest_abs_surprise_ratio == ZERO
    assert summary.average_surprise_ratio == ZERO
    assert summary.reason_codes == (
        "market_research_quits_rate_surprise_digest_missing_consensus",
        "market_research_quits_rate_surprise_digest_no_material_surprise",
    )


def test_empty_quits_rate_surprise_digest_is_blocked_and_decimal_only() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == "block_report_only_quits_rate_surprise"
    assert summary.observation_count == ZERO
    assert summary.material_surprise_count == ZERO
    assert summary.positive_surprise_count == ZERO
    assert summary.negative_surprise_count == ZERO
    assert summary.stale_observation_count == ZERO
    assert summary.thin_source_count == ZERO
    assert summary.missing_consensus_count == ZERO
    assert summary.largest_abs_surprise_ratio == ZERO
    assert summary.average_surprise_ratio == ZERO
    assert summary.average_source_count == ZERO
    assert summary.observations == ()
    assert summary.reason_codes == (
        "market_research_quits_rate_surprise_digest_no_inputs",
    )
    assert summary.reason_code_counts == (
        MarketResearchQuitsRateSurpriseDigestReasonCodeCount(
            reason_code="market_research_quits_rate_surprise_digest_no_inputs",
            count=d("1.000000"),
            observation_ratio=ZERO,
        ),
    )

    public_values = asdict(summary)
    numeric_or_countish = (
        "count",
        "ratio",
        "rate",
        "threshold",
        "seconds",
    )
    for name, value in public_values.items():
        if name != "generated_at" and any(fragment in name for fragment in numeric_or_countish):
            if isinstance(value, (dict, list, tuple)):
                continue
            assert isinstance(value, Decimal), (name, value)


def test_quits_rate_surprise_dataclasses_are_frozen_and_validate_surface() -> None:
    obs = observation(
        "2026-06",
        actual="2.400000",
        consensus="2.100000",
        previous="2.000000",
    )
    summary = report((obs,))

    assert obs.observed_at == datetime(2026, 7, 3, 14, 15, tzinfo=UTC)
    with pytest.raises(FrozenInstanceError):
        obs.release_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.digest_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.reason_code_counts[0].count = d("2.000000")  # type: ignore[misc]

    with pytest.raises(TypeError, match="subclassing"):
        type(
            "BadObservation",
            (MarketResearchQuitsRateSurpriseDigestObservation,),
            {},
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(
            "bad-time",
            actual="2.4",
            consensus="2.1",
            previous="2.0",
            observed_at=datetime(2026, 7, 3, 15, 0),
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(
            "bad-none-offset",
            actual="2.4",
            consensus="2.1",
            previous="2.0",
            observed_at=datetime(2026, 7, 3, 15, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(TypeError, match="actual_quits_rate must be a Decimal"):
        MarketResearchQuitsRateSurpriseDigestObservation(
            release_id="bad-float",
            market_slug="bad-float",
            observed_at=GENERATED_AT,
            actual_quits_rate=2.4,  # type: ignore[arg-type]
            consensus_quits_rate=d("2.100000"),
            previous_quits_rate=d("2.000000"),
            source_count=d("2.000000"),
            release_reference="public-bls-jolts-release",
        )
    with pytest.raises(ValueError, match="release_id must be a plain str"):
        observation(
            _StringSubclass("bad-string"),
            actual="2.4",
            consensus="2.1",
            previous="2.0",
        )
    with pytest.raises(TypeError, match="source_count must be a Decimal"):
        observation(
            "bad-decimal-subclass",
            actual="2.4",
            consensus="2.1",
            previous="2.0",
            source_count=_DecimalSubclass("2.000000"),
        )
    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report(
            (obs,),
            generated_at=_DatetimeSubclass(2026, 7, 3, 15, 0, tzinfo=UTC),
        )
    valid_summary = report(
        (observation("valid-flags", actual="2.4", consensus="2.1", previous="2.0"),),
    )
    valid_row = valid_summary.observations[0]
    valid_reason_count = valid_summary.reason_code_counts[0]
    false_flag_cases = (
        (
            "config",
            lambda flag: config(**{flag: False}),
        ),
        (
            "observation",
            lambda flag: observation(
                "bad-flags",
                actual="2.4",
                consensus="2.1",
                previous="2.0",
                **{flag: False},
            ),
        ),
        (
            "row",
            lambda flag: replace(valid_row, **{flag: False}),
        ),
        (
            "reason code count",
            lambda flag: replace(valid_reason_count, **{flag: False}),
        ),
        (
            "report",
            lambda flag: replace(valid_summary, **{flag: False}),
        ),
    )
    for _label, factory in false_flag_cases:
        for flag in ("paper_only", "report_only", "readonly"):
            with pytest.raises(ValueError, match=flag):
                factory(flag)


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("release_id", "jolts-secret-token"),
        ("market_slug", "quits-wallet-order-route"),
    ),
)
def test_quits_rate_surprise_public_identifiers_reject_unsafe_text(
    field_name: str,
    bad_value: str,
) -> None:
    kwargs = {
        "actual": "2.4",
        "consensus": "2.1",
        "previous": "2.0",
    }
    if field_name == "release_id":
        with pytest.raises(ValueError, match=f"{field_name} has unsafe public text"):
            observation(bad_value, **kwargs)
        return

    with pytest.raises(ValueError, match=f"{field_name} has unsafe public text"):
        observation("safe-release", market_slug=bad_value, **kwargs)


def test_quits_rate_surprise_payload_decimal_strings_and_safe_contract() -> None:
    summary = report((observation("2026-06", actual="2.4", consensus="2.1", previous="2.0"),))
    payload = market_research_quits_rate_surprise_digest_payload(summary)

    assert payload["generated_at"] == "2026-07-03T15:00:00+00:00"
    assert payload["observation_count"] == "1.000000"
    assert payload["average_surprise_ratio"] == "0.142857"
    assert payload["observations"][0]["source_count"] == "2.000000"
    assert payload["observations"][0]["actual_quits_rate"] == "2.400000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "'release_reference':" not in repr(payload)

    for value in (
        config(),
        observation("surface", actual="2.4", consensus="2.1", previous="2.0"),
        summary.observations[0],
        summary.reason_code_counts[0],
        summary,
    ):
        assert is_dataclass(value)
        for item in fields(value):
            public_value = getattr(value, item.name)
            if item.name in ("paper_only", "report_only", "readonly"):
                assert public_value is True
            if isinstance(public_value, tuple):
                continue
            if item.name != "generated_at" and any(
                fragment in item.name
                for fragment in ("count", "ratio", "rate", "threshold", "seconds")
            ):
                assert type(public_value) is Decimal, (item.name, type(public_value))


def test_quits_rate_surprise_row_status_must_match_reason_codes() -> None:
    stale_blocked = report(
        (
            observation(
                "blocked-stale",
                actual="2.000000",
                consensus="0.000000",
                previous="2.100000",
                observed_at=GENERATED_AT - timedelta(hours=3),
            ),
        ),
    ).observations[0]

    assert stale_blocked.digest_status == "blocked"
    assert stale_blocked.reason_codes == (
        "market_research_quits_rate_surprise_digest_stale_observation",
        "market_research_quits_rate_surprise_digest_missing_consensus",
        "market_research_quits_rate_surprise_digest_no_material_surprise",
    )
    with pytest.raises(ValueError, match="digest_status must match reason_codes"):
        replace(stale_blocked, digest_status="watch")


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("material_surprise_count", "1.000000"),
        ("positive_surprise_count", "1.000000"),
        ("negative_surprise_count", "1.000000"),
        ("stale_observation_count", "1.000000"),
        ("thin_source_count", "1.000000"),
        ("missing_consensus_count", "1.000000"),
        ("largest_abs_surprise_ratio", "0.999999"),
        ("average_surprise_ratio", "0.999999"),
        ("average_source_count", "0.999999"),
    ),
)
def test_quits_rate_surprise_report_rejects_forged_aggregate_fields(
    field_name: str,
    bad_value: str,
) -> None:
    summary = report(
        (
            observation(
                "ready",
                actual="2.080000",
                consensus="2.000000",
                previous="1.990000",
                observed_at=GENERATED_AT,
            ),
        ),
    )

    with pytest.raises(ValueError, match=f"{field_name} must match observations"):
        replace(summary, **{field_name: d(bad_value)})


def test_quits_rate_surprise_report_rejects_rows_inconsistent_with_generated_at() -> None:
    summary = report(
        (
            observation(
                "timed",
                actual="2.400000",
                consensus="2.100000",
                previous="2.000000",
                observed_at=GENERATED_AT - timedelta(minutes=15),
            ),
        ),
    )
    row = summary.observations[0]

    with pytest.raises(
        ValueError,
        match="row observation_age_seconds must match generated_at",
    ):
        replace(
            summary,
            observations=(replace(row, observation_age_seconds=ZERO),),
        )

    with pytest.raises(ValueError, match="row observed_at cannot be after generated_at"):
        replace(
            summary,
            observations=(
                replace(
                    row,
                    observed_at=GENERATED_AT + timedelta(seconds=1),
                    observation_age_seconds=d("1.000000"),
                ),
            ),
        )


def test_quits_rate_surprise_rejects_noncanonical_public_aggregate_ordering() -> None:
    summary = report(
        (
            observation(
                "2026-06",
                actual="2.400000",
                consensus="2.100000",
                previous="2.000000",
                observed_at=GENERATED_AT - timedelta(hours=3),
            ),
            observation(
                "2026-05",
                actual="1.850000",
                consensus="2.000000",
                previous="1.950000",
                observed_at=GENERATED_AT - timedelta(hours=3),
                source_count=d("1.000000"),
            ),
        ),
    )

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            summary.observations[1],
            reason_codes=tuple(reversed(summary.observations[1].reason_codes)),
        )
    with pytest.raises(ValueError, match="observations"):
        replace(summary, observations=tuple(reversed(summary.observations)))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(summary, reason_code_counts=tuple(reversed(summary.reason_code_counts)))


def test_quits_rate_surprise_preserves_subsecond_observation_age() -> None:
    summary = report(
        (
            observation(
                "subsecond",
                actual="2.080000",
                consensus="2.000000",
                previous="1.990000",
                observed_at=GENERATED_AT - timedelta(microseconds=500000),
            ),
        ),
    )

    assert summary.observations[0].observation_age_seconds == d("0.500000")


def test_quits_rate_surprise_module_has_no_forbidden_side_effect_imports() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_research_quits_rate_surprise_digest.py"
    )
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_roots = {
        "httpx",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
        "urllib",
        "web3",
    }
    forbidden_calls = {
        "open",
        "connect",
        "execute",
        "commit",
        "request",
        "read_text",
        "write_text",
        "urlopen",
        "post",
        "put",
        "patch",
        "delete",
        "send",
        "submit",
        "trade",
        "place_order",
        "cancel_order",
        "replace_order",
        "sign",
    }
    string_literals: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [alias.name for alias in getattr(node, "names", ())]
            if isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module)
            assert not any(name.split(".")[0] in forbidden_roots for name in names)
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            if isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            string_literals.append(node.value.lower())

    joined_strings = "\n".join(string_literals)
    for forbidden in (
        "live trading",
        "auth",
        "wallet",
        "order placement",
        "order cancel",
        "order replace",
        "exchange mutation",
        "private_key",
        "api_key",
        "secret",
        "token",
        "database",
        "durable",
        "network",
    ):
        assert forbidden not in joined_strings


def walk_values(value: object):
    if isinstance(value, dict):
        for item in value.values():
            yield from walk_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from walk_values(item)
    else:
        yield value

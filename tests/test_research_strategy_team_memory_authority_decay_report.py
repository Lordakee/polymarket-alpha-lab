from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Context, Decimal, ROUND_DOWN, localcontext
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_strategy_team_memory_authority_decay_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_team_memory_authority_decay_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 11, 45, tzinfo=UTC)


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def cfg(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": "research-strategy-team-memory-authority-decay-report-v1",
        "watch_authority_decay_score": d("0.350000"),
        "block_authority_decay_score": d("0.700000"),
        "watch_memory_age_seconds": d("86400.000000"),
        "block_memory_age_seconds": d("259200.000000"),
        "watch_stale_memory_ratio": d("0.400000"),
        "block_stale_memory_ratio": d("0.700000"),
        "watch_unresolved_conflict_ratio": d("0.300000"),
        "block_unresolved_conflict_ratio": d("0.600000"),
        "min_pass_team_confidence_score": d("0.750000"),
        "min_watch_team_confidence_score": d("0.500000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchStrategyTeamMemoryAuthorityDecayConfig(**values)


def observation(
    *,
    team_key: str = "team-alpha",
    authority_family_key: str = "authority-family-a",
    observed_at: datetime = OBSERVED_AT,
    memory_age_seconds: Decimal = d("3600.000000"),
    stale_memory_ratio: Decimal = d("0.100000"),
    authority_decay_score: Decimal = d("0.100000"),
    unresolved_conflict_ratio: Decimal = d("0.050000"),
    team_confidence_score: Decimal = d("0.900000"),
    evidence_reuse_count: Decimal = d("3.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchStrategyTeamMemoryAuthorityDecayObservation(
        team_key=team_key,
        authority_family_key=authority_family_key,
        observed_at=observed_at,
        memory_age_seconds=memory_age_seconds,
        stale_memory_ratio=stale_memory_ratio,
        authority_decay_score=authority_decay_score,
        unresolved_conflict_ratio=unresolved_conflict_ratio,
        team_confidence_score=team_confidence_score,
        evidence_reuse_count=evidence_reuse_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *observations: object,
    generated_at: datetime = GENERATED_AT,
    config: object | None = None,
):
    module = api()
    return module.build_research_strategy_team_memory_authority_decay_report(
        observations,
        generated_at=generated_at,
        config=config or cfg(),
    )


def assert_no_public_number_payload(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"payload numeric was not serialized as string: {value!r}")
    if isinstance(value, dict):
        for item_value in value.values():
            assert_no_public_number_payload(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_public_number_payload(item_value)


def assert_no_forbidden_public_surface(value: Any) -> None:
    forbidden_fragments = (
        "raw",
        "candidate",
        "market",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "network",
        "database",
        "order",
        "buy",
        "sell",
        "trade",
        "position",
        "recommend",
        "sizing",
        "live",
    )
    if isinstance(value, dict):
        for key, item_value in value.items():
            lowered = key.lower()
            for fragment in forbidden_fragments:
                assert fragment not in lowered, key
            assert_no_forbidden_public_surface(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_forbidden_public_surface(item_value)
        return
    if isinstance(value, str):
        lowered = value.lower()
        assert "://" not in lowered
        for fragment in forbidden_fragments:
            assert fragment not in lowered, value


def assert_decimal_public_fields(value: object) -> None:
    decimal_markers = (
        "count",
        "score",
        "seconds",
        "ratio",
        "age",
        "confidence",
        "reuse",
        "max",
        "min",
        "total",
    )
    for field in fields(value):
        if field.name in {"rows", "reason_codes"}:
            continue
        if any(marker in field.name for marker in decimal_markers):
            assert type(getattr(value, field.name)) is Decimal, field.name


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    resigned = json.loads(json.dumps(payload))
    resigned.pop("derived_validation_digest", None)
    encoded = json.dumps(
        resigned,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    resigned["derived_validation_digest"] = hashlib.sha256(encoded).hexdigest()
    return resigned


def set_payload_path(
    payload: dict[str, Any],
    path: tuple[str | int, ...],
    value: object,
) -> None:
    target: Any = payload
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value


def test_empty_input_returns_pass_report_only_decimal_digest() -> None:
    module = api()
    empty_report = report()

    assert is_dataclass(empty_report)
    assert empty_report.generated_at == GENERATED_AT
    assert empty_report.config_version == (
        "research-strategy-team-memory-authority-decay-report-v1"
    )
    assert empty_report.status == "pass"
    assert empty_report.reason_codes == ("team_memory_authority_decay_passed",)
    assert empty_report.observation_count == d("0.000000")
    assert empty_report.pass_count == d("0.000000")
    assert empty_report.watch_count == d("0.000000")
    assert empty_report.block_count == d("0.000000")
    assert empty_report.max_memory_age_seconds == d("0.000000")
    assert empty_report.max_stale_memory_ratio == d("0.000000")
    assert empty_report.max_authority_decay_score == d("0.000000")
    assert empty_report.max_decay_pressure_score == d("0.000000")
    assert empty_report.min_team_confidence_score == d("0.000000")
    assert empty_report.total_evidence_reuse_count == d("0.000000")
    assert empty_report.rows == ()
    assert empty_report.paper_only is True
    assert empty_report.report_only is True
    assert empty_report.readonly is True
    assert_decimal_public_fields(empty_report)

    payload = module.research_strategy_team_memory_authority_decay_report_payload(
        empty_report,
    )
    digest_value = module.research_strategy_team_memory_authority_decay_report_digest(
        empty_report,
    )
    json.dumps(payload, sort_keys=True)
    assert_no_public_number_payload(payload)
    assert_no_forbidden_public_surface(payload)
    assert payload["status"] == "pass"
    assert payload["observation_count"] == "0.000000"
    assert payload["derived_validation_digest"] == digest_value
    assert len(digest_value) == 64
    assert set(digest_value) <= set("0123456789abcdef")


def test_report_scores_authority_memory_conflict_and_confidence_decay() -> None:
    passed = observation(
        team_key="team-charlie",
        authority_family_key="authority-family-c",
        observed_at=GENERATED_AT - timedelta(minutes=5),
    )
    watched = observation(
        team_key="team-bravo",
        authority_family_key="authority-family-b",
        observed_at=GENERATED_AT - timedelta(minutes=10),
        authority_decay_score=d("0.450000"),
        team_confidence_score=d("0.650000"),
    )
    blocked = observation(
        team_key="team-alpha",
        authority_family_key="authority-family-a",
        observed_at=GENERATED_AT - timedelta(minutes=15),
        memory_age_seconds=d("300000.000000"),
        stale_memory_ratio=d("0.800000"),
        authority_decay_score=d("0.850000"),
        unresolved_conflict_ratio=d("0.700000"),
        team_confidence_score=d("0.400000"),
        evidence_reuse_count=d("8.000000"),
    )

    built = report(passed, watched, blocked)

    assert built.status == "block"
    assert built.observation_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.max_memory_age_seconds == d("300000.000000")
    assert built.max_stale_memory_ratio == d("0.800000")
    assert built.max_authority_decay_score == d("0.850000")
    assert built.min_team_confidence_score == d("0.400000")
    assert built.total_evidence_reuse_count == d("14.000000")
    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")
    assert set(row.status for row in built.rows) <= {"pass", "watch", "block"}

    blocked_row, watched_row, passed_row = built.rows
    assert blocked_row.decay_pressure_score == d("0.885000")
    assert blocked_row.reason_codes == (
        "authority_decay_score_block",
        "memory_age_block",
        "stale_memory_ratio_block",
        "unresolved_conflict_ratio_block",
        "team_confidence_score_block",
        "team_memory_authority_decay_block",
    )
    assert watched_row.status == "watch"
    assert watched_row.decay_pressure_score == d("0.195000")
    assert watched_row.reason_codes == (
        "authority_decay_score_watch",
        "team_confidence_score_watch",
        "team_memory_authority_decay_watch",
    )
    assert passed_row.status == "pass"
    assert passed_row.reason_codes == ("team_memory_authority_decay_passed",)


def test_payload_is_sanitized_deterministic_and_digest_checked() -> None:
    module = api()
    observations = (
        observation(
            team_key="team-bravo",
            authority_family_key="authority-family-b",
            authority_decay_score=d("0.450000"),
        ),
        observation(
            team_key="team-alpha",
            authority_family_key="authority-family-a",
            observed_at=GENERATED_AT - timedelta(seconds=30),
            memory_age_seconds=d("300000.000000"),
            stale_memory_ratio=d("0.800000"),
            authority_decay_score=d("0.850000"),
            unresolved_conflict_ratio=d("0.700000"),
            team_confidence_score=d("0.400000"),
        ),
    )
    first = report(*observations)
    second = report(*reversed(observations))

    payload = first.payload
    encoded_payload = json.dumps(payload, sort_keys=True)
    json.dumps(payload, sort_keys=True)
    assert payload["observation_count"] == "2.000000"
    assert payload["rows"][0]["status"] == "block"
    assert payload["rows"][0]["authority_decay_rank"] == "1.000000"
    assert payload["rows"][0]["team_sequence"] == "1.000000"
    assert payload["rows"][1]["authority_decay_score"] == "0.450000"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert first.derived_validation_digest == second.derived_validation_digest
    assert "team-alpha" not in encoded_payload
    assert "team-bravo" not in encoded_payload
    assert "authority-family-a" not in encoded_payload
    assert "authority-family-b" not in encoded_payload
    assert module.research_strategy_team_memory_authority_decay_report_digest(first) == (
        first.derived_validation_digest
    )
    assert_no_public_number_payload(payload)
    assert_no_forbidden_public_surface(payload)
    assert_decimal_public_fields(first)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)

    tampered = dict(payload)
    tampered["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_strategy_team_memory_authority_decay_public_payload(
            tampered,
        )

    unsafe_key_payload = dict(payload)
    unsafe_key_payload["candidate"] = "not-public"
    with pytest.raises(ValueError, match="unsafe"):
        module.validate_research_strategy_team_memory_authority_decay_public_payload(
            unsafe_key_payload,
        )

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["rows"] = [
        dict(payload["rows"][0], reason_codes=["http://x.invalid"]),
        *payload["rows"][1:],
    ]
    with pytest.raises(ValueError, match="unsafe"):
        module.validate_research_strategy_team_memory_authority_decay_public_payload(
            unsafe_value_payload,
        )


@pytest.mark.parametrize(
    ("path", "forged_value", "message"),
    (
        (("status",), "pass", "status must match rows"),
        (("observation_count",), "2.000000", "observation_count must match rows"),
        (("block_count",), "0.000000", "block_count must match rows"),
        (
            ("max_authority_decay_score",),
            "0.100000",
            "max_authority_decay_score must match rows",
        ),
        (
            ("reason_codes",),
            ["team_memory_authority_decay_passed"],
            "reason_codes must match rows",
        ),
        (("rows", 0, "status"), "watch", "derived values"),
        (
            ("rows", 0, "reason_codes"),
            ["team_memory_authority_decay_passed"],
            "derived values",
        ),
        (
            ("rows", 0, "decay_pressure_score"),
            "0.884999",
            "decay_pressure_score must match derived values",
        ),
        (
            ("rows", 0, "authority_decay_rank"),
            "2.000000",
            "authority_decay_rank must match derived values",
        ),
    ),
)
def test_resigned_payload_rejects_forged_derived_values(
    path: tuple[str | int, ...],
    forged_value: object,
    message: str,
) -> None:
    module = api()
    payload = report(
        observation(
            memory_age_seconds=d("300000.000000"),
            stale_memory_ratio=d("0.800000"),
            authority_decay_score=d("0.850000"),
            unresolved_conflict_ratio=d("0.700000"),
            team_confidence_score=d("0.400000"),
            evidence_reuse_count=d("8.000000"),
        ),
    ).payload
    set_payload_path(payload, path, forged_value)
    forged = resign_payload(payload)

    with pytest.raises(ValueError, match=message):
        module.validate_research_strategy_team_memory_authority_decay_public_payload(
            forged,
        )


@pytest.mark.parametrize(
    ("field_name", "value", "message"),
    (
        ("memory_age_seconds", d("-0.0000004"), "memory_age_seconds must be nonnegative"),
        (
            "evidence_reuse_count",
            d("-0.0000004"),
            "evidence_reuse_count must be nonnegative",
        ),
        (
            "stale_memory_ratio",
            d("-0.0000004"),
            "stale_memory_ratio must be between zero and one",
        ),
        (
            "authority_decay_score",
            d("1.0000004"),
            "authority_decay_score must be between zero and one",
        ),
        (
            "unresolved_conflict_ratio",
            d("1.0000004"),
            "unresolved_conflict_ratio must be between zero and one",
        ),
        (
            "team_confidence_score",
            d("-0.0000004"),
            "team_confidence_score must be between zero and one",
        ),
    ),
)
def test_raw_decimal_bounds_are_checked_before_quantization(
    field_name: str,
    value: Decimal,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        observation(**{field_name: value})


@pytest.mark.parametrize(
    "field_name",
    (
        "memory_age_seconds",
        "stale_memory_ratio",
        "authority_decay_score",
        "unresolved_conflict_ratio",
        "team_confidence_score",
        "evidence_reuse_count",
    ),
)
def test_signed_zero_decimal_inputs_are_rejected(field_name: str) -> None:
    with pytest.raises(ValueError, match=f"{field_name} must not be signed zero"):
        observation(**{field_name: d("-0.000000")})


@pytest.mark.parametrize("value", ("NaN", "sNaN", "Infinity", "-Infinity"))
def test_non_finite_decimal_inputs_are_rejected(value: str) -> None:
    with pytest.raises(ValueError, match="authority_decay_score must be finite"):
        observation(authority_decay_score=d(value))


def test_resigned_public_payload_rejects_signed_zero() -> None:
    module = api()
    payload = report().payload
    payload["observation_count"] = "-0.000000"
    forged = resign_payload(payload)

    with pytest.raises(ValueError, match="observation_count must not be signed zero"):
        module.validate_research_strategy_team_memory_authority_decay_public_payload(
            forged,
        )


def test_payload_validation_preserves_supported_custom_config_outputs() -> None:
    module = api()
    custom = cfg(
        watch_authority_decay_score=d("0.200000"),
        block_authority_decay_score=d("0.600000"),
    )
    built = report(
        observation(authority_decay_score=d("0.650000")),
        config=custom,
    )

    payload = built.payload

    assert payload["status"] == "block"
    assert payload["rows"][0]["status"] == "block"
    assert payload["config"]["watch_authority_decay_score"] == "0.200000"
    assert payload["config"]["block_authority_decay_score"] == "0.600000"
    module.validate_research_strategy_team_memory_authority_decay_public_payload(
        payload,
    )


def test_decimal_math_and_digest_ignore_ambient_context() -> None:
    baseline = report(
        observation(
            memory_age_seconds=d("300000.000000"),
            stale_memory_ratio=d("0.8123456"),
            authority_decay_score=d("0.8567894"),
            unresolved_conflict_ratio=d("0.7345675"),
            team_confidence_score=d("0.4123455"),
            evidence_reuse_count=d("8.000000"),
        ),
    )

    with localcontext(Context(prec=3, rounding=ROUND_DOWN)):
        constrained = report(
            observation(
                memory_age_seconds=d("300000.000000"),
                stale_memory_ratio=d("0.8123456"),
                authority_decay_score=d("0.8567894"),
                unresolved_conflict_ratio=d("0.7345675"),
                team_confidence_score=d("0.4123455"),
                evidence_reuse_count=d("8.000000"),
            ),
        )

    assert constrained == baseline
    assert constrained.payload == baseline.payload


def test_evidence_reuse_count_must_be_a_whole_decimal() -> None:
    with pytest.raises(ValueError, match="evidence_reuse_count must be whole"):
        observation(evidence_reuse_count=d("1.500000"))


def test_public_payload_uses_only_privacy_safe_sequences() -> None:
    built = report(
        observation(
            team_key="private-team-zeta",
            authority_family_key="private-authority-zeta",
        ),
        observation(
            team_key="private-team-alpha",
            authority_family_key="private-authority-alpha",
            authority_decay_score=d("0.450000"),
        ),
    )

    encoded = json.dumps(built.payload, sort_keys=True)
    assert "private-team-zeta" not in encoded
    assert "private-team-alpha" not in encoded
    assert "private-authority-zeta" not in encoded
    assert "private-authority-alpha" not in encoded
    assert tuple(row.team_sequence for row in built.rows) == (
        d("1.000000"),
        d("2.000000"),
    )
    assert tuple(row.authority_family_sequence for row in built.rows) == (
        d("1.000000"),
        d("2.000000"),
    )


def test_complete_tie_break_and_ranks_are_input_order_independent() -> None:
    first_observation = observation(
        team_key="same-team",
        authority_family_key="same-authority-family",
        stale_memory_ratio=d("0.100000"),
        unresolved_conflict_ratio=d("0.200000"),
        team_confidence_score=d("0.900000"),
        evidence_reuse_count=d("1.000000"),
    )
    second_observation = observation(
        team_key="same-team",
        authority_family_key="same-authority-family",
        stale_memory_ratio=d("0.200000"),
        unresolved_conflict_ratio=d("0.100000"),
        team_confidence_score=d("0.800000"),
        evidence_reuse_count=d("2.000000"),
    )

    forward = report(first_observation, second_observation)
    reverse = report(second_observation, first_observation)

    assert forward == reverse
    assert forward.payload == reverse.payload
    assert tuple(row.authority_decay_rank for row in forward.rows) == (
        d("1.000000"),
        d("2.000000"),
    )


def test_resigned_payload_rederives_threshold_status_reason_score_and_counts() -> None:
    module = api()
    payload = report(
        observation(authority_decay_score=d("0.200000")),
    ).payload
    row = payload["rows"][0]
    row["status"] = "block"
    row["reason_codes"] = [
        "authority_decay_score_block",
        "team_memory_authority_decay_block",
    ]
    row["decay_pressure_score"] = "0.127500"
    payload["status"] = "block"
    payload["pass_count"] = "0.000000"
    payload["block_count"] = "1.000000"
    payload["max_decay_pressure_score"] = "0.127500"
    payload["reason_codes"] = [
        "authority_decay_score_block",
        "team_memory_authority_decay_block",
    ]

    with pytest.raises(ValueError, match="derived values"):
        module.validate_research_strategy_team_memory_authority_decay_public_payload(
            resign_payload(payload),
        )


def test_digest_revalidates_low_level_resigned_report_mutation() -> None:
    module = api()
    built = report(observation())
    forged_payload = built.payload
    forged_payload["status"] = "block"
    forged_payload.pop("derived_validation_digest")
    forged_digest = hashlib.sha256(
        json.dumps(
            forged_payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
    object.__setattr__(built, "status", "block")
    object.__setattr__(built, "derived_validation_digest", forged_digest)

    with pytest.raises(ValueError, match="status must match rows"):
        module.research_strategy_team_memory_authority_decay_report_digest(built)


def test_digest_rejects_low_level_noncanonical_equivalent_timestamp() -> None:
    module = api()
    built = report(observation())
    object.__setattr__(
        built,
        "generated_at",
        datetime(2026, 7, 9, 13, 0, tzinfo=timezone(timedelta(hours=1))),
    )

    with pytest.raises(ValueError, match="generated_at must be canonical UTC datetime"):
        module.research_strategy_team_memory_authority_decay_report_digest(built)


def test_resigned_payload_rederives_exact_block_score() -> None:
    module = api()
    payload = report(
        observation(team_confidence_score=d("0.400000")),
    ).payload
    payload["rows"][0]["decay_pressure_score"] = "0.300000"
    payload["max_decay_pressure_score"] = "0.300000"

    with pytest.raises(ValueError, match="derived values"):
        module.validate_research_strategy_team_memory_authority_decay_public_payload(
            resign_payload(payload),
        )


@pytest.mark.parametrize("target", ("report", "config", "row"))
def test_resigned_payload_rejects_noncanonical_field_order(target: str) -> None:
    module = api()
    payload = report(observation()).payload
    if target == "report":
        payload = dict(reversed(tuple(payload.items())))
    elif target == "config":
        payload["config"] = dict(reversed(tuple(payload["config"].items())))
    else:
        payload["rows"][0] = dict(reversed(tuple(payload["rows"][0].items())))

    with pytest.raises(ValueError, match="canonical order"):
        module.validate_research_strategy_team_memory_authority_decay_public_payload(
            resign_payload(payload),
        )


def test_dataclasses_are_frozen_and_reject_subclassing_and_bad_flags() -> None:
    module = api()
    built = report(observation())

    with pytest.raises(FrozenInstanceError):
        built.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(module.ResearchStrategyTeamMemoryAuthorityDecayConfig):
            pass

    for cls in (
        module.ResearchStrategyTeamMemoryAuthorityDecayObservation,
        module.ResearchStrategyTeamMemoryAuthorityDecayRow,
        module.ResearchStrategyTeamMemoryAuthorityDecayReport,
    ):
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Bad{cls.__name__}", (cls,), {})

    with pytest.raises(ValueError, match="paper_only"):
        cfg(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        observation(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(built.rows[0], readonly=False)


def test_dataclasses_and_payloads_have_exact_frozen_schemas() -> None:
    module = api()
    built = report(observation())
    expected_fields = {
        module.ResearchStrategyTeamMemoryAuthorityDecayConfig: (
            "config_version",
            "watch_authority_decay_score",
            "block_authority_decay_score",
            "watch_memory_age_seconds",
            "block_memory_age_seconds",
            "watch_stale_memory_ratio",
            "block_stale_memory_ratio",
            "watch_unresolved_conflict_ratio",
            "block_unresolved_conflict_ratio",
            "min_pass_team_confidence_score",
            "min_watch_team_confidence_score",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchStrategyTeamMemoryAuthorityDecayObservation: (
            "team_key",
            "authority_family_key",
            "observed_at",
            "memory_age_seconds",
            "stale_memory_ratio",
            "authority_decay_score",
            "unresolved_conflict_ratio",
            "team_confidence_score",
            "evidence_reuse_count",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchStrategyTeamMemoryAuthorityDecayRow: (
            "authority_decay_rank",
            "team_sequence",
            "authority_family_sequence",
            "observed_at",
            "memory_age_seconds",
            "stale_memory_ratio",
            "authority_decay_score",
            "unresolved_conflict_ratio",
            "team_confidence_score",
            "evidence_reuse_count",
            "decay_pressure_score",
            "status",
            "reason_codes",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchStrategyTeamMemoryAuthorityDecayReport: (
            "generated_at",
            "config_version",
            "config",
            "status",
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_memory_age_seconds",
            "max_stale_memory_ratio",
            "max_authority_decay_score",
            "max_decay_pressure_score",
            "min_team_confidence_score",
            "total_evidence_reuse_count",
            "rows",
            "reason_codes",
            "paper_only",
            "report_only",
            "readonly",
            "derived_validation_digest",
        ),
    }

    for cls, field_names in expected_fields.items():
        assert cls.__dataclass_params__.frozen is True
        assert tuple(field.name for field in fields(cls)) == field_names

    payload = built.payload
    assert tuple(payload) == expected_fields[
        module.ResearchStrategyTeamMemoryAuthorityDecayReport
    ]
    assert tuple(payload["rows"][0]) == expected_fields[
        module.ResearchStrategyTeamMemoryAuthorityDecayRow
    ]


def test_public_dataclasses_are_slotted_runtime_final_and_exact() -> None:
    module = api()
    public_dataclasses = (
        module.ResearchStrategyTeamMemoryAuthorityDecayConfig,
        module.ResearchStrategyTeamMemoryAuthorityDecayObservation,
        module.ResearchStrategyTeamMemoryAuthorityDecayRow,
        module.ResearchStrategyTeamMemoryAuthorityDecayReport,
    )

    for cls in public_dataclasses:
        assert getattr(cls, "__final__", False) is True
        assert tuple(cls.__slots__) == tuple(field.name for field in fields(cls))
        assert "__dict__" not in cls.__dict__


def test_phase_one_surface_is_pure_report_only_paper_only_and_readonly() -> None:
    module = api()
    built = report(observation())
    for value in (cfg(), observation(), built.rows[0], built):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "database",
        "db",
        "http",
        "network",
        "order",
        "persist",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "urllib",
        "wallet",
        "web3",
    )
    forbidden_calls_or_attributes = {
        "buy",
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "execute",
        "executemany",
        "fetch",
        "insert",
        "mkdir",
        "open",
        "order",
        "persist",
        "recommend",
        "rollback",
        "sell",
        "send",
        "sign",
        "sizing",
        "trade",
        "unlink",
        "write",
        "write_bytes",
        "write_text",
    }

    assert not any(
        fragment in imported.lower()
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert forbidden_calls_or_attributes.isdisjoint(call_names)
    assert forbidden_calls_or_attributes.isdisjoint(attribute_names)


def test_strict_types_public_api_and_no_live_dependency_surface() -> None:
    module = api()
    with pytest.raises(ValueError, match="authority_decay_score must be exactly Decimal"):
        observation(authority_decay_score=_DecimalSubclass("0.400000"))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="stale_memory_ratio must be a Decimal"):
        observation(stale_memory_ratio=0.4)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="team_key"):
        observation(team_key="candidate://raw")

    with pytest.raises(ValueError, match="timezone-aware"):
        observation(observed_at=datetime(2026, 7, 9, 11, 45))

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report(observation(), generated_at=_DatetimeSubclass(2026, 7, 9, 12, tzinfo=UTC))

    with pytest.raises(ValueError, match="utcoffset"):
        observation(observed_at=datetime(2026, 7, 9, 11, 45, tzinfo=_NoneOffsetTz()))

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="block_authority_decay_score"):
        cfg(block_authority_decay_score=d("0.300000"))

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
    forbidden_imports = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "web3",
        "py_clob_client",
    }
    assert imported_roots.isdisjoint(forbidden_imports)

    assert module.RESEARCH_STRATEGY_TEAM_MEMORY_AUTHORITY_DECAY_STATUSES == (
        "pass",
        "watch",
        "block",
    )

    forbidden_public_name_fragments = (
        "client",
        "wallet",
        "http",
        "request",
        "network",
        "database",
        "dsn",
        "table",
        "token",
        "order",
        "trade",
        "sizing",
        "recommend",
        "live",
    )
    for public_name in module.__all__:
        lowered = public_name.lower()
        assert all(fragment not in lowered for fragment in forbidden_public_name_fragments)

    forbidden_field_fragments = (
        "raw",
        "candidate",
        "market",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "network",
        "database",
        "order",
        "trade",
        "sizing",
        "recommend",
        "live",
    )
    for cls in (
        module.ResearchStrategyTeamMemoryAuthorityDecayConfig,
        module.ResearchStrategyTeamMemoryAuthorityDecayObservation,
        module.ResearchStrategyTeamMemoryAuthorityDecayRow,
        module.ResearchStrategyTeamMemoryAuthorityDecayReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert all(fragment not in lowered for fragment in forbidden_field_fragments)


@pytest.mark.parametrize(
    ("path", "noncanonical_value"),
    (
        (("generated_at",), "2026-07-09T12:00:00Z"),
        (("generated_at",), "2026-07-09T13:00:00+01:00"),
        (("rows", 0, "observed_at"), "2026-07-09T12:45:00+01:00"),
    ),
)
def test_resigned_payload_rejects_noncanonical_datetime_strings(
    path: tuple[str | int, ...],
    noncanonical_value: str,
) -> None:
    module = api()
    payload = report(observation()).payload
    set_payload_path(payload, path, noncanonical_value)

    with pytest.raises(ValueError, match="must be a canonical UTC datetime"):
        module.validate_research_strategy_team_memory_authority_decay_public_payload(
            resign_payload(payload),
        )


def test_team_and_family_sequences_are_rederived_from_ranked_rows() -> None:
    module = api()
    built = report(
        observation(
            team_key="team-zeta",
            authority_family_key="authority-family-zeta",
            authority_decay_score=d("0.800000"),
        ),
        observation(
            team_key="team-alpha",
            authority_family_key="authority-family-alpha",
        ),
    )

    assert tuple(row.team_sequence for row in built.rows) == (
        d("1.000000"),
        d("2.000000"),
    )
    assert tuple(row.authority_family_sequence for row in built.rows) == (
        d("1.000000"),
        d("2.000000"),
    )

    for field_name in ("team_sequence", "authority_family_sequence"):
        payload = built.payload
        payload["rows"][0][field_name] = "2.000000"
        payload["rows"][1][field_name] = "1.000000"
        with pytest.raises(ValueError, match=f"{field_name} must match derived values"):
            module.validate_research_strategy_team_memory_authority_decay_public_payload(
                resign_payload(payload),
            )


def test_1001_rows_ignore_ambient_decimal_context() -> None:
    observations = tuple(observation() for _ in range(1001))

    with localcontext(Context(prec=3, rounding=ROUND_DOWN)):
        built = report(*observations)
        payload = built.payload

    assert built.observation_count == d("1001.000000")
    assert built.pass_count == d("1001.000000")
    assert built.watch_count == d("0.000000")
    assert built.block_count == d("0.000000")
    assert payload["observation_count"] == "1001.000000"


def test_independent_watch_row_rejects_forged_derived_score() -> None:
    watched_row = report(
        observation(authority_decay_score=d("0.450000")),
    ).rows[0]

    with pytest.raises(ValueError, match="decay_pressure_score must match derived values"):
        replace(watched_row, decay_pressure_score=d("0.000001"))


@pytest.mark.parametrize(
    ("overrides", "expected_status", "expected_reason"),
    (
        (
            {"authority_decay_score": d("0.350000")},
            "watch",
            "authority_decay_score_watch",
        ),
        (
            {"authority_decay_score": d("0.700000")},
            "block",
            "authority_decay_score_block",
        ),
        (
            {"memory_age_seconds": d("86400.000000")},
            "watch",
            "memory_age_watch",
        ),
        (
            {"memory_age_seconds": d("259200.000000")},
            "block",
            "memory_age_block",
        ),
        (
            {"stale_memory_ratio": d("0.400000")},
            "watch",
            "stale_memory_ratio_watch",
        ),
        (
            {"stale_memory_ratio": d("0.700000")},
            "block",
            "stale_memory_ratio_block",
        ),
        (
            {"unresolved_conflict_ratio": d("0.300000")},
            "watch",
            "unresolved_conflict_ratio_watch",
        ),
        (
            {"unresolved_conflict_ratio": d("0.600000")},
            "block",
            "unresolved_conflict_ratio_block",
        ),
        (
            {"team_confidence_score": d("0.749999")},
            "watch",
            "team_confidence_score_watch",
        ),
        (
            {"team_confidence_score": d("0.499999")},
            "block",
            "team_confidence_score_block",
        ),
    ),
)
def test_threshold_endpoints_have_explicit_inclusive_exclusive_semantics(
    overrides: dict[str, Decimal],
    expected_status: str,
    expected_reason: str,
) -> None:
    row = report(observation(**overrides)).rows[0]

    assert row.status == expected_status
    assert expected_reason in row.reason_codes

    assert report(
        observation(team_confidence_score=d("0.750000")),
    ).rows[0].status == "pass"
    assert report(
        observation(team_confidence_score=d("0.500000")),
    ).rows[0].status == "watch"


def test_observed_at_is_the_final_public_tie_break() -> None:
    earlier = observation(observed_at=GENERATED_AT - timedelta(minutes=2))
    later = observation(observed_at=GENERATED_AT - timedelta(minutes=1))

    forward = report(later, earlier)
    reverse = report(earlier, later)

    assert forward == reverse
    assert tuple(row.observed_at for row in forward.rows) == (
        earlier.observed_at,
        later.observed_at,
    )


@pytest.mark.parametrize("target", ("report", "config", "row"))
def test_resigned_payload_rejects_schema_extensions(target: str) -> None:
    module = api()
    payload = report(observation()).payload
    if target == "report":
        payload["extension"] = "unsupported"
    elif target == "config":
        payload["config"]["extension"] = "unsupported"
    else:
        payload["rows"][0]["extension"] = "unsupported"

    with pytest.raises(ValueError, match="unsupported field: extension"):
        module.validate_research_strategy_team_memory_authority_decay_public_payload(
            resign_payload(payload),
        )


def test_module_has_no_filesystem_process_or_dynamic_execution_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    forbidden_import_roots = {
        "asyncio",
        "os",
        "pathlib",
        "shutil",
        "subprocess",
        "tempfile",
    }
    forbidden_name_calls = {
        "__import__",
        "compile",
        "eval",
        "exec",
        "open",
    }
    forbidden_attribute_calls = {
        "open",
        "run",
        "system",
    }
    imported_roots: set[str] = set()
    called_name_functions: set[str] = set()
    called_attribute_functions: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_name_functions.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_attribute_functions.add(node.func.attr)

    assert imported_roots.isdisjoint(forbidden_import_roots)
    assert called_name_functions.isdisjoint(forbidden_name_calls)
    assert called_attribute_functions.isdisjoint(forbidden_attribute_calls)

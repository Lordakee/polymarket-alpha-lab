from __future__ import annotations

import ast
import importlib
from itertools import permutations
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal, Inexact, ROUND_DOWN, localcontext
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_strategy_event_source_freshness_quorum_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_event_source_freshness_quorum_report.py"
)
GENERATED_AT = datetime(2026, 7, 10, 12, 0, tzinfo=UTC)
ROW_DIGEST_LABEL = "research_strategy_event_source_freshness_quorum_report_row"
REPORT_DIGEST_LABEL = "research_strategy_event_source_freshness_quorum_report"


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def cfg(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": (
            "research-strategy-event-source-freshness-quorum-report-test-v0"
        ),
        "freshness_watch_age_seconds": d("1800.000000"),
        "freshness_block_age_seconds": d("7200.000000"),
        "quorum_pass_threshold": d("0.750000"),
        "quorum_block_threshold": d("0.500000"),
        "independent_quorum_pass_threshold": d("0.750000"),
        "independent_quorum_block_threshold": d("0.500000"),
        "freshness_weight": d("0.400000"),
        "evidence_quorum_weight": d("0.350000"),
        "independent_quorum_weight": d("0.250000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchStrategyEventSourceFreshnessQuorumConfig(**values)


def observation(
    event_label: str,
    *,
    public_source_label: str = "official_release",
    private_source_identifier: str = "secret://source/internal-001",
    observed_at: datetime = GENERATED_AT - timedelta(minutes=15),
    evidence_count: Decimal = d("4.000000"),
    required_evidence_count: Decimal = d("4.000000"),
    independent_evidence_count: Decimal = d("2.000000"),
    required_independent_evidence_count: Decimal = d("2.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchStrategyEventSourceFreshnessQuorumObservation(
        event_label=event_label,
        public_source_label=public_source_label,
        private_source_identifier=private_source_identifier,
        observed_at=observed_at,
        evidence_count=evidence_count,
        required_evidence_count=required_evidence_count,
        independent_evidence_count=independent_evidence_count,
        required_independent_evidence_count=required_independent_evidence_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def sample_observations() -> tuple[Any, ...]:
    return (
        observation(
            "event-watch",
            public_source_label="specialist_confirmation",
            private_source_identifier="private-specialist-7788",
            observed_at=GENERATED_AT - timedelta(hours=1),
            evidence_count=d("3.000000"),
            required_evidence_count=d("4.000000"),
            independent_evidence_count=d("1.000000"),
            required_independent_evidence_count=d("2.000000"),
        ),
        observation(
            "event-pass",
            public_source_label="official_release",
            private_source_identifier="https://hidden.example/private/source?id=pass",
            observed_at=GENERATED_AT - timedelta(minutes=15),
        ),
        observation(
            "event-block",
            public_source_label="secondary_confirmation",
            private_source_identifier="wallet-secret-market-source-001",
            observed_at=GENERATED_AT - timedelta(hours=3),
            evidence_count=d("1.000000"),
            required_evidence_count=d("4.000000"),
            independent_evidence_count=d("1.000000"),
            required_independent_evidence_count=d("2.000000"),
        ),
    )


def report(
    observations: tuple[Any, ...] | None = None,
    *,
    generated_at: datetime = GENERATED_AT,
    config: object | None = None,
) -> Any:
    module = api()
    return module.build_research_strategy_event_source_freshness_quorum_report(
        sample_observations() if observations is None else observations,
        generated_at=generated_at,
        config=config or cfg(),
    )


def canonical_digest(label: str, payload: dict[str, object]) -> str:
    canonical = json.dumps(
        {key: value for key, value in payload.items() if key != "derived_validation_digest"},
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(f"{label}|{canonical}".encode("utf-8")).hexdigest()


def resign_payload(payload: dict[str, object]) -> dict[str, object]:
    for row in payload["rows"]:
        row["derived_validation_digest"] = canonical_digest(ROW_DIGEST_LABEL, row)
    payload["derived_validation_digest"] = canonical_digest(REPORT_DIGEST_LABEL, payload)
    return payload


def assert_json_scalars_only(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            assert_json_scalars_only(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_json_scalars_only(item)
        return
    assert type(value) not in (Decimal, float, int, datetime)


def test_builds_deterministic_freshness_and_quorum_diagnostic_report() -> None:
    built = report()

    assert is_dataclass(built)
    assert built.status == "block"
    assert built.event_source_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.stale_count == d("2.000000")
    assert built.quorum_deficit_count == d("2.000000")
    assert built.average_freshness_score == d("0.458333")
    assert built.average_evidence_quorum_score == d("0.666667")
    assert built.average_independent_quorum_score == d("0.666667")
    assert built.average_diagnostic_score == d("0.583333")
    assert built.minimum_diagnostic_score == d("0.212500")
    assert built.maximum_source_age_seconds == d("10800.000000")

    assert tuple(row.event_label for row in built.rows) == (
        "event-block",
        "event-watch",
        "event-pass",
    )
    assert tuple(row.review_rank for row in built.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.diagnostic_status for row in built.rows) == (
        "block",
        "watch",
        "pass",
    )

    blocked, watched, passed = built.rows
    assert blocked.source_age_seconds == d("10800.000000")
    assert blocked.freshness_score == d("0.000000")
    assert blocked.evidence_quorum_score == d("0.250000")
    assert blocked.independent_quorum_score == d("0.500000")
    assert blocked.diagnostic_score == d("0.212500")
    assert blocked.reason_codes == (
        "event_source_freshness_block",
        "event_evidence_quorum_block",
        "event_independent_evidence_quorum_watch",
    )
    assert watched.diagnostic_score == d("0.587500")
    assert watched.reason_codes == (
        "event_source_freshness_watch",
        "event_independent_evidence_quorum_watch",
    )
    assert passed.diagnostic_score == d("0.950000")
    assert passed.reason_codes == ("event_source_freshness_quorum_pass",)

    assert built.reason_codes == (
        "event_source_freshness_watch",
        "event_source_freshness_block",
        "event_evidence_quorum_block",
        "event_independent_evidence_quorum_watch",
        "event_source_freshness_quorum_pass",
    )
    assert tuple(
        (item.reason_code, item.row_count, item.row_ratio)
        for item in built.reason_code_counts
    ) == (
        ("event_source_freshness_watch", d("1.000000"), d("0.333333")),
        ("event_source_freshness_block", d("1.000000"), d("0.333333")),
        ("event_evidence_quorum_block", d("1.000000"), d("0.333333")),
        (
            "event_independent_evidence_quorum_watch",
            d("2.000000"),
            d("0.666667"),
        ),
        ("event_source_freshness_quorum_pass", d("1.000000"), d("0.333333")),
    )


def test_payload_is_canonical_public_safe_and_private_identifiers_never_leak() -> None:
    module = api()
    first = report()
    second = report(tuple(reversed(sample_observations())))

    payload = module.research_strategy_event_source_freshness_quorum_report_payload(
        first,
    )
    reversed_payload = (
        module.research_strategy_event_source_freshness_quorum_report_payload(second)
    )

    assert payload == reversed_payload
    assert json.dumps(payload, allow_nan=False, sort_keys=True)
    assert payload["generated_at"] == "2026-07-10T12:00:00+00:00"
    assert payload["rows"][0]["review_rank"] == "1.000000"
    assert payload["rows"][0]["diagnostic_score"] == "0.212500"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(payload["derived_validation_digest"]) == 64
    assert module.research_strategy_event_source_freshness_quorum_report_digest(
        first,
    ) == first.derived_validation_digest
    assert module.validate_research_strategy_event_source_freshness_quorum_public_payload(
        payload,
    )
    assert (
        module.research_strategy_event_source_freshness_quorum_report_payload(payload)
        == payload
    )
    assert_json_scalars_only(payload)

    serialized = json.dumps(payload, sort_keys=True).lower()
    for private_value in (
        "secret://source/internal-001",
        "private-specialist-7788",
        "https://hidden.example/private/source?id=pass",
        "wallet-secret-market-source-001",
    ):
        assert private_value.lower() not in serialized
    for forbidden_term in (
        "private_source_identifier",
        "recommendation",
        "recommended_position",
        "position_size",
        "buy",
        "sell",
        "wallet",
        "order",
        "trade",
    ):
        assert forbidden_term not in serialized


@pytest.mark.parametrize(
    "mutate",
    (
        lambda payload: payload["rows"][0].update(
            {
                "diagnostic_status": "pass",
                "reason_codes": ["event_source_freshness_quorum_pass"],
            },
        ),
        lambda payload: payload["rows"][0].update(
            {"diagnostic_score": "0.999999"},
        ),
        lambda payload: payload["rows"][0].update(
            {"source_age_seconds": "1.000000"},
        ),
        lambda payload: payload["rows"][0].update(
            {"freshness_score": "0.999999"},
        ),
        lambda payload: payload["rows"][0].update(
            {"evidence_quorum_score": "0.999999"},
        ),
        lambda payload: payload["rows"][0].update(
            {"independent_quorum_score": "0.999999"},
        ),
        lambda payload: payload["rows"][0].update({"review_rank": "3.000000"}),
        lambda payload: payload.update({"status": "pass"}),
        lambda payload: payload.update({"event_source_count": "2.000000"}),
        lambda payload: payload.update({"pass_count": "0.000000"}),
        lambda payload: payload.update({"watch_count": "0.000000"}),
        lambda payload: payload.update({"block_count": "0.000000"}),
        lambda payload: payload.update({"stale_count": "0.000000"}),
        lambda payload: payload.update({"quorum_deficit_count": "0.000000"}),
        lambda payload: payload.update({"average_freshness_score": "0.999999"}),
        lambda payload: payload.update(
            {"average_evidence_quorum_score": "0.999999"},
        ),
        lambda payload: payload.update(
            {"average_independent_quorum_score": "0.999999"},
        ),
        lambda payload: payload.update({"average_diagnostic_score": "0.999999"}),
        lambda payload: payload.update({"minimum_diagnostic_score": "0.999999"}),
        lambda payload: payload.update(
            {"maximum_source_age_seconds": "1.000000"},
        ),
        lambda payload: payload["reason_code_counts"][0].update(
            {"row_count": "2.000000"},
        ),
        lambda payload: payload["reason_code_counts"][0].update(
            {"row_ratio": "0.999999"},
        ),
        lambda payload: payload.update(
            {"reason_codes": ["event_source_freshness_quorum_pass"]},
        ),
        lambda payload: payload.update(
            {"reason_code_counts": payload["reason_code_counts"][1:]},
        ),
        lambda payload: payload["config"].update(
            {"freshness_block_age_seconds": "9000.000000"},
        ),
    ),
    ids=(
        "row-status-and-reasons",
        "row-score",
        "row-source-age",
        "row-freshness-score",
        "row-evidence-quorum-score",
        "row-independent-quorum-score",
        "row-rank",
        "report-status",
        "event-source-count",
        "pass-count",
        "watch-count",
        "status-count",
        "stale-count",
        "quorum-deficit-count",
        "average-freshness-score",
        "average-evidence-quorum-score",
        "average-independent-quorum-score",
        "aggregate",
        "minimum-diagnostic-score",
        "maximum-source-age",
        "reason-count",
        "reason-ratio",
        "reason-codes",
        "reason-code-counts",
        "config-threshold",
    ),
)
def test_resigned_payload_rederives_every_diagnostic_surface(
    mutate: Callable[[dict[str, object]], None],
) -> None:
    module = api()
    payload = module.research_strategy_event_source_freshness_quorum_report_payload(
        report(),
    )
    mutate(payload)
    resign_payload(payload)

    assert not module.validate_research_strategy_event_source_freshness_quorum_public_payload(
        payload,
    )
    with pytest.raises(ValueError, match="must match|consistent|rank|derived"):
        module.research_strategy_event_source_freshness_quorum_report_payload(payload)


def test_strict_exact_schema_digest_and_numeric_string_validation() -> None:
    module = api()
    payload = module.research_strategy_event_source_freshness_quorum_report_payload(
        report(),
    )

    unknown = dict(payload)
    unknown["extra"] = "unexpected"
    assert not module.validate_research_strategy_event_source_freshness_quorum_public_payload(
        unknown,
    )

    missing = dict(payload)
    missing.pop("status")
    assert not module.validate_research_strategy_event_source_freshness_quorum_public_payload(
        missing,
    )

    row_unknown = dict(payload)
    row_unknown["rows"] = [dict(row) for row in payload["rows"]]
    row_unknown["rows"][0]["private_source_identifier"] = "secret"
    resign_payload(row_unknown)
    assert not module.validate_research_strategy_event_source_freshness_quorum_public_payload(
        row_unknown,
    )

    negative_zero = dict(payload)
    negative_zero["average_diagnostic_score"] = "-0.000000"
    negative_zero["derived_validation_digest"] = canonical_digest(
        REPORT_DIGEST_LABEL,
        negative_zero,
    )
    assert not module.validate_research_strategy_event_source_freshness_quorum_public_payload(
        negative_zero,
    )

    noncanonical = dict(payload)
    noncanonical["event_source_count"] = "3"
    noncanonical["derived_validation_digest"] = canonical_digest(
        REPORT_DIGEST_LABEL,
        noncanonical,
    )
    assert not module.validate_research_strategy_event_source_freshness_quorum_public_payload(
        noncanonical,
    )

    tampered = dict(payload)
    tampered["status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_event_source_freshness_quorum_report_payload(tampered)


@pytest.mark.parametrize(
    "target_name",
    ("report", "config", "row", "reason-count"),
)
def test_public_payload_rejects_noncanonical_mapping_field_order(
    target_name: str,
) -> None:
    module = api()
    payload = json.loads(json.dumps(report().payload))

    if target_name == "report":
        payload = {key: payload[key] for key in reversed(tuple(payload))}
    elif target_name == "config":
        config_payload = payload["config"]
        payload["config"] = {
            key: config_payload[key]
            for key in reversed(tuple(config_payload))
        }
    elif target_name == "row":
        row_payload = payload["rows"][0]
        payload["rows"][0] = {
            key: row_payload[key]
            for key in reversed(tuple(row_payload))
        }
    else:
        reason_count_payload = payload["reason_code_counts"][0]
        payload["reason_code_counts"][0] = {
            key: reason_count_payload[key]
            for key in reversed(tuple(reason_count_payload))
        }
    resign_payload(payload)

    assert not module.validate_research_strategy_event_source_freshness_quorum_public_payload(
        payload,
    )
    with pytest.raises(ValueError, match="schema|order"):
        module.research_strategy_event_source_freshness_quorum_report_payload(payload)


def test_builder_revalidates_mutated_observation_identifier_exact_type() -> None:
    value = observation("event-mutated-observation")
    object.__setattr__(
        value,
        "private_source_identifier",
        _StringSubclass(value.private_source_identifier),
    )

    with pytest.raises(ValueError, match="private_source_identifier must be exactly str"):
        report((value,))


def test_builder_revalidates_object_setattr_tampered_config_invariants() -> None:
    value = cfg()
    object.__setattr__(value, "freshness_block_age_seconds", d("900.000000"))

    with pytest.raises(ValueError, match="freshness_block_age_seconds"):
        report((observation("event-tampered-config"),), config=value)


def test_report_revalidates_nested_config_object_setattr_tampering() -> None:
    built = report()
    value = cfg()
    object.__setattr__(value, "quorum_pass_threshold", d("0.250000"))

    with pytest.raises(ValueError, match="quorum_pass_threshold"):
        replace(built, config=value, derived_validation_digest="")


@pytest.mark.parametrize(
    ("field_name", "replacement", "error_match"),
    (
        (
            "diagnostic_status",
            lambda row: _StringSubclass(row.diagnostic_status),
            "diagnostic_status",
        ),
        (
            "reason_codes",
            lambda row: tuple(_StringSubclass(code) for code in row.reason_codes),
            "reason_codes",
        ),
        (
            "derived_validation_digest",
            lambda row: _StringSubclass(row.derived_validation_digest),
            "derived_validation_digest",
        ),
    ),
)
def test_report_revalidates_nested_row_exact_types(
    field_name: str,
    replacement: Callable[[Any], object],
    error_match: str,
) -> None:
    built = report()
    row = built.rows[0]
    object.__setattr__(row, field_name, replacement(row))

    with pytest.raises(ValueError, match=error_match):
        replace(built, rows=built.rows)


def test_report_revalidates_nested_reason_count_exact_types() -> None:
    built = report()
    reason_count = built.reason_code_counts[0]
    object.__setattr__(
        reason_count,
        "reason_code",
        _StringSubclass(reason_count.reason_code),
    )

    with pytest.raises(ValueError, match="reason_code"):
        replace(built, reason_code_counts=built.reason_code_counts)


def test_direct_dataclasses_reject_noncanonical_reason_code_order() -> None:
    built = report()
    row = built.rows[0]

    with pytest.raises(ValueError, match="canonical order"):
        replace(row, reason_codes=tuple(reversed(row.reason_codes)))
    with pytest.raises(ValueError, match="canonical order"):
        replace(built, reason_codes=tuple(reversed(built.reason_codes)))


def test_dataclasses_are_frozen_decimal_only_and_reject_unsafe_values() -> None:
    module = api()
    built = report()
    public_classes = (
        module.ResearchStrategyEventSourceFreshnessQuorumConfig,
        module.ResearchStrategyEventSourceFreshnessQuorumObservation,
        module.ResearchStrategyEventSourceFreshnessQuorumRow,
        module.ResearchStrategyEventSourceFreshnessQuorumReasonCount,
        module.ResearchStrategyEventSourceFreshnessQuorumReport,
    )
    for public_class in public_classes:
        assert is_dataclass(public_class)
        assert public_class.__dataclass_params__.frozen is True

    for instance in (
        cfg(),
        sample_observations()[0],
        built,
        *built.rows,
        *built.reason_code_counts,
    ):
        for field in fields(instance):
            value = getattr(instance, field.name)
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert not isinstance(value, float)

    with pytest.raises(FrozenInstanceError):
        built.rows[0].diagnostic_status = "pass"  # type: ignore[misc]
    with pytest.raises(TypeError):

        class BadReport(module.ResearchStrategyEventSourceFreshnessQuorumReport):
            pass

    with pytest.raises(ValueError, match="evidence_count must be exactly Decimal"):
        observation("float-count", evidence_count=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_count must be exactly Decimal"):
        observation("subclass-count", evidence_count=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="event_label must be exactly str"):
        observation(_StringSubclass("subclass-label"))
    with pytest.raises(ValueError, match="diagnostic_status"):
        replace(
            built.rows[0],
            diagnostic_status=_StringSubclass(built.rows[0].diagnostic_status),
        )
    with pytest.raises(ValueError, match="paper_only"):
        cfg(paper_only=1)
    with pytest.raises(ValueError, match="finite"):
        observation("nan-count", evidence_count=d("NaN"))
    with pytest.raises(ValueError, match="finite"):
        observation("infinite-count", evidence_count=d("Infinity"))
    with pytest.raises(ValueError, match="signed zero"):
        observation("negative-zero", evidence_count=d("-0.000000"))
    with pytest.raises(ValueError, match="whole"):
        observation("fractional-count", evidence_count=d("1.500000"))
    with pytest.raises(ValueError, match="required_evidence_count"):
        observation(
            "over-count",
            evidence_count=d("5.000000"),
            required_evidence_count=d("4.000000"),
        )
    with pytest.raises(ValueError, match="freshness_block_age_seconds"):
        cfg(freshness_block_age_seconds=d("900.000000"))
    with pytest.raises(ValueError, match="weights must sum to one"):
        cfg(freshness_weight=d("0.300000"))
    with pytest.raises(ValueError, match="paper_only"):
        cfg(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(sample_observations()[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(built, readonly=False)
    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report(generated_at=_DatetimeSubclass(2026, 7, 10, 12, tzinfo=UTC))
    with pytest.raises(ValueError, match="timezone-aware"):
        observation("naive-time", observed_at=datetime(2026, 7, 10, 11, 0))
    with pytest.raises(ValueError, match="utcoffset"):
        observation(
            "none-offset",
            observed_at=datetime(2026, 7, 10, 11, 0, tzinfo=_NoneOffsetTz()),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(
            (
                observation(
                    "future",
                    observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )
    with pytest.raises(ValueError, match="unsafe"):
        observation(
            "unsafe-label",
            public_source_label="https://example.invalid/raw-source",
        )


def test_decimal_math_uses_fixed_context_and_checks_raw_bounds_before_quantizing() -> None:
    baseline = report().payload

    with localcontext() as hostile_context:
        hostile_context.prec = 6
        hostile_context.rounding = ROUND_DOWN
        hostile_context.traps[Inexact] = True
        assert report().payload == baseline

    with pytest.raises(ValueError, match="quorum_pass_threshold.*at most one"):
        cfg(quorum_pass_threshold=d("1.0000004"))
    with pytest.raises(ValueError, match="quorum_block_threshold.*nonnegative"):
        cfg(quorum_block_threshold=d("-0.0000004"))
    with pytest.raises(ValueError, match="freshness_watch_age_seconds.*positive"):
        cfg(freshness_watch_age_seconds=d("0.0000004"))
    with pytest.raises(ValueError, match="weights must sum to one"):
        cfg(
            freshness_weight=d("0.4000004"),
            evidence_quorum_weight=d("0.3499996"),
            independent_quorum_weight=d("0.2500004"),
        )


def test_complete_stable_sorting_is_independent_of_input_order() -> None:
    tied = (
        observation(
            "event-zeta",
            public_source_label="source-beta",
            private_source_identifier="private-zeta-beta",
        ),
        observation(
            "event-alpha",
            public_source_label="source-zeta",
            private_source_identifier="private-alpha-zeta",
        ),
        observation(
            "event-alpha",
            public_source_label="source-alpha",
            private_source_identifier="private-alpha-alpha",
        ),
    )

    expected = (
        ("event-alpha", "source-alpha"),
        ("event-alpha", "source-zeta"),
        ("event-zeta", "source-beta"),
    )
    assert tuple(
        (row.event_label, row.public_source_label)
        for row in report(tied).rows
    ) == expected
    assert tuple(
        (row.event_label, row.public_source_label)
        for values in permutations(tied)
        for row in report(values).rows
    ) == expected * 6


def test_empty_report_and_public_surface_remain_report_only() -> None:
    module = api()
    empty = report(())

    assert module.DIAGNOSTIC_STATUSES == ("pass", "watch", "block")
    assert empty.status == "pass"
    assert empty.event_source_count == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == ("event_source_freshness_quorum_pass",)
    assert empty.reason_code_counts == ()
    assert module.validate_research_strategy_event_source_freshness_quorum_public_payload(
        empty.payload,
    )

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
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "scrapling",
        "web3",
        "py_clob_client",
        "keyring",
    }
    assert imported_roots.isdisjoint(forbidden_imports)

    unsafe_public_terms = (
        "recommend",
        "position",
        "wallet",
        "order",
        "trade",
        "client",
        "network",
        "database",
        "persist",
    )
    for public_name in module.__all__:
        lowered_name = public_name.lower()
        assert not any(term in lowered_name for term in unsafe_public_terms)

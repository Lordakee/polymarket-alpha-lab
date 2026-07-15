from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal, Inexact, ROUND_DOWN, Rounded, localcontext
import hashlib
import inspect
import json
from types import ModuleType

import pytest

import polymarket_alpha_lab.research_source_scrapling_authority_memory_scorecard_report as api
from polymarket_alpha_lab.research_source_scrapling_authority_memory_scorecard_report import (
    ResearchSourceScraplingAuthorityMemoryConfig,
    ResearchSourceScraplingAuthorityMemoryEvidence,
    ResearchSourceScraplingAuthorityMemoryPublicPayloadItem,
    ResearchSourceScraplingAuthorityMemoryReport,
    ResearchSourceScraplingAuthorityMemoryRow,
    build_research_source_scrapling_authority_memory_scorecard_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def evidence(**overrides: object) -> ResearchSourceScraplingAuthorityMemoryEvidence:
    values = {
        "private_reference": "https://internal.invalid/raw-candidate-market-source?token=secret",
        "authority_family": "official",
        "memory_class": "resolution-history",
        "observed_at": NOW,
        "authority_score": d("0.900000"),
        "memory_score": d("0.850000"),
        "corroboration_score": d("0.800000"),
        "recency_score": d("0.750000"),
        "conflict_score": d("0.100000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return ResearchSourceScraplingAuthorityMemoryEvidence(**values)


def report(
    *rows: ResearchSourceScraplingAuthorityMemoryEvidence,
    config: ResearchSourceScraplingAuthorityMemoryConfig | None = None,
    public_payload: tuple[ResearchSourceScraplingAuthorityMemoryPublicPayloadItem, ...] = (),
) -> ResearchSourceScraplingAuthorityMemoryReport:
    return build_research_source_scrapling_authority_memory_scorecard_report(
        rows,
        generated_at=NOW,
        config=config,
        public_payload=public_payload,
    )


def test_builds_pass_watch_and_block_scorecard_report() -> None:
    built = report(
        evidence(private_reference="private-pass", authority_family="official"),
        evidence(
            private_reference="private-watch",
            authority_family="archive",
            authority_score=d("0.650000"),
            memory_score=d("0.600000"),
            corroboration_score=d("0.550000"),
            recency_score=d("0.500000"),
            conflict_score=d("0.200000"),
        ),
        evidence(
            private_reference="private-block",
            authority_family="rumor",
            authority_score=d("0.250000"),
            memory_score=d("0.300000"),
            corroboration_score=d("0.200000"),
            recency_score=d("0.400000"),
            conflict_score=d("0.800000"),
        ),
    )

    assert built.status == "block"
    assert built.row_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")
    assert built.rows[0].reason_codes == ("conflict_score_block", "authority_score_block")
    assert built.rows[1].reason_codes == ("authority_memory_score_watch",)
    assert built.rows[2].reason_codes == ("authority_memory_score_pass",)
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True


def test_payload_is_deterministic_json_ready_and_validated_by_sha256() -> None:
    public_item = ResearchSourceScraplingAuthorityMemoryPublicPayloadItem(
        key="run_label",
        value="scrapling-memory-v1",
    )
    first = report(
        evidence(private_reference="private-b"),
        evidence(private_reference="private-a", authority_family="archive"),
        public_payload=(public_item,),
    )
    second = report(
        evidence(private_reference="private-a", authority_family="archive"),
        evidence(private_reference="private-b"),
        public_payload=(public_item,),
    )

    payload = first.payload
    unsigned_payload = dict(payload)
    unsigned_payload.pop("validation_digest")
    expected_validation_digest = hashlib.sha256(
        json.dumps(
            unsigned_payload,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()

    assert payload == second.payload
    assert first.validation_digest == second.validation_digest
    assert payload["validation_digest"] == first.validation_digest
    assert first.validation_digest == expected_validation_digest
    assert len(first.validation_digest) == 64
    assert payload["row_count"] == "2.000000"
    assert payload["rows"][0]["composite_score"] == "0.720000"
    assert payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    json.dumps(payload, sort_keys=True)
    assert not _contains_decimal_object(payload)
    assert not _contains_non_decimal_number(first)

    with pytest.raises(ValueError, match="validation_digest"):
        replace(first, validation_digest="0" * 64)
    with pytest.raises(ValueError, match="validation_digest"):
        replace(
            first,
            public_payload=(
                ResearchSourceScraplingAuthorityMemoryPublicPayloadItem(
                    key="run_label",
                    value="scrapling-memory-v2",
                ),
            ),
        )


def test_decimal_calculations_are_isolated_from_ambient_context() -> None:
    inputs = {
        "private_reference": "private-decimal-context",
        "authority_score": d("0.333333"),
        "memory_score": d("0.666667"),
        "corroboration_score": d("0.555555"),
        "recency_score": d("0.444444"),
        "conflict_score": d("0.111111"),
    }
    baseline = report(evidence(**inputs))

    with localcontext() as context:
        context.prec = 2
        context.rounding = ROUND_DOWN
        context.traps[Inexact] = True
        context.traps[Rounded] = True
        isolated = report(evidence(**inputs))

    assert isolated.payload == baseline.payload


def test_row_sorting_has_a_stable_tie_break_for_equal_evidence_digests() -> None:
    first_evidence = evidence(
        private_reference="private-shared-reference",
        authority_family="archive",
        memory_class="historical-resolution",
        authority_score=d("0.910000"),
    )
    second_evidence = evidence(
        private_reference="private-shared-reference",
        authority_family="official",
        memory_class="resolution-history",
        authority_score=d("0.920000"),
    )

    first = report(first_evidence, second_evidence)
    second = report(second_evidence, first_evidence)

    assert first.payload == second.payload
    assert first.validation_digest == second.validation_digest


def test_public_payload_redacts_private_inputs_and_rejects_sensitive_terms() -> None:
    private_value = "postgres://private/raw-candidate-market-source-url-text-dsn-table-token"
    built = report(evidence(private_reference=private_value))

    payload_json = json.dumps(built.payload, sort_keys=True)
    expected_evidence_digest = hashlib.sha256(private_value.encode("utf-8")).hexdigest()
    assert private_value not in payload_json
    for leaked in ("raw-candidate", "market-source", "source-url", "dsn", "table", "token"):
        assert leaked not in payload_json.lower()
    assert built.rows[0].evidence_digest == expected_evidence_digest

    for key in ("url", "dsn", "table", "token", "wallet", "order"):
        with pytest.raises(ValueError, match="sensitive"):
            ResearchSourceScraplingAuthorityMemoryPublicPayloadItem(key=key, value="safe")
    for value in (
        "https://example.invalid/private",
        "postgres://example.invalid/private",
        "contains raw text payload",
        "wallet material",
        "order route",
        "trade identifier",
        "auth credential",
        "live execution route",
    ):
        with pytest.raises(ValueError, match="sensitive"):
            ResearchSourceScraplingAuthorityMemoryPublicPayloadItem(key="safe_key", value=value)

    for field_name in ("authority_family", "memory_class"):
        with pytest.raises(ValueError, match="sensitive"):
            evidence(**{field_name: "market-identifier"})


def test_public_payload_schema_validation_rejects_resigned_tampering() -> None:
    built = report(
        evidence(private_reference="private-schema"),
        public_payload=(
            ResearchSourceScraplingAuthorityMemoryPublicPayloadItem(
                key="run_label",
                value="scrapling-memory-v1",
            ),
        ),
    )
    payload = built.payload

    assert (
        api.validate_research_source_scrapling_authority_memory_scorecard_report_payload(
            payload,
        )
        is True
    )

    extra_report_field = {**payload, "diagnostic_note": "safe"}
    _resign_payload(extra_report_field)
    with pytest.raises(ValueError, match="canonical report payload schema"):
        api.validate_research_source_scrapling_authority_memory_scorecard_report_payload(
            extra_report_field,
        )

    extra_row_field = json.loads(json.dumps(payload))
    extra_row_field["rows"][0]["diagnostic_note"] = "safe"
    _resign_payload(extra_row_field)
    with pytest.raises(ValueError, match="canonical row payload schema"):
        api.validate_research_source_scrapling_authority_memory_scorecard_report_payload(
            extra_row_field,
        )

    noncanonical_decimal = json.loads(json.dumps(payload))
    noncanonical_decimal["row_count"] = "1"
    _resign_payload(noncanonical_decimal)
    with pytest.raises(ValueError, match="canonical Decimal string"):
        api.validate_research_source_scrapling_authority_memory_scorecard_report_payload(
            noncanonical_decimal,
        )

    missing_report_field = dict(payload)
    missing_report_field.pop("readonly")
    _resign_payload(missing_report_field)
    with pytest.raises(ValueError, match="canonical report payload schema"):
        api.validate_research_source_scrapling_authority_memory_scorecard_report_payload(
            missing_report_field,
        )

    extra_public_payload_field = json.loads(json.dumps(payload))
    extra_public_payload_field["public_payload"][0]["diagnostic_note"] = "safe"
    _resign_payload(extra_public_payload_field)
    with pytest.raises(ValueError, match="canonical public payload item payload schema"):
        api.validate_research_source_scrapling_authority_memory_scorecard_report_payload(
            extra_public_payload_field,
        )


@pytest.mark.parametrize(
    "mapping_path",
    (
        (),
        ("rows", 0),
        ("public_payload", 0),
    ),
)
def test_public_payload_schema_validation_rejects_resigned_noncanonical_key_order(
    mapping_path: tuple[object, ...],
) -> None:
    payload = json.loads(
        json.dumps(
            report(
                evidence(private_reference="private-key-order"),
                public_payload=(
                    ResearchSourceScraplingAuthorityMemoryPublicPayloadItem(
                        key="run_label",
                        value="scrapling-memory-v1",
                    ),
                ),
            ).payload,
        ),
    )
    target: dict[str, object] = payload
    for path_item in mapping_path:
        target = target[path_item]  # type: ignore[index, assignment]
    reordered = dict(reversed(tuple(target.items())))
    if not mapping_path:
        payload = reordered
    elif mapping_path == ("rows", 0):
        payload["rows"][0] = reordered  # type: ignore[index]
    else:
        payload["public_payload"][0] = reordered  # type: ignore[index]
    _resign_payload(payload)

    with pytest.raises(ValueError, match="canonical .* payload schema"):
        api.validate_research_source_scrapling_authority_memory_scorecard_report_payload(
            payload,
        )


def test_rejects_resigned_forgery_of_derived_row_score() -> None:
    payload = json.loads(
        json.dumps(report(evidence(private_reference="private-forged-score")).payload),
    )
    payload["rows"][0]["composite_score"] = "0.999999"
    payload["average_composite_score"] = "0.999999"
    _resign_payload(payload)

    with pytest.raises(ValueError, match="composite_score"):
        api.validate_research_source_scrapling_authority_memory_scorecard_report_payload(
            payload,
        )


def test_rejects_resigned_forgery_of_derived_row_status_and_reason_codes() -> None:
    payload = json.loads(
        json.dumps(report(evidence(private_reference="private-forged-status")).payload),
    )
    payload["rows"][0]["status"] = "watch"
    payload["rows"][0]["reason_codes"] = ["authority_memory_score_watch"]
    payload["status"] = "watch"
    payload["pass_count"] = "0.000000"
    payload["watch_count"] = "1.000000"
    payload["reason_codes"] = ["authority_memory_score_watch"]
    _resign_payload(payload)

    with pytest.raises(ValueError, match="reason_codes"):
        api.validate_research_source_scrapling_authority_memory_scorecard_report_payload(
            payload,
        )


@pytest.mark.parametrize(
    ("field_name", "forged_value", "message"),
    (
        ("row_count", "2.000000", "row_count"),
        ("pass_count", "0.000000", "pass_count"),
        ("watch_count", "1.000000", "watch_count"),
        ("block_count", "1.000000", "block_count"),
        ("average_composite_score", "0.700000", "average_composite_score"),
        ("status", "watch", "status"),
        ("reason_codes", ["authority_memory_score_watch"], "reason_codes"),
    ),
)
def test_rejects_resigned_forgery_of_derived_report_fields(
    field_name: str,
    forged_value: object,
    message: str,
) -> None:
    payload = json.loads(
        json.dumps(report(evidence(private_reference="private-forged-report")).payload),
    )
    payload[field_name] = forged_value
    _resign_payload(payload)

    with pytest.raises(ValueError, match=message):
        api.validate_research_source_scrapling_authority_memory_scorecard_report_payload(
            payload,
        )


def test_payload_export_revalidates_nested_state_and_unique_public_keys() -> None:
    public_item = ResearchSourceScraplingAuthorityMemoryPublicPayloadItem(
        key="run_label",
        value="scrapling-memory-v1",
    )
    built = report(
        evidence(private_reference="private-tamper"),
        public_payload=(public_item,),
    )

    object.__setattr__(built.public_payload[0], "value", "wallet token")
    with pytest.raises(ValueError, match="sensitive"):
        _ = built.payload

    object.__setattr__(built.rows[0], "conflict_score", d("1.000001"))
    with pytest.raises(ValueError, match="conflict_score"):
        _ = built.payload

    rebuilt = report(evidence(private_reference="private-report-tamper"))
    object.__setattr__(rebuilt, "pass_count", d("0.000000"))
    with pytest.raises(ValueError, match="pass_count"):
        _ = rebuilt.payload

    rebuilt = report(evidence(private_reference="private-reason-tamper"))
    object.__setattr__(rebuilt, "reason_codes", ("authority_memory_score_watch",))
    with pytest.raises(ValueError, match="reason_codes"):
        _ = rebuilt.payload

    prebuild_tampered_item = ResearchSourceScraplingAuthorityMemoryPublicPayloadItem(
        key="run_label",
        value="scrapling-memory-v1",
    )
    object.__setattr__(prebuild_tampered_item, "value", "wallet token")
    with pytest.raises(ValueError, match="sensitive"):
        report(
            evidence(private_reference="private-prebuild-tamper"),
            public_payload=(prebuild_tampered_item,),
        )

    prebuild_tampered_config = ResearchSourceScraplingAuthorityMemoryConfig()
    object.__setattr__(prebuild_tampered_config, "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        report(
            evidence(private_reference="private-tampered-config"),
            config=prebuild_tampered_config,
        )

    prebuild_tampered_evidence = evidence(private_reference="private-tampered-evidence")
    object.__setattr__(prebuild_tampered_evidence, "authority_score", 0.9)
    with pytest.raises(ValueError, match="authority_score"):
        report(prebuild_tampered_evidence)

    duplicate_items = (
        ResearchSourceScraplingAuthorityMemoryPublicPayloadItem(
            key="run_label",
            value="scrapling-memory-v1",
        ),
        ResearchSourceScraplingAuthorityMemoryPublicPayloadItem(
            key="run_label",
            value="scrapling-memory-v2",
        ),
    )
    with pytest.raises(ValueError, match="duplicate"):
        report(
            evidence(private_reference="private-duplicate"),
            public_payload=duplicate_items,
        )


def test_rejects_raw_out_of_bounds_decimals_before_quantization() -> None:
    with pytest.raises(ValueError, match="authority_score"):
        evidence(authority_score=d("1.0000004"))
    with pytest.raises(ValueError, match="conflict_score"):
        evidence(conflict_score=d("-0.0000004"))
    with pytest.raises(ValueError, match="min_pass_score"):
        ResearchSourceScraplingAuthorityMemoryConfig(
            min_pass_score=d("1.0000004"),
        )

    built = report(evidence(private_reference="private-raw-bounds"))
    with pytest.raises(ValueError, match="composite_score"):
        replace(built.rows[0], composite_score=d("1.0000004"))
    with pytest.raises(ValueError, match="whole"):
        replace(built, row_count=d("0.9999996"))


def test_rejects_signed_zero_in_models_and_public_payloads() -> None:
    with pytest.raises(ValueError, match="signed zero"):
        evidence(conflict_score=d("-0.000000"))
    with pytest.raises(ValueError, match="signed zero"):
        ResearchSourceScraplingAuthorityMemoryConfig(min_pass_score=d("-0"))

    empty_report = report()
    with pytest.raises(ValueError, match="signed zero"):
        replace(empty_report, average_composite_score=d("-0.000000"))
    with pytest.raises(ValueError, match="signed zero"):
        replace(empty_report, row_count=d("-0.000000"))

    payload = json.loads(
        json.dumps(report(evidence(private_reference="private-signed-zero")).payload),
    )
    payload["rows"][0]["conflict_score"] = "-0.000000"
    _resign_payload(payload)
    with pytest.raises(ValueError, match="canonical Decimal string"):
        api.validate_research_source_scrapling_authority_memory_scorecard_report_payload(
            payload,
        )


@pytest.mark.parametrize(
    "nonfinite",
    (
        d("NaN"),
        d("sNaN"),
        d("Infinity"),
        d("-Infinity"),
    ),
)
def test_rejects_nonfinite_decimals_in_models_and_public_payloads(
    nonfinite: Decimal,
) -> None:
    with pytest.raises(ValueError, match="authority_score must be finite"):
        evidence(authority_score=nonfinite)
    with pytest.raises(ValueError, match="min_pass_score must be finite"):
        ResearchSourceScraplingAuthorityMemoryConfig(min_pass_score=nonfinite)

    payload = json.loads(
        json.dumps(report(evidence(private_reference="private-nonfinite")).payload),
    )
    payload["rows"][0]["authority_score"] = str(nonfinite)
    _resign_payload(payload)
    with pytest.raises(ValueError, match="canonical Decimal string"):
        api.validate_research_source_scrapling_authority_memory_scorecard_report_payload(
            payload,
        )


def test_frozen_dataclasses_decimal_only_flags_and_statuses_are_enforced() -> None:
    built = report(evidence())

    for value in (
        ResearchSourceScraplingAuthorityMemoryConfig(),
        evidence(),
        ResearchSourceScraplingAuthorityMemoryPublicPayloadItem("safe_key", "safe-value"),
        built.rows[0],
        built,
    ):
        with pytest.raises(FrozenInstanceError):
            value.readonly = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="authority_score"):
        evidence(authority_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="memory_score"):
        evidence(memory_score=_DecimalSubclass("0.850000"))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_pass_score"):
        ResearchSourceScraplingAuthorityMemoryConfig(min_pass_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        evidence(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        ResearchSourceScraplingAuthorityMemoryConfig(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(built, readonly=False)
    with pytest.raises(ValueError, match="status"):
        replace(built.rows[0], status="review")

    for item in (built, *built.rows):
        assert item.status in {"pass", "watch", "block"}


def test_public_types_have_exact_frozen_dataclass_schemas() -> None:
    expected_fields = {
        ResearchSourceScraplingAuthorityMemoryConfig: (
            "config_version",
            "min_pass_score",
            "max_block_conflict_score",
            "min_block_authority_score",
            "authority_weight",
            "memory_weight",
            "corroboration_weight",
            "recency_weight",
            "conflict_penalty_weight",
            "paper_only",
            "report_only",
            "readonly",
        ),
        ResearchSourceScraplingAuthorityMemoryEvidence: (
            "private_reference",
            "authority_family",
            "memory_class",
            "observed_at",
            "authority_score",
            "memory_score",
            "corroboration_score",
            "recency_score",
            "conflict_score",
            "paper_only",
            "report_only",
            "readonly",
        ),
        ResearchSourceScraplingAuthorityMemoryPublicPayloadItem: (
            "key",
            "value",
            "paper_only",
            "report_only",
            "readonly",
        ),
        ResearchSourceScraplingAuthorityMemoryRow: (
            "evidence_digest",
            "authority_family",
            "memory_class",
            "observed_at",
            "authority_score",
            "memory_score",
            "corroboration_score",
            "recency_score",
            "conflict_score",
            "composite_score",
            "status",
            "reason_codes",
            "paper_only",
            "report_only",
            "readonly",
        ),
        ResearchSourceScraplingAuthorityMemoryReport: (
            "generated_at",
            "config_version",
            "status",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "average_composite_score",
            "rows",
            "reason_codes",
            "public_payload",
            "validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        ),
    }
    for cls, expected in expected_fields.items():
        assert tuple(field.name for field in fields(cls)) == expected
        assert cls.__dataclass_params__.frozen is True
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Forged{cls.__name__}", (cls,), {})

    assert api.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_SCRAPLING_AUTHORITY_MEMORY_CONFIG_VERSION",
        "ResearchSourceScraplingAuthorityMemoryConfig",
        "ResearchSourceScraplingAuthorityMemoryEvidence",
        "ResearchSourceScraplingAuthorityMemoryPublicPayloadItem",
        "ResearchSourceScraplingAuthorityMemoryReport",
        "ResearchSourceScraplingAuthorityMemoryRow",
        "build_research_source_scrapling_authority_memory_scorecard_report",
        "validate_research_source_scrapling_authority_memory_scorecard_report_payload",
    )


def test_module_surface_has_no_live_storage_execution_or_decision_controls() -> None:
    forbidden_public_names = (
        "db",
        "network",
        "wallet",
        "order",
        "live",
        "trading",
        "sizing",
        "recommendation",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in forbidden_public_names)

    for cls in (
        ResearchSourceScraplingAuthorityMemoryConfig,
        ResearchSourceScraplingAuthorityMemoryEvidence,
        ResearchSourceScraplingAuthorityMemoryPublicPayloadItem,
        ResearchSourceScraplingAuthorityMemoryRow,
        ResearchSourceScraplingAuthorityMemoryReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in forbidden_public_names)

    for forbidden_name in (
        "agent_reach",
        "scrapling",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
    ):
        assert not hasattr(api, forbidden_name)

    forbidden_modules = {
        "agent_reach",
        "ccxt",
        "httpx",
        "pathlib",
        "psycopg",
        "requests",
        "scrapling",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "urllib",
        "web3",
    }
    imported_modules = {
        value.__name__.split(".", maxsplit=1)[0]
        for value in vars(api).values()
        if isinstance(value, ModuleType)
    }
    assert imported_modules.isdisjoint(forbidden_modules)

    forbidden_call_names = {
        "connect",
        "cursor",
        "execute",
        "open",
        "read_bytes",
        "read_text",
        "recv",
        "request",
        "send",
        "write_bytes",
        "write_text",
    }
    for value in vars(api).values():
        if inspect.isfunction(value) and value.__module__ == api.__name__:
            assert set(value.__code__.co_names).isdisjoint(forbidden_call_names)


def _contains_decimal_object(value: object) -> bool:
    if isinstance(value, Decimal):
        return True
    if isinstance(value, dict):
        return any(_contains_decimal_object(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_decimal_object(item) for item in value)
    return False


def _contains_non_decimal_number(value: object) -> bool:
    if isinstance(value, Decimal):
        return False
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return False
    if type(value) is int or isinstance(value, float):
        return True
    if isinstance(value, tuple):
        return any(_contains_non_decimal_number(item) for item in value)
    if hasattr(value, "__dataclass_fields__"):
        return any(
            _contains_non_decimal_number(getattr(value, field.name))
            for field in fields(value)
        )
    return False


def _resign_payload(payload: dict[str, object]) -> None:
    unsigned = dict(payload)
    unsigned.pop("validation_digest", None)
    canonical = json.dumps(
        unsigned,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    payload["validation_digest"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

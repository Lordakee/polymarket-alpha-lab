from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 11, 45, tzinfo=UTC)
EVIDENCE_OBSERVED_AT = datetime(2026, 7, 8, 8, 0, tzinfo=UTC)
MEMORY_REFRESHED_AT = datetime(2026, 7, 8, 6, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_team_specialist_evidence_memory_decay_report.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_specialist_evidence_memory_decay_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def config(**overrides: object):
    return api().ResearchTeamSpecialistEvidenceMemoryDecayConfig(**overrides)


def memory_signal(
    domain_label: str = "politics",
    *,
    specialist_label: str = "team_politics",
    memory_bucket_label: str = "policy_resolution",
    observed_at: datetime = OBSERVED_AT,
    evidence_observed_at: datetime = EVIDENCE_OBSERVED_AT,
    memory_refreshed_at: datetime = MEMORY_REFRESHED_AT,
    evidence_confidence_score: Decimal = d("0.900000"),
    contradiction_score: Decimal = d("0.050000"),
    corroboration_score: Decimal = d("0.850000"),
    memory_reuse_count: Decimal = d("2.000000"),
    **overrides: object,
):
    values = {
        "domain_label": domain_label,
        "specialist_label": specialist_label,
        "memory_bucket_label": memory_bucket_label,
        "observed_at": observed_at,
        "evidence_observed_at": evidence_observed_at,
        "memory_refreshed_at": memory_refreshed_at,
        "evidence_confidence_score": evidence_confidence_score,
        "contradiction_score": contradiction_score,
        "corroboration_score": corroboration_score,
        "memory_reuse_count": memory_reuse_count,
    }
    values.update(overrides)
    return api().ResearchTeamSpecialistEvidenceMemoryDecayInput(**values)


def build_report(*items, cfg=None, generated_at: datetime = GENERATED_AT):
    return api().build_research_team_specialist_evidence_memory_decay_report(
        items,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def test_memory_decay_rollup_is_deterministic_and_validates_digest() -> None:
    items = (
        memory_signal(
            "politics",
            specialist_label="team_politics",
            memory_bucket_label="policy_resolution",
        ),
        memory_signal(
            "crypto",
            specialist_label="team_crypto",
            memory_bucket_label="protocol_updates",
            evidence_observed_at=GENERATED_AT - timedelta(hours=24),
            memory_refreshed_at=GENERATED_AT - timedelta(hours=36),
            evidence_confidence_score=d("0.650000"),
            contradiction_score=d("0.150000"),
            corroboration_score=d("0.550000"),
            memory_reuse_count=d("5.000000"),
        ),
        memory_signal(
            "weather",
            specialist_label="team_weather",
            memory_bucket_label="storm_resolution",
            evidence_observed_at=GENERATED_AT - timedelta(hours=72),
            memory_refreshed_at=GENERATED_AT - timedelta(hours=96),
            evidence_confidence_score=d("0.400000"),
            contradiction_score=d("0.300000"),
            corroboration_score=d("0.250000"),
            memory_reuse_count=d("10.000000"),
        ),
    )

    report = build_report(
        *items,
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )
    reversed_report = build_report(*reversed(items))

    assert api().EVIDENCE_MEMORY_DECAY_STATUSES == ("pass", "watch", "block")
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "research-team-specialist-evidence-memory-decay-report-v0"
    )
    assert report.status == "block"
    assert report.paper_queue_action == "paper_specialist_evidence_memory_decay_block"
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.stale_evidence_count == d("2.000000")
    assert report.stale_memory_count == d("2.000000")
    assert report.low_confidence_count == d("2.000000")
    assert report.contradiction_count == d("2.000000")
    assert report.weak_corroboration_count == d("2.000000")
    assert report.overused_memory_count == d("2.000000")
    assert report.max_evidence_age_hours == d("72.000000")
    assert report.max_memory_age_hours == d("96.000000")
    assert report.max_decay_pressure_score == d("1.000000")
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)

    assert tuple(row.domain_label for row in report.rows) == (
        "crypto",
        "politics",
        "weather",
    )
    by_domain = {row.domain_label: row for row in report.rows}
    assert by_domain["politics"].decay_status == "pass"
    assert by_domain["politics"].reason_codes == (
        "specialist_evidence_memory_decay_clear",
    )
    assert by_domain["crypto"].decay_status == "watch"
    assert by_domain["crypto"].evidence_age_hours == d("24.000000")
    assert by_domain["crypto"].memory_age_hours == d("36.000000")
    assert by_domain["crypto"].reason_codes == (
        "specialist_evidence_memory_evidence_stale_watch",
        "specialist_evidence_memory_memory_stale_watch",
        "specialist_evidence_memory_confidence_watch",
        "specialist_evidence_memory_contradiction_watch",
        "specialist_evidence_memory_corroboration_watch",
        "specialist_evidence_memory_reuse_watch",
    )
    assert by_domain["weather"].decay_status == "block"
    assert by_domain["weather"].reason_codes == (
        "specialist_evidence_memory_evidence_stale_block",
        "specialist_evidence_memory_memory_stale_block",
        "specialist_evidence_memory_confidence_block",
        "specialist_evidence_memory_contradiction_block",
        "specialist_evidence_memory_corroboration_block",
        "specialist_evidence_memory_reuse_block",
    )
    assert report.reason_codes == (
        "specialist_evidence_memory_decay_report_block",
        "specialist_evidence_memory_evidence_stale_block",
        "specialist_evidence_memory_memory_stale_block",
        "specialist_evidence_memory_confidence_block",
        "specialist_evidence_memory_contradiction_block",
        "specialist_evidence_memory_corroboration_block",
        "specialist_evidence_memory_reuse_block",
        "specialist_evidence_memory_evidence_stale_watch",
        "specialist_evidence_memory_memory_stale_watch",
        "specialist_evidence_memory_confidence_watch",
        "specialist_evidence_memory_contradiction_watch",
        "specialist_evidence_memory_corroboration_watch",
        "specialist_evidence_memory_reuse_watch",
    )

    payload = api().research_team_specialist_evidence_memory_decay_report_payload(report)
    reversed_payload = api().research_team_specialist_evidence_memory_decay_report_payload(
        reversed_report,
    )
    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert api().research_team_specialist_evidence_memory_decay_report_digest(report) == (
        payload["derived_validation_digest"]
    )
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["row_count"] == "3.000000"
    assert payload["rows"][0]["domain_label"] == "crypto"
    assert _float_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_empty_memory_decay_report_passes_with_report_reason_only() -> None:
    report = build_report()

    assert report.status == "pass"
    assert report.paper_queue_action == "paper_specialist_evidence_memory_decay_monitor"
    assert report.input_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.max_evidence_age_hours == d("0.000000")
    assert report.max_memory_age_hours == d("0.000000")
    assert report.max_decay_pressure_score == d("0.000000")
    assert report.reason_codes == ("specialist_evidence_memory_decay_report_pass",)
    assert report.reason_code_counts == ()
    assert report.rows == ()


def test_memory_decay_report_payload_preserves_custom_threshold_config() -> None:
    module = api()
    cfg = config(
        min_pass_evidence_confidence_score=d("0.950000"),
        min_watch_evidence_confidence_score=d("0.900000"),
    )
    report = build_report(
        memory_signal(evidence_confidence_score=d("0.920000")),
        cfg=cfg,
    )

    assert report.status == "watch"
    assert report.rows[0].reason_codes == (
        "specialist_evidence_memory_confidence_watch",
    )

    payload = module.research_team_specialist_evidence_memory_decay_report_payload(report)
    assert payload["min_pass_evidence_confidence_score"] == "0.950000"
    assert payload["min_watch_evidence_confidence_score"] == "0.900000"
    assert (
        module.research_team_specialist_evidence_memory_decay_report_payload(payload)
        == payload
    )


def test_memory_decay_is_report_only_public_safe_and_decimal_strict() -> None:
    module = api()
    cfg = config()
    signal = memory_signal("basketball", specialist_label="team_basketball")
    report = build_report(signal, cfg=cfg)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_SPECIALIST_EVIDENCE_MEMORY_DECAY_REPORT_CONFIG_VERSION",
        "EVIDENCE_MEMORY_DECAY_STATUSES",
        "ResearchTeamSpecialistEvidenceMemoryDecayConfig",
        "ResearchTeamSpecialistEvidenceMemoryDecayInput",
        "ResearchTeamSpecialistEvidenceMemoryDecayReasonCodeCount",
        "ResearchTeamSpecialistEvidenceMemoryDecayReport",
        "ResearchTeamSpecialistEvidenceMemoryDecayRow",
        "build_research_team_specialist_evidence_memory_decay_report",
        "research_team_specialist_evidence_memory_decay_report_digest",
        "research_team_specialist_evidence_memory_decay_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        report.rows[0].decay_status = "watch"  # type: ignore[misc]

    for value in (cfg, signal, report, *report.rows, *report.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if field.name.endswith(("_count", "_score", "_ratio", "_hours", "_seconds")):
                assert type(item) is Decimal

    with pytest.raises(ValueError, match="evidence_confidence_score must be a Decimal"):
        memory_signal(evidence_confidence_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="memory_reuse_count must be a Decimal"):
        memory_signal(memory_reuse_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="corroboration_score must be a Decimal"):
        memory_signal(corroboration_score=_DecimalSubclass("0.850000"))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        memory_signal(observed_at=datetime(2026, 7, 8, 11, 45))
    with pytest.raises(ValueError, match="evidence_observed_at must be a datetime"):
        memory_signal(
            evidence_observed_at=_DateTimeSubclass(2026, 7, 8, 10, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="future"):
        build_report(memory_signal(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="future"):
        build_report(
            memory_signal(evidence_observed_at=GENERATED_AT + timedelta(seconds=1)),
        )
    with pytest.raises(ValueError, match="domain_label"):
        memory_signal("Market")
    with pytest.raises(ValueError, match="specialist_label"):
        memory_signal(specialist_label="market_slug")
    with pytest.raises(ValueError, match="unique"):
        build_report(
            memory_signal("politics", specialist_label="team_politics"),
            memory_signal("politics", specialist_label="team_politics"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        memory_signal(paper_only=False)
    with pytest.raises(ValueError, match="max_watch_memory_age_hours"):
        config(
            max_pass_memory_age_hours=d("96.000000"),
            max_watch_memory_age_hours=d("72.000000"),
        )
    with pytest.raises(ValueError, match="min_watch_corroboration_score"):
        config(
            min_pass_corroboration_score=d("0.300000"),
            min_watch_corroboration_score=d("0.500000"),
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, pass_count=d("7.000000"))

    negative_zero_signal = memory_signal(contradiction_score=d("-0.000000"))
    assert str(negative_zero_signal.contradiction_score) == "0.000000"


def test_public_payload_rejects_raw_identifiers_tampering_and_unsafe_surfaces() -> None:
    module = api()
    report = build_report(memory_signal("politics", specialist_label="team_politics"))
    payload = module.research_team_specialist_evidence_memory_decay_report_payload(report)
    payload_text = repr(payload).lower()

    forbidden = (
        "candidate",
        "condition_id",
        "market",
        "slug",
        "question",
        "https://",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "token_id",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommendation",
        "sizing",
        "live",
    )
    for token_value in forbidden:
        assert token_value not in payload_text

    tampered = dict(payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_specialist_evidence_memory_decay_report_payload(tampered)

    for unsafe_key, unsafe_value in (
        ("candidate_id", "opaque"),
        ("condition_id", "0xabc"),
        ("market_slug", "will-fed-cut-rates"),
        ("question", "Will this resolve yes?"),
        ("source_url", "https://example.test/item"),
        ("dsn", "postgres://example"),
        ("token_id", "123"),
        ("wallet", "0xabc"),
        ("order_ticket", "abc"),
        ("sizing", "100"),
        ("recommendation", "buy"),
    ):
        leaked = dict(payload)
        leaked[unsafe_key] = unsafe_value
        leaked["derived_validation_digest"] = canonical_digest(leaked)
        with pytest.raises(ValueError, match="unsafe"):
            module.research_team_specialist_evidence_memory_decay_report_payload(leaked)

    numeric = dict(payload)
    numeric["row_count"] = 1
    numeric["derived_validation_digest"] = canonical_digest(numeric)
    with pytest.raises(ValueError, match="numeric"):
        module.research_team_specialist_evidence_memory_decay_report_payload(numeric)

    downgraded = dict(payload)
    downgraded["readonly"] = False
    downgraded["derived_validation_digest"] = canonical_digest(downgraded)
    with pytest.raises(ValueError, match="readonly"):
        module.research_team_specialist_evidence_memory_decay_report_payload(downgraded)

    object.__setattr__(report.rows[0], "memory_reuse_count", d("99.000000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_specialist_evidence_memory_decay_report_payload(report)


def test_resigned_public_payload_revalidates_schema_and_report_invariants() -> None:
    module = api()
    report = build_report(memory_signal("politics", specialist_label="team_politics"))
    payload = module.research_team_specialist_evidence_memory_decay_report_payload(report)

    def clone_payload() -> dict[str, Any]:
        return json.loads(json.dumps(payload))

    def resign(value: dict[str, Any]) -> dict[str, Any]:
        value["derived_validation_digest"] = canonical_digest(value)
        return value

    extra_field = clone_payload()
    extra_field["extra_field"] = "ok"
    with pytest.raises(ValueError, match="canonical report payload schema"):
        module.research_team_specialist_evidence_memory_decay_report_payload(
            resign(extra_field),
        )

    missing_field = clone_payload()
    missing_field.pop("status")
    with pytest.raises(ValueError, match="canonical report payload schema"):
        module.research_team_specialist_evidence_memory_decay_report_payload(
            resign(missing_field),
        )

    unsupported_status = clone_payload()
    unsupported_status["status"] = "hold"
    with pytest.raises(ValueError, match="status must be one of pass, watch, block"):
        module.research_team_specialist_evidence_memory_decay_report_payload(
            resign(unsupported_status),
        )

    decimal_typed_numeric = clone_payload()
    decimal_typed_numeric["row_count"] = d("1.000000")
    with pytest.raises(ValueError, match="numeric"):
        module.research_team_specialist_evidence_memory_decay_report_payload(
            decimal_typed_numeric,
        )

    datetime_typed_value = clone_payload()
    datetime_typed_value["generated_at"] = GENERATED_AT
    with pytest.raises(ValueError, match="JSON"):
        module.research_team_specialist_evidence_memory_decay_report_payload(
            datetime_typed_value,
        )

    tuple_typed_array = clone_payload()
    tuple_typed_array["reason_codes"] = tuple(tuple_typed_array["reason_codes"])
    with pytest.raises(ValueError, match="JSON"):
        module.research_team_specialist_evidence_memory_decay_report_payload(
            tuple_typed_array,
        )

    invalid_decimal_string = clone_payload()
    invalid_decimal_string["row_count"] = "not-a-decimal"
    with pytest.raises(ValueError, match="row_count must be a Decimal string"):
        module.research_team_specialist_evidence_memory_decay_report_payload(
            resign(invalid_decimal_string),
        )

    for field_name, invalid_value in (
        ("watch_count", "-0.000000"),
        ("row_count", "1"),
        ("row_count", "1.0000000"),
        ("max_evidence_age_hours", "0E-6"),
    ):
        noncanonical_decimal = clone_payload()
        noncanonical_decimal[field_name] = invalid_value
        with pytest.raises(
            ValueError,
            match=f"{field_name} must be a canonical Decimal string",
        ):
            module.research_team_specialist_evidence_memory_decay_report_payload(
                resign(noncanonical_decimal),
            )

    inconsistent_row_metric = clone_payload()
    inconsistent_row_metric["rows"][0]["evidence_confidence_score"] = "0.100000"
    with pytest.raises(ValueError, match="reason_codes must match row metrics"):
        module.research_team_specialist_evidence_memory_decay_report_payload(
            resign(inconsistent_row_metric),
        )

    inconsistent_row_count = clone_payload()
    inconsistent_row_count["row_count"] = "7.000000"
    with pytest.raises(ValueError, match="row_count must match rows"):
        module.research_team_specialist_evidence_memory_decay_report_payload(
            resign(inconsistent_row_count),
        )

    inconsistent_input_count = clone_payload()
    inconsistent_input_count["input_count"] = "7.000000"
    with pytest.raises(ValueError, match="input_count must match rows"):
        module.research_team_specialist_evidence_memory_decay_report_payload(
            resign(inconsistent_input_count),
        )

    nested_extra_field = clone_payload()
    nested_extra_field["rows"][0]["extra_field"] = "ok"
    with pytest.raises(ValueError, match="canonical row payload schema"):
        module.research_team_specialist_evidence_memory_decay_report_payload(
            resign(nested_extra_field),
        )

    nested_unsupported_status = clone_payload()
    nested_unsupported_status["rows"][0]["decay_status"] = "hold"
    with pytest.raises(ValueError, match="decay_status must be one of pass, watch, block"):
        module.research_team_specialist_evidence_memory_decay_report_payload(
            resign(nested_unsupported_status),
        )

    nested_flag_downgrade = clone_payload()
    nested_flag_downgrade["rows"][0]["paper_only"] = False
    with pytest.raises(ValueError, match="paper_only"):
        module.research_team_specialist_evidence_memory_decay_report_payload(
            resign(nested_flag_downgrade),
        )

    inconsistent_reason_count = clone_payload()
    inconsistent_reason_count["reason_code_counts"][0]["count"] = "2.000000"
    with pytest.raises(ValueError, match="reason_code_counts must match rows"):
        module.research_team_specialist_evidence_memory_decay_report_payload(
            resign(inconsistent_reason_count),
        )

    nested_unsafe_key = clone_payload()
    nested_unsafe_key["rows"][0]["source_text"] = "opaque"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_team_specialist_evidence_memory_decay_report_payload(
            resign(nested_unsafe_key),
        )


def test_resigned_public_payload_rejects_decay_pressure_status_mismatches() -> None:
    module = api()

    pass_payload = module.research_team_specialist_evidence_memory_decay_report_payload(
        build_report(memory_signal("politics", specialist_label="team_politics")),
    )
    pass_payload["rows"][0]["decay_pressure_score"] = "0.500000"
    pass_payload["max_decay_pressure_score"] = "0.500000"
    pass_payload["derived_validation_digest"] = canonical_digest(pass_payload)
    with pytest.raises(ValueError, match="decay_pressure_score must match decay_status"):
        module.research_team_specialist_evidence_memory_decay_report_payload(
            pass_payload,
        )

    block_payload = module.research_team_specialist_evidence_memory_decay_report_payload(
        build_report(
            memory_signal(
                "weather",
                specialist_label="team_weather",
                evidence_observed_at=GENERATED_AT - timedelta(hours=72),
            ),
        ),
    )
    block_payload["rows"][0]["decay_pressure_score"] = "0.500000"
    block_payload["max_decay_pressure_score"] = "0.500000"
    block_payload["derived_validation_digest"] = canonical_digest(block_payload)
    with pytest.raises(ValueError, match="decay_pressure_score must match decay_status"):
        module.research_team_specialist_evidence_memory_decay_report_payload(
            block_payload,
        )


@pytest.mark.parametrize(
    ("field_name", "unsafe_value"),
    (
        ("domain_label", "0x" + ("a" * 64)),
        ("specialist_label", "123e4567-e89b-12d3-a456-426614174000"),
        ("memory_bucket_label", "1234567890123456789012345678901234567890"),
        ("domain_label", "auth_context"),
        ("specialist_label", "execution_route"),
    ),
)
def test_resigned_public_payload_rejects_unsafe_public_label_values(
    field_name: str,
    unsafe_value: str,
) -> None:
    module = api()
    payload = module.research_team_specialist_evidence_memory_decay_report_payload(
        build_report(memory_signal("politics", specialist_label="team_politics")),
    )
    payload["rows"][0][field_name] = unsafe_value
    payload["derived_validation_digest"] = canonical_digest(payload)

    with pytest.raises(ValueError, match="unsafe public identifier text"):
        module.research_team_specialist_evidence_memory_decay_report_payload(payload)


def test_module_is_report_only_without_external_write_or_execution_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_import_roots = {
        "http",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
        "web3",
    }
    forbidden_call_names = {
        "connect",
        "execute",
        "open",
        "request",
        "send",
        "urlopen",
        "write",
        "write_text",
        "write_bytes",
        "float",
        "__import__",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float


def _float_paths(value: object, path: str = "") -> tuple[str, ...]:
    if type(value) is float:
        return (path or "<root>",)
    if isinstance(value, dict):
        return tuple(
            found
            for key, item in value.items()
            for found in _float_paths(item, f"{path}.{key}" if path else str(key))
        )
    if isinstance(value, list):
        return tuple(
            found
            for index, item in enumerate(value)
            for found in _float_paths(item, f"{path}[{index}]")
        )
    return ()

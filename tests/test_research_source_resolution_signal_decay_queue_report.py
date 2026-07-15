from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_source_resolution_signal_decay_queue_report.py",
)
FORBIDDEN_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "http://",
    "https://",
    "source_url",
    "source_text",
    "postgres://",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "sizing",
    "recommend",
    "execution",
    "execute",
    "live",
    "authorization",
    "auth_token",
    "password",
    "private_key",
    "session",
    "cookie",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_source_resolution_signal_decay_queue_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def payload_copy(payload: dict[str, Any]) -> dict[str, Any]:
    copied = json.loads(json.dumps(payload))
    assert isinstance(copied, dict)
    return copied


def resign(payload: dict[str, Any]) -> dict[str, Any]:
    payload["derived_validation_digest"] = canonical_digest(payload)
    return payload


def resign_report_object(report: object) -> None:
    values = asdict(report)
    values.pop("derived_validation_digest")
    object.__setattr__(
        report,
        "derived_validation_digest",
        api()._report_digest_from_values(values),
    )


def observation(
    scope_label: str = "resolution_alpha",
    *,
    authority_tier: str = "official",
    latest_verified_at: datetime = GENERATED_AT,
    contradiction_pressure: Decimal = d("0.050000"),
    corroboration_depth: Decimal = d("4"),
    extraction_confidence: Decimal = d("0.950000"),
    deadline_at: datetime = GENERATED_AT + timedelta(hours=96),
    **overrides: object,
):
    values = {
        "scope_label": scope_label,
        "authority_tier": authority_tier,
        "latest_verified_at": latest_verified_at,
        "contradiction_pressure": contradiction_pressure,
        "corroboration_depth": corroboration_depth,
        "extraction_confidence": extraction_confidence,
        "deadline_at": deadline_at,
    }
    values.update(overrides)
    return api().ResearchSourceResolutionSignalDecayObservation(**values)


def build_report(*items, cfg=None, generated_at: datetime = GENERATED_AT):
    return api().build_research_source_resolution_signal_decay_queue_report(
        items,
        config=api().ResearchSourceResolutionSignalDecayQueueConfig() if cfg is None else cfg,
        generated_at=generated_at,
    )


def test_signal_decay_queue_scores_ranks_and_digest_validates() -> None:
    passing = observation("resolution_pass")
    watching = observation(
        "resolution_watch",
        authority_tier="primary",
        latest_verified_at=GENERATED_AT - timedelta(hours=36),
        contradiction_pressure=d("0.300000"),
        corroboration_depth=d("2"),
        extraction_confidence=d("0.650000"),
        deadline_at=GENERATED_AT + timedelta(hours=24),
    )
    blocking = observation(
        "resolution_block",
        authority_tier="tertiary",
        latest_verified_at=GENERATED_AT - timedelta(hours=72),
        contradiction_pressure=d("0.900000"),
        corroboration_depth=d("0"),
        extraction_confidence=d("0.200000"),
        deadline_at=GENERATED_AT + timedelta(hours=6),
    )

    report = build_report(
        passing,
        watching,
        blocking,
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )
    reversed_report = build_report(blocking, watching, passing)

    assert api().SOURCE_RESOLUTION_SIGNAL_DECAY_QUEUE_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.status == "block"
    assert report.queue_action == "paper_source_resolution_signal_decay_queue_block"
    assert report.queue_item_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_signal_decay_score == d("0.420000")
    assert report.max_signal_decay_score == d("0.865000")
    assert report.max_latest_verification_age_hours == d("72.000000")
    assert report.min_extraction_confidence == d("0.200000")
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)

    assert tuple(row.scope_label for row in report.rows) == (
        "resolution_block",
        "resolution_watch",
        "resolution_pass",
    )
    by_label = {row.scope_label: row for row in report.rows}
    assert by_label["resolution_block"].queue_status == "block"
    assert by_label["resolution_block"].signal_decay_score == d("0.865000")
    assert by_label["resolution_block"].reason_codes == (
        "authority_tier_decay_pressure",
        "latest_verification_age_pressure",
        "contradiction_pressure",
        "corroboration_depth_gap",
        "extraction_confidence_gap",
        "deadline_proximity_pressure",
        "source_resolution_signal_decay_block",
    )
    assert by_label["resolution_watch"].queue_status == "watch"
    assert by_label["resolution_watch"].signal_decay_score == d("0.375000")
    assert by_label["resolution_pass"].queue_status == "pass"
    assert by_label["resolution_pass"].signal_decay_score == d("0.020000")
    assert by_label["resolution_pass"].reason_codes == (
        "source_resolution_signal_decay_pass",
    )

    payload = api().research_source_resolution_signal_decay_queue_report_payload(report)
    reversed_payload = api().research_source_resolution_signal_decay_queue_report_payload(
        reversed_report,
    )
    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert api().research_source_resolution_signal_decay_queue_report_digest(report) == (
        payload["derived_validation_digest"]
    )
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["queue_item_count"] == "3.000000"
    assert payload["rows"][0]["signal_decay_score"] == "0.865000"
    assert _float_paths(payload) == ()
    assert _unsafe_public_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_empty_queue_is_report_only_pass_with_stable_payload() -> None:
    report = build_report()

    assert report.status == "pass"
    assert report.queue_action == "paper_source_resolution_signal_decay_queue_monitor"
    assert report.queue_item_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.average_signal_decay_score == d("0.000000")
    assert report.max_signal_decay_score == d("0.000000")
    assert report.min_extraction_confidence == d("0.000000")
    assert report.reason_codes == ("source_resolution_signal_decay_report_pass",)
    assert report.reason_code_counts == ()
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.payload["derived_validation_digest"] == canonical_digest(report.payload)


def test_custom_config_public_payload_round_trips_and_rejects_resigned_tampering() -> None:
    module = api()
    config = module.ResearchSourceResolutionSignalDecayQueueConfig(
        watch_score_threshold=d("0.200000"),
        block_score_threshold=d("0.500000"),
        max_watch_verification_age_hours=d("24"),
        deadline_proximity_window_hours=d("12"),
        min_pass_corroboration_depth=d("2"),
        authority_tier_weight=d("0.100000"),
        latest_verification_age_weight=d("0.300000"),
        contradiction_pressure_weight=d("0.200000"),
        corroboration_depth_weight=d("0.100000"),
        extraction_confidence_weight=d("0.200000"),
        deadline_proximity_weight=d("0.100000"),
    )
    payload = build_report(
        observation(
            "resolution_custom_config",
            authority_tier="primary",
            latest_verified_at=GENERATED_AT - timedelta(hours=18),
            contradiction_pressure=d("0.400000"),
            corroboration_depth=d("1"),
            extraction_confidence=d("0.500000"),
            deadline_at=GENERATED_AT + timedelta(hours=6),
        ),
        cfg=config,
    ).payload

    assert tuple(payload["config"]) == tuple(field.name for field in fields(config))
    assert payload["config"]["max_watch_verification_age_hours"] == "24.000000"
    assert payload["config"]["latest_verification_age_weight"] == "0.300000"
    assert (
        module.research_source_resolution_signal_decay_queue_report_payload(payload)
        == payload
    )

    config_tampered = payload_copy(payload)
    config_tampered["config"]["authority_tier_weight"] = "0.200000"
    config_tampered["config"]["contradiction_pressure_weight"] = "0.100000"
    with pytest.raises(ValueError, match="config|signal_decay_score|rows"):
        module.research_source_resolution_signal_decay_queue_report_payload(
            resign(config_tampered),
        )

    derived_tampered = payload_copy(payload)
    derived_tampered["rows"][0]["signal_decay_score"] = "0.000000"
    with pytest.raises(ValueError, match="signal_decay_score|rows"):
        module.research_source_resolution_signal_decay_queue_report_payload(
            resign(derived_tampered),
        )


def test_decimal_validation_uses_raw_bounds_and_normalizes_signed_zero() -> None:
    module = api()

    with pytest.raises(ValueError, match="watch_score_threshold"):
        module.ResearchSourceResolutionSignalDecayQueueConfig(
            watch_score_threshold=d("-0.0000001"),
        )
    with pytest.raises(ValueError, match="contradiction_pressure"):
        observation("resolution_negative_tiny", contradiction_pressure=d("-0.0000001"))
    with pytest.raises(ValueError, match="extraction_confidence"):
        observation("resolution_above_one_tiny", extraction_confidence=d("1.0000001"))
    with pytest.raises(ValueError, match="corroboration_depth"):
        observation("resolution_fractional_depth", corroboration_depth=d("1.0000001"))

    signed_zero = observation(
        "resolution_signed_zero",
        contradiction_pressure=d("-0.000000"),
    )
    assert signed_zero.contradiction_pressure == d("0.000000")
    assert str(signed_zero.contradiction_pressure) == "0.000000"

    payload = build_report(signed_zero).payload
    assert payload["rows"][0]["contradiction_pressure"] == "0.000000"


def test_complete_deterministic_tie_breaks_are_scope_label_stable() -> None:
    later_label = observation(
        "resolution_tie_b",
        authority_tier="primary",
        latest_verified_at=GENERATED_AT - timedelta(hours=24),
        contradiction_pressure=d("0.300000"),
        corroboration_depth=d("2"),
        extraction_confidence=d("0.700000"),
        deadline_at=GENERATED_AT + timedelta(hours=12),
    )
    earlier_label = observation(
        "resolution_tie_a",
        authority_tier="primary",
        latest_verified_at=GENERATED_AT - timedelta(hours=24),
        contradiction_pressure=d("0.300000"),
        corroboration_depth=d("2"),
        extraction_confidence=d("0.700000"),
        deadline_at=GENERATED_AT + timedelta(hours=12),
    )

    report = build_report(later_label, earlier_label)
    reversed_report = build_report(earlier_label, later_label)

    assert tuple(row.scope_label for row in report.rows) == (
        "resolution_tie_a",
        "resolution_tie_b",
    )
    assert report.payload == reversed_report.payload


def test_frozen_dataclasses_decimal_only_exact_types_and_flags() -> None:
    module = api()
    report = build_report(observation("resolution_pass"))

    for value in (
        module.ResearchSourceResolutionSignalDecayQueueConfig(),
        observation("resolution_exact"),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    ):
        assert is_dataclass(value)
        for flag_name in ("paper_only", "report_only", "readonly"):
            assert getattr(value, flag_name) is True
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    for cls in (
        module.ResearchSourceResolutionSignalDecayQueueConfig,
        module.ResearchSourceResolutionSignalDecayObservation,
        module.ResearchSourceResolutionSignalDecayQueueRow,
        module.ResearchSourceResolutionSignalDecayQueueReasonCodeCount,
        module.ResearchSourceResolutionSignalDecayQueueReport,
    ):
        field_names = {field.name for field in fields(cls)}
        assert {"paper_only", "report_only", "readonly"} <= field_names

    for cls in (
        module.ResearchSourceResolutionSignalDecayQueueConfig,
        module.ResearchSourceResolutionSignalDecayObservation,
        module.ResearchSourceResolutionSignalDecayQueueRow,
        module.ResearchSourceResolutionSignalDecayQueueReasonCodeCount,
        module.ResearchSourceResolutionSignalDecayQueueReport,
    ):
        with pytest.raises(TypeError):
            type(f"Bad{cls.__name__}", (cls,), {})

    with pytest.raises(ValueError, match="contradiction_pressure"):
        observation("resolution_bad_float", contradiction_pressure=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="extraction_confidence"):
        observation(
            "resolution_bad_decimal_subclass",
            extraction_confidence=_DecimalSubclass("0.500000"),
        )
    with pytest.raises(ValueError, match="corroboration_depth"):
        observation("resolution_bad_depth", corroboration_depth=d("1.500000"))
    with pytest.raises(ValueError, match="latest_verified_at"):
        observation(
            "resolution_bad_datetime",
            latest_verified_at=_DateTimeSubclass(2026, 7, 8, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="paper_only"):
        module.ResearchSourceResolutionSignalDecayQueueConfig(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_object_setattr_mutations_are_revalidated_for_config_input_rows_and_counts() -> None:
    module = api()
    cfg = module.ResearchSourceResolutionSignalDecayQueueConfig()
    object.__setattr__(cfg, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        build_report(observation("resolution_cfg_mutation"), cfg=cfg)

    mutated_observation = observation("resolution_input_mutation")
    object.__setattr__(mutated_observation, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        build_report(mutated_observation)

    row_report = build_report(
        observation(
            "resolution_row_mutation",
            authority_tier="tertiary",
            latest_verified_at=GENERATED_AT - timedelta(hours=72),
            contradiction_pressure=d("0.900000"),
            corroboration_depth=d("0"),
            extraction_confidence=d("0.200000"),
            deadline_at=GENERATED_AT + timedelta(hours=6),
        ),
    )
    object.__setattr__(row_report.rows[0], "authority_tier_score", d("0.123456"))
    resign_report_object(row_report)
    with pytest.raises(ValueError, match="authority_tier_score"):
        module.research_source_resolution_signal_decay_queue_report_payload(row_report)

    count_report = build_report(
        observation(
            "resolution_count_mutation",
            authority_tier="primary",
            latest_verified_at=GENERATED_AT - timedelta(hours=36),
            contradiction_pressure=d("0.300000"),
            corroboration_depth=d("2"),
            extraction_confidence=d("0.650000"),
            deadline_at=GENERATED_AT + timedelta(hours=24),
        ),
    )
    object.__setattr__(count_report.reason_code_counts[0], "count", d("9.000000"))
    resign_report_object(count_report)
    with pytest.raises(ValueError, match="reason_code_counts"):
        module.research_source_resolution_signal_decay_queue_report_payload(count_report)


def test_resigned_public_mapping_rederives_row_status_reason_score_and_order_fields() -> None:
    module = api()
    payload = build_report(
        observation(
            "resolution_block",
            authority_tier="tertiary",
            latest_verified_at=GENERATED_AT - timedelta(hours=72),
            contradiction_pressure=d("0.900000"),
            corroboration_depth=d("0"),
            extraction_confidence=d("0.200000"),
            deadline_at=GENERATED_AT + timedelta(hours=6),
        ),
        observation(
            "resolution_watch",
            authority_tier="primary",
            latest_verified_at=GENERATED_AT - timedelta(hours=36),
            contradiction_pressure=d("0.300000"),
            corroboration_depth=d("2"),
            extraction_confidence=d("0.650000"),
            deadline_at=GENERATED_AT + timedelta(hours=24),
        ),
    ).payload

    status_tampered = payload_copy(payload)
    status_tampered["rows"][0]["queue_status"] = "pass"
    with pytest.raises(ValueError, match="queue_status|status|rows"):
        module.research_source_resolution_signal_decay_queue_report_payload(
            resign(status_tampered),
        )

    reason_tampered = payload_copy(payload)
    reason_tampered["rows"][0]["reason_codes"] = [
        "source_resolution_signal_decay_pass",
    ]
    with pytest.raises(ValueError, match="reason_codes|rows"):
        module.research_source_resolution_signal_decay_queue_report_payload(
            resign(reason_tampered),
        )

    score_tampered = payload_copy(payload)
    score_tampered["rows"][0]["signal_decay_score"] = "0.000000"
    with pytest.raises(ValueError, match="signal_decay_score|rows"):
        module.research_source_resolution_signal_decay_queue_report_payload(
            resign(score_tampered),
        )

    order_tampered = payload_copy(payload)
    order_tampered["rows"] = [order_tampered["rows"][1], order_tampered["rows"][0]]
    with pytest.raises(ValueError, match="sorted|rows"):
        module.research_source_resolution_signal_decay_queue_report_payload(
            resign(order_tampered),
        )


def test_resigned_public_mapping_rederives_reason_counts_and_report_aggregates() -> None:
    module = api()
    payload = build_report(
        observation(
            "resolution_block",
            authority_tier="tertiary",
            latest_verified_at=GENERATED_AT - timedelta(hours=72),
            contradiction_pressure=d("0.900000"),
            corroboration_depth=d("0"),
            extraction_confidence=d("0.200000"),
            deadline_at=GENERATED_AT + timedelta(hours=6),
        ),
        observation("resolution_pass"),
    ).payload

    count_tampered = payload_copy(payload)
    count_tampered["reason_code_counts"][0]["count"] = "9.000000"
    with pytest.raises(ValueError, match="reason_code_counts"):
        module.research_source_resolution_signal_decay_queue_report_payload(
            resign(count_tampered),
        )

    aggregate_tampered = payload_copy(payload)
    aggregate_tampered["average_signal_decay_score"] = "0.000000"
    with pytest.raises(ValueError, match="average_signal_decay_score"):
        module.research_source_resolution_signal_decay_queue_report_payload(
            resign(aggregate_tampered),
        )


def test_public_mapping_requires_canonical_schema_key_order_and_sha256() -> None:
    module = api()
    payload = build_report(observation("resolution_schema")).payload
    assert module.research_source_resolution_signal_decay_queue_report_payload(payload) == payload

    extra = payload_copy(payload)
    extra["extra_public_field"] = "public"
    with pytest.raises(ValueError, match="schema|canonical"):
        module.research_source_resolution_signal_decay_queue_report_payload(resign(extra))

    items = list(payload_copy(payload).items())
    reordered = dict([items[1], items[0], *items[2:]])
    with pytest.raises(ValueError, match="key order|canonical"):
        module.research_source_resolution_signal_decay_queue_report_payload(
            resign(reordered),
        )

    nested_extra = payload_copy(payload)
    nested_extra["rows"][0]["extra_public_field"] = "public"
    with pytest.raises(ValueError, match="schema|canonical"):
        module.research_source_resolution_signal_decay_queue_report_payload(
            resign(nested_extra),
        )

    nested_items = list(payload_copy(payload)["rows"][0].items())
    nested_reordered = payload_copy(payload)
    nested_reordered["rows"][0] = dict([nested_items[1], nested_items[0], *nested_items[2:]])
    with pytest.raises(ValueError, match="key order|canonical"):
        module.research_source_resolution_signal_decay_queue_report_payload(
            resign(nested_reordered),
        )

    bad_digest = payload_copy(payload)
    bad_digest["derived_validation_digest"] = "f" * 63 + "g"
    with pytest.raises(ValueError, match="SHA-256"):
        module.research_source_resolution_signal_decay_queue_report_payload(bad_digest)


def test_validation_rejects_unsafe_public_surfaces_and_payload_tampering() -> None:
    module = api()
    report = build_report(observation("resolution_pass"))
    payload = module.research_source_resolution_signal_decay_queue_report_payload(report)

    for bad_label in (
        "candidate_alpha",
        "market_alpha",
        "slug_alpha",
        "question_alpha",
        "wallet_alpha",
        "order_alpha",
        "trade_alpha",
        "sizing_alpha",
        "recommendation_alpha",
        "execution_alpha",
        "execute_alpha",
        "auth_token_alpha",
        "authorization_alpha",
        "live_alpha",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            observation(bad_label)

    with pytest.raises(ValueError, match="latest_verified_at"):
        build_report(
            observation(
                "resolution_future",
                latest_verified_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="unique"):
        build_report(observation("resolution_dup"), observation("resolution_dup"))
    with pytest.raises(ValueError, match="authority_tier"):
        observation("resolution_bad_tier", authority_tier="anonymous")
    with pytest.raises(ValueError, match="block_score_threshold"):
        module.ResearchSourceResolutionSignalDecayQueueConfig(
            watch_score_threshold=d("0.700000"),
            block_score_threshold=d("0.700000"),
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    tampered_status = dict(payload)
    tampered_status["status"] = "blocked"
    tampered_status["derived_validation_digest"] = canonical_digest(tampered_status)
    with pytest.raises(ValueError, match="status"):
        module.research_source_resolution_signal_decay_queue_report_payload(
            tampered_status,
        )

    leaked = dict(payload)
    leaked["candidate_id"] = "candidate_alpha"
    leaked["derived_validation_digest"] = canonical_digest(leaked)
    with pytest.raises(ValueError, match="unsafe"):
        module.research_source_resolution_signal_decay_queue_report_payload(leaked)

    nested_flag = dict(payload)
    nested_flag["rows"] = [dict(row) for row in payload["rows"]]
    nested_flag["rows"][0]["paper_only"] = False
    nested_flag["derived_validation_digest"] = canonical_digest(nested_flag)
    with pytest.raises(ValueError, match="paper_only"):
        module.research_source_resolution_signal_decay_queue_report_payload(nested_flag)

    numeric = dict(payload)
    numeric["queue_item_count"] = 3
    numeric["derived_validation_digest"] = canonical_digest(numeric)
    with pytest.raises(ValueError, match="Decimal"):
        module.research_source_resolution_signal_decay_queue_report_payload(numeric)

    numeric_string = dict(payload)
    numeric_string["queue_item_count"] = "1"
    numeric_string["derived_validation_digest"] = canonical_digest(numeric_string)
    with pytest.raises(ValueError, match="Decimal"):
        module.research_source_resolution_signal_decay_queue_report_payload(numeric_string)


def test_module_imports_no_db_network_or_scraping_dependencies() -> None:
    source = MODULE_PATH.read_text()
    tree = ast.parse(source)
    forbidden_roots = {
        "bs4",
        "asyncio",
        "httpx",
        "multiprocessing",
        "os",
        "playwright",
        "psycopg",
        "requests",
        "scrapy",
        "selenium",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "subprocess",
        "urllib",
    }
    forbidden_calls = {
        "__import__",
        "compile",
        "eval",
        "exec",
        "input",
        "open",
        "print",
    }

    assert ".total_seconds(" not in source
    assert "fast_mode" not in source
    assert "fast mode" not in source.lower()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_roots
        elif isinstance(node, ast.ImportFrom):
            assert node.module is not None
            assert node.module.split(".", 1)[0] not in forbidden_roots
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_calls


def _float_paths(value: object, path: str = "payload") -> tuple[str, ...]:
    if isinstance(value, float):
        return (path,)
    if isinstance(value, dict):
        return tuple(
            item
            for key, child in value.items()
            for item in _float_paths(child, f"{path}.{key}")
        )
    if isinstance(value, list):
        return tuple(
            item
            for index, child in enumerate(value)
            for item in _float_paths(child, f"{path}[{index}]")
        )
    return ()


def _unsafe_public_paths(value: object, path: str = "payload") -> tuple[str, ...]:
    if isinstance(value, str):
        normalized = value.lower()
        if any(fragment in normalized for fragment in FORBIDDEN_PUBLIC_FRAGMENTS):
            return (path,)
        return ()
    if isinstance(value, dict):
        paths: list[str] = []
        for key, child in value.items():
            normalized_key = key.lower()
            if any(fragment in normalized_key for fragment in FORBIDDEN_PUBLIC_FRAGMENTS):
                paths.append(f"{path}.{key}")
            paths.extend(_unsafe_public_paths(child, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        return tuple(
            item
            for index, child in enumerate(value)
            for item in _unsafe_public_paths(child, f"{path}[{index}]")
        )
    return ()

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_team_memory_source_authority_quorum_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_team_memory_source_authority_quorum_report.py",
)
GENERATED_AT = datetime(2026, 7, 9, 15, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 14, 30, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _module() -> Any:
    spec = importlib.util.find_spec(MODULE_NAME)
    assert spec is not None, "research team quorum report module is missing"
    return importlib.import_module(MODULE_NAME)


def _config(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_TEAM_MEMORY_SOURCE_AUTHORITY_QUORUM_CONFIG_VERSION
        ),
        "min_memory_count": d("2.000000"),
        "min_source_family_count": d("2.000000"),
        "min_authority_count": d("2.000000"),
        "min_pass_quorum_score": d("0.750000"),
        "min_watch_quorum_score": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchTeamMemorySourceAuthorityQuorumConfig(**values)


def _observation(module: Any, item_ref: str = "private-item-alpha", **overrides: object) -> Any:
    values = {
        "item_ref": item_ref,
        "memory_ref": "memory-alpha",
        "source_family_ref": "family-alpha",
        "authority_ref": "authority-alpha",
        "observed_at": OBSERVED_AT,
        "memory_confidence_score": d("0.900000"),
        "source_authority_score": d("0.900000"),
        "supports_quorum": True,
        "private_material": (
            "CANDIDATE-RAW-001",
            "MARKET-RAW-001",
            "https://private.example/source",
            "raw source text must stay private",
            "postgres://private-dsn",
            "private_research_table",
            "private-token",
        ),
    }
    values.update(overrides)
    return module.ResearchTeamMemorySourceAuthorityObservation(**values)


def _build(module: Any, observations: tuple[Any, ...], **overrides: object) -> Any:
    values = {
        "observations": observations,
        "generated_at": GENERATED_AT,
        "config": _config(module),
        "public_payload": (),
    }
    values.update(overrides)
    return module.build_research_team_memory_source_authority_quorum_report(**values)


def _payload(module: Any, report: Any) -> dict[str, Any]:
    return module.research_team_memory_source_authority_quorum_report_public_payload(
        report,
    )


def _digest(module: Any, report: Any) -> str:
    return module.research_team_memory_source_authority_quorum_report_digest(report)


def _validate(module: Any, payload: dict[str, Any]) -> dict[str, Any]:
    return module.validate_research_team_memory_source_authority_quorum_public_payload(
        payload,
    )


def test_builds_pass_watch_and_block_rows_without_raw_material_leaks() -> None:
    module = _module()
    report = _build(
        module,
        (
            _observation(
                module,
                "candidate-alpha/market-slug?token=hidden&wallet=private",
                memory_ref="memory-a",
                source_family_ref="family-a",
                authority_ref="authority-a",
                memory_confidence_score=d("0.900000"),
                source_authority_score=d("0.900000"),
            ),
            _observation(
                module,
                "candidate-alpha/market-slug?token=hidden&wallet=private",
                memory_ref="memory-b",
                source_family_ref="family-b",
                authority_ref="authority-b",
                memory_confidence_score=d("0.800000"),
                source_authority_score=d("0.850000"),
            ),
            _observation(
                module,
                "candidate-beta",
                memory_ref="memory-c",
                source_family_ref="family-c",
                authority_ref="authority-c",
                memory_confidence_score=d("0.550000"),
                source_authority_score=d("0.450000"),
            ),
            _observation(
                module,
                "candidate-beta",
                memory_ref="memory-d",
                source_family_ref="family-d",
                authority_ref="authority-d",
                memory_confidence_score=d("0.600000"),
                source_authority_score=d("0.500000"),
            ),
            _observation(
                module,
                "candidate-gamma",
                memory_ref="memory-e",
                source_family_ref="family-e",
                authority_ref="authority-e",
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
        public_payload=(
            module.ResearchTeamMemorySourceAuthorityQuorumPublicPayloadItem(
                key="review_scope",
                value="team memory quorum review only",
            ),
        ),
    )

    assert is_dataclass(report)
    assert type(report) is module.ResearchTeamMemorySourceAuthorityQuorumReport
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.status == "block"
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_quorum_score == d("0.786111")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert {row.status for row in report.rows} == {"pass", "watch", "block"}

    passed = _row_with_status(report, "pass")
    assert passed.item_digest.startswith("sha256:")
    assert passed.observation_count == d("2.000000")
    assert passed.supporting_memory_count == d("2.000000")
    assert passed.supporting_source_family_count == d("2.000000")
    assert passed.supporting_authority_count == d("2.000000")
    assert passed.source_family_quorum_score == d("1.000000")
    assert passed.quorum_score == d("0.908333")
    assert passed.reason_codes == ("memory_source_authority_quorum_pass",)

    watched = _row_with_status(report, "watch")
    assert watched.quorum_score == d("0.683333")
    assert watched.reason_codes == ("quorum_score_watch",)

    blocked = _row_with_status(report, "block")
    assert blocked.reason_codes == (
        "insufficient_memory_quorum",
        "insufficient_source_family_quorum",
        "insufficient_authority_quorum",
    )

    payload = _payload(module, report)
    encoded = json.dumps(payload, sort_keys=True).lower()
    for leaked in (
        "candidate-alpha",
        "market-slug",
        "token=hidden",
        "wallet=private",
        "private.example",
        "raw source text",
        "private-dsn",
        "private_research_table",
        "private-token",
    ):
        assert leaked not in encoded
    for forbidden_key in ("candidate", "market", "source_url", "source_text", "dsn", "table", "token"):
        assert forbidden_key not in encoded
    assert payload["public_payload"] == [
        {
            "key": "review_scope",
            "value": "team memory quorum review only",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]


def test_public_payload_is_deterministic_decimal_stringed_and_digest_validated() -> None:
    module = _module()
    first = _build(
        module,
        (
            _observation(module, "private-b", memory_ref="memory-b", source_family_ref="family-b"),
            _observation(module, "private-a", memory_ref="memory-a", source_family_ref="family-a"),
        ),
    )
    second = _build(
        module,
        (
            _observation(module, "private-a", memory_ref="memory-a", source_family_ref="family-a"),
            _observation(module, "private-b", memory_ref="memory-b", source_family_ref="family-b"),
        ),
    )

    first_payload = _payload(module, first)
    second_payload = _payload(module, second)

    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert first.derived_validation_digest == _digest(module, first)
    assert first_payload["derived_validation_digest"] == _unsigned_digest(first_payload)
    assert len(first.derived_validation_digest) == 64
    int(first.derived_validation_digest, 16)
    assert first_payload["row_count"] == "2.000000"
    assert first_payload["rows"][0]["quorum_score"] == "0.766667"
    assert not any(type(value) in (int, float) for value in _walk_values(first_payload))
    assert _validate(module, first_payload) == first_payload

    tampered_digest = dict(first_payload)
    tampered_digest["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        _validate(module, tampered_digest)

    tampered_score = json.loads(json.dumps(first_payload))
    tampered_score["rows"][0]["quorum_score"] = "0.010000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        _validate(module, tampered_score)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)


def test_dataclasses_are_frozen_exact_type_and_decimal_only() -> None:
    module = _module()
    report = _build(module, (_observation(module),))

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(module.ResearchTeamMemorySourceAuthorityQuorumConfig):
            pass

    with pytest.raises(ValueError, match="Decimal"):
        _config(module, min_memory_count=2)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Decimal"):
        _observation(module, memory_confidence_score=0.8)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="status"):
        replace(report, status="ready")

    _assert_no_non_decimal_public_numbers(report)


def test_safety_flags_public_payload_guards_and_forbidden_runtime_surfaces() -> None:
    module = _module()

    with pytest.raises(ValueError, match="paper_only"):
        _config(module, paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        _observation(module, report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        module.ResearchTeamMemorySourceAuthorityQuorumPublicPayloadItem(
            key="review_scope",
            value="team memory quorum review only",
            readonly=False,
        )

    for key in (
        "db_key",
        "network_key",
        "wallet_key",
        "auth_key",
        "order_key",
        "live_key",
        "trading_key",
        "sizing_key",
        "recommendation_key",
        "candidate_key",
        "market_key",
        "source_url",
        "source_text",
        "dsn_key",
        "table_key",
        "token_key",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            module.ResearchTeamMemorySourceAuthorityQuorumPublicPayloadItem(key, "safe")

    for value in (
        "db value",
        "network value",
        "wallet value",
        "auth value",
        "order value",
        "live trading value",
        "sizing value",
        "recommendation value",
        "candidate value",
        "market value",
        "source url value",
        "source text value",
        "dsn value",
        "table value",
        "token value",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            module.ResearchTeamMemorySourceAuthorityQuorumPublicPayloadItem(
                "review_scope",
                value,
            )

    module_source = MODULE_PATH.read_text(encoding="utf-8").lower()
    for forbidden_fragment in (
        "wallet",
        "order",
        "live trading",
        "sizing",
        "recommendation",
        "requests",
        "urllib",
        "socket",
        "psycopg",
        "sqlite",
        "sqlalchemy",
    ):
        assert forbidden_fragment not in module_source


def _row_with_status(report: Any, status: str) -> Any:
    matches = tuple(row for row in report.rows if row.status == status)
    assert len(matches) == 1
    return matches[0]


def _unsigned_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(
        unsigned,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(_walk_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(_walk_values(item))
        return tuple(nested)
    return (value,)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))

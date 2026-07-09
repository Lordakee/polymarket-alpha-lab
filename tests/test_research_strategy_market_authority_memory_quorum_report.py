from __future__ import annotations

import ast
import importlib
import json
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_strategy_market_authority_memory_quorum_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_market_authority_memory_quorum_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


def api() -> Any:
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


def cfg(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": "authority-memory-quorum-report-test-v0",
        "min_authority_count": d("2.000000"),
        "min_memory_count": d("2.000000"),
        "min_quorum_count": d("3.000000"),
        "max_memory_age_seconds": d("86400.000000"),
        "watch_score_floor": d("0.650000"),
        "block_score_floor": d("0.350000"),
        "authority_weight": d("0.350000"),
        "memory_weight": d("0.250000"),
        "quorum_weight": d("0.250000"),
        "freshness_weight": d("0.150000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchStrategyMarketAuthorityMemoryQuorumConfig(**values)


def observation(
    review_key: str,
    *,
    observed_at: datetime = GENERATED_AT - timedelta(minutes=5),
    authority_count: Decimal = d("2.000000"),
    memory_count: Decimal = d("2.000000"),
    quorum_count: Decimal = d("3.000000"),
    memory_age_seconds: Decimal = d("3600.000000"),
    authority_score: Decimal = d("0.900000"),
    memory_score: Decimal = d("0.900000"),
    quorum_score: Decimal = d("0.900000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchStrategyMarketAuthorityMemoryQuorumObservation(
        review_key=review_key,
        observed_at=observed_at,
        authority_count=authority_count,
        memory_count=memory_count,
        quorum_count=quorum_count,
        memory_age_seconds=memory_age_seconds,
        authority_score=authority_score,
        memory_score=memory_score,
        quorum_score=quorum_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *observations: object,
    generated_at: datetime = GENERATED_AT,
    config: object | None = None,
) -> Any:
    module = api()
    return module.build_research_strategy_market_authority_memory_quorum_report(
        observations,
        config=config or cfg(),
        generated_at=generated_at,
    )


def assert_decimal_public_fields(value: object) -> None:
    for field in fields(value):
        if field.name in {"reason_code_counts", "rows"}:
            continue
        field_value = getattr(value, field.name)
        if isinstance(field_value, bool) or field_value is None:
            continue
        if any(
            marker in field.name
            for marker in (
                "age",
                "count",
                "floor",
                "maximum",
                "minimum",
                "score",
                "total",
                "weight",
            )
        ):
            assert type(field_value) is Decimal, field.name


def assert_payload_has_no_native_numbers(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"payload numeric was not serialized as string: {value!r}")
    if isinstance(value, dict):
        for item_value in value.values():
            assert_payload_has_no_native_numbers(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_payload_has_no_native_numbers(item_value)


def assert_public_payload_is_sanitized(value: Any) -> None:
    forbidden_key_fragments = (
        "candi" + "date",
        "market_id",
        "market_slug",
        "question",
        "raw",
        "source_" + "text",
        "source_" + "url",
        "au" + "th_key",
        "au" + "th_token",
        "dsn",
        "exec" + "ution",
        "li" + "ve",
        "table",
        "token",
    )
    forbidden_value_fragments = (
        "://" ,
        "www.",
        "candi" + "date",
        "market_id",
        "market_slug",
        "question",
        "source_" + "text",
        "source_" + "url",
        "au" + "th key",
        "au" + "th-token",
        "dsn",
        "exec" + "ution",
        "li" + "ve",
        "token",
    )
    if isinstance(value, dict):
        for key, item_value in value.items():
            lowered = key.lower()
            for fragment in forbidden_key_fragments:
                assert fragment not in lowered, key
            assert_public_payload_is_sanitized(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_public_payload_is_sanitized(item_value)
        return
    if isinstance(value, str):
        lowered = value.lower()
        for fragment in forbidden_value_fragments:
            assert fragment not in lowered, value


def resigned_payload(module: Any, payload: dict[str, object]) -> dict[str, object]:
    resigned = deepcopy(payload)
    unsigned = dict(resigned)
    unsigned.pop("derived_validation_digest", None)
    resigned["derived_validation_digest"] = module._digest_from_values(unsigned)
    return resigned


def test_empty_report_is_pass_report_only_decimal_digest_bound_and_json_safe() -> None:
    module = api()
    empty_report = report()

    assert is_dataclass(empty_report)
    assert empty_report.__dataclass_params__.frozen is True
    assert module.AUTHORITY_MEMORY_QUORUM_STATUSES == ("pass", "watch", "block")
    assert empty_report.generated_at == GENERATED_AT
    assert empty_report.config_version == "authority-memory-quorum-report-test-v0"
    assert empty_report.status == "pass"
    assert empty_report.row_count == d("0.000000")
    assert empty_report.pass_count == d("0.000000")
    assert empty_report.watch_count == d("0.000000")
    assert empty_report.block_count == d("0.000000")
    assert empty_report.total_authority_count == d("0.000000")
    assert empty_report.total_memory_count == d("0.000000")
    assert empty_report.total_quorum_count == d("0.000000")
    assert empty_report.average_authority_memory_quorum_score == d("0.000000")
    assert empty_report.minimum_authority_memory_quorum_score == d("0.000000")
    assert empty_report.maximum_memory_age_seconds == d("0.000000")
    assert empty_report.reason_codes == ("authority_memory_quorum_pass",)
    assert empty_report.reason_code_counts == ()
    assert empty_report.rows == ()
    assert empty_report.paper_only is True
    assert empty_report.report_only is True
    assert empty_report.readonly is True
    assert_decimal_public_fields(empty_report)

    payload = empty_report.payload
    digest_value = module.research_strategy_market_authority_memory_quorum_report_digest(
        empty_report,
    )
    json.dumps(payload, allow_nan=False, sort_keys=True)
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["status"] == "pass"
    assert payload["row_count"] == "0.000000"
    assert payload["derived_validation_digest"] == digest_value
    assert len(digest_value) == 64
    assert module.validate_research_strategy_market_authority_memory_quorum_public_payload(
        payload,
    )
    assert_payload_has_no_native_numbers(payload)
    assert_public_payload_is_sanitized(payload)


def test_report_assigns_pass_watch_and_block_from_authority_memory_quorum() -> None:
    built = report(
        observation("case-pass"),
        observation(
            "case-watch",
            authority_count=d("1.000000"),
            memory_count=d("1.000000"),
            quorum_count=d("2.000000"),
            memory_age_seconds=d("50000.000000"),
            authority_score=d("0.600000"),
            memory_score=d("0.600000"),
            quorum_score=d("0.700000"),
        ),
        observation(
            "case-block",
            authority_count=d("0.000000"),
            memory_count=d("0.000000"),
            quorum_count=d("0.000000"),
            memory_age_seconds=d("90000.000000"),
            authority_score=d("0.200000"),
            memory_score=d("0.200000"),
            quorum_score=d("0.200000"),
        ),
    )

    assert built.status == "block"
    assert built.row_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.total_authority_count == d("3.000000")
    assert built.total_memory_count == d("3.000000")
    assert built.total_quorum_count == d("5.000000")
    assert built.average_authority_memory_quorum_score == d("0.479537")
    assert built.minimum_authority_memory_quorum_score == d("0.000000")
    assert built.maximum_memory_age_seconds == d("90000.000000")
    assert tuple(row.review_key for row in built.rows) == (
        "case-block",
        "case-watch",
        "case-pass",
    )

    blocked, watched, passed = built.rows
    assert blocked.status == "block"
    assert blocked.authority_memory_quorum_score == d("0.000000")
    assert blocked.reason_codes == (
        "missing_authority_block",
        "missing_memory_block",
        "weak_quorum_block",
        "stale_memory_block",
        "low_authority_score_block",
        "low_memory_score_block",
        "authority_memory_quorum_score_block",
    )

    assert watched.status == "watch"
    assert watched.authority_component_score == d("0.500000")
    assert watched.memory_component_score == d("0.500000")
    assert watched.quorum_component_score == d("0.666667")
    assert watched.freshness_component_score == d("0.421296")
    assert watched.authority_memory_quorum_score == d("0.529861")
    assert watched.reason_codes == (
        "missing_authority_watch",
        "missing_memory_watch",
        "weak_quorum_watch",
        "stale_memory_watch",
        "low_authority_score_watch",
        "low_memory_score_watch",
        "authority_memory_quorum_score_watch",
    )

    assert passed.status == "pass"
    assert passed.authority_memory_quorum_score == d("0.908750")
    assert passed.reason_codes == ("authority_memory_quorum_pass",)


def test_public_payload_digest_is_deterministic_validated_and_sanitized() -> None:
    module = api()
    observations = (
        observation(
            "case-alpha",
            authority_count=d("1.000000"),
            memory_count=d("2.000000"),
            quorum_count=d("2.000000"),
            memory_age_seconds=d("50000.000000"),
            authority_score=d("0.600000"),
        ),
        observation(
            "case-beta",
            authority_count=d("2.000000"),
            memory_count=d("1.000000"),
            quorum_count=d("3.000000"),
            memory_score=d("0.600000"),
        ),
    )

    first = report(*observations)
    second = report(*reversed(observations))

    assert first.derived_validation_digest == second.derived_validation_digest
    assert module.research_strategy_market_authority_memory_quorum_report_digest(
        first,
    ) == first.derived_validation_digest
    assert first.payload["derived_validation_digest"] == first.derived_validation_digest
    assert module.validate_research_strategy_market_authority_memory_quorum_public_payload(
        first.payload,
    )
    assert_payload_has_no_native_numbers(first.payload)
    assert_public_payload_is_sanitized(first.payload)

    tampered = dict(first.payload)
    tampered["status"] = "pass" if first.status != "pass" else "watch"
    assert not module.validate_research_strategy_market_authority_memory_quorum_public_payload(
        tampered,
    )

    unsafe = dict(first.payload)
    unsafe["candi" + "date_key"] = "hidden"
    assert not module.validate_research_strategy_market_authority_memory_quorum_public_payload(
        unsafe,
    )

    unsafe_value = dict(first.payload)
    unsafe_value["safe_key"] = "https" + "://example.invalid/item"
    assert not module.validate_research_strategy_market_authority_memory_quorum_public_payload(
        unsafe_value,
    )


def test_duplicate_review_keys_are_rejected_to_preserve_canonical_digest() -> None:
    duplicate_key = "case-duplicate"

    with pytest.raises(ValueError, match="review_key"):
        report(
            observation(
                duplicate_key,
                observed_at=GENERATED_AT - timedelta(minutes=10),
            ),
            observation(
                duplicate_key,
                observed_at=GENERATED_AT - timedelta(minutes=5),
            ),
        )


def test_public_payload_validator_rejects_resigned_invalid_public_shape() -> None:
    module = api()
    payload = report(observation("case-payload-shape")).payload

    invalid_top_status = resigned_payload(module, {**payload, "status": "execute"})
    assert not module.validate_research_strategy_market_authority_memory_quorum_public_payload(
        invalid_top_status,
    )

    invalid_top_flag = resigned_payload(module, {**payload, "paper_only": False})
    assert not module.validate_research_strategy_market_authority_memory_quorum_public_payload(
        invalid_top_flag,
    )

    invalid_extra_key = resigned_payload(module, {**payload, "extra_public_key": "pass"})
    assert not module.validate_research_strategy_market_authority_memory_quorum_public_payload(
        invalid_extra_key,
    )

    invalid_row_status = deepcopy(payload)
    invalid_row_status["rows"][0]["status"] = "execute"  # type: ignore[index]
    assert not module.validate_research_strategy_market_authority_memory_quorum_public_payload(
        resigned_payload(module, invalid_row_status),
    )

    invalid_row_flag = deepcopy(payload)
    invalid_row_flag["rows"][0]["readonly"] = False  # type: ignore[index]
    assert not module.validate_research_strategy_market_authority_memory_quorum_public_payload(
        resigned_payload(module, invalid_row_flag),
    )


def test_public_payload_validator_rejects_future_rows_and_oversized_decimals() -> None:
    module = api()
    payload = report(observation("case-payload-boundaries")).payload

    future_row = deepcopy(payload)
    future_row["rows"][0]["observed_at"] = (  # type: ignore[index]
        GENERATED_AT + timedelta(seconds=1)
    ).isoformat()
    assert not module.validate_research_strategy_market_authority_memory_quorum_public_payload(
        resigned_payload(module, future_row),
    )

    oversized_decimal = dict(payload)
    oversized_decimal["row_count"] = f"{'9' * 1000}.000000"
    assert not module.validate_research_strategy_market_authority_memory_quorum_public_payload(
        oversized_decimal,
    )


@pytest.mark.parametrize(
    "review_key",
    (
        "market-id-abc",
        "market.id.abc",
        "source-url-abc",
        "source.text.abc",
    ),
)
def test_public_identifiers_reject_separator_obfuscated_sensitive_names(
    review_key: str,
) -> None:
    with pytest.raises(ValueError, match="unsafe"):
        observation(review_key)


def test_dataclasses_are_frozen_strict_decimal_only_and_enforce_flags() -> None:
    module = api()
    built = report(observation("case-decimal"))

    public_classes = (
        module.ResearchStrategyMarketAuthorityMemoryQuorumConfig,
        module.ResearchStrategyMarketAuthorityMemoryQuorumObservation,
        module.ResearchStrategyMarketAuthorityMemoryQuorumReasonCodeCount,
        module.ResearchStrategyMarketAuthorityMemoryQuorumRow,
        module.ResearchStrategyMarketAuthorityMemoryQuorumReport,
    )
    for public_class in public_classes:
        assert is_dataclass(public_class)
        assert public_class.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        built.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadReport(module.ResearchStrategyMarketAuthorityMemoryQuorumReport):
            pass

    with pytest.raises(ValueError, match="authority_count must be exactly Decimal"):
        observation("case-float", authority_count=1.0)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="memory_score must be exactly Decimal"):
        observation("case-decimal-subclass", memory_score=_DecimalSubclass("0.900000"))

    with pytest.raises(ValueError, match="paper_only must be a bool"):
        observation("case-flag", paper_only=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report(generated_at=_DatetimeSubclass(2026, 7, 9, 12, tzinfo=UTC))

    with pytest.raises(ValueError, match="timezone-aware"):
        observation("case-naive", observed_at=datetime(2026, 7, 9, 11, 30))

    with pytest.raises(ValueError, match="utcoffset"):
        observation(
            "case-offset",
            observed_at=datetime(2026, 7, 9, 11, 30, tzinfo=_NoneOffsetTz()),
        )

    with pytest.raises(ValueError, match="unsafe"):
        observation("mark" + "et_id_abc")

    for unsafe_review_key in (
        "au" + "th-token",
        "li" + "ve-feed",
        "exec" + "ution-id",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            observation(unsafe_review_key)

    with pytest.raises(ValueError, match="report_only"):
        replace(built.rows[0], report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(built, readonly=False)

    with pytest.raises(ValueError, match="weights must sum to one"):
        cfg(freshness_weight=d("0.050000"))

    with pytest.raises(ValueError, match="quantized"):
        observation("case-oversized-decimal", authority_count=Decimal("1e1000"))


def test_module_source_is_report_only_and_has_no_execution_surface() -> None:
    module = api()
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    forbidden_imports = {
        "httpx",
        "psycopg",
        "py_clob_client",
        "requests",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "web3",
    }
    assert imported_roots.isdisjoint(forbidden_imports)

    public_names = set(dir(module))
    for fragment in (
        "client",
        "wall" + "et",
        "or" + "der",
        "exec" + "ution",
        "li" + "ve",
        "tra" + "de",
        "trad" + "ing",
        "siz" + "ing",
        "recomm" + "endation",
    ):
        for public_name in public_names:
            assert fragment not in public_name.lower(), public_name

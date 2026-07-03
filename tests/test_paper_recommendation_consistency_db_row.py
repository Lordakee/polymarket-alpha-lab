from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.paper_recommendation_consistency import (
    PaperRecommendationConsistencyReport,
    PaperRecommendationConsistencyRow,
)


GENERATED_AT = datetime(2026, 6, 21, 15, 30, tzinfo=UTC)


class ConsistencyReportSubclass(PaperRecommendationConsistencyReport):
    pass


def _codec_module():
    from polymarket_alpha_lab import paper_recommendation_consistency_db_row

    return paper_recommendation_consistency_db_row


def _report() -> PaperRecommendationConsistencyReport:
    return PaperRecommendationConsistencyReport(
        generated_at=GENERATED_AT,
        config_version="recommendation-consistency-v1",
        group_count=2,
        pass_count=1,
        watch_count=1,
        blocked_count=0,
        consistency_status="watch",
        consistency_rows=(
            PaperRecommendationConsistencyRow(
                market_slug="alpha-market",
                side="yes",
                source_count=2,
                distinct_statuses=("recommend",),
                edge_min=Decimal("0.100000"),
                edge_max=Decimal("0.110000"),
                edge_spread=Decimal("0.010000"),
                score_min=Decimal("0.700000"),
                score_max=Decimal("0.725000"),
                score_spread=Decimal("0.025000"),
                consistency_status="pass",
                reason_codes=("recommendation_consistency_passed",),
            ),
            PaperRecommendationConsistencyRow(
                market_slug="beta-market",
                side="no",
                source_count=1,
                distinct_statuses=("watch",),
                edge_min=Decimal("0.050000"),
                edge_max=Decimal("0.050000"),
                edge_spread=Decimal("0.000000"),
                score_min=Decimal("0.500000"),
                score_max=Decimal("0.500000"),
                score_spread=Decimal("0.000000"),
                consistency_status="watch",
                reason_codes=("missing_recommendation_sources",),
            ),
        ),
        reason_codes=("missing_recommendation_sources",),
        max_edge_spread=Decimal("0.020000"),
        max_score_spread=Decimal("0.050000"),
        min_source_count=2,
    )


def _row_values(row: object) -> dict[str, object]:
    return dict(row.__dict__)


def _canonical_payload_sha256(payload_json: dict[str, object]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("DB payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def test_consistency_db_row_serializes_canonical_payload_and_round_trips():
    codec = _codec_module()
    report = _report()

    row = codec.to_db_row(report)

    assert type(row) is codec.PaperRecommendationConsistencyDbRow
    assert len(row.report_sha256) == 64
    assert row.report_sha256 == row.report_sha256.lower()
    assert row.generated_at == GENERATED_AT
    assert row.config_version == "recommendation-consistency-v1"
    assert row.consistency_status == "watch"
    assert row.reason_codes_json == ["missing_recommendation_sources"]
    assert row.group_count == 2
    assert row.pass_count == 1
    assert row.watch_count == 1
    assert row.blocked_count == 0
    assert row.max_edge_spread == Decimal("0.020000")
    assert row.max_score_spread == Decimal("0.050000")
    assert row.min_source_count == 2
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.payload_json["generated_at"] == "2026-06-21T15:30:00+00:00"
    assert row.payload_json["max_edge_spread"] == "0.020000"
    assert row.payload_json["max_score_spread"] == "0.050000"
    assert row.payload_json["consistency_rows"][0]["edge_min"] == "0.100000"
    assert row.payload_json["consistency_rows"][0]["score_spread"] == "0.025000"
    assert row.payload_json["paper_only"] is True
    assert row.payload_json["report_only"] is True
    assert row.payload_json["readonly"] is True
    _assert_no_floats(row.payload_json)

    assert row.report_sha256 == _canonical_payload_sha256(row.payload_json)
    assert codec.from_db_row(row) == report
    assert codec.paper_recommendation_consistency_to_db_row(report) == row
    assert codec.paper_recommendation_consistency_from_db_row(row) == report


def test_consistency_db_row_normalizes_generated_at_to_utc_in_row_and_payload():
    codec = _codec_module()
    report = _report()
    naive_generated_at = datetime(2026, 6, 21, 15, 30)
    object.__setattr__(report, "generated_at", naive_generated_at)

    row = codec.to_db_row(report)

    assert row.generated_at == GENERATED_AT
    assert row.payload_json["generated_at"] == "2026-06-21T15:30:00+00:00"
    assert codec.from_db_row(row).generated_at == GENERATED_AT


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("max_edge_spread", "0.020000"),
        ("max_score_spread", 0.05),
    ),
)
def test_consistency_db_row_requires_materialized_decimal_fields_to_be_raw_decimals(
    field_name: str,
    value: object,
):
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=field_name):
        codec.PaperRecommendationConsistencyDbRow(
            **{**_row_values(row), field_name: value},
        )


def test_consistency_db_row_rejects_raw_runtime_payload_values():
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload_json = {**row.payload_json, "generated_at": GENERATED_AT}

    with pytest.raises(ValueError, match="payload_json"):
        codec.PaperRecommendationConsistencyDbRow(
            **{**_row_values(row), "payload_json": payload_json},
        )


def test_consistency_db_row_redacts_secret_like_payload_values():
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload_json = {
        **row.payload_json,
        "audit_metadata": {
            "supabase_url": "http://localhost:54321",
            "supabase_service_role_key": "secret-service-role",
            "postgres_password": "secret-password",
        },
    }
    redacted_payload_json = {
        **row.payload_json,
        "audit_metadata": {
            "supabase_url": "http://localhost:54321",
            "supabase_service_role_key": "[REDACTED]",
            "postgres_password": "[REDACTED]",
        },
    }

    sanitized = codec.PaperRecommendationConsistencyDbRow(
        **{
            **_row_values(row),
            "report_sha256": _canonical_payload_sha256(redacted_payload_json),
            "payload_json": payload_json,
        },
    )

    assert sanitized.payload_json["audit_metadata"] == redacted_payload_json[
        "audit_metadata"
    ]
    assert "secret" not in json.dumps(sanitized.payload_json).lower()


@pytest.mark.parametrize(
    "storage_value",
    (
        "https://project.supabase.co",
        "http://localhost.evil.com/project.supabase.co",
        "postgres://user:pass@db.example.com:5432/postgres",
        "postgres://localhost.evil.com/db",
    ),
)
def test_consistency_db_row_rejects_remote_supabase_and_postgres_payload_assumptions(
    storage_value: str,
):
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload_json = {**row.payload_json, "storage_assumption": storage_value}

    with pytest.raises(ValueError, match="local|Supabase|Postgres"):
        codec.PaperRecommendationConsistencyDbRow(
            **{
                **_row_values(row),
                "report_sha256": _canonical_payload_sha256(payload_json),
                "payload_json": payload_json,
            },
        )


@pytest.mark.parametrize(
    "storage_value",
    (
        "http://localhost:54321/project.supabase.local",
        "http://127.0.0.1:54321/project.supabase.local",
        "postgres://localhost:5432/postgres",
        "postgresql://127.0.0.1:5432/postgres",
    ),
)
def test_consistency_db_row_accepts_local_supabase_and_postgres_payload_assumptions(
    storage_value: str,
):
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload_json = {**row.payload_json, "storage_assumption": storage_value}

    sanitized = codec.PaperRecommendationConsistencyDbRow(
        **{
            **_row_values(row),
            "report_sha256": _canonical_payload_sha256(payload_json),
            "payload_json": payload_json,
        },
    )

    assert sanitized.payload_json["storage_assumption"] == storage_value


def test_consistency_db_row_hash_is_deterministic_for_equivalent_reports():
    codec = _codec_module()
    report = _report()
    same_report = PaperRecommendationConsistencyReport(**report.__dict__)
    different_report = PaperRecommendationConsistencyReport(
        **{**report.__dict__, "config_version": "recommendation-consistency-v2"},
    )

    first = codec.to_db_row(report)
    second = codec.to_db_row(same_report)
    third = codec.to_db_row(different_report)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_consistency_db_row_is_frozen():
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_consistency_db_row_rejects_wrong_report_types_and_subclasses():
    codec = _codec_module()

    with pytest.raises(ValueError, match="PaperRecommendationConsistencyReport"):
        codec.to_db_row(object())

    report = _report()
    with pytest.raises(ValueError, match="PaperRecommendationConsistencyReport"):
        codec.to_db_row(ConsistencyReportSubclass(**report.__dict__))


def test_consistency_db_row_rejects_wrong_row_types_and_subclasses():
    codec = _codec_module()
    row = codec.to_db_row(_report())

    class ConsistencyDbRowSubclass(codec.PaperRecommendationConsistencyDbRow):
        pass

    with pytest.raises(ValueError, match="PaperRecommendationConsistencyDbRow"):
        codec.from_db_row(object())
    with pytest.raises(ValueError, match="PaperRecommendationConsistencyDbRow"):
        codec.from_db_row(ConsistencyDbRowSubclass(**_row_values(row)))


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_consistency_db_row_rejects_false_report_flags_before_write(
    flag_name: str,
):
    codec = _codec_module()
    report = _report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)


def test_consistency_db_row_rejects_corrupted_stored_payload_flags_on_construction():
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload = {
        **row.payload_json,
        "nested_audit": {
            "paper_only": True,
            "report_only": True,
            "readonly": False,
        },
    }

    with pytest.raises(ValueError, match="readonly"):
        codec.PaperRecommendationConsistencyDbRow(
            **{
                **_row_values(row),
                "report_sha256": _canonical_payload_sha256(payload),
                "payload_json": payload,
            },
        )


def test_consistency_from_db_row_rejects_bypassed_corrupted_payload_flags():
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload = {
        **row.payload_json,
        "nested_audit": {
            "paper_only": True,
            "report_only": True,
            "readonly": False,
        },
    }
    malformed = object.__new__(codec.PaperRecommendationConsistencyDbRow)
    for key, value in {
        **_row_values(row),
        "report_sha256": _canonical_payload_sha256(payload),
        "payload_json": payload,
    }.items():
        object.__setattr__(malformed, key, value)

    with pytest.raises(ValueError, match="readonly"):
        codec.from_db_row(malformed)


def test_consistency_db_row_rejects_floats_in_json_payloads():
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="payload_json"):
        codec.PaperRecommendationConsistencyDbRow(
            **{
                **_row_values(row),
                "payload_json": {**row.payload_json, "bad_float": 0.1},
            },
        )


def test_consistency_db_row_rejects_malformed_stored_payload():
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload = {
        key: value
        for key, value in row.payload_json.items()
        if key != "reason_codes"
    }

    with pytest.raises(ValueError, match="payload_json"):
        codec.PaperRecommendationConsistencyDbRow(
            **{
                **_row_values(row),
                "report_sha256": _canonical_payload_sha256(payload),
                "payload_json": payload,
            },
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 21, 15, 31, tzinfo=UTC)}, "generated_at"),
        ({"config_version": "recommendation-consistency-v2"}, "config_version"),
        ({"consistency_status": "blocked"}, "consistency_status"),
        ({"reason_codes_json": ["recommendation_status_disagreement"]}, "reason_codes"),
        ({"group_count": 3}, "group_count"),
        ({"pass_count": 2}, "pass_count"),
        ({"watch_count": 0}, "watch_count"),
        ({"blocked_count": 1}, "blocked_count"),
        ({"max_edge_spread": Decimal("0.030000")}, "max_edge_spread"),
        ({"max_score_spread": Decimal("0.060000")}, "max_score_spread"),
        ({"min_source_count": 3}, "min_source_count"),
    ),
)
def test_consistency_db_row_rejects_materialized_payload_mismatches_on_construction(
    overrides: dict[str, object],
    message: str,
):
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperRecommendationConsistencyDbRow(
            **{**_row_values(row), **overrides},
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_consistency_db_row_rejects_top_level_payload_flag_mismatches_on_construction(
    flag_name: str,
):
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload = {**row.payload_json, flag_name: False}

    with pytest.raises(ValueError, match=flag_name):
        codec.PaperRecommendationConsistencyDbRow(
            **{
                **_row_values(row),
                "report_sha256": _canonical_payload_sha256(payload),
                "payload_json": payload,
            },
        )


def test_consistency_from_db_row_defends_against_bypassed_malformed_row():
    codec = _codec_module()
    row = codec.to_db_row(_report())
    malformed = object.__new__(codec.PaperRecommendationConsistencyDbRow)
    for field_name, value in _row_values(row).items():
        object.__setattr__(malformed, field_name, value)
    object.__setattr__(malformed, "report_sha256", "b" * 64)

    with pytest.raises(ValueError, match="report_sha256"):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "bad"}, "report_sha256"),
        ({"consistency_status": "selected"}, "consistency_status"),
        ({"reason_codes_json": []}, "reason_codes_json"),
        ({"group_count": True}, "group_count"),
        ({"max_edge_spread": 0.02}, "max_edge_spread"),
        ({"max_score_spread": Decimal("0.0500001")}, "max_score_spread"),
        ({"min_source_count": 0}, "min_source_count"),
        ({"paper_only": False}, "paper_only"),
    ),
)
def test_consistency_db_row_validates_row_shape(
    overrides: dict[str, object],
    message: str,
):
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperRecommendationConsistencyDbRow(
            **{**_row_values(row), **overrides},
        )


def test_consistency_db_row_module_is_pure_evidence_codec():
    _codec_module()
    source = Path(
        "src/polymarket_alpha_lab/paper_recommendation_consistency_db_row.py",
    ).read_text(encoding="utf-8")

    for banned in (
        "psycopg",
        "network",
        "auth",
        "wallet",
        "private_key",
        "signing",
        "submission",
        "cancellation",
        "replacement",
        "live_trading",
    ):
        assert banned not in source.lower()

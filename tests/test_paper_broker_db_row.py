from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import importlib
import json

import pytest

from polymarket_alpha_lab.paper_broker import PaperBrokerExecutionRecord


GENERATED_AT = datetime(2026, 6, 25, 10, 30, tzinfo=UTC)
CONFIG_VERSION = "paper-broker-db-test-v0"


def d(value: str) -> Decimal:
    return Decimal(value)


def _codec():
    try:
        return importlib.import_module("polymarket_alpha_lab.paper_broker_db_row")
    except ModuleNotFoundError as exc:
        pytest.fail(f"codec module missing: {exc}")


def _record() -> PaperBrokerExecutionRecord:
    return PaperBrokerExecutionRecord(
        generated_at=GENERATED_AT,
        config_version=CONFIG_VERSION,
        execution_status="paper_submitted",
        recommended_next_step="route_to_paper_order_lifecycle",
        source_gate_status="pass",
        source_proposal_count=2,
        source_proposal_total_notional=d("42.500000"),
        execution_notional=d("42.500000"),
        reason_codes=("paper_broker_execution_submitted",),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _unchecked_record(**overrides: object) -> PaperBrokerExecutionRecord:
    values = dict(_record().__dict__)
    values.update(overrides)
    record = object.__new__(PaperBrokerExecutionRecord)
    for name, value in values.items():
        object.__setattr__(record, name, value)
    return record


def _row_values(row: object) -> dict[str, object]:
    return dict(row.__dict__)


def _unchecked_row(row: object, **overrides: object) -> object:
    values = _row_values(row)
    values.update(overrides)
    unchecked = object.__new__(type(row))
    for name, value in values.items():
        object.__setattr__(unchecked, name, value)
    return unchecked


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("DB payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def _canonical_payload_sha256(payload_json: dict[str, object]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def test_broker_execution_db_row_serializes_canonical_payload_and_round_trips() -> None:
    codec = _codec()
    record = _record()

    row = codec.paper_broker_execution_record_to_db_row(record)

    assert type(row) is codec.PaperBrokerExecutionDbRow
    assert len(row.record_sha256) == 64
    assert row.record_sha256 == row.record_sha256.lower()
    assert row.generated_at == GENERATED_AT
    assert row.config_version == CONFIG_VERSION
    assert row.execution_status == "paper_submitted"
    assert row.recommended_next_step == "route_to_paper_order_lifecycle"
    assert row.source_gate_status == "pass"
    assert row.source_proposal_count == 2
    assert row.source_proposal_total_notional == d("42.500000")
    assert row.execution_notional == d("42.500000")
    assert row.reason_codes_json == ["paper_broker_execution_submitted"]
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.payload_json == {
        "generated_at": "2026-06-25T10:30:00+00:00",
        "config_version": CONFIG_VERSION,
        "execution_status": "paper_submitted",
        "recommended_next_step": "route_to_paper_order_lifecycle",
        "source_gate_status": "pass",
        "source_proposal_count": 2,
        "source_proposal_total_notional": "42.500000",
        "execution_notional": "42.500000",
        "reason_codes": ["paper_broker_execution_submitted"],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    _assert_no_floats(row.payload_json)
    assert row.record_sha256 == _canonical_payload_sha256(row.payload_json)
    assert codec.paper_broker_execution_record_from_db_row(row) == record
    assert codec.to_db_row(record) == row
    assert codec.from_db_row(row) == record


def test_broker_execution_db_row_hash_is_deterministic_over_full_payload() -> None:
    codec = _codec()
    record = _record()
    same_record = PaperBrokerExecutionRecord(**record.__dict__)
    changed_record = PaperBrokerExecutionRecord(
        **{
            **record.__dict__,
            "config_version": "paper-broker-db-test-v1",
        },
    )

    first = codec.to_db_row(record)
    second = codec.to_db_row(same_record)
    third = codec.to_db_row(changed_record)

    assert first.record_sha256 == second.record_sha256
    assert first.payload_json == second.payload_json
    assert first.record_sha256 != third.record_sha256


def test_broker_execution_db_row_is_frozen() -> None:
    codec = _codec()
    row = codec.to_db_row(_record())

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_broker_execution_db_row_rejects_wrong_record_types_and_subclasses() -> None:
    codec = _codec()

    class DuckRecord:
        def __init__(self, record: PaperBrokerExecutionRecord) -> None:
            self.__dict__.update(record.__dict__)

    with pytest.raises(ValueError, match="PaperBrokerExecutionRecord"):
        codec.to_db_row(DuckRecord(_record()))

    with pytest.raises(TypeError, match="does not support subclassing"):

        class BrokerExecutionRecordSubclass(PaperBrokerExecutionRecord):
            pass


def test_broker_execution_db_row_rejects_wrong_row_types_and_subclasses() -> None:
    codec = _codec()
    row = codec.to_db_row(_record())

    class BrokerExecutionDbRowSubclass(codec.PaperBrokerExecutionDbRow):
        pass

    with pytest.raises(ValueError, match="PaperBrokerExecutionDbRow"):
        codec.from_db_row(object())
    with pytest.raises(ValueError, match="PaperBrokerExecutionDbRow"):
        codec.from_db_row(BrokerExecutionDbRowSubclass(**_row_values(row)))


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_broker_execution_db_row_rejects_false_record_flags_before_write(
    flag_name: str,
) -> None:
    codec = _codec()
    record = _unchecked_record(**{flag_name: False})

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(record)


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_broker_execution_db_row_rejects_false_row_flags(flag_name: str) -> None:
    codec = _codec()
    row = codec.to_db_row(_record())

    with pytest.raises(ValueError, match=flag_name):
        codec.PaperBrokerExecutionDbRow(**{**_row_values(row), flag_name: False})


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_broker_execution_db_row_rejects_false_payload_flags(flag_name: str) -> None:
    codec = _codec()
    row = codec.to_db_row(_record())
    payload = {**row.payload_json, flag_name: False}

    with pytest.raises(ValueError, match=flag_name):
        codec.PaperBrokerExecutionDbRow(
            **{
                **_row_values(row),
                "record_sha256": _canonical_payload_sha256(payload),
                "payload_json": payload,
            },
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_broker_execution_db_row_rejects_missing_payload_flags(flag_name: str) -> None:
    codec = _codec()
    row = codec.to_db_row(_record())
    payload = dict(row.payload_json)
    del payload[flag_name]

    with pytest.raises(ValueError, match=flag_name):
        codec.PaperBrokerExecutionDbRow(
            **{
                **_row_values(row),
                "record_sha256": _canonical_payload_sha256(payload),
                "payload_json": payload,
            },
        )


def test_broker_execution_db_row_rejects_payload_without_hard_flags() -> None:
    codec = _codec()
    row = codec.to_db_row(_record())
    payload = {
        key: value
        for key, value in row.payload_json.items()
        if key not in {"paper_only", "report_only", "readonly"}
    }

    with pytest.raises(ValueError, match="paper_only"):
        codec.PaperBrokerExecutionDbRow(
            **{
                **_row_values(row),
                "record_sha256": _canonical_payload_sha256(payload),
                "payload_json": payload,
            },
        )


def test_broker_execution_db_row_rejects_recursive_payload_floats() -> None:
    codec = _codec()
    row = codec.to_db_row(_record())
    payload = {
        **row.payload_json,
        "debug_extra": {"nested": [{"bad_float": 0.1}]},
    }

    with pytest.raises(ValueError, match="float"):
        codec.PaperBrokerExecutionDbRow(
            **{
                **_row_values(row),
                "record_sha256": _canonical_payload_sha256(payload),
                "payload_json": payload,
            },
        )


def test_broker_execution_db_row_constructor_rejects_noncanonical_recovered_payload() -> None:
    codec = _codec()
    row = codec.to_db_row(_record())
    payload = {
        **row.payload_json,
        "source_proposal_total_notional": "42.5000000",
        "execution_notional": "42.5000000",
    }

    with pytest.raises(ValueError, match="canonical|record_sha256"):
        codec.PaperBrokerExecutionDbRow(
            **{
                **_row_values(row),
                "record_sha256": row.record_sha256,
                "payload_json": payload,
            },
        )


def test_broker_execution_from_db_row_rejects_unchecked_raw_hash_bypass() -> None:
    codec = _codec()
    row = codec.to_db_row(_record())
    payload = {
        **row.payload_json,
        "source_proposal_total_notional": "42.5000000",
        "execution_notional": "42.5000000",
    }
    unchecked = _unchecked_row(
        row,
        record_sha256=row.record_sha256,
        payload_json=payload,
    )

    with pytest.raises(ValueError, match="payload_json must be canonical|record_sha256"):
        codec.from_db_row(unchecked)


@pytest.mark.parametrize(
    ("overrides", "payload_updates", "expected_field"),
    (
        ({"record_sha256": "b" * 64}, {}, "record_sha256"),
        ({}, {"config_version": "paper-broker-db-test-v1"}, "config_version"),
        ({}, {"execution_notional": "42.500001"}, "execution_notional"),
        (
            {"source_proposal_total_notional": d("42.5000000")},
            {},
            "source_proposal_total_notional",
        ),
        ({"execution_notional": d("42.5000000")}, {}, "execution_notional"),
        (
            {"reason_codes_json": ["paper_broker_execution_alternate"]},
            {},
            "reason_codes_json",
        ),
        ({"paper_only": False}, {}, "paper_only"),
        ({"report_only": False}, {}, "report_only"),
        ({"readonly": False}, {}, "readonly"),
    ),
)
def test_broker_execution_db_row_constructor_rejects_materialized_field_mismatches(
    overrides: dict[str, object],
    payload_updates: dict[str, object],
    expected_field: str,
) -> None:
    codec = _codec()
    row = codec.to_db_row(_record())
    payload = {**row.payload_json, **payload_updates}
    values = {
        **_row_values(row),
        "record_sha256": _canonical_payload_sha256(payload),
        "payload_json": payload,
        **overrides,
    }

    with pytest.raises(ValueError, match=expected_field):
        codec.PaperBrokerExecutionDbRow(**values)


@pytest.mark.parametrize(
    ("changes", "payload_updates", "expected_field"),
    (
        ({"record_sha256": "b" * 64}, {}, "record_sha256"),
        ({}, {"config_version": "paper-broker-db-test-v1"}, "config_version"),
        ({}, {"execution_notional": "42.500001"}, "execution_notional"),
        (
            {"source_proposal_total_notional": d("42.5000000")},
            {},
            "source_proposal_total_notional",
        ),
        ({"execution_notional": d("42.5000000")}, {}, "execution_notional"),
        (
            {"reason_codes_json": ["paper_broker_execution_alternate"]},
            {},
            "reason_codes_json",
        ),
        ({"paper_only": False}, {}, "paper_only"),
        ({"report_only": False}, {}, "report_only"),
        ({"readonly": False}, {}, "readonly"),
    ),
)
def test_broker_execution_db_row_replace_rejects_materialized_field_mismatches(
    changes: dict[str, object],
    payload_updates: dict[str, object],
    expected_field: str,
) -> None:
    codec = _codec()
    row = codec.to_db_row(_record())
    if payload_updates:
        payload = {**row.payload_json, **payload_updates}
        changes = {
            **changes,
            "record_sha256": _canonical_payload_sha256(payload),
            "payload_json": payload,
        }

    with pytest.raises(ValueError, match=expected_field):
        replace(row, **changes)


@pytest.mark.parametrize(
    ("overrides", "payload_updates", "expected_field"),
    (
        ({"record_sha256": "b" * 64}, {}, "record_sha256"),
        ({}, {"config_version": "paper-broker-db-test-v1"}, "config_version"),
        ({}, {"execution_notional": "42.500001"}, "execution_notional"),
        (
            {"source_proposal_total_notional": d("42.5000000")},
            {},
            "source_proposal_total_notional",
        ),
        ({"execution_notional": d("42.5000000")}, {}, "execution_notional"),
        (
            {"reason_codes_json": ["paper_broker_execution_alternate"]},
            {},
            "reason_codes_json",
        ),
        ({"paper_only": False}, {}, "paper_only"),
        ({"report_only": False}, {}, "report_only"),
        ({"readonly": False}, {}, "readonly"),
    ),
)
def test_broker_execution_from_db_row_rejects_unchecked_materialized_field_mismatches(
    overrides: dict[str, object],
    payload_updates: dict[str, object],
    expected_field: str,
) -> None:
    codec = _codec()
    row = codec.to_db_row(_record())
    payload = {**row.payload_json, **payload_updates}
    unchecked_overrides = {
        "record_sha256": _canonical_payload_sha256(payload),
        "payload_json": payload,
        **overrides,
    }
    unchecked = _unchecked_row(
        row,
        **unchecked_overrides,
    )

    with pytest.raises(ValueError, match=expected_field):
        codec.from_db_row(unchecked)


def test_broker_execution_db_row_rejects_invalid_decimal_json_on_readback() -> None:
    codec = _codec()
    row = codec.to_db_row(_record())
    payload = {**row.payload_json, "execution_notional": 42.5}

    with pytest.raises(ValueError, match="float"):
        codec.PaperBrokerExecutionDbRow(
            **{
                **_row_values(row),
                "record_sha256": _canonical_payload_sha256(payload),
                "payload_json": payload,
            },
        )


def test_broker_execution_db_row_exports_public_codec_api() -> None:
    codec = _codec()

    assert set(codec.__all__) == {
        "PaperBrokerExecutionDbRow",
        "from_db_row",
        "paper_broker_execution_record_from_db_row",
        "paper_broker_execution_record_to_db_row",
        "to_db_row",
    }

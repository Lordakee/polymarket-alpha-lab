from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime, timedelta, timezone
import inspect
import re
from pathlib import Path
from typing import get_type_hints
from unittest.mock import Mock

import pytest

import polymarket_alpha_lab.crypto_btc_evidence_catalog as catalog_module
import polymarket_alpha_lab.crypto_btc_evidence_registry as registry_module
from polymarket_alpha_lab.crypto_btc_evidence_catalog import (
    CRYPTO_BTC_SOURCE_CATALOG_VERSION,
    CryptoBtcTrustedSourceRecord,
    resolve_trusted_crypto_btc_source_record,
    trusted_crypto_btc_source_catalog,
)

EXPECTED_CATALOG_VERSION = "crypto-btc-source-catalog-v0"
EXPECTED_REGISTRY_VERSION = "crypto-btc-approved-registry-v0"
APPROVED_SOURCE_IDS = (
    "btc_derivatives_reference",
    "btc_onchain_reference",
    "btc_resolution_rules",
    "btc_spot_reference",
)
PLAN_DATE_EVALUATED_AT = datetime(2026, 7, 13, 12, 0, 0, tzinfo=UTC)
EXPECTED_SOURCE_RECORD_IDS = {
    "btc_derivatives_reference": ("btc-derivatives-reference-v0",),
    "btc_onchain_reference": ("btc-onchain-reference-v0",),
    "btc_resolution_rules": ("btc-resolution-rules-v0",),
    "btc_spot_reference": ("btc-spot-reference-v0", "btc-spot-reference-v0-pre", "btc-spot-reference-v1"),
}
EXPECTED_RECORD_DIGESTS = {
    "btc-derivatives-reference-v0": "8241604321b517d68563e086e42afb2ac26c55aa97cdab3ea5f41cf21b1c605a",
    "btc-onchain-reference-v0": "9334b4deebb989435bd1302c223b185020cd225139b19bb56e919f5d3ab5d38e",
    "btc-resolution-rules-v0": "30d30f4091f28adbc4cc8cf61ad653f56985abca776ccc38e9887f78e223518e",
    "btc-spot-reference-v0": "5dc1fdbac0ffdd9bdcfb18f3e53d2f0ffdc4c151f026d5636550b6bcb7c023ac",
    "btc-spot-reference-v0-pre": "d0d87f164d28b261ccecd142e2414768ef858a8b913afdaecfcc7376a85ac52b",
    "btc-spot-reference-v1": "72a93cd9dbb94e6fd4d306ce44dfa7b12fae9ba1cfb020a572f0ad03d03019c8",
}
EXPECTED_SOURCE_FAMILIES = {
    "btc_derivatives_reference": "btc_derivatives",
    "btc_onchain_reference": "btc_onchain",
    "btc_resolution_rules": "btc_resolution_rules",
    "btc_spot_reference": "btc_spot",
}
EXPECTED_RELEASE_VINTAGES = {
    "btc-derivatives-reference-v0": "2026-h1",
    "btc-onchain-reference-v0": "2026-h1",
    "btc-resolution-rules-v0": "2026-h1",
    "btc-spot-reference-v0": "2026-h1",
    "btc-spot-reference-v0-pre": "2025-h2",
    "btc-spot-reference-v1": "2026-h2",
}
RECORD_FIELD_NAMES = (
    "source_id",
    "record_id",
    "record_digest",
    "source_family",
    "release_vintage",
    "catalog_version",
    "valid_from",
    "valid_until",
    "paper_only",
    "report_only",
    "readonly",
)
MODULE_PATH = Path(catalog_module.__file__)
FORBIDDEN_CALL_NAMES = frozenset(
    "breakpoint choice choices commit connect eval exec execute execute_many float fork "
    "getenv getrandbytes getrandbits globals input locals monotonic now open perf_counter "
    "popen print randrange read_bytes read_text rollback shuffle spawn system "
    "today total_seconds uniform urandom utcnow write_bytes write_text".split()
)
ALLOWED_IMPORT_ROOTS = frozenset(
    (
        "__future__",
        "dataclasses",
        "datetime",
        "re",
        "typing",
        "polymarket_alpha_lab.crypto_btc_evidence_registry",
    )
)


def _catalog_record(source_id: str, record_id: str) -> CryptoBtcTrustedSourceRecord:
    for record in trusted_crypto_btc_source_catalog():
        if record.source_id == source_id and record.record_id == record_id:
            return record
    raise AssertionError(f"catalog record not found: {source_id}/{record_id}")


def _pinned_record_kwargs() -> dict[str, object]:
    return dict(
        source_id="btc_spot_reference",
        record_id="btc-spot-reference-v0",
        record_digest=EXPECTED_RECORD_DIGESTS["btc-spot-reference-v0"],
        source_family="btc_spot",
        release_vintage="2026-h1",
        catalog_version=EXPECTED_CATALOG_VERSION,
        valid_from=datetime(2026, 1, 1, tzinfo=UTC),
        valid_until=datetime(2026, 12, 31, 23, 59, 59, tzinfo=UTC),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _active_records() -> tuple[CryptoBtcTrustedSourceRecord, ...]:
    return tuple(
        record
        for record in trusted_crypto_btc_source_catalog()
        if record.valid_from <= PLAN_DATE_EVALUATED_AT <= record.valid_until
    )


def test_public_surface_matches_pinned_interface() -> None:
    assert catalog_module.__all__ == (
        "CryptoBtcTrustedSourceRecord",
        "trusted_crypto_btc_source_catalog",
        "resolve_trusted_crypto_btc_source_record",
    )
    assert catalog_module.CRYPTO_BTC_SOURCE_CATALOG_VERSION == "crypto-btc-source-catalog-v0"
    factory_signature = inspect.signature(trusted_crypto_btc_source_catalog)
    assert list(factory_signature.parameters) == []
    factory_return = str(get_type_hints(trusted_crypto_btc_source_catalog)["return"])
    assert factory_return.startswith("tuple")
    assert "CryptoBtcTrustedSourceRecord" in factory_return
    resolve_signature = inspect.signature(resolve_trusted_crypto_btc_source_record)
    assert list(resolve_signature.parameters) == [
        "source_id",
        "record_id",
        "record_digest",
        "evaluated_at",
    ]
    for override_field in ("release_vintage", "trust_tier", "source_family", "catalog_version"):
        assert override_field not in resolve_signature.parameters
    assert resolve_signature.parameters["evaluated_at"].kind is inspect.Parameter.KEYWORD_ONLY
    resolve_hints = get_type_hints(resolve_trusted_crypto_btc_source_record)
    assert resolve_hints["return"] is CryptoBtcTrustedSourceRecord
    assert resolve_hints["evaluated_at"] is datetime
    record = _catalog_record("btc_spot_reference", "btc-spot-reference-v0")
    with pytest.raises(TypeError):
        resolve_trusted_crypto_btc_source_record(
            record.source_id,
            record.record_id,
            record.record_digest,
            evaluated_at=PLAN_DATE_EVALUATED_AT,
            release_vintage="2027-h1",
        )
    with pytest.raises(TypeError):
        resolve_trusted_crypto_btc_source_record(
            record.source_id,
            record.record_id,
            record.record_digest,
            evaluated_at=PLAN_DATE_EVALUATED_AT,
            trust_tier="proxy",
        )


def test_record_dataclass_is_frozen_slotted_and_final() -> None:
    params = CryptoBtcTrustedSourceRecord.__dataclass_params__
    assert params.frozen is True
    assert params.slots is True
    assert [field.name for field in fields(CryptoBtcTrustedSourceRecord)] == list(RECORD_FIELD_NAMES)
    record = _catalog_record("btc_resolution_rules", "btc-resolution-rules-v0")
    assert not hasattr(record, "__dict__")
    with pytest.raises(FrozenInstanceError):
        record.release_vintage = "2027-h1"  # type: ignore[misc]
    with pytest.raises(TypeError):
        class _TamperedRecord(CryptoBtcTrustedSourceRecord):  # type: ignore[misc]
            pass


def test_hard_flags_are_exact_true() -> None:
    for record in trusted_crypto_btc_source_catalog():
        assert record.paper_only is True
        assert record.report_only is True
        assert record.readonly is True
    for flag in ("paper_only", "report_only", "readonly"):
        for bad in (False, 1, "true", None):
            with pytest.raises(ValueError):
                CryptoBtcTrustedSourceRecord(**{**_pinned_record_kwargs(), flag: bad})


def test_catalog_version_is_exact_pinned_constant() -> None:
    assert CRYPTO_BTC_SOURCE_CATALOG_VERSION == "crypto-btc-source-catalog-v0"
    for record in trusted_crypto_btc_source_catalog():
        assert record.catalog_version == EXPECTED_CATALOG_VERSION
    for bad_version in ("crypto-btc-source-catalog-v1", None, 0):
        with pytest.raises(ValueError):
            CryptoBtcTrustedSourceRecord(
                **{**_pinned_record_kwargs(), "catalog_version": bad_version}
            )


def test_factory_returns_frozen_sorted_tuple_and_takes_no_arguments() -> None:
    with pytest.raises(TypeError):
        trusted_crypto_btc_source_catalog("caller-supplied")  # type: ignore[arg-type]
    catalog = trusted_crypto_btc_source_catalog()
    assert type(catalog) is tuple
    assert catalog == trusted_crypto_btc_source_catalog()
    for record in catalog:
        assert type(record) is CryptoBtcTrustedSourceRecord
    assert catalog == tuple(
        sorted(catalog, key=lambda record: (record.source_id, record.record_id))
    )
    record_keys = [(record.source_id, record.record_id) for record in catalog]
    assert len(set(record_keys)) == len(record_keys)
    digests = [record.record_digest for record in catalog]
    assert len(set(digests)) == len(digests)


def test_catalog_covers_every_approved_source_and_matches_registry_families() -> None:
    approved = registry_module.approved_crypto_btc_source_registry()
    assert set(source.source_id for source in approved) == set(APPROVED_SOURCE_IDS)
    catalog = trusted_crypto_btc_source_catalog()
    for source in approved:
        assert source.registry_version == EXPECTED_REGISTRY_VERSION
        records = [record for record in catalog if record.source_id == source.source_id]
        assert records, f"approved source missing catalog records: {source.source_id}"
        for record in records:
            assert record.source_family == source.source_family


def test_record_inventory_is_pinned() -> None:
    catalog = trusted_crypto_btc_source_catalog()
    for source_id in APPROVED_SOURCE_IDS:
        record_ids = tuple(
            record.record_id for record in catalog if record.source_id == source_id
        )
        assert record_ids == EXPECTED_SOURCE_RECORD_IDS[source_id]
    for record in catalog:
        assert record.source_id in APPROVED_SOURCE_IDS
        assert record.source_family == EXPECTED_SOURCE_FAMILIES[record.source_id]
        assert record.release_vintage == EXPECTED_RELEASE_VINTAGES[record.record_id]
        assert record.record_digest == EXPECTED_RECORD_DIGESTS[record.record_id]
        assert record.valid_from < record.valid_until
        assert record.valid_from.tzinfo is not None
        assert record.valid_until.tzinfo is not None


def test_record_validity_windows_are_pinned_utc_bounds() -> None:
    spot_v0 = _catalog_record("btc_spot_reference", "btc-spot-reference-v0")
    assert spot_v0.valid_from == datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
    assert spot_v0.valid_until == datetime(2026, 9, 30, 23, 59, 59, tzinfo=UTC)
    spot_v1 = _catalog_record("btc_spot_reference", "btc-spot-reference-v1")
    assert spot_v1.valid_from == datetime(2026, 10, 1, 0, 0, 0, tzinfo=UTC)
    assert spot_v1.valid_until == datetime(2026, 12, 31, 23, 59, 59, tzinfo=UTC)
    legacy = _catalog_record("btc_spot_reference", "btc-spot-reference-v0-pre")
    assert legacy.valid_from == datetime(2025, 7, 1, 0, 0, 0, tzinfo=UTC)
    assert legacy.valid_until == datetime(2025, 12, 31, 23, 59, 59, tzinfo=UTC)
    for record_id in (
        "btc-derivatives-reference-v0",
        "btc-onchain-reference-v0",
        "btc-resolution-rules-v0",
    ):
        source_id = next(
            source for source, ids in EXPECTED_SOURCE_RECORD_IDS.items() if record_id in ids
        )
        record = _catalog_record(source_id, record_id)
        assert record.valid_from == datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
        assert record.valid_until == datetime(2026, 12, 31, 23, 59, 59, tzinfo=UTC)


def test_resolve_succeeds_within_window_for_every_active_record() -> None:
    active = _active_records()
    assert len(active) >= 4
    for record in active:
        resolved = resolve_trusted_crypto_btc_source_record(
            record.source_id,
            record.record_id,
            record.record_digest,
            evaluated_at=PLAN_DATE_EVALUATED_AT,
        )
        assert resolved == record
        assert resolved.release_vintage == record.release_vintage
        assert resolved.source_family == record.source_family
        assert resolved.catalog_version == EXPECTED_CATALOG_VERSION
    resolution_record = _catalog_record("btc_resolution_rules", "btc-resolution-rules-v0")
    assert (
        resolve_trusted_crypto_btc_source_record(
            resolution_record.source_id,
            resolution_record.record_id,
            resolution_record.record_digest,
            evaluated_at=PLAN_DATE_EVALUATED_AT,
        )
        == resolution_record
    )


def test_resolve_accepts_aware_non_utc_evaluated_at_normalized_to_utc() -> None:
    record = _catalog_record("btc_derivatives_reference", "btc-derivatives-reference-v0")
    shifted = PLAN_DATE_EVALUATED_AT.astimezone(timezone(timedelta(hours=-5)))
    assert (
        resolve_trusted_crypto_btc_source_record(
            record.source_id,
            record.record_id,
            record.record_digest,
            evaluated_at=shifted,
        )
        == record
    )


def test_resolve_window_bounds_are_inclusive() -> None:
    record = _catalog_record("btc_spot_reference", "btc-spot-reference-v0")
    for edge in (record.valid_from, record.valid_until):
        assert (
            resolve_trusted_crypto_btc_source_record(
                record.source_id,
                record.record_id,
                record.record_digest,
                evaluated_at=edge,
            )
            == record
        )
    with pytest.raises(ValueError, match="expired"):
        resolve_trusted_crypto_btc_source_record(
            record.source_id,
            record.record_id,
            record.record_digest,
            evaluated_at=record.valid_until + timedelta(microseconds=1),
        )
    with pytest.raises(ValueError, match="not yet valid"):
        resolve_trusted_crypto_btc_source_record(
            record.source_id,
            record.record_id,
            record.record_digest,
            evaluated_at=record.valid_from - timedelta(microseconds=1),
        )


def test_resolve_rejects_expired_and_not_yet_valid_catalog_records() -> None:
    legacy = _catalog_record("btc_spot_reference", "btc-spot-reference-v0-pre")
    with pytest.raises(ValueError, match="expired"):
        resolve_trusted_crypto_btc_source_record(
            legacy.source_id,
            legacy.record_id,
            legacy.record_digest,
            evaluated_at=PLAN_DATE_EVALUATED_AT,
        )
    future = _catalog_record("btc_spot_reference", "btc-spot-reference-v1")
    with pytest.raises(ValueError, match="not yet valid"):
        resolve_trusted_crypto_btc_source_record(
            future.source_id,
            future.record_id,
            future.record_digest,
            evaluated_at=PLAN_DATE_EVALUATED_AT,
        )


def test_resolve_rejects_unknown_source_id() -> None:
    record = _catalog_record("btc_spot_reference", "btc-spot-reference-v0")
    for bad_source in ("btc_nonsense", "", "BTC_SPOT_REFERENCE", "btc_spot_reference ", 7, None):
        with pytest.raises(ValueError):
            resolve_trusted_crypto_btc_source_record(
                bad_source,  # type: ignore[arg-type]
                record.record_id,
                record.record_digest,
                evaluated_at=PLAN_DATE_EVALUATED_AT,
            )


def test_resolve_rejects_unknown_record_id() -> None:
    record = _catalog_record("btc_onchain_reference", "btc-onchain-reference-v0")
    for bad_record in ("btc-onchain-reference-v9", "", "btc-derivatives-reference-v0", 3, None):
        with pytest.raises(ValueError):
            resolve_trusted_crypto_btc_source_record(
                record.source_id,
                bad_record,  # type: ignore[arg-type]
                record.record_digest,
                evaluated_at=PLAN_DATE_EVALUATED_AT,
            )


def test_resolve_rejects_digest_mismatch() -> None:
    record = _catalog_record("btc_onchain_reference", "btc-onchain-reference-v0")
    for bad_digest in (
        "0" * 64,
        record.record_digest.upper(),
        record.record_digest[:63],
        "deadbeef",
        "",
        42,
        None,
    ):
        with pytest.raises(ValueError, match="digest"):
            resolve_trusted_crypto_btc_source_record(
                record.source_id,
                record.record_id,
                bad_digest,  # type: ignore[arg-type]
                evaluated_at=PLAN_DATE_EVALUATED_AT,
            )


def test_resolve_rejects_source_family_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _catalog_record("btc_spot_reference", "btc-spot-reference-v0")
    drifted = Mock(
        spec=registry_module.CryptoBtcApprovedSource,
        source_id="btc_spot_reference",
        source_family="btc_onchain",
        trust_tier="primary",
        registry_version=EXPECTED_REGISTRY_VERSION,
    )
    monkeypatch.setattr(catalog_module, "require_approved_crypto_btc_source", lambda source_id: drifted)
    with pytest.raises(ValueError, match="family"):
        resolve_trusted_crypto_btc_source_record(
            record.source_id,
            record.record_id,
            record.record_digest,
            evaluated_at=PLAN_DATE_EVALUATED_AT,
        )


def test_resolve_rejects_registry_version_mismatch_from_registry_side(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _catalog_record("btc_derivatives_reference", "btc-derivatives-reference-v0")
    drifted = Mock(
        spec=registry_module.CryptoBtcApprovedSource,
        source_id="btc_derivatives_reference",
        source_family="btc_derivatives",
        trust_tier="primary",
        registry_version="crypto-btc-approved-registry-v9",
    )
    monkeypatch.setattr(catalog_module, "require_approved_crypto_btc_source", lambda source_id: drifted)
    with pytest.raises(ValueError, match="registry version"):
        resolve_trusted_crypto_btc_source_record(
            record.source_id,
            record.record_id,
            record.record_digest,
            evaluated_at=PLAN_DATE_EVALUATED_AT,
        )


def test_resolve_rejects_registry_version_mismatch_from_catalog_side(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _catalog_record("btc_onchain_reference", "btc-onchain-reference-v0")
    monkeypatch.setattr(catalog_module, "_REQUIRED_REGISTRY_VERSION", "crypto-btc-approved-registry-v9")
    with pytest.raises(ValueError, match="registry version"):
        resolve_trusted_crypto_btc_source_record(
            record.source_id,
            record.record_id,
            record.record_digest,
            evaluated_at=PLAN_DATE_EVALUATED_AT,
        )


def test_resolve_rejects_naive_or_invalid_evaluated_at() -> None:
    record = _catalog_record("btc_resolution_rules", "btc-resolution-rules-v0")
    for bad_moment in (
        datetime(2026, 7, 13, 12, 0, 0),
        "2026-07-13T12:00:00+00:00",
        None,
        1783934400,
    ):
        with pytest.raises(ValueError):
            resolve_trusted_crypto_btc_source_record(
                record.source_id,
                record.record_id,
                record.record_digest,
                evaluated_at=bad_moment,  # type: ignore[arg-type]
            )


def test_resolve_rejects_non_string_identity_arguments() -> None:
    record = _catalog_record("btc_spot_reference", "btc-spot-reference-v0")
    for bad_source, bad_record, bad_digest in (
        (7, record.record_id, record.record_digest),
        (record.source_id, b"btc-spot-reference-v0", record.record_digest),
        (record.source_id, record.record_id, bytearray(64)),
    ):
        with pytest.raises(ValueError):
            resolve_trusted_crypto_btc_source_record(
                bad_source,  # type: ignore[arg-type]
                bad_record,  # type: ignore[arg-type]
                bad_digest,  # type: ignore[arg-type]
                evaluated_at=PLAN_DATE_EVALUATED_AT,
            )


def test_record_construction_validates_every_field() -> None:
    for field in ("source_id", "record_id", "source_family", "release_vintage"):
        for bad in ("", "-leading", "trailing-", "UPPER", "a" * 161, 5, None):
            with pytest.raises(ValueError):
                CryptoBtcTrustedSourceRecord(**{**_pinned_record_kwargs(), field: bad})
    for bad_digest in ("Z" * 64, "a" * 63, "g" * 64, 5, None):
        with pytest.raises(ValueError):
            CryptoBtcTrustedSourceRecord(
                **{**_pinned_record_kwargs(), "record_digest": bad_digest}
            )
    for field in ("valid_from", "valid_until"):
        with pytest.raises(ValueError):
            CryptoBtcTrustedSourceRecord(**{**_pinned_record_kwargs(), field: datetime(2026, 1, 1)})
    pinned = _pinned_record_kwargs()
    with pytest.raises(ValueError):
        CryptoBtcTrustedSourceRecord(**{**pinned, "valid_until": pinned["valid_from"]})
    with pytest.raises(ValueError):
        CryptoBtcTrustedSourceRecord(
            **{**pinned, "valid_until": pinned["valid_from"] - timedelta(days=1)}
        )
    built = CryptoBtcTrustedSourceRecord(**pinned)
    twin = CryptoBtcTrustedSourceRecord(**_pinned_record_kwargs())
    assert built == twin
    assert hash(built) == hash(twin)
    shifted_until = datetime(2026, 12, 31, 18, 59, 59, tzinfo=timezone(timedelta(hours=-5)))
    assert built == CryptoBtcTrustedSourceRecord(
        **{**_pinned_record_kwargs(), "valid_until": shifted_until}
    )


def test_module_import_allowlist_and_source_purity() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    allowed_calls = {"compile"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                assert root in ALLOWED_IMPORT_ROOTS or alias.name in ALLOWED_IMPORT_ROOTS
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "") in ALLOWED_IMPORT_ROOTS
        elif isinstance(node, ast.Call):
            name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            assert name in allowed_calls or name not in FORBIDDEN_CALL_NAMES, name
        elif isinstance(node, ast.Constant):
            assert not isinstance(node.value, float)
    for name in catalog_module.__all__:
        assert hasattr(catalog_module, name)


def test_module_has_no_forbidden_surface_tokens() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    forbidden_tokens = re.compile(
        r"(?<![A-Za-z0-9_])(?:float\(|utcnow\(|localtime\(|supabase\.|psycopg\.|"
        r"sqlite3\.|aiohttp\.|requests\.|httpx\.|socket\.|subprocess\.|os\.environ|"
        r"getenv\(|open\(|__import__\(|eval\(|exec\(|random\.)(?![A-Za-z0-9_])"
    )
    match = forbidden_tokens.search(source)
    assert match is None, match.group(0) if match else None
    assert "hash(" not in source

"""Trusted source-record catalog for the crypto BTC evidence policy.

This module owns the review-pinned trusted BTC source records: record
identity and digest, source family, trusted release vintage, the fixed
catalog version, and explicit UTC validity windows. The catalog is a
pure, deterministic, in-code tuple: callers may only name an approved
source ID and a trusted record ID/digest. Callers can never supply
catalog content, promote a proxy source to trusted, or override
release-vintage metadata, because no public callable accepts catalog
entries, families, vintages, or trust tiers.

``resolve_trusted_crypto_btc_source_record`` fails closed on every
mismatch path:

- an unknown or unapproved source ID raises ``ValueError``;
- a registry version that does not match the catalog-required registry
  version raises ``ValueError``;
- an unknown record ID for the approved source raises ``ValueError``;
- a record digest mismatch raises ``ValueError``;
- a registry-vs-catalog source-family mismatch raises ``ValueError``;
- an ``evaluated_at`` outside the record's inclusive validity window
  raises ``ValueError`` (expired or not yet valid);
- a naive or non-datetime ``evaluated_at`` raises ``ValueError``.

Validity windows are inclusive on both bounds: a record is trusted for
``valid_from <= evaluated_at <= valid_until`` in UTC. Aware non-UTC
datetimes are normalized to UTC before comparison.

Phase 1 boundary: every public value preserves the exact ``paper_only``,
``report_only``, and ``readonly`` hard flags. This module performs no
database, Supabase/Postgres, filesystem, JSONL, cache, network, HTTP,
socket, CLI, environment, process, logging, ambient-clock, randomness,
or built-in hash operation, and uses no floats.

Record digest derivation, computed ONCE at authoring time and embedded
below as literal constants (derivation code is intentionally not part
of this module):

    lowercase-hex sha256 over the UTF-8 domain string
    "polymarket-alpha-lab/crypto-btc-source-catalog-v0/<source_id>/"
    "<record_id>/<release_vintage>"
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import re
from typing import Final, final

from polymarket_alpha_lab.crypto_btc_evidence_registry import (
    require_approved_crypto_btc_source,
)

__all__ = (
    "CryptoBtcTrustedSourceRecord",
    "trusted_crypto_btc_source_catalog",
    "resolve_trusted_crypto_btc_source_record",
)

CRYPTO_BTC_SOURCE_CATALOG_VERSION: Final = "crypto-btc-source-catalog-v0"
_REQUIRED_REGISTRY_VERSION: Final = "crypto-btc-approved-registry-v0"

_IDENTIFIER_RE: Final = re.compile(r"[a-z0-9](?:[a-z0-9._:-]*[a-z0-9])?", re.ASCII)
_DIGEST_RE: Final = re.compile(r"[0-9a-f]{64}", re.ASCII)
_HARD_FLAGS: Final = ("paper_only", "report_only", "readonly")
_PUBLIC_CLASS_NAMES: Final = ("CryptoBtcTrustedSourceRecord",)


class _ExactPublicDataclass:
    __slots__ = ()

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        if cls.__bases__ != (_ExactPublicDataclass,) or cls.__name__ not in _PUBLIC_CLASS_NAMES:
            raise TypeError(
                "public crypto BTC evidence catalog dataclasses do not support subclassing"
            )


def _exact_self(value: object, expected: type, path: str) -> None:
    if type(value) is not expected:
        raise ValueError(f"{path} must be exactly {expected.__name__}")


def _identifier(path: str, value: object) -> str:
    if (
        type(value) is not str
        or len(value.encode("utf-8")) > 160
        or _IDENTIFIER_RE.fullmatch(value) is None
    ):
        raise ValueError(f"{path} must be an exact canonical identifier")
    return value


def _digest(path: str, value: object) -> str:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{path} must be an exact lowercase SHA-256 digest")
    return value


def _utc_instant(path: str, value: object) -> datetime:
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{path} must be an exact timezone-aware datetime")
    return value.astimezone(UTC)


def _hard_flags(path: str, value: object) -> None:
    for name in _HARD_FLAGS:
        flag = getattr(value, name)
        if flag is not True:
            raise ValueError(f"{path}.{name} must be exact True")


@final
@dataclass(frozen=True, slots=True)
class CryptoBtcTrustedSourceRecord(_ExactPublicDataclass):
    """One frozen trusted catalog record for an approved BTC source."""

    source_id: str
    record_id: str
    record_digest: str
    source_family: str
    release_vintage: str
    catalog_version: str
    valid_from: datetime
    valid_until: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _exact_self(self, CryptoBtcTrustedSourceRecord, "trusted_source_record")
        for name in ("source_id", "record_id", "source_family", "release_vintage"):
            object.__setattr__(self, name, _identifier(name, getattr(self, name)))
        object.__setattr__(self, "record_digest", _digest("record_digest", self.record_digest))
        if type(self.catalog_version) is not str or self.catalog_version != CRYPTO_BTC_SOURCE_CATALOG_VERSION:
            raise ValueError(
                "catalog_version must equal CRYPTO_BTC_SOURCE_CATALOG_VERSION "
                f"({CRYPTO_BTC_SOURCE_CATALOG_VERSION})"
            )
        object.__setattr__(self, "valid_from", _utc_instant("valid_from", self.valid_from))
        object.__setattr__(self, "valid_until", _utc_instant("valid_until", self.valid_until))
        if not self.valid_from < self.valid_until:
            raise ValueError("valid_from must be strictly before valid_until")
        _hard_flags("trusted_source_record", self)


_TRUSTED_CATALOG_RECORDS: Final = (
    CryptoBtcTrustedSourceRecord(
        source_id="btc_derivatives_reference",
        record_id="btc-derivatives-reference-v0",
        record_digest="8241604321b517d68563e086e42afb2ac26c55aa97cdab3ea5f41cf21b1c605a",
        source_family="btc_derivatives",
        release_vintage="2026-h1",
        catalog_version=CRYPTO_BTC_SOURCE_CATALOG_VERSION,
        valid_from=datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC),
        valid_until=datetime(2026, 12, 31, 23, 59, 59, tzinfo=UTC),
    ),
    CryptoBtcTrustedSourceRecord(
        source_id="btc_onchain_reference",
        record_id="btc-onchain-reference-v0",
        record_digest="9334b4deebb989435bd1302c223b185020cd225139b19bb56e919f5d3ab5d38e",
        source_family="btc_onchain",
        release_vintage="2026-h1",
        catalog_version=CRYPTO_BTC_SOURCE_CATALOG_VERSION,
        valid_from=datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC),
        valid_until=datetime(2026, 12, 31, 23, 59, 59, tzinfo=UTC),
    ),
    CryptoBtcTrustedSourceRecord(
        source_id="btc_resolution_rules",
        record_id="btc-resolution-rules-v0",
        record_digest="30d30f4091f28adbc4cc8cf61ad653f56985abca776ccc38e9887f78e223518e",
        source_family="btc_resolution_rules",
        release_vintage="2026-h1",
        catalog_version=CRYPTO_BTC_SOURCE_CATALOG_VERSION,
        valid_from=datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC),
        valid_until=datetime(2026, 12, 31, 23, 59, 59, tzinfo=UTC),
    ),
    CryptoBtcTrustedSourceRecord(
        source_id="btc_spot_reference",
        record_id="btc-spot-reference-v0",
        record_digest="5dc1fdbac0ffdd9bdcfb18f3e53d2f0ffdc4c151f026d5636550b6bcb7c023ac",
        source_family="btc_spot",
        release_vintage="2026-h1",
        catalog_version=CRYPTO_BTC_SOURCE_CATALOG_VERSION,
        valid_from=datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC),
        valid_until=datetime(2026, 9, 30, 23, 59, 59, tzinfo=UTC),
    ),
    CryptoBtcTrustedSourceRecord(
        source_id="btc_spot_reference",
        record_id="btc-spot-reference-v0-pre",
        record_digest="d0d87f164d28b261ccecd142e2414768ef858a8b913afdaecfcc7376a85ac52b",
        source_family="btc_spot",
        release_vintage="2025-h2",
        catalog_version=CRYPTO_BTC_SOURCE_CATALOG_VERSION,
        valid_from=datetime(2025, 7, 1, 0, 0, 0, tzinfo=UTC),
        valid_until=datetime(2025, 12, 31, 23, 59, 59, tzinfo=UTC),
    ),
    CryptoBtcTrustedSourceRecord(
        source_id="btc_spot_reference",
        record_id="btc-spot-reference-v1",
        record_digest="72a93cd9dbb94e6fd4d306ce44dfa7b12fae9ba1cfb020a572f0ad03d03019c8",
        source_family="btc_spot",
        release_vintage="2026-h2",
        catalog_version=CRYPTO_BTC_SOURCE_CATALOG_VERSION,
        valid_from=datetime(2026, 10, 1, 0, 0, 0, tzinfo=UTC),
        valid_until=datetime(2026, 12, 31, 23, 59, 59, tzinfo=UTC),
    ),
)


def trusted_crypto_btc_source_catalog() -> tuple[CryptoBtcTrustedSourceRecord, ...]:
    """Return the frozen in-code trusted BTC source-record catalog.

    The tuple is sorted by ``(source_id, record_id)`` and is version-bound
    to ``CRYPTO_BTC_SOURCE_CATALOG_VERSION``. No caller-supplied catalog,
    record, family, vintage, or trust tier is accepted anywhere on this
    surface; release vintages exist only inside these catalog records.
    """
    return _TRUSTED_CATALOG_RECORDS


def _catalog_record_for(
    source_id: str, record_id: str
) -> CryptoBtcTrustedSourceRecord | None:
    for record in _TRUSTED_CATALOG_RECORDS:
        if record.source_id == source_id and record.record_id == record_id:
            return record
    return None


def resolve_trusted_crypto_btc_source_record(
    source_id: str,
    record_id: str,
    record_digest: str,
    *,
    evaluated_at: datetime,
) -> CryptoBtcTrustedSourceRecord:
    """Resolve one trusted catalog record, failing closed on any mismatch.

    The caller names an approved source ID plus the trusted record ID and
    digest and supplies the evaluation instant. Resolution checks, in
    deterministic order: exact string argument types, approved-source
    membership in the approved registry, the registry version expected by
    this catalog, trusted record membership for that source, the record
    digest, the registry-vs-catalog source family, and finally the
    inclusive UTC validity window around ``evaluated_at``. Every failed
    check raises ``ValueError``; there is no permissive fallback.
    """
    if type(source_id) is not str:
        raise ValueError("source_id must be an exact str")
    if type(record_id) is not str:
        raise ValueError("record_id must be an exact str")
    if type(record_digest) is not str:
        raise ValueError("record_digest must be an exact str")
    approved_source = require_approved_crypto_btc_source(source_id)
    if getattr(approved_source, "registry_version", None) != _REQUIRED_REGISTRY_VERSION:
        raise ValueError(
            "approved registry version does not match the catalog-required "
            f"registry version ({_REQUIRED_REGISTRY_VERSION})"
        )
    record = _catalog_record_for(source_id, record_id)
    if record is None:
        raise ValueError(
            f"record_id is not a trusted catalog record for source: {source_id}/{record_id}"
        )
    if record.record_digest != record_digest:
        raise ValueError(
            f"record_digest does not match the trusted catalog record digest: {source_id}/{record_id}"
        )
    if getattr(approved_source, "source_family", None) != record.source_family:
        raise ValueError(
            "approved source family does not match the trusted catalog record "
            f"source family: {source_id}/{record_id}"
        )
    moment = _utc_instant("evaluated_at", evaluated_at)
    if moment < record.valid_from:
        raise ValueError(
            f"trusted catalog record is not yet valid at evaluated_at: {source_id}/{record_id}"
        )
    if moment > record.valid_until:
        raise ValueError(
            f"trusted catalog record is expired at evaluated_at: {source_id}/{record_id}"
        )
    return record

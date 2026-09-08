"""Immutable approved BTC evidence source registry for paper-only policy lookups."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, final

CRYPTO_BTC_APPROVED_REGISTRY_VERSION: Final = "crypto-btc-approved-registry-v0"

CRYPTO_BTC_APPROVED_SOURCE_IDS: Final = (
    "btc_derivatives_reference",
    "btc_onchain_reference",
    "btc_resolution_rules",
    "btc_spot_reference",
)

CRYPTO_BTC_SOURCE_FAMILIES: Final = (
    "btc_derivatives",
    "btc_onchain",
    "btc_resolution_rules",
    "btc_spot",
)

CRYPTO_BTC_TRUST_TIERS: Final = (
    "official",
    "primary",
)

_APPROVED_SOURCE_SPEC: Final = (
    ("btc_derivatives_reference", "btc_derivatives", "primary"),
    ("btc_onchain_reference", "btc_onchain", "primary"),
    ("btc_resolution_rules", "btc_resolution_rules", "official"),
    ("btc_spot_reference", "btc_spot", "primary"),
)

_UNKNOWN_SOURCE_ID_MESSAGE: Final = "source_id must be a known approved BTC source"

if (
    CRYPTO_BTC_APPROVED_SOURCE_IDS != tuple(row[0] for row in _APPROVED_SOURCE_SPEC)
    or CRYPTO_BTC_SOURCE_FAMILIES
    != tuple(sorted({row[1] for row in _APPROVED_SOURCE_SPEC}))
    or CRYPTO_BTC_TRUST_TIERS != tuple(sorted({row[2] for row in _APPROVED_SOURCE_SPEC}))
):
    raise RuntimeError("approved BTC registry constants must match the pinned spec")

__all__ = (
    "CryptoBtcApprovedSource",
    "approved_crypto_btc_source_registry",
    "require_approved_crypto_btc_source",
)


@final
@dataclass(frozen=True, slots=True)
class CryptoBtcApprovedSource:
    """One approved BTC evidence source pinned to the fixed registry version."""

    source_id: str
    source_family: str
    trust_tier: str
    registry_version: str = CRYPTO_BTC_APPROVED_REGISTRY_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls) -> None:
        raise TypeError("CryptoBtcApprovedSource does not support subclassing")

    def __post_init__(self) -> None:
        _require_known_source_id(self.source_id)
        _require_known_member(
            "source_family",
            self.source_family,
            CRYPTO_BTC_SOURCE_FAMILIES,
            "BTC source family",
        )
        _require_known_member(
            "trust_tier",
            self.trust_tier,
            CRYPTO_BTC_TRUST_TIERS,
            "BTC trust tier",
        )
        _, pinned_family, pinned_tier = _approved_source_spec_row(self.source_id)
        if self.source_family != pinned_family:
            raise ValueError("source_family must match source_id")
        if self.trust_tier != pinned_tier:
            raise ValueError("trust_tier must match source_id")
        if self.registry_version != CRYPTO_BTC_APPROVED_REGISTRY_VERSION:
            raise ValueError(
                f"registry_version must be {CRYPTO_BTC_APPROVED_REGISTRY_VERSION}"
            )
        _require_hard_flags(self)


def approved_crypto_btc_source_registry() -> tuple[CryptoBtcApprovedSource, ...]:
    """Return a fresh sorted tuple of the four immutable approved BTC sources."""
    return tuple(
        CryptoBtcApprovedSource(
            source_id=source_id,
            source_family=source_family,
            trust_tier=trust_tier,
        )
        for source_id, source_family, trust_tier in _APPROVED_SOURCE_SPEC
    )


def require_approved_crypto_btc_source(source_id: str) -> CryptoBtcApprovedSource:
    """Fail-closed lookup of one approved BTC source by exact source ID."""
    for source in approved_crypto_btc_source_registry():
        if source.source_id == source_id:
            return source
    raise ValueError(_UNKNOWN_SOURCE_ID_MESSAGE)


def _require_known_source_id(value: object) -> str:
    if type(value) is not str or value not in CRYPTO_BTC_APPROVED_SOURCE_IDS:
        raise ValueError(_UNKNOWN_SOURCE_ID_MESSAGE)
    return value


def _require_known_member(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
    label: str,
) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a known {label}")
    return value


def _approved_source_spec_row(source_id: str) -> tuple[str, str, str]:
    for row in _APPROVED_SOURCE_SPEC:
        if row[0] == source_id:
            return row
    raise ValueError(_UNKNOWN_SOURCE_ID_MESSAGE)


def _require_hard_flags(source: CryptoBtcApprovedSource) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(source, field_name) is not True:
            raise ValueError(f"{field_name} must be True")

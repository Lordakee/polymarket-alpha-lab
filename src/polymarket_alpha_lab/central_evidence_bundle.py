"""Pure per-team evidence bundle contracts and the canonical equality rule.

The bundle is the frozen M2 contract consumed by later forecast
integration: every required item resolves to exactly one ``SelectedEvidence``
(ready) or one ``ZeroWeightPlaceholder`` (blocked), and replaying identical
inputs yields an identical bundle identity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
import hashlib
import json
import re
from types import MappingProxyType
from typing import Any, Mapping

from .central_data_contracts import (
    Freshness,
    ObservationValueState,
    ParseState,
    _as_utc,
)
from .central_data_db_row import NormalizedObservationRow, TypedEnvelope


_ITEM_NAME_RE = re.compile(r"[a-z0-9_]{1,64}\Z")
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


class EvidenceItemAvailability(str, Enum):
    READY = "ready"
    MISSING = "missing"
    STALE = "stale"
    PARSE_FAILED = "parse_failed"
    UNKNOWN_VALUE = "unknown_value"
    QUORUM_NOT_MET = "quorum_not_met"
    CONTRADICTORY = "contradictory"


class EvidenceBundleStatus(str, Enum):
    READY = "ready"
    BLOCKED = "blocked"


def _canonical_name(value: object, field_name: str) -> str:
    if type(value) is not str or _ITEM_NAME_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be [a-z0-9_]{{1,64}}")
    return value


def _canonical_optional_text(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string or None")
    return value


def typed_value_equality(left: Any, right: Any) -> bool | None:
    """Canonical equality over decoded typed values.

    Returns ``None`` when the two values are incomparable (different
    envelope kinds); ``None`` never signals contradiction.
    """

    if left is None or right is None:
        return left is None and right is None
    if isinstance(left, bool) or isinstance(right, bool):
        if isinstance(left, bool) and isinstance(right, bool):
            return left is right
        return None
    if isinstance(left, Decimal) and isinstance(right, Decimal):
        return left == right
    if isinstance(left, datetime) and isinstance(right, datetime):
        return left == right
    if isinstance(left, str) and isinstance(right, str):
        return left == right
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        if set(left) != set(right):
            return False
        for key in left:
            result = typed_value_equality(left[key], right[key])
            if result is None:
                return None
            if not result:
                return False
        return True
    if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        if len(left) != len(right):
            return False
        for item_left, item_right in zip(left, right):
            result = typed_value_equality(item_left, item_right)
            if result is None:
                return None
            if not result:
                return False
        return True
    return None


@dataclass(frozen=True)
class EvidenceItemRequirement:
    item_name: str
    source_ids: tuple[str, ...]
    minimum_current_families: int = 1
    max_age_seconds: int | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _canonical_name(self.item_name, "item_name")
        if isinstance(self.source_ids, (str, bytes)) or not self.source_ids:
            raise ValueError("source_ids must be a nonempty tuple of source ids")
        seen: set[str] = set()
        for source_id in self.source_ids:
            if type(source_id) is not str or not source_id or source_id.strip() != source_id:
                raise ValueError("source_ids must contain canonical ids")
            if source_id in seen:
                raise ValueError("source_ids must not contain duplicates")
            seen.add(source_id)
        if (
            type(self.minimum_current_families) is not int
            or self.minimum_current_families < 1
        ):
            raise ValueError("minimum_current_families must be a positive int")
        if self.max_age_seconds is not None and (
            type(self.max_age_seconds) is not int or self.max_age_seconds < 0
        ):
            raise ValueError("max_age_seconds must be a nonnegative int or None")
        for field_name in ("paper_only", "report_only", "readonly"):
            if getattr(self, field_name) is not True:
                raise ValueError(f"{field_name} must be True")


@dataclass(frozen=True)
class SelectedEvidence:
    """One ready observation selected for a required item."""

    observation_id: str
    source_id: str
    source_family: str
    observation_time: datetime
    retrieval_time: datetime
    payload_hash: str
    parser_version: str
    parse_state: ParseState
    freshness_state: Freshness
    value_state: ObservationValueState
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self.observation_id) is not str or _SHA256_RE.fullmatch(self.observation_id) is None:
            raise ValueError("observation_id must be a lowercase SHA-256 digest")
        for name in ("source_id", "source_family", "parser_version"):
            value = getattr(self, name)
            if type(value) is not str or not value or value.strip() != value:
                raise ValueError(f"{name} must be a canonical nonblank string")
        if type(self.payload_hash) is not str or _SHA256_RE.fullmatch(self.payload_hash) is None:
            raise ValueError("payload_hash must be a lowercase SHA-256 digest")
        object.__setattr__(self, "observation_time", _as_utc("observation_time", self.observation_time))
        object.__setattr__(self, "retrieval_time", _as_utc("retrieval_time", self.retrieval_time))
        if type(self.parse_state) is not ParseState or type(self.freshness_state) is not Freshness:
            raise ValueError("parse and freshness states must be enum members")
        if type(self.value_state) is not ObservationValueState:
            raise ValueError("value_state must be an enum member")
        for field_name in ("paper_only", "report_only", "readonly"):
            if getattr(self, field_name) is not True:
                raise ValueError(f"{field_name} must be True")

    @classmethod
    def from_observation(
        cls,
        row: NormalizedObservationRow,
        *,
        source_family: str,
    ) -> "SelectedEvidence":
        if type(row) is not NormalizedObservationRow:
            raise ValueError("row must be a NormalizedObservationRow")
        return cls(
            observation_id=row.normalized_observation_id,
            source_id=row.source_id,
            source_family=source_family,
            observation_time=row.observation_time,
            retrieval_time=row.retrieval_time,
            payload_hash=row.raw_payload_sha256,
            parser_version=row.parser_version,
            parse_state=ParseState(row.parse_state),
            freshness_state=Freshness(row.freshness_state),
            value_state=ObservationValueState(row.value_state),
        )


@dataclass(frozen=True)
class ZeroWeightPlaceholder:
    """The single canonical blocked-item record; weight is exactly zero."""

    item_name: str
    availability: EvidenceItemAvailability
    reason_codes: tuple[str, ...]
    references: tuple[SelectedEvidence, ...] = ()
    weight: Decimal = Decimal("0")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _canonical_name(self.item_name, "item_name")
        if type(self.availability) is not EvidenceItemAvailability:
            raise ValueError("availability must be an EvidenceItemAvailability")
        if self.availability is EvidenceItemAvailability.READY:
            raise ValueError("ready items must use SelectedEvidence")
        if type(self.reason_codes) is not tuple or not self.reason_codes:
            raise ValueError("reason_codes must be a nonempty tuple")
        for code in self.reason_codes:
            if type(code) is not str or not code or code.strip() != code:
                raise ValueError("reason_codes must contain canonical strings")
        if len(set(self.reason_codes)) != len(self.reason_codes):
            raise ValueError("reason_codes must not contain duplicates")
        if type(self.references) is not tuple or any(
            type(reference) is not SelectedEvidence for reference in self.references
        ):
            raise ValueError("references must be a tuple of SelectedEvidence")
        if self.weight != Decimal("0"):
            raise ValueError("placeholder weight must be exactly zero")
        for field_name in ("paper_only", "report_only", "readonly"):
            if getattr(self, field_name) is not True:
                raise ValueError(f"{field_name} must be True")


@dataclass(frozen=True)
class EvidenceBundle:
    team_id: str
    market_reference: str | None
    as_of: datetime
    items: Mapping[str, SelectedEvidence | ZeroWeightPlaceholder] = field(
        repr=False, default_factory=dict
    )
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self.team_id) is not str or not self.team_id or self.team_id.strip() != self.team_id:
            raise ValueError("team_id must be a canonical nonblank string")
        object.__setattr__(self, "market_reference", _canonical_optional_text(self.market_reference, "market_reference"))
        object.__setattr__(self, "as_of", _as_utc("as_of", self.as_of))
        if not isinstance(self.items, Mapping) or not self.items:
            raise ValueError("items must be a nonempty mapping keyed by item name")
        frozen_items = dict(sorted(self.items.items()))
        for name, entry in frozen_items.items():
            _canonical_name(name, "item name")
            if type(entry) not in (SelectedEvidence, ZeroWeightPlaceholder):
                raise ValueError("item entries must be SelectedEvidence or ZeroWeightPlaceholder")
            if getattr(entry, "item_name", None) not in (None, name):
                raise ValueError("placeholder item_name must match its mapping key")
        object.__setattr__(self, "items", MappingProxyType(frozen_items))
        for code in self.reason_codes:
            if type(code) is not str or not code or code.strip() != code:
                raise ValueError("reason_codes must contain canonical strings")
        if len(set(self.reason_codes)) != len(self.reason_codes):
            raise ValueError("reason_codes must not contain duplicates")
        for field_name in ("paper_only", "report_only", "readonly"):
            if getattr(self, field_name) is not True:
                raise ValueError(f"{field_name} must be True")

    @property
    def status(self) -> EvidenceBundleStatus:
        blocked = any(
            type(entry) is ZeroWeightPlaceholder for entry in self.items.values()
        )
        return (
            EvidenceBundleStatus.BLOCKED
            if blocked
            else EvidenceBundleStatus.READY
        )

    @property
    def bundle_id(self) -> str:
        payload: dict[str, Any] = {
            "team_id": self.team_id,
            "market_reference": self.market_reference,
            "as_of": self.as_of.isoformat(),
            "items": {
                name: (
                    {"selected": entry.observation_id}
                    if type(entry) is SelectedEvidence
                    else {
                        "placeholder": entry.availability.value,
                        "reasons": list(entry.reason_codes),
                        "references": [item.observation_id for item in entry.references],
                    }
                )
                for name, entry in sorted(self.items.items())
            },
            "reason_codes": list(self.reason_codes),
        }
        canonical = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


__all__ = (
    "EvidenceBundle",
    "EvidenceBundleStatus",
    "EvidenceItemAvailability",
    "EvidenceItemRequirement",
    "SelectedEvidence",
    "TypedEnvelope",
    "ZeroWeightPlaceholder",
    "typed_value_equality",
)

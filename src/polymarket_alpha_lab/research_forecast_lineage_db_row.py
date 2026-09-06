"""Strict immutable rows for research forecast event lineage."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import re


LINEAGE_STATES = frozenset(
    {"verified", "missing_event", "ambiguous_events", "malformed_event"}
)
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


def _canonical(value: object, field_name: str) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


def _utc(value: object, field_name: str) -> datetime:
    if type(value) is not datetime or value.tzinfo is None:
        raise ValueError(f"{field_name} must be a timezone-aware datetime")
    return value.astimezone(UTC)


@dataclass(frozen=True)
class ResearchForecastLineageRow:
    forecast_payload_sha256: str
    forecast_id: str
    condition_id: str
    team_id: str
    config_version: str
    event_id: str | None
    event_slug: str | None
    market_end_at: datetime | None
    event_lineage_state: str
    metadata_observed_at: datetime
    metadata_payload_sha256: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if (
            type(self.forecast_payload_sha256) is not str
            or _SHA256_RE.fullmatch(self.forecast_payload_sha256) is None
        ):
            raise ValueError(
                "forecast_payload_sha256 must be a lowercase SHA-256 digest"
            )
        for name in ("forecast_id", "condition_id", "team_id", "config_version"):
            _canonical(getattr(self, name), name)
        if self.event_lineage_state not in LINEAGE_STATES:
            raise ValueError("event_lineage_state is invalid")
        verified = self.event_lineage_state == "verified"
        event_values = (self.event_id, self.event_slug, self.market_end_at)
        if verified:
            _canonical(self.event_id, "event_id")
            _canonical(self.event_slug, "event_slug")
            object.__setattr__(
                self, "market_end_at", _utc(self.market_end_at, "market_end_at")
            )
        elif any(value is not None for value in event_values):
            raise ValueError("unknown event lineage must not carry event identity")
        object.__setattr__(
            self,
            "metadata_observed_at",
            _utc(self.metadata_observed_at, "metadata_observed_at"),
        )
        if (
            type(self.metadata_payload_sha256) is not str
            or _SHA256_RE.fullmatch(self.metadata_payload_sha256) is None
        ):
            raise ValueError("metadata_payload_sha256 must be a lowercase SHA-256 digest")
        if any(
            getattr(self, name) is not True
            for name in ("paper_only", "report_only", "readonly")
        ):
            raise ValueError("lineage rows must be paper-only, report-only, and readonly")

    def as_parameters(self) -> tuple[object, ...]:
        return (
            self.forecast_payload_sha256,
            self.forecast_id,
            self.condition_id,
            self.team_id,
            self.config_version,
            self.event_id,
            self.event_slug,
            self.market_end_at,
            self.event_lineage_state,
            self.metadata_observed_at,
            self.metadata_payload_sha256,
            True,
            True,
            True,
        )


__all__ = ("LINEAGE_STATES", "ResearchForecastLineageRow")

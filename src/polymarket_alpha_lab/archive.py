"""Raw JSON archival helpers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RawArchiveEntry:
    source: str
    name: str
    captured_at: datetime
    payload_path: Path
    metadata_path: Path
    payload_sha256: str


@dataclass(frozen=True)
class RawArchive:
    root: Path

    def write(
        self,
        *,
        source: str,
        name: str,
        payload: Any,
        captured_at: datetime | None = None,
        endpoint: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> RawArchiveEntry:
        timestamp_value = _normalize_timestamp(captured_at or datetime.now(UTC))
        timestamp = _format_timestamp(timestamp_value)
        directory = self.root / source
        directory.mkdir(parents=True, exist_ok=True)
        payload_path = directory / f"{timestamp}-{name}.json"
        metadata_path = directory / f"{timestamp}-{name}.meta.json"
        payload_hash = sha256_json(payload)

        payload_path.write_text(
            _canonical_json(payload, indent=2),
            encoding="utf-8",
        )
        metadata_path.write_text(
            _canonical_json(
                {
                    "captured_at": timestamp_value.isoformat(),
                    "endpoint": endpoint,
                    "name": name,
                    "params": params or {},
                    "payload_sha256": payload_hash,
                    "source": source,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return RawArchiveEntry(
            source=source,
            name=name,
            captured_at=timestamp_value,
            payload_path=payload_path,
            metadata_path=metadata_path,
            payload_sha256=payload_hash,
        )


def _format_timestamp(value: datetime) -> str:
    return _normalize_timestamp(value).strftime("%Y%m%dT%H%M%SZ")


def _normalize_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def sha256_json(payload: Any) -> str:
    return hashlib.sha256(_canonical_json(payload, indent=None).encode("utf-8")).hexdigest()


def _canonical_json(payload: Any, *, indent: int | None) -> str:
    return json.dumps(payload, indent=indent, sort_keys=True, separators=(",", ": ")) + "\n"

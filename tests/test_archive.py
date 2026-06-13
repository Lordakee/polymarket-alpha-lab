import json
from datetime import UTC, datetime

from polymarket_alpha_lab.archive import RawArchive, sha256_json


def test_raw_archive_writes_payload_metadata_and_checksum(tmp_path):
    archive = RawArchive(root=tmp_path)
    captured_at = datetime(2026, 6, 13, 12, 30, tzinfo=UTC)
    payload = [{"conditionId": "0xabc"}]

    entry = archive.write(
        source="gamma",
        name="markets",
        payload=payload,
        captured_at=captured_at,
        endpoint="/markets",
        params={"active": True, "closed": False, "limit": 25},
    )

    assert entry.payload_path == tmp_path / "gamma" / "20260613T123000Z-markets.json"
    assert entry.metadata_path == tmp_path / "gamma" / "20260613T123000Z-markets.meta.json"
    assert json.loads(entry.payload_path.read_text()) == payload

    metadata = json.loads(entry.metadata_path.read_text())
    assert metadata == {
        "captured_at": "2026-06-13T12:30:00+00:00",
        "endpoint": "/markets",
        "name": "markets",
        "params": {"active": True, "closed": False, "limit": 25},
        "payload_sha256": sha256_json(payload),
        "source": "gamma",
    }

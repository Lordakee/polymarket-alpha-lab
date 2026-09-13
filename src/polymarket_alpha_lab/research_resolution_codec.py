"""Closed, canonical, content-bound resolution evidence storage codec."""
from __future__ import annotations

import base64
from dataclasses import asdict, replace
from datetime import datetime
from hashlib import sha256
import json

from polymarket_alpha_lab.research_resolution import (
    IndependentResolutionConfirmation, ResolutionSubmission, assess_resolution, digest,
)
from polymarket_alpha_lab.team_research_agent_types import strict_json
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot

MAX_RESOLUTION_PAYLOAD_BYTES = 2097152
SCHEMA = "research-resolution-v1"


def encode_resolution(item: ResolutionSubmission) -> str:
    if type(item) is not ResolutionSubmission:
        raise ValueError("resolution_submission_invalid")
    item = replace(item)
    proof = None if item.confirmation is None else asdict(item.confirmation)
    if proof is not None:
        proof["resolved_at"] = item.confirmation.resolved_at.isoformat()
        proof["confirmed_at"] = item.confirmation.confirmed_at.isoformat()
        proof["source_content_sha256"] = item.confirmation.source_content_sha256
    payload = {
        "schema_version": SCHEMA, "review_id": item.review_id, "condition_id": item.condition_id,
        "market_slug": item.snapshot.market_slug, "checked_at": item.checked_at.isoformat(),
        "snapshot": {"fetched_at": item.snapshot.fetched_at.isoformat(),
                     "raw_base64": base64.b64encode(item.snapshot.raw_json).decode("ascii"),
                     "content_sha256": item.snapshot.content_sha256,
                     "source_reference": item.snapshot.source_reference},
        "confirmation": proof, "assessment": asdict(assess_resolution(item)),
        "paper_only": True, "report_only": True, "readonly": True,
    }
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if len(encoded.encode("utf-8")) > MAX_RESOLUTION_PAYLOAD_BYTES:
        raise ValueError("resolution_payload_too_large")
    return encoded


def decode_resolution(payload: str, *, expected_sha256: str) -> ResolutionSubmission:
    """Recompute assessment, all hashes and exact canonical serialization."""
    try:
        digest(expected_sha256)
        if type(payload) is not str or not 1 <= len(payload) <= MAX_RESOLUTION_PAYLOAD_BYTES:
            raise ValueError("size")
        if sha256(payload.encode("utf-8")).hexdigest() != expected_sha256:
            raise ValueError("digest")
        data = strict_json(payload)
        snapshot = data["snapshot"]
        raw = base64.b64decode(snapshot["raw_base64"], validate=True)
        proof = data["confirmation"]
        if proof is not None:
            proof = dict(proof)
            proof.pop("source_content_sha256")
            for name in ("resolved_at", "confirmed_at"):
                proof[name] = datetime.fromisoformat(proof[name])
            proof = IndependentResolutionConfirmation(**proof)
        item = ResolutionSubmission(data["review_id"], data["condition_id"],
            GammaMarketSnapshot(data["market_slug"], datetime.fromisoformat(snapshot["fetched_at"]), raw),
            datetime.fromisoformat(data["checked_at"]), proof)
        if encode_resolution(item) != payload:
            raise ValueError("noncanonical or inconsistent")
        return item
    except Exception:
        raise ValueError("resolution_payload_invalid") from None

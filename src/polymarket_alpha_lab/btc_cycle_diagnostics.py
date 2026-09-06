"""Pure, redacted diagnostics text for the BTC research cycle.

The reducer accepts already-fetched acquisition outcomes, the evidence
bundle, and the cycle result, and renders deterministic lines containing
only statuses, counters, reason codes, and identifiers — never payloads,
URLs, or credentials. The CLI is the impure composer.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from .btc_research_cycle import BtcCycleResult
from .central_data_acquisition import AcquisitionOutcome
from .central_evidence_bundle import EvidenceBundle


DIAGNOSTICS_VERSION = "btc-cycle-diagnostics-v1"


def format_btc_cycle_diagnostics(
    outcomes: Sequence[AcquisitionOutcome],
    bundle: EvidenceBundle,
    result: BtcCycleResult,
) -> str:
    if not isinstance(outcomes, Sequence):
        raise ValueError("outcomes must be a sequence of AcquisitionOutcome")
    if type(bundle) is not EvidenceBundle:
        raise ValueError("bundle must be an EvidenceBundle")
    if type(result) is not BtcCycleResult:
        raise ValueError("result must be a BtcCycleResult")

    lines = [
        "btc cycle diagnostics",
        f"version: {DIAGNOSTICS_VERSION}",
        f"cycle_id: {result.cycle_id}",
        f"cycle_status: {result.status}",
        f"bundle_status: {bundle.status.value}",
        "acquisition:",
    ]
    for outcome in sorted(outcomes, key=lambda item: item.source_id):
        retry = (
            "none"
            if outcome.retry_after_seconds is None
            else f"{outcome.retry_after_seconds}s"
        )
        reasons = ",".join(outcome.reason_codes) or "none"
        lines.append(
            f"  {outcome.source_id}: status={outcome.failure_status.value} "
            f"attempts={outcome.attempts} retry_after={retry} "
            f"pages={outcome.pages_fetched} normalized={len(outcome.normalized_rows)} "
            f"reasons={reasons}"
        )
    lines.append("evidence items:")
    for name in sorted(bundle.items):
        entry = bundle.items[name]
        if hasattr(entry, "observation_id"):
            lines.append(
                f"  {name}: ready family={entry.source_family} "
                f"payload={entry.payload_hash} parser={entry.parser_version}"
            )
        else:
            lines.append(
                f"  {name}: {entry.availability.value} "
                f"reasons={','.join(entry.reason_codes)}"
            )
    if result.base_probability is not None:
        lines.append(f"base_probability: {format(result.base_probability, 'f')}")
    if result.reason_codes:
        lines.append(f"cycle_reasons: {', '.join(result.reason_codes)}")
    return "\n".join(lines)


__all__ = ("DIAGNOSTICS_VERSION", "format_btc_cycle_diagnostics")

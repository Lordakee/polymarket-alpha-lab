from __future__ import annotations

import json
from decimal import InvalidOperation
from pathlib import Path

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_probability_side_edge import PaperProbabilitySideEdgeRow

__all__ = ("read_paper_probability_recommendation_queue_side_edge_rows",)

_ROW_ENVELOPE_KEYS = ("rows", "side_edge_rows", "inputs", "input_rows")


def read_paper_probability_recommendation_queue_side_edge_rows(
    path: Path | str,
) -> tuple[PaperProbabilitySideEdgeRow, ...]:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    stripped = text.strip()
    if not stripped:
        return ()

    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return _read_jsonl_rows(target, text)

    raw_rows = _extract_row_payloads(payload, path=target)
    return tuple(
        _recover_row(row, path=target, row_number=row_number)
        for row_number, row in enumerate(raw_rows, start=1)
    )


def _read_jsonl_rows(path: Path, text: str) -> tuple[PaperProbabilitySideEdgeRow, ...]:
    rows: list[PaperProbabilitySideEdgeRow] = []
    for row_number, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path} line {row_number} is not valid JSON: {exc}") from exc
        rows.append(_recover_row(payload, path=path, row_number=row_number))
    return tuple(rows)


def _extract_row_payloads(payload: object, *, path: Path) -> tuple[object, ...]:
    if isinstance(payload, list):
        return tuple(payload)
    if isinstance(payload, dict):
        for key in _ROW_ENVELOPE_KEYS:
            if key not in payload:
                continue
            _require_envelope_safety_flags(payload)
            value = payload[key]
            if not isinstance(value, list):
                raise ValueError(f"{path} {key} must be a JSON array")
            return tuple(value)
        return (payload,)
    raise ValueError(
        f"{path} input must be a JSON object, JSON array, or JSONL file",
    )


def _recover_row(
    payload: object,
    *,
    path: Path,
    row_number: int,
) -> PaperProbabilitySideEdgeRow:
    if not isinstance(payload, dict):
        raise ValueError(f"{path} row {row_number} must be a JSON object")
    try:
        recovered = from_jsonable(PaperProbabilitySideEdgeRow, payload)
    except (AttributeError, InvalidOperation, KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"{path} row {row_number} is not a valid PaperProbabilitySideEdgeRow: {exc}",
        ) from exc
    if not isinstance(recovered, PaperProbabilitySideEdgeRow):
        raise ValueError(f"{path} row {row_number} is not a PaperProbabilitySideEdgeRow")
    return recovered


def _require_envelope_safety_flags(payload: dict[str, object]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if field_name in payload and payload[field_name] is not True:
            raise ValueError(f"input envelope must be {field_name}")

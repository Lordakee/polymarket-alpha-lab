"""Pure local-input recovery for paper candidate decision engine bundles."""

from __future__ import annotations

import json
from datetime import datetime
from os import PathLike
from pathlib import Path
from typing import Any

from polymarket_alpha_lab.candidate_decision_score import CandidateDecisionScoreConfig
from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_candidate_decision_engine import (
    PaperCandidateDecisionEngineReport,
)
from polymarket_alpha_lab.paper_candidate_decision_engine_load import (
    PaperCandidateDecisionEngineCandidateBundle,
    load_paper_candidate_decision_engine_report,
)


def paper_candidate_decision_engine_candidate_bundles_from_jsonable(
    value: object,
) -> tuple[PaperCandidateDecisionEngineCandidateBundle, ...]:
    rows = _candidate_bundle_rows(value)
    return tuple(_candidate_bundle_from_jsonable(index, row) for index, row in enumerate(rows))


def paper_candidate_decision_engine_candidate_bundles_from_text(
    text: str,
) -> tuple[PaperCandidateDecisionEngineCandidateBundle, ...]:
    if type(text) is not str:
        raise ValueError("candidate bundle text must be a string")
    stripped = text.strip()
    if not stripped:
        raise ValueError("candidate bundle input must contain at least one candidate bundle")
    try:
        loaded = json.loads(
            stripped,
            parse_float=_reject_json_float,
            parse_constant=_reject_json_constant,
        )
    except json.JSONDecodeError:
        return _candidate_bundles_from_jsonl(stripped)
    return paper_candidate_decision_engine_candidate_bundles_from_jsonable(loaded)


def paper_candidate_decision_engine_candidate_bundles_from_path(
    path: str | PathLike[str],
) -> tuple[PaperCandidateDecisionEngineCandidateBundle, ...]:
    if not isinstance(path, (str, PathLike)):
        raise ValueError("candidate bundle path must be a local path")
    return paper_candidate_decision_engine_candidate_bundles_from_text(
        Path(path).read_text(encoding="utf-8"),
    )


def load_paper_candidate_decision_engine_report_from_local_input(
    *,
    generated_at: datetime,
    score_config: CandidateDecisionScoreConfig | None = None,
    candidate_bundle_rows: object | None = None,
    candidate_bundle_text: str | None = None,
    candidate_bundle_path: str | PathLike[str] | None = None,
) -> PaperCandidateDecisionEngineReport:
    source_count = sum(
        value is not None
        for value in (
            candidate_bundle_rows,
            candidate_bundle_text,
            candidate_bundle_path,
        )
    )
    if source_count != 1:
        raise ValueError("exactly one candidate bundle source is required")
    if candidate_bundle_rows is not None:
        bundles = paper_candidate_decision_engine_candidate_bundles_from_jsonable(
            candidate_bundle_rows,
        )
    elif candidate_bundle_text is not None:
        bundles = paper_candidate_decision_engine_candidate_bundles_from_text(
            candidate_bundle_text,
        )
    else:
        bundles = paper_candidate_decision_engine_candidate_bundles_from_path(
            candidate_bundle_path,
        )
    return load_paper_candidate_decision_engine_report(
        generated_at=generated_at,
        score_config=score_config,
        candidate_bundles=bundles,
    )


def _candidate_bundle_rows(value: object) -> tuple[object, ...]:
    if type(value) is PaperCandidateDecisionEngineCandidateBundle or type(value) is dict:
        return (value,)
    if type(value) not in (list, tuple):
        raise ValueError(
            "candidate bundle input must be a JSON object or JSON array",
        )
    rows = tuple(value)
    if not rows:
        raise ValueError("candidate bundle input must contain at least one candidate bundle")
    return rows


def _candidate_bundle_from_jsonable(
    index: int,
    row: object,
) -> PaperCandidateDecisionEngineCandidateBundle:
    if type(row) is PaperCandidateDecisionEngineCandidateBundle:
        return row
    if type(row) is not dict:
        raise ValueError(f"candidate bundle row {index} must be a JSON object")
    try:
        bundle = from_jsonable(PaperCandidateDecisionEngineCandidateBundle, row)
    except TypeError as exc:
        raise ValueError(f"candidate bundle row {index} is invalid") from exc
    if type(bundle) is not PaperCandidateDecisionEngineCandidateBundle:
        raise ValueError(f"candidate bundle row {index} is invalid")
    return bundle


def _candidate_bundles_from_jsonl(
    text: str,
) -> tuple[PaperCandidateDecisionEngineCandidateBundle, ...]:
    rows: list[Any] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            loaded = json.loads(
                stripped,
                parse_float=_reject_json_float,
                parse_constant=_reject_json_constant,
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"candidate bundle JSONL line {line_number} must be valid JSON",
            ) from exc
        if type(loaded) is not dict:
            raise ValueError(
                f"candidate bundle JSONL line {line_number} must be a JSON object",
            )
        rows.append(loaded)
    return paper_candidate_decision_engine_candidate_bundles_from_jsonable(rows)


def _reject_json_float(_value: str) -> None:
    raise ValueError("JSON Decimal value must not be a float")


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"JSON value must not be non-finite: {value}")


__all__ = (
    "paper_candidate_decision_engine_candidate_bundles_from_jsonable",
    "paper_candidate_decision_engine_candidate_bundles_from_text",
    "paper_candidate_decision_engine_candidate_bundles_from_path",
    "load_paper_candidate_decision_engine_report_from_local_input",
)

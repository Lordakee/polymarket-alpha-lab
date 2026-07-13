from __future__ import annotations

import json
import re
from collections.abc import Iterator
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PHASE1_STRATEGY_CONFIG_PATH = REPO_ROOT / "strategy.example.phase1-screening.json"
PHASE1_CONFIG_DOC_PATHS = (
    REPO_ROOT / "docs" / "config" / "phase-1-strategy-screening-schema.md",
)

HARD_PHASE1_FLAGS = ("paper_only", "report_only", "readonly")

FORBIDDEN_EXACT_FIELD_NAMES = {
    "wallet",
    "wallet_address",
    "wallet_id",
    "private_key",
    "order_submit",
    "cancel",
    "replace",
    "live_execution",
    "autonomous_trade",
}

FORBIDDEN_FIELD_PATTERNS = (
    re.compile(r"(^|_)wallet($|_)"),
    re.compile(r"(^|_)private_key($|_)"),
    re.compile(r"(^|_)order_submit($|_)"),
    re.compile(r"(^|_)cancel($|_)"),
    re.compile(r"(^|_)replace($|_)"),
    re.compile(r"(^|_)live_execution($|_)"),
    re.compile(r"(^|_)autonomous_trade($|_)"),
)


def _load_json_config(path: Path) -> dict[str, object]:
    assert path.exists(), f"{path} must exist"
    with path.open(encoding="utf-8") as config_file:
        loaded = json.load(config_file)
    assert isinstance(loaded, dict), f"{path} must contain a JSON object"
    return loaded


def _json_key_paths(value: object, prefix: tuple[str, ...] = ()) -> Iterator[tuple[str, ...]]:
    if isinstance(value, dict):
        for key, child_value in value.items():
            assert isinstance(key, str)
            key_path = (*prefix, key)
            yield key_path
            yield from _json_key_paths(child_value, key_path)
    elif isinstance(value, list):
        for index, child_value in enumerate(value):
            yield from _json_key_paths(child_value, (*prefix, f"[{index}]"))


def _forbidden_json_field_paths(config: dict[str, object]) -> tuple[str, ...]:
    forbidden_paths: list[str] = []
    for key_path in _json_key_paths(config):
        field_name = key_path[-1].lower()
        if field_name in FORBIDDEN_EXACT_FIELD_NAMES or any(
            pattern.search(field_name) for pattern in FORBIDDEN_FIELD_PATTERNS
        ):
            forbidden_paths.append(".".join(key_path))
    return tuple(forbidden_paths)


def _fenced_code_line_numbers(markdown_text: str) -> set[int]:
    fenced_lines: set[int] = set()
    in_fence = False
    for line_number, line in enumerate(markdown_text.splitlines(), start=1):
        if line.strip().startswith("```"):
            fenced_lines.add(line_number)
            in_fence = not in_fence
            continue
        if in_fence:
            fenced_lines.add(line_number)
    return fenced_lines


def _config_doc_field_mentions(path: Path) -> tuple[tuple[int, str, str], ...]:
    assert path.exists(), f"{path} must exist"
    text = path.read_text(encoding="utf-8")
    fenced_lines = _fenced_code_line_numbers(text)
    mentions: list[tuple[int, str, str]] = []

    for line_number, line in enumerate(text.splitlines(), start=1):
        if line_number in fenced_lines:
            continue
        for field_name in FORBIDDEN_EXACT_FIELD_NAMES:
            if f"`{field_name}`" in line:
                mentions.append((line_number, field_name, line.strip()))

    return tuple(mentions)


def _config_doc_required_true_flag_mentions(path: Path) -> dict[str, bool]:
    assert path.exists(), f"{path} must exist"
    text = path.read_text(encoding="utf-8")
    return {
        flag: bool(
            re.search(
                rf"`{re.escape(flag)}`[^.\n]*(?:must be|should be)\s+`true`",
                text,
                flags=re.IGNORECASE,
            ),
        )
        for flag in HARD_PHASE1_FLAGS
    }


def _markdown_section(text: str, heading: str) -> str:
    heading_pattern = re.compile(rf"^## {re.escape(heading)}\s*$", re.MULTILINE)
    match = heading_pattern.search(text)
    assert match is not None, f"missing section {heading!r}"

    next_heading = re.search(r"^##\s+", text[match.end() :], re.MULTILINE)
    if next_heading is None:
        return text[match.end() :]
    return text[match.end() : match.end() + next_heading.start()]


def test_phase1_strategy_screening_config_exists_and_keeps_hard_flags_true() -> None:
    config = _load_json_config(PHASE1_STRATEGY_CONFIG_PATH)

    assert {flag: config.get(flag) for flag in HARD_PHASE1_FLAGS} == {
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def test_phase1_config_docs_keep_hard_flags_documented_true() -> None:
    for path in PHASE1_CONFIG_DOC_PATHS:
        assert _config_doc_required_true_flag_mentions(path) == {
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        }


def test_phase1_strategy_screening_config_has_no_execution_field_names() -> None:
    config = _load_json_config(PHASE1_STRATEGY_CONFIG_PATH)

    assert _forbidden_json_field_paths(config) == ()


def test_phase1_config_docs_do_not_define_execution_fields() -> None:
    for path in PHASE1_CONFIG_DOC_PATHS:
        mentions = _config_doc_field_mentions(path)
        redaction_section = _markdown_section(
            path.read_text(encoding="utf-8"),
            "Redaction And Forbidden Fields",
        )

        assert mentions == tuple(
            mention
            for mention in mentions
            if mention[2] in redaction_section and "forbidden" in redaction_section.lower()
        )


def test_phase1_config_execution_field_detector_catches_nested_forbidden_names() -> None:
    config_with_execution_fields: dict[str, object] = {
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "nested": {
            "wallet": "0xexample",
            "private_key": "redacted",
            "order_submit": True,
            "cancel": False,
            "replace": False,
            "live_execution": False,
            "autonomous_trade": False,
        },
    }

    assert _forbidden_json_field_paths(config_with_execution_fields) == (
        "nested.wallet",
        "nested.private_key",
        "nested.order_submit",
        "nested.cancel",
        "nested.replace",
        "nested.live_execution",
        "nested.autonomous_trade",
    )

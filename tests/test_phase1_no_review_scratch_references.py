from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

FORMAL_SCAN_ROOTS = (
    REPO_ROOT / "src",
    REPO_ROOT / "tests",
    REPO_ROOT / "docs",
)
FORMAL_SCAN_FILES = (
    REPO_ROOT / "strategy.example.phase1-screening.json",
)

ALLOWED_SELF_PATH = Path("tests/test_phase1_no_review_scratch_references.py")

REVIEW_SCRATCH_REFERENCE_PATTERN = re.compile(
    r"(?ix)"
    r"("
    r"(?:^|[\"'(<\s])(?:\./)?\.review(?:/|\\)"
    r"|"
    r"(?:claude-final-review|current-untracked-batch-summary|staged-review)"
    r"\.(?:diff|status|txt)"
    r")",
)


def _formal_project_files() -> tuple[Path, ...]:
    root_files = tuple(path for path in FORMAL_SCAN_FILES if path.exists())
    rooted_files = tuple(
        path
        for root in FORMAL_SCAN_ROOTS
        if root.exists()
        for path in root.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and ".pytest_cache" not in path.parts
        and path.suffix
        in {
            ".cfg",
            ".css",
            ".html",
            ".ini",
            ".json",
            ".md",
            ".py",
            ".sql",
            ".toml",
            ".txt",
            ".yaml",
            ".yml",
        }
    )
    return tuple(sorted((*root_files, *rooted_files)))


def _review_scratch_reference_hits(paths: tuple[Path, ...]) -> tuple[str, ...]:
    hits: list[str] = []
    for path in paths:
        display_path = _display_path(path)
        if display_path == str(ALLOWED_SELF_PATH):
            continue

        text = path.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if REVIEW_SCRATCH_REFERENCE_PATTERN.search(line):
                hits.append(f"{display_path}:{line_number}:{line.strip()}")

    return tuple(hits)


def _display_path(path: Path) -> str:
    if path.is_relative_to(REPO_ROOT):
        return str(path.relative_to(REPO_ROOT))
    return str(path)


def test_detector_catches_review_scratch_inputs_dependencies_and_doc_links(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate.md"
    candidate.write_text(
        "\n".join(
            (
                "input: .review/staged-review.diff",
                "depends_on: ./.review/claude-final-review.txt",
                "[scratch](../.review/current-untracked-batch-summary.txt)",
            ),
        ),
        encoding="utf-8",
    )

    hits = _review_scratch_reference_hits((candidate,))

    assert hits == (
        f"{candidate}:1:input: .review/staged-review.diff",
        f"{candidate}:2:depends_on: ./.review/claude-final-review.txt",
        (
            f"{candidate}:3:"
            "[scratch](../.review/current-untracked-batch-summary.txt)"
        ),
    )


def test_phase1_formal_files_do_not_reference_review_scratch_artifacts() -> None:
    formal_paths = _formal_project_files()

    assert formal_paths
    assert _review_scratch_reference_hits(formal_paths) == ()

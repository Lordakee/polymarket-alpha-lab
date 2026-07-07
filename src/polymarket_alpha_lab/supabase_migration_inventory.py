"""Read-only Supabase migration inventory."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re


_MIGRATION_FILE_NAME_PATTERN = re.compile(r"^(?P<timestamp>\d{14})_(?P<slug>.+)\.sql$")
_CREATE_TABLE_PATTERN = re.compile(r"\bcreate\s+table\b", re.IGNORECASE)
_CREATE_INDEX_PATTERN = re.compile(
    r"\bcreate\s+(?:unique\s+)?index\b",
    re.IGNORECASE,
)
_ALTER_TABLE_PATTERN = re.compile(r"\balter\s+table\b", re.IGNORECASE)
_FUNCTION_PATTERN = re.compile(
    r"\bcreate\s+(?:or\s+replace\s+)?function\b",
    re.IGNORECASE,
)
_TABLE_NAME_PATTERN = re.compile(
    r"\bcreate\s+table\s+"
    r"(?:if\s+not\s+exists\s+)?"
    r"(?P<table_name>"
    r"(?:\"[^\"]+\"|[A-Za-z_][A-Za-z0-9_$]*)"
    r"(?:\s*\.\s*(?:\"[^\"]+\"|[A-Za-z_][A-Za-z0-9_$]*))?"
    r")",
    re.IGNORECASE,
)
_DURABLE_URL_PATTERN = re.compile(
    r"\b(?P<scheme>postgresql|postgres|mysql|mariadb|redis|mongodb|mongo)://"
    r"[^\s'\";)]*",
    re.IGNORECASE,
)
_DURABLE_WORD_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_])(?P<token>sqlite|duckdb|bigquery|snowflake)(?![A-Za-z0-9_])",
    re.IGNORECASE,
)
_REDACTED_DURABLE_URL_FRAGMENT = "<redacted-durable-url>"


@dataclass(frozen=True)
class SupabaseMigrationInventoryEntry:
    sequence_index: int
    file_name: str
    timestamp: str
    slug: str
    sql_sha256: str
    line_count: int
    create_table_count: int
    create_index_count: int
    alter_table_count: int
    function_count: int
    table_names: tuple[str, ...]
    has_paper_only_flag: bool
    has_report_only_flag: bool
    has_readonly_flag: bool


@dataclass(frozen=True)
class SupabaseMigrationInventoryDuplicateTimestamp:
    timestamp: str
    file_names: tuple[str, ...]


@dataclass(frozen=True)
class SupabaseMigrationInventoryUnsafeDurableBackendToken:
    file_name: str
    timestamp: str
    token: str
    line_number: int
    fragment: str


@dataclass(frozen=True)
class SupabaseMigrationInventorySummary:
    migration_count: int
    create_table_count: int
    create_index_count: int
    alter_table_count: int
    function_count: int
    table_names: tuple[str, ...]
    paper_only_migration_count: int
    report_only_migration_count: int
    readonly_migration_count: int


@dataclass(frozen=True)
class SupabaseMigrationInventoryReport:
    migration_count: int
    entries: tuple[SupabaseMigrationInventoryEntry, ...]
    duplicate_timestamps: tuple[SupabaseMigrationInventoryDuplicateTimestamp, ...]
    unsafe_durable_backend_tokens: tuple[
        SupabaseMigrationInventoryUnsafeDurableBackendToken,
        ...,
    ]
    summary: SupabaseMigrationInventorySummary


def build_supabase_migration_inventory(
    migrations_dir: str | Path,
) -> SupabaseMigrationInventoryReport:
    migration_path = Path(migrations_dir)
    sql_paths = sorted(migration_path.glob("*.sql"), key=lambda path: path.name)
    entries = tuple(
        _build_entry(sequence_index=index, sql_path=sql_path)
        for index, sql_path in enumerate(sql_paths, start=1)
    )
    return SupabaseMigrationInventoryReport(
        migration_count=len(entries),
        entries=entries,
        duplicate_timestamps=_find_duplicate_timestamps(entries),
        unsafe_durable_backend_tokens=tuple(
            finding
            for entry, sql_path in zip(entries, sql_paths, strict=True)
            for finding in _find_unsafe_durable_backend_tokens(entry, sql_path)
        ),
        summary=_build_summary(entries),
    )


def _build_entry(
    *,
    sequence_index: int,
    sql_path: Path,
) -> SupabaseMigrationInventoryEntry:
    sql = sql_path.read_text(encoding="utf-8")
    timestamp, slug = _split_migration_file_name(sql_path.name)
    normalized_sql = _sql_for_metadata(sql)
    return SupabaseMigrationInventoryEntry(
        sequence_index=sequence_index,
        file_name=sql_path.name,
        timestamp=timestamp,
        slug=slug,
        sql_sha256=sha256(sql.encode("utf-8")).hexdigest(),
        line_count=len(sql.splitlines()),
        create_table_count=len(_CREATE_TABLE_PATTERN.findall(normalized_sql)),
        create_index_count=len(_CREATE_INDEX_PATTERN.findall(normalized_sql)),
        alter_table_count=len(_ALTER_TABLE_PATTERN.findall(normalized_sql)),
        function_count=len(_FUNCTION_PATTERN.findall(normalized_sql)),
        table_names=tuple(_extract_table_names(normalized_sql)),
        has_paper_only_flag=_has_identifier(sql, "paper_only"),
        has_report_only_flag=_has_identifier(sql, "report_only"),
        has_readonly_flag=_has_identifier(sql, "readonly"),
    )


def _split_migration_file_name(file_name: str) -> tuple[str, str]:
    match = _MIGRATION_FILE_NAME_PATTERN.fullmatch(file_name)
    if match is not None:
        return match.group("timestamp"), match.group("slug")
    stem = file_name.removesuffix(".sql")
    if len(stem) >= 14 and stem[:14].isdigit():
        return stem[:14], stem[15:] if len(stem) > 15 and stem[14] == "_" else stem[14:]
    return "", stem


def _sql_for_metadata(sql: str) -> str:
    lines: list[str] = []
    in_block_comment = False
    for line in sql.splitlines():
        clean_line, in_block_comment = _strip_sql_line_comment(
            line,
            in_block_comment=in_block_comment,
        )
        lines.append(clean_line)
    return "\n".join(lines)


def _strip_sql_line_comment(
    line: str,
    *,
    in_block_comment: bool,
) -> tuple[str, bool]:
    index = 0
    clean: list[str] = []
    in_single_quote = False
    while index < len(line):
        current = line[index]
        next_two = line[index : index + 2]
        if in_block_comment:
            if next_two == "*/":
                in_block_comment = False
                index += 2
            else:
                index += 1
            continue
        if in_single_quote:
            clean.append(current)
            if current == "'":
                if index + 1 < len(line) and line[index + 1] == "'":
                    clean.append(line[index + 1])
                    index += 2
                    continue
                in_single_quote = False
            index += 1
            continue
        if next_two == "--":
            break
        if next_two == "/*":
            in_block_comment = True
            index += 2
            continue
        clean.append(current)
        if current == "'":
            in_single_quote = True
        index += 1
    return "".join(clean), in_block_comment


def _extract_table_names(sql: str) -> tuple[str, ...]:
    names: list[str] = []
    seen: set[str] = set()
    for match in _TABLE_NAME_PATTERN.finditer(sql):
        table_name = re.sub(r"\s*\.\s*", ".", match.group("table_name"))
        if table_name not in seen:
            names.append(table_name)
            seen.add(table_name)
    return tuple(names)


def _has_identifier(sql: str, identifier: str) -> bool:
    return re.search(
        rf"(?<![A-Za-z0-9_]){re.escape(identifier)}(?![A-Za-z0-9_])",
        sql,
        re.IGNORECASE,
    ) is not None


def _find_duplicate_timestamps(
    entries: tuple[SupabaseMigrationInventoryEntry, ...],
) -> tuple[SupabaseMigrationInventoryDuplicateTimestamp, ...]:
    file_names_by_timestamp: dict[str, list[str]] = defaultdict(list)
    for entry in entries:
        if entry.timestamp:
            file_names_by_timestamp[entry.timestamp].append(entry.file_name)
    return tuple(
        SupabaseMigrationInventoryDuplicateTimestamp(
            timestamp=timestamp,
            file_names=tuple(file_names),
        )
        for timestamp, file_names in sorted(file_names_by_timestamp.items())
        if len(file_names) > 1
    )


def _find_unsafe_durable_backend_tokens(
    entry: SupabaseMigrationInventoryEntry,
    sql_path: Path,
) -> tuple[SupabaseMigrationInventoryUnsafeDurableBackendToken, ...]:
    findings: list[SupabaseMigrationInventoryUnsafeDurableBackendToken] = []
    sql = sql_path.read_text(encoding="utf-8")
    for line_number, line in enumerate(sql.splitlines(), start=1):
        line_findings = [
            (
                match.start(),
                f"{match.group('scheme').lower()}://",
                _redact_durable_url_fragment(line, match.start()),
            )
            for match in _DURABLE_URL_PATTERN.finditer(line)
        ]
        line_findings.extend(
            (
                match.start(),
                match.group("token").lower(),
                line.strip(),
            )
            for match in _DURABLE_WORD_PATTERN.finditer(line)
        )
        for _, token, fragment in sorted(line_findings, key=lambda item: item[0]):
            findings.append(
                SupabaseMigrationInventoryUnsafeDurableBackendToken(
                    file_name=entry.file_name,
                    timestamp=entry.timestamp,
                    token=token,
                    line_number=line_number,
                    fragment=fragment,
                ),
            )
    return tuple(findings)


def _redact_durable_url_fragment(line: str, token_start: int) -> str:
    prefix = line[:token_start].strip()
    return f"{prefix}{_REDACTED_DURABLE_URL_FRAGMENT}"


def _build_summary(
    entries: tuple[SupabaseMigrationInventoryEntry, ...],
) -> SupabaseMigrationInventorySummary:
    table_names = tuple(
        dict.fromkeys(
            table_name
            for entry in entries
            for table_name in entry.table_names
        ),
    )
    return SupabaseMigrationInventorySummary(
        migration_count=len(entries),
        create_table_count=sum(entry.create_table_count for entry in entries),
        create_index_count=sum(entry.create_index_count for entry in entries),
        alter_table_count=sum(entry.alter_table_count for entry in entries),
        function_count=sum(entry.function_count for entry in entries),
        table_names=table_names,
        paper_only_migration_count=sum(entry.has_paper_only_flag for entry in entries),
        report_only_migration_count=sum(entry.has_report_only_flag for entry in entries),
        readonly_migration_count=sum(entry.has_readonly_flag for entry in entries),
    )


__all__ = (
    "SupabaseMigrationInventoryDuplicateTimestamp",
    "SupabaseMigrationInventoryEntry",
    "SupabaseMigrationInventoryReport",
    "SupabaseMigrationInventorySummary",
    "SupabaseMigrationInventoryUnsafeDurableBackendToken",
    "build_supabase_migration_inventory",
)

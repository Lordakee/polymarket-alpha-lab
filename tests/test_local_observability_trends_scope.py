"""Scope contract for the ``polymarket_alpha_lab.local_observability_trends`` module.

This Phase 1 orchestration module may read caller-selected local JSONL artifacts
through existing typed readers and feed existing pure reducers. It must not be
wired into the live ``run`` or ``strategy-cycle`` CLI branches, and it must not
grow live/API/client/order/advice surfaces of its own.
"""

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT / "src" / "polymarket_alpha_lab" / "local_observability_trends.py"
)
CLI_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "cli.py"

ALLOWED_STDLIB_IMPORTS = {
    "__future__",
    "collections",
    "collections.abc",
    "dataclasses",
    "datetime",
    "decimal",
    "pathlib",
    "typing",
}

ALLOWED_FIRST_PARTY_IMPORTS = {
    "polymarket_alpha_lab.journal": {
        "PaperTradeJournal",
        "PaperTradeRecord",
    },
    "polymarket_alpha_lab.nav_risk_metrics": {
        "PaperNavRiskMetricsConfig",
        "PaperNavRiskMetricsReport",
        "build_paper_nav_risk_metrics_report",
    },
    "polymarket_alpha_lab.nav_risk_trend": {
        "PaperNavRiskTrendConfig",
        "PaperNavRiskTrendReport",
        "build_paper_nav_risk_trend_report",
    },
    "polymarket_alpha_lab.outcome_freshness": {
        "OutcomeFreshnessConfig",
        "OutcomeFreshnessReport",
        "PaperOutcomeFreshnessConfig",
        "PaperOutcomeFreshnessReport",
        "build_outcome_freshness_report",
        "build_paper_outcome_freshness_report",
    },
    "polymarket_alpha_lab.outcome_tracker": {
        "OutcomeTrackingLog",
        "OutcomeTrackingReport",
    },
    "polymarket_alpha_lab.paper_trade_cost_audit": {
        "PaperTradeCostAuditConfig",
        "PaperTradeCostAuditReport",
        "build_paper_trade_cost_audit_report",
    },
    "polymarket_alpha_lab.paper_trade_cost_trend": {
        "PaperTradeCostTrendConfig",
        "PaperTradeCostTrendReport",
        "build_paper_trade_cost_trend_report",
    },
    "polymarket_alpha_lab.performance_summary": {
        "PerformanceSummary",
        "PerformanceSummaryConfig",
        "build_performance_summary",
    },
    "polymarket_alpha_lab.positions": {
        "PaperNavLog",
        "PaperNavSnapshot",
    },
    "polymarket_alpha_lab.strategy_audit_history": {
        "PaperStrategyRiskAuditHistoryConfig",
        "PaperStrategyRiskAuditHistoryReport",
        "build_paper_strategy_risk_audit_history_report",
    },
    "polymarket_alpha_lab.strategy_cycle": {
        "PaperStrategyCycleLog",
        "PaperStrategyCycleReport",
    },
    "polymarket_alpha_lab.strategy_evidence": {
        "PaperStrategyEvidenceSnapshotConfig",
        "PaperStrategyEvidenceSnapshotReport",
        "build_paper_strategy_evidence_snapshot_report",
    },
    "polymarket_alpha_lab.strategy_evidence_trend": {
        "PaperStrategyEvidenceTrendConfig",
        "PaperStrategyEvidenceTrendReport",
        "build_paper_strategy_evidence_trend_report",
    },
    "polymarket_alpha_lab.strategy_risk_audit": {
        "PaperStrategyRiskAuditReport",
    },
    "polymarket_alpha_lab.strategy_risk_audit_log": {
        "PaperStrategyRiskAuditLog",
    },
}

FORBIDDEN_IMPORT_FRAGMENTS = {
    "advice",
    "api",
    "auth",
    "client",
    "exchange",
    "http",
    "instruction",
    "live",
    "network",
    "order",
    "private_key",
    "rank",
    "recommend",
    "request",
    "requests",
    "urllib",
    "wallet",
}

FORBIDDEN_NAME_FRAGMENTS = {
    "accountclient",
    "advice",
    "advisory",
    "apikey",
    "apiresponse",
    "apitoken",
    "auth",
    "authenticate",
    "brokerclient",
    "clientfactory",
    "clientrequest",
    "clientsession",
    "clobclient",
    "credential",
    "exchangeclient",
    "exchangeorder",
    "fetch",
    "financialadvice",
    "httpclient",
    "investmentrank",
    "liveclient",
    "liveorder",
    "marketclient",
    "networkclient",
    "orderclient",
    "orderinstruction",
    "orderrequest",
    "privatekey",
    "rankmarket",
    "recommend",
    "requestclient",
    "requestsession",
    "signorder",
    "submitorder",
    "tradeadvice",
    "tradeinstruction",
    "wallet",
}

FORBIDDEN_LIVE_CALL_OR_ATTRIBUTE_FRAGMENTS = {
    "advice",
    "cancel",
    "client",
    "fetch",
    "listmarkets",
    "rank",
    "recommend",
    "request",
    "sign",
    "submit",
}

DIRECT_FILESYSTEM_READ_WRITE_CALL_NAMES = {
    "open",
    "read_bytes",
    "read_text",
    "write_bytes",
    "write_text",
}

PATHLIKE_MUTATION_CALL_NAMES = {
    "mkdir",
    "remove",
    "rename",
    "replace",
    "rmdir",
    "touch",
    "unlink",
}

PATHLIKE_PROBING_CALL_NAMES = {
    "exists",
    "glob",
    "is_block_device",
    "is_char_device",
    "is_dir",
    "is_fifo",
    "is_file",
    "is_junction",
    "is_mount",
    "is_socket",
    "is_symlink",
    "iterdir",
    "lstat",
    "owner",
    "readlink",
    "resolve",
    "rglob",
    "samefile",
    "stat",
    "walk",
}

MODULE_PATHLIKE_MUTATION_CALLS = {
    "os.makedirs",
    "os.mkdir",
    "os.remove",
    "os.rename",
    "os.replace",
    "os.rmdir",
    "os.unlink",
    "shutil.move",
    "shutil.rmtree",
}

MODULE_PATHLIKE_PROBING_CALLS = {
    "glob.glob",
    "glob.iglob",
    "os.listdir",
    "os.lstat",
    "os.scandir",
    "os.stat",
}

PATHLIKE_IDENTIFIER_PARTS = {
    "dir",
    "directory",
    "file",
    "path",
}

PATHLIKE_ANNOTATION_NAMES = {
    "Path",
    "PathLike",
    "PurePath",
}

ARTIFACT_LOG_PARAMETER_NAMES = {
    "cycle_log",
    "trade_log",
    "nav_log",
    "outcome_log",
    "strategy_audit_log",
}

TYPED_LOG_READER_NAMES = {
    "OutcomeTrackingLog",
    "PaperNavLog",
    "PaperStrategyCycleLog",
    "PaperStrategyRiskAuditLog",
    "PaperTradeJournal",
}

EXPECTED_LOCAL_OBSERVABILITY_TYPED_READ_CALLS = {
    "OutcomeTrackingLog.read",
    "PaperNavLog.read",
    "PaperStrategyCycleLog.read",
    "PaperStrategyRiskAuditLog.read",
    "PaperTradeJournal.read",
}

CLI_OBSERVABILITY_TREND_FRAGMENTS = {
    "localobservabilitytrend",
    "localobservabilitytrends",
    "observabilitytrend",
    "observabilitytrends",
}

CLI_OBSERVABILITY_FORBIDDEN_SURFACE_FRAGMENTS = {
    "accountclient",
    "advice",
    "advisory",
    "api",
    "apikey",
    "apitoken",
    "auth",
    "authenticate",
    "client",
    "credential",
    "exchange",
    "fetch",
    "financialadvice",
    "http",
    "instruction",
    "live",
    "network",
    "order",
    "privatekey",
    "rank",
    "recommend",
    "request",
    "session",
    "sign",
    "submit",
    "tradeadvice",
    "tradeinstruction",
    "wallet",
}

def normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def parse_module(path: Path = MODULE_PATH) -> ast.AST:
    assert path.exists(), f"missing Phase 1 scope target: {path}"
    return ast.parse(path.read_text(encoding="utf-8"))


def imported_modules(tree: ast.AST) -> tuple[str, ...]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            modules.append(node.module or "")
    return tuple(modules)


def imported_alias_fragments(tree: ast.AST) -> tuple[str, ...]:
    fragments: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                fragments.append(alias.name)
                if alias.asname is not None:
                    fragments.append(alias.asname)
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                fragments.append(node.module)
            for alias in node.names:
                fragments.append(alias.name)
                if alias.asname is not None:
                    fragments.append(alias.asname)
    return tuple(fragments)


def imported_first_party_symbols(tree: ast.AST) -> dict[str, set[str]]:
    symbols: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module.startswith("polymarket_alpha_lab.")
        ):
            symbols.setdefault(node.module, set()).update(
                alias.name for alias in node.names
            )
    return symbols


def ast_identifier_fragments(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.keyword) and node.arg is not None:
            names.add(node.arg)
        elif isinstance(node, ast.alias):
            names.add(node.name)
            if node.asname is not None:
                names.add(node.asname)
    return names


def call_or_attribute_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call):
        return call_or_attribute_name(node.func)
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _qualified_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_qualified_name(node.value)}.{node.attr}"
    if isinstance(node, ast.Call):
        return f"{_qualified_name(node.func)}(...)"
    return type(node).__name__


def _walk_scope(scope: ast.AST | list[ast.stmt]) -> tuple[ast.AST, ...]:
    if isinstance(scope, ast.AST):
        return tuple(ast.walk(scope))
    nodes: list[ast.AST] = []
    for statement in scope:
        nodes.extend(ast.walk(statement))
    return tuple(nodes)


def _assigned_names(target: ast.AST) -> tuple[str, ...]:
    if isinstance(target, ast.Name):
        return (target.id,)
    if isinstance(target, (ast.Tuple, ast.List)):
        names: list[str] = []
        for element in target.elts:
            names.extend(_assigned_names(element))
        return tuple(names)
    return ()


def _call_receiver(node: ast.Call) -> ast.AST | None:
    if isinstance(node.func, ast.Attribute):
        return node.func.value
    return None


def _receiver_fragments(node: ast.AST) -> set[str]:
    fragments: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            fragments.add(child.id)
        elif isinstance(child, ast.Attribute):
            fragments.add(child.attr)
    return fragments


def _identifier_parts(value: str) -> tuple[str, ...]:
    parts: list[str] = []
    current: list[str] = []
    for character in value:
        if character == "_" or not character.isalnum():
            if current:
                parts.append("".join(current))
                current = []
            continue
        if character.isupper() and current:
            parts.append("".join(current))
            current = []
        current.append(character.lower())
    if current:
        parts.append("".join(current))
    return tuple(parts)


def _is_pathlike_fragment(value: str) -> bool:
    if value in ARTIFACT_LOG_PARAMETER_NAMES:
        return True
    return any(part in PATHLIKE_IDENTIFIER_PARTS for part in _identifier_parts(value))


def _expression_uses_pathlike_binding(
    node: ast.AST,
    pathlike_bindings: set[str],
) -> bool:
    return any(
        isinstance(child, ast.Name) and child.id in pathlike_bindings
        for child in ast.walk(node)
    )


def _annotation_mentions_path(node: ast.AST | None) -> bool:
    if node is None:
        return False
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and child.id in PATHLIKE_ANNOTATION_NAMES:
            return True
        if (
            isinstance(child, ast.Attribute)
            and child.attr in PATHLIKE_ANNOTATION_NAMES
        ):
            return True
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            try:
                string_annotation = ast.parse(child.value, mode="eval").body
            except SyntaxError:
                if any(
                    part in PATHLIKE_IDENTIFIER_PARTS
                    for part in _identifier_parts(child.value)
                ):
                    return True
            else:
                if _annotation_mentions_path(string_annotation):
                    return True
    return False


def _is_pathlike_expression(
    node: ast.AST,
    *,
    pathlike_bindings: set[str],
) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Call) and call_or_attribute_name(child) == "Path":
            return True
    if _expression_uses_pathlike_binding(node, pathlike_bindings):
        return True

    for fragment in _receiver_fragments(node):
        if _is_pathlike_fragment(fragment):
            return True
    return False


def _pathlike_bindings(scope: ast.AST | list[ast.stmt]) -> set[str]:
    bindings: set[str] = set()
    for node in _walk_scope(scope):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            arguments = (
                *node.args.posonlyargs,
                *node.args.args,
                *node.args.kwonlyargs,
            )
            for argument in arguments:
                if (
                    argument.arg in ARTIFACT_LOG_PARAMETER_NAMES
                    or _annotation_mentions_path(argument.annotation)
                ):
                    bindings.add(argument.arg)
            if node.args.vararg is not None and _annotation_mentions_path(
                node.args.vararg.annotation,
            ):
                bindings.add(node.args.vararg.arg)
            if node.args.kwarg is not None and _annotation_mentions_path(
                node.args.kwarg.annotation,
            ):
                bindings.add(node.args.kwarg.arg)
        if isinstance(node, ast.Assign) and _is_pathlike_expression(
            node.value,
            pathlike_bindings=bindings,
        ):
            for target in node.targets:
                bindings.update(_assigned_names(target))
        elif (
            isinstance(node, ast.AnnAssign)
            and node.value is not None
            and _is_pathlike_expression(
                node.value,
                pathlike_bindings=bindings,
            )
        ):
            bindings.update(_assigned_names(node.target))
    return bindings


def _is_typed_log_reader_name(name: str | None) -> bool:
    return name in TYPED_LOG_READER_NAMES


def _is_typed_log_constructor(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    return _is_typed_log_reader_name(call_or_attribute_name(node.func))


def _typed_log_bindings(scope: ast.AST | list[ast.stmt]) -> set[str]:
    bindings: set[str] = set()
    for node in _walk_scope(scope):
        if isinstance(node, ast.Assign) and _is_typed_log_constructor(node.value):
            for target in node.targets:
                bindings.update(_assigned_names(target))
        elif isinstance(node, ast.AnnAssign) and _is_typed_log_constructor(
            node.value,
        ):
            bindings.update(_assigned_names(node.target))
    return bindings


def _is_typed_log_read_call(node: ast.Call) -> bool:
    if not isinstance(node.func, ast.Attribute) or node.func.attr != "read":
        return False
    return _is_typed_log_reader_name(call_or_attribute_name(node.func.value))


def _is_open_call(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and call_or_attribute_name(node) == "open"


def _is_log_append_call(node: ast.Call, typed_log_bindings: set[str]) -> bool:
    if not isinstance(node.func, ast.Attribute) or node.func.attr != "append":
        return False

    receiver = node.func.value
    if _is_typed_log_constructor(receiver):
        return True
    if _is_typed_log_reader_name(call_or_attribute_name(receiver)):
        return True
    return isinstance(receiver, ast.Name) and receiver.id in typed_log_bindings


def _call_has_pathlike_argument(
    node: ast.Call,
    *,
    pathlike_bindings: set[str],
) -> bool:
    return any(
        _is_pathlike_expression(argument, pathlike_bindings=pathlike_bindings)
        for argument in (
            *node.args,
            *(keyword.value for keyword in node.keywords),
        )
    )


def _direct_io_violation(
    node: ast.Call,
    *,
    allow_typed_log_reads: bool,
    pathlike_bindings: set[str],
    typed_log_bindings: set[str],
) -> str | None:
    call_name = call_or_attribute_name(node)
    if call_name is None:
        return None
    normalized = normalize_identifier(call_name)
    display = _qualified_name(node.func)

    if display in MODULE_PATHLIKE_MUTATION_CALLS and _call_has_pathlike_argument(
        node,
        pathlike_bindings=pathlike_bindings,
    ):
        return f"path mutation call: {display}"

    if display in MODULE_PATHLIKE_PROBING_CALLS and _call_has_pathlike_argument(
        node,
        pathlike_bindings=pathlike_bindings,
    ):
        return f"path probing call: {display}"

    if normalized in {
        normalize_identifier(name) for name in DIRECT_FILESYSTEM_READ_WRITE_CALL_NAMES
    }:
        return f"direct filesystem read/write call: {display}"

    receiver = _call_receiver(node)
    if receiver is not None and normalized in {
        normalize_identifier(name) for name in PATHLIKE_MUTATION_CALL_NAMES
    }:
        if _is_pathlike_expression(receiver, pathlike_bindings=pathlike_bindings):
            return f"path mutation call: {display}"

    if receiver is not None and normalized in {
        normalize_identifier(name) for name in PATHLIKE_PROBING_CALL_NAMES
    }:
        if _is_pathlike_expression(receiver, pathlike_bindings=pathlike_bindings):
            return f"path probing call: {display}"

    if _is_log_append_call(node, typed_log_bindings):
        return f"typed log append call: {display}"

    if _is_typed_log_read_call(node):
        if allow_typed_log_reads:
            return None
        return f"typed log read call is not allowed here: {display}"

    if receiver is not None and normalized == "read" and _is_open_call(receiver):
        return f"direct filesystem read call: {display}"

    return None


def _direct_io_violations(
    scope: ast.AST | list[ast.stmt],
    *,
    allow_typed_log_reads: bool,
) -> tuple[str, ...]:
    pathlike_bindings = _pathlike_bindings(scope)
    typed_log_bindings = _typed_log_bindings(scope)
    violations: list[str] = []
    for node in _walk_scope(scope):
        if not isinstance(node, ast.Call):
            continue
        violation = _direct_io_violation(
            node,
            allow_typed_log_reads=allow_typed_log_reads,
            pathlike_bindings=pathlike_bindings,
            typed_log_bindings=typed_log_bindings,
        )
        if violation is not None:
            violations.append(violation)
    return tuple(violations)


def _read_call_displays(scope: ast.AST | list[ast.stmt]) -> tuple[str, ...]:
    displays: list[str] = []
    for node in _walk_scope(scope):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "read"
        ):
            displays.append(_qualified_name(node.func))
    return tuple(displays)


def _normalized_contains_fragment(value: str, fragments: set[str]) -> bool:
    normalized = normalize_identifier(value)
    return any(normalize_identifier(fragment) in normalized for fragment in fragments)


def test_local_observability_trends_module_exists():
    assert MODULE_PATH.exists()


def test_local_observability_trends_imports_only_local_readers_and_reducers():
    tree = parse_module()

    for module_name in imported_modules(tree):
        if module_name.startswith("polymarket_alpha_lab."):
            assert module_name in ALLOWED_FIRST_PARTY_IMPORTS, module_name
            continue
        top_level = module_name.split(".", 1)[0]
        assert top_level in ALLOWED_STDLIB_IMPORTS, module_name


def test_local_observability_trends_imports_no_forbidden_surfaces():
    tree = parse_module()

    for imported_name in imported_alias_fragments(tree):
        normalized = normalize_identifier(imported_name)
        for fragment in FORBIDDEN_IMPORT_FRAGMENTS:
            assert normalize_identifier(fragment) not in normalized, (
                imported_name,
                fragment,
            )


def test_local_observability_trends_uses_only_allowed_first_party_symbols():
    tree = parse_module()

    for module_name, symbols in imported_first_party_symbols(tree).items():
        assert module_name in ALLOWED_FIRST_PARTY_IMPORTS, module_name
        assert symbols <= ALLOWED_FIRST_PARTY_IMPORTS[module_name], (
            module_name,
            symbols - ALLOWED_FIRST_PARTY_IMPORTS[module_name],
        )


def test_local_observability_trends_does_not_import_first_party_modules_wholesale():
    tree = parse_module()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Import):
            continue
        for alias in node.names:
            assert not alias.name.startswith("polymarket_alpha_lab."), alias.name


def test_local_observability_trends_does_not_define_live_or_advice_names():
    tree = parse_module()
    normalized_names = {
        normalize_identifier(name) for name in ast_identifier_fragments(tree)
    }

    for fragment in FORBIDDEN_NAME_FRAGMENTS:
        assert not any(
            normalize_identifier(fragment) in name for name in normalized_names
        ), (fragment, normalized_names)


def test_direct_io_scope_checker_flags_filesystem_calls_and_typed_log_appends():
    tree = ast.parse(
        "Path('artifact.jsonl').read_text()\n"
        "Path('artifact.jsonl').write_text('payload')\n"
        "Path('artifact.jsonl').exists()\n"
        "Path('artifact.jsonl').stat()\n"
        "Path('artifacts').glob('*.jsonl')\n"
        "Path('artifacts').iterdir()\n"
        "artifact_path.is_file()\n"
        "log_dir.rglob('*.jsonl')\n"
        "target = Path('artifact.jsonl')\n"
        "target.exists()\n"
        "base = Path('artifacts')\n"
        "child = base / 'artifact.jsonl'\n"
        "child.stat()\n"
        "def runner(cycle_log: Path | str, nav_log: Path | str):\n"
        "    cycle_log.exists()\n"
        "    nav_log.stat()\n"
        "def cli_runner(args):\n"
        "    os.remove(args.cycle_log)\n"
        "    os.stat(args.nav_log)\n"
        "    glob.glob(args.outcome_log)\n"
        "    shutil.rmtree(args.strategy_audit_log)\n"
        "open('artifact.jsonl').read()\n"
        "PaperTradeJournal(path).append(record)\n"
        "audit_log = PaperStrategyRiskAuditLog(path)\n"
        "audit_log.append(report)\n",
    )

    violations = _direct_io_violations(tree, allow_typed_log_reads=True)

    assert "direct filesystem read/write call: Path(...).read_text" in violations
    assert "direct filesystem read/write call: Path(...).write_text" in violations
    assert "path probing call: Path(...).exists" in violations
    assert "path probing call: Path(...).stat" in violations
    assert "path probing call: Path(...).glob" in violations
    assert "path probing call: Path(...).iterdir" in violations
    assert "path probing call: artifact_path.is_file" in violations
    assert "path probing call: log_dir.rglob" in violations
    assert "path probing call: target.exists" in violations
    assert "path probing call: child.stat" in violations
    assert "path probing call: cycle_log.exists" in violations
    assert "path probing call: nav_log.stat" in violations
    assert "path mutation call: os.remove" in violations
    assert "path probing call: os.stat" in violations
    assert "path probing call: glob.glob" in violations
    assert "path mutation call: shutil.rmtree" in violations
    assert "direct filesystem read/write call: open" in violations
    assert "direct filesystem read call: open(...).read" in violations
    assert "typed log append call: PaperTradeJournal(...).append" in violations
    assert "typed log append call: audit_log.append" in violations


def test_direct_io_scope_checker_allows_in_memory_operations_and_typed_reads():
    tree = ast.parse(
        "items = []\n"
        "items.append(record)\n"
        "text = text.replace('a', 'b')\n"
        "payload.write('memory only')\n"
        "payload.read()\n"
        "metadata.exists()\n"
        "records.stat()\n"
        "items.glob('*.jsonl')\n"
        "children.iterdir()\n"
        "dialog.exists()\n"
        "profile.stat()\n"
        "audit_log.records.stat()\n"
        "log_match.group(1)\n"
        "path_match.group(1)\n"
        "file_match.group(1)\n"
        "directory_match.group(1)\n"
        "PaperTradeJournal.read(path)\n",
    )

    assert _direct_io_violations(tree, allow_typed_log_reads=True) == ()


def test_direct_io_scope_checker_flags_artifact_log_parameter_probes():
    tree = ast.parse(
        "def runner(\n"
        "    *,\n"
        "    cycle_log,\n"
        "    trade_log,\n"
        "    nav_log,\n"
        "    outcome_log,\n"
        "    strategy_audit_log,\n"
        "):\n"
        "    cycle_log.exists()\n"
        "    trade_log.exists()\n"
        "    nav_log.stat()\n"
        "    outcome_log.glob('*.jsonl')\n"
        "    strategy_audit_log.iterdir()\n",
    )

    violations = _direct_io_violations(tree, allow_typed_log_reads=True)

    assert "path probing call: cycle_log.exists" in violations
    assert "path probing call: trade_log.exists" in violations
    assert "path probing call: nav_log.stat" in violations
    assert "path probing call: outcome_log.glob" in violations
    assert "path probing call: strategy_audit_log.iterdir" in violations


def test_direct_io_scope_checker_flags_annotated_pathlike_parameter_probes():
    tree = ast.parse(
        "def runner(\n"
        "    *,\n"
        "    cycle_log: 'Path | str',\n"
        "    trade_log: pathlib.Path | str,\n"
        "    nav_log: Path | str,\n"
        "):\n"
        "    cycle_log.exists()\n"
        "    trade_log.stat()\n"
        "    nav_log.iterdir()\n",
    )

    violations = _direct_io_violations(tree, allow_typed_log_reads=True)

    assert "path probing call: cycle_log.exists" in violations
    assert "path probing call: trade_log.stat" in violations
    assert "path probing call: nav_log.iterdir" in violations


def test_local_observability_trends_calls_no_live_or_advice_surfaces():
    tree = parse_module()

    for node in ast.walk(tree):
        candidate = None
        if isinstance(node, ast.Call):
            candidate = call_or_attribute_name(node)
        elif isinstance(node, ast.Attribute):
            candidate = node.attr
        if candidate is None:
            continue
        normalized = normalize_identifier(candidate)
        for fragment in FORBIDDEN_LIVE_CALL_OR_ATTRIBUTE_FRAGMENTS:
            assert normalize_identifier(fragment) not in normalized, (
                candidate,
                fragment,
            )


def test_local_observability_trends_has_no_direct_filesystem_or_append_calls():
    tree = parse_module()

    assert _direct_io_violations(tree, allow_typed_log_reads=True) == ()


def test_local_observability_trends_reads_only_existing_typed_logs():
    tree = parse_module()
    read_calls = _read_call_displays(tree)

    assert set(read_calls) == EXPECTED_LOCAL_OBSERVABILITY_TYPED_READ_CALLS
    assert len(read_calls) == len(EXPECTED_LOCAL_OBSERVABILITY_TYPED_READ_CALLS)


def _is_args_command(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "command"
        and isinstance(node.value, ast.Name)
        and node.value.id == "args"
    )


def _is_command_literal(node: ast.AST, command: str) -> bool:
    return isinstance(node, ast.Constant) and node.value == command


def _command_test_matches(test: ast.AST, command: str) -> bool:
    if isinstance(test, ast.BoolOp):
        return any(_command_test_matches(value, command) for value in test.values)
    if not isinstance(test, ast.Compare) or len(test.ops) != 1:
        return False
    if not isinstance(test.ops[0], ast.Eq) or len(test.comparators) != 1:
        return False
    comparator = test.comparators[0]
    return (
        _is_args_command(test.left)
        and _is_command_literal(comparator, command)
    ) or (
        _is_command_literal(test.left, command)
        and _is_args_command(comparator)
    )


def _command_branch_bodies(tree: ast.AST, command: str) -> list[list[ast.stmt]]:
    branches: list[list[ast.stmt]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and _command_test_matches(node.test, command):
            branches.append(node.body)
    return branches


def _single_command_branch(tree: ast.AST, command: str) -> list[ast.stmt]:
    branches = _command_branch_bodies(tree, command)
    assert len(branches) == 1, (command, len(branches))
    return branches[0]


def _branch_references(branch: list[ast.stmt]) -> set[str]:
    references: set[str] = set()
    for statement in branch:
        for node in ast.walk(statement):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                references.add(node.name)
            elif isinstance(node, ast.Name):
                references.add(node.id)
            elif isinstance(node, ast.Attribute):
                references.add(node.attr)
            elif isinstance(node, ast.arg):
                references.add(node.arg)
            elif isinstance(node, ast.keyword) and node.arg is not None:
                references.add(node.arg)
            elif isinstance(node, ast.alias):
                references.add(node.name)
                if node.asname is not None:
                    references.add(node.asname)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                references.add(node.value)
    return references


def _branch_call_names(branch: list[ast.stmt]) -> tuple[str, ...]:
    call_names: list[str] = []
    for statement in branch:
        for node in ast.walk(statement):
            if not isinstance(node, ast.Call):
                continue
            candidate = call_or_attribute_name(node)
            if candidate is not None:
                call_names.append(candidate)
    return tuple(call_names)


def _command_parser_variable(tree: ast.AST, command: str) -> str:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        call = node.value
        if not isinstance(call, ast.Call):
            continue
        if call_or_attribute_name(call) != "add_parser":
            continue
        if not call.args or not _is_command_literal(call.args[0], command):
            continue
        return target.id
    raise AssertionError(f"missing parser variable for {command}")


def _parser_argument_surface(
    tree: ast.AST,
    parser_variable: str,
) -> set[str]:
    references: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if call_or_attribute_name(node) != "add_argument":
            continue
        func = node.func
        if (
            not isinstance(func, ast.Attribute)
            or not isinstance(func.value, ast.Name)
            or func.value.id != parser_variable
        ):
            continue
        for arg in node.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                references.add(arg.value)
        for keyword in node.keywords:
            if keyword.arg != "dest":
                continue
            if isinstance(keyword.value, ast.Constant) and isinstance(
                keyword.value.value,
                str,
            ):
                references.add(keyword.value.value)
    return references


def test_cli_run_and_strategy_cycle_branches_do_not_wire_observability_trends():
    tree = parse_module(CLI_PATH)

    for command in ("run", "strategy-cycle"):
        branches = _command_branch_bodies(tree, command)
        assert branches, command
        references = set()
        for branch in branches:
            references.update(_branch_references(branch))
        normalized_references = {
            normalize_identifier(reference) for reference in references
        }
        for fragment in CLI_OBSERVABILITY_TREND_FRAGMENTS:
            assert not any(
                normalize_identifier(fragment) in reference
                for reference in normalized_references
            ), (command, fragment, normalized_references)


def test_cli_observability_trends_branch_has_no_direct_live_or_advice_surfaces():
    tree = parse_module(CLI_PATH)
    branch = _single_command_branch(tree, "observability-trends")
    normalized_references = {
        normalize_identifier(reference) for reference in _branch_references(branch)
    }

    for fragment in CLI_OBSERVABILITY_FORBIDDEN_SURFACE_FRAGMENTS:
        assert not any(
            normalize_identifier(fragment) in reference
            for reference in normalized_references
        ), (fragment, normalized_references)


def test_cli_observability_trends_parser_surface_has_no_live_or_advice_options():
    tree = parse_module(CLI_PATH)
    parser_variable = _command_parser_variable(tree, "observability-trends")
    references = _parser_argument_surface(tree, parser_variable)
    normalized_references = {
        normalize_identifier(reference) for reference in references
    }

    assert references == {
        "--cycle-log",
        "cycle_log",
        "--trade-log",
        "trade_log",
        "--nav-log",
        "nav_log",
        "--outcome-log",
        "outcome_log",
        "--strategy-audit-log",
        "strategy_audit_log",
        "--outcome-stale-after-seconds",
        "outcome_stale_after_seconds",
        "--persist",
        "persist",
    }
    for fragment in CLI_OBSERVABILITY_FORBIDDEN_SURFACE_FRAGMENTS:
        assert not any(
            normalize_identifier(fragment) in reference
            for reference in normalized_references
        ), (fragment, normalized_references)


def test_cli_observability_trends_branch_has_no_direct_filesystem_or_append_calls():
    tree = parse_module(CLI_PATH)
    branch = _single_command_branch(tree, "observability-trends")

    assert "observability_trends_runner" in _branch_call_names(branch)
    assert _direct_io_violations(branch, allow_typed_log_reads=False) == ()

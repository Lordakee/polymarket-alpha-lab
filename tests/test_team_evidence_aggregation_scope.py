from __future__ import annotations
import ast
from dataclasses import MISSING, fields
from decimal import Decimal
import importlib
import inspect
from pathlib import Path
import re
import pytest
ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src" / "polymarket_alpha_lab"
HARD_FLAGS = ("paper_only", "report_only", "readonly")
PRODUCTION_LINE_LIMITS = {
    "team_evidence_aggregation_types.py": 900, "team_evidence_aggregation_codec.py": 500,
    "team_evidence_aggregation_temporal.py": 300, "team_evidence_aggregation_allocation.py": 450,
    "team_evidence_aggregation_witness.py": 650, "team_evidence_aggregation.py": 700,
}
TEST_LINE_LIMITS = {
    "test_team_evidence_aggregation_types.py": 900, "test_team_evidence_aggregation_codec.py": 600,
    "test_team_evidence_aggregation_temporal.py": 450, "test_team_evidence_aggregation_allocation.py": 600,
    "test_team_evidence_aggregation_witness.py": 900, "test_team_evidence_aggregation.py": 900,
    "test_team_evidence_aggregation_scope.py": 500,
}
PRODUCTION_TOTAL_LINE_LIMIT = 3_500
TEST_TOTAL_LINE_LIMIT = 4_850
IMPORT_ALLOWLISTS = {
    "team_evidence_aggregation_types": {"__future__", "collections", "dataclasses", "datetime", "decimal", "re", "typing"},
    "team_evidence_aggregation_codec": {"__future__", "dataclasses", "datetime", "decimal", "hashlib", "json", "typing", "polymarket_alpha_lab.team_evidence_aggregation_types"},
    "team_evidence_aggregation_temporal": {"__future__", "datetime", "decimal", "typing", "polymarket_alpha_lab.team_evidence_aggregation_types"},
    "team_evidence_aggregation_allocation": {"__future__", "decimal", "typing", "polymarket_alpha_lab.team_evidence_aggregation_types"},
    "team_evidence_aggregation_witness": {"__future__", "collections", "datetime", "decimal", "typing", "polymarket_alpha_lab.team_evidence_aggregation_types", "polymarket_alpha_lab.team_evidence_aggregation_allocation"},
    "team_evidence_aggregation": {"__future__", "dataclasses", "decimal", "typing", "polymarket_alpha_lab.team_evidence_aggregation_types", "polymarket_alpha_lab.team_evidence_aggregation_codec", "polymarket_alpha_lab.team_evidence_aggregation_temporal", "polymarket_alpha_lab.team_evidence_aggregation_allocation", "polymarket_alpha_lab.team_evidence_aggregation_witness"},
}
PUBLIC_EXPORTS = {
    "team_evidence_aggregation_types": (
        "TeamEvidenceSourceLineage", "TeamEvidenceCapture", "TeamEvidenceRevision", "TeamEvidenceAssessmentRevision",
        "TeamEvidenceAggregationRecord", "TeamEvidenceCurrentRevisionSelection", "TeamEvidenceAggregationInput",
        "TeamEvidenceRequirement", "TeamEvidenceAggregationConfig", "TeamEvidenceTemporalAssessment",
        "TeamEvidenceWeightAllocation", "TeamEvidenceRequirementWitness", "TeamEvidenceRequirementCoverage",
        "TeamEvidenceDiagnosticRow", "TeamEvidenceContradictionResult", "TeamEvidenceAggregationResult",
        "validate_team_evidence_aggregation_input_contract", "select_team_evidence_canonical_current_records",
        "select_team_evidence_canonical_capture_records",
    ),
    "team_evidence_aggregation_codec": ("team_evidence_aggregation_config_payload", "team_evidence_aggregation_input_payload", "team_evidence_aggregation_config_digest", "team_evidence_aggregation_core_payload", "team_evidence_aggregation_payload", "team_evidence_aggregation_core_digest", "validate_team_evidence_aggregation_core_digest"),
    "team_evidence_aggregation_temporal": ("assess_team_evidence_temporal",),
    "team_evidence_aggregation_allocation": ("allocate_team_evidence_weights",),
    "team_evidence_aggregation_witness": ("build_team_evidence_requirement_coverage",),
    "team_evidence_aggregation": ("build_team_evidence_aggregation_result", "validate_team_evidence_aggregation_result"),
}
FORBIDDEN_COMPONENTS = frozenset(
    "account adapter api auth authenticate authentication authorization browser callback callable "
    "cache cached caches cli client credential credentials csv database databases db dsn env "
    "environ environment external fetch file files filesystem http https jsonl legacy live "
    "loader logging log logger migration migrations modules network packet persist persistence postgres "
    "postgresql process processes random randomness repository request requests scraper supabase "
    "scraping secret service services socket sockets sql store stores storage subprocess token "
    "tokens trade trades trading wallet order orders sign signing execution exchange sizing float inspect introspect sys "
    "introspection reflection builtins temporary tempfile tmp password passwd io shell command decoder decode replay".split()
)
FORBIDDEN_EXACT_IDENTIFIERS = frozenset(("__dict__", "__file__", "__loader__", "__mro__", "__spec__", "__subclasses__"))
FORBIDDEN_SEQUENCES = frozenset(
    (
        ("api", "key"), ("secret", "key"), ("private", "key"), ("key", "material"),
        ("hosted", "account"), ("capital", "allocation"), ("allocation", "to", "capital"),
        ("exchange", "mutation"), ("runtime", "introspection"), ("order", "submission"),
        ("order", "cancellation"), ("order", "replacement"), ("live", "trading"),
        ("legacy", "projection"), ("forecast", "packet"), ("run", "id"), ("replay", "id"),
        ("forecast", "id"), ("evidence", "aggregation", "id"), ("forecast", "evidence", "id"),
        ("team", "evidence", "aggregation", "id"),
        ("team", "forecast", "result", "id"), ("team", "forecast", "evidence", "id"),
    )
)
FORBIDDEN_CALLS = frozenset(
    "__import__ breakpoint choice choices commit compile connect delattr delete dir eval exec execute executemany execv execve "
    "float fork getenv getrandbits globals hash hasattr help id import_module input locals now open "
    "popen post print put random randint randrange read_bytes read_text recv repr request send "
    "rollback setattr shuffle spawn system timestamp today total_seconds uniform urandom utcnow vars write_bytes "
    "write_text".split()
)
OUTER_LITERALS = ("tea:v1", "tfr:v1", "tfe:v1", "btc", "bitcoin", "0.020000", "0.980000")
WORD_RE = re.compile(r"[A-Z]+(?=[A-Z][a-z]|[^A-Za-z]|$)|[A-Z]?[a-z]+|[0-9]+")
BUILD_EXPORT = "build_team_evidence_aggregation_result"
VALIDATE_EXPORT = "validate_team_evidence_aggregation_result"
TYPE_PARAMETER_NODES = tuple(getattr(ast, name) for name in ("TypeVar", "TypeVarTuple", "ParamSpec") if hasattr(ast, name))
DYNAMIC_GETATTR_FORMS = {
    "team_evidence_aggregation_types": (
        (1, "current", "id_name", False), (1, "node", "id_name", False), (1, "node", "previous_digest_name", False), (2, "node", "previous_id_name", False), (1, "normalized", "name", False), (1, "predecessor", "digest_name", False), (1, "projection", "digest_name", False), (1, "projection", "id_name", False), (1, "record", "path", False), (21, "self", "name", False), (3, "value", "name", False),
    ),
    "team_evidence_aggregation_codec": ((1, "normalized", "name", False), (1, "value", "name", False)),
    "team_evidence_aggregation_temporal": ((1, "value", "flag", True),),
    "team_evidence_aggregation_allocation": ((1, "normalized", "name", False), (1, "value", "field_name", True), (2, "value", "name", False)),
    "team_evidence_aggregation_witness": ((1, "normalized", "name", False), (1, "record", "layer_name", False), (1, "record", "name", True), (1, "typed_config", "field_name", True), (1, "value", "field_name", True), (2, "value", "name", False)),
}
PACKAGE_REFLECTION_NAMES = frozenset("__delitem__ __dict__ __import__ __setitem__ append clear compile delattr dir eval exec extend getattr globals hasattr import_module insert locals modules pop remove setdefault setattr sys update vars".split())
def _source(module: str) -> str: return (PACKAGE / f"{module}.py").read_text(encoding="utf-8")
def _tree(module: str) -> ast.Module: return ast.parse(_source(module), filename=f"{module}.py")
def _dotted(node: ast.AST) -> str: return node.id if isinstance(node, ast.Name) else f"{_dotted(node.value)}.{node.attr}".lstrip(".") if isinstance(node, ast.Attribute) else ""
def _words(value: str) -> tuple[str, ...]: return tuple(part.lower() for part in WORD_RE.findall(value))
def _forbidden_identifier(value: str) -> bool:
    words = _words(value)
    return bool(value in FORBIDDEN_EXACT_IDENTIFIERS or set(words) & FORBIDDEN_COMPONENTS or any(words[index:index + len(sequence)] == sequence for sequence in FORBIDDEN_SEQUENCES for index in range(len(words) - len(sequence) + 1)))
def _semantic_identifiers(tree: ast.AST) -> tuple[str, ...]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name): names.append(node.id)
        elif isinstance(node, ast.Attribute): names.append(node.attr)
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef): names.append(node.name)
        elif isinstance(node, ast.arg): names.append(node.arg)
        elif isinstance(node, ast.keyword) and node.arg is not None: names.append(node.arg)
        elif isinstance(node, ast.ExceptHandler) and node.name is not None: names.append(node.name)
        elif isinstance(node, ast.Global | ast.Nonlocal): names.extend(node.names)
        elif isinstance(node, ast.MatchAs | ast.MatchStar) and node.name is not None: names.append(node.name)
        elif isinstance(node, ast.MatchMapping) and node.rest is not None: names.append(node.rest)
        elif isinstance(node, ast.MatchClass): names.extend(node.kwd_attrs)
        elif isinstance(node, TYPE_PARAMETER_NODES): names.append(node.name)
        elif isinstance(node, ast.Import): names.extend(alias.asname for alias in node.names if alias.asname is not None)
        elif isinstance(node, ast.ImportFrom):
            names.extend(alias.name for alias in node.names)
            names.extend(alias.asname for alias in node.names if alias.asname is not None)
    return tuple(names)
def _binding_names(tree: ast.AST, *, skip_ids: set[int] | frozenset[int] = frozenset()) -> tuple[str, ...]:
    names: list[str] = []
    for node in ast.walk(tree):
        if id(node) in skip_ids: continue
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef): names.append(node.name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store | ast.Del): names.append(node.id)
        elif isinstance(node, ast.arg): names.append(node.arg)
        elif isinstance(node, ast.Import): names.extend(alias.asname or alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom): names.extend(alias.asname or alias.name for alias in node.names)
        elif isinstance(node, ast.ExceptHandler) and node.name is not None: names.append(node.name)
        elif isinstance(node, ast.Global | ast.Nonlocal): names.extend(node.names)
        elif isinstance(node, ast.MatchAs | ast.MatchStar) and node.name is not None: names.append(node.name)
        elif isinstance(node, ast.MatchMapping) and node.rest is not None: names.append(node.rest)
        elif isinstance(node, TYPE_PARAMETER_NODES): names.append(node.name)
    return tuple(names)
def _invalid_from_import(node: ast.ImportFrom) -> bool: return node.level != 0 or not node.module or any(alias.name == "*" for alias in node.names)
def _literal_exports(tree: ast.Module) -> tuple[str, ...]:
    assignments = [node for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets)]
    assert len(assignments) == 1; assignment = assignments[0]
    assert len(assignment.targets) == 1 and isinstance(assignment.targets[0], ast.Name) and assignment.targets[0].id == "__all__"
    assert isinstance(assignment.value, ast.Tuple); assert all(isinstance(item, ast.Constant) and type(item.value) is str for item in assignment.value.elts)
    exports = tuple(item.value for item in assignment.value.elts)
    assert len(exports) == len(set(exports)); assert _binding_names(tree).count("__all__") == 1; return exports
def _assert_direct_export_ownership(module: str, tree: ast.Module) -> None:
    exports = set(PUBLIC_EXPORTS[module]); class_exports = set(PUBLIC_EXPORTS["team_evidence_aggregation_types"][:16]) if module == "team_evidence_aggregation_types" else set()
    direct = [node for node in tree.body if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) and node.name in exports]
    assert len(direct) == len(exports) and {node.name for node in direct} == exports; assert all(type(node) is (ast.ClassDef if node.name in class_exports else ast.FunctionDef) for node in direct); assert exports.isdisjoint(_binding_names(tree, skip_ids={id(node) for node in direct}))
def _annotation_has_float(annotation: ast.AST) -> bool: return any(isinstance(node, ast.Name) and node.id == "float" or isinstance(node, ast.Attribute) and node.attr == "float" or isinstance(node, ast.Constant) and node.value == "float" for node in ast.walk(annotation))
def _function_arguments(node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[ast.arg, ...]: return tuple(argument for argument in (*node.args.posonlyargs, *node.args.args, node.args.vararg, *node.args.kwonlyargs, node.args.kwarg) if argument is not None)
def _normalized_call_name(value: str) -> str: return "_".join(_words(value))
def _forbidden_call_name(value: str) -> bool: return value in FORBIDDEN_CALLS or _normalized_call_name(value) in FORBIDDEN_CALLS
def _is_getattr_call(node: ast.AST, resolvers: set[str] | frozenset[str] = frozenset(("getattr",))) -> bool: return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in resolvers
def _resolver_aliases(tree: ast.Module) -> tuple[frozenset[str], frozenset[int]]:
    assignments = [node for node in ast.walk(tree) if isinstance(node, ast.Assign) and isinstance(node.value, ast.Name)]
    resolvers = {"getattr"}
    while added := {target.id for node in assignments if node.value.id in resolvers for target in node.targets if isinstance(target, ast.Name)} - resolvers:
        resolvers.update(added)
    direct, approved = {id(node) for node in tree.body}, set()
    for node in assignments:
        if node.value.id not in resolvers: continue
        assert id(node) in direct and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name), node.lineno; approved.add(id(node))
    return frozenset(resolvers), frozenset(approved)
def _assert_getattr_results_not_called(tree: ast.AST, resolvers: frozenset[str], resolver_assignments: frozenset[int]) -> None:
    parents = {id(child): node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    def scopes(node: ast.AST) -> tuple[int, ...]:
        values, child = [], node
        while parent := parents.get(id(child)):
            if isinstance(parent, ast.Lambda) and child is parent.body or isinstance(parent, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) and child in parent.body: values.append(id(parent))
            child = parent
        return (*values, 0)
    def expression_names(node: ast.AST) -> set[tuple[int, str]]: return {(scope, name) for item in ast.walk(node) if isinstance(item, ast.Name | ast.Attribute) and (name := _dotted(item)) for scope in scopes(item)}
    def target_names(node: ast.AST) -> set[tuple[int, str]]:
        if isinstance(node, ast.Name | ast.Attribute): return {(scopes(node)[0], _dotted(node))}
        if isinstance(node, ast.Subscript): return {(scopes(node)[0], _dotted(node.value))} if _dotted(node.value) else set()
        if isinstance(node, ast.Starred): return target_names(node.value)
        if isinstance(node, ast.List | ast.Tuple): return set().union(*(target_names(item) for item in node.elts))
        return set()
    def alias_names(node: ast.AST) -> set[tuple[int, str]]: return expression_names(node) if isinstance(node, ast.Name | ast.Attribute) else set()
    def returns_getattr_result(node: ast.AST) -> bool: return _is_getattr_call(node, resolvers) or isinstance(node, ast.IfExp) and (returns_getattr_result(node.body) or returns_getattr_result(node.orelse)) or isinstance(node, ast.BoolOp) and any(returns_getattr_result(item) for item in node.values) or isinstance(node, ast.NamedExpr | ast.Starred) and returns_getattr_result(node.value)
    dangerous: set[tuple[int, str]] = set(); edges: set[tuple[tuple[int, str], tuple[int, str]]] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign): targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign | ast.AugAssign | ast.NamedExpr): targets, value = (node.target,), node.value
        else: continue
        if value is None or id(node) in resolver_assignments: continue
        names = set().union(*(target_names(target) for target in targets))
        unpacked = any(isinstance(target, ast.List | ast.Tuple) for target in targets) and isinstance(value, ast.List | ast.Tuple) and any(returns_getattr_result(item) for item in value.elts)
        if returns_getattr_result(value) or unpacked: assert names, node.lineno; dangerous.update(names)
        else: edges.update((target, source) for target_node in targets if isinstance(target_node, ast.Name | ast.Attribute) for target in target_names(target_node) for source in alias_names(value))
    while added := {target for target, source in edges if source in dangerous} - dangerous: dangerous.update(added)
    for node in (item for item in ast.walk(tree) if isinstance(item, ast.Call)):
        assert not any(_is_getattr_call(item, resolvers) for item in ast.walk(node.func)), node.lineno; assert dangerous.isdisjoint(expression_names(node.func)), sorted(dangerous & expression_names(node.func))
def _assert_clean_ast(module: str, tree: ast.Module, *, reviewed: bool = False) -> None:
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
            spellings = (alias.asname for alias in node.names if alias.asname is not None)
        elif isinstance(node, ast.ImportFrom):
            assert not _invalid_from_import(node), (module, node.lineno)
            imported_modules.append(node.module)
            spellings = (value for alias in node.names for value in (alias.name, alias.asname) if value is not None)
        else: continue
        assert not any(_forbidden_call_name(value) or _normalized_call_name(value) == "getattr" for value in spellings), (module, node.lineno)
    assert set(imported_modules) <= IMPORT_ALLOWLISTS[module]
    parents = {id(child): node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    resolvers, resolver_assignments = _resolver_aliases(tree)
    dynamic_forms: dict[tuple[str, str, bool], int] = {}
    for name in _semantic_identifiers(tree):
        assert not _forbidden_identifier(name), (module, name)
    for node in ast.walk(tree):
        assert not (isinstance(node, ast.Constant) and type(node.value) is float), (module, node.lineno)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            assert not _forbidden_identifier(node.value), (module, node.value)
        if isinstance(node, ast.Name | ast.Attribute):
            target = _dotted(node)
            terminal = target.rsplit(".", 1)[-1]
            assert not _forbidden_call_name(terminal) or target in {"re.compile", "object.__setattr__"}, (module, target)
            if target == "object.__setattr__":
                parent = parents[id(node)]; assert module == "team_evidence_aggregation_types" and isinstance(parent, ast.Call) and parent.func is node and not parent.keywords and len(parent.args) == 3 and isinstance(parent.args[0], ast.Name) and parent.args[0].id == "self", (module, target)
            assert not (isinstance(node, ast.Attribute) and _normalized_call_name(terminal) == "getattr"), (module, target)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in resolvers:
            parent = parents[id(node)]
            assert isinstance(parent, ast.Call) and parent.func is node or id(parent) in resolver_assignments and isinstance(parent, ast.Assign) and parent.value is node, (module, node.id)
        if _is_getattr_call(node, resolvers):
            parent = parents[id(node)]
            assert not (isinstance(parent, ast.Call) and parent.func is node), (module, node.lineno)
            assert not node.keywords and 2 <= len(node.args) <= 3 and not any(isinstance(item, ast.Starred) for item in node.args), (module, node.lineno)
            resolved = node.args[1]
            if isinstance(resolved, ast.Constant) and type(resolved.value) is str:
                assert not _forbidden_identifier(resolved.value) and not _forbidden_call_name(resolved.value), (module, resolved.value)
            else:
                assert reviewed
                assert isinstance(node.args[0], ast.Name) and isinstance(resolved, ast.Name)
                assert isinstance(node.args[0].ctx, ast.Load) and isinstance(resolved.ctx, ast.Load)
                assert len(node.args) == 2 or isinstance(node.args[2], ast.Constant) and node.args[2].value is None
                form = (node.args[0].id, resolved.id, len(node.args) == 3)
                dynamic_forms[form] = dynamic_forms.get(form, 0) + 1
        if isinstance(node, ast.FormattedValue):
            assert node.conversion not in {ord("a"), ord("r")}, (module, node.lineno)
        if isinstance(node, ast.ExceptHandler):
            assert node.type is not None
            assert not any(
                _dotted(item).rsplit(".", 1)[-1] in {"Exception", "BaseException"}
                for item in ast.walk(node.type)
                if isinstance(item, ast.Name | ast.Attribute)
            )
    _assert_getattr_results_not_called(tree, resolvers, resolver_assignments)
    if reviewed:
        expected = {(object_name, terminal, has_default): count for count, object_name, terminal, has_default in DYNAMIC_GETATTR_FORMS.get(module, ())}
        assert dynamic_forms == expected, (module, dynamic_forms)
    if module == "team_evidence_aggregation":
        assert not any(
            isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add)
            and any(isinstance(item, ast.Constant) and type(item.value) is str for item in ast.walk(node))
            for node in ast.walk(tree)
        )
    annotations = [
        node.annotation for node in ast.walk(tree)
        if isinstance(node, ast.arg | ast.AnnAssign) and node.annotation is not None
    ]
    annotations.extend(
        node.returns for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.returns is not None
    )
    assert not any(_annotation_has_float(annotation) for annotation in annotations)
    for function in (node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)):
        called = {
            call.func.id for call in ast.walk(function)
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
        }
        for argument in _function_arguments(function):
            if argument.arg in called:
                assert (
                    isinstance(argument.annotation, ast.Subscript)
                    and _dotted(argument.annotation.value) == "type"
                )
def _config_values(**changes: object) -> dict[str, object]:
    values: dict[str, object] = {
        "config_version": "scope-guard-v1",
        "max_evidence_age_seconds": Decimal("0.000000"), "max_capture_lag_seconds": Decimal("0.000000"),
        "independence_group_weight_cap": Decimal("1.000000"), "correlation_group_weight_cap": Decimal("1.000000"),
        "max_requirement_assignments_per_evidence": 32,
        "contradiction_no_probability_max": Decimal("0.250000"), "contradiction_yes_probability_min": Decimal("0.750000"),
        "contradiction_watch_score": Decimal("0.250000"), "contradiction_block_score": Decimal("0.750000"),
        "publish_probability_floor": Decimal("0.000000"), "publish_probability_ceiling": Decimal("1.000000"),
        "maximum_records": 128, "maximum_requirements": 32,
        "maximum_requirement_memberships": 1024, "maximum_witness_edges": 256,
        "requirements": (),
    }
    values.update(changes)
    return values
def _facade_tree(build: str | None = None, extra: str = "") -> ast.Module:
    build = build or f"def {BUILD_EXPORT}(): pass"
    return ast.parse(f"__all__ = {PUBLIC_EXPORTS['team_evidence_aggregation']!r}\n{build}\ndef {VALIDATE_EXPORT}(): pass\n{extra}")
def _accepted_sources(check, cases) -> tuple[str, ...]:
    accepted = []
    for label, source in cases:
        try: check(ast.parse(source))
        except AssertionError: continue
        accepted.append(label)
    return tuple(accepted)
def test_node_2_unified_ast_import_export_forbidden_surface_and_line_size_gate() -> None:
    synthetic_identifiers = (
        "wallet = 1", "value.wallet", "def wallet(): pass", "async def wallet(): pass",
        "class Wallet: pass", "def f(wallet): pass", "f(wallet=1)",
        "try:\n    raise ValueError\nexcept ValueError as wallet:\n    pass",
        "def f():\n    global wallet",
        "def outer():\n    def inner():\n        nonlocal wallet",
        "from decimal import Wallet", "from decimal import Decimal as wallet",
        "import decimal as wallet", "match None:\n    case wallet: pass",
        "match []:\n    case [*wallet]: pass", "match {}:\n    case {**wallet}: pass",
        "match object():\n    case object(wallet): pass", "match object():\n    case object(wallet=value): pass",
    )
    for source in synthetic_identifiers:
        assert any(_forbidden_identifier(name) for name in _semantic_identifiers(ast.parse(source)))
    for module, source in (("team_evidence_aggregation", "import decimal as arithmetic"), ("team_evidence_aggregation", "from decimal import _benign as _arithmetic"), ("team_evidence_aggregation_witness", "import datetime as clock"), ("team_evidence_aggregation_witness", "from datetime import datetime as clock")):
        _assert_clean_ast(module, ast.parse(source))
    for module, source in (("team_evidence_aggregation", "import decimal.extra"), ("team_evidence_aggregation", "from .decimal import Decimal"), ("team_evidence_aggregation", "from decimal import *"), ("team_evidence_aggregation", "import polymarket_alpha_lab"), ("team_evidence_aggregation", "from decimal import _getattr as resolve"), ("team_evidence_aggregation_witness", "import datetime as clock; clock.now()"), ("team_evidence_aggregation_witness", "from datetime import datetime as clock; clock.utcnow()"), ("team_evidence_aggregation_witness", "import datetime as _clock; _clock._now()"), ("team_evidence_aggregation_witness", "from datetime import _utcnow as _clock; _clock()")):
        with pytest.raises(AssertionError):
            _assert_clean_ast(module, ast.parse(source))
    assert _invalid_from_import(ast.ImportFrom(module=None, names=[ast.alias(name="Decimal")], level=0))
    spoof = ast.parse("from polymarket_alpha_lab.team_evidence_aggregation_witness import build_team_evidence_requirement_coverage as build_team_evidence_aggregation_result, build_team_evidence_requirement_coverage as validate_team_evidence_aggregation_result\n__all__ = ('build_team_evidence_aggregation_result', 'validate_team_evidence_aggregation_result')")
    with pytest.raises(AssertionError):
        _assert_direct_export_ownership("team_evidence_aggregation", spoof)
    for build, extra in (
        (None, f"import decimal as {BUILD_EXPORT}"), (None, f"{BUILD_EXPORT} = None"), (None, f"({BUILD_EXPORT} := None)"),
        (None, f"def helper():\n    def {BUILD_EXPORT}(): pass"), (f"async def {BUILD_EXPORT}(): pass", ""),
        (f"class {BUILD_EXPORT}: pass", ""), (None, f"def {BUILD_EXPORT}(): pass"),
        (None, f"match {{'x': 1}}:\n    case {{**{BUILD_EXPORT}}}: pass"),
        (None, f"if False:\n    match {{}}:\n        case {{**{BUILD_EXPORT}}}: pass"),
    ):
        with pytest.raises(AssertionError):
            _assert_direct_export_ownership("team_evidence_aggregation", _facade_tree(build, extra))
    for extra in (f"holder.{BUILD_EXPORT} = None", f"text = '{BUILD_EXPORT}'  # {BUILD_EXPORT}"):
        _assert_direct_export_ownership("team_evidence_aggregation", _facade_tree(extra=extra))
    for rebind in ("import decimal as __all__", "def __all__(): pass", "del __all__", "match {}:\n    case {**__all__}: pass"):
        with pytest.raises(AssertionError):
            _literal_exports(_facade_tree(extra=rebind))
    if hasattr(ast, "TypeVar"):
        for prefix in ("", "*", "**"):
            with pytest.raises(AssertionError):
                _assert_direct_export_ownership("team_evidence_aggregation", _facade_tree(extra=f"def helper[{prefix}{BUILD_EXPORT}](): pass"))
            assert "wallet" in _semantic_identifiers(ast.parse(f"def helper[{prefix}wallet](): pass"))
    for source in (
        "import dataclasses as d\ngetattr(d.sys.modules['os'], 'system')('true')", "import dataclasses as d\nvalue = getattr(d, 'system')",
        "import dataclasses as d\ninvoke = d.sys.modules['os'].system\ninvoke('true')", "invoke = print\ninvoke('not executed')",
        "import dataclasses as d\nvalue = d.sys", "import dataclasses as d\nvalue = d.sys.modules",
    ):
        with pytest.raises(AssertionError):
            _assert_clean_ast("team_evidence_aggregation", ast.parse(source))
    unsafe = _accepted_sources(lambda tree: _assert_clean_ast("team_evidence_aggregation", tree), (
        ("starred-literal", "import dataclasses as d\ngetattr(*(d, 'system'))"),
        ("aliased-forbidden", "import dataclasses as d\nresolve = getattr\nresolve(d, 'system')"),
        ("aliased-dynamic", "import dataclasses as d\nresolve = getattr\nfield = 'fields'\nresolve(d, field)"),
        ("resolver-nested-before", "import dataclasses as d\nif True:\n    base = getattr\nresolve = base\nresolve(d, 'system')"),
        ("resolver-nested-after", "import dataclasses as d\nresolve = base\nif True:\n    base = getattr\nresolve(d, 'system')"),
        ("resolver-attribute-target", "import dataclasses as d\nholder.resolve = getattr\nholder.resolve(d, 'system')"),
        ("result-alias-before", "import dataclasses as d\nvalue = getattr(d, 'fields')\ninvoke = value\ninvoke()"),
        ("result-alias-after", "import dataclasses as d\ninvoke = value\nvalue = getattr(d, 'fields')\ninvoke()"),
        ("result-attribute-target", "import dataclasses as d\nholder.invoke = getattr(d, 'fields')\nholder.invoke()"),
        ("result-subscript-assigned-called", "import dataclasses as d\nholder[0] = getattr(d, 'fields')\nholder[0]()"), ("result-list-unpack-called", "import dataclasses as d\n[invoke] = [getattr(d, 'fields')]\ninvoke()"),
        ("result-immediate-list-called", "import dataclasses as d\n[getattr(d, 'fields')][0]()"), ("result-immediate-dict-called", "import dataclasses as d\n{'key': getattr(d, 'fields')}['key']()"),
        ("result-if-expression-called", "import dataclasses as d\n(getattr(d, 'fields') if condition else fallback)()"), ("result-bool-expression-called", "import dataclasses as d\n(getattr(d, 'fields') or fallback)()"),
        ("assembled-terminal", "import dataclasses as d\na=''.join(('s','ys')); b=''.join(('mod','ules')); c=''.join(('o','s')); e=''.join(('s','ys','tem'))\ngetattr(getattr(getattr(d, a), b)[c], e)('not executed')"),
        ("dynamic-setattr", "import dataclasses as d\nsetattr(d, ''.join(('pro', 'cess')), None)"),
        ("dynamic-delattr", "import dataclasses as d\ndelattr(d, ''.join(('pro', 'cess')))"),
        ("dynamic-hasattr", "import dataclasses as d\nhasattr(d, ''.join(('pro', 'cess')))"),
    ))
    safe = (("literal-safe", "import dataclasses as d\nvalue = getattr(d, 'fields')"), ("alias-literal-safe", "import dataclasses as d\nresolve = getattr\nvalue = resolve(d, 'fields')")); accepted = _accepted_sources(lambda tree: _assert_clean_ast("team_evidence_aggregation", tree), safe)
    assert not unsafe and accepted == tuple(label for label, _ in safe), (unsafe, accepted)
    for source in ("globals().update({'value': 1})", "del locals()['value']", "vars().update({'value': 1})", "setattr(object, 'value', 1)", "object.__setattr__(target, 'value', 1)", "value.__dict__['field'] = 1"):
        with pytest.raises(AssertionError): _assert_clean_ast("team_evidence_aggregation", ast.parse(source))
    assert (sum(count for forms in DYNAMIC_GETATTR_FORMS.values() for count, *_ in forms), sum(map(len, DYNAMIC_GETATTR_FORMS.values()))) == (48, 23)
    for module, expected_exports in PUBLIC_EXPORTS.items():
        tree = _tree(module)
        _assert_clean_ast(module, tree, reviewed=True)
        assert _literal_exports(tree) == expected_exports
        _assert_direct_export_ownership(module, tree)
        source = _source(module).lower()
        assert all(literal not in source for literal in OUTER_LITERALS)
    production_counts = {name: len((PACKAGE / name).read_text(encoding="utf-8").splitlines()) for name in PRODUCTION_LINE_LIMITS}
    test_counts = {name: len((ROOT / "tests" / name).read_text(encoding="utf-8").splitlines()) for name in TEST_LINE_LIMITS}
    assert all(production_counts[name] <= limit for name, limit in PRODUCTION_LINE_LIMITS.items())
    assert all(test_counts[name] <= limit for name, limit in TEST_LINE_LIMITS.items())
    assert sum(production_counts.values()) <= PRODUCTION_TOTAL_LINE_LIMIT
    assert sum(test_counts.values()) <= TEST_TOTAL_LINE_LIMIT
def test_node_2_public_dataclasses_are_frozen_slotted_final_and_hard_flagged() -> None:
    tree = _tree("team_evidence_aggregation_types"); public_classes = PUBLIC_EXPORTS["team_evidence_aggregation_types"][:16]
    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
    assert set(public_classes) == {name for name in classes if name.startswith("TeamEvidence")}
    for name in public_classes:
        node = classes[name]; assert len(node.bases) == 1 and _dotted(node.bases[0]) == "_ExactPublicDataclass"; assert len(node.decorator_list) == 2 and _dotted(node.decorator_list[0]) == "final"
        decorator = node.decorator_list[1]; assert isinstance(decorator, ast.Call) and _dotted(decorator.func) == "dataclass"; assert not decorator.args
        assert {item.arg: ast.literal_eval(item.value) for item in decorator.keywords} == {"frozen": True, "slots": True}
        declared = [item for item in node.body if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)]; flag_fields = [item for item in declared if item.target.id in HARD_FLAGS]
        assert tuple(item.target.id for item in flag_fields) == HARD_FLAGS
        assert all(_dotted(item.annotation) == "bool" and isinstance(item.value, ast.Constant) and item.value.value is True for item in flag_fields)
    base = classes["_ExactPublicDataclass"]; guard = next(item for item in base.body if isinstance(item, ast.FunctionDef) and item.name == "__init_subclass__")
    assert any(isinstance(item, ast.Raise) and isinstance(item.exc, ast.Call) and _dotted(item.exc.func) == "TypeError" for item in ast.walk(guard))
    module = importlib.import_module("polymarket_alpha_lab.team_evidence_aggregation_types")
    for name in public_classes:
        with pytest.raises(TypeError):
            type(f"Illegal{name}", (getattr(module, name),), {})
def test_node_2_config_policy_fields_have_no_defaults_and_hard_maxima_fail_closed() -> None:
    tree = _tree("team_evidence_aggregation_types")
    config_node = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "TeamEvidenceAggregationConfig")
    declared = [item for item in config_node.body if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)]
    assert all(item.value is None for item in declared if item.target.id not in HARD_FLAGS)
    module = importlib.import_module("polymarket_alpha_lab.team_evidence_aggregation_types")
    config_type = module.TeamEvidenceAggregationConfig
    policy_fields = [field for field in fields(config_type) if field.name not in HARD_FLAGS]
    signature = inspect.signature(config_type)
    assert all(field.default is MISSING for field in policy_fields)
    assert all(signature.parameters[field.name].default is inspect.Parameter.empty for field in policy_fields)
    assert not any("MAX" in name for name in PUBLIC_EXPORTS["team_evidence_aggregation_types"])
    assert config_type(**_config_values())
    for field_name, invalid_value in (
        ("max_requirement_assignments_per_evidence", 33), ("maximum_records", 129),
        ("maximum_requirements", 33), ("maximum_requirement_memberships", 1025), ("maximum_witness_edges", 257),
    ):
        with pytest.raises(ValueError):
            config_type(**_config_values(**{field_name: invalid_value}))
def _package_binding_names(tree: ast.Module) -> tuple[str, ...]:
    parents = {id(child): node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    comprehension_targets = {id(target) for node in ast.walk(tree) if isinstance(node, ast.comprehension) for target in ast.walk(node.target)}
    def is_local(node: ast.AST) -> bool:
        child = node
        while parent := parents.get(id(child)):
            if isinstance(parent, ast.Lambda) and child is parent.body: return True
            if isinstance(parent, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) and child in parent.body: return True
            child = parent
        return False
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Global): names.extend(node.names); continue
        if is_local(node): continue
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store | ast.Del) and id(node) not in comprehension_targets: names.append(node.id)
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef): names.append(node.name)
        elif isinstance(node, ast.Import): names.extend(alias.asname or alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom): names.extend(alias.asname or alias.name for alias in node.names)
        elif isinstance(node, ast.ExceptHandler) and node.name is not None: names.append(node.name)
        elif isinstance(node, ast.MatchAs | ast.MatchStar) and node.name is not None: names.append(node.name)
        elif isinstance(node, ast.MatchMapping) and node.rest is not None: names.append(node.rest)
    return tuple(names)
def _assert_package_root(tree: ast.Module) -> None:
    forbidden = set().union(*PUBLIC_EXPORTS.values())
    bindings = _package_binding_names(tree)
    assert forbidden.isdisjoint(bindings)
    assert not any(name in PACKAGE_REFLECTION_NAMES or _normalized_call_name(name) in PACKAGE_REFLECTION_NAMES for name in _semantic_identifiers(tree))
    assert not any(
        isinstance(node, ast.Constant) and node.value in {"__all__", "__dict__"}
        or isinstance(node, ast.Name) and node.id == "__all__" and isinstance(node.ctx, ast.Load)
        or isinstance(node, ast.Attribute | ast.Subscript) and isinstance(node.ctx, ast.Store | ast.Del)
        for node in ast.walk(tree)
    )
    if "__all__" not in bindings:
        return
    assignments = [node for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets)]
    assert bindings.count("__all__") == len(assignments) == 1
    assignment = assignments[0]
    assert len(assignment.targets) == 1 and isinstance(assignment.targets[0], ast.Name) and assignment.targets[0].id == "__all__"
    assert isinstance(assignment.value, ast.Tuple | ast.List)
    assert all(isinstance(item, ast.Constant) and type(item.value) is str for item in assignment.value.elts)
    assert forbidden.isdisjoint(item.value for item in assignment.value.elts)
def test_node_2_package_root_has_no_node_2_public_exports() -> None:
    _assert_package_root(ast.parse((PACKAGE / "__init__.py").read_text(encoding="utf-8"), filename="__init__.py"))
    for source in (
        f"__all__ = []\ndef {BUILD_EXPORT}(): return 1\n__all__.append('{BUILD_EXPORT}')", f"class {BUILD_EXPORT}: pass",
        f"match {{}}:\n    case {{**{BUILD_EXPORT}}}: pass", f"__all__ = []\n__all__.append('{BUILD_EXPORT}')",
        f"__all__ = []\n__all__ += ('{BUILD_EXPORT}',)",
    ):
        with pytest.raises(AssertionError):
            _assert_package_root(ast.parse(source))
    assert not (accepted := _accepted_sources(_assert_package_root, (
        ("function-default", f"def helper(value=({BUILD_EXPORT} := None)): pass"), ("function-decorator", f"@({BUILD_EXPORT} := (lambda value: value))\ndef helper(): pass"), ("function-annotation", f"def helper(value: ({BUILD_EXPORT} := object)): pass"),
        ("class-base", f"class Helper(({BUILD_EXPORT} := object)): pass"), ("class-keyword", f"class Helper(metaclass=({BUILD_EXPORT} := type)): pass"), ("class-decorator", f"@({BUILD_EXPORT} := (lambda value: value))\nclass Helper: pass"),
        ("comprehension-walrus", f"[({BUILD_EXPORT} := value) for value in (None,)]"), ("globals-all", f"__all__ = []\nglobals()['__all__'].append('{BUILD_EXPORT}')"), ("vars-all", f"__all__ = []\nvars()['__all__'].append('{BUILD_EXPORT}')"),
        ("class-global-export", f"class Helper:\n    global {BUILD_EXPORT}\n    {BUILD_EXPORT} = 1"), ("function-global-export", f"def helper():\n    global {BUILD_EXPORT}\n    {BUILD_EXPORT} = 1\nhelper()"), ("function-global-delete", f"def helper():\n    global {BUILD_EXPORT}\n    del {BUILD_EXPORT}"),
        ("class-global-all-replace", f"__all__ = []\nclass Helper:\n    global __all__\n    __all__ = ['{BUILD_EXPORT}']"), ("all-alias-append", f"__all__ = []\nalias = __all__\nalias.append('{BUILD_EXPORT}')"), ("all-unbound-append", f"__all__ = []\nlist.append(__all__, '{BUILD_EXPORT}')"),
        ("setattr-modules-all", f"__all__ = []\nimport sys\nsetattr(sys.modules[__name__], '__all__', ['{BUILD_EXPORT}'])"), ("setattr-modules-export", f"import sys\nsetattr(sys.modules[__name__], '{BUILD_EXPORT}', 1)"),
        ("modules-delete-all", "__all__ = []\nimport sys\nnamespace = sys.modules[__name__]\ndel namespace['__all__']"), ("modules-update-export", f"import sys\nnamespace = sys.modules[__name__]\nnamespace.update({{'{BUILD_EXPORT}': 1}})"),
    ))), ", ".join(accepted)
    local_controls = (("function-local-protected", f"def helper():\n    {BUILD_EXPORT} = None"), ("class-local-protected", f"class Helper:\n    {BUILD_EXPORT} = None"), ("lambda-body-local", f"value = lambda: ({BUILD_EXPORT} := None)"), ("comprehension-target-local", f"[None for {BUILD_EXPORT} in ()]"), ("nonlocal-control", f"def outer():\n    {BUILD_EXPORT} = None\n    def inner():\n        nonlocal {BUILD_EXPORT}\n        {BUILD_EXPORT} = 1"))
    assert _accepted_sources(_assert_package_root, local_controls) == tuple(label for label, _ in local_controls)
    for source in (f"__all__ = []\nnamespace = globals()\ndel namespace['__all__']", f"namespace = locals()\nnamespace.update({{'{BUILD_EXPORT}': 1}})", "module.__dict__['value'] = 1", "namespace = module.__dict__", f"exec('{BUILD_EXPORT} = None')"):
        with pytest.raises(AssertionError): _assert_package_root(ast.parse(source))
    _assert_package_root(ast.parse("__all__ = ('ExistingExport',)\nfrom decimal import Decimal as ExistingExport"))
    _assert_package_root(ast.parse("def helper():\n    local_result = None\n    import decimal as arithmetic\nclass Helper:\n    local_result = None\n[None for local_result in ()]"))
def test_node_2_has_no_outer_identity_packet_legacy_or_persistence_surface() -> None:
    for module in PUBLIC_EXPORTS:
        source = _source(module)
        tree = ast.parse(source, filename=f"{module}.py")
        assert all(literal not in source.lower() for literal in OUTER_LITERALS)
        strings = tuple(node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str))
        for value in (*_semantic_identifiers(tree), *strings):
            assert not _forbidden_identifier(value), (module, value)

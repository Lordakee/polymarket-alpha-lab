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
    "team_evidence_aggregation_types.py": 900,
    "team_evidence_aggregation_codec.py": 500,
    "team_evidence_aggregation_temporal.py": 300,
    "team_evidence_aggregation_allocation.py": 450,
    "team_evidence_aggregation_witness.py": 650,
    "team_evidence_aggregation.py": 700,
}
TEST_LINE_LIMITS = {
    "test_team_evidence_aggregation_types.py": 900,
    "test_team_evidence_aggregation_codec.py": 600,
    "test_team_evidence_aggregation_temporal.py": 450,
    "test_team_evidence_aggregation_allocation.py": 600,
    "test_team_evidence_aggregation_witness.py": 900,
    "test_team_evidence_aggregation.py": 900,
    "test_team_evidence_aggregation_scope.py": 500,
}
PRODUCTION_TOTAL_LINE_LIMIT = 3_500
TEST_TOTAL_LINE_LIMIT = 4_850

IMPORT_ALLOWLISTS = {
    "team_evidence_aggregation_types": {
        "__future__", "collections", "dataclasses", "datetime", "decimal", "re", "typing",
    },
    "team_evidence_aggregation_codec": {
        "__future__", "dataclasses", "datetime", "decimal", "hashlib", "json", "typing",
        "polymarket_alpha_lab.team_evidence_aggregation_types",
    },
    "team_evidence_aggregation_temporal": {
        "__future__", "datetime", "decimal", "typing",
        "polymarket_alpha_lab.team_evidence_aggregation_types",
    },
    "team_evidence_aggregation_allocation": {
        "__future__", "decimal", "typing",
        "polymarket_alpha_lab.team_evidence_aggregation_types",
    },
    "team_evidence_aggregation_witness": {
        "__future__", "collections", "datetime", "decimal", "typing",
        "polymarket_alpha_lab.team_evidence_aggregation_types",
        "polymarket_alpha_lab.team_evidence_aggregation_allocation",
    },
    "team_evidence_aggregation": {
        "__future__", "dataclasses", "decimal", "typing",
        "polymarket_alpha_lab.team_evidence_aggregation_types",
        "polymarket_alpha_lab.team_evidence_aggregation_codec",
        "polymarket_alpha_lab.team_evidence_aggregation_temporal",
        "polymarket_alpha_lab.team_evidence_aggregation_allocation",
        "polymarket_alpha_lab.team_evidence_aggregation_witness",
    },
}
PUBLIC_EXPORTS = {
    "team_evidence_aggregation_types": (
        "TeamEvidenceSourceLineage", "TeamEvidenceCapture", "TeamEvidenceRevision",
        "TeamEvidenceAssessmentRevision", "TeamEvidenceAggregationRecord",
        "TeamEvidenceCurrentRevisionSelection", "TeamEvidenceAggregationInput",
        "TeamEvidenceRequirement", "TeamEvidenceAggregationConfig",
        "TeamEvidenceTemporalAssessment", "TeamEvidenceWeightAllocation",
        "TeamEvidenceRequirementWitness", "TeamEvidenceRequirementCoverage",
        "TeamEvidenceDiagnosticRow", "TeamEvidenceContradictionResult",
        "TeamEvidenceAggregationResult", "validate_team_evidence_aggregation_input_contract",
        "select_team_evidence_canonical_current_records",
        "select_team_evidence_canonical_capture_records",
    ),
    "team_evidence_aggregation_codec": (
        "team_evidence_aggregation_config_payload",
        "team_evidence_aggregation_input_payload",
        "team_evidence_aggregation_config_digest",
        "team_evidence_aggregation_core_payload",
        "team_evidence_aggregation_payload",
        "team_evidence_aggregation_core_digest",
        "validate_team_evidence_aggregation_core_digest",
    ),
    "team_evidence_aggregation_temporal": ("assess_team_evidence_temporal",),
    "team_evidence_aggregation_allocation": ("allocate_team_evidence_weights",),
    "team_evidence_aggregation_witness": (
        "build_team_evidence_requirement_coverage",
    ),
    "team_evidence_aggregation": (
        "build_team_evidence_aggregation_result",
        "validate_team_evidence_aggregation_result",
    ),
}

FORBIDDEN_COMPONENTS = frozenset(
    "account adapter api auth authenticate authentication authorization browser callback callable "
    "cache cached caches cli client credential credentials csv database databases db dsn env "
    "environ environment external fetch file files filesystem http https jsonl legacy live "
    "loader logging log logger migration migrations network packet persist persistence postgres "
    "postgresql process processes random randomness repository request requests scraper supabase "
    "scraping secret service services socket sockets sql store stores storage subprocess token "
    "tokens trade trades trading wallet order orders sign signing execution exchange sizing float inspect introspect "
    "introspection reflection builtins temporary tempfile tmp password passwd io shell command decoder decode replay".split()
)
FORBIDDEN_EXACT_IDENTIFIERS = frozenset(("__dict__", "__file__", "__loader__", "__mro__", "__spec__", "__subclasses__"))
FORBIDDEN_SEQUENCES = frozenset(
    (
        ("api", "key"), ("secret", "key"), ("private", "key"),
        ("key", "material"), ("hosted", "account"), ("capital", "allocation"),
        ("allocation", "to", "capital"), ("exchange", "mutation"),
        ("runtime", "introspection"),
        ("order", "submission"), ("order", "cancellation"),
        ("order", "replacement"), ("live", "trading"), ("legacy", "projection"),
        ("forecast", "packet"), ("run", "id"), ("replay", "id"),
        ("forecast", "id"), ("evidence", "aggregation", "id"),
        ("forecast", "evidence", "id"), ("team", "evidence", "aggregation", "id"),
        ("team", "forecast", "result", "id"), ("team", "forecast", "evidence", "id"),
    )
)
FORBIDDEN_CALLS = frozenset(
    "__import__ breakpoint choice choices commit compile connect delete delattr dir eval exec execute "
    "executemany execv execve float fork getattr getenv getrandbits globals hasattr hash help id "
    "import_module input locals now open popen post print put random randint randrange read_bytes "
    "read_text recv repr request send rollback setattr shuffle spawn system timestamp today "
    "total_seconds uniform urandom utcnow vars write_bytes write_text".split()
)
OUTER_LITERALS = ("tea:v1", "tfr:v1", "tfe:v1", "btc", "bitcoin", "0.020000", "0.980000")
WORD_RE = re.compile(r"[A-Z]+(?=[A-Z][a-z]|[^A-Za-z]|$)|[A-Z]?[a-z]+|[0-9]+")


def _source(module: str) -> str:
    return (PACKAGE / f"{module}.py").read_text(encoding="utf-8")


def _tree(module: str) -> ast.Module:
    return ast.parse(_source(module), filename=f"{module}.py")


def _dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_dotted(node.value)}.{node.attr}".lstrip(".")
    return ""


def _words(value: str) -> tuple[str, ...]:
    return tuple(part.lower() for part in WORD_RE.findall(value))


def _forbidden_identifier(value: str) -> bool:
    words = _words(value)
    return bool(
        value in FORBIDDEN_EXACT_IDENTIFIERS
        or set(words) & FORBIDDEN_COMPONENTS
        or any(
            words[index:index + len(sequence)] == sequence
            for sequence in FORBIDDEN_SEQUENCES
            for index in range(len(words) - len(sequence) + 1)
        )
    )


def _semantic_identifiers(tree: ast.AST) -> tuple[str, ...]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.append(node.id)
        elif isinstance(node, ast.Attribute):
            names.append(node.attr)
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.append(node.name)
        elif isinstance(node, ast.arg):
            names.append(node.arg)
        elif isinstance(node, ast.keyword) and node.arg is not None:
            names.append(node.arg)
        elif isinstance(node, ast.ExceptHandler) and node.name is not None:
            names.append(node.name)
        elif isinstance(node, ast.Global | ast.Nonlocal):
            names.extend(node.names)
        elif isinstance(node, ast.Import):
            names.extend(alias.asname for alias in node.names if alias.asname is not None)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.append(alias.name)
                if alias.asname is not None:
                    names.append(alias.asname)
        elif isinstance(node, ast.MatchAs | ast.MatchStar) and node.name is not None:
            names.append(node.name)
        elif isinstance(node, ast.MatchMapping) and node.rest is not None:
            names.append(node.rest)
        elif isinstance(node, ast.MatchClass):
            names.extend(node.kwd_attrs)
    return tuple(names)


def _invalid_from_import(node: ast.ImportFrom) -> bool:
    return node.level != 0 or not node.module or any(alias.name == "*" for alias in node.names)


def _literal_exports(tree: ast.Module) -> tuple[str, ...]:
    assignments = [
        node for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets)
    ]
    assert len(assignments) == 1
    assignment = assignments[0]
    assert len(assignment.targets) == 1
    assert isinstance(assignment.targets[0], ast.Name)
    assert assignment.targets[0].id == "__all__"
    assert isinstance(assignment.value, ast.Tuple)
    assert all(isinstance(item, ast.Constant) and type(item.value) is str for item in assignment.value.elts)
    exports = tuple(item.value for item in assignment.value.elts)
    assert len(exports) == len(set(exports))
    assert sum(
        isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and node.id == "__all__"
        for node in ast.walk(tree)
    ) == 1
    return exports


def _annotation_has_float(annotation: ast.AST) -> bool:
    return any(
        isinstance(node, ast.Name) and node.id == "float"
        or isinstance(node, ast.Attribute) and node.attr == "float"
        or isinstance(node, ast.Constant) and node.value == "float"
        for node in ast.walk(annotation)
    )


def _function_arguments(node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[ast.arg, ...]:
    return tuple(
        argument for argument in (
            *node.args.posonlyargs, *node.args.args, node.args.vararg,
            *node.args.kwonlyargs, node.args.kwarg,
        ) if argument is not None
    )


def _assert_clean_ast(module: str, tree: ast.Module) -> None:
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert not _invalid_from_import(node), (module, node.lineno)
            imported_modules.append(node.module)
    assert set(imported_modules) <= IMPORT_ALLOWLISTS[module]

    for name in _semantic_identifiers(tree):
        assert not _forbidden_identifier(name), (module, name)
    for node in ast.walk(tree):
        assert not (isinstance(node, ast.Constant) and type(node.value) is float), (module, node.lineno)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            assert not _forbidden_identifier(node.value), (module, node.value)
        if isinstance(node, ast.Call):
            target = _dotted(node.func)
            call_name = target.rsplit(".", 1)[-1]
            if call_name == "getattr":
                attr = node.args[1] if len(node.args) > 1 else None
                if isinstance(attr, ast.Constant) and type(attr.value) is str:
                    assert not _forbidden_identifier(attr.value), (module, attr.value)
                assert module != "team_evidence_aggregation" or isinstance(attr, ast.Constant)
            else:
                assert call_name not in FORBIDDEN_CALLS or target in {"re.compile", "object.__setattr__"}, (module, target)
        if isinstance(node, ast.FormattedValue):
            assert node.conversion not in {ord("a"), ord("r")}, (module, node.lineno)
        if isinstance(node, ast.ExceptHandler):
            assert node.type is not None
            assert not any(
                _dotted(item).rsplit(".", 1)[-1] in {"Exception", "BaseException"}
                for item in ast.walk(node.type)
                if isinstance(item, ast.Name | ast.Attribute)
            )
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
        "max_evidence_age_seconds": Decimal("0.000000"),
        "max_capture_lag_seconds": Decimal("0.000000"),
        "independence_group_weight_cap": Decimal("1.000000"),
        "correlation_group_weight_cap": Decimal("1.000000"),
        "max_requirement_assignments_per_evidence": 32,
        "contradiction_no_probability_max": Decimal("0.250000"),
        "contradiction_yes_probability_min": Decimal("0.750000"),
        "contradiction_watch_score": Decimal("0.250000"),
        "contradiction_block_score": Decimal("0.750000"),
        "publish_probability_floor": Decimal("0.000000"),
        "publish_probability_ceiling": Decimal("1.000000"),
        "maximum_records": 128,
        "maximum_requirements": 32,
        "maximum_requirement_memberships": 1024,
        "maximum_witness_edges": 256,
        "requirements": (),
    }
    values.update(changes)
    return values


def test_node_2_unified_ast_import_export_forbidden_surface_and_line_size_gate() -> None:
    synthetic_identifiers = (
        "wallet = 1", "value.wallet", "def wallet(): pass", "async def wallet(): pass",
        "class Wallet: pass", "def f(wallet): pass", "f(wallet=1)",
        "try:\n    raise ValueError\nexcept ValueError as wallet:\n    pass",
        "def f():\n    global wallet",
        "def outer():\n    def inner():\n        nonlocal wallet",
        "from decimal import Wallet", "from decimal import Decimal as wallet",
        "import decimal as wallet",
    )
    for source in synthetic_identifiers:
        assert any(_forbidden_identifier(name) for name in _semantic_identifiers(ast.parse(source)))
    for source in ("from decimal import *", "from .decimal import Decimal", "from . import x"):
        node = next(item for item in ast.walk(ast.parse(source)) if isinstance(item, ast.ImportFrom))
        assert _invalid_from_import(node)
    assert not _invalid_from_import(ast.parse("from decimal import _private as _alias").body[0])
    assert not any(_forbidden_identifier(name) for name in (
        "TeamEvidenceWeightAllocation", "allocate_team_evidence_weights", "correlation_group_weight_cap",
    ))
    for source in ("match x:\n case {**wallet}:\n  pass", "match x:\n case OS(wallet=1):\n  pass"):
        assert any(_forbidden_identifier(name) for name in _semantic_identifiers(ast.parse(source)))

    for module, expected_exports in PUBLIC_EXPORTS.items():
        tree = _tree(module)
        _assert_clean_ast(module, tree)
        exports = _literal_exports(tree)
        assert exports == expected_exports
        definitions = {
            node.name: node for node in tree.body
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
        }
        assert set(exports) <= set(definitions)
        for export in exports:
            node = definitions[export]
            assert isinstance(node, ast.ClassDef if export[0].isupper() else ast.FunctionDef)
        assert all(literal not in _source(module).lower() for literal in OUTER_LITERALS)

    production_counts = {
        name: len((PACKAGE / name).read_text(encoding="utf-8").splitlines())
        for name in PRODUCTION_LINE_LIMITS
    }
    test_counts = {
        name: len((ROOT / "tests" / name).read_text(encoding="utf-8").splitlines())
        for name in TEST_LINE_LIMITS
    }
    assert all(production_counts[name] <= limit for name, limit in PRODUCTION_LINE_LIMITS.items())
    assert all(test_counts[name] <= limit for name, limit in TEST_LINE_LIMITS.items())
    assert sum(production_counts.values()) <= PRODUCTION_TOTAL_LINE_LIMIT
    assert sum(test_counts.values()) <= TEST_TOTAL_LINE_LIMIT


def test_node_2_public_dataclasses_are_frozen_slotted_final_and_hard_flagged() -> None:
    tree = _tree("team_evidence_aggregation_types")
    public_classes = PUBLIC_EXPORTS["team_evidence_aggregation_types"][:16]
    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
    assert set(public_classes) == {name for name in classes if name.startswith("TeamEvidence")}
    for name in public_classes:
        node = classes[name]
        assert len(node.bases) == 1 and _dotted(node.bases[0]) == "_ExactPublicDataclass"
        assert len(node.decorator_list) == 2 and _dotted(node.decorator_list[0]) == "final"
        decorator = node.decorator_list[1]
        assert isinstance(decorator, ast.Call) and _dotted(decorator.func) == "dataclass"
        assert not decorator.args
        assert {item.arg: ast.literal_eval(item.value) for item in decorator.keywords} == {
            "frozen": True, "slots": True,
        }
        declared = [
            item for item in node.body
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
        ]
        flag_fields = [item for item in declared if item.target.id in HARD_FLAGS]
        assert tuple(item.target.id for item in flag_fields) == HARD_FLAGS
        assert all(
            _dotted(item.annotation) == "bool"
            and isinstance(item.value, ast.Constant)
            and item.value.value is True
            for item in flag_fields
        )
    base = classes["_ExactPublicDataclass"]
    guard = next(item for item in base.body if isinstance(item, ast.FunctionDef) and item.name == "__init_subclass__")
    assert any(
        isinstance(item, ast.Raise)
        and isinstance(item.exc, ast.Call)
        and _dotted(item.exc.func) == "TypeError"
        for item in ast.walk(guard)
    )
    module = importlib.import_module("polymarket_alpha_lab.team_evidence_aggregation_types")
    for name in public_classes:
        with pytest.raises(TypeError):
            type(f"Illegal{name}", (getattr(module, name),), {})


def test_node_2_config_policy_fields_have_no_defaults_and_hard_maxima_fail_closed() -> None:
    tree = _tree("team_evidence_aggregation_types")
    config_node = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "TeamEvidenceAggregationConfig"
    )
    declared = [
        item for item in config_node.body
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
    ]
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
        ("max_requirement_assignments_per_evidence", 33),
        ("maximum_records", 129),
        ("maximum_requirements", 33),
        ("maximum_requirement_memberships", 1025),
        ("maximum_witness_edges", 257),
    ):
        with pytest.raises(ValueError):
            config_type(**_config_values(**{field_name: invalid_value}))


def test_node_2_package_root_has_no_node_2_public_exports() -> None:
    tree = ast.parse(
        (PACKAGE / "__init__.py").read_text(encoding="utf-8"),
        filename="__init__.py",
    )
    forbidden = set().union(*PUBLIC_EXPORTS.values())
    bindings = {
        node.id for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            bindings.update(alias.asname or alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            bindings.update(alias.asname or alias.name for alias in node.names)
    assert forbidden.isdisjoint(bindings)
    package_all = [
        node for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets)
    ]
    for assignment in package_all:
        assert isinstance(assignment.value, ast.Tuple | ast.List)
        assert all(isinstance(item, ast.Constant) and type(item.value) is str for item in assignment.value.elts)
        exports = tuple(item.value for item in assignment.value.elts)
        assert forbidden.isdisjoint(exports)


def test_node_2_has_no_outer_identity_packet_legacy_or_persistence_surface() -> None:
    for module in PUBLIC_EXPORTS:
        source = _source(module)
        tree = ast.parse(source, filename=f"{module}.py")
        assert all(literal not in source.lower() for literal in OUTER_LITERALS)
        strings = tuple(node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str))
        for value in (*_semantic_identifiers(tree), *strings):
            assert not _forbidden_identifier(value), (module, value)

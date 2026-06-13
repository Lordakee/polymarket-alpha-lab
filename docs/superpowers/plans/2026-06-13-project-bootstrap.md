# Project Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the initial Polymarket Alpha Lab repository with research documentation, domain vocabulary, tests, git initialization, and CodeGraph indexing.

**Architecture:** The bootstrap contains documentation first and only a thin Python domain model. It intentionally avoids network access, wallet logic, account authentication, and live trading.

**Tech Stack:** Markdown documentation, Python 3.11 dataclasses, pytest, git, CodeGraph.

---

### Task 1: Repository Skeleton

**Files:**
- Create: `README.md`
- Create: `AGENTS.md`
- Create: `.gitignore`
- Create: `pyproject.toml`

- [x] **Step 1: Initialize git repository**

Run:

```bash
git init /home/ubuntu/polymarket-alpha-lab
```

Expected: an empty git repository exists.

- [x] **Step 2: Add project metadata**

Create README, project instructions, ignore rules, and Python packaging metadata.

- [x] **Step 3: Verify repository state**

Run:

```bash
git -C /home/ubuntu/polymarket-alpha-lab status --short
```

Expected: new project files are listed as untracked.

### Task 2: Research Documentation

**Files:**
- Create: `docs/research/data-api-research.md`
- Create: `docs/research/strategy-research.md`
- Create: `docs/research/risk-system-research.md`
- Create: `docs/sources.md`

- [x] **Step 1: Save data/API research**

Record source priority, key fields, technical difficulties, and MVP data pipeline.

- [x] **Step 2: Save strategy research**

Record candidate edge types, strategy stability ranking, and validation rules.

- [x] **Step 3: Save risk research**

Record risk characteristics, sizing constraints, performance metrics, paper-trading journal fields, and initial parameter template.

- [x] **Step 4: Save sources**

Record official documentation, live sampled endpoints, and secondary references.

### Task 3: Design And Plan Documents

**Files:**
- Create: `docs/superpowers/specs/2026-06-13-polymarket-alpha-lab-design.md`
- Create: `docs/superpowers/plans/2026-06-13-project-bootstrap.md`

- [x] **Step 1: Save project design**

Write the current design: purpose, non-goals, architecture, data flow, source priority, scoring model, and validation rules.

- [x] **Step 2: Save bootstrap plan**

Write this plan so future implementation can continue from a documented checkpoint.

### Task 4: Thin Domain Model

**Files:**
- Create: `src/polymarket_alpha_lab/__init__.py`
- Create: `src/polymarket_alpha_lab/domain.py`
- Create: `tests/test_domain.py`

- [x] **Step 1: Define domain dataclasses**

Create dataclasses for outcome tokens, market snapshots, order book snapshots, order book levels, and market scores.

- [x] **Step 2: Add tests for basic derived values**

Test tradeability, spread, midpoint, and initial score weighting.

- [x] **Step 3: Run tests**

Run:

```bash
python -m pytest
```

Expected: all tests pass.

### Task 5: CodeGraph Initialization

**Files:**
- Create: `.codegraph/`

- [x] **Step 1: Initialize CodeGraph**

Run:

```bash
codegraph init /home/ubuntu/polymarket-alpha-lab
```

Expected: CodeGraph creates `.codegraph/` and indexes the repository.

- [x] **Step 2: Check CodeGraph status**

Run:

```bash
codegraph status /home/ubuntu/polymarket-alpha-lab
```

Expected: status reports an indexed project.

### Task 6: Commit Bootstrap

**Files:**
- Modify: all files above

- [ ] **Step 1: Inspect changes**

Run:

```bash
git -C /home/ubuntu/polymarket-alpha-lab status --short
```

Expected: project files and `.codegraph/` metadata are visible.

- [ ] **Step 2: Commit**

Run:

```bash
git -C /home/ubuntu/polymarket-alpha-lab add .
git -C /home/ubuntu/polymarket-alpha-lab commit -m "chore: bootstrap polymarket alpha lab"
```

Expected: initial commit is created.

# Bounded team research agents

## Delivered layer and architecture

This additive layer implements a real **model -> tool call -> observation ->
model** loop for the existing ten team IDs. It is a small custom Python runtime,
not LangGraph, CrewAI, AutoGen, a distributed worker service, or a renamed batch
of forecast-building functions. There is no new dependency or lockfile change.

The model chooses between three closed tools:

| Tool | Capability |
| --- | --- |
| `search_evidence(query)` | Search titles/text in the approved task snapshot; `*` lists up to ten source titles. |
| `read_evidence(source_id)` | Read an eligible source, its timestamp and reference. |
| `finish_research(...)` | Return canonical P(YES), confidence, a short rationale and source IDs. Must be called alone. |

Unlike the earlier supplied-input forecast builders, this loop delegates the
next research action and final probability to a model. Unlike an open web
agent, it searches **only the caller-approved evidence snapshot**. It does not
crawl the internet, read arbitrary URLs, execute code, open files, query a DB,
call other agents, or load model-selected plugins. Evidence references are
provenance labels, not automatically fetched URLs.

`run_team_research_batch` runs independent team research sessions with bounded
thread concurrency and stable input ordering. It validates/copies every task
before starting any worker/model factory. A new application-supplied model
client is requested per task; factories must return isolated clients. This is
parallel delegation and result collection, not inter-agent debate or recursive
handoffs. Threads are joined before return. Default concurrency is four,
configurable from one to 32; batch size is limited to 100.

## Files and interfaces

- `team_research_agent_types.py`: immutable task, evidence, tool response,
  limits and research-result contracts.
- `team_research_agent.py`: provider-neutral loop, fixed tools and batch API.
- `team_research_glm.py`: explicit opt-in GLM function-calling HTTP adapter.
- `scripts/run_team_research_demo.py`: fully synthetic offline demonstration.

Import directly from these modules. Existing package-root exports, legacy
builders, BTC advanced policy service, strategy cycle and CLI are unchanged.

## Offline demonstration

After the normal locked editable installation:

```bash
python scripts/run_team_research_demo.py --team crypto_eth --team macro_rates --max-workers 2
```

Omit `--team` to exercise all ten team IDs. The demo uses `ScriptedDemoModel`,
**not an LLM**. Its JSON explicitly reports `synthetic_demo=true` and
`live_model_called=false`. The demo cannot read credentials or enable live
model calls; it writes nothing and prints only synthetic results to stdout.
Its 0.5 probability is a fixture, not a fallback in the real runtime.

## Application integration

Construct a `TeamResearchTask` with a unique task ID, existing team ID,
condition ID, market slug, question, explicit resolution criteria, aware
`as_of` timestamp, and a tuple of `ResearchEvidence` records. Each record must
match the task's team and condition. Supply only public, redacted evidence
approved for transmission to the chosen model provider. This layer does NOT
automatically classify or redact confidential input; the application must do
so before construction. Stored evidence must be read through the already
approved local Supabase/Postgres paths, not a new file journal or hosted DB.

```python
from polymarket_alpha_lab.team_research_agent import run_team_research_agent
from polymarket_alpha_lab.team_research_agent_types import ResearchAgentLimits
from polymarket_alpha_lab.team_research_glm import GLMResearchModel

# task: an application-constructed TeamResearchTask containing approved data.
# model_api_token and model_name: explicitly supplied by the application;
# do not paste them into source, reports, console output or Git commits.
model = GLMResearchModel(
    api_token=model_api_token,
    model=model_name,
    allow_model_calls=True,
    timeout_seconds=20,
)
result = run_team_research_agent(
    task,
    model=model,
    limits=ResearchAgentLimits(max_model_calls=6, max_tool_calls=12),
)
```

The GLM adapter is disabled by default. Explicit enabling transmits public
question/rules/evidence to the **fixed** official GLM HTTPS chat-completions
endpoint and may incur provider charges. No model name is assumed; choose a
function-calling-capable model available to the caller. The v0 adapter uses
non-thinking function-calling mode and does not collect hidden reasoning.
Tokens are caller-supplied, excluded from repr, never read from disk or env,
and never put in a research result. The client is not a serializable report.

Requests use fresh tool schemas, `tool_choice=auto`, output-token limits,
network timeouts, a bounded response read, disabled redirects and disabled
proxy environment discovery. There are no automatic retries, streaming,
endpoint overrides, production secrets in CI, or provider fallback.

## Status, citations, and limits

`completed` means that the model returned a structurally valid **uncalibrated
research estimate** citing eligible sources actually read in this session.
It does not prove source authenticity, semantic support for every claim,
calibration, forecast quality, profitability, publication eligibility or
execution permission. Search hits alone do not count as read sources. Future,
stale, cross-team and cross-condition sources cannot support completion.
Freshness is measured against the explicit task timestamp, not wall-clock now.

`blocked` suppresses probability, confidence, summary and citations when
there is no eligible evidence, malformed/unapproved/repeated tool calls,
invalid citations, or exhausted model/tool/token/context limits. `failed`
also suppresses these fields after a model or factory error. No error is
converted into a neutral probability or a successful legacy forecast packet.
Errors return fixed reason codes; exceptions, prompts and raw model outputs
are not returned. The in-memory result includes task scope, counts and a
trace of tool names, never hidden model reasoning or raw tool arguments.

Defaults: six model calls, twelve tools (including finish), 12,000 cumulative
provider-reported tokens, 1,024 output tokens per call, 100,000 transcript
characters, and evidence no older than 86,400 seconds. Arguments and source
text also have size limits. All calls in one model response are validated
before any tool in that response runs. A final call cannot piggyback on a read.

Token accounting happens **after** a reply. The provider may already have billed
an over-budget request; this is not a hard monetary cap. Input-token estimation
and provider-side budget controls are not implemented. Per-task limits are
not shared fleet quotas. The concrete HTTP timeout bounds blocking network
operations, not the total run's wall clock; injected model clients must enforce
their own I/O timeouts. The runtime does not kill Python threads or promise
cancellation of a hung third-party client.

## Phase 1 and release evidence

All tasks/evidence/results preserve `paper_only=True`, `report_only=True`,
`readonly=True`. No live trading, wallet, account, exchange auth, order path,
strategy weights, position sizing, side selection or strategy-cycle wiring is
added. No project-data persistence is added. There is deliberately no automatic
conversion to `TeamForecastPacket`, no promotion of raw model outputs into BTC
publication envelopes, and no bypass of existing quality/cost/risk gates.

The owner's current instruction permits self-review, commit and merge without
external-review or CodeGraph gates. This is not an external PASS. Focused tests
use deterministic model replies and fake HTTP responses; they establish protocol,
isolation and failure behavior, not live-model forecasting quality. Run:

```bash
python -m pytest -q tests/test_team_research_agent.py tests/test_team_research_glm.py
python scripts/verify_local.py --full
```

Actual final revision, test totals and self-review findings are recorded in the
PR. Live provider and real Supabase integration are separate acceptance steps;
no successful live provider call is claimed for this delivery.

## Next integration boundary

Next work should feed this loop from approved source collectors/local evidence
readback, add calibration and review of its outputs, and only then consider
persistent research jobs or richer inter-team handoffs. Do not simply store a
`completed` model estimate as an approved forecast or wire it into execution.

## Primary protocol references

- GLM tools and tool response IDs: https://docs.bigmodel.cn/cn/guide/capabilities/function-calling
- GLM thinking parameter: https://docs.bigmodel.cn/cn/guide/capabilities/thinking
- Thread executor lifecycle: https://docs.python.org/3.12/library/concurrent.futures.html

create table if not exists public.candidate_decision_score_reports (
    report_sha256 text primary key
        check (report_sha256 ~ '^[a-f0-9]{64}$'),
    generated_at timestamptz not null,
    config_version text not null,
    candidate_id text not null,
    market_id text not null,
    normalized_market_question text not null,
    primary_team_id text not null,
    secondary_team_ids jsonb not null default '[]'::jsonb
        check (jsonb_typeof(secondary_team_ids) = 'array'),
    selected_side text not null
        check (selected_side in ('yes', 'no')),
    forecast_probability numeric(18, 6)
        check (forecast_probability is null or forecast_probability between 0 and 1),
    executable_price numeric(18, 6)
        check (executable_price is null or executable_price between 0 and 1),
    gross_edge numeric(18, 6)
        check (gross_edge is null or gross_edge between -1 and 1),
    estimated_cost_drag numeric(18, 6) not null
        check (estimated_cost_drag >= 0),
    net_edge numeric(18, 6)
        check (net_edge is null or net_edge between -1 and 1),
    cost_score numeric(18, 6) not null
        check (cost_score between 0 and 1),
    liquidity_score numeric(18, 6) not null
        check (liquidity_score between 0 and 1),
    evidence_score numeric(18, 6) not null
        check (evidence_score between 0 and 1),
    resolution_score numeric(18, 6) not null
        check (resolution_score between 0 and 1),
    team_memory_score numeric(18, 6) not null
        check (team_memory_score between 0 and 1),
    team_memory_policy text not null
        check (team_memory_policy in ('allow', 'throttle', 'block')),
    decision_score numeric(18, 6) not null
        check (decision_score between 0 and 1),
    action text not null
        check (action in ('reject', 'watch', 'research_more', 'paper_recommend')),
    hard_blocker_codes jsonb not null default '[]'::jsonb
        check (jsonb_typeof(hard_blocker_codes) = 'array'),
    reason_codes jsonb not null default '[]'::jsonb
        check (jsonb_typeof(reason_codes) = 'array'),
    source_report_refs jsonb not null default '[]'::jsonb
        check (jsonb_typeof(source_report_refs) = 'array'),
    derived_validation_digest text not null
        check (derived_validation_digest ~ '^[a-f0-9]{64}$'),
    boundary_statement text not null,
    payload jsonb not null
        check (jsonb_typeof(payload) = 'object'),
    paper_only boolean not null default true
        check (paper_only is true),
    report_only boolean not null default true
        check (report_only is true),
    readonly boolean not null default true
        check (readonly is true),
    inserted_at timestamptz not null default now(),
    check (
        payload::text !~*
        '"([^"]*[_ -])?(auth|wallet|account|order|trade|execute|submit|cancel|sign|private[_ -]?key|api[_ -]?key|secret|token|credential)([_ -][^"]*)?"[[:space:]]*:'
    ),
    check (((payload ->> 'generated_at')::timestamptz = generated_at) is true),
    check ((payload ->> 'config_version' = config_version) is true),
    check ((payload ->> 'candidate_id' = candidate_id) is true),
    check ((payload ->> 'market_id' = market_id) is true),
    check ((payload ->> 'normalized_market_question' = normalized_market_question) is true),
    check ((payload ->> 'primary_team_id' = primary_team_id) is true),
    check ((payload -> 'secondary_team_ids' = secondary_team_ids) is true),
    check ((payload ->> 'selected_side' = selected_side) is true),
    check ((payload ->> 'forecast_probability' is null and forecast_probability is null)
        or ((payload ->> 'forecast_probability')::numeric = forecast_probability)),
    check ((payload ->> 'executable_price' is null and executable_price is null)
        or ((payload ->> 'executable_price')::numeric = executable_price)),
    check ((payload ->> 'gross_edge' is null and gross_edge is null)
        or ((payload ->> 'gross_edge')::numeric = gross_edge)),
    check (((payload ->> 'estimated_cost_drag')::numeric = estimated_cost_drag) is true),
    check ((payload ->> 'net_edge' is null and net_edge is null)
        or ((payload ->> 'net_edge')::numeric = net_edge)),
    check (((payload ->> 'cost_score')::numeric = cost_score) is true),
    check (((payload ->> 'liquidity_score')::numeric = liquidity_score) is true),
    check (((payload ->> 'evidence_score')::numeric = evidence_score) is true),
    check (((payload ->> 'resolution_score')::numeric = resolution_score) is true),
    check (((payload ->> 'team_memory_score')::numeric = team_memory_score) is true),
    check ((payload ->> 'team_memory_policy' = team_memory_policy) is true),
    check (((payload ->> 'decision_score')::numeric = decision_score) is true),
    check ((payload ->> 'action' = action) is true),
    check ((payload -> 'hard_blocker_codes' = hard_blocker_codes) is true),
    check ((payload -> 'reason_codes' = reason_codes) is true),
    check ((payload -> 'source_report_refs' = source_report_refs) is true),
    check ((payload ->> 'derived_validation_digest' = derived_validation_digest) is true),
    check ((payload ->> 'boundary_statement' = boundary_statement) is true),
    check ((payload ->> 'paper_only' = 'true') is true),
    check ((payload ->> 'report_only' = 'true') is true),
    check ((payload ->> 'readonly' = 'true') is true)
);

create index if not exists idx_cdsr_generated_at
    on public.candidate_decision_score_reports (generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists idx_cdsr_action_generated_at
    on public.candidate_decision_score_reports (action, generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists idx_cdsr_primary_team_generated_at
    on public.candidate_decision_score_reports (primary_team_id, generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists idx_cdsr_config_version_generated_at
    on public.candidate_decision_score_reports (config_version, generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists idx_cdsr_candidate_market
    on public.candidate_decision_score_reports (candidate_id, market_id, generated_at desc);

create index if not exists idx_cdsr_reason_codes_gin
    on public.candidate_decision_score_reports using gin (reason_codes jsonb_path_ops);

create index if not exists idx_cdsr_source_report_refs_gin
    on public.candidate_decision_score_reports using gin (source_report_refs jsonb_path_ops);

comment on table public.candidate_decision_score_reports is
    'Local Supabase/Postgres paper-only, report-only, read-only candidate decision score reports.';

create table if not exists public.paper_autonomous_proposal_risk_gate_reports (
    report_sha256 text primary key,
    generated_at timestamptz not null,
    config_version text not null,
    gate_status text not null,
    recommended_next_step text not null,
    source_proposal_status text not null,
    source_proposal_count integer not null,
    source_proposal_total_notional numeric(38, 6) not null,
    blocked_reason_codes_json jsonb not null,
    watch_reason_codes_json jsonb not null,
    reason_codes_json jsonb not null,
    payload_json jsonb not null,
    paper_only boolean not null default true,
    report_only boolean not null default true,
    readonly boolean not null default true,
    inserted_at timestamptz not null default now(),
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
    check (config_version <> '' and config_version !~ '^[[:space:]]|[[:space:]]$'),
    check (gate_status in ('pass', 'watch', 'blocked')),
    check (source_proposal_status in ('candidate', 'blocked', 'watch', 'retired')),
    check (recommended_next_step = case gate_status when 'pass' then 'allow_paper_proposal_to_paper_broker' when 'watch' then 'hold_paper_proposal_for_risk_review' when 'blocked' then 'block_paper_proposal_pending_risk_repair' end),
    check (source_proposal_count >= 0),
    check (source_proposal_total_notional >= 0),
    check (jsonb_typeof(blocked_reason_codes_json) = 'array'),
    check (jsonb_typeof(watch_reason_codes_json) = 'array'),
    check (jsonb_typeof(reason_codes_json) = 'array'),
    check (jsonb_typeof(payload_json) = 'object'),
    check (not jsonb_path_exists(blocked_reason_codes_json, '$[*] ? (@.type() != "string")')),
    check (not jsonb_path_exists(watch_reason_codes_json, '$[*] ? (@.type() != "string")')),
    check (not jsonb_path_exists(reason_codes_json, '$[*] ? (@.type() != "string")')),
    check (gate_status <> 'blocked' or jsonb_array_length(blocked_reason_codes_json) > 0),
    check (gate_status <> 'pass' or jsonb_array_length(blocked_reason_codes_json) = 0),
    check (gate_status <> 'pass' or jsonb_array_length(watch_reason_codes_json) = 0),
    check (gate_status <> 'watch' or jsonb_array_length(blocked_reason_codes_json) = 0),
    check (paper_only is true),
    check (report_only is true),
    check (readonly is true),
    check (payload_json ? 'paper_only' and payload_json -> 'paper_only' = 'true'::jsonb),
    check (payload_json ? 'report_only' and payload_json -> 'report_only' = 'true'::jsonb),
    check (payload_json ? 'readonly' and payload_json -> 'readonly' = 'true'::jsonb),
    check (payload_json ? 'generated_at' and jsonb_typeof(payload_json -> 'generated_at') = 'string' and (payload_json ->> 'generated_at')::timestamptz = generated_at),
    check (payload_json ? 'config_version' and jsonb_typeof(payload_json -> 'config_version') = 'string' and payload_json ->> 'config_version' = config_version),
    check (payload_json ? 'gate_status' and jsonb_typeof(payload_json -> 'gate_status') = 'string' and payload_json ->> 'gate_status' = gate_status),
    check (payload_json ? 'recommended_next_step' and jsonb_typeof(payload_json -> 'recommended_next_step') = 'string' and payload_json ->> 'recommended_next_step' = recommended_next_step),
    check (payload_json ? 'source_proposal_status' and jsonb_typeof(payload_json -> 'source_proposal_status') = 'string' and payload_json ->> 'source_proposal_status' = source_proposal_status),
    check (payload_json ? 'source_proposal_count' and jsonb_typeof(payload_json -> 'source_proposal_count') = 'number' and (payload_json ->> 'source_proposal_count')::integer = source_proposal_count),
    check (payload_json ? 'source_proposal_total_notional' and jsonb_typeof(payload_json -> 'source_proposal_total_notional') = 'string' and (payload_json ->> 'source_proposal_total_notional')::numeric = source_proposal_total_notional),
    check (payload_json ->> 'source_proposal_total_notional' ~ '^(0|[1-9][0-9]*)[.][0-9]{6}$'),
    check (payload_json ? 'blocked_reason_codes' and jsonb_typeof(payload_json -> 'blocked_reason_codes') = 'array' and payload_json -> 'blocked_reason_codes' = blocked_reason_codes_json),
    check (payload_json ? 'watch_reason_codes' and jsonb_typeof(payload_json -> 'watch_reason_codes') = 'array' and payload_json -> 'watch_reason_codes' = watch_reason_codes_json),
    check (payload_json ? 'reason_codes' and jsonb_typeof(payload_json -> 'reason_codes') = 'array' and payload_json -> 'reason_codes' = reason_codes_json)
);

create index if not exists idx_paprg_generated_at
    on public.paper_autonomous_proposal_risk_gate_reports
    (generated_at desc);

create index if not exists idx_paprg_gate_status_generated
    on public.paper_autonomous_proposal_risk_gate_reports
    (gate_status, generated_at desc);

create index if not exists idx_paprg_source_status_generated
    on public.paper_autonomous_proposal_risk_gate_reports
    (source_proposal_status, generated_at desc);

create index if not exists idx_paprg_config_generated
    on public.paper_autonomous_proposal_risk_gate_reports
    (config_version, generated_at desc);

create index if not exists idx_paprg_reason_codes_json
    on public.paper_autonomous_proposal_risk_gate_reports using gin
    (reason_codes_json);

create index if not exists idx_paprg_payload_json
    on public.paper_autonomous_proposal_risk_gate_reports using gin
    (payload_json);

create index if not exists idx_paprg_load_sort
    on public.paper_autonomous_proposal_risk_gate_reports
    (generated_at desc, inserted_at desc, report_sha256 desc);

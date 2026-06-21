create table if not exists public.strategy_risk_audit_reports (
    report_sha256 text primary key,
    generated_at timestamptz not null,
    config_version text not null,
    status text not null,
    gate_count integer not null,
    pass_count integer not null,
    fail_count integer not null,
    incomplete_count integer not null,
    gate_results_json jsonb not null,
    payload_json jsonb not null,
    paper_only boolean not null default true,
    report_only boolean not null default true,
    readonly boolean not null default true,
    inserted_at timestamptz not null default now(),
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
    check (status in ('audit_ready', 'blocked_by_risk', 'insufficient_evidence')),
    check (gate_count >= 0),
    check (pass_count >= 0),
    check (fail_count >= 0),
    check (incomplete_count >= 0),
    check (gate_count = pass_count + fail_count + incomplete_count),
    check ((fail_count > 0
            and status = 'blocked_by_risk')
        or (fail_count = 0
            and incomplete_count > 0
            and status = 'insufficient_evidence')
        or (fail_count = 0
            and incomplete_count = 0
            and status = 'audit_ready')),
    check (jsonb_typeof(gate_results_json) = 'array'),
    check (jsonb_array_length(gate_results_json) = gate_count),
    check (jsonb_typeof(payload_json) = 'object'),
    check (payload_json ? 'generated_at'
        and jsonb_typeof(payload_json -> 'generated_at') = 'string'
        and (payload_json ->> 'generated_at')::timestamptz = generated_at),
    check (payload_json ? 'config_version'
        and jsonb_typeof(payload_json -> 'config_version') = 'string'
        and payload_json ->> 'config_version' = config_version),
    check (payload_json ? 'status'
        and jsonb_typeof(payload_json -> 'status') = 'string'
        and payload_json ->> 'status' = status),
    check (payload_json ? 'gate_count'
        and jsonb_typeof(payload_json -> 'gate_count') = 'number'
        and (payload_json ->> 'gate_count')::integer = gate_count),
    check (payload_json ? 'pass_count'
        and jsonb_typeof(payload_json -> 'pass_count') = 'number'
        and (payload_json ->> 'pass_count')::integer = pass_count),
    check (payload_json ? 'fail_count'
        and jsonb_typeof(payload_json -> 'fail_count') = 'number'
        and (payload_json ->> 'fail_count')::integer = fail_count),
    check (payload_json ? 'incomplete_count'
        and jsonb_typeof(payload_json -> 'incomplete_count') = 'number'
        and (payload_json ->> 'incomplete_count')::integer = incomplete_count),
    check (payload_json ? 'gate_results'
        and jsonb_typeof(payload_json -> 'gate_results') = 'array'
        and payload_json -> 'gate_results' = gate_results_json),
    check (payload_json ? 'paper_only'
        and payload_json -> 'paper_only' = 'true'::jsonb),
    check (payload_json ? 'report_only'
        and payload_json -> 'report_only' = 'true'::jsonb),
    check (paper_only is true),
    check (report_only is true),
    check (readonly is true)
);

create index if not exists idx_srar_generated_at
    on public.strategy_risk_audit_reports (generated_at desc);

create index if not exists idx_srar_status_generated
    on public.strategy_risk_audit_reports (status, generated_at desc);

create index if not exists idx_srar_config_generated
    on public.strategy_risk_audit_reports (config_version, generated_at desc);

create index if not exists idx_srar_payload_json
    on public.strategy_risk_audit_reports using gin (payload_json);

create index if not exists idx_srar_gate_results_json
    on public.strategy_risk_audit_reports using gin (gate_results_json);

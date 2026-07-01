create table if not exists public.paper_autonomous_screening_gate_transition_trend_reports (
    report_sha256 text primary key,
    generated_at timestamptz not null,
    config_version text not null,
    transition_report_count integer not null,
    first_transition_generated_at timestamptz,
    latest_transition_generated_at timestamptz,
    latest_from_gate_status text,
    latest_to_gate_status text,
    latest_introduced_reason_code_count integer not null,
    latest_cleared_reason_code_count integer not null,
    latest_persistent_reason_code_count integer not null,
    latest_transition_count integer not null,
    latest_instability_ratio numeric(18, 6),
    payload_json jsonb not null,
    paper_only boolean not null default true,
    report_only boolean not null default true,
    readonly boolean not null default true,
    inserted_at timestamptz not null default now(),
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
    check (latest_from_gate_status is null or latest_from_gate_status in ('pass', 'watch', 'blocked')),
    check (latest_to_gate_status is null or latest_to_gate_status in ('pass', 'watch', 'blocked')),
    check (transition_report_count >= 0),
    check (latest_introduced_reason_code_count >= 0),
    check (latest_cleared_reason_code_count >= 0),
    check (latest_persistent_reason_code_count >= 0),
    check (latest_transition_count >= 0),
    check (latest_instability_ratio is null or (latest_instability_ratio >= 0 and latest_instability_ratio <= 1)),
    check (
        (transition_report_count = 0 and first_transition_generated_at is null and latest_transition_generated_at is null)
        or (transition_report_count > 0 and first_transition_generated_at is not null and latest_transition_generated_at is not null)
    ),
    check (
        (latest_transition_count = 0 and latest_from_gate_status is null and latest_to_gate_status is null)
        or (latest_transition_count > 0 and latest_from_gate_status is not null and latest_to_gate_status is not null)
    ),
    check (payload_json is not null and jsonb_typeof(payload_json) = 'object'),
    check (payload_json ? 'generated_at' and jsonb_typeof(payload_json -> 'generated_at') = 'string' and (payload_json ->> 'generated_at')::timestamptz = generated_at),
    check (payload_json ? 'config_version' and jsonb_typeof(payload_json -> 'config_version') = 'string' and payload_json ->> 'config_version' = config_version),
    check (((payload_json -> 'transition_report_count') = to_jsonb(transition_report_count)) is true),
    check (payload_json ? 'first_transition_generated_at' and ((first_transition_generated_at is null and payload_json -> 'first_transition_generated_at' = 'null'::jsonb) or (first_transition_generated_at is not null and jsonb_typeof(payload_json -> 'first_transition_generated_at') = 'string' and (payload_json ->> 'first_transition_generated_at')::timestamptz = first_transition_generated_at))),
    check (payload_json ? 'latest_transition_generated_at' and ((latest_transition_generated_at is null and payload_json -> 'latest_transition_generated_at' = 'null'::jsonb) or (latest_transition_generated_at is not null and jsonb_typeof(payload_json -> 'latest_transition_generated_at') = 'string' and (payload_json ->> 'latest_transition_generated_at')::timestamptz = latest_transition_generated_at))),
    check (payload_json ? 'latest_from_gate_status' and ((latest_from_gate_status is null and payload_json -> 'latest_from_gate_status' = 'null'::jsonb) or (latest_from_gate_status is not null and jsonb_typeof(payload_json -> 'latest_from_gate_status') = 'string' and payload_json ->> 'latest_from_gate_status' = latest_from_gate_status))),
    check (payload_json ? 'latest_to_gate_status' and ((latest_to_gate_status is null and payload_json -> 'latest_to_gate_status' = 'null'::jsonb) or (latest_to_gate_status is not null and jsonb_typeof(payload_json -> 'latest_to_gate_status') = 'string' and payload_json ->> 'latest_to_gate_status' = latest_to_gate_status))),
    check (((payload_json -> 'latest_introduced_reason_code_count') = to_jsonb(latest_introduced_reason_code_count)) is true),
    check (((payload_json -> 'latest_cleared_reason_code_count') = to_jsonb(latest_cleared_reason_code_count)) is true),
    check (((payload_json -> 'latest_persistent_reason_code_count') = to_jsonb(latest_persistent_reason_code_count)) is true),
    check (((payload_json -> 'latest_transition_count') = to_jsonb(latest_transition_count)) is true),
    check (payload_json ? 'latest_instability_ratio' and ((latest_instability_ratio is null and payload_json -> 'latest_instability_ratio' = 'null'::jsonb) or (latest_instability_ratio is not null and jsonb_typeof(payload_json -> 'latest_instability_ratio') = 'string' and (payload_json ->> 'latest_instability_ratio')::numeric(18, 6) = latest_instability_ratio))),
    check (payload_json ->> 'latest_instability_ratio' is null or payload_json ->> 'latest_instability_ratio' ~ '^(0|1)[.][0-9]{6}$'),
    check (payload_json ? 'paper_only' and payload_json -> 'paper_only' = 'true'::jsonb),
    check (payload_json ? 'report_only' and payload_json -> 'report_only' = 'true'::jsonb),
    check (payload_json ? 'readonly' and payload_json -> 'readonly' = 'true'::jsonb),
    check (paper_only is true),
    check (report_only is true),
    check (readonly is true)
);

create index if not exists pasgttr_generated_at_idx
    on public.paper_autonomous_screening_gate_transition_trend_reports
    (generated_at desc);

create index if not exists pasgttr_config_generated_at_idx
    on public.paper_autonomous_screening_gate_transition_trend_reports
    (config_version, generated_at desc);

create index if not exists pasgttr_latest_from_idx
    on public.paper_autonomous_screening_gate_transition_trend_reports
    (latest_from_gate_status, generated_at desc);

create index if not exists pasgttr_latest_to_idx
    on public.paper_autonomous_screening_gate_transition_trend_reports
    (latest_to_gate_status, generated_at desc);

create index if not exists pasgttr_payload_json_idx
    on public.paper_autonomous_screening_gate_transition_trend_reports
    using gin (payload_json jsonb_path_ops);

create index if not exists pasgttr_load_sort_idx
    on public.paper_autonomous_screening_gate_transition_trend_reports
    (generated_at desc, inserted_at desc, report_sha256 desc);

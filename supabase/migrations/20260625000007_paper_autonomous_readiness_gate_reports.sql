create table if not exists public.paper_autonomous_readiness_gate_reports (
    report_sha256 text primary key,
    generated_at timestamptz not null,
    config_version text not null,
    readiness_status text not null,
    recommended_next_step text not null,
    source_statuses_json jsonb not null,
    source_config_versions_json jsonb not null,
    reason_code_counts_json jsonb not null,
    reason_codes_json jsonb not null,
    payload_json jsonb not null,
    paper_only boolean not null default true,
    report_only boolean not null default true,
    readonly boolean not null default true,
    inserted_at timestamptz not null default now(),
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
    check (readiness_status in ('pass', 'watch', 'blocked')),
    check (
        recommended_next_step = case readiness_status
            when 'pass' then 'allow_paper_autonomous_readiness_review'
            when 'watch' then 'throttle_paper_autonomous_readiness_review'
            when 'blocked' then 'block_paper_autonomous_readiness_review'
        end
    ),
    check (jsonb_typeof(source_statuses_json) = 'array'),
    check (jsonb_typeof(source_config_versions_json) = 'array'),
    check (jsonb_typeof(reason_code_counts_json) = 'array'),
    check (jsonb_typeof(reason_codes_json) = 'array'),
    check (jsonb_typeof(payload_json) = 'object'),
    check (jsonb_array_length(source_statuses_json) = 3),
    check (jsonb_array_length(source_config_versions_json) = 3),
    check (paper_only is true),
    check (report_only is true),
    check (readonly is true),
    check (payload_json ? 'paper_only' and payload_json -> 'paper_only' = 'true'::jsonb),
    check (payload_json ? 'report_only' and payload_json -> 'report_only' = 'true'::jsonb),
    check (payload_json ? 'readonly' and payload_json -> 'readonly' = 'true'::jsonb),
    check (payload_json ? 'generated_at' and jsonb_typeof(payload_json -> 'generated_at') = 'string' and (payload_json ->> 'generated_at')::timestamptz = generated_at),
    check (payload_json ? 'config_version' and jsonb_typeof(payload_json -> 'config_version') = 'string' and payload_json ->> 'config_version' = config_version),
    check (payload_json ? 'readiness_status' and jsonb_typeof(payload_json -> 'readiness_status') = 'string' and payload_json ->> 'readiness_status' = readiness_status),
    check (payload_json ? 'recommended_next_step' and jsonb_typeof(payload_json -> 'recommended_next_step') = 'string' and payload_json ->> 'recommended_next_step' = recommended_next_step),
    check (payload_json ? 'source_statuses' and jsonb_typeof(payload_json -> 'source_statuses') = 'array' and source_statuses_json = payload_json -> 'source_statuses'),
    check (payload_json ? 'source_config_versions' and jsonb_typeof(payload_json -> 'source_config_versions') = 'array' and source_config_versions_json = payload_json -> 'source_config_versions'),
    check (payload_json ? 'reason_code_counts' and jsonb_typeof(payload_json -> 'reason_code_counts') = 'array' and reason_code_counts_json = payload_json -> 'reason_code_counts'),
    check (payload_json ? 'reason_codes' and jsonb_typeof(payload_json -> 'reason_codes') = 'array' and reason_codes_json = payload_json -> 'reason_codes')
);

create index if not exists paper_autonomous_readiness_gate_generated_at_idx
    on public.paper_autonomous_readiness_gate_reports
    (generated_at desc);

create index if not exists paper_autonomous_readiness_gate_status_generated_at_idx
    on public.paper_autonomous_readiness_gate_reports
    (readiness_status, generated_at desc);

create index if not exists paper_autonomous_readiness_gate_config_generated_at_idx
    on public.paper_autonomous_readiness_gate_reports
    (config_version, generated_at desc);

create index if not exists paper_autonomous_readiness_gate_source_statuses_idx
    on public.paper_autonomous_readiness_gate_reports using gin
    (source_statuses_json jsonb_path_ops);

create index if not exists pargr_source_status_sort_idx
    on public.paper_autonomous_readiness_gate_reports
    (
        (source_statuses_json #>> '{0,status}'),
        (source_statuses_json #>> '{1,status}'),
        (source_statuses_json #>> '{2,status}'),
        generated_at desc,
        inserted_at desc,
        report_sha256 desc
    );

create index if not exists paper_autonomous_readiness_gate_status_sort_idx
    on public.paper_autonomous_readiness_gate_reports
    (readiness_status, generated_at desc, inserted_at desc, report_sha256 desc);

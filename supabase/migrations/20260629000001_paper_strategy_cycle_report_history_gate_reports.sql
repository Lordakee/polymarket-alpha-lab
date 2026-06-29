create table if not exists public.paper_strategy_cycle_report_history_gate_reports (
    report_sha256 text primary key,
    generated_at timestamptz not null,
    config_version text not null,
    source_config_version text not null,
    source_generated_at timestamptz not null,
    gate_status text not null,
    recommended_next_step text not null,
    source_history_status text not null,
    source_report_count integer not null,
    latest_source_generated_at timestamptz null,
    latest_source_age_seconds integer null,
    latest_snapshot_ready_share numeric(18, 6) not null,
    blocked_market_share numeric(18, 6) not null,
    latest_snapshot_ready_count integer not null,
    latest_considered_count integer not null,
    total_blocked_market_count integer not null,
    reason_code_counts_json jsonb not null,
    reason_codes_json jsonb not null,
    payload_json jsonb not null,
    paper_only boolean not null default true,
    report_only boolean not null default true,
    readonly boolean not null default true,
    inserted_at timestamptz not null default now(),
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
    check (gate_status in ('pass', 'watch', 'blocked')),
    check (source_history_status in ('pass', 'watch', 'blocked')),
    check (
        recommended_next_step = case gate_status
            when 'pass' then 'allow_strategy_cycle_history_gate'
            when 'watch' then 'throttle_strategy_cycle_history_gate'
            when 'blocked' then 'block_strategy_cycle_history_gate'
        end
    ),
    check (source_report_count > 0),
    check (latest_source_age_seconds is null or latest_source_age_seconds >= 0),
    check (latest_snapshot_ready_share >= 0 and latest_snapshot_ready_share <= 1),
    check (blocked_market_share >= 0 and blocked_market_share <= 1),
    check (latest_snapshot_ready_count >= 0),
    check (latest_considered_count >= 0),
    check (total_blocked_market_count >= 0),
    check (latest_snapshot_ready_count <= latest_considered_count),
    check (jsonb_typeof(reason_code_counts_json) = 'array'),
    check (jsonb_typeof(reason_codes_json) = 'array'),
    check (jsonb_typeof(payload_json) = 'object'),
    check (paper_only is true),
    check (report_only is true),
    check (readonly is true),
    check (payload_json ? 'generated_at' and jsonb_typeof(payload_json -> 'generated_at') = 'string' and (payload_json ->> 'generated_at')::timestamptz = generated_at),
    check (payload_json ? 'config_version' and jsonb_typeof(payload_json -> 'config_version') = 'string' and payload_json ->> 'config_version' = config_version),
    check (payload_json ? 'source_config_version' and jsonb_typeof(payload_json -> 'source_config_version') = 'string' and payload_json ->> 'source_config_version' = source_config_version),
    check (payload_json ? 'source_generated_at' and jsonb_typeof(payload_json -> 'source_generated_at') = 'string' and (payload_json ->> 'source_generated_at')::timestamptz = source_generated_at),
    check (payload_json ? 'gate_status' and jsonb_typeof(payload_json -> 'gate_status') = 'string' and payload_json ->> 'gate_status' = gate_status),
    check (payload_json ? 'recommended_next_step' and jsonb_typeof(payload_json -> 'recommended_next_step') = 'string' and payload_json ->> 'recommended_next_step' = recommended_next_step),
    check (payload_json ? 'source_history_status' and jsonb_typeof(payload_json -> 'source_history_status') = 'string' and payload_json ->> 'source_history_status' = source_history_status),
    check (payload_json ? 'source_report_count' and (payload_json ->> 'source_report_count')::integer = source_report_count),
    check (payload_json ? 'latest_source_age_seconds' and ((latest_source_age_seconds is null and payload_json -> 'latest_source_age_seconds' = 'null'::jsonb) or (latest_source_age_seconds is not null and (payload_json ->> 'latest_source_age_seconds')::integer = latest_source_age_seconds))),
    check (payload_json ? 'latest_source_generated_at' and ((latest_source_generated_at is null and payload_json -> 'latest_source_generated_at' = 'null'::jsonb) or (latest_source_generated_at is not null and jsonb_typeof(payload_json -> 'latest_source_generated_at') = 'string' and (payload_json ->> 'latest_source_generated_at')::timestamptz = latest_source_generated_at))),
    check (payload_json ? 'latest_snapshot_ready_share' and jsonb_typeof(payload_json -> 'latest_snapshot_ready_share') = 'string' and (payload_json ->> 'latest_snapshot_ready_share')::numeric(18, 6) = latest_snapshot_ready_share),
    check (payload_json ? 'blocked_market_share' and jsonb_typeof(payload_json -> 'blocked_market_share') = 'string' and (payload_json ->> 'blocked_market_share')::numeric(18, 6) = blocked_market_share),
    check (payload_json ? 'latest_snapshot_ready_count' and (payload_json ->> 'latest_snapshot_ready_count')::integer = latest_snapshot_ready_count),
    check (payload_json ? 'latest_considered_count' and (payload_json ->> 'latest_considered_count')::integer = latest_considered_count),
    check (payload_json ? 'total_blocked_market_count' and (payload_json ->> 'total_blocked_market_count')::integer = total_blocked_market_count),
    check (payload_json ? 'reason_code_counts' and jsonb_typeof(payload_json -> 'reason_code_counts') = 'array' and reason_code_counts_json = payload_json -> 'reason_code_counts'),
    check (payload_json ? 'reason_codes' and jsonb_typeof(payload_json -> 'reason_codes') = 'array' and reason_codes_json = payload_json -> 'reason_codes'),
    check (payload_json ? 'paper_only' and payload_json -> 'paper_only' = 'true'::jsonb),
    check (payload_json ? 'report_only' and payload_json -> 'report_only' = 'true'::jsonb),
    check (payload_json ? 'readonly' and payload_json -> 'readonly' = 'true'::jsonb)
);

create index if not exists pschgr_generated_at_idx
    on public.paper_strategy_cycle_report_history_gate_reports
    (generated_at desc);

create index if not exists pschgr_gate_status_generated_at_idx
    on public.paper_strategy_cycle_report_history_gate_reports
    (gate_status, generated_at desc);

create index if not exists pschgr_config_version_generated_at_idx
    on public.paper_strategy_cycle_report_history_gate_reports
    (config_version, generated_at desc);

create index if not exists pschgr_source_config_generated_at_idx
    on public.paper_strategy_cycle_report_history_gate_reports
    (source_config_version, source_generated_at desc);

create index if not exists pschgr_reason_codes_json_idx
    on public.paper_strategy_cycle_report_history_gate_reports using gin
    (reason_codes_json jsonb_path_ops);

create index if not exists pschgr_payload_json_idx
    on public.paper_strategy_cycle_report_history_gate_reports using gin
    (payload_json jsonb_path_ops);

create index if not exists pschgr_load_sort_idx
    on public.paper_strategy_cycle_report_history_gate_reports
    (generated_at desc, inserted_at desc, report_sha256 desc);

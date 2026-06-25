create table if not exists public.paper_autonomous_screening_gate_transition_reports (
    report_sha256 text primary key,
    generated_at timestamptz not null,
    config_version text not null,
    gate_report_count integer not null,
    transition_count integer not null,
    first_report_generated_at timestamptz,
    latest_report_generated_at timestamptz,
    latest_from_gate_status text,
    latest_to_gate_status text,
    latest_introduced_reason_codes_json jsonb not null default '[]'::jsonb,
    latest_cleared_reason_codes_json jsonb not null default '[]'::jsonb,
    latest_persistent_reason_codes_json jsonb not null default '[]'::jsonb,
    status_transition_rows_json jsonb,
    reason_change_rows_json jsonb,
    payload_json jsonb not null,
    paper_only boolean not null default true,
    report_only boolean not null default true,
    readonly boolean not null default true,
    inserted_at timestamptz not null default now(),
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
    check (latest_from_gate_status is null or latest_from_gate_status in ('pass', 'watch', 'blocked')),
    check (latest_to_gate_status is null or latest_to_gate_status in ('pass', 'watch', 'blocked')),
    check (gate_report_count >= 0),
    check (transition_count >= 0),
    check (transition_count = greatest(gate_report_count - 1, 0)),
    check (
        (gate_report_count = 0 and first_report_generated_at is null and latest_report_generated_at is null)
        or (gate_report_count > 0 and first_report_generated_at is not null and latest_report_generated_at is not null)
    ),
    check (
        (transition_count = 0 and latest_from_gate_status is null and latest_to_gate_status is null)
        or (transition_count > 0 and latest_from_gate_status is not null and latest_to_gate_status is not null)
    ),
    check (jsonb_typeof(latest_introduced_reason_codes_json) = 'array'),
    check (jsonb_typeof(latest_cleared_reason_codes_json) = 'array'),
    check (jsonb_typeof(latest_persistent_reason_codes_json) = 'array'),
    check (status_transition_rows_json is null or jsonb_typeof(status_transition_rows_json) = 'array'),
    check (reason_change_rows_json is null or jsonb_typeof(reason_change_rows_json) = 'array'),
    check (payload_json is not null and jsonb_typeof(payload_json) = 'object'),
    check (payload_json ? 'generated_at' and jsonb_typeof(payload_json -> 'generated_at') = 'string' and (payload_json ->> 'generated_at')::timestamptz = generated_at),
    check (payload_json ? 'config_version' and jsonb_typeof(payload_json -> 'config_version') = 'string' and payload_json ->> 'config_version' = config_version),
    check (((payload_json -> 'gate_report_count') = to_jsonb(gate_report_count)) is true),
    check (((payload_json -> 'transition_count') = to_jsonb(transition_count)) is true),
    check (
        (first_report_generated_at is null and payload_json -> 'first_report_generated_at' = 'null'::jsonb)
        or (
            first_report_generated_at is not null
            and payload_json ? 'first_report_generated_at'
            and jsonb_typeof(payload_json -> 'first_report_generated_at') = 'string'
            and (payload_json ->> 'first_report_generated_at')::timestamptz = first_report_generated_at
        )
    ),
    check (
        (latest_report_generated_at is null and payload_json -> 'latest_report_generated_at' = 'null'::jsonb)
        or (
            latest_report_generated_at is not null
            and payload_json ? 'latest_report_generated_at'
            and jsonb_typeof(payload_json -> 'latest_report_generated_at') = 'string'
            and (payload_json ->> 'latest_report_generated_at')::timestamptz = latest_report_generated_at
        )
    ),
    check (
        (latest_from_gate_status is null and payload_json -> 'latest_from_gate_status' = 'null'::jsonb)
        or (
            latest_from_gate_status is not null
            and payload_json ? 'latest_from_gate_status'
            and jsonb_typeof(payload_json -> 'latest_from_gate_status') = 'string'
            and payload_json ->> 'latest_from_gate_status' = latest_from_gate_status
        )
    ),
    check (
        (latest_to_gate_status is null and payload_json -> 'latest_to_gate_status' = 'null'::jsonb)
        or (
            latest_to_gate_status is not null
            and payload_json ? 'latest_to_gate_status'
            and jsonb_typeof(payload_json -> 'latest_to_gate_status') = 'string'
            and payload_json ->> 'latest_to_gate_status' = latest_to_gate_status
        )
    ),
    check (latest_introduced_reason_codes_json = payload_json -> 'latest_introduced_reason_codes'),
    check (latest_cleared_reason_codes_json = payload_json -> 'latest_cleared_reason_codes'),
    check (latest_persistent_reason_codes_json = payload_json -> 'latest_persistent_reason_codes'),
    check ((status_transition_rows_json is null and payload_json -> 'status_transition_rows' = 'null'::jsonb) or (status_transition_rows_json is not null and status_transition_rows_json = payload_json -> 'status_transition_rows')),
    check ((reason_change_rows_json is null and payload_json -> 'reason_change_rows' = 'null'::jsonb) or (reason_change_rows_json is not null and reason_change_rows_json = payload_json -> 'reason_change_rows')),
    check (payload_json ? 'paper_only' and payload_json -> 'paper_only' = 'true'::jsonb),
    check (payload_json ? 'report_only' and payload_json -> 'report_only' = 'true'::jsonb),
    check (payload_json ? 'readonly' and payload_json -> 'readonly' = 'true'::jsonb),
    check (paper_only is true),
    check (report_only is true),
    check (readonly is true)
);

create index if not exists pasgtr_generated_at_idx
    on public.paper_autonomous_screening_gate_transition_reports
    (generated_at desc);

create index if not exists pasgtr_config_generated_at_idx
    on public.paper_autonomous_screening_gate_transition_reports
    (config_version, generated_at desc);

create index if not exists pasgtr_latest_from_idx
    on public.paper_autonomous_screening_gate_transition_reports
    (latest_from_gate_status, generated_at desc);

create index if not exists pasgtr_latest_to_idx
    on public.paper_autonomous_screening_gate_transition_reports
    (latest_to_gate_status, generated_at desc);

create index if not exists pasgtr_status_sort_idx
    on public.paper_autonomous_screening_gate_transition_reports
    (latest_from_gate_status, latest_to_gate_status, generated_at desc, inserted_at desc, report_sha256 desc);

create table if not exists public.paper_order_lifecycle_records (
    report_sha256 text primary key,
    generated_at timestamptz not null,
    config_version text not null,
    lifecycle_status text not null,
    recommended_next_step text not null,
    source_execution_status text not null,
    source_execution_notional numeric not null,
    fill_notional numeric not null,
    is_terminal boolean not null,
    reason_codes_json jsonb not null,
    payload_json jsonb not null,
    paper_only boolean not null default true,
    report_only boolean not null default true,
    readonly boolean not null default true,
    inserted_at timestamptz not null default now(),
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
    check (lifecycle_status in (
        'proposed', 'risk_passed', 'risk_blocked',
        'paper_submitted', 'paper_filled', 'paper_cancelled',
        'paper_expired', 'human_approval_pending', 'rejected'
    )),
    check (source_execution_status in ('paper_submitted', 'paper_blocked', 'paper_held')),
    check (source_execution_notional >= 0),
    check (fill_notional >= 0),
    check (jsonb_typeof(reason_codes_json) = 'array'),
    check (jsonb_typeof(payload_json) = 'object'),
    check (paper_only is true),
    check (report_only is true),
    check (readonly is true)
);

create index if not exists paper_order_lifecycle_generated_at_idx
    on public.paper_order_lifecycle_records (generated_at desc);

create index if not exists paper_order_lifecycle_status_generated_at_idx
    on public.paper_order_lifecycle_records (lifecycle_status, generated_at desc);

create index if not exists paper_order_lifecycle_status_order_idx
    on public.paper_order_lifecycle_records (lifecycle_status, generated_at desc, inserted_at desc, report_sha256 desc);

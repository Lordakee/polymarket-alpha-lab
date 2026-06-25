create table if not exists public.paper_broker_execution_records (
    record_sha256 text primary key,
    generated_at timestamptz not null,
    config_version text not null,
    execution_status text not null,
    recommended_next_step text not null,
    source_gate_status text not null,
    source_proposal_count integer not null,
    source_proposal_total_notional numeric not null,
    execution_notional numeric not null,
    reason_codes jsonb not null,
    payload jsonb not null,
    paper_only boolean not null default true,
    report_only boolean not null default true,
    readonly boolean not null default true,
    inserted_at timestamptz not null default now(),
    check (record_sha256 ~ '^[a-f0-9]{64}$'),
    check (execution_status in (
        'paper_submitted', 'paper_blocked', 'paper_held'
    )),
    check (recommended_next_step in (
        'route_to_paper_order_lifecycle',
        'block_paper_execution_pending_repair',
        'hold_for_broker_review'
    )),
    check (source_gate_status in ('pass', 'watch', 'blocked')),
    check (source_proposal_count >= 0),
    check (source_proposal_total_notional >= 0),
    check (execution_notional >= 0),
    check (jsonb_typeof(reason_codes) = 'array'),
    check (jsonb_typeof(payload) = 'object'),
    check (paper_only is true),
    check (report_only is true),
    check (readonly is true),
    check ((payload ->> 'paper_only')::boolean is true),
    check ((payload ->> 'report_only')::boolean is true),
    check ((payload ->> 'readonly')::boolean is true),
    check (
        (
            execution_status = 'paper_submitted'
            and recommended_next_step = 'route_to_paper_order_lifecycle'
            and execution_notional > 0
        )
        or (
            execution_status = 'paper_held'
            and recommended_next_step = 'hold_for_broker_review'
            and execution_notional = 0
        )
        or (
            execution_status = 'paper_blocked'
            and recommended_next_step = 'block_paper_execution_pending_repair'
            and execution_notional = 0
        )
    )
);

create index if not exists paper_broker_execution_records_generated_order_idx
    on public.paper_broker_execution_records (generated_at desc, inserted_at desc, record_sha256 desc);

create index if not exists paper_broker_execution_records_config_order_idx
    on public.paper_broker_execution_records (config_version, generated_at desc, inserted_at desc, record_sha256 desc);

create index if not exists paper_broker_execution_records_status_order_idx
    on public.paper_broker_execution_records (execution_status, generated_at desc, inserted_at desc, record_sha256 desc);

create index if not exists paper_broker_execution_records_gate_order_idx
    on public.paper_broker_execution_records (source_gate_status, generated_at desc, inserted_at desc, record_sha256 desc);

create index if not exists paper_broker_execution_records_reason_codes_idx
    on public.paper_broker_execution_records using gin (reason_codes jsonb_path_ops);

create index if not exists paper_broker_execution_records_payload_idx
    on public.paper_broker_execution_records using gin (payload jsonb_path_ops);

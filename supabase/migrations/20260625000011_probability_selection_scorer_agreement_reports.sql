create table if not exists public.probability_selection_scorer_agreement_reports (
    report_sha256 text primary key,
    generated_at timestamptz not null,
    config_version text not null,
    selection_generated_at timestamptz,
    scorer_generated_at timestamptz,
    selected_count integer not null,
    scorer_candidate_count integer not null,
    selected_market_overlap_count integer not null,
    selected_condition_overlap_count integer not null,
    rejected_but_scored_count integer not null,
    scored_but_unselected_count integer not null,
    scorer_gate_status text not null,
    agreement_status text not null,
    recommended_next_step text not null,
    reason_codes jsonb not null,
    reason_code_divergence_counts jsonb not null,
    payload jsonb not null,
    paper_only boolean not null default true,
    report_only boolean not null default true,
    readonly boolean not null default true,
    inserted_at timestamptz not null default now(),
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
    check (selected_count >= 0),
    check (scorer_candidate_count >= 0),
    check (selected_market_overlap_count >= 0),
    check (selected_condition_overlap_count >= 0),
    check (rejected_but_scored_count >= 0),
    check (scored_but_unselected_count >= 0),
    check (agreement_status in ('aligned', 'gate_blocked', 'insufficient_identifiers', 'low_overlap', 'missing_inputs')),
    check (jsonb_typeof(reason_codes) = 'array'),
    check (jsonb_typeof(reason_code_divergence_counts) = 'array'),
    check (jsonb_typeof(payload) = 'object'),
    check (paper_only is true),
    check (report_only is true),
    check (readonly is true),
    check ((payload ->> 'paper_only') = 'true'),
    check ((payload ->> 'report_only') = 'true'),
    check ((payload ->> 'readonly') = 'true'),
    check (not (payload ?| array[
        'account',
        'auth',
        'condition_id',
        'market_slug',
        'order',
        'private_key',
        'question',
        'wallet'
    ]))
);

create index if not exists probability_selection_scorer_agreement_generated_order_idx
    on public.probability_selection_scorer_agreement_reports (generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists probability_selection_scorer_agreement_config_order_idx
    on public.probability_selection_scorer_agreement_reports (config_version, generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists probability_selection_scorer_agreement_status_order_idx
    on public.probability_selection_scorer_agreement_reports (agreement_status, generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists probability_selection_scorer_agreement_scorer_gate_order_idx
    on public.probability_selection_scorer_agreement_reports (scorer_gate_status, generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists probability_selection_scorer_agreement_reason_codes_idx
    on public.probability_selection_scorer_agreement_reports using gin (reason_codes jsonb_path_ops);

create index if not exists probability_selection_scorer_agreement_payload_idx
    on public.probability_selection_scorer_agreement_reports using gin (payload jsonb_path_ops);

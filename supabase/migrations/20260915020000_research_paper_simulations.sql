-- One immutable prospective input/result per original research record.
-- This is simulation evidence, not an order, account action or fee attestation.
create table research_capture.paper_simulations (
  record_id text primary key references research_capture.attempts(record_id),
  request_sha256 text not null check (request_sha256 ~ '^[a-f0-9]{64}$'),
  attempt_payload_sha256 text not null check (attempt_payload_sha256 ~ '^[a-f0-9]{64}$'),
  first_record_id text not null references research_capture.attempts(record_id),
  history_at timestamptz not null check (isfinite(history_at)),
  history_sha256 text not null check (history_sha256 ~ '^[a-f0-9]{64}$'),
  forecast_cutoff_at timestamptz not null check (isfinite(forecast_cutoff_at)),
  recorded_at timestamptz not null check (isfinite(recorded_at)),
  input_payload text not null check (octet_length(input_payload) between 1 and 4194304),
  input_sha256 text not null check (input_sha256 ~ '^[a-f0-9]{64}$'),
  result_payload text not null check (octet_length(result_payload) between 1 and 1048576),
  result_sha256 text not null check (result_sha256 ~ '^[a-f0-9]{64}$'),
  paper_only boolean not null default true check (paper_only is true),
  report_only boolean not null default true check (report_only is true),
  readonly boolean not null default true check (readonly is true),
  check (history_at <= recorded_at and recorded_at < forecast_cutoff_at),
  check (encode(sha256(convert_to(input_payload,'UTF8')),'hex') = input_sha256),
  check (encode(sha256(convert_to(result_payload,'UTF8')),'hex') = result_sha256)
);

create function research_capture.stamp_paper_simulation() returns trigger
language plpgsql set search_path = pg_catalog as $$
declare claimed research_capture.execution_claims%rowtype;
        original research_capture.attempts%rowtype;
        first_id text; body jsonb; result jsonb; decision timestamptz; age integer;
begin
  select * into strict original from research_capture.attempts where record_id=new.record_id;
  perform pg_advisory_xact_lock(hashtextextended('polymarket/research_capture/' || original.condition_id,0));
  select * into strict claimed from research_capture.execution_claims where record_id=new.record_id;
  select record_id into strict first_id from research_capture.attempts
    where team_id=original.team_id and model_id=original.model_id
      and protocol_version=original.protocol_version and condition_id=original.condition_id
    order by recorded_at,record_id limit 1;
  new.recorded_at := clock_timestamp();
  body := new.input_payload::jsonb;
  result := new.result_payload::jsonb;
  decision := (body ->> 'decision_at')::timestamptz;
  age := (body ->> 'max_age_seconds')::integer;
  if (body ->> 'schema_version' = 'research-paper-input-v1'
      and body ->> 'record_id' = new.record_id
      and body ->> 'record_sha256' ~ '^[a-f0-9]{64}$'
      and body -> 'paper_only' = 'true'::jsonb and body -> 'report_only' = 'true'::jsonb
      and body -> 'readonly' = 'true'::jsonb
      and original.team_id in ('crypto_btc','crypto_eth')
      and claimed.condition_id=original.condition_id and claimed.market_slug=original.market_slug
      and claimed.request_sha256=new.request_sha256
      and original.payload_sha256=new.attempt_payload_sha256
      and first_id=new.first_record_id
      and new.forecast_cutoff_at=(claimed.request_payload::jsonb ->> 'forecast_cutoff_at')::timestamptz
      and isfinite(decision) and age between 1 and 300
      and original.recorded_at <= decision and decision <= new.history_at
      and new.history_at <= new.recorded_at and new.recorded_at < new.forecast_cutoff_at
      and new.recorded_at-decision <= make_interval(secs => age)
      and result ->> 'record_id'=new.record_id
      and result ->> 'record_sha256'=body ->> 'record_sha256'
      and result ->> 'team_id'=original.team_id and result ->> 'model_id'=original.model_id
      and result ->> 'protocol_version'=original.protocol_version
      and result ->> 'condition_id'=original.condition_id
      and result ->> 'status' in ('paper_scenario_ready','paper_scenario_rejected','not_simulated')
      and result ->> 'original_reason_code' in
          ('outcome_pending','research_failed','research_blocked','intake_blocked','later_attempt')) is not true
      or exists (select 1 from research_capture.outcomes where condition_id=original.condition_id) then
    raise exception 'research_paper_admission_invalid';
  end if;
  return new;
end $$;

create function research_capture.finish_paper_simulation() returns trigger
language plpgsql set search_path = pg_catalog as $$
begin
  -- Deferred check narrows long-transaction exposure. It is not a promise about
  -- the later WAL flush or the time the caller receives COMMIT acknowledgement.
  if clock_timestamp() >= new.forecast_cutoff_at then
    raise exception 'research_paper_admission_expired';
  end if;
  return new;
end $$;

create trigger stamp_paper_simulation before insert on research_capture.paper_simulations
  for each row execute function research_capture.stamp_paper_simulation();
create constraint trigger finish_paper_simulation after insert on research_capture.paper_simulations
  deferrable initially deferred for each row execute function research_capture.finish_paper_simulation();
create trigger immutable_paper_simulations before update or delete on research_capture.paper_simulations
  for each row execute function research_capture.reject_mutation();
create trigger no_truncate_paper_simulations before truncate on research_capture.paper_simulations
  for each statement execute function research_capture.reject_mutation();
revoke all on research_capture.paper_simulations from public;
revoke all on function research_capture.stamp_paper_simulation() from public;
revoke all on function research_capture.finish_paper_simulation() from public;

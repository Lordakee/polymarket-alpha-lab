-- Native project PostgreSQL: resolution evidence, not trading authorization.
-- Applied by the hash-locked migration manager; outer transaction is its owner.
CREATE TABLE research_capture.resolution_reviews (
  review_id text PRIMARY KEY CHECK (length(review_id) BETWEEN 1 AND 128 AND review_id ~ '^[A-Za-z0-9_.:-]+$'),
  condition_id text NOT NULL CHECK (condition_id ~ '^0x[0-9a-f]{64}$'),
  market_slug text NOT NULL,
  checked_at timestamptz NOT NULL CHECK (isfinite(checked_at)),
  recorded_at timestamptz NOT NULL,
  status text NOT NULL CHECK (status IN ('ready','pending','blocked','needs_confirmation')),
  reason_code text NOT NULL,
  actual_yes boolean,
  resolved_at timestamptz,
  payload text NOT NULL CHECK (octet_length(payload) BETWEEN 1 AND 2097152),
  payload_sha256 text NOT NULL CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),
  paper_only boolean NOT NULL DEFAULT true CHECK (paper_only IS TRUE),
  report_only boolean NOT NULL DEFAULT true CHECK (report_only IS TRUE),
  readonly boolean NOT NULL DEFAULT true CHECK (readonly IS TRUE),
  FOREIGN KEY (condition_id,market_slug) REFERENCES research_capture.markets(condition_id,market_slug),
  CHECK (checked_at <= recorded_at),
  CHECK ((status='ready' AND actual_yes IS NOT NULL AND resolved_at IS NOT NULL AND isfinite(resolved_at)) OR
         (status<>'ready' AND actual_yes IS NULL AND resolved_at IS NULL)),
  CHECK (encode(sha256(convert_to(payload,'UTF8')),'hex')=payload_sha256),
  CHECK ((payload::jsonb ->> 'schema_version'='research-resolution-v1') IS TRUE),
  CHECK ((payload::jsonb ->> 'review_id'=review_id) IS TRUE),
  CHECK ((payload::jsonb ->> 'condition_id'=condition_id) IS TRUE),
  CHECK ((payload::jsonb ->> 'market_slug'=market_slug) IS TRUE),
  CHECK (((payload::jsonb ->> 'checked_at')::timestamptz=checked_at) IS TRUE),
  CHECK ((payload::jsonb #>> '{assessment,status}'=status) IS TRUE),
  CHECK ((payload::jsonb #>> '{assessment,reason_code}'=reason_code) IS TRUE),
  CHECK ((payload::jsonb -> 'paper_only'='true'::jsonb) IS TRUE),
  CHECK ((payload::jsonb -> 'report_only'='true'::jsonb) IS TRUE),
  CHECK ((payload::jsonb -> 'readonly'='true'::jsonb) IS TRUE),
  CHECK (status<>'ready' OR ((
    reason_code='operator_confirmed' AND
    payload::jsonb #> '{confirmation,independently_verified}'='true'::jsonb AND
    payload::jsonb #> '{confirmation,paper_only}'='true'::jsonb AND
    payload::jsonb #> '{confirmation,report_only}'='true'::jsonb AND
    payload::jsonb #> '{confirmation,readonly}'='true'::jsonb AND
    payload::jsonb #>> '{confirmation,condition_id}'=condition_id AND
    payload::jsonb #>> '{confirmation,market_slug}'=market_slug AND
    payload::jsonb #> '{confirmation,actual_yes}'=to_jsonb(actual_yes) AND
    payload::jsonb #> '{assessment,candidate_yes}'=to_jsonb(actual_yes) AND
    (payload::jsonb #>> '{confirmation,resolved_at}')::timestamptz=resolved_at AND
    resolved_at <= (payload::jsonb #>> '{snapshot,fetched_at}')::timestamptz AND
    (payload::jsonb #>> '{snapshot,fetched_at}')::timestamptz <= (payload::jsonb #>> '{confirmation,confirmed_at}')::timestamptz AND
    (payload::jsonb #>> '{confirmation,confirmed_at}')::timestamptz <= checked_at AND
    checked_at-(payload::jsonb #>> '{snapshot,fetched_at}')::timestamptz <= interval '600 seconds' AND
    payload::jsonb #>> '{confirmation,gamma_content_sha256}'=payload::jsonb #>> '{snapshot,content_sha256}'
  ) IS TRUE))
);
CREATE FUNCTION research_capture.stamp_resolution_review() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN
  NEW.recorded_at := clock_timestamp();
  IF NEW.recorded_at-NEW.checked_at > interval '600 seconds' THEN
    RAISE EXCEPTION 'research_resolution_capture_time_invalid';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER stamp_resolution_review BEFORE INSERT ON research_capture.resolution_reviews
  FOR EACH ROW EXECUTE FUNCTION research_capture.stamp_resolution_review();
CREATE TRIGGER immutable_resolution_reviews BEFORE UPDATE OR DELETE ON research_capture.resolution_reviews
  FOR EACH ROW EXECUTE FUNCTION research_capture.reject_mutation();
CREATE TRIGGER no_truncate_resolution_reviews BEFORE TRUNCATE ON research_capture.resolution_reviews
  FOR EACH STATEMENT EXECUTE FUNCTION research_capture.reject_mutation();

CREATE FUNCTION research_capture.check_resolution_outcome_link() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog AS $$
DECLARE ref_prefix constant text := 'urn:polymarket-alpha-lab:resolution-review:';
BEGIN
  IF starts_with(NEW.source_reference,ref_prefix) AND NOT EXISTS (
    SELECT 1 FROM research_capture.resolution_reviews r
    WHERE r.review_id=substr(NEW.source_reference,length(ref_prefix)+1) AND r.status='ready'
      AND r.condition_id=NEW.condition_id AND r.market_slug=NEW.market_slug
      AND r.actual_yes=NEW.actual_yes AND r.resolved_at=NEW.resolved_at
      AND r.payload_sha256=NEW.source_content_sha256
  ) THEN RAISE EXCEPTION 'research_resolution_outcome_link_invalid'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER check_resolution_outcome_link BEFORE INSERT ON research_capture.outcomes
  FOR EACH ROW EXECUTE FUNCTION research_capture.check_resolution_outcome_link();
CREATE FUNCTION research_capture.require_resolution_outcome() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog AS $$
BEGIN
  IF NEW.status='ready' AND NOT EXISTS (
    SELECT 1 FROM research_capture.outcomes o WHERE o.condition_id=NEW.condition_id
      AND o.market_slug=NEW.market_slug AND o.actual_yes=NEW.actual_yes AND o.resolved_at=NEW.resolved_at
      AND o.source_reference='urn:polymarket-alpha-lab:resolution-review:' || NEW.review_id
      AND o.source_content_sha256=NEW.payload_sha256
  ) THEN RAISE EXCEPTION 'research_resolution_outcome_missing'; END IF;
  RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER require_resolution_outcome AFTER INSERT ON research_capture.resolution_reviews
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION research_capture.require_resolution_outcome();
REVOKE ALL ON research_capture.resolution_reviews FROM PUBLIC;
REVOKE ALL ON FUNCTION research_capture.stamp_resolution_review() FROM PUBLIC;
REVOKE ALL ON FUNCTION research_capture.check_resolution_outcome_link() FROM PUBLIC;
REVOKE ALL ON FUNCTION research_capture.require_resolution_outcome() FROM PUBLIC;

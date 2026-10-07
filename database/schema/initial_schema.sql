-- X-SENTINEL V2 canonical schema reference.
-- DO NOT apply this file manually in normal development. Alembic migrations are authoritative.
-- Revision: 0001_v2_multiuser

CREATE TABLE users (
  id uuid PRIMARY KEY,
  email varchar(320) NOT NULL,
  normalized_email varchar(320) NOT NULL UNIQUE,
  display_name varchar(200),
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE roles (
  id serial PRIMARY KEY,
  code varchar(64) NOT NULL UNIQUE,
  description varchar(255)
);

CREATE TABLE user_roles (
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role_id integer NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
  assigned_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, role_id)
);

CREATE TABLE model_versions (
  id uuid PRIMARY KEY,
  name varchar(120) NOT NULL,
  version varchar(120) NOT NULL,
  sha256 varchar(64) NOT NULL,
  config_hash varchar(64) NOT NULL,
  metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  is_active boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (name, version)
);

CREATE TABLE analysis_jobs (
  id uuid PRIMARY KEY,
  request_id varchar(128) NOT NULL UNIQUE,
  user_id uuid REFERENCES users(id) ON DELETE SET NULL,
  model_version_id uuid REFERENCES model_versions(id) ON DELETE SET NULL,
  status varchar(32) NOT NULL DEFAULT 'queued' CHECK (status IN ('queued','running','completed','failed','quarantined')),
  input_mode varchar(32) NOT NULL DEFAULT 'vector' CHECK (input_mode IN ('vector','raw_pe')),
  input_sha256 varchar(64),
  input_artifact_uri text,
  config_version varchar(128),
  demo_mode boolean NOT NULL DEFAULT true,
  error_code varchar(128),
  error_message text,
  created_at timestamptz NOT NULL DEFAULT now(),
  started_at timestamptz,
  completed_at timestamptz
);

CREATE TABLE analysis_results (
  analysis_job_id uuid PRIMARY KEY REFERENCES analysis_jobs(id) ON DELETE CASCADE,
  malware_score double precision,
  suspicion_score double precision,
  threshold double precision,
  decision varchar(32) NOT NULL DEFAULT 'unknown' CHECK (decision IN ('unknown','pass','alert','quarantine')),
  latency_ms double precision,
  view_contributions jsonb NOT NULL DEFAULT '{}'::jsonb,
  result_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  evidence_uri text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE detector_scores (
  analysis_job_id uuid NOT NULL REFERENCES analysis_jobs(id) ON DELETE CASCADE,
  detector_code varchar(16) NOT NULL CHECK (detector_code IN ('M1','M2','M3','M4','M5')),
  score double precision NOT NULL,
  diagnostics jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (analysis_job_id, detector_code)
);

CREATE TABLE alerts (
  id uuid PRIMARY KEY,
  analysis_job_id uuid NOT NULL REFERENCES analysis_jobs(id) ON DELETE CASCADE,
  severity varchar(16) NOT NULL DEFAULT 'medium' CHECK (severity IN ('low','medium','high','critical')),
  status varchar(32) NOT NULL DEFAULT 'open' CHECK (status IN ('open','acknowledged','resolved','dismissed')),
  reason text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  resolved_at timestamptz
);

CREATE TABLE artifacts (
  id uuid PRIMARY KEY,
  analysis_job_id uuid REFERENCES analysis_jobs(id) ON DELETE CASCADE,
  kind varchar(64) NOT NULL,
  uri text NOT NULL,
  sha256 varchar(64) NOT NULL,
  content_type varchar(255),
  size_bytes bigint,
  metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE audit_events (
  id bigserial PRIMARY KEY,
  request_id varchar(128),
  user_id uuid REFERENCES users(id) ON DELETE SET NULL,
  event_type varchar(128) NOT NULL,
  entity_type varchar(64),
  entity_id varchar(128),
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE experiment_runs (
  id uuid PRIMARY KEY,
  created_by_user_id uuid REFERENCES users(id) ON DELETE SET NULL,
  experiment_code varchar(16) NOT NULL CHECK (experiment_code IN ('E0','E1','E2','E3','E4','E5')),
  status varchar(32) NOT NULL DEFAULT 'planned' CHECK (status IN ('planned','running','completed','failed')),
  config_hash varchar(64) NOT NULL,
  seed integer,
  results_uri text,
  metrics_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz
);

-- Blind ground-truth/manifest data is intentionally absent from this application schema.

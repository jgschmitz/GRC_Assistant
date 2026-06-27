-- ============================================================================
-- Legacy GRC relational model (the "before").
-- This is the highly-normalized MySQL/PostgreSQL schema we are migrating away
-- from. It is included so the conversion in scripts/migrate.py is self-evident:
-- every table below maps to a MongoDB collection or an embedded sub-document.
--
-- Color legend from the source ER diagrams:
--   raw data, derived data, log tables.
-- ============================================================================

-- ---- Governance reference data (raw) --------------------------------------

CREATE TABLE policies (
    policy_id       VARCHAR(32) PRIMARY KEY,   -- version lives at end of name, e.g. "POL-111"
    title           VARCHAR(255) NOT NULL,
    version         INT NOT NULL,
    status          VARCHAR(32)  NOT NULL,
    effective_date  DATE,
    retired_date    DATE NULL,
    body            MEDIUMTEXT,
    owner_team      VARCHAR(128),
    owner_contact   VARCHAR(128)
);

CREATE TABLE security_standards (
    standard_id     VARCHAR(32) PRIMARY KEY,   -- e.g. "111.1.1" (may not exist yet)
    name            VARCHAR(255) NOT NULL,
    statement       MEDIUMTEXT,
    version         INT,
    effective_date  DATE,
    retired_date    DATE NULL
);

CREATE TABLE control_standards (
    control_standard_id VARCHAR(32) PRIMARY KEY,  -- e.g. "111.1.01" (imported level)
    security_standard_id VARCHAR(32),
    control_name    VARCHAR(255),
    statement       MEDIUMTEXT,
    status          VARCHAR(32),
    version         INT,
    effective_date  DATE,
    retired_date    DATE NULL,
    FOREIGN KEY (security_standard_id) REFERENCES security_standards (standard_id)
);

CREATE TABLE controls (
    control_id      VARCHAR(32) PRIMARY KEY,
    control_input   VARCHAR(255),
    control_class   VARCHAR(64),
    classname       VARCHAR(128),
    version         INT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE documents (
    document_id     VARCHAR(32) PRIMARY KEY,
    policy_id       VARCHAR(32),
    filename        VARCHAR(255),
    mime_type       VARCHAR(128),
    version         INT,
    blob_ref        VARCHAR(512),  -- pointer to file store
    FOREIGN KEY (policy_id) REFERENCES policies (policy_id)
);

-- ---- Operational risk data (raw) ------------------------------------------

CREATE TABLE risk_records (
    risk_record_id  VARCHAR(32) PRIMARY KEY,
    title           VARCHAR(255),
    control_name    VARCHAR(255),
    control_class   VARCHAR(64),
    severity        VARCHAR(32),
    likelihood      VARCHAR(32),
    business_unit   VARCHAR(128),
    division        VARCHAR(128),
    submit_request  TIMESTAMP NULL,
    risk_owner      VARCHAR(128),
    risk_manager    VARCHAR(128),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NULL
);

-- One-to-one "type" tables that bloat the relational model. These collapse
-- into a single embedded `typeDetails` sub-document in MongoDB.
CREATE TABLE vulnerability_type (
    risk_record_id  VARCHAR(32) PRIMARY KEY,
    term_source     VARCHAR(255),
    device_scope    VARCHAR(64),     -- internal / external
    is_application  BOOLEAN,
    ip_simple_id    VARCHAR(64),
    justification   MEDIUMTEXT,
    FOREIGN KEY (risk_record_id) REFERENCES risk_records (risk_record_id)
);

CREATE TABLE firewall_type (
    risk_record_id  VARCHAR(32) PRIMARY KEY,
    protocols_used  VARCHAR(255),
    rule_logged     BOOLEAN,
    connection_scope VARCHAR(64),    -- internal / external
    cloud_provider  VARCHAR(128),
    cloud_service   VARCHAR(128),
    firewall_category VARCHAR(128),
    access_granted_how VARCHAR(255),
    FOREIGN KEY (risk_record_id) REFERENCES risk_records (risk_record_id)
);

-- ---- Risk analysis / groupings (derived) ----------------------------------

CREATE TABLE risk_analysis (
    analysis_id     VARCHAR(32) PRIMARY KEY,
    risk_record_id  VARCHAR(32),
    recommend_summary MEDIUMTEXT,
    process_summary MEDIUMTEXT,
    business_impact MEDIUMTEXT,
    -- embedding stored as an opaque blob/array in the legacy DB
    embedding       LONGBLOB,
    FOREIGN KEY (risk_record_id) REFERENCES risk_records (risk_record_id)
);

CREATE TABLE risk_grouping (
    item_set_id     VARCHAR(32) PRIMARY KEY,
    risk_record_id  VARCHAR(32),
    flow_1          VARCHAR(255),
    flow_2          VARCHAR(255),
    flow_3          VARCHAR(255),
    FOREIGN KEY (risk_record_id) REFERENCES risk_records (risk_record_id)
);

-- ---- Policy mapping workflow (raw + derived) ------------------------------

CREATE TABLE jobs (
    job_id          VARCHAR(32) PRIMARY KEY,
    status          VARCHAR(32),
    progress        INT,
    available_standards INT,
    control_filename VARCHAR(255),
    standards_filename VARCHAR(255),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE job_rows (
    job_id          VARCHAR(32),
    row_id          INT,
    raw_input       MEDIUMTEXT,
    control_exception MEDIUMTEXT,
    recommended_standards MEDIUMTEXT,
    finalized_standard_pair VARCHAR(255),
    identifier_gaps MEDIUMTEXT,
    row_status      VARCHAR(32),
    last_error      MEDIUMTEXT,
    started_at      TIMESTAMP NULL,
    completed_at    TIMESTAMP NULL,
    PRIMARY KEY (job_id, row_id),
    FOREIGN KEY (job_id) REFERENCES jobs (job_id)
);

CREATE TABLE approved_control_mappings (
    control_key     VARCHAR(32) PRIMARY KEY,
    control_id      VARCHAR(32),
    source_job_id   VARCHAR(32),
    service_temp_id VARCHAR(64),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NULL,
    FOREIGN KEY (control_id) REFERENCES controls (control_id),
    FOREIGN KEY (source_job_id) REFERENCES jobs (job_id)
);

-- ---- Log tables -----------------------------------------------------------

CREATE TABLE change_log (
    change_record_id VARCHAR(32) PRIMARY KEY,
    policy_id       VARCHAR(32),
    change_description MEDIUMTEXT,
    status          VARCHAR(32),
    change_type     VARCHAR(64),
    version_no      INT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (policy_id) REFERENCES policies (policy_id)
);

CREATE TABLE risk_rules_log (
    record_id       VARCHAR(32) PRIMARY KEY,
    risk_record_id  VARCHAR(32),
    event_class     VARCHAR(64),
    field_changed   VARCHAR(128),
    changed_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (risk_record_id) REFERENCES risk_records (risk_record_id)
);

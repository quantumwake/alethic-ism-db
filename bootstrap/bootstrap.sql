drop table if exists user_profile cascade;
create table user_profile (
  user_id character varying(36) primary key not null,
  email character varying(255),
  created_date timestamp without time zone not null default CURRENT_TIMESTAMP,
  name character varying(255),
  max_agentic_units integer
);

-- create user profile credentials
drop table if exists user_profile_credential cascade;
create table user_profile_credential (
    user_id varchar(36) not null primary key references user_profile (user_id),
    type varchar(255) not null,
    credentials varchar(255) not null,
    created_date timestamp not null default current_timestamp
);

drop table if exists user_project cascade;
create table user_project (
  project_id varchar(36) not null primary key,
  project_name varchar(255) not null,
  user_id varchar(36) not null references user_profile (user_id),
  created_date timestamp not null default current_timestamp,
  unique (user_id, project_name)
);

drop table if exists workflow_node cascade;
create table workflow_node (
    node_id varchar(36) not null primary key,
    object_id varchar(255) null,    -- the actual object id based on the identifier
    node_type varchar(255) not null,
    node_label varchar(255) null,
    project_id varchar(36) not null references user_project (project_id),
    position_x int null,
    position_y int null,
    width int null,
    height int null
);

drop table if exists workflow_edge;
create table workflow_edge (
    source_node_id varchar(36) not null references workflow_node (node_id),
    target_node_id varchar(36) not null references  workflow_node (node_id),
    source_handle varchar(255) null,
    target_handle varchar(255) null,
    animated bool not null default true,
    edge_label varchar(255) null,
    type varchar(255) not null default 'default',
    primary key (source_node_id, target_node_id)
);

drop table if exists template;
create table template (
    template_id varchar(36) not null primary key,
    template_path varchar(255) not null,
    template_content text not null,
    template_type varchar(255) default 'user_template',
    project_id varchar(36) null references user_project (project_id)
);

drop table if exists state cascade;
create table state
(
    id varchar(36) not null primary key,
    project_id varchar(36) null references user_project (project_id),
    count int not null default 0,
    state_type varchar(255) not null default 'StateConfig'
);

drop table if exists state_config;
create table state_config (
    state_id varchar(255) not null references state(id),
    attribute varchar(255) not null,
    data text,
    primary key (state_id, attribute)
);

drop table if exists state_column_key_definition;
create table state_column_key_definition(
    id serial not null primary key,
    state_id varchar(255) not null references state (id),
    name varchar(255) not null,
    alias varchar(255),
    required bool default false,
    callable bool default false,
    definition_type varchar(255) not null
);

drop table if exists state_column cascade;
create table state_column (
    id serial not null primary key,
    state_id varchar(36) not null references state(id),
    name varchar(255) not null,
    data_type varchar(64) default 'str',
    required boolean default true,
    callable boolean default false,
    min_length int default 0,
    max_length int default 255,
    dimensions int default 384,
    value varchar(255),
    source_column_name varchar(255)
);

alter table state_column add column display_order int default 0;

create unique index state_column_unique_key on state_column (id, state_id);
create unique index state_column_state_name_ux on state_column (state_id, name);

drop table if exists state_column_data;
create table state_column_data
(
    column_id bigint not null references state_column (id),
    data_index bigint not null,
    data_value text
);

drop table if exists state_column_data_mapping;
create table state_column_data_mapping (
    state_id varchar(36) not null,
    state_key varchar(255) not null,
    data_index bigint not null,
    primary key (state_id, state_key, data_index)
);

-- drop table if exists model cascade;
-- create table model (
--     id serial primary key,
--     provider_name varchar(255) not null,
--     model_name varchar(255) not null,
--     unique (provider_name, model_name)
-- );
--
-- insert into model (provider_name, model_name) values ('OpenAI', 'gpt-4-1106-preview');
-- insert into model (provider_name, model_name) values ('Anthropic', 'claude-2.0');
-- insert into model (provider_name, model_name) values ('Anthropic', 'claude-2.1');
-- commit;

drop table if exists processor_class cascade;
create table processor_class (
    class_name varchar(32) not null primary key
);

INSERT INTO processor_class VALUES
    ('CodeProcessing'),
    ('NaturalLanguageProcessing'),
    ('ImageProcessing'),
    ('DataTransformation'),
    ('TextProcessing'),
    ('VideoProcessing'),
    ('AudioProcessing'),
    ('DataAnalysis'),
    ('SignalProcessing'),
    ('MachineLearning'),
    ('DatabaseProcessing'),
    ('Interaction')
    ON CONFLICT DO NOTHING;

COMMIT;

DROP TABLE IF EXISTS processor_provider cascade;
CREATE TABLE processor_provider (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    version VARCHAR(32) NOT NULL,
    class_name VARCHAR(32) NOT NULL REFERENCES processor_class (class_name),
    user_id varchar(36) NULL REFERENCES user_profile (user_id),
    project_id VARCHAR(36) NULL REFERENCES user_project (project_id)
);

INSERT INTO processor_provider (id, name, version, class_name) VALUES
    ('language/models/openai/gpt-4o', 'OpenAI', 'gpt-4o', 'NaturalLanguageProcessing'),
    ('language/models/openai/gpt-4o-mini', 'OpenAI', 'gpt-4o-mini', 'NaturalLanguageProcessing'),
    ('language/models/openai/gpt-4o-2024-05-13', 'OpenAI', 'gpt-4o-2024-05-13', 'NaturalLanguageProcessing'),
    ('language/models/openai/gpt-4o-2024-08-06', 'OpenAI', 'gpt-4o-2024-08-06', 'NaturalLanguageProcessing'),
    ('language/models/openai/gpt-4o-2024-11-20', 'OpenAI', 'gpt-4o-2024-11-20', 'NaturalLanguageProcessing'),
    ('language/models/openai/gpt-4o-latest', 'OpenAI', 'chatgpt-4o-latest', 'NaturalLanguageProcessing'),
    ('language/models/openai/o1-preview', 'OpenAI', 'o1-preview', 'NaturalLanguageProcessing'),
    ('image/models/openai/dall-e-2', 'OpenAI', 'dall-e-2', 'ImageProcessing'),
    ('image/models/openai/dall-e-3', 'OpenAI', 'dall-e-3', 'ImageProcessing'),
    ('language/models/llama/llama3.1-8b', 'LLama', 'llama3.1-8b', 'NaturalLanguageProcessing'),
    ('language/models/llama/llama3.1-705b', 'LLama', 'llama3.1-70b', 'NaturalLanguageProcessing'),
    ('language/models/llama/llama3.1-405b', 'LLama', 'llama3.1-405b', 'NaturalLanguageProcessing'),
    ('language/models/google/gemini-1.5-flash', 'Google', 'gemini-1.5-flash', 'NaturalLanguageProcessing'),
    ('language/models/google/gemini-1.5-pro-001', 'Google', 'gemini-1.5-pro-001', 'NaturalLanguageProcessing'),
    ('language/models/anthropic/claude-2.0', 'Anthropic', 'claude-2', 'NaturalLanguageProcessing'),
    ('language/models/anthropic/claude-2.1', 'Anthropic', 'claude-2.1', 'NaturalLanguageProcessing'),
    ('language/models/anthropic/claude-3-opus-20240229', 'Anthropic', 'claude-3-opus-20240229', 'NaturalLanguageProcessing'),
    ('language/models/anthropic/claude-3-5-sonnet-latest', 'Anthropic', 'claude-3-5-sonnet-latest', 'NaturalLanguageProcessing'),
    ('language/models/anthropic/claude-3-5-haiku-latest', 'Anthropic', 'claude-3-5-haiku-latest', 'NaturalLanguageProcessing'),
    ('language/models/anthropic/claude-3-opus-latest', 'Anthropic', 'claude-3-opus-latest', 'NaturalLanguageProcessing'),
    ('language/models/anthropic/claude-3-5-sonnet-20240620', 'Anthropic', 'claude-3-5-sonnet-20240620', 'NaturalLanguageProcessing'),
    ('language/models/anthropic/claude-3-5-sonnet-20241022', 'Anthropic', 'claude-3-5-sonnet-20241022', 'NaturalLanguageProcessing'),
    ('language/models/anthropic/claude-3-5-haiku-20241022', 'Anthropic', 'claude-3-5-haiku-20241022', 'NaturalLanguageProcessing'),
    ('data/transformers/mixer/state-online-join-1.0', 'State Online Join', 'state-online-join-1.0', 'DataTransformation'),
    ('data/transformers/mixer/state-online-merge-1.0', 'State Online Merge', 'state-online-merge-1.0', 'DataTransformation'),
    ('data/transformers/mixer/state-online-cross-join-1.0', 'State Online Cross Join', 'state-online-cross-join-1.0', 'DataTransformation'),
    ('data/transformers/sampler/state-sample-multiplier-1.0', 'State Sample Multiplier', 'state-sample-multiplier-1.0', 'DataTransformation'),
    ('data/source/sql-1.0', 'SQL', 'sql-1.0', 'DatabaseProcessing'),
    ('code/executor/python/python-executor-1.0', 'Python Executor', 'python-executor-1.0', 'CodeProcessing'),
    ('code/executor/mako/mako-executor-1.0', 'Mako Executor', 'mako-executor-1.0', 'CodeProcessing'),
    ('interaction/user/user-interaction', 'User Interaction', 'user-interaction-1.0', 'Interaction')
ON CONFLICT (id) DO UPDATE SET
    name=EXCLUDED.name,
    version=EXCLUDED.version,
    class_name=EXCLUDED.class_name;

drop type if exists processor_status cascade;
create type processor_status AS ENUM (
       'CREATED', 'ROUTE', 'ROUTED',
       'QUEUED', 'RUNNING', 'COMPLETED',
       'TERMINATE', 'STOPPED', 'FAILED'
);

drop table if exists processor cascade;
create table processor (
    id varchar(36) not null primary key,
    provider_id varchar(255) null references processor_provider (id),
    project_id varchar(36) not null references user_project (project_id),
    status processor_status not null
);

drop table if exists processor_property;
create table processor_property (
    processor_id varchar(255) not null references processor(id),
    name varchar(255) not null,
    value text,
    primary key (processor_id, name)
);

drop type if exists processor_state_direction cascade;
create type processor_state_direction AS ENUM (
       'INPUT', 'OUTPUT'
);

drop table if exists processor_state;
create table processor_state (
    id varchar(73) not null,
    internal_id serial not null,
    processor_id varchar(36) not null,
    state_id varchar(36) not null references state (id),
    direction processor_state_direction not null,
    status processor_status not null,
    count int null,
    current_index int null,
    maximum_index int null,
    primary key (processor_id, state_id, direction),
    unique (internal_id),
    unique (id)
);

alter table processor_state add constraint processor_state_state_id_fk foreign key (state_id) references state(id);
alter table processor_state add constraint processor_state_processor_id_fk foreign key (processor_id) references processor(id);
commit;

-- drop table if exists trace;
-- create table if not exists trace
-- (
--     id serial not null primary key,
--     partition   varchar(128)                            not null,
--     reference   varchar(128)                            not null,
--     action      varchar(255)                            not null,
--     action_time timestamp   default CURRENT_TIMESTAMP   not null,
--     level       trace_level default 'INFO'::trace_level not null,
--     message     text
-- );

drop table if exists monitor_log_event;
create table monitor_log_event (
    log_id serial not null primary key,
    log_type varchar(255) not null, -- TODO should be an enum of type log_type
    log_time timestamp not null default current_timestamp,
    internal_reference_id int null, -- an internal id depending on what is being monitored, e.g. a processor_state internal_id
    user_id varchar(36) null,       -- this is useful when processor_state_id is not defined
    project_id varchar(36) null,    -- this is useful when processor_state_id is not defined
    exception text null,
    data text null
);

CREATE OR REPLACE VIEW state_column_data_view
AS
SELECT sc.*, sd.* FROM state_column sc
 LEFT OUTER JOIN state_column_data sd
   ON sc.id = sd.column_id
ORDER BY state_id, data_index, column_id;

--- VALIDATION FUNCTION FOR COLUMN ID
DROP FUNCTION IF EXISTS validate_column_id;
CREATE OR REPLACE FUNCTION validate_column_id(new_id BIGINT, new_state_id VARCHAR)
RETURNS BIGINT AS $$
DECLARE
    result BIGINT;
BEGIN
    IF new_id IS NOT NULL THEN
        -- Check if the provided id exists with the given state_id
        IF EXISTS (SELECT 1 FROM state_column WHERE id = new_id AND state_id = new_state_id) THEN
            result := new_id;
        -- Check if the provided id exists with a different state_id
        ELSIF EXISTS (SELECT 1 FROM state_column WHERE id = new_id) THEN
            RAISE EXCEPTION 'ILLEGAL ID: The provided id already exists with a different state_id';
        ELSE
            result := NULL;
        END IF;
    ELSE
        result := NULL;
    END IF;

    RETURN result;
END;
$$ LANGUAGE plpgsql;


-- auto-generated definition
drop type if exists usage_unit_type cascade;
create type usage_unit_type as enum ('TOKEN', 'COMPUTE');

drop type if exists usage_unit_subtype cascade;
create type usage_unit_subtype as enum ('INPUT', 'OUTPUT');

-- alter type usage_unit_type owner to postgres;

drop table if exists usage;

-- drop table if exists usage;
create table if not exists usage
(
    id               serial primary key,
    transaction_time timestamp,
    project_id       varchar(36)        not null references public.user_project,
    resource_id      varchar(255)       not null,
    resource_type    varchar(255)       not null,
    unit_type        usage_unit_type    not null,
    unit_subtype     usage_unit_subtype not null,
    unit_count       integer default 0  not null,
    metadata         text
);

create index usage_project_idx on usage (project_id);
create index user_project_user_id_idx on user_project (user_id);

-- USAGE VIEW FOR USAGE TABLE (extracts year, month, day, hour, minute, second from transaction_time)
CREATE OR REPLACE VIEW usage_v
AS
SELECT
    extract(year from transaction_time) as year,
    extract(month from transaction_time) as month,
    extract(day from transaction_time) as day,
    extract(hour from transaction_time) as hour,
    extract(minute from transaction_time) as minute,
    extract(second from transaction_time) as second,
    up.user_id,
    u.project_id,
    u.resource_id,
    u.resource_type,
    u.unit_type,
    COALESCE(u.unit_count, 0) as unit_count
 FROM usage u
RIGHT OUTER JOIN user_project up
  ON up.project_id = u.project_id;


-- audit logging table for various user functions
-- create table audit (
--     partition varchar(128) not null,
--     reference varchar(128) not null,
--     action varchar(255) not null,
--     action_time timestamp not null default current_timestamp,
--     message text
-- );
--
--

drop table if exists session cascade;
create table session (
    session_id varchar(36) not null primary key,
    created_date    timestamp not null,
    owner_user_id   varchar(36) not null references user_profile (user_id)
);

drop table if exists session_message cascade;
create table session_message (
    message_id serial not null primary key,
    session_id varchar(36) not null references session (session_id),
    user_id varchar(36) not null references user_profile (user_id),
    original_content text null,
    executed_content text null,
    message_date timestamp not null
);

drop type if exists user_session_access_level cascade;
create type user_session_access_level as enum ('default', 'admin');

drop table if exists user_session_access cascade;
create table user_session_access (
    user_id varchar(36) not null references user_profile (user_id),
    session_id varchar(36) not null references session (session_id),
    access_level user_session_access_level not null default 'default',
    access_date timestamp not null
);


-- Define ENUM for configuration types
CREATE TYPE config_type AS ENUM ('secret', 'config_map');

-- Table to manage encryption key providers
DROP TABLE IF EXISTS vault;
CREATE TABLE vault (
    id VARCHAR(36) PRIMARY KEY, -- Unique identifier for the provider
    name VARCHAR(255) NOT NULL UNIQUE, -- Provider name (e.g., AWS KMS, HashiCorp Vault)
    type VARCHAR(50) NOT NULL, -- Provider type (e.g., 'kms', 'vault', 'local')
    metadata JSONB, -- Additional metadata for the provider (e.g., region, endpoint)
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

DROP TABLE IF EXISTS config_map;
CREATE TABLE config_map (
    id VARCHAR(36) PRIMARY KEY, -- Use UUID for unique identifiers
    name VARCHAR(255) NOT NULL, -- Descriptive name for the configuration
    type config_type NOT NULL, -- Enum for 'secret' or 'config_map'
    data JSONB NOT NULL, -- Configuration data (encrypted or plaintext)
    vault_key_id VARCHAR(255), -- ID of the encryption key (nullable)
    vault_id VARCHAR(36) REFERENCES vault (id), -- Reference to encryption key provider
    owner_id VARCHAR(36), -- Optional: ownership for multi-tenancy
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP -- Optional: soft delete support
);

-- Index for JSONB data to optimize queries
CREATE INDEX idx_configuration_data ON config_map USING gin(data jsonb_path_ops);

-- Index for filtering by type (optional optimization)
CREATE INDEX idx_configuration_type ON config_map(type);

-- Table for filters
DROP TABLE IF EXISTS filter CASCADE;
CREATE TABLE filter (
    id VARCHAR(255) PRIMARY KEY, -- Unique identifier for the filter
    name VARCHAR(255), -- Filter name
    user_id VARCHAR(36) NOT NULL REFERENCES user_profile(user_id), -- Owner of the filter
    filter_items JSONB NOT NULL DEFAULT '{}', -- Filter items stored as JSON
    created_date TIMESTAMP DEFAULT NOW(),
    updated_date TIMESTAMP DEFAULT NOW()
);

-- Index for user_id to optimize queries by user
CREATE INDEX idx_filter_user_id ON filter(user_id);

-- Index for JSONB filter_items to optimize queries
CREATE INDEX idx_filter_items ON filter USING gin(filter_items jsonb_path_ops);

create index processor_state_processor_direction_idx on processor_state (processor_id, direction);
create index processor_state_state_direction_idx on processor_state (state_id, direction);
create index processor_state_processor on processor_state (processor_id);
create index processor_state_state on processor_state (state_id);

create index state_project_idx on state (project_id);
create index processor_project_idx on processor (project_id);
create index state_column_state_idx on state_column (state_id);

create index state_config_state_idx on state_config (state_id);
create index template_project_idx on template (project_id);
create index workflow_node_project_idx on workflow_node (project_id);
create index state_column_key_definition_state_idx on state_column_key_definition (state_id);
create unique index state_column_key_definition_state_name_type_idx on state_column_key_definition (state_id, name, definition_type);
create index state_column_data_mapping_state_idx on state_column_data_mapping (state_id);
create index monitor_log_event_user_id on monitor_log_event (user_id);
create index monitor_log_event_project_id on monitor_log_event (project_id);
create index monitor_log_event_user_and_project_id on monitor_log_event (user_id, project_id);

-- Create ENUM type for action_type
CREATE TYPE action_type_enum AS ENUM ('slider', 'text', 'yes/no', 'dropdown');

-- Create the main table
CREATE TABLE state_action_definition (
    id varchar(36) PRIMARY KEY, -- Automatically generate a UUID if not provided
    state_id varchar(36) NOT NULL,                       -- Foreign key, if needed, can be defined here
    action_type action_type_enum NOT NULL,       -- ENUM type for action type
    field varchar(255) not null,                 -- Optional field name
    remote_url varchar(4000) DEFAULT null,            -- Defaults to FALSE if not provided
    field_options JSON NOT NULL,                -- Field options as raw JSON
    created_date TIMESTAMPTZ DEFAULT NOW()        -- Automatically set to current timestamp
);
create index state_action_definition_state_idx on state_action_definition (state_id);
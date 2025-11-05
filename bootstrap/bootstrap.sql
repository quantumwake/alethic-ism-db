drop table if exists user_profile cascade;
create table user_profile (
  user_id character varying(36) primary key not null,
  email character varying(255),
  created_date timestamp without time zone not null default CURRENT_TIMESTAMP,
  name character varying(255),
  max_agentic_units bigint not null default 1000
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

alter table user_project add column updated_date timestamp not null default current_timestamp;

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
    ('Interaction'),
    ('Proprietary')
    ON CONFLICT DO NOTHING;

COMMIT;

DROP TABLE IF EXISTS processor_provider cascade;
CREATE TABLE processor_provider (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(512) NOT NULL,
    version VARCHAR(256) NOT NULL,
    class_name VARCHAR(256) NOT NULL REFERENCES processor_class (class_name),
    user_id varchar(36) NULL REFERENCES user_profile (user_id),
    project_id VARCHAR(36) NULL REFERENCES user_project (project_id)
);

alter table processor_provider add column route jsonb null;
alter table processor_provider add column created_date timestamp not null default current_timestamp;
alter table processor_provider add column updated_date timestamp null default null;


INSERT INTO processor_provider (id, name, version, class_name) VALUES
 --- gpt 4o
    ('language/models/openai/gpt-4o', 'OpenAI', 'gpt-4o', 'NaturalLanguageProcessing'),
    ('language/models/openai/gpt-4o-mini', 'OpenAI', 'gpt-4o-mini', 'NaturalLanguageProcessing'),
    ('language/models/openai/gpt-4o-2024-05-13', 'OpenAI', 'gpt-4o-2024-05-13', 'NaturalLanguageProcessing'),
    ('language/models/openai/gpt-4o-2024-08-06', 'OpenAI', 'gpt-4o-2024-08-06', 'NaturalLanguageProcessing'),
    ('language/models/openai/gpt-4o-2024-11-20', 'OpenAI', 'gpt-4o-2024-11-20', 'NaturalLanguageProcessing'),
    ('language/models/openai/gpt-4o-latest', 'OpenAI', 'chatgpt-4o-latest', 'NaturalLanguageProcessing'),

 --- gpt 4.1
    ('language/models/openai/gpt-4.1', 'OpenAI', 'gpt-4.1', 'NaturalLanguageProcessing'),
    ('language/models/openai/gpt-4.1-mini', 'OpenAI', 'gpt-4.1-mini', 'NaturalLanguageProcessing'),
    ('language/models/openai/gpt-4.1-nano', 'OpenAI', 'gpt-4.1-nano', 'NaturalLanguageProcessing'),


--- gpt 5
    ('language/models/openai/gpt-5', 'OpenAI', 'gpt-5', 'NaturalLanguageProcessing'),
    ('language/models/openai/gpt-5-chat-latest', 'OpenAI', 'gpt-5-chat-latest', 'NaturalLanguageProcessing'),
    ('language/models/openai/gpt-5-mini', 'OpenAI', 'gpt-5-mini', 'NaturalLanguageProcessing'),
    ('language/models/openai/gpt-5-nano', 'OpenAI', 'gpt-5-nano', 'NaturalLanguageProcessing'),

--- other openai
    ('language/models/openai/o1-preview', 'OpenAI', 'o1-preview', 'NaturalLanguageProcessing'),
    ('image/models/openai/dall-e-2', 'OpenAI', 'dall-e-2', 'ImageProcessing'),
    ('image/models/openai/dall-e-3', 'OpenAI', 'dall-e-3', 'ImageProcessing'),

-- openrouter
    ('language/models/openrouter/openai/gpt-4.1', 'OpenRouter', 'openai/gpt-4.1', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/openai/gpt-4.1-mini', 'OpenRouter', 'openai/gpt-4.1-mini', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/openai/gpt-4.1-nano', 'OpenRouter', 'openai/gpt-4.1-nano', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/openai/gpt-4', 'OpenRouter', 'openai/gpt-4', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/openai/gpt-4o', 'OpenRouter', 'openai/gpt-4o', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/openai/gpt-4-turbo', 'OpenRouter', 'openai/gpt-4-turbo', 'NaturalLanguageProcessing'),

    ('language/models/openrouter/openai/gpt-5', 'OpenRouter', 'openai/gpt-5', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/openai/gpt-5-mini', 'OpenRouter', 'openai/gpt-5-mini', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/openai/gpt-5-codex', 'OpenRouter', 'openai/gpt-5-codex', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/openai/gpt-5-chat', 'OpenRouter', 'openai/gpt-5-chat', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/openai/gpt-5-nano', 'OpenRouter', 'openai/gpt-5-nano', 'NaturalLanguageProcessing'),

    ('language/models/openrouter/google/gemini-2.5-flash', 'OpenRouter', 'google/gemini-2.5-flash', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/google/gemini-2.5-pro', 'OpenRouter', 'google/gemini-2.5-pro', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/google/gemini-2.5-flash-lite', 'OpenRouter', 'google/gemini-2.5-flash-lite', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/google/gemini-pro-1.5', 'OpenRouter', 'google/gemini-pro-1.5', 'NaturalLanguageProcessing'),

    ('language/models/openrouter/x-ai/grok-4', 'OpenRouter', 'x-ai/grok-4', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/x-ai/grok-4-fast', 'OpenRouter', 'x-ai/grok-4-fast', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/x-ai/grok-3', 'OpenRouter', 'x-ai/grok-3', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/x-ai/grok-3-mini', 'OpenRouter', 'x-ai/grok-3-mini', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/x-ai/grok-2', 'OpenRouter', 'x-ai/grok-2', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/x-ai/grok-2-mini', 'OpenRouter', 'x-ai/grok-2-mini', 'NaturalLanguageProcessing'),

    ('language/models/openrouter/moonshotai/kimi-k2', 'OpenRouter', 'moonshotai/kimi-k2', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/anthropic/claude-3-opus', 'OpenRouter', 'anthropic/claude-3-opus', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/anthropic/claude-opus-4', 'OpenRouter', 'anthropic/claude-opus-4', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/anthropic/claude-opus-4.1', 'OpenRouter', 'anthropic/claude-opus-4.1', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/anthropic/claude-sonnet-4.5', 'OpenRouter', 'anthropic/claude-sonnet-4.5', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/anthropic/claude-sonnet-4', 'OpenRouter', 'anthropic/claude-sonnet-4', 'NaturalLanguageProcessing'),

    ('language/models/openrouter/anthropic/claude-3-sonnet', 'OpenRouter', 'anthropic/claude-3-sonnet', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/anthropic/claude-3.5-sonnet', 'OpenRouter', 'anthropic/claude-3.5-sonnet', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/anthropic/claude-3.7-sonnet', 'OpenRouter', 'anthropic/claude-3.7-sonnet', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/anthropic/claude-3.7-sonnet:thinking', 'OpenRouter', 'anthropic/claude-3.7-sonnet:thinking', 'NaturalLanguageProcessing'),



    ('language/models/openrouter/mistralai/mistral-nemo', 'OpenRouter', 'mistralai/mistral-nemo', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/mistralai/mistral-tiny', 'OpenRouter', 'mistralai/mistral-tiny', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/mistralai/mistral-small-3.2-24b-instruct', 'OpenRouter', 'mistralai/mistral-small-3.2-24b-instruct', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/mistralai/mistral-small', 'OpenRouter', 'mistralai/mistral-small', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/mistralai/mistral-medium-3.1', 'OpenRouter', 'mistralai/mistral-medium-3.1', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/mistralai/mistral-large', 'OpenRouter', 'mistralai/mistral-large', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/mistralai/mistral-large-2411', 'OpenRouter', 'mistralai/mistral-large-2411', 'NaturalLanguageProcessing'),

    ('language/models/openrouter/mistralai/magistral-small-2506', 'OpenRouter', 'mistralai/magistral-small-2506', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/mistralai/magistral-medium-2506', 'OpenRouter', 'mistralai/magistral-medium-2506', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/mistralai/magistral-medium-2506:thinking', 'OpenRouter', 'mistralai/magistral-medium-2506:thinking', 'NaturalLanguageProcessing'),


    ('language/models/openrouter/deepseek/deepseek-r1', 'OpenRouter', 'deepseek/deepseek-r1', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/deepseek/deepseek-r1-distill-llama-70b', 'OpenRouter', 'deepseek/deepseek-r1-distill-llama-70b', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/mdeepseek/deepseek-r1-0528-qwen3-8b', 'OpenRouter', 'deepseek/deepseek-r1-0528-qwen3-8b', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/deepseek/deepseek-r1-distill-qwen-32b', 'OpenRouter', 'deepseek/deepseek-r1-distill-qwen-32b', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/deepseek/deepseek-chat-v3.1', 'OpenRouter', 'deepseek/deepseek-chat-v3.1', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/deepseek/deepseek-v3.1-terminus', 'OpenRouter', 'deepseek/deepseek-v3.1-terminus', 'NaturalLanguageProcessing'),

    ('language/models/openrouter/meta-llama/llama-4-scout', 'OpenRouter', 'meta-llama/llama-4-scout', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/meta-llama/llama-4-maverick', 'OpenRouter', 'meta-llama/llama-4-maverick', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/meta-llama/llama-3.1-405b-instruct', 'OpenRouter', 'meta-llama/llama-3.1-405b-instruct', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/nvidia/llama-3.3-nemotron-super-49b-v1', 'OpenRouter', 'nvidia/llama-3.3-nemotron-super-49b-v1', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/meta-llama/codellama-34b-instruct', 'OpenRouter', 'meta-llama/codellama-34b-instruct', 'NaturalLanguageProcessing'),
    ('language/models/openrouter/meta-llama/llama-guard-4-12b', 'OpenRouter', 'meta-llama/llama-guard-4-12b', 'NaturalLanguageProcessing'),

-- others
    ('language/models/llama/llama3.1-8b', 'LLama', 'llama3.1-8b', 'NaturalLanguageProcessing'),
    ('language/models/llama/llama3.1-705b', 'LLama', 'llama3.1-70b', 'NaturalLanguageProcessing'),
    ('language/models/llama/llama3.1-405b', 'LLama', 'llama3.1-405b', 'NaturalLanguageProcessing'),
    ('language/models/google/gemini-1.5-flash', 'Google', 'gemini-1.5-flash', 'NaturalLanguageProcessing'),
    ('language/models/google/gemini-1.5-pro-001', 'Google', 'gemini-1.5-pro-001', 'NaturalLanguageProcessing'),

-- anthropic
    ('language/models/anthropic/claude-2.0', 'Anthropic', 'claude-2', 'NaturalLanguageProcessing'),
    ('language/models/anthropic/claude-2.1', 'Anthropic', 'claude-2.1', 'NaturalLanguageProcessing'),

    ('language/models/anthropic/claude-3-opus-latest', 'Anthropic', 'claude-3-opus-latest', 'NaturalLanguageProcessing'),
    ('language/models/anthropic/claude-3-opus-20240229', 'Anthropic', 'claude-3-opus-20240229', 'NaturalLanguageProcessing'),
    ('language/models/anthropic/claude-4.0-opus-latest', 'Anthropic', 'claude-opus-4-0', 'NaturalLanguageProcessing'),
    ('language/models/anthropic/claude-4.1-opus-latest', 'Anthropic', 'claude-opus-4-1', 'NaturalLanguageProcessing'),

    ('language/models/anthropic/claude-3-5-sonnet-latest', 'Anthropic', 'claude-3-5-sonnet-latest', 'NaturalLanguageProcessing'),
    ('language/models/anthropic/claude-3-5-sonnet-20240620', 'Anthropic', 'claude-3-5-sonnet-20240620', 'NaturalLanguageProcessing'),
    ('language/models/anthropic/claude-3-5-sonnet-20241022', 'Anthropic', 'claude-3-5-sonnet-20241022', 'NaturalLanguageProcessing'),
    ('language/models/anthropic/claude-3-7-sonnet-latest', 'Anthropic', 'claude-3-7-sonnet-latest', 'NaturalLanguageProcessing'),
    ('language/models/anthropic/claude-4.0-sonnet-latest', 'Anthropic', 'claude-sonnet-4-0', 'NaturalLanguageProcessing'),

    ('language/models/anthropic/claude-3-5-haiku-latest', 'Anthropic', 'claude-3-5-haiku-latest', 'NaturalLanguageProcessing'),
    ('language/models/anthropic/claude-3-5-haiku-20241022', 'Anthropic', 'claude-3-5-haiku-20241022', 'NaturalLanguageProcessing'),

    -- mixers
    ('data/transformers/mixer/state-online-join-1.0', 'State Online Join', 'state-online-join-1.0', 'DataTransformation'),
    ('data/transformers/mixer/state-online-merge-1.0', 'State Online Merge', 'state-online-merge-1.0', 'DataTransformation'),
    ('data/transformers/mixer/state-online-cross-join-1.0', 'State Online Cross Join', 'state-online-cross-join-1.0', 'DataTransformation'),
    ('data/transformers/mixer/state-tables-1.0', 'State Tables', 'state-tables-1.0', 'DataTransformation'),
    ('data/transformers/sampler/state-sample-multiplier-1.0', 'State Sample Multiplier', 'state-sample-multiplier-1.0', 'DataTransformation'),

    -- data source
    ('data/source/sql-1.0', 'SQL', 'sql-1.0', 'DatabaseProcessing'),

    -- code executors
    ('code/executor/python/python-executor-1.0', 'Python Executor', 'python-executor-1.0', 'CodeProcessing'),
    ('code/executor/mako/mako-executor-1.0', 'Mako Executor', 'mako-executor-1.0', 'CodeProcessing'),

    --- user interactions
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

alter table processor add column properties jsonb null;
alter table processor add column name varchar(255) null;
alter table processor add column created_date timestamp not null default current_timestamp;
alter table processor add column updated_date timestamp null default null;

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

--------------------------------------------------
-- USAGE VIEW FOR USAGE TABLE (extracts year, month, day, hour, minute, second from transaction_time)
--------------------------------------------------

-- ===========================
-- CLEANUP OLD DEFINITIONS
-- ===========================

-- Drop old triggers, functions, and table
DROP TRIGGER IF EXISTS trg_usage_rollup_ins ON usage;
DROP TRIGGER IF EXISTS trg_usage_rollup_upd ON usage;
DROP TRIGGER IF EXISTS trg_usage_rollup_del ON usage;

DROP FUNCTION IF EXISTS usage_rollup_trg() CASCADE;
DROP FUNCTION IF EXISTS _usage_rollup_apply(
    timestamptz, varchar, varchar, varchar, varchar,
    usage_unit_type, usage_unit_subtype, integer
) CASCADE;

DROP TABLE IF EXISTS usage_minute_rollup CASCADE;

-- ===========================
-- RECREATE FRESH DEFINITIONS
-- ===========================
CREATE TABLE usage_minute_rollup (
    bucket_utc     timestamptz       NOT NULL,
    user_id        varchar(36)       NOT NULL,
    project_id     varchar(36)       NOT NULL,
    resource_id    varchar(255)      NOT NULL,
    resource_type  varchar(255)      NOT NULL,
    unit_type      usage_unit_type   NOT NULL,
    unit_subtype   usage_unit_subtype NOT NULL,
    unit_count     integer           NOT NULL DEFAULT 0,
    PRIMARY KEY (bucket_utc, user_id, project_id, resource_id, resource_type, unit_type, unit_subtype)
);

CREATE INDEX usage_minute_rollup_proj_time ON usage_minute_rollup (project_id, bucket_utc);
CREATE INDEX usage_minute_rollup_user_time ON usage_minute_rollup (user_id, bucket_utc);

CREATE OR REPLACE FUNCTION _usage_rollup_apply(
    p_bucket     timestamptz,
    p_user       varchar(36),
    p_proj       varchar(36),
    p_res        varchar(255),
    p_rtype      varchar(255),
    p_utype      usage_unit_type,
    p_usubtype   usage_unit_subtype,
    p_delta      integer
) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO usage_minute_rollup
        (bucket_utc, user_id, project_id, resource_id,
         resource_type, unit_type, unit_subtype, unit_count)
    VALUES
        (p_bucket, p_user, p_proj, p_res,
         p_rtype, p_utype, p_usubtype, p_delta)
    ON CONFLICT (bucket_utc, user_id, project_id, resource_id, resource_type, unit_type, unit_subtype)
    DO UPDATE SET unit_count = usage_minute_rollup.unit_count + EXCLUDED.unit_count;
END$$;


CREATE OR REPLACE FUNCTION usage_rollup_trg()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    v_old integer := 0;
    v_new integer := 0;
    v_delta integer := 0;
    v_bucket timestamptz;
    v_user varchar(36);
BEGIN
    IF TG_OP = 'INSERT' THEN
        v_new := COALESCE(NEW.unit_count, 0);
        v_delta := v_new;
        v_bucket := date_trunc('minute', NEW.transaction_time AT TIME ZONE 'UTC');
        SELECT up.user_id INTO v_user FROM user_project up WHERE up.project_id = NEW.project_id;
        PERFORM _usage_rollup_apply(
            v_bucket, v_user, NEW.project_id, NEW.resource_id,
            NEW.resource_type, NEW.unit_type, NEW.unit_subtype, v_delta);
        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        v_old := COALESCE(OLD.unit_count, 0);
        v_new := COALESCE(NEW.unit_count, 0);

        IF date_trunc('minute', OLD.transaction_time AT TIME ZONE 'UTC')
             <> date_trunc('minute', NEW.transaction_time AT TIME ZONE 'UTC')
           OR OLD.project_id     <> NEW.project_id
           OR OLD.resource_id    <> NEW.resource_id
           OR OLD.resource_type  <> NEW.resource_type
           OR OLD.unit_type      <> NEW.unit_type
           OR OLD.unit_subtype   <> NEW.unit_subtype THEN

            v_bucket := date_trunc('minute', OLD.transaction_time AT TIME ZONE 'UTC');
            SELECT up.user_id INTO v_user FROM user_project up WHERE up.project_id = OLD.project_id;
            PERFORM _usage_rollup_apply(
                v_bucket, v_user, OLD.project_id, OLD.resource_id,
                OLD.resource_type, OLD.unit_type, OLD.unit_subtype, -v_old);

            v_bucket := date_trunc('minute', NEW.transaction_time AT TIME ZONE 'UTC');
            SELECT up.user_id INTO v_user FROM user_project up WHERE up.project_id = NEW.project_id;
            PERFORM _usage_rollup_apply(
                v_bucket, v_user, NEW.project_id, NEW.resource_id,
                NEW.resource_type, NEW.unit_type, NEW.unit_subtype, v_new);
        ELSE
            v_delta := v_new - v_old;
            v_bucket := date_trunc('minute', NEW.transaction_time AT TIME ZONE 'UTC');
            SELECT up.user_id INTO v_user FROM user_project up WHERE up.project_id = NEW.project_id;
            PERFORM _usage_rollup_apply(
                v_bucket, v_user, NEW.project_id, NEW.resource_id,
                NEW.resource_type, NEW.unit_type, NEW.unit_subtype, v_delta);
        END IF;
        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        v_old := COALESCE(OLD.unit_count, 0);
        v_bucket := date_trunc('minute', OLD.transaction_time AT TIME ZONE 'UTC');
        SELECT up.user_id INTO v_user FROM user_project up WHERE up.project_id = OLD.project_id;
        PERFORM _usage_rollup_apply(
            v_bucket, v_user, OLD.project_id, OLD.resource_id,
            OLD.resource_type, OLD.unit_type, OLD.unit_subtype, -v_old);
        RETURN OLD;
    END IF;
END$$;

CREATE TRIGGER trg_usage_rollup_ins AFTER INSERT ON usage FOR EACH ROW EXECUTE FUNCTION usage_rollup_trg();
CREATE TRIGGER trg_usage_rollup_upd AFTER UPDATE ON usage FOR EACH ROW EXECUTE FUNCTION usage_rollup_trg();
CREATE TRIGGER trg_usage_rollup_del AFTER DELETE ON usage FOR EACH ROW EXECUTE FUNCTION usage_rollup_trg();

CREATE INDEX IF NOT EXISTS usage_proj_time_idx ON usage (project_id, transaction_time);
CREATE INDEX IF NOT EXISTS usage_minute_rollup_user_idx ON usage_minute_rollup (user_id);
CREATE INDEX IF NOT EXISTS usage_minute_rollup_proj_idx ON usage_minute_rollup (project_id);
CREATE INDEX IF NOT EXISTS usage_minute_rollup_user_idx ON usage_minute_rollup (user_id);

-- (optional) Backfill existing usage data into usage_minute_rollup
-- BEGIN;
-- WITH src AS (
--   SELECT
--     date_trunc('minute', u.transaction_time AT TIME ZONE 'UTC') AS bucket_utc,
--     up.user_id,
--     u.project_id,
--     u.resource_id,
--     u.resource_type,
--     u.unit_type,
--     u.unit_subtype,
--     SUM(u.unit_count)::int AS unit_count
-- --   count(up.user_id) as cnt
--   FROM usage u
--   -- if user_project can have duplicate rows, DISTINCT it:
--   JOIN (SELECT DISTINCT project_id, user_id FROM user_project) up
--     ON up.project_id = u.project_id
--   /* optional time window
--   WHERE u.transaction_time >= :from_ts
--     AND u.transaction_time <  :to_ts
--   */
--   GROUP BY 1,2,3,4,5,6,7
-- )
-- INSERT INTO usage_minute_rollup (
--   bucket_utc, user_id, project_id, resource_id, resource_type, unit_type, unit_subtype, unit_count
-- )
-- SELECT * FROM src
-- ON CONFLICT (bucket_utc, user_id, project_id, resource_id, resource_type, unit_type, unit_subtype)
-- DO UPDATE SET unit_count = EXCLUDED.unit_count;
-- COMMIT;

-- Replace old view
DROP VIEW IF EXISTS usage_v CASCADE;

CREATE VIEW usage_v
  (year, month, day, hour, minute, second,
   user_id, project_id, resource_id, resource_type, unit_type, unit_subtype, unit_count) AS
SELECT
  EXTRACT(YEAR   FROM (bucket_utc AT TIME ZONE 'UTC'))    AS year,
  EXTRACT(MONTH  FROM (bucket_utc AT TIME ZONE 'UTC'))    AS month,
  EXTRACT(DAY    FROM (bucket_utc AT TIME ZONE 'UTC'))    AS day,
  EXTRACT(HOUR   FROM (bucket_utc AT TIME ZONE 'UTC'))    AS hour,
  EXTRACT(MINUTE FROM (bucket_utc AT TIME ZONE 'UTC'))    AS minute,
  EXTRACT(SECOND FROM (bucket_utc AT TIME ZONE 'UTC'))    AS second,  -- always 0
  user_id,
  project_id,
  resource_id,
  resource_type,
  unit_type,
  unit_subtype,
  unit_count
FROM usage_minute_rollup;

-- =========================
-- 1) Calendar-style daily tokens (per resource)
-- =========================
DROP VIEW IF EXISTS usage_report_calendar_v CASCADE;
CREATE OR REPLACE VIEW usage_report_calendar_v AS
SELECT
  user_id,
  project_id,
  EXTRACT(YEAR  FROM (bucket_utc AT TIME ZONE 'UTC'))::int  AS year,
  EXTRACT(MONTH FROM (bucket_utc AT TIME ZONE 'UTC'))::int  AS month,
  EXTRACT(DAY   FROM (bucket_utc AT TIME ZONE 'UTC'))::int  AS day,
  resource_type,
  SUM(unit_count)::bigint                                   AS tokens
FROM usage_minute_rollup
GROUP BY user_id, project_id, year, month, day, resource_type;

-- =========================
-- 2) Daily aggregates with stats (unchanged source, just explicit)
-- =========================
DROP VIEW IF EXISTS usage_report_daily_v CASCADE;
CREATE OR REPLACE VIEW usage_report_daily_v AS
SELECT
  date_trunc('day', bucket_utc)         AS daily_utc,
  user_id,
  project_id,
  resource_type,
  unit_type,
  unit_subtype,
  SUM(unit_count)::bigint               AS sum_units,
  ROUND(AVG(unit_count)::numeric, 2)    AS avg_units,
  MIN(unit_count)                       AS min_units,
  MAX(unit_count)                       AS max_units
FROM usage_minute_rollup
GROUP BY 1,2,3,4,5,6;


-- =========================
-- 3) Daily aggregates + pricing
-- =========================
DROP VIEW IF EXISTS usage_report_daily_pricing_v CASCADE;
CREATE OR REPLACE VIEW usage_report_daily_pricing_v AS
WITH pricing AS (
  SELECT
    u.*,
    CASE
      WHEN u.unit_subtype = 'OUTPUT' THEN p.output_price_per_1k_tokens
      WHEN u.unit_subtype = 'INPUT'  THEN p.input_price_per_1k_tokens
      ELSE NULL
    END AS price_per_unit
  FROM usage_report_daily_v u
  LEFT JOIN processor_provider_pricing p
    ON u.resource_type = p.processor_provider_id
)
SELECT
  pricing.*,
  (pricing.price_per_unit * pricing.sum_units) / 1000.0 AS cost
FROM pricing;



--
-- CREATE OR REPLACE VIEW usage_v
-- AS
-- SELECT
--     extract(year from transaction_time) as year,
--     extract(month from transaction_time) as month,
--     extract(day from transaction_time) as day,
--     extract(hour from transaction_time) as hour,
--     extract(minute from transaction_time) as minute,
--     extract(second from transaction_time) as second,
--     up.user_id,
--     u.project_id,
--     u.resource_id,
--     u.resource_type,
--     u.unit_type,
--     COALESCE(u.unit_count, 0) as unit_count
--  FROM usage u
-- RIGHT OUTER JOIN user_project up
--   ON up.project_id = u.project_id;


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

------------------------------------------------------------------
-- session and session messages for tracking user interactions
------------------------------------------------------------------
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
    created_date TIMESTAMP DEFAULT NOW(),
    updated_date TIMESTAMP DEFAULT NOW()
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
    created_date TIMESTAMP DEFAULT NOW(),
    updated_date TIMESTAMP DEFAULT NOW(),
    deleted_date TIMESTAMP -- Optional: soft delete support
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

-- CREATE UNIQUE INDEX
CREATE EXTENSION IF NOT EXISTS pg_trgm;

create unique index if not exists state_column_data_comp_ux
    on public.state_column_data (column_id, data_index);
create index state_column_data_column_idx
    on public.state_column_data (column_id);
create index state_column_data_trgm_idx
    on public.state_column_data using gin (data_value public.gin_trgm_ops);


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
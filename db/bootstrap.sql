drop table if exists user_profile cascade;
create table user_profile (
    user_id varchar(36) not null primary key
);

drop table if exists user_project cascade;
create table user_project (
  project_id varchar(36) not null primary key,
  project_name varchar(255) not null,
  user_id varchar(36) not null references user_profile (user_id),
  unique (user_id, project_name)
);

-- select gen_random_uuid();

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

create unique index state_column_unique_key on state_column (id, state_id);

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

drop table if exists model cascade;
create table model (
    id serial primary key,
    provider_name varchar(255) not null,
    model_name varchar(255) not null,
    unique (provider_name, model_name)
);

insert into model (provider_name, model_name) values ('OpenAI', 'gpt-4-1106-preview');
insert into model (provider_name, model_name) values ('Anthropic', 'claude-2.0');
insert into model (provider_name, model_name) values ('Anthropic', 'claude-2.1');
commit;

drop table if exists processor_class cascade;
create table processor_class (
    class_name varchar(32) not null primary key
);

INSERT INTO processor_class VALUES ('CodeProcessing');
INSERT INTO processor_class VALUES ('NaturalLanguageProcessing');
INSERT INTO processor_class VALUES ('ImageProcessing');
INSERT INTO processor_class VALUES ('DataTransformation');
INSERT INTO processor_class VALUES ('TextProcessing');
INSERT INTO processor_class VALUES ('VideoProcessing');
INSERT INTO processor_class VALUES ('AudioProcessing');
INSERT INTO processor_class VALUES ('DataAnalysis');
INSERT INTO processor_class VALUES ('SignalProcessing');
INSERT INTO processor_class VALUES ('MachineLearning');

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
('language/models/openai/gpt-4o-2024-05-13', 'OpenAI', 'gpt-4o-2024-05-13', 'NaturalLanguageProcessing'),
('language/models/openai/o1-preview', 'OpenAI', 'o1-preview', 'NaturalLanguageProcessing'),
('image/models/openai/dall-e-2', 'OpenAI', 'dall-e-2', 'ImageProcessing'),
('image/models/openai/dall-e-3', 'OpenAI', 'dall-e-3', 'ImageProcessing'),
('language/models/llama/llama3.1-8b', 'LLama', 'llama3.1-8b', 'NaturalLanguageProcessing'),
('language/models/llama/llama3.1-705b', 'LLama', 'llama3.1-70b', 'NaturalLanguageProcessing'),
('language/models/llama/llama3.1-405b', 'LLama', 'llama3.1-405b', 'NaturalLanguageProcessing'),
('language/models/google/gemini-1.5-flash', 'Google', 'gemini-1.5-flash', 'NaturalLanguageProcessing'),
('language/models/google/gemini-1.5-pro-001', 'Google', 'gemini-1.5-pro-001', 'NaturalLanguageProcessing'),
('language/models/anthropic/claude-2.0', 'Anthropic', 'claude-2', 'NaturalLanguageProcessing'),
('language/models/anthropic/claude-2.0', 'Anthropic', 'claude-2', 'NaturalLanguageProcessing'),
('language/models/anthropic/claude-2.0', 'Anthropic', 'claude-2', 'NaturalLanguageProcessing'),
('language/models/anthropic/claude-2.1', 'Anthropic', 'claude-2.1', 'NaturalLanguageProcessing'),
('language/models/anthropic/claude-3-opus-20240229', 'Anthropic', 'claude-3-opus-20240229', 'NaturalLanguageProcessing'),
('language/models/anthropic/claude-3-5-sonnet-20240620', 'Anthropic', 'claude-3-5-sonnet-20240620', 'NaturalLanguageProcessing'),
('data/transformers/mixer/state-coalescer-1.0', 'State Coalescer', 'state-coalescer-1.0', 'DataTransformation'),
('data/transformers/mixer/state-composite-1.0', 'State Coalescer', 'state-composite-1.0', 'DataTransformation'),
('data/transformers/sampler/state-ensembler-1.0', 'State Ensembler', 'state-ensembler-1.0', 'DataTransformation'),
('code/executor/python/python-executor-1.0', 'Python Executor', 'python-executor-1.0', 'CodeProcessing')
ON CONFLICT DO NOTHING;

drop type if exists processor_status cascade;
create type processor_status AS ENUM (
       'CREATED', 'ROUTE', 'ROUTED',
       'QUEUED', 'RUNNING', 'COMPLETED',
       'TERMINATE', 'STOPPED', 'FAILED'
);

drop table if exists processor cascade;
create table processor (
    id varchar(36) not null primary key,
    provider_id varchar(255) not null references processor_provider (id),
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
    id serial primary key,
    transaction_time timestamp,
    project_id varchar(36) not null references user_project (project_id),

    -- resource information (e.g. a processor or a datasource
    resource_id varchar(255) not null,      -- a processor id, or a datasource id, or a compute node id, or something else that we want to bill on
    resource_type varchar(255) not null,    -- the type of resource this is, generally a processor or a datasource, or storage, etc.
    unit_type        usage_unit_type            not null,
    unit_subtype    usage_unit_subtype            not null,
    unit_count       int          default 0 not null,
    metadata    text null
);

create index usage_project_idx on usage (project_id);
create index user_project_user_id_idx on user_project (user_id)



---

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

-- auto-generated definition
drop type if exists user_session_access_level cascade;
create type user_session_access_level as enum ('default', 'admin');

drop table if exists user_session_access cascade;
create table user_session_access (
    user_id varchar(36) not null references user_profile (user_id),
    session_id varchar(36) not null references session (session_id),
    access_level user_session_access_level not null default 'default',
    access_date timestamp not null
);


alter table user_profile add column email varchar(255) null;
alter table user_profile add column name varchar(255) null;
alter table user_profile add column created_date timestamp not null default current_timestamp;
alter table user_project add column created_date timestamp not null default current_timestamp;



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
create index state_column_key_definition_state_idx on state_column_key_definition (state_id);
create index state_column_data_mapping_state_idx on state_column_data_mapping (state_id);
create index monitor_log_event_user_id on monitor_log_event (user_id);
create index monitor_log_event_project_id on monitor_log_event (project_id);
create index monitor_log_event_user_and_project_id on monitor_log_event (user_id, project_id);

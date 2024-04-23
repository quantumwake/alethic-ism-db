drop table if exists user_profile cascade;
create table user_profile (
    user_id varchar(36) not null primary key
);

insert into user_profile (user_id) values ('a57263b6-8869-406b-91e9-bdfb8dfd6785');

drop table if exists user_project cascade;
create table user_project (
  project_id varchar(36) not null primary key,
  project_name varchar(255) not null,
  user_id varchar(36) not null references user_profile (user_id)
);

-- select gen_random_uuid();

drop table if exists workflow_node cascade;
create table workflow_node (
    node_id varchar(255) not null primary key,
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
    source_node_id varchar(255) not null references workflow_node (node_id),
    target_node_id varchar(255) not null references  workflow_node (node_id),
    source_handle varchar(255) null,
    target_handle varchar(255) null,
    animated bool not null default true,
    edge_label varchar(255) null,
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
    id varchar(255) not null primary key,
    name varchar(255) not null,
    version varchar(255) not null,
    count int not null default 0,
    state_type varchar(255) not null default 'StateConfig'
);

drop table if exists state_config;
create table state_config (
    state_id varchar(255) not null,
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
    state_id varchar(255) not null references state(id),
    name varchar(255) not null,
    data_type varchar(64) default 'str',
    "null" boolean default true,
    min_length int default 0,
    max_length int default 255,
    dimensions int default 384,
    value varchar(255),
    source_column_name varchar(255)
);

drop table if exists state_column_data;
create table state_column_data
(
    column_id bigint not null references state_column (id),
    data_index bigint not null,
    data_value text
);

drop table if exists state_column_data_mapping;
create table state_column_data_mapping (
    state_id varchar(255) not null,
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

drop table processor_class cascade;
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
('language/models/openai/gpt-4-1106-preview', 'OpenAI', 'gpt-4-1106-preview', 'NaturalLanguageProcessing'),
('language/models/anthropic/claude-2.0', 'Anthropic', 'claude-2', 'NaturalLanguageProcessing'),
('language/models/anthropic/claude-2.1', 'Anthropic', 'claude-2.1', 'NaturalLanguageProcessing'),
('language/models/anthropic/claude-3.0', 'Anthropic', 'claude-3', 'NaturalLanguageProcessing'),
('data/transformer/alethic/state-fuser-1.0', 'Alethic', 'state-fuser-1.0', 'DataTransformation'),
('data/transformer/alethic/state-monte-carlo-1.0', 'Alethic', 'state-monte-carlo-1.0', 'DataTransformation')
ON CONFLICT DO NOTHING;

drop type if exists processor_status cascade;
create type processor_status AS ENUM (
       'CREATED', 'QUEUED',
       'RUNNING', 'TERMINATED',
       'STOPPED', 'COMPLETED',
       'FAILED'
);

drop table if exists processor cascade;
create table processor (
    id varchar(36) not null primary key,
    provider_id varchar(36) not null references processor_provider (id),
    project_id varchar(36) not null references user_project (project_id),
    status processor_status not null
);

drop type if exists processor_state_direction cascade;
create type processor_state_direction AS ENUM (
       'INPUT', 'OUTPUT'
);

drop table if exists processor_state;
create table processor_state (
    processor_id varchar(36) not null primary key,
    state_id varchar(36) not null references state (id),
    direction processor_state_direction not null
);

commit;
drop table if exists template;
create table template (
    template_path varchar(255) not null primary key,
    template_content text not null,
    template_type varchar(255) default 'user_template'
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
    state_id varchar(255) not null references state (id),
    name varchar(255) not null,
    alias varchar(255),
    required bool default false,
    definition_type varchar(255) not null,
    primary key (state_id, name, definition_type)
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

drop table if exists processor cascade;
create table processor (
    id varchar(255) not null primary key,
    type varchar(255) not null,
    unique(id, type)
);

insert into processor (id, type) values ('language/models/openai/gpt-4-1106-preview', 'OpenAIQuestionAnswerProcessor');
insert into processor (id, type) values ('language/models/anthropic/claude-2.0', 'AnthropicQuestionAnswerProcessor');
insert into processor (id, type) values ('language/models/anthropic/claude-2.1', 'AnthropicQuestionAnswerProcessor');
commit;

drop table if exists processor_state;
create type processor_status AS ENUM (
       'CREATED', 'QUEUED',
       'RUNNING', 'TERMINATED',
       'STOPPED', 'COMPLETED',
       'FAILED'
);



drop table if exists processor_state;
create table processor_state (
    processor_id varchar(255) not null references processor (id),
    input_state_id  varchar(255) not null references state (id),
    output_state_id varchar(255) not null references state (id),
    status processor_status not null default 'CREATED',
    primary key (processor_id, input_state_id, output_state_id)
);


------------------
--- VIEWS
------------------
drop view if exists state_column_data_view;
create or replace view state_column_data_view
as
select state_id,
       c.id as column_id,
       c.name,
    case
        when d.data_value is null then c.value
        else d.data_value
    end as data_value,
    d.data_index
from state_column_data d
 inner join state_column c
    on c.id = d.column_id;


create or replace view state_column_state_grouped_view
as select state_id, name, count(data_index) as cnt
     from state_column_data_view
    group by state_id, name
    order by state_id, name;


create index state_column_data_mapping__state_key_idx on state_column_data_mapping (state_key);
create index state_column_data_mapping__state_id_idx on state_column_data_mapping (state_id);
create index state_column_data_mapping__data_index_idx on state_column_data_mapping (data_index);
create index state_column_data__index_idx on state_column_data (data_index);
create index state_column_data__column_id_idx on state_column_data (column_id);
create index state_column_data__composite_id_idx on state_column_data (data_index, column_id);
create index state_config__state_id_idx on state_config (state_id);
create index state_column_key_definition__state_id_idx on state_column_key_definition (state_id);
create index state_column__state_id_idx on state_column (state_id);


drop table if exists state cascade;

drop table if exists template;

create table template (
    template_path varchar(255) not null primary key,
    template_content text not null,
    template_type varchar(255) default 'user_template'
);

select * from template;

-- select * from state where id = 'ea6ee46f537da30c47443138b970eaba40f7628a0bc669f29cc43c3c6c4efce3';
-- select * from state_column where state_id = 'ea6ee46f537da30c47443138b970eaba40f7628a0bc669f29cc43c3c6c4efce3';

create table state
(
    id varchar(255) not null primary key,
    name varchar(255) not null,
    version varchar(255) not null,
    count int not null default 0,
    state_type varchar(255) not null default 'StateConfig'
);

select * from state;

/*
select c.name, c.value, d.data_index, d.data_value from state_column_data d
  inner join state_column c
    on c.id = d.column_id
where state_id = '271bb8e81c7b6826a6efce152488bec7bc3bf4a41f519f7ea56b7c71bea13744'
order by c.name, d.data_index;
*/

drop table if exists state_config;

create table state_config (
    state_id varchar(255) not null,
    attribute varchar(255) not null,
    data text,
    primary key (state_id, attribute)
);

select * from state_config;

---
drop table if exists state_column_key_definition;

create table state_column_key_definition(
    state_id varchar(255) not null references state (id),
    name varchar(255) not null,
    alias varchar(255),
    required bool default false,
    definition_type varchar(255) not null,
    primary key (state_id, name, definition_type)
);

select * from state_column_key_definition;

update state_column_key_definition set definition_type = 'query_state_inheritance' where definition_type = 'include_extra_from_input_definition';
commit;

---

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

select * from state_column;

drop table if exists state_column_data;
create table state_column_data
(
    column_id bigint not null references state_column (id),
    data_index bigint not null,
    data_value text
);

select * from state_column_data;

create index state_column_data__index_idx on state_column_data (data_index);

drop table if exists state_column_data_mapping;

create table state_column_data_mapping (
    state_id varchar(255) not null,
    state_key varchar(255) not null,
    data_index bigint not null,
    primary key (state_id, state_key, data_index)
);

select * from state_column_data_mapping;

select count(*) from state_column_data_mapping;

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

select * from model;

drop table if exists processor cascade;
create table processor (
    id serial not null primary key,
    name varchar(255) not null,
    type varchar(255) not null,
    model_id bigint not null references model(id),
    unique (name, type, model_id)
);

insert into processor (name, type, model_id) values ('AnthropicQuestionAnswerProcessor', 'Language', 1);
insert into processor (name, type, model_id) values ('OpenAIQuestionAnswerProcessor', 'Language', 2);
insert into processor (name, type, model_id) values ('OpenAIQuestionAnswerProcessor', 'Language', 3);

drop table if exists processor_state;

create table processor_state (
    processor_id int not null references processor (id),
    input_state_id  varchar(255) not null references state (id),
    output_state_id varchar(255) not null references state (id),
    primary key (processor_id, input_state_id, output_state_id)
);

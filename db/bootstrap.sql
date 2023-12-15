drop table if exists state cascade;

drop table if exists template;

create table template (
    template_path varchar(255) not null primary key,
    template_content text not null,
    template_type varchar(255) default 'user_template'
);

select * from template;

create table state
(
    id varchar(255) not null primary key,
    name varchar(255) not null,
    version varchar(255) not null,
    count int not null default 0,
    state_type varchar(255) not null default 'StateConfig'
);

select * from state;

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

-- update state_column_key_definition set definition_type = 'primary_key' where definition_type = 'output_primary_key_definition';
-- commit;

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

drop table if exists processor cascade;

create table processor (
    id varchar(255) not null primary key,
    type varchar(255) not null
);

insert into processor (id, type) values ('AnthropicQuestionAnswerProcessor',
                                         'Language');

insert into processor (id, type) values ('OpenAIQuestionAnswerProcessor',
                                         'Language');

drop table if exists processor_state;
create table processor_state (
    processor_id varchar(255) not null references processor (id),
    input_state_id  varchar(255) not null references state (id),
    output_state_id varchar(255) not null references state (id),
    primary key (processor_id, input_state_id, output_state_id)
);


-- with x as (
--     select * from state_column where state_id = '222cab9859359ccd850c8bca7825c691183043df1a3fb15812d640a28d4ea0ab'
-- )
-- select * from state_column_data
--     where column_id in (select id from x);

create user ism_db_user;
create database ism_db;
alter user ism_db_user with encrypted password '<hello world>';
grant all privileges on database ism_db to ism_db_user;


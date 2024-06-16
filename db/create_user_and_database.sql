create user ism_db_user;
create database ism_db;
alter user ism_db_user with encrypted password '0aa0a535d1b592d1';
grant all privileges on database ism_db to ism_db_user;


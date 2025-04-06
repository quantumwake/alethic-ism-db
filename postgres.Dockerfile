FROM alpine:latest

# Install PostgreSQL client
RUN apk add --no-cache postgresql-client

WORKDIR /scripts

# Copy the bootstrap.sql script
COPY bootstrap.sql /scripts/bootstrap.sql
COPY entrypoint.sh /scripts/entrypoint.sh
#RUN chmod +x /scripts/entrypoint.sh

# Set execute permissions for the script
#RUN chmod +x /scripts/bootstrap.sql
#
## Create an entrypoint script that will connect to the database and run the bootstrap script

ENTRYPOINT ["/scripts/entrypoint.sh"]
FROM alpine:latest

# Install PostgreSQL client
RUN apk add --no-cache postgresql-client

WORKDIR /scripts

# Copy the bootstrap.sql script
COPY bootstrap.sql /scripts/bootstrap.sql
COPY entrypoint.sh /scripts/entrypoint.sh

ENTRYPOINT ["/scripts/entrypoint.sh"]
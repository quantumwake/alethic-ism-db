#!/bin/bash

image="quantumwake/alethic-ism-db:latest"
search_path=/app/conda/env/local_channel
search_pattern="alethic-ism-db-*-*_*.tar.bz2"

name=$(find "$image" "$search_path" -name "$search_pattern")
name=$(basename $name)

tar -zcvf /app/local_channel.tar.gz /app/conda/env/local_channel


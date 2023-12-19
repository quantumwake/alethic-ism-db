#!/bin/bash

image="quantumwake/alethic-ism-db:latest"
search_path=/app/conda/env/local_channel
search_pattern="alethic-ism-db-*-*_*.tar.bz2"

container_id=$(docker create quantumwake/alethic-ism-db:latest)
echo "Container ID: $container_id" # For debugging

docker images # Optional: For debugging, to list available images
file_path=$(docker run --rm --entrypoint find "$image" "$search_path" -name "$search_pattern")
file_name=$(basename $file_path)
echo "File name: $file_name located in docker image at $file_path" # For debugging

docker cp "$container_id:$file_path" $file_name 
echo "::set-output name=file_name::$file_name"


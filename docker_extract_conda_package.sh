#!/bin/bash

APP_NAME="alethic-ism-db"
DOCKER_NAMESPACE="krasaee"
GIT_COMMIT_ID=$(git rev-parse HEAD)
TAG="$DOCKER_NAMESPACE/$APP_NAME:$GIT_COMMIT_ID"

#image="quantumwake/alethic-ism-db:latest"
#container_id=$(docker create quantumwake/alethic-ism-db:latest)

container_id=`docker create $TAG`
echo "Container ID: $container_id from image $image" # For debugging
docker images # Optional: For debugging, to list available images

# extract the gzip package
file_name="local_channel.tar.gz"
echo "File name: $file_name located in docker image" # For debugging
docker cp "$container_id:/app/$file_name" $file_name

target_file_name=$(awk '
    /version:/ {version = $2; gsub(/"|,/, "", version)}
    /number:/ {build = $2; gsub(/"|,/, "", build)}
    END {printf("alethic-ism-db_%s_%s.tar.gz\n", version, build)}
' ./recipe/meta.yaml)

mv $file_name $target_file_name
file_name=$target_file_name

echo "final file_name: $file_name"
echo "::set-output name=file_name::$file_name"

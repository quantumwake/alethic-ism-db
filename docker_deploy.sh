#!/bin/bash

# Function to print usage
print_usage() {
  echo "Usage: $0 [-a app_name] [-n docker_namespace] [-t tag]"
  echo "  -a app_name           Application name (default: alethic-ism-core)"
  echo "  -n docker_namespace   Docker namespace (default: krasaee)"
  echo "  -t tag                Docker image tag"
}

# Default values
APP_NAME=$(pwd | sed -e 's/^.*\///g')
DOCKER_NAMESPACE="krasaee"
TAG=""

# Parse command line arguments
while getopts 'a:n:t:' flag; do
  case "${flag}" in
    a) APP_NAME="${OPTARG}" ;;
    n) DOCKER_NAMESPACE="${OPTARG}" ;;
    t) TAG="${OPTARG}" ;;
    *) print_usage
       exit 1 ;;
  esac
done

# If TAG is not provided, generate it using GIT_COMMIT_ID
if [ -z "$TAG" ]; then
  GIT_COMMIT_ID=$(git rev-parse HEAD)
  TAG="$DOCKER_NAMESPACE/$APP_NAME:$GIT_COMMIT_ID"
fi

# Cleanup data
find . -type f -name "$APP_NAME*.gz" -exec rm -f {} \+

# Create the Docker container
container_id=$(docker create "$TAG")
echo "Container ID: $container_id from image $TAG" # For debugging
docker images # Optional: For debugging, to list available images

# Extract the gzip package
file_name="local_channel.tar.gz"
echo "File name: $file_name located in docker image" # For debugging
docker cp "$container_id:/app/$file_name" "$file_name"

# Generate the target file name from meta.yaml
target_file_name=$(awk -v app_name="$APP_NAME" '
    /version:/ {version = $2; gsub(/"|,/, "", version)}
    /number:/ {build = $2; gsub(/"|,/, "", build)}
    END {printf("%s_%s_%s.tar.gz\n", app_name, version, build)}
' ./recipe/meta.yaml)

# Move and rename the file
mv "$file_name" "$target_file_name"
file_name="$target_file_name"

echo "Final file_name: $file_name"
echo "::set-output name=file_name::$file_name"


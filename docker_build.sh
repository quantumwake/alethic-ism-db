#!/bin/bash

print_usage() {
  echo "Usage: $0 [-t tag] [-a architecture]"
  echo "  -t tag             Docker image tag"
  echo "  -a platform        Target platform architecture (default: linux/amd64)"
}

# Check for ANACONDA_API_TOKEN
#if [ -z "$ANACONDA_API_TOKEN" ]; then
#    echo "Error: ANACONDA_API_TOKEN environment variable is not set"
#    exit 1
#fi

TAG=""
ARCH="linux/amd64"

while getopts 't:a:' flag; do
  case "${flag}" in
    t) TAG="${OPTARG}" ;;
    a) ARCH="${OPTARG}" ;;
    *) print_usage
       exit 1 ;;
  esac
done

# Validate TAG is provided
if [ -z "$TAG" ]; then
    echo "Error: -t tag is required"
    print_usage
    exit 1
fi

#  --build-arg ANACONDA_API_TOKEN=$ANACONDA_API_TOKEN \
#
#docker build \
#  --platform "$ARCH" -t "$TAG" \
#  --no-cache .


docker build --secret id=pypirc,src=/tmp/secrets/pypirc \
  --platform "$ARCH" -t "$TAG" .
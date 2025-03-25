#!/bin/bash

print_usage() {
  echo "Usage: $0 [-t tag] [-a architecture]"
  echo "  -t tag             Docker image tag"
  echo "  -a platform        Target platform architecture (default: linux/amd64)"
}

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

docker build --secret id=pypirc,src=/tmp/secrets/pypirc \
  --platform "$ARCH" -t "$TAG" .
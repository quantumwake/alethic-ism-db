#!/bin/bash

CONDA_PACKAGE_PATH_ISM_CORE="../alethic-ism-core"

# Function to print usage
print_usage() {
  echo "Usage: $0 [-t tag] [-a architecture]"
  echo "  -t tag             Docker image tag"
  echo "  -ismcore	     ISM Core Library Path"
  echo "  -p platform        Target platform architecture (default: linux/amd64)"
}

# Default values
TAG=""
ARCH="linux/amd64"

# Parse command line arguments
while getopts 't:a:' flag; do
  case "${flag}" in
    t) TAG="${OPTARG}" ;;
    a) ARCH="${OPTARG}" ;;
    ismcore) CONDA_PACKAGE_PATH_ISM_CORE="${OPTARG}" ;;
    *) print_usage
       exit 1 ;;
  esac
done

# Check if ARCH is set, if not default to linux/amd64
if [ -z "$ARCH" ]; then
  ARCH="linux/amd64"
  # TODO: Check operating system and set ARCH accordingly, e.g., ARCH="linux/arm64"
fi

CONDA_ISM_CORE_PATH=$(ls -ltr $CONDA_PACKAGE_PATH_ISM_CORE/alethic-ism-core*.tar.gz | awk '{print $9}' | tail -n 1)
CONDA_ISM_CORE_PATH=$(basename $CONDA_ISM_CORE_PATH)

## Display arguments
echo "Platform: $ARCH"
echo "Platform Docker Image Tag: $TAG"
echo "Conda ISM core library: $CONDA_ISM_CORE_PATH"

## Ensure ISM core library exists
if [ -z "${CONDA_ISM_CORE_PATH}" ];
then
  echp "Unable to build without alethic-ism-core package, no data found in path $CONDA_PACKAGE_PATH_ISM_CORE"
  exit;
fi

# Copy dependencies and build the ISM db library package
cp $CONDA_PACKAGE_PATH_ISM_CORE/$CONDA_ISM_CORE_PATH $CONDA_ISM_CORE_PATH

# Build the Docker image which creates the package
docker build --progress=plain \
  --platform "$ARCH" -t "$TAG" \
  --build-arg CONDA_ISM_CORE_PATH=$CONDA_ISM_CORE_PATH \
  --no-cache .


# Cleanup
find . -type f -name "$CONDA_ISM_CORE_PATH" -exec rm -f {} \+

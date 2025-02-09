#!/bin/bash

set -euo pipefail  # Enables strict error handling

ARTIFACT_DIR="/app"
CHANNEL_DIR="/app/conda/env/local_channel"
ARTIFACT_NAME="local_channel.tar.gz"
ARTIFACT_PATH="$ARTIFACT_DIR/$ARTIFACT_NAME"

echo "Starting the packaging process for the local conda channel..."

# Ensure the directory exists before proceeding
if [[ ! -d "$CHANNEL_DIR" ]]; then
    echo "Error: The directory '$CHANNEL_DIR' does not exist. Exiting."
    exit 1
fi

# Remove existing artifact if present
if [[ -f "$ARTIFACT_PATH" ]]; then
    echo "Removing existing artifact: $ARTIFACT_PATH"
    rm -f "$ARTIFACT_PATH"
fi

# Create the tarball with proper compression and error handling
echo "Creating tarball: $ARTIFACT_PATH"
if tar -zcvf "$ARTIFACT_PATH" -C "$CHANNEL_DIR" .; then
    echo "Packaging completed successfully."
else
    echo "Error: Failed to create tarball."
    exit 1
fi

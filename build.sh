#!/bin/bash

# Default values
META_YAML_PATH="./recipe"
LOCAL_CHANNEL_PATH=~/miniconda3/envs/local_channel
SKIP_PURGE=false
VERBOSE=false

# Parse optional arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --meta-yaml-path) META_YAML_PATH="$2"; shift ;;
        --local-channel-path) LOCAL_CHANNEL_PATH="$2"; shift ;;
        --skip-purge) SKIP_PURGE=true ;;
        --verbose) VERBOSE=true ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# Function to log messages if verbose mode is on
log() {
    if [ "$VERBOSE" = true ]; then
        echo "$@"
    fi
}

log "Using META_YAML_PATH: $META_YAML_PATH"
log "Using LOCAL_CHANNEL_PATH: $LOCAL_CHANNEL_PATH"

# Update build number
build_no=$(cat "$META_YAML_PATH/meta.yaml" | awk '/number: [0-9]+/ {printf("%s+1\n", $2)}')
build_no=$((build_no+1))
log "Updated build number to: $build_no"

sed -E "s/number: [0-9]+/number: $build_no/g" "$META_YAML_PATH/meta.yaml" > ./tmp_meta.yaml
mv ./tmp_meta.yaml "$META_YAML_PATH/meta.yaml"
grep "number: " "$META_YAML_PATH/meta.yaml"

# Purge and clean, unless skipped
if [ "$SKIP_PURGE" = false ]; then
    log "Purging and cleaning..."
    yes | conda build purge
    yes | conda clean --all
else
    log "Skipping purge and clean..."
fi

# Build to a local channel
conda build "$META_YAML_PATH" --output-folder "$LOCAL_CHANNEL_PATH"
conda index "$LOCAL_CHANNEL_PATH"

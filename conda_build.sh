#!/bin/bash
#set -euo pipefail

META_YAML_PATH="./recipe"
LOCAL_CHANNEL_PATH=~/miniconda3/envs/local_channel
SKIP_PURGE=false
VERBOSE=true
USE_BOA=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --meta-yaml-path) META_YAML_PATH="$2"; shift ;;
        --local-channel-path) LOCAL_CHANNEL_PATH="$2"; shift ;;
        --skip-purge) SKIP_PURGE=true ;;
        --use-boa) USE_BOA=true ;;
        --verbose) VERBOSE=true ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

log() {
    if [ "$VERBOSE" = true ]; then
        echo "$@"
    fi
}

log "Using META_YAML_PATH: $META_YAML_PATH"
log "Using LOCAL_CHANNEL_PATH: $LOCAL_CHANNEL_PATH"

if [ "$SKIP_PURGE" = false ]; then
    log "Purging and cleaning..."
    yes | conda build purge
    yes | conda clean --all
else
    log "Skipping purge and clean..."
fi

if [ "$USE_BOA" = true ]; then
    log "Using BOA (mamba) for faster builds"
    boa build "$META_YAML_PATH" --output-folder "$LOCAL_CHANNEL_PATH"
else
    log "Using Conda Build"
    conda build "$META_YAML_PATH" --output-folder "$LOCAL_CHANNEL_PATH" --dirty
fi

conda index "$LOCAL_CHANNEL_PATH"

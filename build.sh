#!/bin/bash

META_YAML_PATH="./recipe"
LOCAL_CHANNEL_PATH="/app/conda/env/local_channel"

build_no=$(cat ./recipe/meta.yaml | awk '/number: [0-9]+/ {printf("%s+1\n", $2)}')
build_no=$((build_no+1))

# update the build number
cat ./recipe/meta.yaml | sed -E 's/number: [0-9]+/number: '''$build_no'''/g' > ./tmp_meta.yaml
mv ./tmp_meta.yaml ./recipe/meta.yaml
cat ./recipe/meta.yaml | grep "number: "

# purge the repo if anything and build it to a local channel
yes | conda build purge
yes | conda clean --all
conda build $META_YAML_PATH --output-folder $LOCAL_CHANNEL_PATH
conda index $LOCAL_CHANNEL_PATH

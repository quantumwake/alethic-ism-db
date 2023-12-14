#!/bin/bash

i=$(cat ./recipe/meta.yaml | awk '/number: [0-9]+/ {printf("%s+1\n", $2)}' | bc)
cat ./recipe/meta.yaml | sed -E 's/number: [0-9]+/number: '''$i'''/g' > ./tmp_meta.yaml
mv ./tmp_meta.yaml ./recipe/meta.yaml

cat meta.yaml | grep "number: "

#conda install -c defaults conda-build

META_YAML_PATH="./recipe"

yes | conda build purge
yes | conda clean --all
conda build $META_YAML_PATH --output-folder ~/miniconda3/envs/local_channel
conda index ~/miniconda3/envs/local_channel

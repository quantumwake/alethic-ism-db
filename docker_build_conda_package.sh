#!/bin/bash

conda_ism_core_path=$(find . -type f -name "alethic-ism-*.tar.bz2")

#docker build --platform linux/amd64 -t quantumwake/alethic-ism-db:latest \
# --build-arg GITHUB_REPO_URL=https://github.com/quantumwake/alethic-ism-db.git --no-cahce .

docker build -t quantumwake/alethic-ism-db:latest \
 --build-arg CONDA_ISM_CORE_PATH=$conda_ism_core_path \
 --build-arg GITHUB_REPO_URL=https://github.com/quantumwake/alethic-ism-db.git --no-cache .

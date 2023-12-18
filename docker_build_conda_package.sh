#!/bin/bash

#docker build --platform linux/amd64 -t quantumwake/alethic-ism-db:latest \
# --build-arg GITHUB_REPO_URL=https://github.com/quantumwake/alethic-ism-db.git --no-cahce .

docker build -t quantumwake/alethic-ism-db:latest \
 --build-arg GITHUB_REPO_URL=https://github.com/quantumwake/alethic-ism-db.git --no-cache .

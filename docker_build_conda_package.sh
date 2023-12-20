CONDA_LOCAL_CHANNEL_TARGZ=$(basename `find . -type f -name "alethic-ism-core*.tar.gz"`)

#docker build --platform linux/amd64 -t quantumwake/alethic-ism-db:latest \
# --build-arg GITHUB_REPO_URL=https://github.com/quantumwake/alethic-ism-db.git --no-cahce .

# TODO hardcoded - this is set to a private repo for now, such that it can be deployed to k8s
docker build \
 --progress=plain -t quantumwake/alethic-ism-db:latest \
 --build-arg CONDA_LOCAL_CHANNEL_TARGZ=$CONDA_LOCAL_CHANNEL_TARGZ \
 --build-arg GITHUB_REPO_URL=https://github.com/quantumwake/alethic-ism-db.git \
 --no-cache .
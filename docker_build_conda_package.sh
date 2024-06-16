APP_NAME="alethic-ism-api"
DOCKER_NAMESPACE="krasaee"
CONDA_PACKAGE_PATH_ISM_CORE="../alethic-ism-core"
GIT_COMMIT_ID=$(git rev-parse HEAD)
TAG="$DOCKER_NAMESPACE/$APP_NAME:$GIT_COMMIT_ID"

ARCH=$1
if [ -z "$ARCH" ];
then
  ARCH="linux/amd64"
  #TODO check operating system ARCH="linux/arm64"
fi;

echo "Using arch: $ARCH for image tag $TAG"
conda_ism_core_path=$(find $CONDA_PACKAGE_PATH_ISM_CORE -type f -name "alethic-ism-core*.tar.gz")
conda_ism_core_path=$(basename $conda_ism_core_path)

echo "Using Conda ISM core: $conda_ism_core_path"
if [ ! -z "${conda_ism_core_path}" ];
then
  echo "Copying $CONDA_PACKAGE_PATH_ISM_CORE/$conda_ism_core_path -> $conda_ism_core_path"
  cp $CONDA_PACKAGE_PATH_ISM_CORE/$conda_ism_core_path $conda_ism_core_path

  # TODO hardcoded - this is set to a private repo for now, such that it can be deployed to k8s
  docker build \
   --progress=plain --platform $ARCH -t quantumwake/alethic-ism-db:latest \
   --build-arg CONDA_ISM_CORE_PATH=$conda_ism_core_path \
   --no-cache .
fi;

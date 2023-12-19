# Use an x86 base image
# Stage 1: Base Image with Miniconda
FROM continuumio/miniconda3 as base

# Set the working directory
WORKDIR /app

ARG CONDA_ISM_CORE_PATH
ARG GITHUB_REPO_URL

RUN git clone --depth 1 ${GITHUB_REPO_URL} repo
RUN mkdir -p /app/conda/env/local_channel 

# copy the alethic-ism-core conda package
COPY ${CONDA_ISM_CORE_PATH} /app/conda/env/local_channel 

# Move to the repository directory
WORKDIR /app/repo

# Force all commands to run in bash
SHELL ["/bin/bash", "--login", "-c"]

# Add the pytorch channel (required for apple silicon)
RUN conda config --add channels pytorch

# Install necessary dependencies for the build process
RUN conda install -y conda-build

# Index the local channel
## RUN conda index /app/conda/env/local_channel

# Initialize the conda environment specific to this build
RUN conda env create -f environment.yml

# Install ISM core directly instead, instead of environment.yml
RUN conda install "/app/conda/env/local_channel/${CONDA_ISM_CORE_PATH}"

# Initialize conda in bash config files:
RUN conda init bash

# Activate the environment, and make sure it's activated:
RUN echo "conda activate alethic-ism-core" > ~/.bashrc

# Run the build command (adjust as per your repo's requirements)
RUN bash ./build.sh

# Install the anaconda client to upload
#RUN conda install anaconda-client

# (Optional) Command to keep the container running, adjust as needed
#CMD tail -f /dev/null



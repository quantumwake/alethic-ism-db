# Stage 1: Base Image with Miniconda
FROM continuumio/miniconda3

# Set the working directory
WORKDIR /app

# copy the entire repo
ADD . /app/repo

# copy the alethic-ism-core conda package
ARG CONDA_ISM_CORE_PATH
COPY ${CONDA_ISM_CORE_PATH} .
RUN tar -zxvf $CONDA_ISM_CORE_PATH -C /

# Move to the repository directory
WORKDIR /app/repo

# Force all commands to run in bash
SHELL ["/bin/bash", "--login", "-c"]

# install the conda build package in base
RUN conda install -y conda-build

# Initialize the conda environment
RUN conda env create -f environment.yaml

# Initialize conda in bash config files:
RUN conda init bash

# Activate the environment, and make sure it's activated:
RUN echo "conda activate alethic-ism-db" > ~/.bashrc

# display information about the current activation
RUN conda info

# Install necessary dependencies for the build process
RUN conda install -y conda-build

# Run the build command (adjust as per your repo's requirements)
RUN bash ./conda_build.sh --local-channel-path /app/conda/env/local_channel

# package the local channel such that we can extract into an artifact
RUN chmod +x ./package-conda-channel.sh
RUN bash ./package-conda-channel.sh


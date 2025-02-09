# Use an x86 base image
# Stage 1: Base Image with Miniconda
FROM continuumio/miniconda3:24.5.0-0 AS core

# conda package repository token such that we can upload the package to anaconda cloud
ARG ANACONDA_API_TOKEN
ENV ANACONDA_API_TOKEN=$ANACONDA_API_TOKEN

# Set the working directory
WORKDIR /app

ADD alethic_ism_db /app/repo/alethic_ism_db
ADD environment.yaml /app/repo/environment.yaml
ADD recipe /app/repo/recipe
ADD conda_build.sh /app/repo/conda_build.sh
ADD conda_package_channel.sh /app/repo/conda_package_channel.sh

ADD pyproject.toml /app/repo/pyproject.toml
ADD Makefile /app/repo/Makefile
ADD setup.py /app/repo/setup.py

# Move to the repository directory
WORKDIR /app/repo

# Force all commands to run in bash
SHELL ["/bin/bash", "--login", "-c"]

# install the conda build package in base
RUN conda install -y conda-build -c conda-forge

# Initialize the conda environment
RUN conda env create -f environment.yaml

# Activate the environment, and make sure it's activated:
RUN echo "conda activate alethic-ism-db" > ~/.bashrc

# Initialize conda in bash config files:
RUN conda init bash


# display information about the current activation
RUN conda info

# Install necessary dependencies for the build process
RUN conda install -y conda-build anaconda-client -c conda-forge --override-channels

# Run the build command (adjust as per your repo's requirements)
RUN bash ./conda_build.sh --local-channel-path /app/conda/env/local_channel

# package the local channel such that we can extract into an artifact
RUN chmod +x ./conda_package_channel.sh && \
    bash ./conda_package_channel.sh

## push the package to anaconda cloud
#RUN anaconda upload /app/conda/env/local_channel/linux-64/*.tar.bz2 ### only if we have compiled code
RUN anaconda upload /app/conda/env/local_channel/noarch/*.conda

FROM ghcr.io/astral-sh/uv:python3.12-alpine as core

# Set the working directory
WORKDIR /
# add repository
ADD . .

# Create a virtual environment using uv
RUN uv venv

# Install your package in editable mode using the virtual environment’s pip
RUN source .venv/bin/activate && \
    apk --no-cache update && \
    apk --no-cache add git gcc musl-dev postgresql-dev python3-dev && \
    uv pip install -U pip twine setuptools setuptools-scm build && \
    uv pip install -r requirements.txt -U --no-cache

# Build the package using the virtual environment’s Python interpreter
RUN source .venv/bin/activate && \
    python -m build

RUN --mount=type=secret,id=pypirc,target=/tmp/.pypirc \
    source .venv/bin/activate && \
    python -m twine upload --config-file /tmp/.pypirc --repository pypi dist/*


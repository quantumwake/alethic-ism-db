# Makefile
.PHONY: build push deploy all

# Default image name - can be overridden with make IMAGE=your-image-name
IMAGE ?= krasaee/alethic-ism-db:latest

# Ensure scripts are executable
.PHONY: init
init:
	 chmod +x docker_build.sh docker_push.sh docker_deploy.sh

# Build the Docker image using buildpacks
.PHONY: build
build:
	 sh docker_build.sh -i $(IMAGE)

# Push the Docker image to registry
.PHONY: push
push:
	 sh docker_push.sh -i $(IMAGE)

# Deploy the application to kubernetes using the k8s/deployment.yaml as a template.
.PHONY: deploy
deploy:
	 sh docker_deploy.sh -i $(IMAGE)

# Build helm postgres init image
.PHONY: build-initdb
build-initdb:
	 @docker build -t krasaee/alethic-ism-db:initdb.20250407 -f postgres.Dockerfile ./bootstrap/.

push-initdb:
	 @docker push krasaee/alethic-ism-db:initdb.20250407

# Build, push and deploy
.PHONY: all
all: build push deploy

# Clean up old images and containers (optional)
.PHONY: clean
clean:
	 @docker system prune -f

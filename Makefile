# Makefile
.PHONY: build push deploy all version

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

# Version bump (patch version)
version:
	@echo "Bumping patch version..."
	@git fetch --tags
	@LATEST_TAG=$$(git describe --tags --abbrev=0 2>/dev/null || echo ""); \
	if [[ -z "$$LATEST_TAG" ]]; then \
		MAJOR=0; MINOR=1; PATCH=0; \
		OLD_TAG="<none>"; \
	else \
		OLD_TAG="$$LATEST_TAG"; \
		VERSION="$${LATEST_TAG#v}"; \
		IFS='.' read -r MAJOR MINOR PATCH <<< "$$VERSION"; \
		PATCH=$$((PATCH + 1)); \
	fi; \
	NEW_TAG="v$${MAJOR}.$${MINOR}.$${PATCH}"; \
	git tag -a "$$NEW_TAG" -m "Release $$NEW_TAG"; \
	git push origin "$$NEW_TAG"; \
	echo "➜ bumped $${OLD_TAG} → $${NEW_TAG}"

# Build helm postgres init image
# Default initdb image name and tag - can be overridden with make INITDB_IMAGE=your-image-name INITDB_TAG=your-tag
INITDB_IMAGE ?= krasaee/alethic-ism-db
INITDB_TAG ?= initdb.latest

.PHONY: build-initdb
build-initdb:
	 @docker build -t $(INITDB_IMAGE):$(INITDB_TAG) -f postgres.Dockerfile ./bootstrap/.

.PHONY: push-initdb
push-initdb:
	 @docker push $(INITDB_IMAGE):$(INITDB_TAG)

# Build, push and deploy
.PHONY: all
all: build push deploy

# Clean up old images and containers (optional)
.PHONY: clean
clean:
	 @docker system prune -f

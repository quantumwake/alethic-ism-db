#!/bin/bash
set -euo pipefail

META_FILE="${META_YAML_PATH:-./recipe}/meta.yaml"

# Make sure yq is installed (this example uses mikefarah's yq v4+)
if ! command -v yq &>/dev/null; then
  echo "yq is required but not found. Please install yq (https://github.com/mikefarah/yq) and try again." >&2
  exit 1
fi

# --- Bump the build number ---
# Use a default of 0 if the build number is not present.
current_build=$(yq eval '.build.number // 0' "$META_FILE")
new_build=$(( current_build + 1 ))
yq eval -i ".build.number = $new_build" "$META_FILE"
echo "Updated build number from $current_build to $new_build"

# --- Bump the version (patch) ---
# Assumes the version is in the form "X.Y.Z" under package.version.
current_version=$(yq eval '.package.version' "$META_FILE")
IFS='.' read -r major minor patch <<< "$current_version"
new_patch=$(( patch + 1 ))
new_version="${major}.${minor}.${new_patch}"
yq eval -i ".package.version = \"$new_version\"" "$META_FILE"
echo "Updated version from $current_version to $new_version"

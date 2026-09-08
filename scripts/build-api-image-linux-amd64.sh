#!/usr/bin/env bash

set -euo pipefail

REPOSITORY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_REPOSITORY="${API_IMAGE_REPOSITORY:-pocket-farm-api}"
IMAGE_TAG="${API_IMAGE_TAG:-$(date -u +%Y%m%d%H%M%S)}"
OUTPUT_DIRECTORY="${OUTPUT_DIRECTORY:-${REPOSITORY_ROOT}/artifacts}"

if [[ ! "${IMAGE_TAG}" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]*$ ]]; then
  echo "API_IMAGE_TAG may only contain letters, digits, dots, underscores, and hyphens." >&2
  exit 1
fi

if ! docker buildx version >/dev/null 2>&1; then
  echo "Docker Buildx is required. Install Docker Desktop or the Docker Buildx plugin first." >&2
  exit 1
fi

IMAGE="${IMAGE_REPOSITORY}:${IMAGE_TAG}"
ARCHIVE="${OUTPUT_DIRECTORY}/${IMAGE_REPOSITORY##*/}-${IMAGE_TAG}-linux-amd64.tar.gz"

mkdir -p "${OUTPUT_DIRECTORY}"

echo "Building ${IMAGE} for linux/amd64..."
docker buildx build \
  --platform linux/amd64 \
  --load \
  --tag "${IMAGE}" \
  --file "${REPOSITORY_ROOT}/apps/api/Dockerfile" \
  "${REPOSITORY_ROOT}/apps/api"

echo "Exporting ${ARCHIVE}..."
docker save "${IMAGE}" | gzip -c > "${ARCHIVE}"

(
  cd "${OUTPUT_DIRECTORY}"
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$(basename "${ARCHIVE}")" > "$(basename "${ARCHIVE}").sha256"
  else
    sha256sum "$(basename "${ARCHIVE}")" > "$(basename "${ARCHIVE}").sha256"
  fi
)

cat <<EOF

Done.
Image:    ${IMAGE}
Archive:  ${ARCHIVE}
Checksum: ${ARCHIVE}.sha256

Upload the archive and checksum to the server, then run:
  sha256sum -c $(basename "${ARCHIVE}").sha256
  docker load -i $(basename "${ARCHIVE}")

Start the imported image from deploy/ with one of the following options.

Use the MySQL service managed by Compose:
  docker compose -f docker-compose.server.yml up -d mysql
  API_IMAGE=${IMAGE} docker compose -f docker-compose.server.yml --profile migration run --rm migrate
  API_IMAGE=${IMAGE} docker compose -f docker-compose.server.yml up -d api

Use an existing external MySQL database configured in api.env:
  API_IMAGE=${IMAGE} docker compose -f docker-compose.external-db.yml --profile migration run --rm migrate
  API_IMAGE=${IMAGE} docker compose -f docker-compose.external-db.yml up -d api
EOF

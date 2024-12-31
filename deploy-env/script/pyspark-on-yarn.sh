#!/bin/bash

ROOT_DIR="deploy-env"

WORK_DIR=$(pwd)
while [[ ! $(basename "$WORK_DIR") == "$ROOT_DIR" ]]; do
  if [[ "$WORK_DIR" == "/" ]]; then
    echo "Error: Could not find a directory ending with '$ROOT_DIR'. Exiting."
    exit 1
  fi
  WORK_DIR=$(dirname "$WORK_DIR")
done

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path_to_spark_application>"
    exit 1
fi

APP_PATH=$1
DEPENDENCIES_PATH="$WORK_DIR/dependencies"
CONTAINER_DEPS_PATH="/dependencies"

ZIP_FILES=$(find "$DEPENDENCIES_PATH" -type f -name "*.zip")

PY_FILES_ARG=""
if [ -n "$ZIP_FILES" ]; then
  for ZIP_FILE in $ZIP_FILES; do
    CONTAINER_PATH="$CONTAINER_DEPS_PATH/$(basename "$ZIP_FILE")"
    if [ -z "$PY_FILES_ARG" ]; then
      PY_FILES_ARG="--py-files $CONTAINER_PATH"
    else
      PY_FILES_ARG="$PY_FILES_ARG,$CONTAINER_PATH"
    fi
  done
fi
echo "$PY_FILES_ARG"

docker exec master spark-submit \
  --master spark://master:7077 \
  $PY_FILES_ARG \
  "$APP_PATH"

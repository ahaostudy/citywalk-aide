#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path_to_spark_application>"
    exit 1
fi

APP_PATH=$1

docker exec master spark-submit \
  --master yarn \
  --deploy-mode cluster \
  "$APP_PATH"

#!/bin/bash

CONTAINER_NAMES=("datanode1 datanode2 datanode3 resourcemanager")
HOSTS_FILE="/etc/hosts"

for CONTAINER_NAME in "${CONTAINER_NAMES[@]}"; do
  echo "127.0.0.1 $CONTAINER_NAME" | sudo tee -a "$HOSTS_FILE" > /dev/null
done
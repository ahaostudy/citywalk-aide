#!/bin/bash

ROOT_DIR="deploy-env"
HDFS_VOLUMES="hdfs"

# install pyspark
WORK_DIR=$(pwd)
while [[ ! $(basename "$WORK_DIR") == "$ROOT_DIR" ]]; do
  if [[ "$WORK_DIR" == "/" ]]; then
    echo "Error: Could not find a directory ending with '$ROOT_DIR'. Exiting."
    exit 1
  fi
  WORK_DIR=$(dirname "$WORK_DIR")
done

mkdir "$WORK_DIR/$HDFS_VOLUMES/pyspark_lib"
docker cp master:/usr/spark-2.3.0/python/lib/. "$WORK_DIR/$HDFS_VOLUMES/pyspark_lib"
zip -r "$WORK_DIR/$HDFS_VOLUMES/pyspark_lib.zip" "$WORK_DIR/$HDFS_VOLUMES/pyspark_lib"

docker exec namenode hdfs dfs -mkdir -p /user/envs
docker exec namenode hdfs dfs -put -f /$HDFS_VOLUMES/pyspark_lib.zip /user/envs/pyspark_lib.zip

rm -rf "$WORK_DIR/$HDFS_VOLUMES/pyspark_lib"
rm -rf "$WORK_DIR/$HDFS_VOLUMES/pyspark_lib.zip"

# install python on resourcemanager
docker exec resourcemanager sh -c "echo 'deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ xenial main universe' > /etc/apt/sources.list"
docker exec resourcemanager sh -c "echo 'deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ xenial-updates main universe' >> /etc/apt/sources.list"
docker exec resourcemanager sh -c "echo 'deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ xenial-security main universe' >> /etc/apt/sources.list"
docker exec resourcemanager apt-get update
docker exec resourcemanager apt-get install --force-yes -y python3 python3-pip
docker exec resourcemanager ln -s /usr/bin/python3 /usr/bin/python

# install python on nodemanager
docker exec nodemanager1 sh -c "echo 'deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ xenial main universe' > /etc/apt/sources.list"
docker exec nodemanager1 sh -c "echo 'deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ xenial-updates main universe' >> /etc/apt/sources.list"
docker exec nodemanager1 sh -c "echo 'deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ xenial-security main universe' >> /etc/apt/sources.list"
docker exec nodemanager1 apt-get update
docker exec nodemanager1 apt-get install --force-yes -y python3 python3-pip
docker exec nodemanager1 ln -s /usr/bin/python3 /usr/bin/python

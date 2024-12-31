# Environment Setup

This guide covers the setup of a Hadoop and Spark on Yarn environment, supporting Pyspark.

## Prerequisites

Please ensure that Docker and Docker-Compose are installed.

## Deployment

### 1. Start Containers

```shell
docker-compose up -d
```

### 2. Install Pyspark Environment in Containers

```shell
./script/pyspark-env-init.sh
```

### 3. Testing

You can open the following Web UI interfaces to check if the deployment was successful:

- HDFS: http://localhost:50070
- YARN (Resource Manager): http://localhost:8088
- Spark: http://localhost:8080/

## Examples

### 1. Upload Test Data to HDFS

```shell
docker exec namenode hdfs dfs -mkdir -p /user/example
docker exec namenode hdfs dfs -put /hdfs/example/sales_data.csv /user/example/
```

### 2. Submitting Applications

- Method 1: Submit applications using the [pyspark-on-yarn.sh](script/pyspark-on-yarn.sh) script

```shell
./script/pyspark-on-yarn.sh /code/example/example.py
```

- Method 2: Manually enter the container and submit applications using Docker exec

```shell
docker exec master spark-submit \
  --master yarn \
  --deploy-mode cluster \
  /code/example/example.py
```

Note: The paths accepted here are paths within the Spark container, which are mapped from the local [code](code) directory to the `/code` directory inside the container.

## Node Scaling

### Node Manager

Add a new node in the [docker-compose.yml](docker-compose.yml) file, and refer to [pyspark-on-yarn.sh](script/pyspark-on-yarn.sh) to install the Python environment in the new NodeManager.

### Data Node

Simply add a new node in the [docker-compose.yml](docker-compose.yml) file while ensuring to modify port mapping and configuration file mounts as needed.

### Spark Worker

You can directly add a new node in the [docker-compose.yml](./docker.yml) file, keeping in mind the necessary modifications to port mapping and configuration file mounts.

## Recommendations

Consider configuring command aliases locally to simplify commands like `docker exec <container>`, improving efficiency in executing commands within containers. Here's an example:

```shell
alias dm='docker exec master'
alias dw='docker exec worker'
alias dn='docker exec namenode'
```

### Quick Configuration

- **bash**
  ```shell
  echo -e "\nalias dm='docker exec master'\nalias dw='docker exec worker'\nalias dn='docker exec namenode'" >> ~/.bashrc
  source ~/.bashrc
  ```

- **zsh**
  ```shell
  echo -e "\nalias dm='docker master'\nalias dw='docker exec worker'\nalias dn='docker exec namenode'" >> ~/.zshrc
  source ~/.zshrc
  ```
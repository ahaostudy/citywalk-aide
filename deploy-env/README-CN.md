# 环境部署

用于 Hadoop 和 Spark on Yarn 环境的搭建，支持 Pyspark 。

## 前置

请自行安装 Docker 和 Docker-Compose。

## 部署

### 1. 启动容器

```shell
docker-compose up -d
```

### 2. 在容器中安装 Pyspark 相关环境

```shell
./script/pyspark-env-init.sh
```

### 3. 测试

可以打开以下 Web UI 界面查看是否完成部署：

- HDFS: http://localhost:50070
- YARN (Resource Manger): http://localhost:8088
- Spark: http://localhost:8080/

## 示例

### 1. 将测试数据上传到 HDFS 中

```shell
docker exec namenode hdfs dfs -mkdir -p /user/example
docker exec namenode hdfs dfs -put /hdfs/example/sales_data.csv /user/example/
```

### 2. 提交程序

- 方式一：通过 [pyspark-on-yarn.sh](./script/pyspark-env-init.sh) 脚本提交程序

```shell
./script/pyspark-on-yarn.sh /code/example/example.py
```

- 方式二：手动通过 Docker exec 进入容器提交程序

```shell
docker exec master spark-submit \
  --master yarn \
  --deploy-mode cluster \
  /code/example/example.py
```

补充: 此处接收的路径是 Spark 容器内的路径，是通过 Docker 挂载卷将本地的 [code](./code) 目录挂载到容器内的 `/code` 中的。

## 节点拓展

### Node Manager

先在 [docker-compose.yml](./docker-compose.yml) 中添加新节点，同时参考 [pyspark-on-yarn.sh](./script/pyspark-env-init.sh)
，在新的 NodeManager 中安装 Python 环境。

### Data Node

直接在 [docker-compose.yml](./docker-compose.yml) 中添加新节点，注意修改端口映射和配置文件挂载即可。

### Spark Worker

直接在 [docker-compose.yml](./docker-compose.yml) 中添加新节点，注意修改端口映射和配置文件挂载即可。

## 建议

可以在本地配置命令别名，将 docker exec \<container\> 简化，来提高在容器中执行命令的效率，参考如下：

```shell
alias dm='docker exec master'
alias dw='docker exec worker'
alias dn='docker exec namenode'
```

### 快速配置

- **bash**
  ```shell
  echo -e "\nalias dm='docker exec master'\nalias dw='docker exec worker'\nalias dn='docker exec namenode'" >> ~/.bashrc
  source ~/.bashrc
  ```

- **zsh**
  ```shell
  echo -e "\nalias dm='docker exec master'\nalias dw='docker exec worker'\nalias dn='docker exec namenode'" >> ~/.zshrc
  source ~/.zshrc
  ```

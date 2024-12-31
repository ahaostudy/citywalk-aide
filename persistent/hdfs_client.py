from hdfs import InsecureClient

from logger.logger import logger


class HDFSClient:
    def __init__(self, host: str, user: str):
        self.client = InsecureClient(host, user=user)

    def list_files(self, path: str = '/') -> list:
        try:
            return self.client.list(path)
        except Exception as e:
            logger.error(f"Error listing files in {path}: {e}")
            return []

    def write_file(self, path: str, data: str, overwrite: bool = True):
        try:
            self.client.write(path, data=data, overwrite=overwrite)
            logger.info(f"Data written to {path}")
        except Exception as e:
            logger.error(f"Error writing to {path}: {e}")

    def read_file(self, path: str) -> str:
        try:
            with self.client.read(path) as reader:
                return reader.read().decode('utf-8')
        except Exception as e:
            logger.error(f"Error reading from {path}: {e}")
            return ""

    def delete_file(self, path: str):
        try:
            self.client.delete(path)
            logger.info(f"{path} deleted")
        except Exception as e:
            logger.error(f"Error deleting {path}: {e}")

    def make_directory(self, path: str, permission: str = None):
        try:
            self.client.makedirs(path, permission=permission)
            logger.info(f"Directory {path} created with permission {permission}")
        except Exception as e:
            logger.error(f"Error creating directory {path}: {e}")

    def exists(self, path: str) -> bool:
        try:
            self.client.status(path)
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Error checking existence of {path}: {e}")
            return False


if __name__ == '__main__':
    hdfs_client = HDFSClient('http://localhost:50070', user='root')

    logger.info("Files in root: %s", hdfs_client.list_files('/'))

    hdfs_file_path = '/user/spider/xhs/note/test.txt'
    hdfs_client.write_file(hdfs_file_path, "This is a test string.")

    logger.info("File content: %s", hdfs_client.read_file(hdfs_file_path))

    hdfs_client.delete_file(hdfs_file_path)

    hdfs_client.make_directory('/user/spider/xhs/note', permission='777')

    print(hdfs_client.read_file('/user/data/routes.csv')[:10000])

import json

from logger.logger import logger
from persistent.hdfs_client import HDFSClient
from cachetools import TTLCache
from datetime import datetime

recommend_result_path = '/user/data/recommend_result.json'
hdfs_client = HDFSClient('http://localhost:50070', 'root')

cache = TTLCache(maxsize=5000, ttl=600)


def load_recommendation_from_hdfs(route_id):
    raw_data = hdfs_client.read_file(recommend_result_path)
    all_recommendations = json.loads(raw_data)
    print(all_recommendations)

    cache[route_id] = all_recommendations.get(route_id, [])
    return cache[route_id]


def get_recommendations(route_id):
    if route_id in cache:
        logger.debug(f"{datetime.now()}: Fetching recommendation for route_id={route_id} from cache...")
        return cache[route_id]

    return load_recommendation_from_hdfs(route_id)


# 示例用法
if __name__ == '__main__':
    route_id = '94c0d943-473b-4472-99a9-8aa84d89cdd6'

    # 查询推荐结果
    recommendations = get_recommendations(route_id)
    print(f"Recommendations for route_id {route_id}: {recommendations}")
    # 查询推荐结果
    recommendations = get_recommendations(route_id)
    print(f"Recommendations for route_id {route_id}: {recommendations}")

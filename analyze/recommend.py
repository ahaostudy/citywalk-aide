import io
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from persistent.hdfs_client import HDFSClient
import schedule
import time
import json
from datetime import datetime

hdfs_client = HDFSClient('http://localhost:50070', 'root')
routes_df = pd.read_csv(io.StringIO(hdfs_client.read_file('/user/data/routes.csv')))
locations_df = pd.read_csv(io.StringIO(hdfs_client.read_file('/user/data/locations.csv')))
recommend_result_path = '/user/data/recommend_result.json'


def load_chinese_stopwords():
    stopwords = []
    with open('chinese_stopwords.txt', 'r', encoding='utf-8') as f:
        stopwords = [line.strip() for line in f.readlines()]
    return stopwords


chinese_stopwords = load_chinese_stopwords()


def calculate_time_similarity(pub_date1, pub_date2):
    date_format = "%Y-%m-%d"
    pub1 = datetime.strptime(pub_date1, date_format)
    pub2 = datetime.strptime(pub_date2, date_format)
    delta = abs((pub1 - pub2).days)
    max_delta = 365
    return 1 - (delta / max_delta)


def calculate_likes_similarity(likes1, likes2):
    max_likes = max(routes_df['liked_count'])
    return 1 - abs(likes1 - likes2) / max_likes


def calculate_description_similarity(desc1, desc2):
    desc1 = desc1 if pd.notna(desc1) else ""
    desc2 = desc2 if pd.notna(desc2) else ""

    tfidf = TfidfVectorizer(stop_words=chinese_stopwords)
    tfidf_matrix = tfidf.fit_transform([desc1, desc2])
    return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]


def calculate_location_name_similarity(route_id1, route_id2):
    locations1 = locations_df[locations_df['route_id'] == route_id1]['name'].dropna().values
    locations2 = locations_df[locations_df['route_id'] == route_id2]['name'].dropna().values

    if len(locations1) == 0 or len(locations2) == 0:
        return 0.0

    tfidf = TfidfVectorizer(stop_words=chinese_stopwords)
    tfidf_matrix = tfidf.fit_transform(list(locations1) + list(locations2))
    similarity = cosine_similarity(tfidf_matrix[:len(locations1)], tfidf_matrix[len(locations1):])
    return np.mean(similarity)


def calculate_city_similarity(route_id1, route_id2):
    city1 = routes_df[routes_df['id'] == route_id1]['city'].dropna().values
    city2 = routes_df[routes_df['id'] == route_id2]['city'].dropna().values

    if len(city1) == 0 or len(city2) == 0:
        return 0.0

    return 1.0 if city1[0] == city2[0] else 0.0


def calculate_all_recommendations():
    recommendations_dict = {}
    total_routes = len(routes_df)

    for idx, current_route in routes_df.iterrows():
        current_route_id = current_route['id']
        print(f"[{int(idx) + 1}/{total_routes}] Processing route_id={current_route_id}...")

        recommendations = []

        for _, route in routes_df.iterrows():
            if route['id'] == current_route_id:
                continue

            try:
                time_similarity = calculate_time_similarity(current_route['published_at'], route['published_at'])
                likes_similarity = calculate_likes_similarity(current_route['liked_count'], route['liked_count'])
                description_similarity = calculate_description_similarity(current_route['summary'], route['summary'])
                location_name_similarity = calculate_location_name_similarity(current_route_id, route['id'])
                city_similarity = calculate_city_similarity(current_route_id, route['id'])

                total_similarity = (0.1 * time_similarity + 0.2 * likes_similarity +
                                    0.2 * description_similarity + 0.2 * location_name_similarity + 0.3 * city_similarity)

                recommendations.append((route['id'], total_similarity))
            except Exception as e:
                print(f"Error processing route_id={current_route_id}, comparing with route_id={route['id']}: {e}")
                continue

        recommendations.sort(key=lambda x: x[1], reverse=True)
        recommendations_dict[current_route_id] = recommendations[:20]
        print(f"  Top 5 recommendations for route_id={current_route_id}: "
              f"{[r[0] for r in recommendations[:5]]}")

    return recommendations_dict


def calculate_and_store_recommendations():
    print(f"Job started at {datetime.now()}")

    all_recommendations = calculate_all_recommendations()

    recommend_result = json.dumps(all_recommendations, ensure_ascii=False)
    hdfs_client.write_file(recommend_result_path, recommend_result)

    print(f"All recommendations have been calculated and stored at {recommend_result_path}.")


if __name__ == '__main__':
    print("Scheduler started. Waiting for the job to run...")

    calculate_and_store_recommendations()
    schedule.every().day.at("20:00").do(calculate_and_store_recommendations)

    while True:
        schedule.run_pending()
        time.sleep(600)

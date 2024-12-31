import json
import random
from datetime import datetime, date
from uuid import UUID

from flask import Flask, request, jsonify
from flask_cors import CORS

from model.note import NoteInfo
from model.route import Location, Route
from persistent.clickhouse_client import ClickhouseClient
from server.recommend import get_recommendations

app = Flask(__name__)
CORS(app)

clickhouse_client = ClickhouseClient('citywalk_aide')


@app.route('/route/<route_id>', methods=['GET'])
def get_route(route_id: str):
    route = Route.objects_in(clickhouse_client).filter(id=route_id)[0]
    note = NoteInfo.objects_in(clickhouse_client).filter(id=route.note_id)[0]

    result = route.to_dict()
    result['locations'] = []
    result['cover'] = json.loads(note.cover)

    locations = Location.objects_in(clickhouse_client).filter(route_id=route_id)
    for loc in locations:
        loc_dict = loc.to_dict()
        loc_dict['activities'] = json.loads(loc.activities)
        loc_dict['transportation'] = json.loads(loc.transportation)
        result['locations'].append(loc_dict)

    resp = json.dumps({
        "data": result,
    }, cls=CustomJSONEncoder, ensure_ascii=False)
    return resp, 200, {'Content-Type': 'application/json; charset=utf-8'}


@app.route('/search', methods=['GET'])
def search():
    city = request.args.get('city')
    keyword = request.args.get('keyword', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))

    offset = (page - 1) * page_size

    location_join = "LEFT JOIN citywalk_aide.locations l ON toString(r.id) = l.route_id" if len(keyword) else ''
    keyword_where = f"""
        AND (r.title LIKE '%{keyword}%'
        OR r.summary LIKE '%{keyword}%'
        OR has(arrayMap(x -> x LIKE '%{keyword}%', r.tags), 1)
        OR l.name LIKE '%{keyword}%'
        OR l.description LIKE '%{keyword}%'
        OR has(arrayMap(x -> x LIKE '%{keyword}%', l.tags), 1))
        """ if len(keyword) else ''

    route_query = f"""
    SELECT DISTINCT r.id AS id,
       r.note_id AS note_id,
       r.city AS city,
       r.title AS title,
       r.summary AS summary,
       r.tags AS tags,
       r.start_time AS start_time,
       r.end_time AS end_time,
       r.total_duration AS total_duration,
       r.liked_count AS liked_count,
       r.notes AS notes,
       r.published_at AS published_at,
       r.created_at AS created_at,
       n.cover AS cover
    FROM citywalk_aide.routes r
    {location_join}
    JOIN citywalk_aide.note_infos n ON n.id = r.note_id
    WHERE r.city = '{city}' AND r.title <> '' {keyword_where}
    ORDER BY r.liked_count DESC
    LIMIT {page_size} OFFSET {offset}
    """
    print(route_query)
    routes = [route.to_dict() for route in clickhouse_client.select(route_query)]

    route_map = {str(route.get('id')): route for route in routes}
    for route in route_map.values():
        route['cover'] = json.loads(route.get('cover', '{}'))
        route['locations'] = []

    locations = Location.objects_in(clickhouse_client) \
        .filter(Location.route_id.isIn(route_map.keys())) \
        .order_by('route_id', 'order') if len(route_map) else []

    for loc in locations:
        route_id = loc.route_id
        if route_id in route_map:
            loc_dict = loc.to_dict()
            loc_dict['activities'] = json.loads(loc.activities)
            loc_dict['transportation'] = json.loads(loc.transportation)
            route_map[route_id]['locations'].append(loc_dict)

    count_query = f"""
    SELECT COUNT(DISTINCT id) AS total
    FROM citywalk_aide.routes r
    {location_join}
    WHERE r.city = '{city}' AND r.title <> '' {keyword_where}
    """
    total = [t.to_dict() for t in clickhouse_client.select(count_query)][0]['total']

    resp = json.dumps({
        "data": list(route_map.values()),
        "total": total,
        "page": page,
        "page_size": page_size
    }, cls=CustomJSONEncoder, ensure_ascii=False)
    return resp, 200, {'Content-Type': 'application/json; charset=utf-8'}


@app.route('/recommendation', methods=['GET'])
def recommendation():
    route_id = request.args.get('route_id', '')

    recommends = {item[0]: item[1] for item in get_recommendations(route_id)}
    print(recommends)

    if not recommends or len(recommends) == 0:
        return jsonify({'data': []})

    routes = Route.objects_in(clickhouse_client) \
        .filter(Route.id.isIn(recommends.keys())) \
        .order_by('created_at')

    locations = Location.objects_in(clickhouse_client) \
        .filter(Location.route_id.isIn(recommends.keys())) \
        .order_by('route_id', 'order')

    location_map = {}
    for loc in locations:
        route_id = loc.route_id
        if route_id not in location_map:
            location_map[route_id] = []
        loc_dict = loc.to_dict()
        loc_dict['activities'] = json.loads(loc.activities)
        loc_dict['transportation'] = json.loads(loc.transportation)
        location_map[route_id].append(loc_dict)

    route_list = []
    for route in routes:
        route_dict = route.to_dict()
        route_id = str(route.id)
        route_dict['id'] = route_id
        route_dict['locations'] = location_map.get(route_id, [])
        route_dict['score'] = recommends.get(route_id, 0)
        route_list.append(route_dict)

    route_list.sort(key=lambda x: x['score'], reverse=True)

    resp = json.dumps({
        "data": route_list,
    }, cls=CustomJSONEncoder, ensure_ascii=False)

    return resp, 200, {'Content-Type': 'application/json; charset=utf-8'}


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

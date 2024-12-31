from clickhouse_driver import Client
from persistent.hdfs_client import HDFSClient

if __name__ == '__main__':
    clickhouse_client = Client('localhost')
    hdfs_client = HDFSClient('http://localhost:50070', 'root')

    routes_query = "SELECT * FROM citywalk_aide.routes"
    locations_query = "SELECT * FROM citywalk_aide.locations"

    routes_df = clickhouse_client.query_dataframe(routes_query)
    locations_df = clickhouse_client.query_dataframe(locations_query)

    routes_csv_data = routes_df.to_csv(index=False)
    locations_csv_data = locations_df.to_csv(index=False)

    hdfs_client.write_file('/user/data/routes.csv', routes_csv_data)
    hdfs_client.write_file('/user/data/locations.csv', locations_csv_data)

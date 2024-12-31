from model.note import NoteInfo
from model.route import Route, Location
from persistent.clickhouse_client import ClickhouseClient

if __name__ == '__main__':
    client = ClickhouseClient('citywalk_aide')
    client.create_table(NoteInfo)
    client.create_table(Route)
    client.create_table(Location)

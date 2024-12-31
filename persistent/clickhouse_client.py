from clickhouse_orm import Database


class ClickhouseClient(Database):
    def __init__(self, db_name: str):
        super().__init__(db_name)

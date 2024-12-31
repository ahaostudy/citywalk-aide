from dataclasses import dataclass

from clickhouse_orm import models, fields
from clickhouse_orm.engines import MergeTree


class NoteInfo(models.Model):
    id = fields.StringField()
    xsec_token = fields.StringField()
    url = fields.StringField()
    type = fields.StringField()
    display_title = fields.StringField()
    liked_count = fields.Int32Field()
    cover = fields.StringField()
    image_list = fields.StringField()
    user = fields.StringField()
    page_hdfs_path = fields.StringField()
    city = fields.StringField()
    created_at = fields.DateTimeField()

    engine = MergeTree('created_at', ('id', 'created_at'))

    @classmethod
    def table_name(cls):
        return 'note_infos'


@dataclass
class UserInfo:
    nick_name: str
    avatar: str
    user_id: str
    nickname: str
    xsec_token: str


@dataclass
class ImageInfo:
    width: int
    height: int
    url: str

from dataclasses import asdict
from enum import Enum

import json


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        if hasattr(obj, "__dataclass_fields__"):
            return asdict(obj)
        return super().default(obj)


def json_encode(data, **kwargs):
    return json.dumps(data, cls=JSONEncoder, **kwargs)

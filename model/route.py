import json
from datetime import datetime
from uuid import uuid4

from clickhouse_orm import models, fields
from clickhouse_orm.engines import MergeTree
from typing import Optional, List

from pydantic import BaseModel, Field
from enum import Enum


class Route(models.Model):
    id = fields.UUIDField()
    note_id = fields.StringField()
    city = fields.StringField()
    title = fields.StringField()
    summary = fields.StringField()
    tags = fields.ArrayField(fields.StringField())
    start_time = fields.StringField()
    end_time = fields.StringField()
    total_duration = fields.Int32Field()
    liked_count = fields.Int32Field()
    notes = fields.StringField()
    published_at = fields.DateField()
    created_at = fields.DateTimeField()

    engine = MergeTree('created_at', ('note_id', 'created_at'))

    @classmethod
    def table_name(cls):
        return 'routes'


class Location(models.Model):
    id = fields.UUIDField()
    route_id = fields.StringField()
    order = fields.Int32Field()
    name = fields.StringField()
    description = fields.StringField()
    latitude = fields.Float64Field()
    longitude = fields.Float64Field()
    address = fields.StringField()
    tags = fields.ArrayField(fields.StringField())
    entry_fee = fields.Float64Field()
    time_range = fields.StringField()
    duration = fields.Int32Field()
    activities = fields.StringField()
    transportation = fields.StringField()
    created_at = fields.DateTimeField()

    engine = MergeTree('created_at', ('route_id', 'order', 'created_at'))

    @classmethod
    def table_name(cls):
        return 'locations'


class LLMTransportationMode(str, Enum):
    WALKING = "步行"
    BICYCLE = "骑行"
    CAR = "驾车/打车"
    BUS = "公交"
    SUBWAY = "地铁"
    TRAIN = "火车"
    HIGH_SPEED_RAIL = "高铁"
    AIRPLANE = "飞机"
    SHIP = "轮船"


class LLMActivity(BaseModel):
    name: str = Field(..., description="Activity name")
    description: Optional[str] = Field(None, description="Activity description")
    duration: Optional[int] = Field(None, description="Activity duration (minutes)")
    optional: bool = Field(..., description="Whether the activity is optional")


class LLMTransportation(BaseModel):
    mode: LLMTransportationMode = Field(..., description="Transportation mode")
    distance: Optional[float] = Field(None, description="Transportation distance (kilometers)")
    duration: Optional[int] = Field(None, description="Transportation duration (minutes)")
    notes: Optional[str] = Field(None, description="Transportation-related notes")


class LLMLocation(BaseModel):
    name: str = Field(..., description="Location name")
    description: Optional[str] = Field(None, description="Detailed description of the location")
    latitude: Optional[float] = Field(None, description="Latitude")
    longitude: Optional[float] = Field(None, description="Longitude")
    address: Optional[str] = Field(None, description="Address")
    tags: Optional[List[str]] = Field(None, description="List of tags")
    entry_fee: Optional[float] = Field(None, description="Entry fee")
    time_range: Optional[str] = Field(None, description="Opening hours range")
    duration: Optional[int] = Field(None, description="Stay duration (minutes)")
    activities: Optional[List[LLMActivity]] = Field(None, description="List of activities to be done at this location")
    transportation: Optional[List[LLMTransportation]] = Field(None,
                                                              description="Transportation modes to reach this location. For locations other than the first one, transportation should be provided.")


class LLMRoute(BaseModel):
    title: str = Field(..., description="Route title")
    summary: Optional[str] = Field(None, description="Route summary")
    tags: Optional[List[str]] = Field(None, description="List of route tags")
    start_time: Optional[str] = Field(None, description="Start time")
    end_time: Optional[str] = Field(None, description="End time")
    total_duration: Optional[int] = Field(None, description="Total duration (minutes)")
    notes: Optional[str] = Field(None, description="Route-related notes")
    locations: List[LLMLocation] = Field(..., description="List of locations")

    def to_route_model(self) -> tuple[Route, list[Location]]:
        route = Route(
            id=uuid4(),
            title=self.title,
            summary=self.summary or "",
            start_time=self.start_time or "",
            end_time=self.end_time or "",
            total_duration=self.total_duration or 0,
            notes=self.notes or "",
            published_at=datetime.now(),
            created_at=datetime.now()
        )

        locations = []
        for order, location_data in enumerate(self.locations):
            location = Location(
                id=uuid4(),
                route_id=str(route.id),
                order=order + 1,
                name=location_data.name,
                description=location_data.description or "",
                latitude=location_data.latitude or 0,
                longitude=location_data.longitude or 0,
                address=location_data.address or "",
                tags=location_data.tags or [],
                entry_fee=location_data.entry_fee or 0,
                time_range=location_data.time_range or "",
                duration=location_data.duration or 0,
                activities=json.dumps(
                    [activity.model_dump() for activity in location_data.activities]
                    if location_data.activities else [],
                    ensure_ascii=False,
                ),
                transportation=json.dumps(
                    [transportation.model_dump() for transportation in location_data.transportation]
                    if location_data.transportation else [],
                    ensure_ascii=False,
                ),
                created_at=datetime.now()
            )
            locations.append(location)

        return route, locations


class LLMRoutes(BaseModel):
    routes: List[LLMRoute] = Field(..., description="List of routes")

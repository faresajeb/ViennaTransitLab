from pydantic import BaseModel, Field


class TransportStop(BaseModel):
    stop_id: str
    station_id: str | None = None
    name: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    modes: list[str] = Field(default_factory=list)
    route_ids: list[str] = Field(default_factory=list)
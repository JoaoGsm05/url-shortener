from datetime import datetime

from pydantic import BaseModel, HttpUrl


class UrlCreate(BaseModel):
    original_url: HttpUrl
    expires_at: datetime | None = None


class UrlResponse(BaseModel):
    slug: str
    short_url: str
    original_url: str
    total_clicks: int
    created_at: datetime
    expires_at: datetime | None = None

    model_config = {"from_attributes": True}


class StatsResponse(BaseModel):
    slug: str
    original_url: str
    total_clicks: int
    last_click: datetime | None
    top_user_agents: list[str]

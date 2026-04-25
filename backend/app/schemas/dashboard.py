from __future__ import annotations

from pydantic import BaseModel


class MarketStat(BaseModel):
    market_type: str
    total: int
    hits: int
    hit_rate: float | None


class IdeaTypeStat(BaseModel):
    idea_type: str
    count: int


class TipsterStat(BaseModel):
    id: int
    name: str
    display_name: str | None
    total_ideas: int
    actionable_ideas: int
    evaluated_ideas: int
    hits: int
    hit_rate: float | None


class DashboardResponse(BaseModel):
    total_tipsters: int
    active_tipsters: int
    total_videos: int
    analyzed_videos: int
    total_ideas: int
    actionable_ideas: int
    evaluated_ideas: int
    overall_hit_rate: float | None
    ideas_by_market: list[MarketStat]
    ideas_by_type: list[IdeaTypeStat]
    top_tipsters: list[TipsterStat]

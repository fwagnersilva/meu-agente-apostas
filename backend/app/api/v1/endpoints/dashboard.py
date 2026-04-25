from fastapi import APIRouter, Depends
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.tipster import Tipster
from app.models.video import Video
from app.models.idea import GameIdea
from app.models.result import IdeaEvaluation
from app.schemas.dashboard import (
    DashboardResponse, MarketStat, IdeaTypeStat, TipsterStat,
)

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    # Tipsters
    t_total = (await db.execute(select(func.count()).select_from(Tipster))).scalar_one()
    t_active = (await db.execute(
        select(func.count()).select_from(Tipster).where(Tipster.status == "active")
    )).scalar_one()

    # Videos
    v_total = (await db.execute(select(func.count()).select_from(Video))).scalar_one()
    v_analyzed = (await db.execute(
        select(func.count()).select_from(Video).where(Video.status == "analyzed")
    )).scalar_one()

    # Ideas
    i_total = (await db.execute(select(func.count()).select_from(GameIdea))).scalar_one()
    i_actionable = (await db.execute(
        select(func.count()).select_from(GameIdea).where(GameIdea.is_actionable == True)
    )).scalar_one()

    # Evaluations
    eval_rows = (await db.execute(
        select(
            func.count().label("total"),
            func.sum(case((IdeaEvaluation.is_hit == True, 1), else_=0)).label("hits"),
        ).select_from(IdeaEvaluation)
        .where(IdeaEvaluation.evaluation_status == "evaluated")
    )).one()
    i_evaluated = eval_rows.total or 0
    i_hits = int(eval_rows.hits or 0)
    overall_hit_rate = round(i_hits / i_evaluated, 3) if i_evaluated else None

    # Ideas by market
    market_rows = await db.execute(
        select(
            GameIdea.market_type,
            func.count().label("total"),
            func.sum(
                case((IdeaEvaluation.is_hit == True, 1), else_=0)
            ).label("hits"),
        )
        .outerjoin(IdeaEvaluation, IdeaEvaluation.idea_id == GameIdea.id)
        .where(GameIdea.is_actionable == True)
        .group_by(GameIdea.market_type)
        .order_by(func.count().desc())
    )
    ideas_by_market = [
        MarketStat(
            market_type=r.market_type,
            total=r.total,
            hits=int(r.hits or 0),
            hit_rate=round(int(r.hits or 0) / r.total, 3) if r.total else None,
        )
        for r in market_rows.all()
    ]

    # Ideas by type
    type_rows = await db.execute(
        select(GameIdea.idea_type, func.count().label("count"))
        .group_by(GameIdea.idea_type)
        .order_by(func.count().desc())
    )
    ideas_by_type = [
        IdeaTypeStat(idea_type=r.idea_type, count=r.count)
        for r in type_rows.all()
    ]

    # Top tipsters
    tipster_rows = await db.execute(
        select(
            Tipster.id,
            Tipster.name,
            Tipster.display_name,
            func.count(GameIdea.id).label("total_ideas"),
            func.sum(case((GameIdea.is_actionable == True, 1), else_=0)).label("actionable"),
            func.sum(
                case((IdeaEvaluation.evaluation_status == "evaluated", 1), else_=0)
            ).label("evaluated"),
            func.sum(
                case((IdeaEvaluation.is_hit == True, 1), else_=0)
            ).label("hits"),
        )
        .outerjoin(GameIdea, GameIdea.tipster_id == Tipster.id)
        .outerjoin(IdeaEvaluation, IdeaEvaluation.idea_id == GameIdea.id)
        .group_by(Tipster.id, Tipster.name, Tipster.display_name)
        .order_by(func.count(GameIdea.id).desc())
        .limit(10)
    )
    top_tipsters = []
    for r in tipster_rows.all():
        ev = int(r.evaluated or 0)
        hits = int(r.hits or 0)
        top_tipsters.append(TipsterStat(
            id=r.id,
            name=r.name,
            display_name=r.display_name,
            total_ideas=int(r.total_ideas or 0),
            actionable_ideas=int(r.actionable or 0),
            evaluated_ideas=ev,
            hits=hits,
            hit_rate=round(hits / ev, 3) if ev else None,
        ))

    return DashboardResponse(
        total_tipsters=t_total,
        active_tipsters=t_active,
        total_videos=v_total,
        analyzed_videos=v_analyzed,
        total_ideas=i_total,
        actionable_ideas=i_actionable,
        evaluated_ideas=i_evaluated,
        overall_hit_rate=overall_hit_rate,
        ideas_by_market=ideas_by_market,
        ideas_by_type=ideas_by_type,
        top_tipsters=top_tipsters,
    )

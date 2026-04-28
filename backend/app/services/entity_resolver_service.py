"""Serviço de resolução de entidades esportivas.

Dado um nome de time vindo da transcrição (ex: "São Paulo", "Spfc", "SPFC"),
tenta encontrar o registro correspondente em `teams` via `team_aliases`.
Se não encontrar, cria um novo time e alias.

Mesmo processo para competições e jogos.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sport import Team, TeamAlias, Competition, Game


class EntityResolverService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Times ──────────────────────────────────────────────────────────────

    async def resolve_team(self, raw_name: str) -> Team:
        """Retorna o Team correspondente ao nome, criando se necessário."""
        normalized = self._normalize_name(raw_name)

        # Busca por alias exato
        result = await self.db.execute(
            select(TeamAlias).where(TeamAlias.alias == normalized)
        )
        alias = result.scalar_one_or_none()
        if alias:
            team_result = await self.db.execute(
                select(Team).where(Team.id == alias.team_id)
            )
            return team_result.scalar_one()

        # Busca por nome principal (fuzzy simples)
        result = await self.db.execute(
            select(Team).where(Team.name.ilike(f"%{normalized}%"))
        )
        team = result.scalar_one_or_none()
        if team:
            # Registra o alias para próximas vezes
            self.db.add(TeamAlias(team_id=team.id, alias=normalized, source="extraction"))
            await self.db.flush()
            return team

        # Cria novo time + alias
        team = Team(name=raw_name.strip())
        self.db.add(team)
        await self.db.flush()
        self.db.add(TeamAlias(team_id=team.id, alias=normalized, source="extraction"))
        await self.db.flush()
        return team

    # ── Competições ────────────────────────────────────────────────────────

    async def resolve_competition(self, raw_name: str | None) -> Competition | None:
        if not raw_name:
            return None
        normalized = self._normalize_name(raw_name)
        result = await self.db.execute(
            select(Competition).where(Competition.name.ilike(f"%{normalized}%"))
        )
        comp = result.scalar_one_or_none()
        if comp:
            return comp
        comp = Competition(name=raw_name.strip())
        self.db.add(comp)
        await self.db.flush()
        return comp

    # ── Jogos ──────────────────────────────────────────────────────────────

    async def resolve_game(
        self,
        home_name: str,
        away_name: str,
        competition_name: str | None,
        scheduled_date_str: str | None,
    ) -> Game:
        """Retorna o jogo correspondente, criando se necessário."""
        home = await self.resolve_team(home_name)
        away = await self.resolve_team(away_name)
        comp = await self.resolve_competition(competition_name)

        scheduled_at = self._parse_date(scheduled_date_str)

        # Tenta encontrar jogo existente (mesmo dia + times)
        if scheduled_at:
            result = await self.db.execute(
                select(Game).where(
                    Game.home_team_id == home.id,
                    Game.away_team_id == away.id,
                    Game.scheduled_at >= scheduled_at.replace(hour=0, minute=0, second=0),
                    Game.scheduled_at < scheduled_at.replace(hour=23, minute=59, second=59),
                )
            )
            game = result.scalar_one_or_none()
            if game:
                return game

        game = Game(
            home_team_id=home.id,
            away_team_id=away.id,
            competition_id=comp.id if comp else None,
            scheduled_at=scheduled_at,
            status="scheduled",
        )
        self.db.add(game)
        await self.db.flush()
        return game

    # ── Helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Lowercase, sem acentos, sem pontuação especial."""
        try:
            from unidecode import unidecode
            name = unidecode(name)
        except ImportError:
            pass
        name = name.lower().strip()
        name = re.sub(r"[^\w\s]", "", name)
        name = re.sub(r"\s+", " ", name)
        return name

    @staticmethod
    def _parse_date(date_str: str | None) -> datetime | None:
        from datetime import date, timedelta
        if not date_str:
            return None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                dt = datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
                # If the LLM returned a year more than 60 days in the past, assume
                # it guessed the wrong year and try advancing by 1 or 2 years.
                today = datetime.now(tz=timezone.utc).date()
                delta = (today - dt.date()).days
                if delta > 60:
                    for years_ahead in (1, 2):
                        candidate = dt.replace(year=dt.year + years_ahead)
                        if (candidate.date() - today).days >= -7:
                            dt = candidate
                            break
                return dt
            except ValueError:
                continue
        return None

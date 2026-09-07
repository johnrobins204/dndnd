from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from dndnd.models import Character, Game, Quest, SessionRun, SessionRunStatus


@dataclass(frozen=True)
class TableGame:
    key: str
    kind: str
    name: str
    status: str
    session_count: int
    turn_count: int
    active_session_title: str


class SessionRepository:
    def list_for_campaign(self, session: Session, campaign_id: int) -> list[SessionRun]:
        return list(
            session.scalars(
                select(SessionRun)
                .where(SessionRun.campaign_id == campaign_id)
                .options(
                    selectinload(SessionRun.character),
                    selectinload(SessionRun.quest),
                    selectinload(SessionRun.entries),
                )
                .order_by(SessionRun.created_at.desc())
            )
        )

    def list_active_for_campaign(
        self, session: Session, campaign_id: int
    ) -> list[SessionRun]:
        return list(
            session.scalars(
                select(SessionRun)
                .where(
                    SessionRun.campaign_id == campaign_id,
                    SessionRun.status == SessionRunStatus.ACTIVE,
                )
                .options(
                    selectinload(SessionRun.character),
                    selectinload(SessionRun.quest),
                    selectinload(SessionRun.entries),
                )
                .order_by(SessionRun.created_at.desc())
            )
        )

    def list_games_for_campaign(
        self, session: Session, campaign_id: int
    ) -> list[TableGame]:
        runs = self.list_for_campaign(session, campaign_id)
        characters = list(
            session.scalars(
                select(Character)
                .where(Character.campaign_id == campaign_id)
                .order_by(Character.name)
            )
        )
        quests = list(
            session.scalars(
                select(Quest)
                .where(Quest.campaign_id == campaign_id)
                .order_by(Quest.title)
            )
        )
        games: list[TableGame] = []
        for character in characters:
            linked_runs = [run for run in runs if run.character_id == character.id]
            active_run = next(
                (run for run in linked_runs if run.status == SessionRunStatus.ACTIVE),
                None,
            )
            games.append(
                TableGame(
                    key=f"character:{character.id}",
                    kind="Character",
                    name=character.name,
                    status="Running" if active_run else "Ready",
                    session_count=len(linked_runs),
                    turn_count=sum(len(run.entries) for run in linked_runs),
                    active_session_title=active_run.title if active_run else "",
                )
            )
        for quest in quests:
            linked_runs = [run for run in runs if run.quest_id == quest.id]
            active_run = next(
                (run for run in linked_runs if run.status == SessionRunStatus.ACTIVE),
                None,
            )
            games.append(
                TableGame(
                    key=f"quest:{quest.id}",
                    kind="Quest",
                    name=quest.title,
                    status="Running" if active_run else quest.status,
                    session_count=len(linked_runs),
                    turn_count=sum(len(run.entries) for run in linked_runs),
                    active_session_title=active_run.title if active_run else "",
                )
            )
        return games

    def get(self, session: Session, session_id: int) -> SessionRun | None:
        return session.scalar(
            select(SessionRun)
            .where(SessionRun.id == session_id)
            .options(
                selectinload(SessionRun.character),
                selectinload(SessionRun.quest),
                selectinload(SessionRun.entries),
            )
        )

    def get_or_create_active_for_game(self, session: Session, game: Game) -> SessionRun:
        active_run = session.scalar(
            select(SessionRun)
            .where(
                SessionRun.game_id == game.id,
                SessionRun.status == SessionRunStatus.ACTIVE,
            )
            .options(
                selectinload(SessionRun.character),
                selectinload(SessionRun.quest),
                selectinload(SessionRun.entries),
            )
            .order_by(SessionRun.created_at.desc())
        )
        if active_run is not None:
            return active_run
        run = SessionRun(
            campaign_id=game.campaign_id,
            game_id=game.id,
            character_id=game.character_id,
            quest_id=game.quest_id,
            title=game.name,
            status=SessionRunStatus.ACTIVE,
            started_at=datetime.now(),
        )
        session.add(run)
        session.flush()
        return run

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from dndnd.models import (
    Campaign,
    Character,
    Game,
    GameCharacter,
    GameStatus,
    Quest,
    SessionRun,
)


@dataclass(frozen=True)
class CharacterGameOption:
    key: str
    label: str
    campaign_id: int
    character_id: int


@dataclass(frozen=True)
class QuestGameOption:
    key: str
    label: str
    campaign_id: int
    quest_id: int


class GameRepository:
    def list_active(self, session: Session) -> list[Game]:
        return list(
            session.scalars(
                select(Game)
                .where(Game.status == GameStatus.ACTIVE)
                .options(
                    selectinload(Game.campaign),
                    selectinload(Game.character),
                    selectinload(Game.quest),
                    selectinload(Game.character_links).selectinload(
                        GameCharacter.character
                    ),
                    selectinload(Game.session_runs),
                )
                .order_by(Game.created_at.desc())
            )
        )

    def get_active(self, session: Session, game_id: int) -> Game | None:
        return session.scalar(
            select(Game)
            .where(Game.id == game_id, Game.status == GameStatus.ACTIVE)
            .options(
                selectinload(Game.campaign),
                selectinload(Game.character),
                selectinload(Game.quest),
                selectinload(Game.character_links).selectinload(
                    GameCharacter.character
                ),
                selectinload(Game.session_runs).selectinload(SessionRun.entries),
            )
        )

    def list_character_options(self, session: Session) -> list[CharacterGameOption]:
        rows = session.execute(
            select(Campaign, Character)
            .join(Character, Character.campaign_id == Campaign.id)
            .order_by(Campaign.name, Character.name)
        )
        return [
            CharacterGameOption(
                key=f"{campaign.id}:{character.id}",
                label=f"{campaign.name} · {character.name}",
                campaign_id=campaign.id,
                character_id=character.id,
            )
            for campaign, character in rows
        ]

    def list_character_options_for_campaign(
        self, session: Session, campaign_id: int
    ) -> list[CharacterGameOption]:
        rows = session.execute(
            select(Campaign, Character)
            .join(Character, Character.campaign_id == Campaign.id)
            .where(Campaign.id == campaign_id)
            .order_by(Character.name)
        )
        return [
            CharacterGameOption(
                key=str(character.id),
                label=character.name,
                campaign_id=campaign.id,
                character_id=character.id,
            )
            for campaign, character in rows
        ]

    def list_quest_options_for_campaign(
        self, session: Session, campaign_id: int
    ) -> list[QuestGameOption]:
        rows = session.execute(
            select(Campaign, Quest)
            .join(Quest, Quest.campaign_id == Campaign.id)
            .where(Campaign.id == campaign_id)
            .order_by(Quest.title)
        )
        return [
            QuestGameOption(
                key=str(quest.id),
                label=quest.title,
                campaign_id=campaign.id,
                quest_id=quest.id,
            )
            for campaign, quest in rows
        ]

    def create(
        self,
        session: Session,
        name: str,
        campaign_id: int,
        character_id: int,
        character_ids: list[int] | None = None,
        quest_id: int | None = None,
    ) -> Game:
        game = Game(
            name=name,
            campaign_id=campaign_id,
            character_id=character_id,
            quest_id=quest_id,
            status=GameStatus.ACTIVE,
        )
        selected_character_ids = list(
            dict.fromkeys([character_id, *(character_ids or [])])
        )
        for selected_character_id in selected_character_ids:
            game.character_links.append(
                GameCharacter(character_id=selected_character_id)
            )
        session.add(game)
        session.flush()
        return game

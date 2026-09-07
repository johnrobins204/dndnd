from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from dndnd.models import Character, Item, Location, Quest


class QuestRepository:
    def list_for_campaign(self, session: Session, campaign_id: int) -> list[Quest]:
        return list(
            session.scalars(
                select(Quest)
                .where(Quest.campaign_id == campaign_id)
                .order_by(Quest.title)
            )
        )

    def list_items_for_campaign(self, session: Session, campaign_id: int) -> list[Item]:
        return list(
            session.scalars(
                select(Item).where(Item.campaign_id == campaign_id).order_by(Item.name)
            )
        )

    def list_characters_for_campaign(
        self, session: Session, campaign_id: int
    ) -> list[Character]:
        return list(
            session.scalars(
                select(Character)
                .where(Character.campaign_id == campaign_id)
                .order_by(Character.name)
            )
        )

    def list_locations_for_campaign(
        self, session: Session, campaign_id: int
    ) -> list[Location]:
        return list(
            session.scalars(
                select(Location)
                .where(Location.campaign_id == campaign_id)
                .order_by(Location.name)
            )
        )

    def get_builder(self, session: Session, quest_id: int) -> Quest | None:
        return session.scalar(
            select(Quest)
            .where(Quest.id == quest_id)
            .options(
                selectinload(Quest.chapters),
                selectinload(Quest.objectives),
                selectinload(Quest.triggers),
                selectinload(Quest.rewards),
                selectinload(Quest.item_links),
                selectinload(Quest.npc_links),
            )
        )

from sqlalchemy import select
from sqlalchemy.orm import Session

from dndnd.models import Campaign

STARTER_CAMPAIGN_NAME = "The Lantern March"
STARTER_CAMPAIGN_SUMMARY = "A new campaign waits for its first mark in the chronicle."


class CampaignRepository:
    def list_all(self, session: Session) -> list[Campaign]:
        return list(session.scalars(select(Campaign).order_by(Campaign.name)))

    def ensure_starter(self, session: Session) -> Campaign:
        campaign = session.scalar(select(Campaign).order_by(Campaign.id).limit(1))
        if campaign is not None:
            return campaign
        return self.create(session, STARTER_CAMPAIGN_NAME, STARTER_CAMPAIGN_SUMMARY)

    def get(self, session: Session, campaign_id: int) -> Campaign | None:
        return session.get(Campaign, campaign_id)

    def create(self, session: Session, name: str, summary: str = "") -> Campaign:
        campaign = Campaign(name=name, summary=summary)
        session.add(campaign)
        session.flush()
        return campaign

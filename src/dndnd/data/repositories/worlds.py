import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from dndnd.models import Location, WorldDraft, WorldDraftChange, WorldProfile


class WorldRepository:
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

    def list_draft_changes_for_campaign(
        self, session: Session, campaign_id: int
    ) -> list[WorldDraftChange]:
        return list(
            session.scalars(
                select(WorldDraftChange)
                .where(WorldDraftChange.campaign_id == campaign_id)
                .order_by(WorldDraftChange.created_at.desc())
            )
        )

    def get_profile(self, session: Session, campaign_id: int) -> WorldProfile | None:
        return session.scalar(
            select(WorldProfile).where(WorldProfile.campaign_id == campaign_id)
        )

    def get_draft(self, session: Session, campaign_id: int) -> WorldDraft | None:
        return session.scalar(
            select(WorldDraft).where(WorldDraft.campaign_id == campaign_id)
        )

    def save_draft(
        self,
        session: Session,
        campaign_id: int,
        answers: dict[str, str],
        current_step: int,
        is_reviewing: bool,
        review_opened: bool = False,
    ) -> WorldDraft:
        draft = self.get_draft(session, campaign_id)
        if draft is None:
            draft = WorldDraft(campaign_id=campaign_id)
            session.add(draft)
        saved_answers = dict(answers)
        saved_answers["_review_opened"] = "true" if review_opened else "false"
        draft.answers_json = json.dumps(saved_answers)
        draft.current_step = current_step
        draft.is_reviewing = is_reviewing
        draft.updated_at = datetime.now()
        session.flush()
        return draft

    def delete_draft(self, session: Session, campaign_id: int) -> None:
        draft = self.get_draft(session, campaign_id)
        if draft is not None:
            session.delete(draft)
            session.flush()

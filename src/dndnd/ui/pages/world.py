"""World page boundary.

The deterministic builder and canonical acceptance flow remain in app.py
briefly while their persistence and guidance services are extracted.
"""

from sqlalchemy.orm import Session

from dndnd.models import Campaign


def render(session: Session, campaign: Campaign) -> None:
    from dndnd.app import world_page

    world_page(session, campaign)

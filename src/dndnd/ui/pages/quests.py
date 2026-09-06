"""Quest page boundary.

The quest builder remains in app.py temporarily while its draft and domain
services are extracted behind this route.
"""

from sqlalchemy.orm import Session

from dndnd.models import Campaign


def render(session: Session, campaign: Campaign) -> None:
    from dndnd.app import quests_page

    quests_page(session, campaign)

"""Party page boundary.

The implementation remains in app.py temporarily while its nested character
workflows are extracted into domain services. This module owns the page route.
"""

from sqlalchemy.orm import Session

from dndnd.models import Campaign


def render(session: Session, campaign: Campaign) -> None:
    from dndnd.app import party_page

    party_page(session, campaign)

from dataclasses import dataclass


@dataclass(frozen=True)
class WorldCheck:
    severity: str
    message: str


def check_world_draft(draft: dict[str, str]) -> list[WorldCheck]:
    checks: list[WorldCheck] = []
    geography = draft.get("geography", "").casefold()
    starting_problem = draft.get("starting_problem", "").strip()
    fantastic_rule = draft.get("fantastic_rule", "").casefold()
    premise = draft.get("premise", "").strip()
    power_holders = draft.get("power_holders", "").strip()

    if not premise:
        checks.append(
            WorldCheck("missing", "Add a premise so later suggestions have a creative anchor.")
        )
    if not starting_problem:
        checks.append(WorldCheck("missing", "Add a starting problem so the world is playable."))
    if not power_holders:
        checks.append(WorldCheck("missing", "Name at least one power holder or faction."))
    if fantastic_rule and not any(
        marker in fantastic_rule for marker in ("cost", "limit", "forbid", "danger", "price")
    ):
        checks.append(
            WorldCheck(
                "challenge",
                "The fantastic rule has a capability but no visible cost or limitation yet.",
            )
        )
    if any(word in geography for word in ("isolated", "impassable", "cut off", "no route")) and any(
        word in geography for word in ("trade", "merchant", "caravan", "frequent travel")
    ):
        checks.append(
            WorldCheck(
                "contradiction",
                (
                    "The geography describes isolation alongside active trade or travel; "
                    "explain the route or choose which pressure dominates."
                ),
            )
        )
    if not checks:
        checks.append(
            WorldCheck("ready", "No obvious completeness or contradiction checks are waiting.")
        )
    return checks
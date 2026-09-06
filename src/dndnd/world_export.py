from collections.abc import Mapping

from dndnd.world_checks import WorldCheck


def build_world_brief(draft: Mapping[str, str], checks: list[WorldCheck]) -> str:
    sections = [
        f"# {draft.get('world_name', 'Unnamed world')}",
        "",
        f"## Premise\n{draft.get('premise', 'Not recorded')}",
        f"## Tone\n{draft.get('mood', 'Not recorded')}",
        f"## Scope\n{draft.get('scope', 'Not recorded')}",
        f"## Starting Region\n{draft.get('starting_region', 'Not recorded')}",
        f"## Geography\n{draft.get('geography', 'Not recorded')}",
        f"## History\n{draft.get('turning_point', 'Not recorded')}",
        f"## Power And Society\n{draft.get('power_holders', 'Not recorded')}",
        f"## Everyday Life\n{draft.get('everyday_life', 'Not recorded')}",
        f"## The Fantastic\n{draft.get('fantastic_rule', 'Not recorded')}",
        f"## Starting Situation\n{draft.get('starting_problem', 'Not recorded')}",
        "## Readiness Notes",
        "\n".join(f"- **{check.severity.title()}:** {check.message}" for check in checks),
    ]
    return "\n\n".join(sections) + "\n"

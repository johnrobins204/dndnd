from dndnd.prompting import build_world_guidance_prompt


class WorldGuide:
    """Build bounded world guidance requests; callers decide acceptance."""

    def build_prompt(self, mode: str, step_name: str, answers: dict[str, str], existing_world: str = "") -> str:
        return build_world_guidance_prompt(
            mode=mode,
            step_name=step_name,
            answers=answers,
            existing_world=existing_world,
        )

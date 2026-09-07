import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from dndnd.models import (
    Character,
    QuestObjectiveStatus,
    SessionEntryKind,
)


@dataclass(frozen=True)
class VoiceConfig:
    key: str
    label: str
    instruction: str


VOICE_CONFIGS = {
    "dm_voice": VoiceConfig(
        key="dm_voice",
        label="DM voice",
        instruction=(
            "Respond in the dungeon master's table voice: sensory, immediate, playable, "
            "and addressed to the player without revealing hidden analysis."
        ),
    ),
    "dm_analysis": VoiceConfig(
        key="dm_analysis",
        label="DM analysis and workflow",
        instruction=(
            "Respond as the dungeon master's private analysis: clarify intent, identify "
            "likely checks or consequences, and propose the next practical table step."
        ),
    ),
    "player_voice": VoiceConfig(
        key="player_voice",
        label="Player voice",
        instruction=(
            "Respond in the player's character voice: first person, grounded in the "
            "provided character context, with no out-of-character mechanics unless asked."
        ),
    ),
    "player_journal": VoiceConfig(
        key="player_journal",
        label="Player journal article",
        instruction=(
            "Respond as a player-facing journal article: reflective, chronological, "
            "and suitable to save as an in-world campaign record."
        ),
    ),
}


@dataclass(frozen=True)
class NarratorVoiceParams:
    tone: str
    dm_persona: str
    verbosity: str
    sensory_focus: str
    consequence_level: str


# Tunable inputs for the DM voice narrator pass. Adjust these to coach tone/output.
DM_VOICE_PARAMS = NarratorVoiceParams(
    tone="Grounded and immersive, with a touch of dry wit.",
    dm_persona="A seasoned dungeon master who respects player agency.",
    verbosity="Moderate: two to four sentences.",
    sensory_focus="Sight and sound, with texture when it heightens tension.",
    consequence_level="Serious but not gratuitous; consequences land without dwelling on gore.",
)


@dataclass(frozen=True)
class PromptStage:
    name: str
    model: str
    prompt: str
    raw_response: str
    parsed_response: str
    stripped_preamble: str | None = None


@dataclass(frozen=True)
class PartyMemberStatus:
    name: str
    class_name: str
    level: int
    current_hp: int
    max_hp: int
    condition: str


@dataclass(frozen=True)
class TurnSummary:
    turn_number: int
    scene: str
    quest_title: str | None
    quest_goal: str
    party: list[PartyMemberStatus]


CHARACTER_INCLUDE_PATTERN = re.compile(r"/character\s+([^/\n]+)", re.IGNORECASE)

PREAMBLE_LEAD_INS = (
    "here's your response",
    "here is your response",
    "here's the narration",
    "here is the narration",
    "sure, here's",
    "sure here's",
    "certainly,",
    "okay, here's",
    "here's what happens",
    "here is what happens",
    "here's the analysis",
    "here is the analysis",
)


def strip_preamble(text: str) -> tuple[str, str | None]:
    """Detect and strip leading meta-commentary while preserving real narrative."""
    stripped = text.strip()
    if len(stripped) > 1 and stripped[0] == stripped[-1] and stripped[0] in {'"', "'"}:
        return stripped[1:-1].strip(), None

    lower_stripped = stripped.lower()
    for lead_in in PREAMBLE_LEAD_INS:
        prefix = f"{lead_in}:"
        if lower_stripped.startswith(prefix):
            cleaned = stripped[len(prefix) :].strip()
            return cleaned, stripped[: len(prefix)]

    parts = stripped.split("\n\n", 1)
    if len(parts) != 2:
        return stripped, None

    head, rest = parts
    head_single = head.strip()
    if "\n" in head_single or len(head_single) > 80:
        return stripped, None

    lower_head = head_single.lower()
    if lower_head.startswith(PREAMBLE_LEAD_INS):
        return rest.strip(), head_single

    if head_single.endswith(":") and any(
        marker in lower_head for marker in ("response", "narration", "outcome")
    ):
        return rest.strip(), head_single

    return stripped, None


def character_include_names(text: str) -> list[str]:
    return [match.strip() for match in CHARACTER_INCLUDE_PATTERN.findall(text) if match.strip()]


def character_prompt_data(character: Character) -> dict[str, object]:
    sheet = character.sheet
    return {
        "id": character.id,
        "name": character.name,
        "kind": character.kind,
        "ancestry": character.ancestry,
        "class_name": character.class_name,
        "level": character.level,
        "armor_class": character.armor_class,
        "hit_points": {"current": character.current_hp, "maximum": character.max_hp},
        "notes": character.notes,
        "sheet": None
        if sheet is None
        else {
            "background": sheet.background,
            "alignment": sheet.alignment,
            "speed": sheet.speed,
            "proficiency_bonus": sheet.proficiency_bonus,
            "passive_perception": sheet.passive_perception,
            "hit_dice": sheet.hit_dice,
            "spellcasting_ability": sheet.spellcasting_ability,
            "notes": sheet.notes,
        },
        "abilities": [
            {
                "name": ability.ability_name,
                "score": ability.score,
                "modifier": ability.modifier,
                "save_bonus": ability.save_bonus,
            }
            for ability in character.abilities
        ],
        "features": [
            {
                "name": feature.name,
                "category": feature.category,
                "source": feature.source,
                "description": feature.description,
            }
            for feature in character.features
        ],
    }


def _truncate(s: str, n: int) -> str:
    if s is None:
        return ""
    return s if len(s) <= n else s[: n - 1] + "…"


def _compact_json(obj) -> str:
    # compact, deterministic JSON (no spaces)
    return json.dumps(obj, separators=(",", ":"), sort_keys=True)


def _minimal_character_data(character) -> dict[str, Any]:
    # Whitelist the fields the model needs; keep strings truncated
    data: dict[str, Any] = character_prompt_data(character)
    hit_points = data.get("hit_points") or {}
    return {
        "id": data.get("id"),
        "name": data.get("name"),
        "class": data.get("class_name"),
        "level": data.get("level"),
        "hp": {
            "current": int(hit_points.get("current", 0)),
            "max": max(1, int(hit_points.get("maximum", 1))),
        },
        "status": _truncate(str(data.get("condition", "")), 80),
        "short_notes": _truncate(str(data.get("notes", "")), 120),
    }


def build_game_chat_prompt(
    *,
    game,
    session_run,
    voice_key: str,
    user_input: str,
    max_turns: int = 6,
    max_field_len: int = 240,
) -> str:
    # voice
    voice = VOICE_CONFIGS.get(voice_key, VOICE_CONFIGS["dm_voice"])
    current = game.character

    # minimal character data: keep character_prompt_data but trim large fields
    raw = character_prompt_data(current)
    # If character_prompt_data returns a dict, truncate long string fields
    if isinstance(raw, dict):
        minimal = {}
        for k, v in raw.items():
            if isinstance(v, str):
                minimal[k] = _truncate(v, max_field_len)
            else:
                minimal[k] = v
    else:
        minimal = raw

    included_json = _compact_json(minimal)

    # recent turns: keep last max_turns, truncate each content
    recent_entries = session_run.entries[-max_turns:]
    recent_turns = (
        "\n".join(f"{e.kind}:{_truncate(e.content, max_field_len)}" for e in recent_entries)
        or "None"
    )

    # selected characters (short)
    game_characters = [link.character.name for link in game.character_links] or [current.name]
    selected = ",".join(game_characters)

    # single-line metadata to save tokens
    meta = (
        f"GAME:{game.name}|CAMPAIGN:{game.campaign.name}|"
        f"QUEST:{(game.quest.title if game.quest else 'None')}|CHAR:{current.name}|SEL:{selected}"
    )

    # final compact prompt (short labels, explicit instruction)
    parts = [
        "SYS:DND5e",
        f"VOICE:{voice.label}",
        _truncate(getattr(voice, "instruction", ""), 300),
        meta,
        f"CHAR_JSON:{included_json}",
        f"RECENT:{recent_turns}",
        f"INPUT:{_truncate(user_input, max_field_len)}",
        "INSTR:Use CHAR_JSON as authoritative source; do not invent missing sheet data.",
    ]

    return "\n".join(parts)


def build_game_state_payload(
    *,
    game,
    session_run,
    user_input: str,
    included_characters: Iterable[Any],
    max_turns: int = 6,
) -> dict[str, Any]:
    """Compact, deterministic payload for adjudication and small LLMs."""
    # characters referenced by the game (cache minimal serialization)
    game_chars = [link.character for link in game.character_links] or [game.character]
    char_map = {c.id: _minimal_character_data(c) for c in game_chars}

    included = []
    for c in included_characters:
        # prefer cached if present, otherwise compute minimal
        included.append(char_map.get(c.id) or _minimal_character_data(c))

    recent = [
        {"kind": str(e.kind), "content": _truncate(e.content, 200)}
        for e in session_run.entries[-max_turns:]
    ]

    payload = {
        "game": {
            "name": game.name,
            "campaign": game.campaign.name,
            "quest": (game.quest.title if game.quest else None),
        },
        "characters": list(char_map.values()),
        "included_characters": included,
        "recent_turns": recent,
        "last_action": _truncate(user_input, 300),
    }

    # return compact JSON string if you prefer a single string payload:
    # return _compact_json(payload)
    return payload


def build_turn_summary_compact(*, game, session_run, max_turns: int = 6) -> TurnSummary:
    quest = game.quest
    quest_title = quest.title if quest else None
    quest_goal = "No active quest"
    if quest:
        open_objectives = sorted(
            (o for o in quest.objectives if o.status == QuestObjectiveStatus.OPEN),
            key=lambda o: o.sort_order,
        )
        if open_objectives:
            quest_goal = open_objectives[0].title
        elif getattr(quest, "objective", None):
            quest_goal = quest.objective

    game_chars = [link.character for link in game.character_links] or [game.character]
    party: list[PartyMemberStatus] = []
    for c in game_chars:
        max_hp = max(1, int(c.max_hp or 0))
        current_hp = int(c.current_hp or 0)
        ratio = current_hp / max_hp
        if current_hp <= 0:
            condition = "Down"
        elif ratio <= 0.5:
            condition = "Bloodied"
        else:
            condition = "Healthy"
        party.append(
            PartyMemberStatus(
                name=c.name,
                class_name=c.class_name,
                level=c.level,
                current_hp=current_hp,
                max_hp=max_hp,
                condition=condition,
            )
        )

    turn_number = sum(1 for e in session_run.entries if e.kind == SessionEntryKind.CHAT_INPUT) + 1
    scene = (session_run.current_scene or session_run.title or "No scene set").strip()

    return TurnSummary(
        turn_number=turn_number,
        scene=scene,
        quest_title=quest_title,
        quest_goal=quest_goal,
        party=party,
    )


# Backwards-compatible aliases used by ui/pages/table.py
build_turn_summary = build_turn_summary_compact


def build_adjudicator_prompt(game_state: dict[str, object]) -> str:
    json_payload = json.dumps(game_state, indent=2, sort_keys=True, default=str)
    return "\n\n".join(
        [
            "You are the logic engine for a tabletop RPG. Your task is to analyze "
            "the provided game state JSON and determine the strict, literal "
            "mechanical outcome of the last action taken.",
            "Do not write flavor text, dialogue, or narrative prose. State only "
            "the physical and mechanical facts.",
            f"[Game State]\n{json_payload}",
            (
                "Based on the characters' stats, the turn state, and the last "
                "action taken, determine the following:\n"
                "1. Did the action succeed, fail, or partially succeed?\n"
                "2. Who or what was physically affected?\n"
                "3. What are the immediate mechanical consequences (e.g., damage "
                "taken, items dropped, status effects applied, movement)?"
            ),
            "Output ONLY a concise, bulleted list of the mechanical outcomes.",
            "Do not include preambles, labels, meta-commentary, or lead-ins such as "
            '"Here is the analysis:". Start directly with the first bullet.',
        ]
    )


def build_narrator_prompt(adjudicator_output: str, params: NarratorVoiceParams) -> str:
    return "\n\n".join(
        [
            "You are an expert Dungeon Master running a tabletop RPG. Your task "
            "is to translate a raw mechanical outcome into a compelling "
            "narrative response directed at the player.",
            f"[Mechanical Outcome]\n{adjudicator_output}",
            (
                "[Voice Parameters]\n"
                f"Tone: {params.tone}\n"
                f"Persona: {params.dm_persona}\n"
                f"Verbosity: {params.verbosity}\n"
                f"Sensory Focus: {params.sensory_focus}\n"
                f"Consequence Level: {params.consequence_level}"
            ),
            (
                "Directives:\n"
                '- Write in the second person ("You swing...", "Your spell...").\n'
                "- Adhere strictly to the Voice Parameters. Let the tone and "
                "persona dictate your word choice and attitude.\n"
                "- Include details matching the Sensory Focus.\n"
                "- Scale the graphic intensity or comedic effect based on the "
                "Consequence Level.\n"
                "- Do not alter the facts provided in the Mechanical Outcome. Do "
                "not invent new monsters, items, or locations.\n"
                "- Do not mention mechanics, numbers, or dice rolls. Output only "
                "the narrative prose.\n"
                "- Do not include preambles, labels, meta-commentary, or lead-ins "
                'such as "Here\'s your response:" or "Sure, here is the narration:". '
                "Output must begin directly with the first narrative sentence."
            ),
        ]
    )

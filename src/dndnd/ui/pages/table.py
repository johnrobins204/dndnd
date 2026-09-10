from dndnd.data.repositories.campaigns import CampaignRepository
from dndnd.data.repositories.characters import CharacterRepository
from dndnd.data.repositories.games import GameRepository
from dndnd.data.repositories.sessions import SessionRepository
from dndnd.intelligence.game_chat import (
    PromptStage,
    strip_preamble,
)
from dndnd.models import Game

campaigns = CampaignRepository()
characters = CharacterRepository()
games = GameRepository()
sessions = SessionRepository()


def active_game_label(game: Game) -> str:
    quest_name = game.quest.title if game.quest else "No quest"
    return f"{game.name} · {game.campaign.name} · {quest_name}"


def run_normal_chat(payload, session, game, session_run, voice_key):

    from dndnd.config import get_settings
    from dndnd.intelligence.client import OllamaClient
    from dndnd.intelligence.game_chat import (
        DM_VOICE_PARAMS,
        build_adjudicator_prompt,
        build_game_chat_prompt,
        build_game_state_payload,
        build_narrator_prompt,
    )

    settings = get_settings()
    client = OllamaClient(settings)

    model_name = settings.ollama_model
    stages = []

    if voice_key == "dm_voice":
        # DM voice pipeline
        game_state = build_game_state_payload(
            game=game,
            session_run=session_run,
            user_input=payload,
            included_characters=[],
        )

        adjudicator_prompt = build_adjudicator_prompt(game_state)
        raw_mech = client.generate(adjudicator_prompt)
        mech_text, mech_preamble = strip_preamble(raw_mech)

        narrator_prompt = build_narrator_prompt(
            mech_text,
            DM_VOICE_PARAMS,
            player_intent=payload,
        )
        raw_response = client.generate(narrator_prompt)
        response, preamble = strip_preamble(raw_response)

        stages.append(
            PromptStage(
                name="Adjudicator",
                model=model_name,
                prompt=adjudicator_prompt,
                raw_response=raw_mech,
                parsed_response=mech_text,
                stripped_preamble=mech_preamble,
            )
        )
        stages.append(
            PromptStage(
                name="Narrator",
                model=model_name,
                prompt=narrator_prompt,
                raw_response=raw_response,
                parsed_response=response,
                stripped_preamble=preamble,
            )
        )

    else:
        # regular chat
        prompt = build_game_chat_prompt(
            game=game,
            session_run=session_run,
            voice_key=voice_key,
            user_input=payload,
            included_characters=[],
        )
        raw_response = client.generate(prompt)
        response, preamble = strip_preamble(raw_response)

        stages.append(
            PromptStage(
                name="Response",
                model=model_name,
                prompt=prompt,
                raw_response=raw_response,
                parsed_response=response,
                stripped_preamble=preamble,
            )
        )

    return response, stages

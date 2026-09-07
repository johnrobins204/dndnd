from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from dndnd.domain.characters import CharacterDraft, ability_modifier
from dndnd.models import Character, CharacterAbility, CharacterFeature, CharacterSheet, Item, Player


class CharacterRepository:
    def list_players_for_campaign(self, session: Session, campaign_id: int) -> list[Player]:
        return list(
            session.scalars(
                select(Player).where(Player.campaign_id == campaign_id).order_by(Player.name)
            )
        )

    def list_for_campaign(self, session: Session, campaign_id: int) -> list[Character]:
        return list(
            session.scalars(
                select(Character)
                .where(Character.campaign_id == campaign_id)
                .order_by(Character.name)
            )
        )

    def list_items_for_campaign(self, session: Session, campaign_id: int) -> list[Item]:
        return list(
            session.scalars(select(Item).where(Item.campaign_id == campaign_id).order_by(Item.name))
        )

    def get_workspace(self, session: Session, character_id: int) -> Character | None:
        return session.scalar(
            select(Character)
            .where(Character.id == character_id)
            .options(
                selectinload(Character.abilities),
                selectinload(Character.features),
                selectinload(Character.inventory),
                selectinload(Character.journal_entries),
                selectinload(Character.sheet),
            )
        )

    def find_by_name_for_campaign(
        self, session: Session, campaign_id: int, name: str
    ) -> Character | None:
        characters = session.scalars(
            select(Character)
            .where(Character.campaign_id == campaign_id)
            .options(
                selectinload(Character.abilities),
                selectinload(Character.features),
                selectinload(Character.inventory),
                selectinload(Character.journal_entries),
                selectinload(Character.sheet),
            )
        )
        normalized = name.casefold()
        return next(
            (character for character in characters if character.name.casefold() == normalized),
            None,
        )

    def exists_name_in_campaign(self, session: Session, campaign_id: int, name: str) -> bool:
        normalized = name.casefold()
        count = session.scalar(
            select(func.count())
            .where(Character.campaign_id == campaign_id)
            .where(func.lower(Character.name) == normalized)
        )
        return bool(count and count > 0)

    def create_from_draft(
        self, session: Session, campaign_id: int, draft: CharacterDraft
    ) -> Character:
        character = Character(
            campaign_id=campaign_id,
            player_id=draft.player_id,
            name=draft.name,
            kind=draft.kind,
            ancestry=draft.ancestry,
            class_name=draft.class_name,
            level=draft.level,
            armor_class=draft.derived.armor_class,
            max_hp=draft.derived.max_hp,
            current_hp=draft.derived.max_hp,
            notes=draft.notes,
        )
        character.sheet = CharacterSheet(
            background=draft.background,
            alignment=draft.alignment,
            speed=draft.derived.speed,
            proficiency_bonus=draft.derived.proficiency_bonus,
            passive_perception=draft.derived.passive_perception,
            hit_dice=draft.derived.hit_dice,
            spellcasting_ability=draft.derived.spellcasting_ability,
            ability_score_method=draft.ability_method,
            notes=draft.concept,
        )
        for ability_name, score in draft.ability_scores.items():
            modifier = ability_modifier(score)
            character.abilities.append(
                CharacterAbility(
                    ability_name=ability_name,
                    score=score,
                    modifier=modifier,
                    save_proficient=False,
                    save_bonus=modifier,
                )
            )
        for feature_line in draft.feature_lines:
            feature_name, _, description = feature_line.partition("|")
            character.features.append(
                CharacterFeature(
                    name=feature_name.strip(),
                    description=description.strip(),
                )
            )
        session.add(character)
        return character

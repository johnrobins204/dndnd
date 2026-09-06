# ruff: noqa: E501

from dataclasses import dataclass


@dataclass(frozen=True)
class RuleReference:
    name: str
    summary: str
    wiki_url: str
    official_url: str | None = None


COMBAT_RULES_REFERENCE = RuleReference(
    "Combat-facing character state",
    "Armor Class starts from 10 + Dexterity modifier and can be changed by armor, magic, and features. At level 1, maximum Hit Points use the class hit die maximum plus Constitution modifier. Speed, Proficiency Bonus, and spellcasting ability come from the character's rules choices and are best treated as derived values.",
    "https://forgottenrealms.fandom.com/wiki/Combat",
    "https://www.dndbeyond.com/sources/dnd/br-2024/playing-the-game#Combat",
)


CLASS_REFERENCES = {
    "Barbarian": RuleReference(
        "Barbarian",
        "A Strength-forward martial class built around Rage, weapon mastery, durability, and a primal subclass chosen during advancement.",
        "https://forgottenrealms.fandom.com/wiki/Barbarian",
    ),
    "Bard": RuleReference(
        "Bard",
        "A Charisma-based full spellcaster whose Bardic Inspiration, broad skill access, and adaptable magic support the whole party.",
        "https://forgottenrealms.fandom.com/wiki/Bard",
    ),
    "Cleric": RuleReference(
        "Cleric",
        "A Wisdom-based divine spellcaster with healing and protection tools, Channel Divinity, and a Divine Order that shapes the role.",
        "https://forgottenrealms.fandom.com/wiki/Cleric",
    ),
    "Druid": RuleReference(
        "Druid",
        "A Wisdom-based primal spellcaster with nature magic, Wild Shape, and a druidic subclass that defines its relationship to the wild.",
        "https://forgottenrealms.fandom.com/wiki/Druid",
    ),
    "Fighter": RuleReference(
        "Fighter",
        "A flexible martial specialist with Fighting Style, Second Wind, Action Surge, weapon mastery, and a combat-focused subclass.",
        "https://forgottenrealms.fandom.com/wiki/Fighter",
    ),
    "Monk": RuleReference(
        "Monk",
        "A Dexterity and Wisdom martial artist using Martial Arts, Focus abilities, mobility, and an ascetic subclass.",
        "https://forgottenrealms.fandom.com/wiki/Monk",
    ),
    "Paladin": RuleReference(
        "Paladin",
        "A Charisma-based holy warrior combining heavy-armor combat, Lay on Hands, Divine Smite, a protective aura, and an oath-based subclass.",
        "https://forgottenrealms.fandom.com/wiki/Paladin",
    ),
    "Ranger": RuleReference(
        "Ranger",
        "A martial explorer with wilderness expertise, weapon mastery, spellcasting, and a focused hunting feature that supports a mobile striker role.",
        "https://forgottenrealms.fandom.com/wiki/Ranger",
    ),
    "Rogue": RuleReference(
        "Rogue",
        "A Dexterity-based specialist built around Sneak Attack, Cunning Action, Expertise, skill utility, and tactical subclass features.",
        "https://forgottenrealms.fandom.com/wiki/Rogue",
    ),
    "Sorcerer": RuleReference(
        "Sorcerer",
        "A Charisma-based full spellcaster with innate magic, flexible Metamagic, and a magical origin that shapes the subclass.",
        "https://forgottenrealms.fandom.com/wiki/Sorcerer",
    ),
    "Warlock": RuleReference(
        "Warlock",
        "A Charisma-based pact spellcaster with powerful limited spell slots, Eldritch Invocations, and a patron-defined subclass.",
        "https://forgottenrealms.fandom.com/wiki/Warlock",
    ),
    "Wizard": RuleReference(
        "Wizard",
        "An Intelligence-based arcane spellcaster centered on a spellbook, prepared magic, ritual breadth, and a scholarly subclass.",
        "https://forgottenrealms.fandom.com/wiki/Wizard",
    ),
}


ANCESTRY_REFERENCES = {
    "Aasimar": RuleReference(
        "Aasimar",
        "A celestial-touched species with darkvision, radiant resilience, restorative abilities, and a revelation that manifests at higher level.",
        "https://forgottenrealms.fandom.com/wiki/Aasimar",
    ),
    "Dragonborn": RuleReference(
        "Dragonborn",
        "A draconic species defined by an ancestry-linked Breath Weapon, elemental resistance, and a later draconic flight feature.",
        "https://forgottenrealms.fandom.com/wiki/Dragonborn",
    ),
    "Dwarf": RuleReference(
        "Dwarf",
        "A sturdy subterranean species with darkvision, resilience, extra durability, and stone-focused exploration abilities.",
        "https://forgottenrealms.fandom.com/wiki/Dwarf",
    ),
    "Elf": RuleReference(
        "Elf",
        "A fey-descended species with darkvision, keen senses, resistance to magical sleep, Trance, and a lineage choice.",
        "https://forgottenrealms.fandom.com/wiki/Elf",
    ),
    "Gnome": RuleReference(
        "Gnome",
        "A small, magically resilient species with darkvision, mental defenses, and a lineage that grants additional magical expression.",
        "https://forgottenrealms.fandom.com/wiki/Gnome",
    ),
    "Goliath": RuleReference(
        "Goliath",
        "A giant-descended species with increased speed, powerful build, and a Giant Ancestry feature that changes how it handles challenges.",
        "https://forgottenrealms.fandom.com/wiki/Goliath",
    ),
    "Halfling": RuleReference(
        "Halfling",
        "A small, lucky species with Brave, nimble movement through larger creatures, and a natural talent for avoiding notice.",
        "https://forgottenrealms.fandom.com/wiki/Halfling",
    ),
    "Human": RuleReference(
        "Human",
        "A versatile species with broad skill access, an extra origin feat, and a resourceful feature that rewards improvisation.",
        "https://forgottenrealms.fandom.com/wiki/Human",
    ),
    "Orc": RuleReference(
        "Orc",
        "A hardy species with darkvision, a burst of movement and temporary resilience, and Relentless Endurance against dropping.",
        "https://forgottenrealms.fandom.com/wiki/Orc",
    ),
    "Tiefling": RuleReference(
        "Tiefling",
        "A fiend-touched species with darkvision, innate magical expression, and a Fiendish Legacy that defines its supernatural gifts.",
        "https://forgottenrealms.fandom.com/wiki/Tiefling",
    ),
}

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


@dataclass(frozen=True)
class AncestryTraits:
    speed: int
    bonuses: tuple[tuple[str, int], ...]
    traits: str
    reference: RuleReference | None = None


@dataclass(frozen=True)
class BackgroundBonuses:
    bonuses: tuple[tuple[str, int], ...]
    proficiencies: tuple[str, ...]


CLASS_PRIORITIES: dict[str, tuple[str, ...]] = {
    "Barbarian": ("Strength", "Constitution", "Dexterity", "Wisdom", "Charisma", "Intelligence"),
    "Bard": ("Charisma", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Strength"),
    "Cleric": ("Wisdom", "Charisma", "Constitution", "Intelligence", "Strength", "Dexterity"),
    "Druid": ("Wisdom", "Constitution", "Intelligence", "Dexterity", "Charisma", "Strength"),
    "Fighter": ("Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"),
    "Monk": ("Dexterity", "Wisdom", "Constitution", "Strength", "Intelligence", "Charisma"),
    "Paladin": ("Strength", "Charisma", "Constitution", "Wisdom", "Intelligence", "Dexterity"),
    "Ranger": ("Dexterity", "Wisdom", "Constitution", "Intelligence", "Strength", "Charisma"),
    "Rogue": ("Dexterity", "Intelligence", "Constitution", "Charisma", "Wisdom", "Strength"),
    "Sorcerer": ("Charisma", "Constitution", "Dexterity", "Intelligence", "Wisdom", "Strength"),
    "Warlock": ("Charisma", "Constitution", "Dexterity", "Wisdom", "Intelligence", "Strength"),
    "Wizard": ("Intelligence", "Dexterity", "Constitution", "Wisdom", "Charisma", "Strength"),
}

ANCESTRY_TRAITS: dict[str, AncestryTraits] = {
    "Aasimar": AncestryTraits(
        speed=30,
        bonuses=(("Charisma", 2), ("Wisdom", 1)),
        traits="Darkvision, Celestial Resistance, Healing Hands, Light Bearer",
        reference=ANCESTRY_REFERENCES["Aasimar"],
    ),
    "Dragonborn": AncestryTraits(
        speed=30,
        bonuses=(("Strength", 2), ("Charisma", 1)),
        traits="Draconic Ancestry, Breath Weapon, Damage Resistance",
        reference=ANCESTRY_REFERENCES["Dragonborn"],
    ),
    "Dwarf": AncestryTraits(
        speed=30,
        bonuses=(("Constitution", 2), ("Wisdom", 1)),
        traits="Darkvision, Dwarven Resilience, Stonecunning",
        reference=ANCESTRY_REFERENCES["Dwarf"],
    ),
    "Elf": AncestryTraits(
        speed=30,
        bonuses=(("Dexterity", 2), ("Intelligence", 1)),
        traits="Darkvision, Fey Ancestry, Trance, Keen Senses",
        reference=ANCESTRY_REFERENCES["Elf"],
    ),
    "Gnome": AncestryTraits(
        speed=30,
        bonuses=(("Intelligence", 2), ("Dexterity", 1)),
        traits="Darkvision, Gnome Cunning",
        reference=ANCESTRY_REFERENCES["Gnome"],
    ),
    "Goliath": AncestryTraits(
        speed=35,
        bonuses=(("Strength", 2), ("Constitution", 1)),
        traits="Natural Athlete, Stone's Endurance, Powerful Build, Large Form",
        reference=ANCESTRY_REFERENCES["Goliath"],
    ),
    "Halfling": AncestryTraits(
        speed=30,
        bonuses=(("Dexterity", 2), ("Charisma", 1)),
        traits="Lucky, Brave, Halfling Nimbleness",
        reference=ANCESTRY_REFERENCES["Halfling"],
    ),
    "Human": AncestryTraits(
        speed=30,
        bonuses=(("Strength", 1), ("Dexterity", 1), ("Constitution", 1)),
        traits="Extra origin feat, Resourceful, Skillful",
        reference=ANCESTRY_REFERENCES["Human"],
    ),
    "Orc": AncestryTraits(
        speed=30,
        bonuses=(("Strength", 2), ("Constitution", 1)),
        traits="Darkvision, Adrenaline Rush, Relentless Endurance",
        reference=ANCESTRY_REFERENCES["Orc"],
    ),
    "Tiefling": AncestryTraits(
        speed=30,
        bonuses=(("Charisma", 2), ("Intelligence", 1)),
        traits="Darkvision, Infernal Legacy, Fire Resistance",
        reference=ANCESTRY_REFERENCES["Tiefling"],
    ),
}

BACKGROUND_OPTIONS = [
    "Acolyte",
    "Artisan",
    "Charlatan",
    "Criminal",
    "Entertainer",
    "Farmer",
    "Guard",
    "Guide",
    "Hermit",
    "Merchant",
    "Noble",
    "Pilgrim",
    "Sage",
    "Sailor",
    "Scribe",
    "Soldier",
    "Wayfarer",
]

BACKGROUND_BONUSES: dict[str, BackgroundBonuses] = {
    "Acolyte": BackgroundBonuses((("Wisdom", 2), ("Intelligence", 1)), ("Insight", "Religion")),
    "Artisan": BackgroundBonuses(
        (("Dexterity", 2), ("Intelligence", 1)), ("Sleight of Hand", "Investigation")
    ),
    "Charlatan": BackgroundBonuses(
        (("Charisma", 2), ("Dexterity", 1)), ("Deception", "Sleight of Hand")
    ),
    "Criminal": BackgroundBonuses(
        (("Dexterity", 2), ("Charisma", 1)), ("Stealth", "Thieves' Tools")
    ),
    "Entertainer": BackgroundBonuses(
        (("Charisma", 2), ("Dexterity", 1)), ("Acrobatics", "Performance")
    ),
    "Farmer": BackgroundBonuses(
        (("Constitution", 2), ("Wisdom", 1)), ("Animal Handling", "Nature")
    ),
    "Guard": BackgroundBonuses((("Strength", 2), ("Wisdom", 1)), ("Athletics", "Perception")),
    "Guide": BackgroundBonuses((("Wisdom", 2), ("Dexterity", 1)), ("Survival", "Perception")),
    "Hermit": BackgroundBonuses((("Wisdom", 2), ("Constitution", 1)), ("Medicine", "Religion")),
    "Merchant": BackgroundBonuses(
        (("Charisma", 2), ("Intelligence", 1)), ("Insight", "Persuasion")
    ),
    "Noble": BackgroundBonuses((("Charisma", 2), ("Intelligence", 1)), ("History", "Persuasion")),
    "Pilgrim": BackgroundBonuses((("Wisdom", 2), ("Constitution", 1)), ("Religion", "Survival")),
    "Sage": BackgroundBonuses((("Intelligence", 2), ("Wisdom", 1)), ("Arcana", "History")),
    "Sailor": BackgroundBonuses((("Dexterity", 2), ("Strength", 1)), ("Athletics", "Perception")),
    "Scribe": BackgroundBonuses(
        (("Intelligence", 2), ("Dexterity", 1)), ("Investigation", "History")
    ),
    "Soldier": BackgroundBonuses(
        (("Strength", 2), ("Constitution", 1)), ("Athletics", "Intimidation")
    ),
    "Wayfarer": BackgroundBonuses((("Dexterity", 2), ("Wisdom", 1)), ("Stealth", "Survival")),
}

HIT_DICE: dict[str, str] = {
    "Barbarian": "d12",
    "Fighter": "d10",
    "Paladin": "d10",
    "Ranger": "d10",
    "Bard": "d8",
    "Cleric": "d8",
    "Druid": "d8",
    "Monk": "d8",
    "Rogue": "d8",
    "Sorcerer": "d6",
    "Wizard": "d6",
    "Warlock": "d8",
}

HIT_DIE_SIZES = {class_name: int(hit_die[1:]) for class_name, hit_die in HIT_DICE.items()}

SPELLCASTING_ABILITIES: dict[str, str] = {
    "Bard": "Charisma",
    "Cleric": "Wisdom",
    "Druid": "Wisdom",
    "Ranger": "Wisdom",
    "Sorcerer": "Charisma",
    "Warlock": "Charisma",
    "Wizard": "Intelligence",
}

STARTING_FEATURES: dict[str, str] = {
    "Barbarian": "Rage | Enter a focused battle fury",
    "Bard": "Bardic Inspiration | Encourage an ally with a die",
    "Cleric": "Channel Divinity | Call on divine power",
    "Druid": "Wild Shape | Take on a natural form",
    "Fighter": "Second Wind | Recover during a fight",
    "Monk": "Martial Arts | Fight with disciplined technique",
    "Paladin": "Lay on Hands | Restore an ally's vitality",
    "Ranger": "Favored Enemy | Pursue a chosen quarry",
    "Rogue": "Sneak Attack | Exploit an opening",
    "Sorcerer": "Innate Sorcery | Unleash inherent magic",
    "Warlock": "Eldritch Invocation | Shape pact-given power",
    "Wizard": "Spellbook | Prepare a studied repertoire",
}

RANDOM_CONCEPTS = [
    "Seeks a lost promise beneath an ordinary life.",
    "Protects a secret that could change the campaign.",
    "Follows an omen no one else can see.",
    "Wants to repay a debt before it comes due.",
    "Is drawn toward danger by an unfinished question.",
    "Carries a charm that points toward an unknown destiny.",
    "Hides a noble past behind a common name.",
    "Owes a favor to a being that collects in dreams.",
]

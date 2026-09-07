# Character Randomizer Delivery

## Requirements

**Outcome:** Polish the DNDND character randomizer so that one-click and guided generation produces level-1 D&D 5e (2024) characters that match the conventions of best-in-class tools: valid ability scores, class-aware placement, ancestry/background bonuses, correct derived statistics, flavorful names, and a clear preview before saving — all while staying local-first.

**Users affected:** DMs rolling NPCs and players quickly drafting PCs.

### Acceptance criteria

1. **Multiple ability-score methods with validation.** Standard array, 4d6 drop lowest, point buy (27 points, scores 8–15), and manual entry are all supported, each with method-specific validation and provenance stored on the sheet.
2. **Class-aware score assignment.** Randomized scores are placed using class priorities (primary ability → secondary/weapon ability → Constitution) instead of a pure shuffle; reroll keeps the same priorities.
3. **Ancestry and background bonuses.** Generated characters apply 2024-style ancestry ability-score increases and baseline traits (e.g., Human +1 to three scores, Goliath 35 ft speed, others +2/+1). Backgrounds grant a fixed +2/+1 ability increase pair and suggested skill/tool proficiencies.
4. **Correct derived values.** AC, max HP, proficiency bonus, passive perception, speed, hit dice, and spellcasting ability are derived from the finalized scores and validated (HP > 0, AC reasonable, etc.).
5. **Collision-free, flavorful names.** Random names avoid duplicates within the campaign and use a small fantasy-name generator rather than a raw slug.
6. **Builder-style UX affordances.** The flow exposes “Regenerate” and “Lock identity/abilities” controls and a preview card before the character is persisted.
7. **Tested and clean.** All generation and derivation logic has focused unit tests with deterministic seeds, and `uv run pytest`, `uv run ruff check .`, and `uv run mypy src` pass.

### Out of scope

- Full equipment, feat, and spell-list automation
- Subclass selection or multi-classing
- Level-up beyond level 1
- External rules API calls or Ollama-driven generation

## Status

- [x] Requirements approved by user
- [x] ADR produced by Enterprise Architect
- [x] Sprint plan produced by Sprint Planner
- [x] Sprint plan signed off by Enterprise Architect
- [x] Implementation completed by Senior Developer
- [x] Final validation passed
- [x] Delivery reported to user

## Artifacts

- ADR: [docs/adr/002-character-randomizer-architecture.md](../docs/adr/002-character-randomizer-architecture.md)
- Sprint plan: [plans/character-randomizer-sprint-plan.md](character-randomizer-sprint-plan.md)
- Architect sign-off: Approved with minor suggestions (incorporated)

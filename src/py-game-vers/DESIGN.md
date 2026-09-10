# Pygame D&D DM Architecture Plan

## Workspace Layout

your_project/
│
├── app/
│   └── main.py
│
├── ui/
│   ├── window.py            # GameWindow, main loop, scene stack
│   ├── scenes.py            # Scene base and concrete scenes
│   ├── widgets.py           # Buttons, labels, inputs, scroll lists, cards
│   ├── styles.py            # colors, fonts, sizes
│   └── panels/
│       ├── __init__.py
│       ├── table_panel.py   # TablePanel
│       ├── chat_panel.py    # ChatPanel
│       ├── character_panel.py # CharacterPanel and CharacterCard
│       └── quest_panel.py   # QuestPanel
│
├── data/
│   ├── models.py
│   └── repos.py
│
├── intelligence/
│   ├── client.py
│   ├── prompt_builders.py
│   └── tools/
│       ├── __init__.py
│       └── narrate.py
│
├── services/
│   ├── game_service.py
│   ├── session_service.py
│   └── tool_service.py
│
├── assets/
│   └── config.py
│
└── README.md


## Package Responsibilities

### app
Bootstrap pygame, wire dependencies, start main loop.

### ui
Pygame rendering, event loop, scenes, widgets.

### data
Domain models and repository interfaces.

### intelligence
LLM client, prompt builders, tool modules.

### services
Business logic orchestrating data + intelligence.

### assets
Static resources and configuration.

## Development Pattern

- UI calls Services
- Services call Repos + Intelligence
- Intelligence calls AIClient + Tools
- Repos read/write game state
- UI renders state returned by Services

## Next Steps

We will build each file one by one:
1. app/main.py
2. ui/window.py
3. ui/scenes.py
4. data/models.py
5. data/repos.py
6. intelligence/client.py
7. intelligence/prompt_builders.py
8. intelligence/tools/narrate.py
9. services/tool_service.py
10. services/session_service.py
11. assets/config.py
12. README.md

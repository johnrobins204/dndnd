from dndnd.world_checks import check_world_draft


def test_world_checks_require_playable_core() -> None:
    checks = check_world_draft({})
    messages = [check.message for check in checks]

    assert any("premise" in message for message in messages)
    assert any("starting problem" in message for message in messages)
    assert any("power holder" in message for message in messages)


def test_world_checks_flag_missing_magic_constraint() -> None:
    checks = check_world_draft(
        {
            "premise": "A frontier where magic is waking.",
            "power_holders": "The Salt Compact",
            "starting_problem": "The bell rings beneath the tide.",
            "fantastic_rule": "Water preserves memories.",
        }
    )

    assert any(check.severity == "challenge" for check in checks)


def test_world_checks_flag_isolation_trade_contradiction() -> None:
    checks = check_world_draft(
        {
            "premise": "A coastal frontier.",
            "power_holders": "The Salt Compact",
            "starting_problem": "A bell rings beneath the tide.",
            "geography": (
                "The coast is isolated and impassable, but frequent trade caravans arrive."
            ),
        }
    )

    assert any(check.severity == "contradiction" for check in checks)

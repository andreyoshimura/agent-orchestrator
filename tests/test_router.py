import unittest

from app.core.router import DEFAULT_PROVIDER_MAX_TOKENS, Router


class RouterResolveMaxTokensTest(unittest.TestCase):
    def test_falls_back_to_hardcoded_default_when_nothing_configured(self) -> None:
        router = Router({})
        self.assertEqual(
            router.resolve_max_tokens("explain-file", "claude"),
            DEFAULT_PROVIDER_MAX_TOKENS,
        )

    def test_uses_global_defaults_when_task_has_no_override(self) -> None:
        router = Router({
            "_defaults": {"provider_max_tokens": 4096},
            "explain-file": {"preferred": "claude", "execution": {}},
        })
        self.assertEqual(router.resolve_max_tokens("explain-file", "claude"), 4096)

    def test_task_level_override_wins_over_global_defaults(self) -> None:
        router = Router({
            "_defaults": {"provider_max_tokens": 4096},
            "explain-file": {
                "preferred": "claude",
                "execution": {"provider_max_tokens": 1024},
            },
        })
        self.assertEqual(router.resolve_max_tokens("explain-file", "claude"), 1024)

    def test_provider_specific_override_wins_over_task_level(self) -> None:
        router = Router({
            "_defaults": {"provider_max_tokens": 4096},
            "explain-file": {
                "preferred": "claude",
                "execution": {
                    "provider_max_tokens": 1024,
                    "provider_max_tokens_by_provider": {"claude": 2048},
                },
            },
        })
        self.assertEqual(router.resolve_max_tokens("explain-file", "claude"), 2048)
        # Provider sem override específico cai no task-level
        self.assertEqual(router.resolve_max_tokens("explain-file", "gemini"), 1024)

    def test_profile_override_wins_over_routing_config(self) -> None:
        router = Router({
            "explain-file": {
                "preferred": "claude",
                "execution": {
                    "provider_max_tokens": 1024,
                    "provider_max_tokens_by_provider": {"claude": 2048},
                },
            },
        })
        profile_overrides = {"explain-file": {"default": 8192}}
        self.assertEqual(
            router.resolve_max_tokens(
                "explain-file", "claude", profile_overrides=profile_overrides
            ),
            8192,
        )

    def test_profile_provider_specific_wins_over_profile_default(self) -> None:
        router = Router({})
        profile_overrides = {
            "default": 4096,
            "explain-file": {
                "default": 8192,
                "by_provider": {"claude": 12000},
            },
        }
        self.assertEqual(
            router.resolve_max_tokens(
                "explain-file", "claude", profile_overrides=profile_overrides
            ),
            12000,
        )
        self.assertEqual(
            router.resolve_max_tokens(
                "explain-file", "gemini", profile_overrides=profile_overrides
            ),
            8192,
        )
        self.assertEqual(
            router.resolve_max_tokens(
                "review-file", "claude", profile_overrides=profile_overrides
            ),
            4096,
        )

    def test_profile_accepts_shorthand_integer_task_override(self) -> None:
        router = Router({"explain-file": {"execution": {"provider_max_tokens": 1024}}})
        profile_overrides = {"explain-file": 6000}
        self.assertEqual(
            router.resolve_max_tokens(
                "explain-file", "claude", profile_overrides=profile_overrides
            ),
            6000,
        )

    def test_invalid_or_non_positive_values_are_ignored(self) -> None:
        router = Router({
            "_defaults": {"provider_max_tokens": 4096},
            "explain-file": {
                "execution": {
                    "provider_max_tokens": "not-a-number",
                    "provider_max_tokens_by_provider": {"claude": -1},
                },
            },
        })
        # Cai no _defaults porque os valores na task são inválidos
        self.assertEqual(router.resolve_max_tokens("explain-file", "claude"), 4096)

    def test_decide_uses_resolved_max_tokens_for_preferred_provider(self) -> None:
        router = Router({
            "explain-file": {
                "preferred": "claude",
                "fallback": ["gemini"],
                "execution": {
                    "provider_max_tokens": 1024,
                    "provider_max_tokens_by_provider": {"claude": 2048},
                },
            },
        })
        decision = router.decide("explain-file")
        self.assertEqual(decision.provider, "claude")
        self.assertEqual(decision.provider_max_tokens, 2048)


if __name__ == "__main__":
    unittest.main()

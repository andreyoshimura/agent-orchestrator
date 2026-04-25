import os
import unittest

from app.providers.config import load_provider_settings


class ProviderConfigTest(unittest.TestCase):
    def test_load_provider_settings_reads_env_configuration(self) -> None:
        old_enabled = os.environ.get("OPENAI_ENABLED")
        old_model = os.environ.get("OPENAI_MODEL")
        old_key = os.environ.get("OPENAI_API_KEY")
        try:
            os.environ["OPENAI_ENABLED"] = "true"
            os.environ["OPENAI_MODEL"] = "gpt-test"
            os.environ["OPENAI_API_KEY"] = "secret"

            settings = load_provider_settings()

            self.assertTrue(settings["openai"].enabled)
            self.assertEqual(settings["openai"].model, "gpt-test")
            self.assertEqual(settings["openai"].api_key, "secret")
            self.assertTrue(settings["openai"].ready_for_live_execution)
        finally:
            _restore_env("OPENAI_ENABLED", old_enabled)
            _restore_env("OPENAI_MODEL", old_model)
            _restore_env("OPENAI_API_KEY", old_key)

    def test_load_provider_settings_supports_gemini_v2_configuration(self) -> None:
        old_enabled = os.environ.get("GEMINI_V2_ENABLED")
        old_model = os.environ.get("GEMINI_V2_MODEL")
        old_key = os.environ.get("GEMINI_V2_API_KEY")
        old_base = os.environ.get("GEMINI_V2_API_BASE")
        try:
            os.environ["GEMINI_V2_ENABLED"] = "true"
            os.environ["GEMINI_V2_MODEL"] = "gemini-2.5-pro"
            os.environ["GEMINI_V2_API_KEY"] = "secret-v2"
            os.environ["GEMINI_V2_API_BASE"] = "https://example.test/gemini"

            settings = load_provider_settings()

            self.assertIn("gemini_v2", settings)
            self.assertTrue(settings["gemini_v2"].enabled)
            self.assertEqual(settings["gemini_v2"].provider_type, "gemini")
            self.assertEqual(settings["gemini_v2"].model, "gemini-2.5-pro")
            self.assertEqual(settings["gemini_v2"].api_key, "secret-v2")
            self.assertEqual(settings["gemini_v2"].api_base, "https://example.test/gemini")
            self.assertTrue(settings["gemini_v2"].ready_for_live_execution)
        finally:
            _restore_env("GEMINI_V2_ENABLED", old_enabled)
            _restore_env("GEMINI_V2_MODEL", old_model)
            _restore_env("GEMINI_V2_API_KEY", old_key)
            _restore_env("GEMINI_V2_API_BASE", old_base)


def _restore_env(name: str, value: str | None) -> None:
    if value is None:
        os.environ.pop(name, None)
        return
    os.environ[name] = value


if __name__ == "__main__":
    unittest.main()

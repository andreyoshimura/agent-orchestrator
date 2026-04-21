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


def _restore_env(name: str, value: str | None) -> None:
    if value is None:
        os.environ.pop(name, None)
        return
    os.environ[name] = value


if __name__ == "__main__":
    unittest.main()

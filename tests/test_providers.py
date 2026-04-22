import unittest
from io import BytesIO
from urllib.error import HTTPError
from unittest.mock import MagicMock, patch

from app.providers import get_provider
from app.providers.base import BaseProvider, ProviderRequest
from app.providers.config import ProviderSettings


class ProviderTest(unittest.TestCase):
    def test_get_provider_returns_registered_provider(self) -> None:
        provider = get_provider(
            "openai",
            ProviderSettings(name="openai", enabled=True, model="", api_key="", api_base=""),
        )
        response = provider.run(ProviderRequest(prompt="hello", metadata={"task_type": "test"}))

        self.assertEqual(response.provider, "openai")
        self.assertEqual(response.status, "stub")
        self.assertEqual(response.output["prompt_length"], 5)
        self.assertEqual(response.output["failure_type"], "configuration")

    def test_get_provider_raises_for_unknown_name(self) -> None:
        with self.assertRaises(KeyError):
            get_provider("missing", ProviderSettings(name="missing", enabled=True, model="", api_key="", api_base=""))

    @patch("app.providers.openai_provider.urllib_request.urlopen")
    def test_openai_provider_uses_live_execution_when_ready(self, mock_urlopen: MagicMock) -> None:
        response_handle = MagicMock()
        response_handle.read.return_value = b'{"id":"resp_123","output_text":"ok"}'
        mock_urlopen.return_value.__enter__.return_value = response_handle

        provider = get_provider(
            "openai",
            ProviderSettings(name="openai", enabled=True, model="gpt-test", api_key="secret", api_base=""),
        )
        response = provider.run(ProviderRequest(prompt="hello", metadata={"task_type": "test"}))

        self.assertEqual(response.status, "completed")
        self.assertEqual(response.output["mode"], "live")
        self.assertEqual(response.output["output_text"], "ok")

    @patch("app.providers.openai_provider.urllib_request.urlopen")
    def test_openai_provider_classifies_http_failure(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = HTTPError(
            url="https://api.openai.com/v1/responses",
            code=400,
            msg="bad request",
            hdrs=None,
            fp=BytesIO(b"bad request"),
        )

        provider = get_provider(
            "openai",
            ProviderSettings(name="openai", enabled=True, model="gpt-test", api_key="secret", api_base=""),
        )
        response = provider.run(ProviderRequest(prompt="hello", metadata={"task_type": "test"}))

        self.assertEqual(response.status, "error")
        self.assertEqual(response.output["failure_type"], "invalid_request")

    @patch("app.providers.claude_provider.urllib_request.urlopen")
    def test_claude_provider_uses_live_execution_when_ready(self, mock_urlopen: MagicMock) -> None:
        response_handle = MagicMock()
        response_handle.read.return_value = b'{"id":"msg_123","content":[{"type":"text","text":"ok claude"}]}'
        mock_urlopen.return_value.__enter__.return_value = response_handle

        provider = get_provider(
            "claude",
            ProviderSettings(name="claude", enabled=True, model="claude-test", api_key="secret", api_base=""),
        )
        response = provider.run(ProviderRequest(prompt="hello", metadata={"task_type": "test"}))

        self.assertEqual(response.status, "completed")
        self.assertEqual(response.output["mode"], "live")
        self.assertEqual(response.output["output_text"], "ok claude")

    @patch("app.providers.claude_provider.urllib_request.urlopen")
    def test_claude_provider_classifies_http_failure(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = HTTPError(
            url="https://api.anthropic.com/v1/messages",
            code=429,
            msg="rate limit",
            hdrs=None,
            fp=BytesIO(b"rate limit"),
        )

        provider = get_provider(
            "claude",
            ProviderSettings(name="claude", enabled=True, model="claude-test", api_key="secret", api_base=""),
        )
        response = provider.run(ProviderRequest(prompt="hello", metadata={"task_type": "test"}))

        self.assertEqual(response.status, "error")
        self.assertEqual(response.output["failure_type"], "rate_limit")

    @patch("app.providers.gemini_provider.urllib_request.urlopen")
    def test_gemini_provider_uses_live_execution_when_ready(self, mock_urlopen: MagicMock) -> None:
        response_handle = MagicMock()
        response_handle.read.return_value = (
            b'{"candidates":[{"content":{"parts":[{"text":"ok gemini"}]}}]}'
        )
        mock_urlopen.return_value.__enter__.return_value = response_handle

        provider = get_provider(
            "gemini",
            ProviderSettings(name="gemini", enabled=True, model="gemini-test", api_key="secret", api_base=""),
        )
        response = provider.run(ProviderRequest(prompt="hello", metadata={"task_type": "test"}))

        self.assertEqual(response.status, "completed")
        self.assertEqual(response.output["mode"], "live")
        self.assertEqual(response.output["output_text"], "ok gemini")

    @patch("app.providers.gemini_provider.urllib_request.urlopen")
    def test_gemini_provider_classifies_http_failure(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = HTTPError(
            url="https://generativelanguage.googleapis.com/v1beta/models/gemini-test:generateContent",
            code=401,
            msg="unauthorized",
            hdrs=None,
            fp=BytesIO(b"unauthorized"),
        )

        provider = get_provider(
            "gemini",
            ProviderSettings(name="gemini", enabled=True, model="gemini-test", api_key="secret", api_base=""),
        )
        response = provider.run(ProviderRequest(prompt="hello", metadata={"task_type": "test"}))

        self.assertEqual(response.status, "error")
        self.assertEqual(response.output["failure_type"], "authorization")

    @patch("app.providers.openai_provider.urllib_request.urlopen")
    def test_openai_provider_handles_invalid_json_response(self, mock_urlopen: MagicMock) -> None:
        response_handle = MagicMock()
        response_handle.read.return_value = b"{invalid"
        mock_urlopen.return_value.__enter__.return_value = response_handle

        provider = get_provider(
            "openai",
            ProviderSettings(name="openai", enabled=True, model="gpt-test", api_key="secret", api_base=""),
        )
        response = provider.run(ProviderRequest(prompt="hello", metadata={"task_type": "test"}))

        self.assertEqual(response.status, "error")
        self.assertEqual(response.output["failure_type"], "temporary")
        self.assertIn("invalid_response_json", response.output["reason"])

    @patch("app.providers.claude_provider.urllib_request.urlopen")
    def test_claude_provider_handles_invalid_json_response(self, mock_urlopen: MagicMock) -> None:
        response_handle = MagicMock()
        response_handle.read.return_value = b"[1,2,3]"
        mock_urlopen.return_value.__enter__.return_value = response_handle

        provider = get_provider(
            "claude",
            ProviderSettings(name="claude", enabled=True, model="claude-test", api_key="secret", api_base=""),
        )
        response = provider.run(ProviderRequest(prompt="hello", metadata={"task_type": "test"}))

        self.assertEqual(response.status, "error")
        self.assertEqual(response.output["failure_type"], "temporary")
        self.assertEqual(response.output["reason"], "invalid_response_shape:top_level_not_object")

    def test_base_provider_run_handles_internal_exception(self) -> None:
        class BrokenProvider(BaseProvider):
            name = "broken"

            def _run(self, request: ProviderRequest):  # type: ignore[override]
                raise RuntimeError("boom")

        provider = BrokenProvider(
            ProviderSettings(name="broken", enabled=True, model="n/a", api_key="n/a", api_base="")
        )
        response = provider.run(ProviderRequest(prompt="hello", metadata={"task_type": "test"}))

        self.assertEqual(response.status, "error")
        self.assertEqual(response.output["failure_type"], "temporary")
        self.assertIn("provider_internal_error", response.output["reason"])


if __name__ == "__main__":
    unittest.main()

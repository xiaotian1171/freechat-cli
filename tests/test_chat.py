"""Tests for the native Pollinations legacy endpoint client."""

import json
import unittest

from freechat_cli.chat import ChatClient
from freechat_cli.config import Config, DEFAULT_BASE_URL


class FakeLegacyResponse:
    """Minimal file-like object emulating urlopen() responses."""

    def __init__(self, lines, decode_errors=False):
        self._lines = lines
        self._decode_errors = decode_errors

    def read(self):
        return "\n".join(self._lines).encode("utf-8")

    def __iter__(self):
        for line in self._lines:
            bad = "\udcff" if self._decode_errors else ""
            yield (line + bad).encode("utf-8", errors="replace") if self._decode_errors else (
                line + "\n"
            ).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def make_client():
    return ChatClient(config=Config())


class TestLegacyDetection(unittest.TestCase):
    def test_default_base_url_is_legacy(self):
        self.assertEqual(DEFAULT_BASE_URL, "https://text.pollinations.ai/")
        client = make_client()
        self.assertTrue(client._is_legacy_pollinations())

    def test_openai_compatible_url_is_not_legacy(self):
        config = Config(base_url="https://api.openai.com/v1")
        client = ChatClient(config=config)
        self.assertFalse(client._is_legacy_pollinations())

    def test_trailing_slash_variants(self):
        for url in ("https://text.pollinations.ai", "https://text.pollinations.ai/"):
            self.assertTrue(ChatClient(config=Config(base_url=url))._is_legacy_pollinations())


class TestLegacyRequestBody(unittest.TestCase):
    def test_sync_request_shape(self):
        req = make_client()._legacy_request(
            [{"role": "user", "content": "hi"}], stream=False
        )
        body = json.loads(req.data.decode("utf-8"))
        self.assertEqual(body["messages"], [{"role": "user", "content": "hi"}])
        self.assertNotIn("stream", body)
        self.assertNotIn("model", body)  # anonymous tier: no model field
        self.assertEqual(req.full_url, "https://text.pollinations.ai/")
        self.assertNotIn("Accept", req.headers)

    def test_stream_request_shape(self):
        req = make_client()._legacy_request(
            [{"role": "user", "content": "hi"}], stream=True
        )
        body = json.loads(req.data.decode("utf-8"))
        self.assertTrue(body["stream"])
        self.assertNotIn("model", body)
        self.assertTrue(
            any(k.lower() == "user-agent" for k in req.headers), "User-Agent must be set"
        )
        self.assertEqual(req.headers.get("Accept"), "text/event-stream")


class TestSSEParsing(unittest.TestCase):
    def _collect(self, sse_lines):
        client = make_client()
        chunks = list(client._legacy_consume_sse(FakeLegacyResponse(sse_lines)))
        return chunks, client.conversation.last_response

    def test_content_deltas_are_yielded(self):
        lines = [
            'data: {"choices":[{"delta":{"content":""}}]}',
            'data: {"choices":[{"delta":{"reasoning":"thinking"}}]}',
            'data: {"choices":[{"delta":{"content":"Hel"}}]}',
            'data: {"choices":[{"delta":{"content":"lo"}}]}',
            "data: [DONE]",
        ]
        chunks, full = self._collect(lines)
        self.assertEqual("".join(chunks), "Hello")
        self.assertEqual(full, "Hello")

    def test_reasoning_only_chunks_are_skipped(self):
        chunks, full = self._collect(['data: {"choices":[{"delta":{"reasoning":"hmm"}}]}'])
        self.assertEqual(chunks, [])
        self.assertEqual(full, "")

    def test_error_payload_raises(self):
        with self.assertRaises(RuntimeError):
            list(self._collect(['data: {"error": "402 Payment Required"}']))

    def test_malformed_lines_are_ignored(self):
        chunks, full = self._collect(
            ["data: not-json", "", ": keep-alive comment", 'data: {"choices":[{"delta":{"content":"ok"}}]}']
        )
        self.assertEqual("".join(chunks), "ok")

    def test_empty_stream_yields_nothing(self):
        chunks, full = self._collect([])
        self.assertEqual(chunks, [])
        self.assertEqual(full, "")


class TestPlainParsing(unittest.TestCase):
    def _consume(self, body_text):
        client = make_client()
        chunks = list(client._legacy_consume_plain(FakeLegacyResponse([body_text])))
        return "".join(chunks)

    def test_plain_text_passthrough(self):
        self.assertEqual(self._consume("OK"), "OK")

    def test_json_error_raises(self):
        body = json.dumps({"error": "Payment Required", "status": 402})
        with self.assertRaises(RuntimeError):
            self._consume(body)


if __name__ == "__main__":
    unittest.main()

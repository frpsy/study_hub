"""gemini_client의 폴백·재시도 동작을 네트워크 없이 확인한다."""
import json
import os
import sys
import unittest
import urllib.error
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts", "ai_review"))
import gemini_client as gc  # noqa: E402


def _http(code, body=b""):
    return urllib.error.HTTPError("u", code, "x", {}, __import__("io").BytesIO(body))


def _ok(text):
    return {"candidates": [{"content": {"parts": [{"text": text}]}}]}


class GeminiClientTest(unittest.TestCase):
    def setUp(self):
        p = mock.patch.object(gc.time, "sleep", lambda s: None)
        p.start()
        self.addCleanup(p.stop)

    def test_quota_error_moves_to_next_model(self):
        calls = []

        def post(url, body, key, timeout):
            calls.append(url)
            if "gemini-a" in url:
                raise _http(429)
            return _ok("정상")

        with mock.patch.object(gc, "_post", post):
            r = gc.generate("q", models=["gemini-a", "gemini-b"], key="k", log=lambda m: None)
        self.assertEqual((r.text, r.model), ("정상", "gemini-b"))
        self.assertLessEqual(sum("gemini-a" in c for c in calls), 2)  # 429는 오래 붙잡지 않는다

    def test_empty_404_is_retried_then_succeeds(self):
        seq = [_http(404), _http(404)]

        def post(url, body, key, timeout):
            if seq:
                raise seq.pop(0)
            return _ok("복구")

        with mock.patch.object(gc, "_post", post):
            r = gc.generate("q", models=["gemini-a"], key="k", log=lambda m: None)
        self.assertEqual((r.text, r.model), ("복구", "gemini-a"))

    def test_falls_back_to_interactions_route(self):
        def post(url, body, key, timeout):
            if "generateContent" in url:
                raise _http(503)
            return {"steps": [{"type": "model_output", "content": [{"type": "text", "text": "대체경로"}]}]}

        with mock.patch.object(gc, "_post", post):
            r = gc.generate("q", models=["gemini-a"], key="k", log=lambda m: None)
        self.assertEqual((r.text, r.route), ("대체경로", "interactions"))

    def test_permanent_error_is_not_retried(self):
        calls = []

        def post(url, body, key, timeout):
            calls.append(url)
            raise _http(403, b"denied")

        with mock.patch.object(gc, "_post", post):
            with self.assertRaises(gc.GeminiError):
                gc.generate("q", models=["gemini-a"], key="k", log=lambda m: None)
        self.assertEqual(len(calls), 2)  # 경로당 1회, 재시도 없음

    def test_broken_json_is_retried(self):
        seq = ["{깨짐", json.dumps([1])]

        def post(url, body, key, timeout):
            return _ok(seq.pop(0))

        with mock.patch.object(gc, "_post", post):
            r = gc.generate("q", json_mode=True, models=["gemini-a"], key="k", log=lambda m: None)
        self.assertEqual(json.loads(r.text), [1])

    def test_all_fail_raises(self):
        with mock.patch.object(gc, "_post", side_effect=_http(503)):
            with self.assertRaises(gc.GeminiError):
                gc.generate("q", models=["gemini-a"], key="k", log=lambda m: None)


if __name__ == "__main__":
    unittest.main()

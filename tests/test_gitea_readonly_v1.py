import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from orion_v3.modules.gitea_readonly_v1 import GiteaReadonly, _segment

class FakeResponse:
    status = 200
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()
    def read(self, amount):
        return self.payload[:amount]
    def __enter__(self): return self
    def __exit__(self, *args): pass

class TestGiteaReadonly(unittest.TestCase):
    def test_strict_loopback(self):
        for origin in ("https://example.org:3000", "http://192.168.0.1:3000",
                       "http://localhost:3000/root", "http://user:pw@localhost:3000",
                       "http://localhost:3000?x=1"):
            with self.assertRaises(ValueError):
                GiteaReadonly(origin)
        GiteaReadonly("http://127.0.0.1:3000")

    def test_reject_unsafe_segments(self):
        for x in ("../etc", ".", "..", "hello/world", "a\\b", "a?b"):
            with self.assertRaises(ValueError): _segment(x)

    @patch("urllib.request.build_opener")
    def test_get_only_and_minimal_repo_projection(self, mock_opener):
        opener = mock_opener.return_value
        opener.open.return_value = FakeResponse([{"owner":{"login":"owner"},
            "name":"repo","default_branch":"main","private":True,"secret_field":"not exposed"}])
        x = GiteaReadonly("http://127.0.0.1:3000", token="example-test-token")
        result = x.list_repositories()
        self.assertEqual(result,[{"owner":"owner","name":"repo","default_branch":"main","private":True}])
        req = opener.open.call_args.args[0]
        self.assertEqual(req.get_method(), "GET")
        self.assertTrue(req.full_url.endswith("/api/v1/user/repos?page=1&limit=50"))
        self.assertEqual(req.headers["Authorization"],"token example-test-token")

    @patch("urllib.request.build_opener")
    def test_sha_required_and_truncation_flag(self, mock_opener):
        x = GiteaReadonly("http://localhost:3000")
        with self.assertRaises(ValueError): x.tree("o","r","main")
        mock_opener.return_value.open.return_value = FakeResponse({"sha":"a"*40,"truncated":True,
                "tree":[{"path":"one.py","type":"blob","sha":"b"*40}]})
        out=x.tree("o","r","a"*40)
        self.assertTrue(out["truncated"])
        self.assertEqual(out["tree"][0]["path"],"one.py")

if __name__=="__main__": unittest.main()

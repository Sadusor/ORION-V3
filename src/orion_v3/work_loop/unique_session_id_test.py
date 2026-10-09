import re
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from .unique_session_id import new_session_id

class UniqueSessionIdTest(unittest.TestCase):
    def test_format_and_utc(self):
        s = new_session_id(datetime(2026,10,9,1,2,3,456789,tzinfo=timezone.utc), "a"*32)
        self.assertEqual(s,"20261009T010203456789Z-"+"a"*32)
    def test_distinct_same_timestamp(self):
        now=datetime(2026,10,9,tzinfo=timezone.utc)
        self.assertNotEqual(new_session_id(now,"a"*32),new_session_id(now,"b"*32))
    def test_entropy_uses_crypto_source(self):
        with patch("orion_v3.work_loop.unique_session_id.token_hex",return_value="f"*32) as rng:
            self.assertTrue(new_session_id().endswith("-"+"f"*32))
            rng.assert_called_once_with(16)
    def test_reject_naive_time(self):
        with self.assertRaises(ValueError):
            new_session_id(datetime(2026,10,9))
    def test_reject_invalid_entropy(self):
        for e in ("abc","G"*32,"x"*32,"0"*33):
            with self.subTest(e=e),self.assertRaises(ValueError):
                new_session_id(entropy=e)
    def test_safe_filesystem_chars(self):
        self.assertRegex(new_session_id(),r"^[0-9]{8}T[0-9]{12}Z-[0-9a-f]{32}$")

if __name__=="__main__":
    unittest.main()

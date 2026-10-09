import unittest
from orion_v3.work_loop.free_quota_monitor import classify,safe_record

class FreeQuotaTests(unittest.TestCase):
 def test_unknown_without_quota(self):
  s=classify(provider="openrouter",model="free",usage={"total_tokens":900})
  self.assertEqual(s.status,"UNKNOWN")
  self.assertEqual(s.used_tokens,900)
  self.assertIsNone(s.remaining_tokens)
 def test_cooldown(self):
  self.assertEqual(classify(provider="p",model="m",rate_limited=True).status,"COOLDOWN")
 def test_exhausted_tokens(self):
  self.assertEqual(classify(provider="p",model="m",quota={"remaining_tokens":0}).status,"EXHAUSTED")
 def test_exhausted_requests(self):
  self.assertEqual(classify(provider="p",model="m",quota={"remaining_requests":0}).status,"EXHAUSTED")
 def test_low(self):
  self.assertEqual(classify(provider="p",model="m",quota={"remaining_tokens":10,"token_limit":100}).status,"LOW")
 def test_available(self):
  self.assertEqual(classify(provider="p",model="m",quota={"remaining_tokens":80,"token_limit":100}).status,"AVAILABLE")
 def test_request_availability(self):
  self.assertEqual(classify(provider="p",model="m",quota={"remaining_requests":5}).status,"AVAILABLE")
 def test_no_bool_quota(self):
  self.assertEqual(classify(provider="p",model="m",quota={"remaining_tokens":True}).status,"UNKNOWN")
 def test_no_negative(self):
  self.assertEqual(classify(provider="p",model="m",quota={"remaining_tokens":-1}).status,"UNKNOWN")
 def test_no_secret_in_record(self):
  record=safe_record(classify(provider="p",model="m"))
  self.assertNotIn("api_key",record)
  self.assertNotIn("raw_response",record)
 def test_invalid(self):
  with self.assertRaises(ValueError):classify(provider="",model="m")
 def test_reset(self):
  s=classify(provider="p",model="m",quota={"remaining_requests":0,"reset_at":"2026-10-10T00:00:00Z"})
  self.assertEqual(s.reset_at,"2026-10-10T00:00:00Z")
if __name__=="__main__":unittest.main()

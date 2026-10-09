import unittest
from orion_v3.work_loop.provider_quota_telemetry import observe

class TelemetryTests(unittest.TestCase):
 def test_unknown(self):
  self.assertEqual(observe(provider="openrouter",model="m")["status"],"UNKNOWN")
 def test_usage_not_balance(self):
  r=observe(provider="openrouter",model="m",response={"usage":{"total_tokens":400}})
  self.assertEqual(r["used_tokens"],400)
  self.assertIsNone(r["remaining_tokens"])
  self.assertEqual(r["status"],"UNKNOWN")
 def test_prompt_completion_fallback(self):
  r=observe(provider="gemini",model="m",response={"usage":{"prompt_tokens":2,"completion_tokens":3}})
  self.assertEqual(r["used_tokens"],5)
 def test_groq_remaining(self):
  r=observe(provider="groq",model="m",headers={"x-ratelimit-remaining-requests":"8"})
  self.assertEqual(r["remaining_requests"],8)
 def test_groq_low(self):
  r=observe(provider="groq",model="m",headers={"x-ratelimit-remaining-tokens":"10","x-ratelimit-limit-tokens":"100"})
  self.assertEqual(r["status"],"LOW")
 def test_zero(self):
  r=observe(provider="groq",model="m",headers={"x-ratelimit-remaining-requests":"0"})
  self.assertEqual(r["status"],"EXHAUSTED")
 def test_rate_limit(self):
  r=observe(provider="openrouter",model="m",http_status=429)
  self.assertEqual(r["status"],"COOLDOWN")
 def test_retry_after(self):
  r=observe(provider="groq",model="m",http_status=429,headers={"Retry-After":"30"})
  self.assertEqual(r["retry_after_seconds"],30)
  self.assertIsNone(r["reset_at"])
 def test_no_arbitrary_header(self):
  r=observe(provider="groq",model="m",headers={"authorization":"SECRET"})
  self.assertNotIn("SECRET",str(r))
 def test_no_openrouter_groq_header(self):
  r=observe(provider="openrouter",model="m",headers={"x-ratelimit-remaining-tokens":"100"})
  self.assertIsNone(r["remaining_tokens"])
 def test_negative(self):
  r=observe(provider="groq",model="m",headers={"x-ratelimit-remaining-requests":"-1"})
  self.assertIsNone(r["remaining_requests"])
 def test_bad_response(self):
  with self.assertRaises(ValueError):observe(provider="groq",model="m",response=[])
if __name__=="__main__":unittest.main()

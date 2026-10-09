import unittest
from orion_v3.work_loop.provider_health import Health,update_health,is_callable,can_probe
class HealthTests(unittest.TestCase):
 def setUp(self):self.h=Health("gemini","flash")
 def test_unknown_not_callable(self):self.assertFalse(is_callable(self.h,now=100))
 def test_success(self):self.assertTrue(is_callable(update_health(self.h,outcome="SUCCESS",now=100),now=101))
 def test_stale(self):self.assertFalse(is_callable(update_health(self.h,outcome="SUCCESS",now=100),now=90000))
 def test_future(self):self.assertFalse(is_callable(update_health(self.h,outcome="SUCCESS",now=100),now=99))
 def test_rate_limit(self):self.assertEqual(update_health(self.h,outcome="RATE_LIMIT",now=100).cooldown_until,160)
 def test_double_backoff(self):
  a=update_health(self.h,outcome="PROVIDER",now=100)
  b=update_health(a,outcome="PROVIDER",now=200)
  self.assertEqual(b.cooldown_until,320)
 def test_capped_backoff(self):
  a=self.h
  for i in range(10):a=update_health(a,outcome="TRANSPORT",now=100+i)
  self.assertLessEqual(a.cooldown_until,100+10+3600)
 def test_cooldown_blocks(self):
  a=update_health(self.h,outcome="OVERLOADED",now=100)
  self.assertFalse(can_probe(a,now=159))
 def test_cooldown_expires(self):
  a=update_health(self.h,outcome="OVERLOADED",now=100)
  self.assertTrue(can_probe(a,now=160))
 def test_auth_unavailable(self):self.assertEqual(update_health(self.h,outcome="AUTH",now=100).status,"UNAVAILABLE")
 def test_no_credentials(self):self.assertEqual(update_health(self.h,outcome="NO_CREDENTIAL",now=100).status,"UNAVAILABLE")
 def test_request_unavailable(self):self.assertEqual(update_health(self.h,outcome="REQUEST",now=100).status,"UNAVAILABLE")
 def test_malformed(self):self.assertEqual(update_health(self.h,outcome="MALFORMED_RESPONSE",now=100).status,"UNAVAILABLE")
 def test_unknown_outcome(self):
  with self.assertRaises(ValueError):update_health(self.h,outcome="UNKNOWN",now=100)
 def test_invalid_time(self):
  with self.assertRaises(ValueError):update_health(self.h,outcome="SUCCESS",now=-1)
 def test_success_resets(self):
  a=update_health(self.h,outcome="RATE_LIMIT",now=100)
  b=update_health(a,outcome="SUCCESS",now=200)
  self.assertEqual((b.failures,b.cooldown_until),(0,0))
 def test_success_at_zero_not_callable(self):
  self.assertFalse(is_callable(update_health(self.h,outcome="SUCCESS",now=0),now=1))
 def test_no_probe_during_cooldown(self):
  a=update_health(self.h,outcome="RATE_LIMIT",now=100)
  self.assertFalse(can_probe(a,now=101))
if __name__=="__main__":unittest.main()

import unittest
from unittest.mock import patch
from orion_v3.work_loop.unified_cloud_adapter import dispatch,DispatchError
from orion_v3.work_loop.existing_reviewer_slot_adapter import ReviewerInvocationError
from orion_v3.work_loop.openrouter_text_adapter import CloudRequestError

class AdapterIntegrationTests(unittest.TestCase):
 def args(self,**kw):
  a=dict(provider="groq",model="m",prompt="proposal",stop_requested=lambda:False,
         connector=object(),reviewer_id="r")
  a.update(kw)
  return a
 def test_groq(self):
  with patch("orion_v3.work_loop.unified_cloud_adapter.invoke_existing",return_value="ok") as call:
   r=dispatch(**self.args())
   self.assertEqual(r["text"],"ok")
   self.assertEqual(call.call_args.kwargs["reviewer_id"],"r")
 def test_gemini(self):
  with patch("orion_v3.work_loop.unified_cloud_adapter.invoke_existing",return_value="yes"):
   self.assertEqual(dispatch(**self.args(provider="gemini"))["provider"],"gemini")
 def test_openrouter(self):
  with patch("orion_v3.work_loop.unified_cloud_adapter.completion",return_value={"provider":"openrouter","model":"m","text":"ok"}) as call:
   r=dispatch(**self.args(provider="openrouter",connector=None,reviewer_id=None,api_key="placeholder"))
   self.assertEqual(r["text"],"ok")
   self.assertEqual(call.call_args.kwargs["api_key"],"placeholder")
 def test_stop_before(self):
  with self.assertRaises(DispatchError) as ctx:dispatch(**self.args(stop_requested=lambda:True))
  self.assertEqual(ctx.exception.category,"STOPPED")
 def test_stop_after_openrouter(self):
  checks=iter([False,True])
  with patch("orion_v3.work_loop.unified_cloud_adapter.completion",return_value={"text":"ok"}):
   with self.assertRaises(DispatchError) as ctx:
    dispatch(**self.args(provider="openrouter",connector=None,reviewer_id=None,api_key="placeholder",stop_requested=lambda:next(checks)))
  self.assertEqual(ctx.exception.category,"STOPPED")
 def test_provider_error(self):
  with patch("orion_v3.work_loop.unified_cloud_adapter.invoke_existing",side_effect=ReviewerInvocationError("PROVIDER")):
   with self.assertRaises(DispatchError) as ctx:dispatch(**self.args())
  self.assertEqual(ctx.exception.category,"PROVIDER")
 def test_rate_limit(self):
  with patch("orion_v3.work_loop.unified_cloud_adapter.completion",side_effect=CloudRequestError("RATE_LIMIT")):
   with self.assertRaises(DispatchError) as ctx:dispatch(**self.args(provider="openrouter",connector=None,reviewer_id=None,api_key="placeholder"))
  self.assertEqual(ctx.exception.category,"RATE_LIMIT")
 def test_wrong_adapter(self):
  with self.assertRaises(DispatchError):dispatch(**self.args(provider="openrouter"))
 def test_missing_reviewer(self):
  with self.assertRaises(DispatchError):dispatch(**self.args(reviewer_id=None))
 def test_no_private_key_in_donor(self):
  with self.assertRaises(DispatchError):dispatch(**self.args(api_key="placeholder"))
 def test_unknown_provider(self):
  with self.assertRaises(DispatchError) as ctx:dispatch(**self.args(provider="unknown"))
  self.assertEqual(ctx.exception.category,"UNSUPPORTED_PROVIDER")
 def test_empty_prompt(self):
  with self.assertRaises(ValueError):dispatch(**self.args(prompt=""))
 def test_oversized_prompt(self):
  with self.assertRaises(ValueError):dispatch(**self.args(prompt="a"*12001))
 def test_missing_stop(self):
  with self.assertRaises(ValueError):dispatch(**self.args(stop_requested=None))
 def test_timeout(self):
  with self.assertRaises(ValueError):dispatch(**self.args(timeout=61))
if __name__=="__main__":unittest.main()

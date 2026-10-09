import unittest
from orion_v3.work_loop.connector_collision_guard import invoke_collision_safe, ConnectorStateCollision
from orion_v3.work_loop.unified_cloud_adapter import dispatch, DispatchError

class FakeConnector:
 def __init__(self,collision=False):
  self.collision=collision
  self.starts=0
  self.stops=0
 def start(self,prompt,ids,popup_windows=False):
  self.starts+=1
  if self.collision:raise FileExistsError("sensitive-private-path")
 def view(self):
  return {"state":"completed","reviewers":[{"reviewer_id":"r1","state":"completed","output":"valid proposal"}]}
 def stop(self):self.stops+=1

class CollisionTests(unittest.TestCase):
 def test_collision_is_categorized(self):
  c=FakeConnector(True)
  with self.assertRaises(ConnectorStateCollision) as x:
   invoke_collision_safe(connector=c,reviewer_id="r1",prompt="plan",stop_requested=lambda:False,timeout=1)
  self.assertEqual(x.exception.category,"CONNECTOR_STATE_COLLISION")
  self.assertNotIn("sensitive-private-path",str(x.exception))
  self.assertEqual(c.starts,1)
  self.assertEqual(c.stops,0)
 def test_unified_fail_closed(self):
  c=FakeConnector(True)
  with self.assertRaises(DispatchError) as x:
   dispatch(provider="groq",model="m",prompt="plan",stop_requested=lambda:False,connector=c,reviewer_id="r1",timeout=1)
  self.assertEqual(x.exception.category,"CONNECTOR_STATE_COLLISION")
  self.assertEqual(c.starts,1)
 def test_success_preserved(self):
  c=FakeConnector()
  r=dispatch(provider="groq",model="m",prompt="plan",stop_requested=lambda:False,connector=c,reviewer_id="r1",timeout=1)
  self.assertEqual(r["text"],"valid proposal")
 def test_stop_before_start(self):
  c=FakeConnector()
  with self.assertRaises(DispatchError) as x:
   dispatch(provider="groq",model="m",prompt="plan",stop_requested=lambda:True,connector=c,reviewer_id="r1",timeout=1)
  self.assertEqual(x.exception.category,"STOPPED")
  self.assertEqual(c.starts,0)
if __name__=="__main__":unittest.main()

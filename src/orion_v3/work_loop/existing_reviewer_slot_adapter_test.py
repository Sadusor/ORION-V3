import unittest
from orion_v3.work_loop.existing_reviewer_slot_adapter import invoke_existing,ReviewerInvocationError

class Fake:
 def __init__(self, states):
  self.states=list(states);self.stopped=0;self.started=[]
 def start(self,prompt,ids,popup_windows=False):self.started.append((prompt,ids,popup_windows))
 def view(self):return self.states.pop(0) if len(self.states)>1 else self.states[0]
 def stop(self):self.stopped+=1
def state(status="completed",output="proposal",rid="r"):
 return {"state":"completed" if status=="completed" else "running",
         "reviewers":[{"reviewer_id":rid,"state":status,"output":output}]}
class AdapterTests(unittest.TestCase):
 def call(self,c,**kwargs):
  return invoke_existing(connector=c,reviewer_id="r",prompt="proposal only",
                         stop_requested=lambda:False,**kwargs)
 def test_success(self):
  c=Fake([state()]);self.assertEqual(self.call(c),"proposal")
  self.assertEqual(c.started[0][1],["r"])
 def test_failure(self):
  c=Fake([state("failed")])
  with self.assertRaises(ReviewerInvocationError) as ctx:self.call(c)
  self.assertEqual(ctx.exception.category,"PROVIDER")
 def test_wrong_attribution(self):
  with self.assertRaises(ReviewerInvocationError) as ctx:self.call(Fake([state(rid="wrong")]))
  self.assertEqual(ctx.exception.category,"MALFORMED_RESPONSE")
 def test_empty(self):
  with self.assertRaises(ReviewerInvocationError):self.call(Fake([state(output="")]))
 def test_stop_before(self):
  c=Fake([state()])
  with self.assertRaises(ReviewerInvocationError) as ctx:
   invoke_existing(connector=c,reviewer_id="r",prompt="p",stop_requested=lambda:True)
  self.assertEqual(ctx.exception.category,"STOPPED")
  self.assertEqual(c.started,[])
 def test_stop_during(self):
  c=Fake([{"state":"running","reviewers":[]}])
  checks=[False,True]
  def stop():return checks.pop(0) if checks else True
  with self.assertRaises(ReviewerInvocationError):
   invoke_existing(connector=c,reviewer_id="r",prompt="p",stop_requested=stop)
  self.assertEqual(c.stopped,1)
 def test_timeout(self):
  c=Fake([{"state":"running","reviewers":[]}])
  ticks=iter([0,0,2])
  with self.assertRaises(ReviewerInvocationError) as ctx:
   self.call(c,timeout=1,clock=lambda:next(ticks),sleep=lambda _:None)
  self.assertEqual(ctx.exception.category,"TRANSPORT")
  self.assertEqual(c.stopped,1)
if __name__=="__main__":unittest.main()

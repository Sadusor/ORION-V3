import unittest
from src.orion_v3.modules.history_archive_indexed_boundary_v1 import IndexedArchiveBoundaryV1

class FakeBoundary:
    def __init__(self):
        self.success=True
    def sync(self,*,device_token,body):
        return (200,{"ok":True}) if self.success else (403,{"ok":False})
    def owner_delete(self,*,owner_token,conversation_id,project_id):
        return (200,{"ok":True}) if self.success else (403,{"ok":False})

class FakeIndex:
    def __init__(self):
        self.events=[]
        self.fail=False
    def after_archive_commit(self):
        if self.fail: raise RuntimeError("index unavailable")
        self.events.append("sync")
    def after_owner_deletion(self):
        if self.fail: raise RuntimeError("index unavailable")
        self.events.append("delete")

class IndexedBoundaryTests(unittest.TestCase):
    def test_index_after_committed_sync_and_deletion_only(self):
        boundary=FakeBoundary()
        index=FakeIndex()
        bridge=IndexedArchiveBoundaryV1(boundary=boundary,index_sync=index)
        self.assertEqual(bridge.sync(device_token="test",body={})[0],200)
        self.assertEqual(bridge.owner_delete(owner_token="test",conversation_id="c",project_id="p")[0],200)
        self.assertEqual(index.events,["sync","delete"])
        boundary.success=False
        self.assertEqual(bridge.sync(device_token="test",body={})[0],403)
        self.assertEqual(bridge.owner_delete(owner_token="test",conversation_id="c",project_id="p")[0],403)
        self.assertEqual(index.events,["sync","delete"])
    def test_derived_index_failures_are_not_reported_as_rolled_back(self):
        index=FakeIndex()
        index.fail=True
        bridge=IndexedArchiveBoundaryV1(boundary=FakeBoundary(),index_sync=index)
        code,reply=bridge.sync(device_token="test",body={})
        self.assertEqual(code,503)
        self.assertTrue(reply["archive_committed"])
        self.assertTrue(reply["index_needs_rebuild"])
        code,reply=bridge.owner_delete(owner_token="test",conversation_id="c",project_id="p")
        self.assertEqual(code,503)
        self.assertTrue(reply["deletion_committed"])
        self.assertTrue(reply["index_needs_rebuild"])

if __name__=="__main__":
    unittest.main()

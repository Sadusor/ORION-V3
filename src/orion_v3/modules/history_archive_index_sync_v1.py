"""Archive-index synchronization adapter; deliberately not wired to production.

Call only after a successfully committed archive write or authorized deletion.
The existing project-scoped FTS projection is rebuilt from archive truth.
"""
from __future__ import annotations
from .history_archive_search_projection_v1 import ArchiveSearchProjectionV1

class ArchiveIndexSyncV1:
    def __init__(self, archive_path, index_path):
        self.projection = ArchiveSearchProjectionV1(archive_path, index_path)
    def after_archive_commit(self):
        return {"indexed_messages":self.projection.refresh(),"status":"indexed"}
    def after_owner_deletion(self):
        return {"indexed_messages":self.projection.refresh(),"status":"deleted_filtered"}
    def retrieve(self, *, project_id, query, limit=12):
        return self.projection.search(project_id=project_id,query=query,limit=limit)

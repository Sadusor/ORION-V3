"""Read-only production SQLite backup/restore rehearsal, separate backup directory.

Never modifies the source database. Uses SQLite online backup API for WAL safety.
"""
import argparse
import datetime
import hashlib
import json
import pathlib
import sqlite3

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True)
    p.add_argument("--destination-root",required=True)
    args=p.parse_args()
    source=pathlib.Path(args.source).resolve(strict=True)
    base=pathlib.Path(args.destination_root).resolve()
    if source.suffix.lower() not in (".db",".sqlite3",".sqlite"):
        raise ValueError("Source must be a SQLite database")
    if not source.is_file() or source.stat().st_size==0:
        raise ValueError("Source missing or empty")
    base.mkdir(parents=True,exist_ok=True)
    if base==source.parent or source==base or base in source.parents:
        raise ValueError("Backup must be separate from source")
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest=base/("orion-chat-"+stamp+".sqlite3")
    if dest.exists():
        raise FileExistsError(dest)
    src=sqlite3.connect("file:"+str(source).replace("\\","/")+"?mode=ro",uri=True,timeout=20)
    try:
        with sqlite3.connect(str(dest)) as backup:
            src.backup(backup)
        # Rehearse restoration into a *second* independent temporary database.
        restored=base/("orion-restore-rehearsal-"+stamp+".sqlite3")
        if restored.exists():
            raise FileExistsError(restored)
        with sqlite3.connect(str(dest)) as saved:
            with sqlite3.connect(str(restored)) as check:
                saved.backup(check)
        with sqlite3.connect("file:"+str(restored).replace("\\","/")+"?mode=ro",uri=True) as check:
            status=check.execute("PRAGMA quick_check").fetchone()[0]
            if status!="ok":
                raise RuntimeError("Restore rehearsal integrity check failed: "+status)
        if sha256(dest)!=sha256(restored):
            raise RuntimeError("Backup and restore bytes differ")
        restored.unlink()
        manifest={"source_name":source.name,"backup":str(dest),"sha256":sha256(dest),"bytes":dest.stat().st_size,"restore_rehearsal":"PASS"}
        (base/("orion-chat-"+stamp+".manifest.json")).write_text(json.dumps(manifest,indent=2),encoding="utf-8")
        print("PRODUCTION_PC_SQLITE_ONLINE_BACKUP> PASS")
        print("PRODUCTION_PC_SQLITE_RESTORE_REHEARSAL> PASS")
        print("PRODUCTION_PC_BACKUP_FILE> "+str(dest))
    finally:
        src.close()

if __name__=="__main__":
    main()

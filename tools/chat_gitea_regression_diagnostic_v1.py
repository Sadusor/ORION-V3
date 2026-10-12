"""Read-only ORION chat/Gitea regression diagnostic. No secrets or chat text printed."""
from pathlib import Path
import argparse
import json
import os
import socket
import sqlite3
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import URLError, HTTPError

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def probe_port(port):
    with socket.socket() as s:
        s.settimeout(2)
        try:
            s.connect(("127.0.0.1", port))
            return "LISTENING"
        except OSError:
            return "NOT_LISTENING"

def probe_gitea(port):
    url=f"http://127.0.0.1:{port}/api/v1/version"
    try:
        with build_opener(NoRedirect()).open(Request(url,method="GET"),timeout=3) as response:
            data=json.loads(response.read(2048))
            return "GITEA_API_OK" if isinstance(data,dict) and "version" in data else "UNEXPECTED_API_RESPONSE"
    except HTTPError as e:
        return "HTTP_"+str(e.code)
    except (URLError,ValueError,OSError):
        return "API_UNAVAILABLE"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--state-dir",required=True)
    a=p.parse_args()
    root=Path(a.state_dir)
    print("ORION_CHAT_REGRESSION_DIAGNOSTIC> START")
    for port in (3000,3001,8890):
        print(f"PORT_{port}> {probe_port(port)}")
    for port in (3000,3001):
        print(f"GITEA_API_{port}> {probe_gitea(port)}")
    trace=root/"chat-source-trace.jsonl"
    print("CHAT_SOURCE_TRACE> "+("PRESENT" if trace.is_file() else "MISSING"))
    if trace.is_file():
        try:
            # Tail only; do not disclose prompts, source snippets, or credentials.
            with trace.open("rb") as f:
                f.seek(0,os.SEEK_END)
                size=f.tell()
                f.seek(max(0,size-131072))
                rows=f.read().decode("utf-8","replace").splitlines()
            parsed=[]
            for line in rows[-25:]:
                try:
                    x=json.loads(line)
                    parsed.append({"lookup":x.get("lookup"),"injected":x.get("injected"),
                                   "source_count":len(x.get("source_ids",[])),
                                   "error_classes":[str(v).split(":",1)[-1].split(":",1)[0][:60] for v in x.get("source_errors",[])]})
                except (ValueError,TypeError):
                    continue
            print("CHAT_SOURCE_TRACE_TAIL> "+json.dumps(parsed[-8:]))
        except OSError:
            print("CHAT_SOURCE_TRACE_TAIL> UNREADABLE")
    for name in ("gitea-code-index-v2-full.sqlite3","indexed_documents.sqlite3"):
        f=root/name
        print(name.upper().replace(".","_")+"> "+("PRESENT" if f.is_file() else "MISSING"))
    print("ORION_CHAT_REGRESSION_DIAGNOSTIC> COMPLETE")
if __name__=="__main__":
    main()

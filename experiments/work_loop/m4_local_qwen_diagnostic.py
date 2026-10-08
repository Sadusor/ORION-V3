"""Local Qwen 9B diagnostics, no cloud dependency, no secret logging."""
from __future__ import annotations
import json
import urllib.request
import urllib.error

BASE="http://127.0.0.1:11434"
try:
    with urllib.request.urlopen(BASE+"/api/tags",timeout=8) as response:
        tags=json.load(response)
except Exception as exc:
    print("M4_QWEN_DIAG> OLLAMA_UNREACHABLE",type(exc).__name__)
    raise SystemExit(2)
names=[str(x.get("name") or "") for x in tags.get("models",[]) if isinstance(x,dict)]
matches=[n for n in names if "qwen" in n.lower() and ("9b" in n.lower())]
print("M4_QWEN_DIAG> QWEN_9B_INSTALLED",len(matches))
if not matches:raise SystemExit(3)
model=next((n for n in matches if "orion" in n.lower()),matches[0])
print("M4_QWEN_DIAG> SELECTED_MODEL",model)
payload=json.dumps({"model":model,"prompt":"Reply with one short sentence: Qwen is ready.",
                    "stream":False,"think":False,"options":{"num_predict":240,"temperature":0}}).encode()
try:
    req=urllib.request.Request(BASE+"/api/generate",data=payload,
                               headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=75) as response:
        data=json.load(response)
except urllib.error.HTTPError as exc:
    print("M4_QWEN_DIAG> HTTP_STATUS",exc.code)
    raise SystemExit(4)
except Exception as exc:
    print("M4_QWEN_DIAG> GENERATE_FAILED",type(exc).__name__)
    raise SystemExit(5)
answer=str(data.get("response") or "")
thinking=str(data.get("thinking") or "")
print("M4_QWEN_DIAG> RESPONSE_NONEMPTY",bool(answer.strip()))
print("M4_QWEN_DIAG> THINKING_NONEMPTY",bool(thinking.strip()))
print("M4_QWEN_DIAG> DONE",bool(data.get("done")))
if not answer.strip():raise SystemExit(6)
print("M4_QWEN_DIAG> LOCAL_GENERATION_PASS")

$ErrorActionPreference='Stop'
Write-Host 'ORION_GITEA_REAL_CODEMAP> BEGIN'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$env:PYTHONPATH=Join-Path $root 'src'
$python=@'
import json
from orion_v3.modules.gitea_readonly_v1 import GiteaReadonly
from orion_v3.modules.gitea_codebase_map_v1 import create_codebase_map
api=GiteaReadonly("http://127.0.0.1:3001")
repo=api.repository("MyGitea","ORION-V3")
branches=api.branches("MyGitea","ORION-V3")
branch=next((b for b in branches if b["name"]==repo["default_branch"]),None)
if not branch: raise RuntimeError("Default branch missing from Gitea")
ref=branch["commit_id"]
tree=api.tree("MyGitea","ORION-V3",ref)
report=create_codebase_map(tree,owner="MyGitea",repository="ORION-V3",commit_sha=ref)
print("GITEA_REPO> MyGitea/ORION-V3")
print("GITEA_SOURCE_COMMIT> "+ref)
print("GITEA_CODE_FILES> "+str(report["file_count"]))
print("GITEA_EXTENSIONS> "+json.dumps(report["extensions"],sort_keys=True))
print("GITEA_TREE_COMPLETE> "+str(not tree["truncated"]))
assert report["file_count"]>0
assert report["authority"]=="context_only"
print("ORION_GITEA_REAL_CODEMAP> PASS")
'@
$python | & py -3.11 -
if($LASTEXITCODE -ne 0){throw 'Gitea real code map failed'}

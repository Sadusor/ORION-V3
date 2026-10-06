/* ======================================================================
   routes.js — the UI's ROUTE ALLOWLIST. bridge.call() refuses anything not listed here, before any network I/O.
   kind:
     read      GET, no side effects
     auth      pairing
     request   asks ORION to PROPOSE something (backend preflight + verifier + authorization decide what happens)
     approval  a human approval boundary (generated PowerShell / exact-SHA run). Requires a real, trusted user gesture.
     stop      targeted stop
     storage   bounded chat-history data sync; never authorizes execution
     command   existing Remote V1 control (backend validates and may refuse with 409)
     high      high-impact; the UI asks for a browser confirm() as a courtesy. The backend remains the authority.
   Deliberately NOT registered (still available only in the legacy UI): /api/manual/run, /api/reviewers/run,
   /api/project-links/clone|create, /api/providers/save|delete, /api/generate, /api/tags, /api/memory/candidate (write),
   /api/session/* beyond start/stop. Add a route here only when a V3 screen genuinely needs it.
   ====================================================================== */
const ROUTES={
 'GET /api/status':{kind:'read'},'GET /api/project-links':{kind:'read'},'GET /api/work-exchange/latest':{kind:'read'},
 'GET /api/memory/candidates':{kind:'read'},'GET /api/reviewers/latest':{kind:'read'},'GET /api/providers':{kind:'read'},'GET /api/chat-history':{kind:'read'},
 'POST /api/pair':{kind:'auth'},
 'POST /api/chat-history/sync':{kind:'storage'},
 'POST /api/local-hand/draft':{kind:'request',note:'Local Brain proposes. ORION preflight, semantic verifier and original-request authorization decide whether a registered capability starts.'},
 'POST /api/local-hand/revise':{kind:'request'},
 'POST /api/local-hand/run':{kind:'approval',note:'Approve & Run for generated PowerShell. The server re-checks the approved script hash.'},
 'POST /api/run/start':{kind:'approval',note:'Approve & Run for the exact pending SHA (GitHub developer loop).'},
 'POST /api/local-hand/stop':{kind:'stop'},'POST /api/manual/stop':{kind:'stop'},'POST /api/run/stop':{kind:'stop'},
 'POST /api/session/stop':{kind:'stop'},'POST /api/reviewers/stop':{kind:'stop'},
 'POST /api/github/check':{kind:'command'},'POST /api/github/sync':{kind:'command'},
 'POST /api/mode/enter':{kind:'command'},'POST /api/mode/pause':{kind:'command'},'POST /api/mode/resume':{kind:'command'},'POST /api/mode/exit':{kind:'command'},
 'POST /api/session/start':{kind:'command'},
 'POST /api/project-links/refresh':{kind:'command'},'POST /api/project-links/activate':{kind:'command'},
 'POST /api/reviewers/catalog/refresh':{kind:'command'},
 'POST /api/providers/test':{kind:'command'},'POST /api/providers/enabled':{kind:'command'},
 'POST /api/system/update-restart':{kind:'high',note:'Restarts ORION. The backend refuses unless the pending SHA already PASSed.'}
};
const routeInfo=(method,route)=>ROUTES[method+' '+String(route).split('?')[0]]||null;
const isRegistered=(method,route)=>!!routeInfo(method,route);
if(typeof window!=='undefined')window.STRATA_ROUTES=ROUTES;

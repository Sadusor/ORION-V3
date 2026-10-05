/* ======================================================================
   ORION product connector descriptors.
   Presentation only: descriptors never mint authority and expose no V1 Remote controls.
   All facts come from canonical UiState; unavailable capabilities are shown honestly.
   ====================================================================== */
const PLANNED=[
 ['voice','Voice','Phone/PC push-to-talk after the shared turn journal and local STT are qualified.'],
 ['pc_live_view','PC Live View','Separate view-only media channel. Viewing never grants computer-control authority.'],
 ['calendar_email','Calendar / Email','Replaceable connector seam. Not connected yet.'],
 ['workflows','Workflows','Replaceable workflow connector seam. n8n is a donor candidate, not authority.'],
 ['computer_hand','Computer Hand','Future governed computer-use connector. Not enabled by UI presence.'],
 ['android_hand','Android / Device','Future device connector.']
];
function buildConnectors(ui,extra){
 extra=extra||{};const A=[],live=ui.connection.status==='live',ts=ui.timestamps.snapshotAt;
 const st=(ok,busy)=>!live?'unknown':busy?'busy':ok?'ready':'degraded';
 const row=(label,detail)=>({label,detail:detail||'—'});
 const p=ui.project||{},g=ui.github||{},l=ui.localBrain||{},r=ui.reviewers||{models:{total:0,available:0},items:[],status:'idle'},h=ui.hands||{},rt=ui.runtime||{};
 A.push({id:'project',kind:'project',label:'Projects',status:st(!!(g.repo||p.label)),status_ts:ts,
  status_detail:p.label?'Active workspace · '+p.label:'No active project selected',items:[row('Active',p.label||'none'),row('Repository',g.repo||'not connected'),row('Branch',g.branch||'—'),row('Scope',p.scope||'—')]});
 A.push({id:'github',kind:'connector',label:'GitHub / Source',status:st(!!g.repo,g.executionState==='running'),status_ts:ts,
  status_detail:g.repo?'Source state is available to ORION':'Connector not wired to this product surface yet',items:[row('Repository',g.repo||'—'),row('Checkout',g.checkoutSha||'—'),row('Pending source revision',g.pendingSha||'none')]});
 A.push({id:'brain',kind:'brain',label:'Local Brain',status:st(!!(l.model||l.defaultModel),l.state==='running'),status_ts:ts,
  status_detail:l.state==='running'?'Working · '+(l.phase||'running'):(l.model||l.defaultModel?'Ready':'No model reported'),items:[row('Model',l.model||l.defaultModel||'not reported'),row('Reasoning mode','not reported by backend'),row('Last request',l.goal||'—')]});
 A.push({id:'hands',kind:'hand',label:'Hands',status:st(!!h.local,(h.local&&h.local.executionState==='running')||(h.manual&&h.manual.executionState==='running')),status_ts:ts,
  status_detail:'Execution remains behind ORION authority; this UI does not grant permissions.',items:[row('Deterministic hand',h.local?(h.local.executionState+(h.local.verdict?' · '+h.local.verdict:'')):'not connected'),row('Manual lane',h.manual?(h.manual.executionState+(h.manual.verdict?' · '+h.manual.verdict:'')):'not connected')]});
 A.push({id:'reviewers',kind:'specialist',label:'Cloud AI Council',status:!live?'unknown':r.status==='running'?'busy':r.status==='failed'?'unavailable':r.status==='partial'?'degraded':r.models.total?'ready':'unknown',status_ts:ts,
  status_detail:r.models.total?(r.models.available+' of '+r.models.total+' reviewer model(s) available'):'Provider/reviewer catalog not connected',items:(r.items||[]).slice(0,5).map(i=>row((i.provider||'AI')+' · '+(i.model||'model'),i.phase+(i.error?' · '+i.error:'')))});
 A.push({id:'providers',kind:'provider',label:'Provider Vault',status:!live?'unknown':ui.providers.status==='ready'?'ready':ui.providers.status==='unavailable'?'degraded':'unknown',status_ts:ts,
  status_detail:ui.providers.items.length?ui.providers.items.length+' saved provider(s)':'No provider slots reported yet',items:ui.providers.items.slice(0,5).map(x=>row(x.label,[x.adapter,x.enabled?'enabled':'disabled',x.freeConfigured?'configured-free':''].filter(Boolean).join(' · ')))});
 A.push({id:'memory',kind:'memory',label:'Memory',status:'preview',status_ts:ts,status_detail:'Memory candidates can be previewed. Promoted canonical Memory is not exposed by the current backend.',items:[row('Authority','ORION-owned'),row('Current surface','candidate preview only')],actions:[{label:'Open Memory',ui:'memory'}]});
 A.push({id:'runtime',kind:'runtime',label:'Runtime',status:st(true),status_ts:ts,status_detail:'Replaceable substrate/runtime facts reported by ORION.',items:[row('Default model',rt.defaultModel||'not reported'),row('Local models',(rt.ollamaModels||[]).length?rt.ollamaModels.length+' reported':'not reported'),row('Connection',ui.connection.status)]});
 A.push({id:'safety',kind:'safety',label:'Authority & Safety',status:live?'ready':'unknown',status_ts:ts,status_detail:'UI presentation is never execution authority.',items:[row('Remote V1','frozen · separate engineering control path'),row('STOP targets',ui.stops.length?ui.stops.length+' stoppable execution(s)':'none reported'),row('PC control','not authorized by viewing or connection')]});
 return{active:A,planned:PLANNED};
}

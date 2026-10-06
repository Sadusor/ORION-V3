/* Every referenced file exists; live page has no mock; demo page has only mock; no ES imports; all DOM ids the code needs exist; docs present. */
const {ROOT,fs,path,ok,done,scriptsOf}=require('../harness');
const read=f=>fs.readFileSync(path.join(ROOT,f),'utf8');
console.log('assets');
for(const page of ['index.html','demo.html']){
 const html=read(page),refs=[...html.matchAll(/(?:src|href)="([^"#]+)"/g)].map(m=>m[1]).filter(u=>!/^(data:|https?:|\/)/.test(u));
 ok(refs.length>=10,page+': references '+refs.length+' local assets');
 for(const r of refs)ok(fs.existsSync(path.join(ROOT,r)),page+' -> '+r+' exists');
 ok(!/https?:\/\//.test(html.replace(/xmlns=%27[^%]*%27/g,'')),page+': no external URLs (self-contained)');}
const live=scriptsOf('index.html'),demo=scriptsOf('demo.html');
ok(live.includes('bridge/real-bridge.js')&&!live.includes('bridge/mock-bridge.js'),'index.html (live) loads the REAL bridge and never the mock');
ok(live.includes('modules/chat-history.js'),'index.html loads the bounded chat-history module');
ok(live.indexOf('shell/shell.js')<live.indexOf('modules/chat-history.js'),'chat history loads after shell so it observes the proven chat DOM instead of replacing it');
ok(demo.includes('bridge/mock-bridge.js')&&!demo.includes('bridge/real-bridge.js'),'demo.html loads ONLY the mock bridge');
ok(!/mock/i.test(read('index.html').replace(/<!--.*?-->/gs,'').replace('DEMO / MOCK BACKEND','')),'index.html contains no mock wiring (only the hidden banner text)');
const all=[];(function walk(d){for(const f of fs.readdirSync(d)){const p=path.join(d,f);fs.statSync(p).isDirectory()?(f==='tests'?0:walk(p)):all.push(p)}})(ROOT);
for(const f of all.filter(f=>f.endsWith('.js'))){const t=fs.readFileSync(f,'utf8');ok(!/^\s*(import\s.+from|export\s)/m.test(t),path.relative(ROOT,f)+': classic script (no ES import/export to resolve)')}
const ids=new Set([...read('index.html').matchAll(/id="([^"]+)"/g)].map(m=>m[1]));
const used=new Set();for(const f of ['shell/shell.js','memory/memory.js','components/sky-planet.js','state/store.js'])for(const m of read(f).matchAll(/\$\(['"]([A-Za-z0-9_-]+)['"]\)/g))used.add(m[1]);
const dyn=new Set(['cinfo','rawpre','rawsel','epin','epsave','forget','refreshnow','pcode','pgo','perr','vstage','demosel','muPropose','muPromote','muReject','muDefer','muRevoke']);   // created at runtime by the shell
for(const u of used)if(!dyn.has(u))ok(ids.has(u),'DOM id #'+u+' used by code exists in index.html');
for(const d of ['README.md','ARCHITECTURE.md','INTEGRATION.md','STATE_CONTRACT.md','TESTING.md'])ok(fs.existsSync(path.join(ROOT,d)),d+' present');
ok(all.some(f=>f.endsWith('styles'+path.sep+'tokens.css'))&&all.some(f=>f.endsWith('styles'+path.sep+'base.css'))&&all.some(f=>f.endsWith('styles'+path.sep+'strata.css')),'all three stylesheets present');
done('assets');

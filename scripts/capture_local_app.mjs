// Run against the local server and a dedicated Chrome --remote-debugging-port=9329 session.
// Uses Node's built-in DevTools/WebSocket support; no browser packages are installed.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const origin=process.env.WAFERGUARD_PREVIEW_ORIGIN||'http://127.0.0.1:8768';
const debug=process.env.WAFERGUARD_CHROME_DEBUG||'http://127.0.0.1:9329';
const pages=await(await fetch(debug+'/json/list')).json();
const ws=new WebSocket(pages.find(p=>p.type==='page').webSocketDebuggerUrl);
await new Promise(r=>ws.addEventListener('open',r,{once:true}));
let sequence=0;const pending=new Map(),errors=[],requests=[],checks=[],captures=[];
ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.id){const p=pending.get(m.id);pending.delete(m.id);if(m.error)p?.reject(m.error);else p?.resolve(m.result);}if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.text);if(m.method==='Network.requestWillBeSent')requests.push(m.params.request.url);});
function send(method,params={}){return new Promise((resolve,reject)=>{const id=++sequence;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});}
async function evaluate(expression){const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true,userGesture:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;}
async function waitFor(expression){for(let n=0;n<100;n++){if(await evaluate(expression))return;await new Promise(r=>setTimeout(r,50));}throw Error('Timed out: '+expression);}
function assert(value,label){if(!value)throw Error(label);checks.push(label);console.log('PASS '+label);}
const out=path.join(root,'DOC/screenshots');await fs.mkdir(out,{recursive:true});
async function screenshot(name,width,height){await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:width<700});await evaluate('scrollTo(0,0)');await new Promise(r=>setTimeout(r,120));assert(await evaluate('document.documentElement.scrollWidth<=innerWidth'),`${name} fits viewport width`);const r=await send('Page.captureScreenshot',{format:'png'});const bytes=Buffer.from(r.data,'base64');await fs.writeFile(path.join(out,name+'.png'),bytes);captures.push({file:name+'.png',width,height,sha256:createHash('sha256').update(bytes).digest('hex')});}
try{
await send('Page.enable');await send('Runtime.enable');await send('Network.enable');await send('Emulation.setFocusEmulationEnabled',{enabled:true});
await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1080,deviceScaleFactor:1,mobile:false});
await send('Page.navigate',{url:origin+'/DOC/app/'});
await waitFor('document.querySelectorAll(".metric").length===4');
await evaluate('localStorage.removeItem("waferguard-research-notebook-v1");location.reload()');
await waitFor('document.querySelectorAll(".metric").length===4');
assert(await evaluate('document.querySelector(".metric strong").textContent==="0.7265"'),'dashboard displays committed frozen-test macro-F1');
assert(await evaluate('document.querySelectorAll(".recall-row").length===9'),'all nine measured class recalls render');
assert(await evaluate('document.querySelectorAll(".fail-tag").length===3'),'all three failed qualification criteria remain visible');
await screenshot('overview',1440,1080);
await evaluate('location.hash="inspect"');await waitFor('!document.getElementById("inspect").hidden');
assert(await evaluate('document.getElementById("input-origin").textContent.includes("Synthetic")'),'example provenance is visible');
await screenshot('inspector',1440,1080);
await evaluate('document.getElementById("wafer").dispatchEvent(new KeyboardEvent("keydown",{key:"ArrowRight",bubbles:true}))');
assert(await evaluate('document.getElementById("cell-info").textContent.includes("column 2")'),'grid supports keyboard cell inspection');
await evaluate('document.getElementById("example").value="ring";document.getElementById("example").dispatchEvent(new Event("change"))');
assert(await evaluate('document.getElementById("grid-title").textContent==="Ring pattern"'),'example selector changes the displayed grid');
await evaluate('document.getElementById("example").value="line";document.getElementById("example").dispatchEvent(new Event("change"))');
await evaluate('document.getElementById("add-case").click()');await waitFor('!document.getElementById("notebook").hidden');
await evaluate('document.getElementById("note-category").value="further-inspection";document.getElementById("note-text").value="The synthetic line structure crosses the center. Inspect whether grid encoding preserves narrow structures before comparing model representations.";document.querySelector("#case-detail form").requestSubmit()');
await waitFor('document.querySelector(".case-status")?.textContent==="Note recorded"');
assert(await evaluate('!localStorage.getItem("waferguard-research-notebook-v1").includes("\\\"grid\\\"")&&!localStorage.getItem("waferguard-research-notebook-v1").includes("\\\"wafer\\\"")'),'notebook storage excludes raw grid arrays');
await screenshot('notebook',1440,1080);
await evaluate('location.reload()');await waitFor('document.querySelectorAll(".case-row").length===1');
assert(await evaluate('document.querySelector(".case-status").textContent==="Note recorded"'),'research notes survive reload');
await evaluate('document.getElementById("case-filter").value="pending";document.getElementById("case-filter").dispatchEvent(new Event("change"))');
assert(await evaluate('document.querySelectorAll(".case-row").length===0'),'pending filter excludes recorded notes');
await evaluate('location.hash="inspect"');await waitFor('!document.getElementById("inspect").hidden');
async function upload(value){await evaluate(`(()=>{const dt=new DataTransfer();dt.items.add(new File([${JSON.stringify(JSON.stringify(value))}],"test-grid.json",{type:"application/json"}));const input=document.getElementById("grid-file");input.files=dt.files;input.dispatchEvent(new Event("change"));})()`);await new Promise(r=>setTimeout(r,100));}
await upload([[0]]);assert(await evaluate('document.getElementById("feedback").textContent.includes("Input rejected")'),'all-outside grid rejected');
await upload([[0,1,2],[1,2,0]]);assert(await evaluate('document.getElementById("dimensions").textContent==="2 × 3"'),'valid uploaded JSON grid renders');
assert(await evaluate('document.getElementById("input-origin").textContent.includes("Imported")'),'uploaded grid is distinguished from synthetic examples');
await upload([[1],[1,2]]);assert(await evaluate('document.getElementById("feedback").textContent.includes("same number")'),'ragged uploaded grid rejected');
await evaluate('document.getElementById("example").dispatchEvent(new Event("change"))');await screenshot('inspector-mobile',390,844);
await evaluate('location.hash="overview"');await screenshot('overview-mobile',390,844);
assert(!requests.some(url=>url.startsWith('http')&&!url.startsWith(origin+'/')),'app makes no external network requests');
assert(!requests.some(url=>url.includes('/api/')),'app makes no inference or approval API requests');
assert(errors.length===0,'no uncaught browser exceptions');
const sources={};for(const name of ['index.html','app.css','app.js','core.mjs'])sources['DOC/app/'+name]=createHash('sha256').update(await fs.readFile(path.join(root,'DOC/app',name))).digest('hex');
const receipt={capturedAt:new Date().toISOString(),scope:'Actual Chrome captures of the local browser research app. Inspector and notebook use labeled deterministic synthetic inputs; dashboard uses committed aggregate metrics. No model inference or production approval.',checks,captures,sources};
await fs.writeFile(path.join(out,'receipt.json'),JSON.stringify(receipt,null,2)+'\n');
console.log(`Captured ${captures.length} screenshots; ${checks.length} checks passed.`);
}finally{ws.close();}

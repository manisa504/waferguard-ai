'use strict';
(async () => {
const {validateGrid,syntheticGrid,createCase,addNote}=await import('./core.mjs');
const $=id=>document.getElementById(id);
const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
const pct=value=>(value*100).toFixed(1)+'%';
const count=value=>value.toLocaleString('en-US');
const notify=message=>{$('feedback').textContent=message;};
const storageKey='waferguard-research-notebook-v1';
let cases=[], selected=null, gridState=null, origin='synthetic', title='Line pattern', currentCell=[15,15];
try {
  const saved=JSON.parse(localStorage.getItem(storageKey)||'[]');
  if(!Array.isArray(saved)||saved.some(c=>!c||typeof c.id!=='string'||!Array.isArray(c.notes)||!['pending','reviewed'].includes(c.status)||!c.summary))throw new Error();
  cases=saved;
} catch {notify('Browser notes could not be read. This session starts with an empty notebook. Export any recoverable notes before clearing storage.');}
function save(next){try{localStorage.setItem(storageKey,JSON.stringify(next));cases=next;return true;}catch{notify('Browser storage is unavailable or full. Your latest change was not saved. Export existing notes before closing.');return false;}}
function download(name,value){const blob=new Blob([JSON.stringify(value,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=node('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function route(){const name=location.hash.slice(1)||'overview';const page=['overview','inspect','notebook','diagrams'].includes(name)?name:'overview';document.querySelectorAll('.page').forEach(p=>p.hidden=p.id!==page);document.querySelectorAll('[data-page]').forEach(link=>{if(link.dataset.page===page)link.setAttribute('aria-current','page');else link.removeAttribute('aria-current');});if(page==='notebook')renderNotebook();document.title=`WaferGuard · ${{overview:'Evidence overview',inspect:'Grid inspector',notebook:'Review notebook',diagrams:'System diagrams'}[page]}`;}
window.addEventListener('hashchange',route);
async function evidence(){
  try {
    const paths=['test','qualification'];
    const [test,qualification]=await Promise.all(paths.map(async name=>{const r=await fetch(`../../reports/metrics/gate4-final/${name}.json`);if(!r.ok)throw new Error();return r.json();}));
    const c=test.classification,scratch=c.per_class.Scratch;
    $('metrics').replaceChildren();
    for(const [label,value,detail,warn] of [['Test macro-F1',c.macro_f1.toFixed(4),'Declared minimum 0.75',false],['Scratch recall',pct(scratch.recall),'65 of 117 detected',true],['Scratch precision',pct(scratch.precision),'Predicted-class reliability',false],['Critical false accepts',String(test.selective.critical_false_accepts),'Offline policy · not operational',true]]){
      const card=node('div',undefined,'metric'+(warn?' warn':''));card.append(node('div',label,'metric-label'),node('strong',value),node('small',detail));$('metrics').append(card);
    }
    $('recall-chart').replaceChildren();
    for(const name of c.classes){const row=node('div',undefined,'recall-row'+(name==='Scratch'?' critical':''));const track=node('div',undefined,'track'),bar=node('div',undefined,'bar');bar.style.width=`${c.per_class[name].recall*100}%`;track.append(bar);row.append(node('span',name),track,node('strong',pct(c.per_class[name].recall)));row.setAttribute('aria-label',`${name} recall ${pct(c.per_class[name].recall)}, support ${c.per_class[name].support}`);$('recall-chart').append(row);}
    for(const [label,value] of [['Macro-F1 ≥ 0.75',c.macro_f1>=.75],['Scratch recall ≥ 60%',scratch.recall>=.6],['Zero critical false accepts',test.selective.critical_false_accepts===0]]){const item=node('div',undefined,'gate');item.append(node('span',label),node('span',value?'PASS':'FAIL','fail-tag'));$('gates').append(item);}
    $('ece').textContent=test.calibration.ece.toFixed(4);
    if(qualification.qualified_for_promotion||qualification.automatic_acceptance_authorized)notify('Evidence state changed. Review the source qualification before relying on this presentation.');
  }catch{$('metrics').replaceChildren(node('p','Committed evidence could not be loaded. Start the local server or open the published page; do not use a file:// URL.'));}
}
function drawGrid(){
  const canvas=$('wafer'),ctx=canvas.getContext('2d'),{rows,cols,grid}=gridState;
  ctx.fillStyle='#f0f3ed';ctx.fillRect(0,0,640,640);
  const unit=580/Math.max(rows,cols),left=(640-cols*unit)/2,top=(640-rows*unit)/2;
  canvas.gridGeometry={unit,left,top};
  for(let r=0;r<rows;r++)for(let c=0;c<cols;c++){ctx.fillStyle=['#e5eae0','#698f79','#d49446'][grid[r][c]];const gap=unit>4?Math.min(2,unit*.14):0;ctx.fillRect(left+c*unit+gap/2,top+r*unit+gap/2,unit-gap,unit-gap);}
  canvas.setAttribute('aria-label',`${origin==='synthetic'?'Synthetic example':'Imported grid'}: ${rows} rows, ${cols} columns, ${gridState.pass} pass-state cells and ${gridState.fail} fail-state cells. No model prediction.`);
}
function loadGrid(input,newOrigin,newTitle){gridState=validateGrid(input);origin=newOrigin;title=newTitle;currentCell=[0,0];$('grid-title').textContent=title;$('input-origin').textContent=origin==='synthetic'?'Synthetic example':'Imported · browser memory only';$('dimensions').textContent=`${gridState.rows} × ${gridState.cols}`;$('sample-note').textContent=origin==='synthetic'?'This is a deterministic synthetic grid for demonstrating the interface. It is not a WM-811K sample and has no ground-truth defect label.':'This user-supplied grid is held in browser memory. No ground-truth label or model prediction is assigned, and no grid is uploaded or saved to the notebook.';$('grid-summary').replaceChildren();for(const [name,value] of [['Input contract','Valid categorical grid'],['Inside-wafer cells',count(gridState.inside)],['Pass-state cells',count(gridState.pass)],['Fail-state cells',count(gridState.fail)],['Fail-state fraction',pct(gridState.fail/gridState.inside)],['Model execution','Disabled']]){const row=node('div');row.append(node('dt',name),node('dd',value));$('grid-summary').append(row);}$('add-status').textContent='';$('cell-info').textContent='Point to a die to inspect its position and state.';drawGrid();}
$('example').addEventListener('change',()=>{const value=$('example').value;loadGrid(syntheticGrid(value),'synthetic',({line:'Line pattern',ring:'Ring pattern',scatter:'Scattered pattern'})[value]);notify('');});
$('download-example').addEventListener('click',()=>download('synthetic-wafer-example.json',{synthetic:true,description:'UI demonstration only; no real wafer or defect label.',wafer:syntheticGrid($('example').value)}));
$('grid-file').addEventListener('change',async e=>{const file=e.target.files[0];if(!file)return;try{if(file.size>512*1024)throw new Error('The JSON file must be at most 512 KB.');loadGrid(JSON.parse(await file.text()),'imported','Imported categorical grid');notify('Grid validated locally. It has not been uploaded.');}catch(error){notify(`Input rejected: ${error.message}. The previous grid remains available.`);}finally{e.target.value='';}});
function describeCell(r,c){if(r<0||c<0||r>=gridState.rows||c>=gridState.cols)return;currentCell=[r,c];$('cell-info').textContent=`Row ${r+1}, column ${c+1} · ${['Outside wafer','Pass state','Fail state'][gridState.grid[r][c]]}.`;}
$('wafer').addEventListener('pointermove',e=>{const rect=$('wafer').getBoundingClientRect(),{left,top,unit}=$('wafer').gridGeometry;describeCell(Math.floor(((e.clientY-rect.top)*640/rect.height-top)/unit),Math.floor(((e.clientX-rect.left)*640/rect.width-left)/unit));});
$('wafer').addEventListener('keydown',e=>{const delta={ArrowUp:[-1,0],ArrowDown:[1,0],ArrowLeft:[0,-1],ArrowRight:[0,1]}[e.key];if(!delta)return;e.preventDefault();describeCell(Math.max(0,Math.min(gridState.rows-1,currentCell[0]+delta[0])),Math.max(0,Math.min(gridState.cols-1,currentCell[1]+delta[1])));});
$('add-case').addEventListener('click',()=>{const record=createCase(gridState,origin,title,crypto.randomUUID(),new Date().toISOString());if(save([...cases,record])){selected=record.id;$('add-status').textContent='Summary saved locally.';location.hash='notebook';renderNotebook();}});
function renderNotebook(){
  $('case-count').textContent=`${cases.length} case${cases.length===1?'':'s'}`;$('case-list').replaceChildren();
  const filter=$('case-filter').value,shown=cases.filter(c=>filter==='all'||c.status===filter);
  if(!shown.length)$('case-list').append(node('p',cases.length?'No cases match this status.':'No research cases yet. Add a synthetic example or imported grid from the inspector.','empty'));
  for(const c of [...shown].reverse()){const button=node('button',undefined,'case-row');button.type='button';button.setAttribute('aria-pressed',String(c.id===selected));button.append(node('strong',c.title),node('span',`${c.origin==='synthetic'?'Synthetic example':'Imported grid'} · ${c.summary.rows} × ${c.summary.cols}`),node('span',c.status==='pending'?'Pending note':'Note recorded','case-status'));button.addEventListener('click',()=>{selected=c.id;renderNotebook();});$('case-list').append(button);}
  const record=cases.find(c=>c.id===selected),detail=$('case-detail');detail.replaceChildren();
  if(!record){detail.append(node('h2','Select a case'),node('p','Add an example from the grid inspector to begin.','muted'));return;}
  detail.append(node('p',record.origin==='synthetic'?'SYNTHETIC EXAMPLE · NO GROUND-TRUTH LABEL':'USER INPUT · NO MODEL PREDICTION','detail-origin'),node('h2',record.title),node('p',`${record.summary.rows} × ${record.summary.cols} grid · ${record.summary.pass} pass-state cells · ${record.summary.fail} fail-state cells`,'muted'),node('p','This record contains a grid summary only. A note documents research observations; it does not release or approve a wafer.','muted'));
  const form=node('form'),label=node('label','Research category'),select=node('select');select.id='note-category';for(const [value,name] of [['observation','Pattern observation'],['further-inspection','Needs further inspection'],['input-question','Input quality question']]){const option=node('option',name);option.value=value;select.append(option);}label.append(select);
  const noteLabel=node('label','Observation'),textarea=node('textarea');textarea.id='note-text';textarea.required=true;textarea.minLength=3;textarea.maxLength=1200;textarea.placeholder='What do you see? What should a researcher inspect next?';noteLabel.append(textarea);const submit=node('button','Save research note','button');submit.type='submit';form.append(label,noteLabel,submit);form.addEventListener('submit',e=>{e.preventDefault();try{const updated=addNote(record,textarea.value,select.value,new Date().toISOString());if(save(cases.map(c=>c.id===updated.id?updated:c))){notify('Research note saved in this browser. No operational approval was created.');renderNotebook();}}catch(error){notify(error.message);}});detail.append(form);
  if(record.notes.length){const history=node('div',undefined,'note-history');history.append(node('h3','Recorded observations'));for(const n of record.notes){history.append(node('p',n.text),node('p',`${n.category} · ${new Date(n.at).toLocaleString()}`,'muted'));}detail.append(history);}
}
$('case-filter').addEventListener('change',renderNotebook);
$('export-notes').addEventListener('click',()=>download('waferguard-research-notes.json',{scope:'Browser-only research notes. No operational approval or raw wafer grids.',cases}));
$('clear-notes').addEventListener('click',()=>{if(!cases.length){notify('The notebook is already empty.');return;}if(confirm('Clear all research notes from this browser? Export them first if needed.')&&save([])){selected=null;renderNotebook();notify('Browser notebook cleared.');}});
loadGrid(syntheticGrid('line'),'synthetic','Line pattern');route();evidence();
})().catch(()=>{document.getElementById('feedback').textContent='The workspace could not start. Use the local server or the published page, and reload.';});

// Exercise the delivered script without accessing a browser or local URL.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync(process.argv[2],'utf8');
class Element{
 constructor(tag='div'){this.tag=tag;this.children=[];this.value='';this.textContent='';this.style={};this.dataset={};this.classList={toggle(){}};this.attributes={};}
 append(...xs){this.children.push(...xs);if(xs.length&&this.tag==='select'&&this.children.length===xs.length)this.value=String(xs[0].value);}
 replaceChildren(...xs){this.children=[];this.append(...xs);}
 setAttribute(k,v){this.attributes[k]=v;}click(){this.onclick?.();}
 querySelectorAll(s){return this.children.flatMap(c=>[...(s==='button'&&c.tag==='button'?[c]:[]),...c.querySelectorAll(s)]);}
}
const els={};for(const m of html.matchAll(/<(\w+)[^>]*\bid="([^"]+)"[^>]*>/g)){assert.ok(!els[m[2]],m[2]);const e=new Element(m[1]);e.value=m[0].match(/\bvalue="([^"]*)"/)?.[1]||'';els[m[2]]=e;}
for(const n of ['start','build','systems','stock','verify']){const b=new Element('button');b.dataset.section=n;els.nav.append(b);}
els.materialGroup.value='all';let downloads=0,failWrites=false;const saved=new Map();
const context=vm.createContext({document:{getElementById:id=>{assert.ok(els[id],id);return els[id]},createElement:tag=>new Element(tag)},console,
 localStorage:{getItem:k=>saved.get(k),setItem:(k,v)=>{if(failWrites)throw Error('Storage unavailable');saved.set(k,v)}},Blob,URL:{createObjectURL:()=>{downloads++;return 'blob:test'},revokeObjectURL(){}}});
vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1],context,{timeout:30000});
const data=JSON.parse(html.split('const D=')[1].split(';/* END_DATA */')[0]);
assert.equal(els.phase.children.length,6);assert.equal(els.stageCards.children.length,6);assert.equal(els.moduleButtons.children.length,11);assert.equal(els.gateCards.children.length,3);assert.equal(els.routeRows.children.length,53);assert.equal(els.tileRows.children.length,324);
assert.equal(els.materialRows.children.length,88);assert.ok(els.worldBounds.textContent.includes('32'));
for(let i=0;i<6;i++){els.phase.value=String(i);els.phase.onchange();assert.ok(els.phaseGoal.textContent.length>5);assert.ok(els.actionRows.children.length>0);assert.ok(els.grid.querySelectorAll('button').length<=256);}
context.locate([3,5,-47]);assert.equal(els.blockTitle.textContent,'切制砂岩');assert.ok(els.blockWorld.textContent.includes('85'));assert.ok(els.taskBadge.textContent.includes('本页'));
context.locate([55,3,32]);assert.ok(els.blockMethod.children.some(e=>e.textContent.includes('(55,4,32)')));assert.ok(els.pageInfo.textContent.includes('最终关闭态'));
context.locate([21,-28,8]);assert.ok(els.pageInfo.textContent.includes('B批'));assert.ok(els.blockMethod.children.some(e=>e.textContent.includes('支撑块')));
context.locate([999,0,0]);assert.ok(els.status.textContent.includes('范围'));
els.ox.value='';els.ox.onchange();assert.ok(els.worldBounds.textContent.includes('有限整数'));assert.equal(els.complete.disabled,true);
els.cornerX.value='10';els.cornerY.value='32';els.cornerZ.value='116';els.useCorner.onclick();assert.equal(els.ox.value,'100');assert.equal(els.oy.value,'80');assert.equal(els.oz.value,'200');
context.locate([3,5,-47]);assert.ok(els.blockWorld.textContent.includes('103'));assert.ok(els.blockWorld.textContent.includes('153'));
const before=vm.runInContext('current',context);els.complete.onclick();assert.equal(vm.runInContext('current',context),before+1);assert.equal(vm.runInContext('done.size',context),1);
els.prevPage.onclick();assert.equal(els.undoPage.disabled,false);els.undoPage.onclick();assert.equal(vm.runInContext('done.size',context),0);
els.complete.onclick();els.exportProgress.onclick();assert.equal(downloads,1);
els.ox.value='101';els.ox.onchange();assert.equal(vm.runInContext('done.size',context),0);els.ox.value='100';els.ox.onchange();assert.equal(vm.runInContext('done.size',context),1);
els.featureSearch.value='不存在的构件';els.featureSearch.oninput();assert.equal(els.featureGo.disabled,true);els.featureSearch.value='凸窗';els.featureSearch.oninput();assert.equal(els.featureGo.disabled,false);els.featureGo.onclick();
els.materialSearch.value='切制砂岩';els.materialSearch.oninput();assert.ok(els.materialRows.children.length>=1);assert.ok(els.materialRows.children.every(row=>row.children[0].textContent.includes('切制砂岩')));
const c=els.grid.querySelectorAll('button')[0];c.onclick();assert.ok(els.blockDesign.textContent.includes('设计坐标'));
async function progressImportTests(){
 const progress=JSON.parse(vm.runInContext('JSON.stringify(progressValue())',context));
 const extra=data.plan.pages.find(p=>!progress.done.includes(p.id)).id;
 const upload=async value=>{const raw=JSON.stringify(value);els.importProgress.files=[{size:raw.length,text:async()=>raw}];await els.importProgress.onchange();assert.equal(els.importProgress.value,'');};
 await upload({...progress,done:[extra]});assert.equal(vm.runInContext('done.size',context),2);assert.ok(els.progressStatus.textContent.includes('已合并'));
 for(const invalid of [
  {...progress,modelHash:'wrong'}, {...progress,origin:[0,0,0]},
  {...progress,done:['not-a-page']}, {...progress,done:[extra,extra]}
 ]){await upload(invalid);assert.ok(els.progressStatus.textContent.startsWith('未导入'));assert.equal(vm.runInContext('done.size',context),2);}
 const third=data.plan.pages.find(p=>!progress.done.includes(p.id)&&p.id!==extra).id;
 failWrites=true;await upload({...progress,done:[third]});
 assert.equal(vm.runInContext('done.size',context),3,'import remains in memory');
 assert.match(els.progressStatus.textContent,/无法|不允许/,'storage failure must not be hidden by merge success');
 assert.match(els.progressStatus.textContent,/导出/,'show recovery action');
 assert.equal(els.buildProgressStatus.textContent,els.progressStatus.textContent,'warning also visible while building');
 failWrites=false;
 console.log(`V20 DOM stub passed: ${data.plan.pages.length} pages, 6 stages, 11 modules, 3 gates, locate, material filters, completion/undo, origin-isolated persistence, import validation and storage-failure warning. Not browser rendering.`);
}
progressImportTests().catch(e=>{console.error(e);process.exitCode=1;});

const $=id=>document.getElementById(id),R=D.report,P=D.plan,pages=P.pages,names=D.names;
const blocks=new Map(),pageIndex=new Map(),footprint=new Map(),cellsByPage=new Map();
for(let i=0;i<pages.length;i++)pageIndex.set(pages[i].id,i);
for(let i=0;i<D.blocks.length;i++){
 const row=D.blocks[i],p=row.slice(0,3).map((v,k)=>v-D.offset[k]),s=D.palette[row[3]],phase=P.blockPhases[i],sub=P.blockPasses[i],id=`${phase}:${sub}:${p[1]}:${Math.floor(row[0]/16)}:${Math.floor(row[2]/16)}`;
 const cell={p,s,phase,sub};blocks.set(p.join(','),cell);if(!cellsByPage.has(id))cellsByPage.set(id,[]);cellsByPage.get(id).push(cell);
 const key=`${Math.floor(row[0]/8)},${Math.floor(row[2]/8)}`;footprint.set(key,Math.max(footprint.get(key)||-100,p[1]));
}
for(const cs of cellsByPage.values())cs.sort((a,b)=>a.p[2]-b.p[2]||a.p[0]-b.p[0]);
let current=0,selected=null,done=new Set(),featureMatches=[];
const at=p=>blocks.get(p.join(','))?.s||null,origin=()=>['ox','oy','oz'].map(id=>$(id).value.trim()===''?NaN:Number($(id).value)),validOrigin=()=>origin().every(Number.isInteger),world=p=>validOrigin()?p.map((v,i)=>v+origin()[i]):null;
const make=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e},btn=(text,fn)=>{const e=make('button',text);e.onclick=fn;return e},option=(select,value,text)=>{const e=make('option',text);e.value=String(value);select.append(e)},cn=n=>names[n]||n;
const progressContext=()=>({hash:R.progressKeyHash,origin:origin(),ids:new Set(pageIndex.keys())});
const progressValue=()=>({version:1,modelHash:R.progressKeyHash,origin:origin(),done:[...done].sort()});
const progressKey=()=>`echo-castle-v20:${R.progressKeyHash}:${origin().join(',')}`;
function progressInfo(){$('progressInfo').textContent=`此原点已核对 ${done.size.toLocaleString()} / ${pages.length.toLocaleString()} 个施工页。页码包含阶段、工作批次、层高和分区；完成标记可以撤销。`;}
function progressStatus(message){for(const id of ['progressStatus','buildProgressStatus'])$(id).textContent=message;}
function saveProgress(){
 if(!validOrigin()){progressStatus('原点无效，未保存。');return false;}
 let persisted=false;
 try{localStorage.setItem(progressKey(),JSON.stringify(progressValue()));persisted=true;progressStatus('进度已尝试保存到当前浏览器；换浏览器或发给朋友请到“材料与分工”导出JSON。');}catch(e){progressStatus('浏览器不允许或无法本地保存；当前勾选仍在，请及时到“材料与分工”导出进度JSON。');}progressInfo();return persisted;
}
function loadProgress(){done=new Set();if(validOrigin())try{const raw=localStorage.getItem(progressKey());if(raw)done=new Set(Manual.validateProgress(JSON.parse(raw),progressContext()));progressStatus('已切换到此原点的独立进度。');}catch(e){progressStatus('没有载入本地进度：'+e.message);}else progressStatus('原点无效，不能保存进度；先填写有效原点。');progressInfo();}
function show(id){for(const n of ['start','build','systems','stock','verify'])$(n).hidden=n!==id;for(const b of $('nav').querySelectorAll('button')){b.classList.toggle('active',b.dataset.section===id);b.setAttribute('aria-pressed',String(b.dataset.section===id));}if(id==='stock')progressInfo();}
for(const b of $('nav').querySelectorAll('button'))b.onclick=()=>show(b.dataset.section);
function coordinates(){
 const o=origin(),lo=world(R.designMin),hi=world(R.designMax);
 $('worldBounds').textContent=lo?`全堡世界范围：(${lo.join(', ')}) → (${hi.join(', ')})`:'原点X、Y、Z必须全部填写有限整数。';
 const limits=['minY','maxY'].map(id=>$(id).value.trim()===''?NaN:Number($(id).value));
 $('heightCheck').textContent=lo&&limits.every(Number.isInteger)&&lo[1]>=limits[0]&&hi[1]<=limits[1]?`输入的高度范围可容纳全堡Y${lo[1]}…${hi[1]}；未检查地形、已有建筑、权限。`:'高度/原点检查不通过，停止导入；核对整数原点和维度高度。';
 $('tileRows').replaceChildren();for(const t of D.tiles){const tr=make('tr');for(const v of [t.file,world(t.designMin)?.join(', ')||'原点无效',t.size.join('×')])tr.append(make('td',v));$('tileRows').append(tr);}if(selected)inspect(selected);
}
for(const id of ['ox','oy','oz'])$(id).onchange=()=>{coordinates();loadProgress();drawPage();};for(const id of ['minY','maxY'])$(id).onchange=coordinates;
$('useCorner').onclick=()=>{const c=['cornerX','cornerY','cornerZ'].map(id=>$(id).value.trim()===''?NaN:Number($(id).value));if(!c.every(Number.isInteger)){$('worldBounds').textContent='最小角也须填写三个有限整数。';return;}['ox','oy','oz'].forEach((id,i)=>$(id).value=String(c[i]-R.designMin[i]));coordinates();loadProgress();drawPage();};
function drawLocator(){
 const pg=pages[current],x=R.designMin[0]+pg.tx*16,z=R.designMin[2]+pg.tz*16;
 let svg='<rect x="-100" y="-95" width="215" height="300" fill="#f1f2e8"/>';
 for(const[k,y]of footprint){const[a,b]=k.split(',').map(Number);svg+=`<rect x="${R.designMin[0]+a*8}" y="${R.designMin[2]+b*8}" width="8" height="8" fill="${y>45?'#708979':y>0?'#a5b7a5':'#d0d7c7'}"/>`;}
 svg+=`<rect x="${x}" y="${z}" width="${Math.min(16,R.designMax[0]-x+1)}" height="${Math.min(16,R.designMax[2]-z+1)}" fill="#edb44d" fill-opacity=".7" stroke="#925706" stroke-width="2"/><text x="0" y="-86" font-size="10" fill="#243c34">北 −Z ↑</text><text x="35" y="198" font-size="10" fill="#243c34">↓ 南 +Z</text>`;
 $('locator').innerHTML=svg;$('mapNote').textContent=`俯视范围示意（8格采样），橙框是当前16格区。X${x}…${Math.min(x+15,R.designMax[0])}，Z${z}…${Math.min(z+15,R.designMax[2])}。`;
}
function selectPage(index,focus=null){current=Math.max(0,Math.min(pages.length-1,index));const pg=pages[current];$('phase').value=String(pg.phase);populateAreas(pg);selected=focus;drawPage();}
function populateAreas(pg){
 const relevant=pages.filter(p=>p.phase===pg.phase),keys=[...new Set(relevant.map(p=>p.tx+','+p.tz))].sort((a,b)=>{const[x,z]=a.split(',').map(Number),[X,Z]=b.split(',').map(Number);return z-Z||x-X});
 $('area').replaceChildren();for(const k of keys){const[x,z]=k.split(',').map(Number);option($('area'),k,`X分区${x+1} / Z分区${z+1}`);}$('area').value=pg.tx+','+pg.tz;
 populateFloors(pg);
}
function populateFloors(pg){$('floor').replaceChildren();for(const p of pages.filter(p=>p.phase===pg.phase&&p.tx===pg.tx&&p.tz===pg.tz))option($('floor'),p.id,`${p.sub===0?'A 支撑/主体':'B 元件/挂件'} · 设计Y${p.y}`);$('floor').value=pg.id;}
function short(s){const[n,p]=s;if(n==='note_block')return '音高'+p.note;if(n==='repeater')return p.delay+'档'+({north:'↑',south:'↓',east:'→',west:'←'})[Manual.opp[p.facing]];if(n.endsWith('_stairs'))return (p.half==='top'?'倒梯':'楼梯')+({north:'↑',south:'↓',east:'→',west:'←'})[p.facing];if(n.endsWith('_slab'))return p.type==='top'?'上半砖':p.type==='double'?'双台阶':'下半砖';if(n==='piston_head')return '自动头';return cn(n).slice(0,4);}
function inspect(p){
 selected=p;const cell=blocks.get(p.join(',')),s=cell?.s,pg=pages[current],active=cell?.phase===pg.phase&&cell?.sub===pg.sub;
 $('taskBadge').textContent=!s?'留空':active?'本页要建 / 核对':`参考：第${(cell.phase+1).toString().padStart(2,'0')}阶段${cell.sub===0?'A批':'B批'}`;
 $('blockTitle').textContent=s?cn(s[0]):'空气';$('blockWorld').textContent=world(p)?`X ${world(p)[0]}\nY ${world(p)[1]}\nZ ${world(p)[2]}`:'先填写有效原点';$('blockWorld').style.whiteSpace='pre-line';$('blockDesign').textContent=`设计坐标 (${p.join(', ')})。${s&&!active?'此格不属于当前工作批次，不要在本页重复放置。':''}`;
 $('blockMethod').replaceChildren();for(const t of Manual.instructions(s,p,at,names))$('blockMethod').append(make('li',t));$('rawState').textContent=s?`minecraft:${s[0]}\n${JSON.stringify(s[1],null,2)}`:'空气';
 const actions=cellsByPage.get(pg.id),i=actions.findIndex(v=>v.p.join(',')===p.join(','));$('prevBlock').disabled=i<=0;$('nextBlock').disabled=i<0||i===actions.length-1;
 for(const e of $('grid').querySelectorAll('button'))e.classList.toggle('selected',e.dataset.pos===p.join(','));
}
function drawPage(){
 const pg=pages[current],ph=P.phases[pg.phase],cs=cellsByPage.get(pg.id),x0=R.designMin[0]+16*pg.tx,z0=R.designMin[2]+16*pg.tz,nx=Math.min(16,R.designMax[0]-x0+1),nz=Math.min(16,R.designMax[2]-z0+1);
 $('phaseGoal').textContent=ph.goal;$('phaseSteps').replaceChildren();for(const t of ph.steps)$('phaseSteps').append(make('li',t));$('phaseCheck').textContent='阶段检查：'+ph.check;
 $('pageInfo').textContent=`${ph.name} · ${pg.sub===0?'A批：先建支撑/主体':'B批：支撑全齐后装元件/挂件'} · 本阶段按A批全高→B批全高施工。当前第${current+1}/${pages.length}页，设计Y${pg.y}（世界Y${validOrigin()?pg.y+origin()[1]:'未定'}），本页${pg.count}格。${done.has(pg.id)?'已手动核对完成。':'尚未标记完成。'}${pg.phase===5?'本阶段先按机关初装顺序操作，网格仅核对最终关闭态。':''}`;
 const grid=$('grid');grid.replaceChildren();grid.style.gridTemplateColumns=`repeat(${nx+1},48px)`;grid.append(make('span','Z / X'));for(let x=x0;x<x0+nx;x++){const e=make('span',x);e.className='axis';grid.append(e);}
 for(let z=z0;z<z0+nz;z++){const ax=make('span',z);ax.className='axis';grid.append(ax);for(let x=x0;x<x0+nx;x++){
  const p=[x,pg.y,z],c=blocks.get(p.join(',')),task=c&&c.phase===pg.phase&&c.sub===pg.sub,e=btn('',()=>inspect(p));e.dataset.pos=p.join(',');e.className='cell '+(!c?'empty':task?'task':'reference');e.append(make('span',c?short(c.s):'留空'),make('small',c?(task?'本步':'参考'):''));e.setAttribute('aria-label',`设计${p.join(',')}，${c?cn(c.s[0]):'空气'}，${task?'本步':c?'参考':'留空'}`);grid.append(e);
 }}
 $('actionRows').replaceChildren();const items={};for(const[i,c]of cs.entries()){
  for(const[n,k]of Object.entries(Manual.cost(c.s)))items[n]=(items[n]||0)+k;
  const tr=make('tr');for(const v of [i+1,`${c.p[0]} / ${c.p[2]}`,cn(c.s[0])])tr.append(make('td',v));const td=make('td');td.append(btn('看坐标与摆法',()=>inspect(c.p)));tr.append(td);$('actionRows').append(tr);
 }
 $('pageMaterials').textContent='本页成品物品：'+(Object.entries(items).sort((a,b)=>b[1]-a[1]).map(([n,k])=>cn(n)+' × '+k).join('； ')||'均为自动生成部件，按专用步骤核对。');
 $('prevPage').disabled=current===0;$('nextPage').disabled=current===pages.length-1;$('undoPage').disabled=!done.has(pg.id);$('complete').disabled=!validOrigin();
 drawLocator();inspect(selected||cs[0].p);progressInfo();
}
for(const[i,ph]of P.phases.entries()){option($('phase'),i,ph.name);const card=make('div');card.className='stage';card.append(make('b',ph.name),make('p',ph.goal),btn('查看这一阶段',()=>{show('build');selectPage(pages.findIndex(p=>p.phase===i));}));$('stageCards').append(card);}
$('phase').onchange=()=>selectPage(pages.findIndex(p=>p.phase===Number($('phase').value)));
$('area').onchange=()=>{const[tx,tz]=$('area').value.split(',').map(Number);selectPage(pages.findIndex(p=>p.phase===Number($('phase').value)&&p.tx===tx&&p.tz===tz));};
$('floor').onchange=()=>selectPage(pageIndex.get($('floor').value));$('prevPage').onclick=()=>selectPage(current-1);$('nextPage').onclick=()=>selectPage(current+1);
$('prevBlock').onclick=()=>{const a=cellsByPage.get(pages[current].id),i=a.findIndex(v=>v.p.join(',')===selected?.join(','));if(i>0)inspect(a[i-1].p);};
$('nextBlock').onclick=()=>{const a=cellsByPage.get(pages[current].id),i=a.findIndex(v=>v.p.join(',')===selected?.join(','));if(i>=0&&i<a.length-1)inspect(a[i+1].p);};
$('complete').onclick=()=>{if(!validOrigin())return;done.add(pages[current].id);saveProgress();selectPage(current+1);};$('undoPage').onclick=()=>{done.delete(pages[current].id);saveProgress();drawPage();};
function locate(p){
 if(!p.every((v,i)=>Number.isInteger(v)&&v>=R.designMin[i]&&v<=R.designMax[i])){$('status').textContent='坐标须为全堡范围内的三个整数，未跳转。';show('build');return;}
 const c=blocks.get(p.join(','));if(!c){$('status').textContent='此坐标是最终空气，不属于任何施工任务。请先查邻近实体。';show('build');return;}
 const tx=Math.floor((p[0]-R.designMin[0])/16),tz=Math.floor((p[2]-R.designMin[2])/16),id=`${c.phase}:${c.sub}:${p[1]}:${tx}:${tz}`;show('build');selectPage(pageIndex.get(id),p);$('status').textContent='已定位；不会自动标记完成。';
}
$('locate').onclick=()=>locate(['px','py','pz'].map(id=>$(id).value.trim()===''?NaN:Number($(id).value)));$('begin').onclick=()=>{show('build');selectPage(0);};$('example').onclick=()=>locate([3,5,-47]);
function filterFeatures(){const q=$('featureSearch').value.trim();featureMatches=D.features.map((f,i)=>[f,i]).filter(([f])=>!q||[f.name,f.note,f.build].join(' ').includes(q));$('feature').replaceChildren();for(const[f,i]of featureMatches)option($('feature'),i,f.name);$('featureGo').disabled=!featureMatches.length;featureNote();}
function featureNote(){const f=D.features[Number($('feature').value)];$('featureNote').textContent=featureMatches.length&&f?f.note+' '+f.build:'没有匹配构件，试试“北墙”或“凸窗”。';}
$('featureSearch').oninput=filterFeatures;$('feature').onchange=featureNote;$('featureGo').onclick=()=>{const f=D.features[Number($('feature').value)];if(!f)return;let choice=null;for(const c of blocks.values())if(c.p.every((v,i)=>v>=f.region[i*2]&&v<=f.region[i*2+1])){if(!choice||c.p[1]<choice[1])choice=c.p;}if(choice)locate(choice);};filterFeatures();
function pointList(title,ps){const details=make('details'),summary=make('summary',title),list=make('ol');details.append(summary);for(const p of ps){const c=at(p),li=make('li',`设计(${p.join(', ')}) · ${c?cn(c[0]):'空气'} `);li.append(btn('看摆法',()=>locate(p)));list.append(li);}details.append(list);return details;}
for(const m of D.modules)$('moduleButtons').append(btn(m.name,()=>locate(m.input)));$('startMusic').onclick=()=>locate([23,-23,-3]);$('listenMusic').onclick=()=>locate([21,-3,4]);
for(const[i,c]of D.connections.connections.entries())option($('connection'),i,`${String(c.from).padStart(2,'0')} → ${String(c.to).padStart(2,'0')}`);
function drawConnection(){const c=D.connections.connections[Number($('connection').value)],paths=D.connections.paths.filter(p=>p.name.startsWith(String(c.from).padStart(2,'0')+'_'));$('connectionInfo').textContent=`依次核对下方5段。总延迟${c.totalTicks}红石刻：取信号1＋输入线${c.inputWireDelay}＋计时器${c.timerDelay}＋跨段线${c.linkWireDelay}＋输入中继器1。80个计时中继器按蛇形次序，不按X重新排列。`;$('connectionSteps').replaceChildren(pointList('1 取信号',[c.tapPosition]),pointList('2 输入线',paths[0].positions),pointList('3 计时器：80个中继器',c.timerPositions),pointList('4 跨模块线路',paths[1].positions),pointList('5 下一模块输入',[c.nextRelayPosition]));}
$('connection').onchange=drawConnection;drawConnection();
for(const c of D.gates){const d=make('details');d.append(make('summary',c.id+' · '+c.name),make('p',c.discovery));if(c.id!=='S3')d.append(make('p','先完成支撑/固定梯和梯背，再安装门、红石线和拉杆。拉杆OFF关闭、ON持续打开，最后OFF复位；初次沿旧路进入内侧。'));d.append(btn('定位内侧拉杆',()=>locate(c.lever)),pointList('控制件位置',[c.lever,c.leverMount,...c.wire,c.repeater,c.outputBlock,...(c.gateParts||[c.piston,c.head,c.stone,c.torch])].filter(Boolean)));$('gateCards').append(d);}
for(const r of D.routes){const tr=make('tr'),td=make('td');tr.append(make('td',r.name));td.append(btn('起点',()=>locate(r.points[0])),btn('终点',()=>locate(r.points.at(-1))));tr.append(td);$('routeRows').append(tr);}
function materials(){const g=$('materialGroup').value,counts=g==='all'?D.materials.items:D.materials.byGroup[g],q=$('materialSearch').value.trim().toLowerCase();$('materialRows').replaceChildren();for(const[n,c]of Object.entries(counts).sort((a,b)=>b[1]-a[1]))if((cn(n)+' '+n).toLowerCase().includes(q)){const tr=make('tr');for(const v of [cn(n),c.toLocaleString(),`${Math.floor(c/64)}组 + ${c%64}`])tr.append(make('td',v));$('materialRows').append(tr);}$('materialSummary').textContent=`全堡${R.totalBlocks.toLocaleString()}个非空气状态格，对应${D.materials.itemTotal.toLocaleString()}件成品、${D.materials.itemKinds}种；当前分组${Object.values(counts).reduce((a,b)=>a+b,0).toLocaleString()}件。`;}
$('materialGroup').onchange=materials;$('materialSearch').oninput=materials;materials();
$('exportProgress').onclick=()=>{if(!validOrigin()){progressStatus('先填写有效原点，才能导出。');return;}const blob=new Blob([JSON.stringify(progressValue(),null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=make('a');a.href=url;a.download='余响堡_V20施工进度.json';a.click();URL.revokeObjectURL(url);progressStatus('已请求下载进度文件；请确认浏览器下载完成。');};
$('importProgress').onchange=async()=>{
 const f=$('importProgress').files?.[0];if(!f)return;
 try{
  if(f.size>4000000)throw Error('文件过大，请选本册导出的进度JSON。');
  const loaded=Manual.validateProgress(JSON.parse(await f.text()),progressContext());
  done=new Set([...done,...loaded]);const persisted=saveProgress();drawPage();
  const result=`已合并${loaded.length}个完成页；不会清空你原来的标记。`;
  progressStatus(result+(persisted?'进度已保存到当前浏览器。':'浏览器无法本地保存，标记只在当前页面；刷新前请到“材料与分工”导出进度JSON。'));
 }catch(e){progressStatus('未导入：'+e.message);}finally{$('importProgress').value='';}
};
$('summary').textContent=`当前完整模型 ${R.totalBlocks.toLocaleString()}格 · ${R.lights}个建筑光源 · 53条普通路线 / 3捷径 · ${R.features}组构件。`;
coordinates();loadProgress();selectPage(0);

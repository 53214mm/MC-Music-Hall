// Execute the full delivered script against a minimal DOM stub. This is NOT a browser.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync(process.argv[2],'utf8');
class Element{
 constructor(tag='div'){this.tag=tag;this.children=[];this.dataset={};this.value='';this.textContent='';this.style={setProperty(){}};this.classList={toggle(){}};this.hidden=false;}
 append(...xs){this.children.push(...xs);if(this.tag==='select'&&this.children.length===xs.length)this.value=String(xs[0].value);}
 replaceChildren(...xs){this.children=[];this.append(...xs);}
 setAttribute(){} scrollIntoView(){}
 querySelectorAll(selector){return this.children.flatMap(c=>[(selector==='button'&&c.tag==='button'?c:null),...c.querySelectorAll(selector)]).filter(Boolean);}
}
const els={};
for(const m of html.matchAll(/<(\w+)[^>]*\bid="([^"]+)"[^>]*>/g)){const e=new Element(m[1]);e.value=m[0].match(/\bvalue="([^"]*)"/)?.[1]||'';els[m[2]]=e;}
// Native selects pick their first option. Populate only static defaults.
for(const[id,v]of Object.entries({group:'all',matGroup:'all'}))els[id].value=v;
const context=vm.createContext({document:{getElementById:id=>{assert.ok(els[id],id);return els[id]},createElement:t=>new Element(t)},console});
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
vm.runInContext(script,context,{timeout:30000});
assert.equal(els.gates.children.length,3);
assert.equal(els.moduleRows.children.length,11);
assert.equal(els.routeRows.children.length,53);
assert.equal(els.materialRows.children.length,88);
assert.equal(els.tileRows.children.length,324);
assert.ok(els.worldBounds.textContent.includes('32'));
context.locate([23,-23,-3]);assert.ok(els.blockDetail.textContent.includes('stone_button'));
context.locate([98,121,182]);assert.equal(els.layer.value,121);assert.ok(els.layerCount.textContent.includes('Z172…182'));
assert.equal(els.grid.querySelectorAll('button').length,29*11);
context.locate([999,0,0]);assert.ok(els.blockDetail.textContent.includes('坐标超出'));
els.group.value='music';context.drawGrid();assert.ok(els.layerCount.textContent.includes('显示0格'));
els.ox.value='100';context.coordinates();assert.ok(els.worldBounds.textContent.includes('(10, 32, -84)'));
els.minY.value='300';context.coordinates();assert.ok(els.heightCheck.textContent.startsWith('高度范围不通过'));
els.ox.value='1.5';context.coordinates();assert.ok(els.heightCheck.textContent.startsWith('原点无效'));
els.ox.value='';context.coordinates();assert.ok(els.heightCheck.textContent.startsWith('原点无效'));
console.log('Full-script DOM-stub smoke: startup, 3 gates, 53 routes, material/NBT tables, locate, edge pages, filters and origin OK; NOT browser rendering/interactions.');

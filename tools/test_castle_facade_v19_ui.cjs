// Full delivered script execution in a DOM stub, not browser rendering or interaction.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync(process.argv[2],'utf8');
class Element{
 constructor(tag='div'){this.tag=tag;this.children=[];this.value='';this.textContent='';this.style={};this.classList={add(){},remove(){}};}
 append(...xs){this.children.push(...xs);if(this.tag==='select'&&this.children.length===xs.length)this.value=String(xs[0].value);}
 replaceChildren(...xs){this.children=[];this.append(...xs);}
 setAttribute(){}
 querySelectorAll(s){return this.children.flatMap(c=>[(s==='button'&&c.tag==='button'?c:null),...c.querySelectorAll(s)]).filter(Boolean);}
}
const els={};
for(const m of html.matchAll(/<(\w+)[^>]*\bid="([^"]+)"[^>]*>/g)){const e=new Element(m[1]);e.value=m[0].match(/\bvalue="([^"]*)"/)?.[1]||'';els[m[2]]=e;}
const context=vm.createContext({document:{getElementById:id=>{assert.ok(els[id],id);return els[id]},createElement:t=>new Element(t)},console});
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];vm.runInContext(script,context,{timeout:30000});
const payload=JSON.parse(html.match(/const P=([\s\S]*?),\$=id=>/)[1]);
assert.equal(els.view.children.length,20);
assert.equal(els.materials.children.length,new Set([...Object.keys(payload.materials.placeItems),...Object.keys(payload.materials.dismantleItems)]).size);
for(let i=0;i<els.view.children.length;i++){
 els.view.value=String(i);els.view.onchange();
 const r=i<3?payload.views[i].region:payload.features[i-3].region;
 assert.equal(els.grid.querySelectorAll('button').length,(r[1]-r[0]+1)*(r[5]-r[4]+1));
 els.y.value='9999';els.y.onchange();assert.equal(Number(els.y.value),r[3]);assert.equal(els.up.disabled,true);
 els.y.value='-9999';els.y.onchange();assert.equal(Number(els.y.value),r[2]);assert.equal(els.down.disabled,true);
}
context.detail('21,30,-46');assert.ok(els.detail.textContent.includes('lantern'));assert.ok(els.detail.textContent.includes('世界(21, 110, -46)'));
assert.ok(els.detail.textContent.includes('原 空气'));assert.ok(els.detail.textContent.includes('新 '));
els.ox.value='';context.detail('21,30,-46');assert.ok(els.detail.textContent.includes('原点须填写'));
els.ox.value='1.5';context.detail('21,30,-46');assert.ok(els.detail.textContent.includes('原点须填写'));
els.ox.value='100';context.detail('21,30,-46');assert.ok(els.detail.textContent.includes('世界(121, 110, -46)'));
els.view.value='0';els.view.onchange();els.grid.querySelectorAll('button')[0].onclick();assert.ok(els.detail.textContent.startsWith('设计('));
console.log('V19 full-script DOM stub: 20 views, layer clamps, grid clicks, materials, before/after and origin validation OK. NOT a browser test.');

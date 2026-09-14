// Test pure coordinate/material/display transforms from the shipped HTML. No browser.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync(process.argv[2],'utf8');
const d=JSON.parse(html.split('const D=')[1].split(',$=id=>')[0]);
const ctx=vm.createContext({});
for(const name of ['world','cost','match']){
  const line=html.split('\n').find(l=>l.startsWith(`function ${name}(`));
  assert.ok(line,`Missing ${name}`);vm.runInContext(line,ctx);
}
vm.runInContext("const lights=new Set(['lantern','sea_lantern','ochre_froglight'])",ctx);
const norm=v=>JSON.parse(JSON.stringify(v));
assert.deepEqual(norm(ctx.world([-90,-48,-84],[100,80,200])),[10,32,116]);
assert.deepEqual(norm(ctx.cost('spruce_slab',{type:'double'})),{spruce_slab:2});
assert.deepEqual(norm(ctx.cost('iron_door',{half:'upper'})),{});
assert.equal(ctx.match(['note_block',{},'01'],'music'),true);
assert.equal(ctx.match(['stone',{},'terrain'],'shell'),false);
const count={};
for(const b of d.blocks){const s=d.palette[b[3]];for(const[n,c]of Object.entries(ctx.cost(s[0],s[1])))count[n]=(count[n]||0)+c;}
assert.deepEqual(count,d.materials.items);
for(const p of [[-90,-48,-84],[98,121,182],[23,-23,-3]]){
  const tile=d.tiles.find(t=>p.every((v,i)=>v>=t.designMin[i]&&v<t.designMin[i]+t.size[i]));
  assert.ok(tile);assert.equal(Math.floor((p[0]+90)/32),tile.offset[0]/32);
}
console.log('UI pure transforms: coordinates, filters, edge tile mapping, 521445 material cells OK (not browser interaction).');

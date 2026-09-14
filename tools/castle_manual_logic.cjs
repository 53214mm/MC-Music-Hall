// Pure shared logic for the offline page and Node regression tests.
const Manual=(()=>{
 const cn={north:'北（−Z）',south:'南（+Z）',east:'东（+X）',west:'西（−X）',up:'上',down:'下'},opp={north:'south',south:'north',east:'west',west:'east'};
 const cost=s=>{if(!s)return {};const[n,p]=s;if(n==='piston_head'||n.endsWith('_door')&&p.half==='upper')return {};if(n.startsWith('potted_'))return {flower_pot:1,[n.slice(7)]:1};return {[({redstone_wire:'redstone',redstone_wall_torch:'redstone_torch'})[n]||n]:n.endsWith('_slab')&&p.type==='double'?2:1}};
 function instructions(s,pos,get,names){
  if(!s)return ['留空。这是最终模型的空气，不是缺失数据；不要填实。'];
  const[n,p]=s,dir=cn[p.facing]||p.facing,name=names[n]||n,below=get([pos[0],pos[1]-1,pos[2]]),above=get([pos[0],pos[1]+1,pos[2]]);let a=[];
  if(n==='piston_head')return ['不要手放活塞头，也不用为它备料。','按S3专用初装顺序操作，活塞伸出后自动生成这里的头。'];
  if(pos.join(',')==='55,3,32')return ['S3闩石的最终关闭位置；初装不能在此硬放。','先让上方黏性活塞收回，把1块雕纹砂岩放在设计(55,4,32)，再按S3步骤通电伸出到此处。'];
  if(n.endsWith('_door')&&p.half==='upper')return ['由下半门自动生成，不再放第二扇门。','先安装下方一格的门，再检查上下两半闭合一致。'];
  a.push(`物品：${name}。放在卡片给出的世界“方块坐标”，不是玩家脚底坐标。`);
  if(n==='note_block')a.push(`全新、未调音音符盒从0开始：右击${p.note}次。已有盒不能再次直接累计点击。`,`下方应为${below?(names[below[0]]||below[0]):'空气（异常，先检查）'}；上方应留空${above?'，当前模型有方块，停止检查':'。'}`);
  else if(n==='repeater')a.push(`信号由${cn[p.facing]}输入，向${cn[opp[p.facing]]}输出。沿输出箭头接下一段。`,`${p.delay}档：新放1档后右击${Number(p.delay)-1}次，不要照输入侧箭头反接。`);
  else if(n.endsWith('_stairs'))a.push(`${p.half==='top'?'倒置楼梯：占格子的上半主体，可点上方方块底面或相邻方块侧面的上半部安装。':'普通楼梯：下半主体，先在支撑块上安装。'}`,`几何升高方向：${dir}。${p.shape&&p.shape!=='straight'?'此处是拐角楼梯，先按朝向放，再搭相邻楼梯让拐角自动形成。':'装齐邻块后再核对是否被自动变成拐角。'}`);
  else if(n.endsWith('_slab'))a.push(p.type==='double'?'同一格放2个同材台阶，合成双台阶。':p.type==='top'?'上半台阶：占本格上半；点相邻块侧面的上半部或上方块底面安装。':'下半台阶：占本格下半；点下方支撑顶面安装。');
  else if(n==='lantern'||n==='soul_lantern')a.push(p.hanging==='true'?`悬挂灯：先完成上方的${above?(names[above[0]]||above[0]):'支撑（先检查）'}，再点其底面挂灯。`:`落地灯：先完成下方的${below?(names[below[0]]||below[0]):'支撑（先检查）'}，再放灯。`);
  else if(n==='ladder')a.push(`梯子正面朝${dir}，背后的承重块在${cn[opp[p.facing]]}一侧。先搭梯背，再从下面接上来。`);
  else if(n==='grindstone')a.push(`安装面：${({floor:'地面，点下方支撑的顶面',wall:'墙面，点对应墙的侧面',ceiling:'天花板倒挂，点上方梁的底面'})[p.face]}；正面朝${dir}。`,'先完成梁/墙支撑，再安装砂轮；它在本建筑中也用于装饰构件。');
  else if(n==='sticky_piston'||n==='piston')a.push(`活塞头朝${dir}。本体先安装，伸缩和闩石位置按S3专用步骤处理，不能手放头。`);
  else if(n==='lever'||n.endsWith('_button'))a.push(`安装面：${({floor:'地面',ceiling:'天花板',wall:'墙面'})[p.face]||'见完整状态'}；朝${dir}。`,`最终${p.powered==='true'?'开启':'关闭'}。机关阶段必须先接支撑和线路，未验收前不要连续触发。`);
  else if(n==='redstone_wall_torch')a.push(`火把向${dir}伸出，支撑块在${cn[opp[p.facing]]}一侧。`,`目标${p.lit==='true'?'亮':'灭'}由电路决定，不是右击设置；S3最后按专用顺序装。`);
  else if(n==='redstone_wire')a.push('先有下面的承重块，再放红石粉；按“音乐与机关”查看整段顺序。线的连接形状由邻块自动更新。');
  else if(n.endsWith('_trapdoor'))a.push(`${p.half==='top'?'上半安装':'下半安装'}；朝${dir}。最终${p.open==='true'?'打开为竖直':'关闭为水平'}。`,n==='iron_trapdoor'?'铁活板门不能手动右击开关，按S2电路控制。':'木活板门可右击切换；此处可能是椅背/柜门造景，不要当作房间入口。');
  else if(n.endsWith('_door'))a.push(`只在本格放1扇完整门；正面朝${dir}，铰链${p.hinge==='left'?'左侧':'右侧'}。`,'铁门按电路开关；若铰链相反，检查门两侧邻块和放置位置后重装。');
  else if(n.endsWith('_wall')||n.endsWith('_fence')||n.endsWith('_pane')||n==='iron_bars')a.push('这是细形方块，不是整块石柱。先放指定材料；连接臂由周围方块自动形成，整组搭完再核对。');
  else if(n.startsWith('potted_'))a.push(`先放花盆，再插入${names[n.slice(7)]||n.slice(7)}；不是直接拿“盆栽方块”施工。`);
  else if(p.axis)a.push(`长轴/纹路沿${({x:'东西（X轴）',y:'上下（Y轴）',z:'南北（Z轴）'})[p.axis]}；先用临时邻块辅助对齐，之后移除。`);
  else a.push('按图放置；没有朝向属性的整块无需旋转。');
  if(p.facing&&!a.some(t=>t.includes('朝')||t.includes('输入')))a.push(`方块正面朝${dir}。`);
  if(['barrel','furnace','lectern'].includes(n))a.push('默认空置，不装物品/燃料/书。');
  return a;
 }
 function validateProgress(v,c){
  if(!v||v.version!==1||v.modelHash!==c.hash)throw Error('进度版本不匹配，请使用这本V20总册导出的进度。');
  if(!Array.isArray(v.origin)||v.origin.length!==3||!v.origin.every(Number.isInteger)||v.origin.some((n,i)=>n!==c.origin[i]))throw Error('原点不同：先把本页原点改为朋友使用的相同坐标，再导入。');
  if(!Array.isArray(v.done)||v.done.length>c.ids.size||v.done.some(id=>typeof id!=='string'||!c.ids.has(id))||new Set(v.done).size!==v.done.length)throw Error('进度文件包含无效或重复施工页，未导入。');
  return v.done.slice();
 }
 return {cn,opp,cost,instructions,validateProgress};
})();
if(typeof module!=='undefined')module.exports=Manual;

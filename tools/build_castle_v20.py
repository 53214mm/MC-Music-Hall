"""V20 full offline release with a novice-facing construction plan."""
import argparse,gzip,hashlib,json,zipfile
from pathlib import Path
from castle_v20 import model_v20,SOURCE,OUT,TITLE
from castle_detail import ROOT
from build_craft_integration import encode
from build_music_hall import encode_structure
from castle_release import material_report,tile_manifest,tile_blocks
from castle_manual import manual_plan
from castle_finish import EMISSION
from vanilla_mesh import VanillaAssets,JAR

def dump(p,obj):
    text=json.dumps(obj,ensure_ascii=False,separators=(',',':'))
    if not p.exists() or p.read_text(encoding='utf-8')!=text:p.write_text(text,encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--skip-nbt',action='store_true');args=ap.parse_args()
    m=model_v20();d=m['data'];b=m['after'];OUT.mkdir(exist_ok=True);(OUT/'structure_tiles').mkdir(exist_ok=True)
    meta=dict(features=m['features'],fixtures=m['fixtures']);assets=VanillaAssets();colors=dict(d['colors'])
    for p in sorted(m['changed']):
        if p in b:
            n,pr,_=b[p];assets.elements(n,tuple(sorted(pr.items())))
            if n not in colors:colors[n]=assets.swatch(n,tuple(sorted(pr.items())))
    full={**d,**encode(b,d['offset']),'colors':colors,'sidewallV20':meta,'features':d['features']+m['features'],'fixtures':d['fixtures']+m['fixtures']}
    full['report']={'version':'V20','source':'V19','sourceHash':sha(SOURCE),'totalBlocks':len(b),'features':len(full['features']),
        'changedCoordinates':len(m['changed']),'added':len(set(b)-set(m['before'])),'removed':len(set(m['before'])-set(b)),
        'replaced':len(m['changed']&set(b)&set(m['before'])),'lightBlocks':sum(s[0] in EMISSION for s in b.values()),
        'oldLightBlocks':541,'newLights':2,'musicBlocks':32260,'noteBlocks':2307,'routes':53,'shortcuts':3,
        'target':'26.3-snapshot-9','dataVersion':5011,'designMin':d['report']['designMin'],'designMax':d['report']['designMax'],
        'newNBT':True,'browserTest':False,'inGameTest':False}
    dump(OUT/'castle_v20.json',full);dump(OUT/'v20_changes.json',[dict(pos=p,before=m['before'].get(p),after=b.get(p)) for p in sorted(m['changed'])]);dump(OUT/'sidewall.json',meta)
    mat=material_report(b);dump(OUT/'materials.json',mat)
    tiles=tile_manifest(full['report']['designMin'],full['size'])
    if args.skip_nbt:
        saved=json.loads((OUT/'tile_manifest.json').read_text(encoding='utf-8'));assert len(saved)==len(tiles)
        for t,v in zip(tiles,saved):assert all(v[k]==x for k,x in t.items())
        tiles=saved
    else:
        for t in tiles:
            part=tile_blocks(b,t);f=OUT/'structure_tiles'/t['file'];f.write_bytes(gzip.compress(encode_structure(part,5011),mtime=0));t.update(nonAir=sum(s[0]!='air' for s in part.values()),sha256=sha(f))
            if t['order']%54==0:print(f'NBT {t["order"]}/324',flush=True)
        dump(OUT/'tile_manifest.json',tiles)
    plan=manual_plan(full,b);dump(OUT/'construction_plan.json',plan)
    sources=[SOURCE,ROOT/'castle_v3/watch_v17/castle_v17.json',*sorted((ROOT/'nbt_save').glob('*.nbt'))]
    report=dict(version='V20',modelHash=sha(OUT/'castle_v20.json'),target='26.3-snapshot-9',dataVersion=5011,targetJarHash=sha(Path(JAR)),
        sourceHashes={str(p.relative_to(ROOT)):sha(p) for p in sources},size=full['size'],designMin=full['report']['designMin'],designMax=full['report']['designMax'],
        totalBlocks=len(b),materialItems=mat['itemTotal'],materialKinds=mat['itemKinds'],tiles=len(tiles),airInclusiveCells=189*170*267,airCells=189*170*267-len(b),
        ordinaryRoutes=53,shortcuts=3,musicBlocks=32260,noteBlocks=2307,lights=sum(s[0] in EMISSION for s in b.values()),features=len(full['features']),
        constructionPages=len(plan['pages']),newChanges=len(m['changed']),browserTest=False,inGameTest=False,worldsModified=False,
        constructionPlanHash=sha(OUT/'construction_plan.json'),progressKeyHash=hashlib.sha256((sha(OUT/'castle_v20.json')+sha(OUT/'construction_plan.json')).encode()).hexdigest())
    dump(OUT/'release_report.json',report)
    modules=[]
    for i in range(1,12):
        g=str(i).zfill(2);ps=[p for p,s in b.items() if s[2]==g]
        modules.append(dict(group=g,name=f'{g}号音乐模块',count=len(ps),min=[min(p[k] for p in ps) for k in range(3)],max=[max(p[k] for p in ps) for k in range(3)],input=[23,-23,-3] if i==1 else d['connections']['connections'][i-2]['nextRelayPosition']))
    names={**d['names'],'redstone':'红石粉','redstone_torch':'红石火把','iron_chain':'铁链','cut_sandstone':'切制砂岩','sandstone_wall':'砂岩墙','gray_stained_glass_pane':'灰色染色玻璃板','flower_pot':'花盆','oxeye_daisy':'滨菊'}
    payload=dict(palette=full['palette'],blocks=full['blocks'],offset=full['offset'],names=names,colors=colors,report=report,plan=plan,materials=mat,tiles=tiles,
        features=[dict(name=f['name'],region=f['region'],note=f.get('note',''),build=f.get('build','')) for f in full['features']],modules=modules,
        routes=full['routes'],connections=full['connections'],gates=[*full['shortcutsV14']['shortcuts'],full['serviceV15']['shortcut']])
    template=ROOT/'tools/castle_v20_viewer.html'
    if template.exists():
        html=template.read_text(encoding='utf-8').replace('__DATA__',json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
        html=html.replace('__LOGIC__',(ROOT/'tools/castle_manual_logic.cjs').read_text(encoding='utf-8')).replace('__UI__',(ROOT/'tools/castle_v20_ui.js').read_text(encoding='utf-8'))
        (OUT/TITLE).write_text(html,encoding='utf-8')
    guide=['# 余响堡 V20：从空地开始的施工顺序','', '本册已合并V19主墙和V20侧墙修饰。从零建造只用V20，不能累加旧版采购表或重复叠加NBT。无需Python、无需联网。','',
           '## 先读坐标','', 'O是设计(0,0,0)对应的世界方块坐标，不是全堡最小角，也不随构件变化。示例O=(100,80,200)：设计(3,5,-47)→世界(103,85,153)。全堡范围从O+(-90,-48,-84)至O+(98,121,182)，不是已检查过的服务器场地。图中Y是目标方块/路线支撑块的坐标，不是玩家脚底。','',
           '## 工作台怎么用','', '选择施工阶段→从该阶段首个施工页开始→按本层动作清单逐格放→核对→标记本页完成→下一施工页。每页16×16，每阶段先A批支撑/主体的全部高度，再B批元件/挂件的全部高度；每批按Y从低到高、同层分区扫描。这样跨分区的墙火把也有先建好的承重块。黄色并标“本步”的格子才是本页任务；“参考”是别阶段/批次实体，不能填空或拆掉。普通空气写“留空”。第06阶段是特例，按机关专用初装顺序操作，不机械照最终关闭态逐Y放。', '',
           '现场需要临时脚手架、垫脚和防跌落设施，未计入模型/备料。不要照实心地基填满全部方框，灰色岩体只按图中的实体表层和支撑建造。','']
    for phase in plan['phases']:guide += [f'## {phase["name"]}','',phase['goal'],'']+[f'{i+1}. {v}' for i,v in enumerate(phase['steps'])]+['', '检查：'+phase['check'],'']
    oldguide=(ROOT/'castle_v3/release_v18/施工与隔离测试.md').read_text(encoding='utf-8')
    inherited=oldguide[oldguide.index('## 音乐连接与启动'):].replace('V18','V20').replace('echo_v18','echo_v20')
    inherited=inherited.replace('8,057,265',f'{report["airCells"]:,}').replace('342灯笼',f'{sum(s[0]=="lantern" for s in b.values())}灯笼')
    inherited=inherited.replace('模块界面中R数字为中继器档位（新放后右击档位-1次），箭头为输出；N数字为新音符盒右击次数。','V20格子中“1档/2档…”为中继器档位（新放后右击档位-1次），箭头为输出；“音高”数字为新音符盒右击次数，详细操作见中文卡片。')
    guide+=['## 进度与分工','', '每人先设相同O；阶段→A/B批次→层→分区编号用于分工，B批须等待该阶段全部A批完成。完成标记仅表示你自行核对，不是游戏检测。当前浏览器尝试本地保存，失败会提示；导出进度JSON可发给朋友，导入时核对模型哈希/原点/页码。合并完成页，不自动共享或远程同步。换原点会切换一套独立进度，不把旧场地勾选套到新位置。','',inherited]
    (OUT/'施工方法与验收.md').write_text('\n'.join(guide)+'\n',encoding='utf-8')
    lines=['# V20全堡成品材料','',mat['note'],'',f'完整模型{len(b):,}格；成品物品{mat["itemTotal"]:,}件、{mat["itemKinds"]}种。已合并V19/V20，不能再加旧增量。','','| 材料 | 成品数量 | 组+余数 |','|---|---:|---|']
    lines += [f'| {names.get(n,n)} `{n}` | {c} | {c//64}组+{c%64} |' for n,c in sorted(mat['items'].items(),key=lambda v:-v[1])]
    (OUT/'全堡材料表.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (OUT/'先看这里.md').write_text(f'# 余响堡 V20\n\n双击“{TITLE}”。按开始→施工工作台→音乐与机关→材料→验收的目录使用。发给朋友请发整个release_v20文件夹或完整ZIP；不能只发HTML。\n\n这是完整新版，已合并V19/V20；旧V18包保留作历史。324个NBT含空气，会覆盖189×170×267范围，只供独立备份创造测试区，不能覆盖朋友服务器。手建不需要NBT。\n\n先读施工方法与验收.md。配图为实际模型离线渲染；静态检查不等于浏览器/游戏实测。\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)

if __name__=='__main__':main()

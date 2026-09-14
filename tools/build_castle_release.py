"""Portable V18 construction bundle, explicitly not game-tested or auto-installed."""
import argparse
import gzip
import hashlib
import json
import shutil
import zipfile
from collections import Counter
from pathlib import Path
from castle_release import ROOT,SOURCE,OUT,TITLE,material_report,tile_manifest,tile_blocks
from castle_detail import read_model
from build_music_hall import encode_structure
from vanilla_mesh import JAR
from castle_finish import EMISSION

def dump(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def write_guides(d,b,report,mat,tiles,names):
    def cn(n):return names.get(n,n)
    lines=['# 余响堡 V18 全堡成品物品表','',mat['note'],'',
        f'非空气方块 {len(b):,} 格；成品物品 {mat["itemTotal"]:,} 个，{mat["itemKinds"]} 种。所有数字对应 V17 完整模型，没有再次更换造型。',
        '', '建筑、岩体、音乐分组为互斥统计。建筑内包含三套捷径电路；音乐列只含11段原机与连接。岩体为设计表层，不能将该列从NBT里直接删除后声称仍可用。',
        '', '| 成品物品 | 建筑/机关 | 岩体表层 | 音乐/连接 | 合计 | 组+余数 | 占用背包格 |', '|---|---:|---:|---:|---:|---|---:|']
    for n,c in sorted(mat['items'].items(),key=lambda kv:(-kv[1],kv[0])):
        g=mat['byGroup'];lines.append(f'| {cn(n)} `{n}` | {g["shell"].get(n,0)} | {g["terrain"].get(n,0)} | {g["music"].get(n,0)} | {c} | {c//64}组+{c%64} | {(c+63)//64} |')
    slots=sum((c+63)//64 for c in mat['items'].values())
    lines += ['',f'若按物品类型分别码放，共 {slots:,} 格库存容量；等效至少 {(slots+53)//54} 个大箱子的容量（不是摆放规划，未计箱子本身）。',
        '', '## 特殊计数','', '铁门上下两格只备1个门；活塞头由黏性活塞伸出生成，不购买或手摆。双台阶按2个台阶；普通上/下台阶按1个。盆栽拆为1花盆+1滨菊。红石线按红石粉物品，墙上红石火把按红石火把物品。',
        '桶、熔炉、讲台为空；没有燃料、物品、谱本、实体或可睡眠的床。普通书架按整个书架物品。所有木椅/木床为造景。',
        '', '## 原始方块状态数量','', '| 方块 ID | 格数 |','|---|---:|']
    lines += [f'| `{n}` | {c} |' for n,c in sorted(mat['blocks'].items(),key=lambda kv:-kv[1])]
    (OUT/'全堡材料表.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    guides=['# V18 施工、连接与隔离测试','',
        '这是当前全堡施工候选包，不是已经通过实机验收的生存开工保证。先在独立创造档完成下方验证，再决定在朋友服务器建造；本程序没有修改存档或服务器。',
        '', '## 坐标：统一一种起点','',
        '- O = 城堡设计原点在世界里的坐标，不是全堡最小角。世界坐标 = O + 图中设计坐标。',
        '- 全堡设计范围 X=-90…98，Y=-48…121，Z=-84…182；尺寸189×170×267。JSON offset=(90,48,84)只用于数组索引，不再叠加到世界坐标。',
        '- 例如纯演算 O=(100,80,200)，全堡世界范围=(10,32,116)…(198,201,382)。这不是已检查过的服务器空地。',
        '- 路线Y表示支撑块坐标；一般站立脚底为Y+1。自定义维度要另查建造高度。网页可输入已知高度上下限，检查整个覆盖范围。',
        '', '## 手建顺序','',
        '1. 放样设计原点与外包范围，按道路/内堡/塔楼定位。先做基础、楼板、支撑柱、梁、楼梯和临时护栏。网格隐藏筛选不表示空气；确实空气显示“空”。',
        '2. 先完成所有通路骨架，再铺岩体表层。必须保留桥洞、地下池、音乐舱和三格路线空气，不能填满山体。',
        '3. 建11个原音乐模块与10条连接：网页逐条定位取信号、输入线、80个计时中继器、跨模块线、下一输入。音乐分组和连接分组不得换材。',
        '4. 未封屋顶时逐段试听，再连播全曲。音符盒上方保持空气，下方材质决定乐器；中继器按输出方向和档位摆。',
        '5. 建暖石/砖墙、凹窗、扶壁、深色坡顶；由下至上摆倒楼梯托架、台阶、墙、栅栏、玻璃片、活板门。实际自动连接更新后再次对照状态。',
        '6. 安装所有照明与室内家具，逐层核对最新53条普通路线，再装S1/S2/S3。椅背活板门需开到竖直状态，讲台不放书。',
        '7. 进行夜间、双向行走、门闩和试听验收，通过后才转生存。按楼层分工时共用一个O，不各自选起点。',
        '', '## 音乐连接与启动','',
        '- 主按钮设计(23,-23,-3)，试听台支撑块(21,-3,4)。听众提前到台上，朋友从维护区按按钮；不要播放中重复按。主按钮维护接近方式还需实机核对。',
        '- 01→02至09→10各320红石刻；10→11为322，补偿第11段内部启动差。正常20游戏刻/秒时分别为32秒/32.2秒的电路延迟；不要把末条改成320。',
        '- 整机仅从音乐馆位置下移32格，当前图已经换算；不要再减32。02—11正面是输入中继器，保留侧面测试按钮。',
        '- 模块界面中R数字为中继器档位（新放后右击档位-1次），箭头为输出；N数字为新音符盒右击次数。原NBT中11块生成器告示牌沿用既定省略，不把文字伪装成已写入。保留原始文件及署名资料。',
        '', '## 三套捷径初装与验收','']
    for c in d['shortcutsV14']['shortcuts']:
        guides += [f'### {c["id"]} {c["name"]}','',f'内侧拉杆{c["lever"]}；门/活板门{c["gate"]}。'+(f'中继器{c["repeater"]}。' if 'repeater' in c else '本支路不含独立中继器，沿图中红石粉接入。'),
                   c['discovery'],c['reset'],'先搭支撑和路线/梯子，再安装门、线和拉杆；初始拉杆OFF关闭，ON持续开启，最后OFF复位。旧“拆栏杆/补6梯”已废弃。','']
    guides += ['### S3 维修道升降石闩','',
        '先搭廊道/门框及电路承重块。黏性活塞本体(55,5,32)朝下，暂不装墙火把；保持其收回。在(55,4,32)放1块雕纹砂岩，(55,3,32)先留空。',
        '按网页搭7格红石线、中继器(58,5,32)朝东（向西输出）、内侧拉杆(57,3,26)。将拉杆置ON，确认输出块(57,5,32)已供电，再在其西面(56,5,32)安装朝西的墙火把，应保持熄灭。',
        '缓慢OFF：火把亮，活塞向下伸出，砂岩移到(55,3,32)，活塞头自动出现在(55,4,32)。缓慢ON：火把灭，活塞收回，砂岩回到Y4，Y3恢复空气。确认后OFF留作默认关闭。不要手放活塞头；不要连点或使用短脉冲。',
        '此处只有一格宽、两格净高的开启洞口，其余维修道三格宽。它挡普通站立/蹲伏通行，但不是权限锁，不能防拆或防爬行。',
        '上述是按已核对静态两稳态制定的待实测安装顺序，不是游戏测试记录。若NBT载入后活塞/门状态异常，停下测试，先定位问题；不要批量重贴旧NBT或往音乐区补红石。',
        '', '## NBT：完整空气覆盖，高风险','',
        f'{len(tiles)}个不重叠32格分块（边缘缩短），共{report["airInclusiveCells"]:,}格，含{report["airCells"]:,}空气。纯空气分块也属于精确模型。覆盖区域内原建筑、地形等会被替换/清空，不能恢复请勿加载。',
        '只复制到你已备份的独立空白创造测试世界；不要操作朋友服务器。本包没有自动命令/安装器，也没有随包运行脚本。不是已有城堡重置包：未显式写容器NBT，覆盖现有同类桶/熔炉/讲台不保证清掉旧物品或书。',
        '本机26.3-snapshot-9已核对目录为 <测试世界>/generated/echo_v18/structure/（单数structure）。将structure_tiles里的NBT复制进去。结构名称示例 echo_v18:castle_0_0_0，不带.nbt，不混用旧版structures或数据包目录。',
        '清单按底层到顶层排序。每块目标最小角=O+清单designMin；旋转0°、无镜像、完整性1.0、不含实体、严格放置ON。严格放置可跳过部分放置/形状更新，不代表游戏动力学已经验证。',
        '推荐在当前块的目标最小角临时放结构方块，相对位置(0,0,0)，由当前完整含空气NBT覆盖它自身。首次尺寸不同可能只出现准备边框，须再次加载至成功，并确认临时方块已变成该格的目标方块/空气。此方案依据目标版本代码，仍需实测。',
        '如果你选在目标角正下方放结构方块并设(0,1,0)，那格可能属于已加载的下层：务必记录位置，完成后按图恢复原方块或空气；当前块不会替你清掉下层的临时结构方块。临时垫脚块同样需移除/恢复。',
        '所有分块必须加载完才启动。分块会切过红石与墙/楼梯，加载期间可能产生掉落、形状更新、瞬态信号；底层优先不等于免更新或稳定运行。导出默认关闭的活塞头只是参考状态，不保证运行时载入后仍保持。',
        '加载完：先核对跨分块线路/门/梯和音符盒底材、上方空气，再逐一ON/OFF调试三机关并保存重进。发现缺块时只在测试档按坐标修复后重新验收，不把“文件回读通过”当运行通过。',
        '', '## 实机验收记录（目前全部待验）','',
        '- [ ] 全部324块定位正确，无重叠、遗漏或范围外覆盖；目标游戏版本确认。',
        '- [ ] 53条普通路线及3捷径双向实走，不需飞行；半格踏步、转弯、梯口、护栏防跌落通过。',
        '- [ ] 三机关ON/OFF后各保存退出重进；无活塞掉头/丢块/门两半不一致，无邻接触发音乐。',
        '- [ ] 检查342灯笼、146赭黄蛙明灯、51海晶灯及实际夜间暗角；灯数不是防刷怪证明。',
        '- [ ] 11段单独试听通过；整曲不中断，无重触发、接缝错拍、缺音；服务器模拟距离/TPS满足播放。',
        '- [ ] 网页交互由用户手动打开检查；本轮仅静态文件/脚本/配图检查。',
        '', '详细逐格分块位置在tile_manifest.json和网页NBT页；每块SHA256在清单内，离线分享见先看这里.md。']
    (OUT/'施工与隔离测试.md').write_text('\n'.join(guides)+'\n',encoding='utf-8')
    (OUT/'先看这里.md').write_text(f'# 余响堡 V18 统一施工包\n\n双击“{TITLE}”，无需Python、服务器或联网。发给朋友请发送整个release_v18目录，或解压同级ZIP后再打开；不要只发HTML漏掉PNG。\n\nV18完整数据与V17一模一样；不是再改外观。324个NBT只供隔离创造档测试，含空气，会清空整个189×170×267范围。先读“施工与隔离测试.md”，不能在朋友服务器盲目覆盖。旧版NBT/增量包不再叠加。\n\n三个常用入口：网页逐层搭法、全堡材料表.md、施工与隔离测试.md。verification.json记录静态审计；SHA256SUMS.json供解压核对。全部实机项目仍待验，审计不等于实测。\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--skip-nbt',action='store_true');args=parser.parse_args()
    d,b=read_model(SOURCE);OUT.mkdir(exist_ok=True);(OUT/'structure_tiles').mkdir(exist_ok=True)
    low=d['report']['designMin'];size=d['size'];tiles=tile_manifest(low,size);mat=material_report(b)
    assert len(b)==521445 and mat['blocks']['note_block']==2307
    names={**d['names'],'redstone':'红石粉','redstone_torch':'红石火把','iron_door':'铁门','sticky_piston':'黏性活塞'}
    with zipfile.ZipFile(JAR) as jar:
        files=set(jar.namelist());version=json.loads(jar.read('version.json'))
        assert version['world_version']==5011
        for n in mat['items']:assert f'assets/minecraft/items/{n}.json' in files,('Missing item',n)
    source_hashes={str(p.relative_to(ROOT)):sha(p) for p in [SOURCE,*sorted((ROOT/'nbt_save').glob('*.nbt'))]}
    if args.skip_nbt:
        old=json.loads((OUT/'tile_manifest.json').read_text(encoding='utf-8'))
        for m,n in zip(tiles,old):assert all(n[k]==v for k,v in m.items())
        assert len(old)==len(tiles);tiles=old
    else:
        for m in tiles:
            tile=tile_blocks(b,m);path=OUT/'structure_tiles'/m['file']
            path.write_bytes(gzip.compress(encode_structure(tile,5011),mtime=0))
            m.update(nonAir=sum(s[0]!='air' for s in tile.values()),sha256=sha(path))
            if m['order']%54==0:print(f'NBT {m["order"]}/{len(tiles)}',flush=True)
        dump(OUT/'tile_manifest.json',tiles)
    total=size[0]*size[1]*size[2]
    report=dict(version='V18',modelVersion='V17',target=version['id'],dataVersion=version['world_version'],
        sourceHashes=source_hashes,targetJarHash=sha(Path(JAR)),totalBlocks=len(b),airInclusiveCells=total,airCells=total-len(b),
        size=size,designMin=low,designMax=d['report']['designMax'],tiles=len(tiles),materialItems=mat['itemTotal'],
        routes=len(d['routes']),shortcuts=3,lightBlocks=sum(s[0] in EMISSION for s in b.values()),
        musicBlocks=sum(s[2]=='control' or s[2].isdigit() for s in b.values()),noteBlocks=2307,
        changedModelCoordinates=0,browserTest=False,inGameTest=False,worldsModified=False,
        status='静态施工与NBT测试候选包，未经游戏更新/行走/光照/全曲试听验收。')
    shutil.copyfile(SOURCE,OUT/'castle_v17.json')
    dump(OUT/'materials.json',mat);dump(OUT/'release_report.json',report)
    write_guides(d,b,report,mat,tiles,names)
    features=[dict(name=f['name'],region=f['region'],note=f.get('note',''),build=f.get('build','')) for f in d['features']]
    gates=[*d['shortcutsV14']['shortcuts'],d['serviceV15']['shortcut']]
    modules=[]
    for i in range(1,12):
        group=str(i).zfill(2);cells={p:s for p,s in b.items() if s[2]==group}
        modules.append(dict(number=i,group=group,blocks=len(cells),
            designMin=[min(p[k] for p in cells) for k in range(3)],designMax=[max(p[k] for p in cells) for k in range(3)],
            input=[23,-23,-3] if i==1 else d['connections']['connections'][i-2]['nextRelayPosition'],
            buttons=[p for p,s in cells.items() if s[0]=='stone_button']))
    payload=dict(palette=d['palette'],blocks=d['blocks'],offset=d['offset'],size=size,names=names,colors=d['colors'],
        report=report,materials=mat,tiles=tiles,routes=d['routes'],connections=d['connections'],features=features,gates=gates,modules=modules)
    html=(ROOT/'tools/castle_release_viewer.html').read_text(encoding='utf-8')
    (OUT/TITLE).write_text(html.replace('__DATA__',json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__':main()

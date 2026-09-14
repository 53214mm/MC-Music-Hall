"""Deterministic, exhaustive construction pages; no automatic game actions."""
from collections import Counter

PHASES=[
 dict(name='01 基础与地下骨架',goal='先定位，再从低处搭岩体表层、地下支撑与楼板。',
      steps=['共用一个设计原点O，在现场标出全堡四角和16格网格线。','每阶段先完成A批全部支撑，再做B批元件；每批由低到高，同层依次分区。只放“本步”，空气和参考格不填。','空腔、桥洞和音乐舱不是实心山；临时脚手架自行搭设并记录，正式图中不含临时块。'],check='核对地下开口与留空；确认基础、楼板和台阶连续，再进入主体阶段。'),
 dict(name='02 主体、楼板与通路',goal='把地面主体、通行支撑和挂件支座搭出来，先不要启动电路。',
      steps=['从低到高搭原木/石墙/实体梁、楼板和通行楼梯，保留门窗洞与三格路线净空。','楼梯先核对上下半格和升高方向；装饰悬挑用临时脚手架辅助，完成后移除。','图中墙类栏杆/玻璃/灯会在第05阶段安装；高处施工期间另加临时防跌落设施。'],check='53条路线的支撑与楼梯按图定位；不得把未来家具/灯具的空位封死。'),
 dict(name='03 音乐模块与连接',goal='保持原材料、音高和线路，完成11段模块与10条接线。',
      steps=['先从低到高完成A批全部音乐支撑，再从低到高完成B批音符盒与线路；跨层悬置部分先架临时脚手架。','音符盒先核对下方底材，再右击设定音高；上方必须留空。中继器按卡片输出箭头和档位摆。','在“音乐与机关”中按01→11逐段核对输入和10条连接；全部供电保持默认关闭。','先逐段试听再整曲播放；已建低层和后来高层相互检查，不能跳过试听直接封顶。'],check='11段单独试听与完整连播，末条322红石刻不改为320；通过后再封高层屋顶。'),
 dict(name='04 高层、山墙与屋顶',goal='封上部主体和屋面，保留已设计的水晶采光。',
      steps=['完成前一阶段试听后，再从低到高搭上部石芯、山墙、屋面与悬挑支撑。','台阶分上半/下半，楼梯分普通/倒置；不要以整块替代，外挑构件先搭托臂与背板。','细柱/玻璃等后装件仍显示为参考；不要因此填实窗洞或音乐核心。'],check='屋面接坡连续；机房仍保留维修入口，原窗洞和通路未封堵。'),
 dict(name='05 窗栏、灯具与内装',goal='补齐薄件、照明、家具与闭合造景。',
      steps=['A批先安装墙状细柱、栅栏、玻璃片和家具主体；它们不是空气。完成本阶段全部A批后，再做B批挂件。','B批挂灯先检查上方铁链/实体支撑，落地灯检查脚下支座；支架必须在更早阶段或本阶段A批已完成。','花盆、桶、书架和讲台按中文卡片安装；默认没有书、物品、燃料或实体装饰。','墙/玻璃片/楼梯可能因邻居自动变形，整组装完再核对；不要在音符盒顶上加装饰。'],check='拆除临时块，补足全部护栏与灯；夜间检查暗角，灯数量不是防刷怪证明。'),
 dict(name='06 三处机关专用初装',goal='这是最后的特殊安装阶段，不能逐格照最终闭合态硬摆。',
      steps=['先阅读“音乐与机关”的S1/S2/S3专用初装顺序，完成各自全部支撑。','S1铁门下半安装时自动生成上半；S2先有梯子和梯背，再装铁活板门、电路和拉杆。','S3先让活塞收回，在Y4放闩石，再按指定顺序接火把；默认图中的Y3闩石/活塞头是最终关闭态。','每个机关缓慢ON/OFF测试并保存重进；最终关闭。不得快速连点或向音乐区补红石。'],check='专用初装与复位通过，再按验收清单双向实走/试听；本阶段网格只作最终态核对。')]

THIN=('lantern','soul_lantern','sea_lantern','ochre_froglight','iron_bars','flower_pot','barrel','furnace','lectern','bookshelf','grindstone')

def phase_for(p,s,gates):
    n,pr,g=s
    if g=='control' or g.isdigit():return 2
    if p in gates:return 5
    if g=='terrain':return 0
    if n in THIN or n.startswith('potted_') or n.endswith(('_wall','_fence','_pane','_trapdoor','_door')):return 4
    if p[1]>45 or p[1]>=20 and n.startswith('deepslate_tile'):return 3
    return 0 if p[1]<=0 else 1

def work_pass(s):
    n=s[0]
    return int(n in('note_block','redstone_wire','repeater','redstone_torch','redstone_wall_torch','lantern','soul_lantern','grindstone','flower_pot','ladder') or n.endswith('_button') or n.startswith('potted_'))

def make_pages(rows,phases,offset,passes=None):
    if len(rows)!=len(phases):raise ValueError('One phase per block required')
    passes=passes if passes is not None else [0]*len(rows)
    if len(passes)!=len(rows):raise ValueError('One pass per block required')
    counts=Counter((phase,sub,row[1]-offset[1],row[2]//16,row[0]//16) for row,phase,sub in zip(rows,phases,passes))
    return [dict(id=f'{ph}:{sub}:{y}:{tx}:{tz}',phase=ph,sub=sub,y=y,tx=tx,tz=tz,count=c) for (ph,sub,y,tz,tx),c in sorted(counts.items())]

def manual_plan(data,blocks):
    cs=[*data['shortcutsV14']['shortcuts'],data['serviceV15']['shortcut']];gates=set()
    for c in cs:
        for key in('lever','leverMount','repeater','outputBlock','gate','piston','head','stone','torch'):
            if c.get(key):gates.add(tuple(c[key]))
        gates.update(map(tuple,c.get('wire',[])));gates.update(map(tuple,c.get('gateParts',[])))
    phases=[phase_for(tuple(row[i]-data['offset'][i] for i in range(3)),data['palette'][row[3]],gates) for row in data['blocks']]
    passes=[work_pass(data['palette'][row[3]]) for row in data['blocks']]
    return dict(phases=PHASES,blockPhases=phases,blockPasses=passes,pages=make_pages(data['blocks'],phases,data['offset'],passes),gatePositions=sorted(gates),edge=16)

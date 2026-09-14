import json
from collections import Counter
from PIL import Image,ImageDraw,ImageFont
from castle_craft_samples import ROOT,samples,old_window
from vanilla_mesh import VanillaAssets,render

OUT=ROOT/'castle_v3/craft_v7'
FONT='C:/Windows/Fonts/msyh.ttc'
NAMES={'bricks':'红砖块','tuff_bricks':'凝灰岩砖','cut_sandstone':'切制砂岩','smooth_sandstone':'平滑砂岩','chiseled_sandstone':'雕纹砂岩','sandstone_wall':'砂岩墙','gray_stained_glass_pane':'灰色染色玻璃板','spruce_fence':'云杉栅栏','smooth_sandstone_stairs':'平滑砂岩楼梯','smooth_sandstone_slab':'平滑砂岩台阶','dark_oak_trapdoor':'深色橡木活板门','spruce_trapdoor':'云杉活板门','deepslate_tile_stairs':'深板岩瓦楼梯','deepslate_tiles':'深板岩瓦','deepslate_tile_slab':'深板岩瓦台阶','grindstone':'砂轮','lantern':'灯笼','waxed_weathered_cut_copper_stairs':'涂蜡的斑驳切制铜楼梯','waxed_weathered_cut_copper_slab':'涂蜡的斑驳切制铜台阶','stripped_spruce_log':'去皮云杉原木','spruce_planks':'云杉木板','spruce_stairs':'云杉楼梯','spruce_slab':'云杉台阶','calcite':'方解石'}


def main():
    OUT.mkdir(exist_ok=True);assets=VanillaAssets();ss=samples();payload=[]
    old=old_window();compare=Image.new('RGB',(1800,1380),'#eee8db');d=ImageDraw.Draw(compare)
    title=ImageFont.truetype(FONT,27);text=ImageFont.truetype(FONT,18)
    d.text((28,18),'V7｜同一原版模型与纹理下，比较窗跨本身',font=title,fill='#393d36')
    d.text((28,62),'左：V6窗跨剖去前方唱诗堂遮挡；右：独立试样。两侧同尺度同取景，不是整堡或游戏截图。',font=text,fill='#6a7065')
    for x,label,blocks in[(20,'V6窗跨：灰石同色，厚边框',old),(920,'V7试样：暖石、砖红、铜绿与细窗棂',ss[0].blocks)]:
        d.text((x+10,105),label,font=title,fill='#393d36');compare.paste(render(assets,blocks,ss[0].region,850,1200,20),(x,158))
    compare.save(OUT/'01_窗跨同纹理对照.png');print('Window comparison ready.',flush=True)
    overview=Image.new('RGB',(2100,1380),'#eee8db');d=ImageDraw.Draw(overview)
    d.text((28,18),'V7｜三种构件，不复制同一套装饰到所有房间',font=title,fill='#393d36')
    d.text((28,62),'使用26.3-snapshot-9的原版模型与纹理绘制；各样板单独适配画面，不能据此比较相对大小。',font=text,fill='#6a7065')
    for i,s in enumerate(ss):
        for view,angle in [('front',0),('oblique',24)]:
            image=render(assets,s.blocks,s.region,920,1150,angle);image.save(OUT/f'{s.id}_{view}.png')
        d.text((20+700*i,118),s.title,font=title,fill='#393d36')
        overview.paste(render(assets,s.blocks,s.region,665,1120,24),(20+700*i,180))
        counts=Counter(n for n,p,g in s.blocks.values());states=sorted({(n,tuple(sorted(p.items()))) for n,p,g in s.blocks.values()})
        # Mesh resolution is fail-closed; all sample IDs/states must be supported.
        for n,p in states:assets.elements(n,p)
        item=dict(id=s.id,title=s.title,region=s.region,blocks=[[x,y,z,n,p] for (x,y,z),(n,p,g) in sorted(s.blocks.items())],materials=dict(counts),steps=s.steps,swatches={n:assets.swatch(n,p) for n,p in states},total=len(s.blocks))
        payload.append(item)
        (OUT/f'{s.id}_blocks.json').write_text(json.dumps(item,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
        print(s.title,len(s.blocks),'blocks ready.',flush=True)
    overview.save(OUT/'02_三组异形构件.png')
    data=dict(samples=payload,names=NAMES,status='独立构件试样，尚未合并全堡，也未游戏实测。')
    html=(ROOT/'tools/castle_craft_viewer.html').read_text(encoding='utf-8').replace('__DATA__',json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'))
    (OUT/'余响堡_V7构件与配色试样.html').write_text(html,encoding='utf-8')
    lines=['# V7样板材料与搭建说明','','仅对应3个独立试样，不是全堡采购清单。不含工具和脚手架。局部坐标以样板左后底角为0，Z增大朝正面。原堡、音乐机与灯光文件都未改。','']
    for s,item in zip(ss,payload):
        lines +=[f'## {s.title}','',f'共{s.blocks.__len__()}个非空气方块；包围范围X={s.region[0]}…{s.region[1]}，Y={s.region[2]}…{s.region[3]}，Z={s.region[4]}…{s.region[5]}。显示范围包含留白，不代表每格都要填满。','']
        lines +=[f'{i+1}. **{name}**：{step}' for i,(name,step) in enumerate(s.steps)]
        lines +=['','| 材料 | 数量 |','|---|---:|']+[f'| {NAMES.get(n,n)} | {c} |' for n,c in Counter(n for n,p,g in s.blocks.values()).most_common()]+['']
    lines +=['## 手建注意','','- 木活板门可手动开合；open=true表示竖起的薄片，closed/false表示水平，half决定铰链高度。此处不使用需要供电才能维持打开的铁活板门。','- 楼梯的facing、half和转角、墙/栅栏连接状态需要在游戏中复核；自动更新可能改变外观。页面给的是设计状态，不保证游戏放置顺序完全相同。','- 样板灯具已有连接构件，但没有完成存档导入、游戏碰撞、光照或结构更新验收。不能把这组试样直接覆盖到音乐机附近。','- 原版模型和纹理直接从本机合法安装读取；仅输出建筑示意PNG，不打包或分发材质资源。绘图不含环境遮蔽、游戏光照、UV锁定和生物群系染色，动画材质取首帧。','- 全堡仍以V6作存档底稿；V7只是待确认的构件方向，不是成品总方案。','', '研究依据见上级目录《V7异形方块与配色参考.md》。']
    (OUT/'样板材料与搭法.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (OUT/'validation.json').write_text(json.dumps(dict(target='26.3-snapshot-9',samples={s.id:len(s.blocks) for s in ss},existingCastleModified=False,musicModified=False,newNBT=False,inGameTest=False,browserTest=False,rendererLimitations=['UV lock omitted','no ambient occlusion/game light','first animation frame','no biome tint']),ensure_ascii=False,indent=2),encoding='utf-8')
    print('V7 sample page generated. Existing castle and music untouched.',flush=True)


if __name__=='__main__':main()

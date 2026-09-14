"""Actual vanilla-model views, declared section cuts and a coordinate schematic."""
from collections import defaultdict,deque
from PIL import Image,ImageDraw,ImageFont
from castle_detail import read_model
from castle_service import service_variant
from vanilla_mesh import VanillaAssets,render
from build_castle_service import OUT


def main():
    d,a=read_model(OUT/'castle_v15.json');c=d['serviceV15']['shortcut'];assets=VanillaAssets()
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',32);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',23)
    def canvas(size,title,sub):
        im=Image.new('RGB',size,'#eee8db');dr=ImageDraw.Draw(im);dr.text((36,24),title,font=font,fill='#364e3f');dr.text((36,78),sub,font=small,fill='#6e7864');return im,dr
    im,dr=canvas((2500,1800),'S3 上下层关系｜从庭院的边缘进入石台，再回到音乐门厅','上：已登记普通路线与新捷径的俯视；下：实际方块沿X方向剖开。不是游戏截图。')
    graph=defaultdict(set)
    for r in d['routes']:
        for p,q in zip(r['points'],r['points'][1:]):p=tuple(p);q=tuple(q);graph[p].add(q);graph[q].add(p)
    start=tuple(c['points'][0]);end=tuple(c['points'][-1]);parent={start:None};queue=deque([start])
    while queue:
        p=queue.popleft()
        if p==end:break
        for q in sorted(graph[p]):
            if q not in parent:parent[q]=p;queue.append(q)
    old=[end]
    while old[-1]!=start:old.append(parent[old[-1]])
    old.reverse();assert len(old)-1==77
    xy=lambda p:(120+(p[0]-50)*42,165+(p[2]-4)*8)
    for x in range(50,73,2):
        px=xy((x,0,4))[0];dr.line((px,155,px,630),fill='#d0d0bc');dr.text((px-12,122),str(x),font=small,fill='#7e826e')
    for z in range(4,61,8):
        py=xy((50,0,z))[1];dr.line((110,py,1050,py),fill='#d0d0bc');dr.text((62,py-13),str(z),font=small,fill='#7e826e')
    dr.line([xy(p) for p in old],fill='#9b7055',width=15,joint='curve')
    dr.line([xy(p) for p in c['points']],fill='#4f816d',width=13,joint='curve')
    for p,label in [(start,'庭院  Y16'),(end,'音乐门厅高桥  Y1')]:
        x,y=xy(p);dr.ellipse((x-10,y-10,x+10,y+10),fill='#385d4b');dr.text((x+28,y-12),label,font=small,fill='#3b604d')
    x,y=xy(c['stone']);dr.rectangle((x-12,y-7,x+12,y+7),fill='#c8994d');dr.text((x-190,y-14),'石闩 Z32',font=small,fill='#826236')
    x,y=xy(c['lever']);dr.ellipse((x-8,y-8,x+8,y+8),fill='#a34333');dr.text((x+28,y-14),'内侧拉杆 Z26',font=small,fill='#925241')
    for y,text in [(155,'棕色：旧长路 77 段，始终保留'),(215,'绿色：新维修道 53 段，开闩后双向'),(285,'高端 (55,16,58) → 北侧下行15格'),(335,'低端 (55,1,5) → 原音乐门厅高桥'),(410,'旧路第一次绕到拉杆内侧，再打开石闩'),(465,'首遇时看见关闭出口；折返后认出头顶庭院'),(535,'坐标轴为设计X/Z，纵横采用不同图示比例'),(585,'段数按已登记最短图计边，不代表耗时')]:
        dr.text((1210,y),text,font=small,fill='#5c6e56')
    dr.line((35,680,2465,680),fill='#b3bca5',width=2)
    dr.text((36,708),'纵剖：保留西侧墙和中线地板，移去东侧遮挡以展示楼梯和内道',font=font,fill='#3a5946')
    dr.text((36,765),'显示 X51…55 / Y0…23 / Z5…59；原东侧墙、屋顶与未截入的城堡仍在完整模型。',font=small,fill='#6e7864')
    section={p:s for p,s in a.items() if p[0]<=55}
    im.paste(render(assets,section,(51,55,0,23,5,59),2420,895,90),(40,835))
    im.save(OUT/'01_上下层路线与剖面.png');print('route section rendered',flush=True)

    im,dr=canvas((2500,1700),'升降石闩｜相同坐标、相同视角的关闭与开启预期','门框只截Z32断面，前后覆盖层省略。下方另看拉杆入口。实际模型渲染，非游戏内验收。')
    for x,on in [(25,False),(1275,True)]:
        dr.text((x+25,132),'OFF：火把亮 → 石块在Y3，挡站立' if not on else 'ON：火把灭 → 石块在Y4，净高2',font=font,fill='#405c48')
        im.paste(render(assets,service_variant(a,c,on),(53,59,1,7,32,32),1200,870,155),(x,195))
    dr.text((45,1085),'内侧控制位｜音乐门厅向南进维修道，站(55,1,26)支撑格抬头拨西向墙拉杆',font=font,fill='#405c48')
    control={p:s for p,s in a.items() if p[0]>=55 and p[1]<=4}
    im.paste(render(assets,control,(55,59,1,4,24,28),1100,480,270),(40,1170))
    for y,text in [(1210,'拉杆 (57,3,26) · 附着东邻满块 (58,3,26)'),(1270,'普通站立/蹲伏被闭合石闩挡住，但爬行可能通过'),(1330,'关闩南侧指定接近处，至整个拉杆格至少6.3格'),(1390,'以4.5格触及假设，仅证明这条指定入口不能伸手拨到'),(1450,'先ON搭活塞和Y4石块，再OFF，等待完整伸出'),(1510,'别手放活塞头；别站闩下关门；不要快速来回拨')]:
        dr.text((1210,y),text,font=small,fill='#69775f')
    im.save(OUT/'02_石闩开关与控制位.png');print('latch states rendered',flush=True)

    im,dr=canvas((2600,1600),'S3 反相电路｜七格线、一个中继器、一根墙火把','展开图不按空间比例；实际X/Y/Z以每格标签为准。信号强度是稳态推导，不是实测。')
    dr.text((45,140),'拉杆L (57,3,26) → 东邻附着座A (58,3,26) → W1',font=font,fill='#405c48')
    for i,p in enumerate(c['wire']):
        x=55+i*355;y=400-(p[1]-3)*55
        if i:
            oldp=c['wire'][i-1];px=55+(i-1)*355;py=400-(oldp[1]-3)*55
            dr.line((px+270,py+40,x,y+40),fill='#ac5941',width=9)
        dr.rounded_rectangle((x,y,x+270,y+82),10,fill='#a74e3b')
        dr.text((x+16,y+24),f'W{i+1}  /  ON: {15-i}',font=small,fill='#fff3d6')
        dr.rectangle((x,y+91,x+270,y+148),fill='#c6b28a')
        dr.text((x+20,y+104),f'满块支撑Y={p[1]-1}',font=small,fill='#4d5d44')
        dr.text((x,y+169),str(tuple(p)),font=small,fill='#566c4d')
    dr.text((55,685),'W1→W2、W2→W3各升1格；(59,4,26)、(59,5,27)两处低线头顶留空。',font=font,fill='#405c48')
    dr.text((55,747),'W7实际连接北侧W6与西侧中继器：north=side、west=side、east/south=none。',font=small,fill='#67795d')
    dr.line((35,820,2565,820),fill='#b7bda7',width=2)
    nodes=[('W7','(59,5,32)','线 / 9'),('R','(58,5,32)','中继器 / 1档'),('C','(57,5,32)','切制砂岩'),('T','(56,5,32)','西向墙火把'),('P','(55,5,32)','向下黏性活塞')]
    for i,(n,p,label) in enumerate(nodes):
        x=60+i*495
        dr.rounded_rectangle((x,918,x+405,1070),8,fill='#d2c5a5')
        dr.text((x+25,940),n+' · '+label,font=small,fill='#465d45');dr.text((x+25,1010),p,font=small,fill='#465d45')
        if i<4:dr.line((x+414,988,x+485,988),fill='#8e6f49',width=6);dr.polygon([(x+485,988),(x+470,978),(x+470,998)],fill='#8e6f49')
    dr.text((60,865),'输出段沿世界X递减向西（本示意从左到右展开）',font=font,fill='#405c48')
    for y,text in [(1140,'R facing=east：东侧输入，西侧输出。T facing=west：附着东邻C，不附着P。'),(1210,'L OFF → 线0 → R灭 → T亮 → P伸 → 头Y4 / 石Y3（默认关闭）'),(1280,'L ON  → 线15…9 → R亮 → T灭 → P缩 → 石Y4 / Y3空气（保持开启）'),(1370,'活塞直接供电与上方准连接邻域按逐层图保持；不要在附近临接探测铁轨、拉杆或其他电源。'),(1450,'严禁把支持导线的满块改半砖；每次开关等运动稳定，快脉冲吐块/火把烧毁不在本机关保证内。')]:
        dr.text((60,y),text,font=small,fill='#5c6f53')
    im.save(OUT/'03_反相接线坐标.png');print('wiring rendered',flush=True)

    im,dr=canvas((2600,1600),'入口与灯龛｜木构雨棚、浅石台阶、暖灯维修墙','每幅按标注区域裁切、比例不同；不要把截去的覆盖层当成实际拆除范围。非游戏截图。')
    dr.text((40,137),'庭院雨棚：X51…59 / Y14…24 / Z50…59',font=font,fill='#405c48')
    im.paste(render(assets,a,(51,59,14,24,50,59),1240,1270,25),(25,220))
    dr.text((1320,137),'侧龛灯：X53…56 / Y1…4 / Z16…20',font=font,fill='#405c48')
    im.paste(render(assets,a,(53,56,1,4,16,20),1220,530,90),(1310,225))
    dr.text((1320,820),'高桥接入口：X52…58 / Y1…4 / Z4…9',font=font,fill='#405c48')
    im.paste(render(assets,a,(52,58,1,4,4,9),1220,570,175),(1310,903))
    dr.text((45,1530),'灯具全在X53，Z10/18/26/36/44/51；开口X54…56有连续地板，X53/57端栏杆仍保留。',font=small,fill='#6b7860')
    im.save(OUT/'04_雨棚与暖灯细部.png');print('details rendered',flush=True)


if __name__=='__main__':main()

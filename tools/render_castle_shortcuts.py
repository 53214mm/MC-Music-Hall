"""Render actual default/open model states and a numbered wiring drawing."""
import json
from PIL import Image,ImageDraw,ImageFont
from castle_detail import ROOT,read_model
from castle_shortcuts import variant
from vanilla_mesh import VanillaAssets,render
from build_castle_shortcuts import OUT


def main():
    d,a=read_model(OUT/'castle_v14.json');assets=VanillaAssets();cs=d['shortcutsV14']['shortcuts']
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',30);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',21)
    def canvas(size,title,sub):
        im=Image.new('RGB',size,'#eee8db');dr=ImageDraw.Draw(im);dr.text((32,22),title,font=font,fill='#364d3d');dr.text((32,74),sub,font=small,fill='#67765f');return im,dr
    r=(-36,-28,0,5,52,61)
    im,dr=canvas((2500,1500),'S1 回廊便门｜北侧内廊视角，同坐标与相机比较','裁切 X=-36…-28 / Y=0…5 / Z=52…61。上方旧墙/屋顶仍在完整模型；原版模型图，非游戏截图。')
    for x,on in [(25,False),(1275,True)]:
        dr.text((x+20,128),'拉杆关 · 铁门阻挡' if not on else '拉杆开 · 左铰链门片靠西',font=font,fill='#465a42')
        im.paste(render(assets,variant(a,cs[0],on),r,1200,1230,172),(x,193))
    im.save(OUT/'01_回廊门开关.png');print('S1 rendered',flush=True)
    im,dr=canvas((2600,1750),'S2 藏谱梯口｜固定梯子，上廊先开锁，再从下厅折返','左图只裁取 X=-48…-45 / Y=16…35 / Z=1…3；右图是上廊局部，同相机对照。非游戏截图。')
    dr.text((35,132),'整列梯子 · 开启状态',font=font,fill='#465a42')
    im.paste(render(assets,variant(a,cs[1],True),(-48,-45,16,35,1,3),760,1420,70),(28,208))
    for x,on in [(830,False),(1715,True)]:
        dr.text((x+15,132),'上廊 · 关闭' if not on else '上廊 · 开启',font=font,fill='#465a42')
        im.paste(render(assets,variant(a,cs[1],on),(-48,-42,31,35,-5,3),850,1280,70),(x,230))
    dr.text((840,1545),'上廊裁切 X=-48…-42 / Y=31…35 / Z=-5…3。',font=small,fill='#637259')
    dr.text((840,1590),'原下层/上层地板和背墙保留；图中裁切边缘不代表施工洞口。',font=small,fill='#637259')
    dr.text((840,1635),'新拉杆在北端 Z=-4，梯口在南端 Z=2；线藏在原墙内侧一层。',font=small,fill='#637259')
    im.save(OUT/'02_梯口开关.png');print('S2 rendered',flush=True)
    im,dr=canvas((2600,1700),'机关铺线｜按编号落位，每根红石粉下面都有实心支撑','这是明确标注坐标的施工线路图；色彩表达设计信号，不是Minecraft实时亮度或游戏截图。')
    # S1 unfolded sequence: y-aware carrier drawing, explicitly not a horizontal plan.
    dr.text((35,144),'S1 · 展开线路（转弯已展开，实际X/Z以标签为准）',font=font,fill='#465a42')
    for i,p in enumerate(cs[0]['wire']):
        x=55+i*265;y=275+(5-p[1])*68
        if i:
            prev=cs[0]['wire'][i-1];px=55+(i-1)*265;py=275+(5-prev[1])*68
            dr.line((px+205,py+32,x,y+32),fill='#b14d39',width=8)
        dr.rounded_rectangle((x,y,x+205,y+68),10,fill='#b55741')
        dr.text((x+14,y+13),f'{i+1}  /  强度 {15-i}',font=small,fill='#fff6df')
        dr.rectangle((x,y+75,x+205,y+125),fill='#c8b28b')
        dr.text((x+8,y+85),f'支撑 Y={p[1]-1}',font=small,fill='#4b5943')
        dr.text((x,y+141),str(tuple(p)),font=small,fill='#4b5943')
    dr.text((55,235),'拉杆(-34,4,53) → 附着柱(-35,4,53) → 上方首线',font=small,fill='#536349')
    dr.text((55,792),'末线9 → 中继器(-32,1,59)，facing=north，1档 → 输出柱(-32,1,60) → 门(-31,1…2,60)',font=font,fill='#465a42')
    dr.text((55,850),'导线5→6向南降1格，6→7→8→9每次向东降1格；低线正上方不可堵塞。',font=small,fill='#617058')
    dr.line((35,920,2565,920),fill='#b7b7a3',width=2)
    dr.text((35,962),'S2 · 俯视顺序：全部线 X=-47、Y=34，Z由北向南递增',font=font,fill='#465a42')
    for i,p in enumerate(cs[1]['wire']):
        x=75+i*335;y=1080
        if i:dr.line((x-75,y+40,x,y+40),fill='#b14d39',width=8)
        dr.rounded_rectangle((x,y,x+260,y+78),10,fill='#b55741')
        dr.text((x+22,y+20),f'{i+1}  /  Z={p[2]}  /  {15-i}',font=small,fill='#fff6df')
        dr.text((x+18,y+105),'下方Y33原块保留',font=small,fill='#596c4e')
    dr.text((75,1300),'北端：拉杆(-45,34,-4) → 新座(-46,34,-4) → 首线(-47,34,-4)',font=font,fill='#465a42')
    dr.text((75,1370),'南端：末线7 → 原木板(-47,33,2) → 东邻铁活板门(-46,33,2)',font=font,fill='#465a42')
    dr.text((75,1440),'原X=-48背墙和Y=35墙不动。铁活板门朝东、下半；正下Y32普通梯子同样朝东。',font=small,fill='#617058')
    dr.text((75,1515),'S1/S2终端预期强度分别7/9；S1中继器恢复为15。拉杆关闭后全线0，两门关闭。',font=small,fill='#617058')
    dr.text((75,1575),'逐格状态见页面下方施工图；请先在独立创造档验证开关、攀爬、邻居更新及存档重进。',font=small,fill='#617058')
    im.save(OUT/'03_机关铺线坐标.png');print('Wiring drawing rendered',flush=True)
    im,dr=canvas((2500,1450),'捷径补灯｜保留原灯，补足门外与梯井中段','两图为裁切近景，不是同一比例；灯具所在坐标以标注和逐层施工图为准。非游戏截图。')
    for x,r,angle,title in [(25,(-33,-28,0,5,59,68),8,'S1 门外柱灯：(-30,2,65)'),
                            (1275,(-48,-44,23,28,1,4),70,'S2 梯井壁座灯：(-46,26,3)')]:
        dr.text((x+15,130),title,font=font,fill='#465a42')
        dr.text((x+15,181),f'X={r[0]}…{r[1]} / Y={r[2]}…{r[3]} / Z={r[4]}…{r[5]}',font=small,fill='#637259')
        im.paste(render(assets,a,r,1200,1120,angle),(x,244))
    im.save(OUT/'04_捷径补灯.png');print('Shortcut light details rendered',flush=True)


if __name__=='__main__':main()

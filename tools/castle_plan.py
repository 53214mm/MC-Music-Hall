"""V3 architectural study. Coordinates are design-space, not final NBT placement.

Rooms/routes are an explicit spatial brief; they must be voxelized and clearance
tested before this study can be called a Minecraft construction blueprint.
"""
import math


def rectangle(x0,z0,x1,z1):return [[x0,z0],[x1,z0],[x1,z1],[x0,z1]]
def octagon(cx,cz,r):
    return [[round(cx+math.cos(math.pi/8+i*math.pi/4)*r,1),round(cz+math.sin(math.pi/8+i*math.pi/4)*r,1)] for i in range(8)]


def plan():
    masses=[]
    def mass(id,name,poly,base,top,kind='stone',roof=0):
        masses.append(dict(id=id,name=name,polygon=poly,base=base,top=top,kind=kind,roof=roof))
    # Broken, terraced silhouette; the large negative spaces are intentional.
    island=[[-85,70],[-82,0],[-64,-66],[-20,-90],[53,-80],[89,-32],[103,34],[77,105],[22,122],[-43,114]]
    mass('cliff','岩岬与旧堡地基',island,-48,-4,'terrain')
    mass('core','封存的音乐内堡',[[-11,-34],[-5,-40],[49,-40],[55,-34],[55,35],[49,41],[-5,41],[-11,35]],-34,46)
    mass('crown','偏心冠楼',octagon(-4,-20,22),12,108)
    mass('crown_overhang','外挑石冠',octagon(-4,-20,25),108,118,'crown')
    mass('crystal','核心采光裂隙',octagon(21,10,11),46,48,'crystal',7)
    mass('north_stair','北阶塔',octagon(-20,-42,10),-4,65,'stone',9)
    mass('beacon','孤立守望塔',octagon(-45,-34,11),6,77,'stone',17)
    mass('east_service','东侧检修阶塔',octagon(65,7,11),-4,64,'stone',10)
    mass('east_crown','东阶塔外挑冠',octagon(65,7,13),59,64,'crown')
    mass('broken','西侧残塔',octagon(-69,24,10),-4,36,'ruin')
    mass('gate_w','低门塔：露台石冠',octagon(-56,100,10),-28,28)
    mass('gate_e','高门塔：三段内梯',octagon(-28,104,11),-28,45,'stone',15)
    mass('gate','折入式门道',rectangle(-49,93,-37,113),-12,8)
    mass('front_cliff','南侧裂隙岩岬：详见联建图',[[-84,81],[-6,80],[3,106],[-9,144],[-16,181],[-63,181],[-81,140],[-90,102]],-48,-12,'terrain')
    mass('bridge','跨裂隙拱桥：详见联建图',rectangle(-46,116,-40,151),-32,-12,'stone')
    mass('barracks','改为收容所的旧营房',[[-67,67],[-47,72],[-42,41],[-64,36]],0,19,'stone',9)
    mass('kitchen','厨房与补给院',rectangle(-63,9,-43,35),0,17,'stone',8)
    mass('archive','两层藏谱室',rectangle(-47,-14,-15,14),16,40,'stone',13)
    mass('choir','纪念礼拜堂',[[-9,48],[18,48],[29,59],[29,79],[14,90],[-9,81]],16,39,'stone',17)
    mass('cloister_w','回廊西廊',rectangle(-42,27,-38,59),0,7)
    mass('cloister_n','回廊北廊',rectangle(-42,25,-16,29),0,7)
    mass('cloister_e','回廊东廊',rectangle(-20,27,-16,59),0,7)
    mass('cloister_s','回廊南廊',rectangle(-42,55,-16,59),0,7)
    mass('terrace','上层悬廊',rectangle(-47,16,-13,21),15,16,'walk')
    mass('choir_bridge','通往礼拜堂的窄桥',rectangle(-15,49,-8,55),15,16,'walk')
    mass('east_gallery','东翼开敞连廊',rectangle(60,31,76,70),8,19,'stone')
    mass('cistern','排空的旧蓄水池',rectangle(-35,57,-13,77),-12,-11,'water')
    # Curtain wall segments do not share a single horizontal roofline.
    walls=[([-69,82],[-74,23],-4,15),([-74,23],[-54,-52],-4,23),([-54,-52],[-12,-68],-4,31),
           ([-12,-68],[62,-58],-4,29),([62,-58],[84,0],-4,26),([84,0],[82,60],-4,23),
           ([82,60],[51,98],-4,18),([51,98],[-8,111],-4,14),([-8,111],[-27,106],-12,10),
           ([-60,97],[-69,82],-12,10)]
    for i,(a,b,base,top) in enumerate(walls):
        dx=b[0]-a[0];dz=b[1]-a[1];length=math.hypot(dx,dz);nx=-dz/length*2;nz=dx/length*2
        poly=[[a[0]+nx,a[1]+nz],[b[0]+nx,b[1]+nz],[b[0]-nx,b[1]-nz],[a[0]-nx,a[1]-nz]]
        mass(f'wall{i}','外城墙',poly,base,top,'wall')
    # Coordinates of floor surfaces, not eye height. Planned grade changes are
    # deliberately explicit rather than implied by overlapping room rectangles.
    rooms=[
      ('approach','01 断碑坡道',[-18,-28,178],'抵达','沿折转坡道进入五格宽拱桥。此段已按联建图展开；灰模岩岬未显示全部挖空。','倒下的旧路碑与后来补铺的石阶指向不同年代。'),
      ('gatehouse','02 守门人小室',[-43,-12,102],'抵达','狭窄折入门道；先见主门后的庭院，再从侧梯上行。','旧值勤桌仍整齐，旁边却堆着撤离用的空箱。'),
      ('bailey','03 余烬前庭',[-38,0,74],'枢纽','第一个露天宽空间，可认出上层悬廊和远处冠楼；与已建西翼样板的接口。','磨损车辙绕过一块被保护起来的纪念石。'),
      ('shelter','04 旧营房收容所',[-54,0,55],'叙事','低矮暖色房间，提供前庭与厨房之间的生活路线。','原整齐军床被换成不等长床铺；长桌拼成临时病床。'),
      ('kitchen','05 停火后的厨房',[-53,0,24],'叙事','从营房穿入备餐间；一条服务梯登上藏谱室。','熄灭的炉台、数量不齐的碗、只擦净的一段台面。'),
      ('cloister','06 空井回廊',[-29,0,42],'枢纽','环形可走的庭院，能仰望上层桥和藏谱窗。','井口封盖，但一条新绳仍垂向下层；水痕解释旧地坪。'),
      ('stair','07 旧服务阶梯',[-48,16,5],'爬升','绕墙连续登高16格，有中间休息台，不要求跳跃。','墙上旧封门被撬开，留下粗木补强，而非任意破洞。'),
      ('archive','08 藏谱室下厅',[-31,16,0],'叙事','双层通高大厅；一进门看见上层缺口，但当前不能直达。','普通书架杂乱，只有曲谱柜和维修记录保存完好。'),
      ('gallery','09 回望悬廊',[-28,16,19],'回望','从上层回看先前的空井，终于解释先前看到的桥。','磨亮的扶手说明仍有人反复走这条路。'),
      ('choir','10 空席礼拜堂',[8,16,66],'叙事','进入偏心高厅：主座并非居中，通往声音的路在侧面。','一排空席与一张仍放着乐谱的椅子；窗下新石与旧墙相接。'),
      ('eastcourt','11 日光庭院',[45,16,57],'枢纽','从暗礼拜堂进入亮院，北望只有局部水晶发光的内堡。','风化雕像只保留基座，基座旁重新种植的小树仍被照料。'),
      ('service','12 东侧阶塔',[65,16,7],'转折','沿独立侧梯下降进入机房；另一支阶梯通向城墙与检修层。','备用木板、工具架、近期修补的不同色石块说明音乐仍被维护。'),
      ('listening','13 最后的合唱',[21,-3,4],'终点','整机整体下沉32格后，抵达同一听音平台；这里才完整揭示音乐机器。','从地上城堡进入岩体中的保存室，冷光从高处的局部水晶透入。'),
      ('archive_upper','14 藏谱室上廊',[-31,32,0],'探索','从阶塔另一支到上廊，向下看见刚才走过的书桌。','能看清下厅看不到的背面标签：曲谱曾被重新排序。'),
      ('roof','15 屋面巡路',[-26,48,-18],'探索','屋面不是连续跑酷；窄檐有护栏并接真正的楼梯。','短段临时木桥跨过旧塌口，提示维修者的行进方向。'),
      ('beacon','16 独塔观景台',[-45,72,-34],'奖励','登上非最高的孤塔回望全堡，音乐冠楼仍高于自己。','只留一张面朝来路的椅子和灯，物件少而位置明确。'),
      ('cistern','17 干涸蓄水池',[-24,-12,66],'探索','从空井的服务口下降，再沿水道返回前庭。','水线、堵塞进水口与后来加的梯子解释空间为何失去原用途。'),
      ('memorial','18 无名纪念龛',[-7,-12,75],'死路','短支路尽头不再硬接新房间，提供安静停顿和回望。','空基座与未点燃的灯，呼应终点缺席的指挥者。'),
      ('workshop','19 封闭的旧工坊',[-65,0,4],'死路','厨房后的安静小室；得到线索后原路退回。','坏掉的装饰音管与备用零件，把生活区和音乐核心联系起来。'),
      ('s1','S1 回廊便门',[-38,0,65],'捷径','首次由内侧移开门闩，前庭到回廊不必再绕营房。','门闩机制待方块样板验证，默认关闭；不连接音乐红石。'),
      ('s2','S2 藏谱折返梯',[-39,16,2],'捷径','从上廊放下梯子，返回已到过的下厅，而非开向新地图。','单向发现、双向复用；普通游览保留不使用此捷径的替代路。'),
      ('s3','S3 维修者通道',[58,16,37],'捷径','从内侧打开通往日光庭院的门，缩短再次进入听音区的路。','与音乐电路分区，必要时先以普通门进行空间测试。'),
    ]
    nodes=[dict(id=id,name=name,position=p,role=role,experience=experience,story=story) for id,name,p,role,experience,story in rooms]
    edges=[]
    def edge(a,b,kind='main',via=None,description=''):
        pa=next(n['position'] for n in nodes if n['id']==a);pb=next(n['position'] for n in nodes if n['id']==b)
        pts=[pa]+(via or [])+[pb]
        length=sum(math.dist(u,v) for u,v in zip(pts,pts[1:]))
        edges.append(dict(a=a,b=b,kind=kind,points=pts,length=round(length,1),description=description))
    edge('approach','gatehouse',via=[[-43,-28,178],[-43,-28,174],[-43,-12,158]])
    edge('gatehouse','bailey',via=[[-43,-12,97],[-49,-12,97],[-49,-12,92],[-49,0,80],[-49,0,76],[-38,0,76]])
    edge('bailey','shelter');edge('shelter','kitchen');edge('kitchen','cloister')
    edge('cloister','stair',via=[[-45,0,28],[-48,16,28]])
    edge('stair','archive');edge('archive','gallery')
    edge('gallery','choir',via=[[-15,16,19],[-15,16,52],[8,16,52]])
    edge('choir','eastcourt',via=[[24,16,72],[45,16,72]])
    edge('eastcourt','service',via=[[80,16,57],[80,16,10]],description='首次经东翼巡廊到阶塔')
    edge('service','listening',via=[[65,-3,7],[47,-3,4]],description='回转楼梯下降19格；尚待逐格展开')
    edge('archive','archive_upper','explore',via=[[-18,16,-4],[-18,32,-4]],description='回转楼梯，不是直上竖井')
    edge('archive_upper','roof','explore',via=[[-16,32,0],[-16,48,-18]])
    edge('roof','beacon','explore',via=[[-45,48,-18],[-45,72,-34]],description='独塔内转折楼梯')
    edge('cloister','cistern','explore',via=[[-24,0,50],[-24,-12,50]])
    edge('cistern','bailey','explore',via=[[-38,-12,66],[-38,0,76]],description='地下回路返回前庭')
    edge('cistern','memorial','deadend');edge('kitchen','workshop','deadend')
    edge('cloister','s1','shortcut');edge('s1','bailey','shortcut')
    edge('archive_upper','s2','shortcut',description='从上层开启');edge('s2','archive','shortcut')
    edge('service','s3','shortcut',via=[[58,16,7]])
    edge('s3','eastcourt','shortcut')
    return dict(version='3.0-space-study',title='余响堡 · 最后的合唱',status='空间与体量方案，非最终逐格NBT施工图',
                coordinates='城堡设计坐标；Y为平台地面。音乐机整体平移(0,-32,0)，地形底部约-48，未换算世界原点。',
                musicTranslation=[0,-32,0],
                protectedMusic={'min':[-7,-34,-36],'max':[49,45,37]},
                masses=masses,nodes=nodes,edges=edges,
                mainRoute=['approach','gatehouse','bailey','shelter','kitchen','cloister','stair','archive','gallery','choir','eastcourt','service','listening'])

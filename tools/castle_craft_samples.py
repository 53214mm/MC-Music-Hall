"""Independent V7 construction samples: do not edit or claim integration with V6."""
import math
from castle_detail import ROOT,read_model


class Sample:
    def __init__(self,id,title,region):self.id=id;self.title=title;self.region=region;self.blocks={};self.steps=[]
    def put(self,x,y,z,name,**props):self.blocks[x,y,z]=(name,{k:str(v).lower() for k,v in props.items()},'sample')
    def box(self,x0,y0,z0,x1,y1,z1,name,**props):
        for x in range(x0,x1+1):
            for y in range(y0,y1+1):
                for z in range(z0,z1+1):self.put(x,y,z,name,**props)
    def remove(self,x,y,z):self.blocks.pop((x,y,z),None)
    def stair(self,x,y,z,n,facing,half='bottom',shape='straight'):self.put(x,y,z,n,facing=facing,half=half,shape=shape,waterlogged=False)
    def slab(self,x,y,z,n,kind='bottom'):self.put(x,y,z,n,type=kind,waterlogged=False)
    def wall(self,x,y,z,n='sandstone_wall'):self.put(x,y,z,n,up=True,north='none',south='none',east='none',west='none',waterlogged=False)
    def fence(self,x,y,z,n='spruce_fence'):self.put(x,y,z,n,north=False,south=False,east=False,west=False,waterlogged=False)
    def trap(self,x,y,z,n='spruce_trapdoor',facing='south',opened=True,half='bottom'):self.put(x,y,z,n,facing=facing,half=half,open=opened,powered=False,waterlogged=False)
    def lantern(self,x,y,z,hanging=True):self.put(x,y,z,'lantern',hanging=hanging,waterlogged=False)
    def connect(self):
        # Explicit straight arms for same-family elements and adjacent full opaque blocks.
        full={'bricks','granite','polished_granite','smooth_sandstone','cut_sandstone','chiseled_sandstone','sandstone','tuff_bricks','polished_tuff','calcite','stripped_spruce_log','spruce_planks','deepslate_tiles','deepslate_bricks','waxed_weathered_cut_copper'}
        for (x,y,z),(n,props,g) in list(self.blocks.items()):
            if not n.endswith(('_wall','_fence','_glass_pane')):continue
            props=dict(props)
            for side,dx,dz in(('north',0,-1),('south',0,1),('east',1,0),('west',-1,0)):
                nn=self.blocks.get((x+dx,y,z+dz),('',{},''))[0]
                connect=nn==n or nn in full
                props[side]=('low' if connect else 'none') if n.endswith('_wall') else str(connect).lower()
            self.blocks[x,y,z]=(n,props,g)


def samples():
    a=Sample('window','A · 暖石尖拱窗跨',(0,18,0,33,0,11))
    a.box(0,0,0,18,2,7,'tuff_bricks')
    a.box(1,3,2,17,27,3,'bricks')
    # Red masonry fields bounded by projecting pale pilasters.
    for x in(1,17):
        a.box(x,3,4,x,24,4,'cut_sandstone')
        for y in range(5,24):a.wall(x,y,5)
        a.stair(x,3,5,'smooth_sandstone_stairs','north',half='top')
        a.slab(x,4,5,'smooth_sandstone_slab')
        a.put(x,24,5,'chiseled_sandstone');a.stair(x,25,5,'smooth_sandstone_stairs','north',half='top')
    # Opening is genuinely cut; glass is behind the fine sandstone/wood tracery.
    for x in range(5,14):
        top=19+int((4-abs(x-9))*1.45)
        for y in range(7,top+1):
            a.remove(x,y,2);a.remove(x,y,3)
            a.put(x,y,2,'gray_stained_glass_pane',east=True,west=True,north=False,south=False,waterlogged=False)
    for x in(4,14):
        a.box(x,6,4,x,19,4,'smooth_sandstone')
        for y in range(7,20):a.wall(x,y,5)
    for x in range(4,15):
        y=20+int((5-abs(x-9))*1.2)
        a.stair(x,y,4,'smooth_sandstone_stairs','east' if x<9 else 'west',half='top')
        a.slab(x,y+1,4,'smooth_sandstone_slab')
    # Two lancets, narrow posts, small inner arches; no one-block-wide solid mullions.
    for x in(6,9,12):
        for y in range(7,19):a.fence(x,y,3)
    for cx in(7,11):
        a.stair(cx-1,19,3,'smooth_sandstone_stairs','east',half='top')
        a.stair(cx+1,19,3,'smooth_sandstone_stairs','west',half='top')
        a.slab(cx,20,3,'smooth_sandstone_slab',kind='top')
    for x in range(7,12):a.fence(x,22,3)
    for y in(21,23,24):a.fence(9,y,3)
    for x in range(3,16):a.slab(x,6,5,'smooth_sandstone_slab',kind='top')
    for x in(3,15):
        for y in range(9,15):a.trap(x,y,5,'dark_oak_trapdoor')
    # Thin dentils and corbels have air between them, not a solid continuous ledge.
    for x in range(0,19):
        a.slab(x,28,5,'smooth_sandstone_slab',kind='top')
        a.stair(x,29,4,'deepslate_tile_stairs','north')
        if x%3==0:a.stair(x,27,5,'smooth_sandstone_stairs','north',half='top')
    for x in(3,15):
        a.put(x,6,5,'chiseled_sandstone')
        a.put(x,5,5,'grindstone',face='ceiling',facing='south')
        a.put(x,27,5,'smooth_sandstone')
        a.put(x,26,5,'spruce_fence',north=True,south=False,east=False,west=False,waterlogged=False)
        a.lantern(x,25,5)
    # Small copper window cap, not a wholesale teal castle roof.
    for x in range(6,13):
        roof_y=29+(3-abs(x-9))
        for y in range(28,roof_y):a.put(x,y,3,'bricks')
        for z in range(2,5):a.stair(x,roof_y,z,'waxed_weathered_cut_copper_stairs','east' if x<9 else 'west')
    a.slab(9,33,3,'waxed_weathered_cut_copper_slab')
    a.steps=[('厚墙与基座','先搭X=0…18、Y=0…2的凝灰岩砖基座；红砖墙在Z=2…3。窗口玻璃放在后侧Z=2，前面保留空隙。'),('窗洞、窗套与细窗棂','窗口X=5…13从Y=7起向上收尖。外圈暖砂岩；内侧云杉栅栏形成细窗棂，倒置楼梯做小窗头。栅栏、墙的连接由邻块决定，按逐层图搭。'),('窗扇、窗台、托石','外侧深橡木活板门手动打开为竖片；Y=6用上半台阶做薄窗台，Y=5的磨石是托件。不要把活板门位置填成整块。'),('檐口与灯','Y=27的倒楼梯之间留空，上方用上半台阶压边；灯笼挂在栅栏下方。小范围铜绿只用于上部窗帽。')]
    a.connect()

    b=Sample('dormer','B · 变坡老虎窗与薄檐',(0,12,0,20,0,10))
    b.box(1,0,1,11,1,8,'tuff_bricks');b.box(2,2,2,10,9,6,'bricks')
    for x in(2,10):b.box(x,2,7,x,9,7,'cut_sandstone')
    for x in range(4,9):
        for y in range(4,9):
            for z in range(2,7):b.remove(x,y,z)
            b.put(x,y,6,'gray_stained_glass_pane',east=True,west=True,north=False,south=False,waterlogged=False)
            if x==6:b.fence(x,y,7)
    for x in range(3,10):b.slab(x,3,7,'smooth_sandstone_slab',kind='top')
    for x in(3,9):
        for y in range(5,8):b.trap(x,y,8,'spruce_trapdoor')
    # Increasing rise toward the ridge changes the silhouette, including half-block lips.
    heights={0:9,1:10,2:11,3:13,4:15,5:17,6:18}
    for x in range(13):
        k=min(x,12-x);roof_y=heights[k]
        for z in range(0,10):
            if 2<=x<=10:
                for yy in range(10,roof_y):b.put(x,yy,6,'bricks')
            b.stair(x,roof_y,z,'deepslate_tile_stairs','east' if x<6 else 'west')
            if z in(0,9):b.stair(x,roof_y-1,z,'smooth_sandstone_stairs','east' if x<6 else 'west',half='top')
        b.slab(x,roof_y,10,'smooth_sandstone_slab')
    for z in range(0,11):b.slab(6,19,z,'deepslate_tile_slab')
    for x in(1,11):
        b.stair(x,8,7,'smooth_sandstone_stairs','north',half='top')
        b.slab(x,9,8,'smooth_sandstone_slab',kind='top')
    for x in(4,8):b.stair(x,10,7,'smooth_sandstone_stairs','east' if x==4 else 'west',half='top')
    b.put(6,11,7,'chiseled_sandstone');b.fence(6,18,10);b.lantern(6,17,10)
    b.steps=[('窗芯','先搭红砖窗芯，窗玻璃在Z=6，细窗棂和浅色窗框在Z=7。'),('变坡屋面','从两侧向中心，每格屋面高度依次为9、10、11、13、15、17、18；镜像搭另一侧。跨两格高度的位置需要完整砖块封住下方，不能只留悬空楼梯。'),('薄屋檐','前后山墙用倒置砂岩楼梯托住深灰瓦，最外侧Z=10用半台阶收薄；不要把倒楼梯之间的缺角填实。'),('屋脊灯','屋脊上加半台阶，前端栅栏向下吊一盏灯。铜绿留给A窗帽，B不再重复同色装饰。')]
    # Close steep roof risers within the weather skin, not below an entire solid attic.
    for x in range(12):
        y0,y1=heights[min(x,12-x)],heights[min(x+1,11-x)]
        if abs(y1-y0)>1:
            xx=x+1 if y1>y0 else x
            for z in range(1,9):
                for y in range(min(y0,y1)+1,max(y0,y1)):b.put(xx,y,z,'deepslate_tiles')
    b.connect()

    c=Sample('timber','C · 外挑木窗与三格托架',(0,12,0,18,0,10))
    c.box(0,0,0,12,1,7,'tuff_bricks');c.box(1,2,2,11,14,3,'calcite')
    for x in(1,6,11):c.box(x,2,4,x,15,4,'stripped_spruce_log',axis='y')
    for y in(7,14):c.box(1,y,4,11,y,4,'stripped_spruce_log',axis='x')
    # Bay projects beyond the supporting lower wall. The support tapers in half-steps.
    c.box(2,8,4,10,8,6,'spruce_planks')
    for x in(2,10):
        c.box(x,9,6,x,13,6,'stripped_spruce_log',axis='y')
        c.stair(x,5,4,'spruce_stairs','north',half='top')
        c.stair(x,6,5,'spruce_stairs','north',half='top')
        c.slab(x,7,6,'spruce_slab',kind='top')
    for x in range(3,10):
        for y in range(9,13):
            for z in(2,3,4):c.remove(x,y,z)
            c.put(x,y,5,'gray_stained_glass_pane',east=True,west=True,north=False,south=False,waterlogged=False)
            if x in(4,8):c.fence(x,y,6)
        c.trap(x,13,6,opened=False,half='top')
        c.trap(x,8,7)
    for x in(1,11):
        for y in range(10,13):c.trap(x,y,6,'dark_oak_trapdoor')
    for x in range(1,12):
        k=min(x-1,11-x)
        for z in range(3,8):c.slab(x,15+k//2,z,'waxed_weathered_cut_copper_slab',kind='top' if k%2 else 'bottom')
        for y in range(15,15+k//2):c.put(x,y,4,'spruce_planks')
    for x in range(2,11):
        c.stair(x,14,7,'spruce_stairs','north',half='top')
        c.slab(x,15,8,'spruce_slab')
    for x in(3,9):c.fence(x,7,5);c.lantern(x,6,5)
    c.steps=[('下墙与木架','凝灰岩砖打底，方解石填墙；主木柱竖向，Y=7、14横梁用横向原木，别让木纹方向都一样。'),('三格托架','每侧依次是贴墙倒楼梯、外移一格并升一格的倒楼梯、最外侧上半台阶；阶梯形下面是空气，不是三角实心墙。'),('外挑窗体','Y=8搭外挑平台，玻璃在Z=5、细栅栏在Z=6；活板门只做平台边沿与窗扇。'),('铜帽和灯','小窗顶用打蜡斑驳切制铜台阶，上下半格交替形成缓坡；檐下再加薄木台阶。灯笼挂在梁下，避开窗台操作面。')]
    c.connect()
    return [a,b,c]


def old_window():
    _,blocks=read_model(ROOT/'castle_v3/finish_v6/castle_v6.json')
    # Remove the foreground choir wall (Z>=48) to reveal the actual old keep window.
    # This is labeled as a section, not a whole-castle before/after.
    return {(x+8,y-5,z-40):(n,p,g) for (x,y,z),(n,p,g) in blocks.items() if -8<=x<=10 and 5<=y<=38 and 40<=z<=47}

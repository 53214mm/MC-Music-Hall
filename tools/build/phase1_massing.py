"""阶段 1 · 总体体块：只做体积、轮廓与体块关系。不加任何装饰。

设计依据：design/重构方案.md（已批准）。标高来自 tools/build/plan_massing.py。
生成的是"新体块"，不含细节（窗、线脚、扶壁、斗拱都留给后续阶段）。

体块清单与尺寸（设计坐标）：
  核心体块   X=-7..49   Z=-37..38   檐口 69，35° 坡屋顶到屋脊 89
  侧廊       核心两侧各挖出净宽 5、高 18 的廊（原有实心带内）
  中殿       X=8..35（净宽 28）净高 44，Z=42..117（长 76），屋脊 52
  中殿侧廊   净宽 6 外侧，单坡顶 18
  后殿       北端 Z=-49..-38，逐层收进，顶 30
  双塔       各 19×19，Z=118..123，塔顶 东 147 / 西 137
  门廊       两塔之间，18 宽 × 6 深，顶 26
  中央塔楼   核心屋脊 89 → 鼓座 137 → 尖顶 163
"""
from plan_massing import CENTER

# ---- 定稿标高 ----
CORE_EAVE = 69
CORE_RIDGE = 89
AISLE_TOP = 18
NAVE_H = 44
NAVE_RIDGE = 52
APSE_TOP = 30
TOWER_W = 19
TOWER_EAST_APEX = 147
TOWER_WEST_APEX = 137
TOWER_SPIRE_H = 44
LANTERN_TOP = 137
CENTRAL_APEX = 163
PORTAL_W, PORTAL_H = 18, 26

# ---- 平面边界 ----
CORE_X0, CORE_X1 = -7, 49
CORE_Z0, CORE_Z1 = -37, 38
NAVE_X0, NAVE_X1 = 8, 35              # 中殿净宽 28
NAVE_Z0 = 42
NAVE_Z1 = NAVE_Z0 + 75                 # 长 76
Z_APSE = -49
Z_TOWER0 = NAVE_Z1 + 1                 # 118
Z_TOWER1 = Z_TOWER0 + 5                # 123
WALL = 2


def generate():
    """返回 {(x, y, z): (name, props, group)}；group 一律 'shell'。"""
    b = {}

    def put(x, y, z, name):
        b[(x, y, z)] = (name, {}, 'shell')

    def slab(xa, xb, za, zb, y, name):
        for x in range(xa, xb + 1):
            for z in range(za, zb + 1):
                put(x, y, z, name)

    def walls(xa, xb, za, zb, ytop, name):
        for x in range(xa, xb + 1):
            for z in range(za, zb + 1):
                if x in (xa, xb) or z in (za, zb):
                    for y in range(0, ytop + 1):
                        put(x, y, z, name)

    def gable(xa, xb, za, zb, eave, ridge, axis='x'):
        """双坡屋顶：沿 axis 方向向脊线收。"""
        if axis == 'x':
            span = (xb - xa) // 2
            for step in range(span + 1):
                y = eave + round(step * (ridge - eave) / max(1, span))
                for x in (xa + step, xb - step):
                    if x > xb - step:
                        break
                    for z in range(za, zb + 1):
                        put(x, y, z, 'dark_prismarine')
        else:
            span = (zb - za) // 2
            for step in range(span + 1):
                y = eave + round(step * (ridge - eave) / max(1, span))
                for z in (za + step, zb - step):
                    if z > zb - step:
                        break
                    for x in range(xa, xb + 1):
                        put(x, y, z, 'dark_prismarine')

    # ---------- 1. 地基 ----------
    slab(CORE_X0 - 2, CORE_X1 + 2, Z_APSE - 1, Z_TOWER1 + 1, -1, 'smooth_stone')

    # ---------- 2. 核心体块 ----------
    walls(CORE_X0, CORE_X1, CORE_Z0, CORE_Z1, CORE_EAVE, 'white_concrete')
    gable(CORE_X0, CORE_X1, CORE_Z0, CORE_Z1, CORE_EAVE, CORE_RIDGE)

    # ---------- 3. 侧廊：从核心两侧的实心带里挖出 ----------
    for x0 in (CORE_X0 + WALL, CORE_X1 - WALL - 4):
        for x in range(x0, x0 + 5):
            for z in range(CORE_Z0, CORE_Z1 + 1):
                put(x, AISLE_TOP, z, 'light_blue_stained_glass')

    # ---------- 4. 中殿 ----------
    walls(NAVE_X0 - WALL, NAVE_X1 + WALL, NAVE_Z0, NAVE_Z1, NAVE_H, 'white_concrete')
    gable(NAVE_X0, NAVE_X1, NAVE_Z0, NAVE_Z1, NAVE_H, NAVE_RIDGE)
    # 中殿两侧的侧廊（单坡顶 18）
    for xa, xb in ((CORE_X0, NAVE_X0 - WALL - 1), (NAVE_X1 + WALL + 1, CORE_X1)):
        if xa <= xb:
            slab(xa, xb, NAVE_Z0, NAVE_Z1, AISLE_TOP, 'dark_prismarine')
    # 南端墙留出主入口洞
    for x in range(NAVE_X0 - WALL, NAVE_X1 + WALL + 1):
        for y in range(0, NAVE_RIDGE + 1):
            if NAVE_X0 - 1 <= x <= NAVE_X1 + 1 and y <= 20:
                continue
            put(x, y, NAVE_Z1, 'white_concrete')

    # ---------- 5. 后殿：北端逐层收进 ----------
    for i, z in enumerate(range(Z_APSE, CORE_Z0)):
        shrink = CORE_Z0 - z
        xa, xb = CORE_X0 + shrink, CORE_X1 - shrink
        if xa > xb:
            break
        top = max(6, APSE_TOP - shrink * 2)
        walls(xa, xb, z, z, top, 'white_concrete')
        slab(xa, xb, z, z, top, 'dark_prismarine')

    # ---------- 6. 双塔（19×19，受控不对称） ----------
    for xa, apex in ((CORE_X0, TOWER_WEST_APEX), (CORE_X1 - TOWER_W + 1, TOWER_EAST_APEX)):
        xb = xa + TOWER_W - 1
        shaft_top = apex - TOWER_SPIRE_H
        walls(xa, xb, Z_TOWER0, Z_TOWER1, shaft_top, 'white_concrete')
        if xb - xa >= 2:
            slab(xa + 1, xb - 1, Z_TOWER0 + 1, Z_TOWER1 - 1, shaft_top, 'dark_prismarine')
        # 尖塔：逐层收分
        span = apex - shaft_top
        for step in range(1, span + 1):
            y = shaft_top + step
            shrink = max(0, round(step * (TOWER_W // 2) / span * 2))
            xa2, xb2 = xa + shrink, xb - shrink
            za2, zb2 = Z_TOWER0 + shrink, Z_TOWER1 - shrink
            if xa2 > xb2 or za2 > zb2:
                mid_x, mid_z = (xa + xb) // 2, (Z_TOWER0 + Z_TOWER1) // 2
                xa2 = xb2 = mid_x
                za2 = zb2 = mid_z
            for x in range(xa2, xb2 + 1):
                for z in range(za2, zb2 + 1):
                    put(x, y, z, 'dark_prismarine')

    # ---------- 7. 门廊：两塔之间 ----------
    for x in range(CENTER - PORTAL_W // 2, CENTER + PORTAL_W // 2 + 1):
        for z in range(Z_TOWER0, Z_TOWER1 + 1):
            for y in range(0, PORTAL_H + 1):
                if y == PORTAL_H or z == Z_TOWER1:
                    put(x, y, z, 'smooth_quartz')
                elif abs(x - CENTER) <= 3 and y <= 20:
                    continue                     # 主入口洞
                elif x in (CENTER - PORTAL_W // 2, CENTER + PORTAL_W // 2):
                    put(x, y, z, 'white_concrete')

    # ---------- 8. 中央塔楼：屋脊 → 鼓座 → 尖顶 ----------
    # 鼓座：从核心屋脊起，半径由 7 收到 5；尖顶：从 5 逐层收到 1。
    # 鼓座顶端直径 11（约核心 57 宽的 1/5），与真实交叉塔的量级相符。
    LANTERN_R0, LANTERN_R1 = 7, 5
    for y in range(CORE_RIDGE, CENTRAL_APEX + 1):
        if y <= LANTERN_TOP:
            t = (y - CORE_RIDGE) / max(1, LANTERN_TOP - CORE_RIDGE)
            r = round(LANTERN_R0 + (LANTERN_R1 - LANTERN_R0) * t)
        else:
            t = (CENTRAL_APEX - y) / max(1, CENTRAL_APEX - LANTERN_TOP)
            r = max(0, round(1 + (LANTERN_R1 - 1) * t))
        if r <= 0:
            put(CENTER, y, 1, 'dark_prismarine')
            continue
        for x in range(CENTER - r, CENTER + r + 1):
            for z in range(1 - r, 1 + r + 1):
                if abs(x - CENTER) + abs(z - 1) <= r:
                    edge = abs(x - CENTER) == r or abs(z - 1) == r
                    put(x, y, z, 'smooth_quartz' if edge else 'light_blue_stained_glass')

    return b

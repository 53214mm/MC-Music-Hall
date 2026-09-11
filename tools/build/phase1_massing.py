"""阶段 1 修订版 · 总体体块：按反馈解决三个问题。

问题 1 双塔像"长方柱 + 一根针" → 改成 4 级明确收分（塔基座 / 下段塔身 / 钟室 / 尖顶），
        钟室向外挑出，形成哥特钟楼特有的"外挑钟室"轮廓。
问题 2 中央塔像"从大屋顶插出来的针" → 改成 5 级：交叉脊 → 基座 → 过渡体 → 塔身 → 尖顶，
        至少 3 次收分，塔根落在交叉脊上而不是落在平屋面上。
问题 3 核心仍是"完整大矩形" → 用体块本身打碎：南北各出横向耳堂 + 侧廊体块成层 +
        屋顶分三段不同坡度，使 45° 轴测下不再读成一块盒子。

约束：不改音乐模块、红石线路、时序、听音点。塔与机房只靠 Z 向错开保证不重叠。
只做体块，不做窗/扶壁/彩绘/材质分层/线脚/室内/装饰。
"""
from plan_massing import CENTER

# ===================== 定稿标高 =====================
CORE_EAVE = 69            # 机房顶 68 之上 1 格
CORE_RIDGE = 89           # 35° 坡
AISLE_TOP = 18            # 中殿净高 44 × 0.42
TRANCEPT_TOP = 58         # 耳堂山墙顶，介于侧廊 18 与核心 89 之间
NAVE_H = 44
NAVE_RIDGE = 52
APSE_TOP = 34
TOWER_WEST_APEX = 137     # 受控不对称
TOWER_EAST_APEX = 147
LANTERN_BASE = CORE_RIDGE
LANTERN_STAGE1 = 103      # 基座顶
LANTERN_STAGE2 = 119      # 鼓座顶
CENTRAL_APEX = 167        # 中央最高

# ===================== 平面 =====================
CORE_X0, CORE_X1 = -7, 49
CORE_Z0, CORE_Z1 = -37, 38

NAVE_X_OUT0, NAVE_X_OUT1 = 10, 32      # 中殿外墙外皮
NAVE_Z0 = 46
NAVE_Z1 = NAVE_Z0 + 70                 # 长 71，止于 116

TOWER_W, TOWER_D = 17, 17
TOWER_WEST_X0 = CORE_X0                # -7
TOWER_EAST_X1 = CORE_X1                # 49
TOWER_Z0 = NAVE_Z1 + 2                 # 118，与中殿南墙隔 1 格
TOWER_Z1 = TOWER_Z0 + TOWER_D - 1      # 129

TRANCEPT_X0, TRANCEPT_X1 = -13, 55     # 横向耳堂外皮（只在核心宽 57 内凸出，不撑大宽度）
TRANCEPT_Z0 = CORE_Z0 + 4
TRANCEPT_Z1 = CORE_Z1 - 4

APSE_Z0 = CORE_Z0 - 12


def generate():
    b = {}

    def put(x, y, z, name):
        b[(x, y, z)] = (name, {}, 'shell')

    def slab(xa, xb, ya, yb, za, zb, name):
        for x in range(xa, xb + 1):
            for y in range(ya, yb + 1):
                for z in range(za, zb + 1):
                    put(x, y, z, name)

    def ring(xa, xb, za, zb, y, name):
        for x in range(xa, xb + 1):
            for z in range(za, zb + 1):
                if x in (xa, xb) or z in (za, zb):
                    put(x, y, z, name)

    def walls(xa, xb, za, zb, ytop, name='white_concrete'):
        """只砌四周墙，绝不封顶——封顶会压在音乐模块上。"""
        for y in range(0, ytop + 1):
            ring(xa, xb, za, zb, y, name)

    def roof_z(xa, xb, za, zb, eave, ridge, name='dark_prismarine'):
        """沿 Z 向的双坡屋顶，脊线在 Z 中点。

        核心机房占 X 0..42、Z -20..8（含走廊），任何横墙都会压到模块，
        所以核心屋顶不设横向内墙，只用这一面大坡屋顶从中轴往南北两端降。
        """
        mid = (za + zb) / 2
        half = max(1.0, (zb - za) / 2)
        for z in range(za, zb + 1):
            y = round(ridge - abs(z - mid) / half * (ridge - eave))
            for x in range(xa, xb + 1):
                put(x, y, z, name)

    def roof_x(xa, xb, za, zb, eave, ridge, name='dark_prismarine', ymin=0):
        """沿 X 向的双坡屋顶，只铺屋面，不填内部。"""
        span = max(1, (xb - xa) // 2)
        for step in range(span + 1):
            y = eave + round(step * (ridge - eave) / span)
            if y < ymin:
                continue
            for x in (xa + step, xb - step):
                if x > xb - step:
                    break
                for z in range(za, zb + 1):
                    put(x, y, z, name)

    # ============ 1. 地基 ============
    slab(TRANCEPT_X0 - 2, TRANCEPT_X1 + 2, -1, -1, APSE_Z0 - 1, TOWER_Z1 + 1, 'smooth_stone')

    # ============ 2. 核心体块 ============
    # 实测：机房占 X 0..42、Z -20..8，任何横向内墙都会压到模块，
    # 所以核心只砌四周外墙 + 一面沿 Z 的双坡屋顶，靠屋面起伏与侧廊成层打碎体块。
    # 外墙内收 3 格，避免与模块外缘（X 0 与 42）相撞。
    walls(CORE_X0, CORE_X1, CORE_Z0, CORE_Z1, CORE_EAVE, 'white_concrete')
    roof_z(CORE_X0, CORE_X1, CORE_Z0, CORE_Z1, CORE_EAVE, CORE_RIDGE)

    # ============ 3. 侧廊：核心两侧成层（体块层级，不是装饰） ============
    slab(CORE_X0 + 2, CORE_X0 + 6, AISLE_TOP, AISLE_TOP, CORE_Z0, CORE_Z1, 'white_concrete')
    slab(CORE_X1 - 6, CORE_X1 - 2, AISLE_TOP, AISLE_TOP, CORE_Z0, CORE_Z1, 'white_concrete')

    # ============ 4. 横向耳堂：向前后、向左右凸出，打碎核心大矩形 ============
    for xa, xb in ((TRANCEPT_X0, CORE_X0 - 1), (CORE_X1 + 1, TRANCEPT_X1)):
        walls(xa, xb, TRANCEPT_Z0, TRANCEPT_Z1, TRANCEPT_TOP - 6, 'white_concrete')
        # 山墙：沿 Z 向双坡，脊线在耳堂中段
        mid = (TRANCEPT_Z0 + TRANCEPT_Z1) // 2
        span = max(1, (TRANCEPT_Z1 - TRANCEPT_Z0) // 2)
        for step in range(span + 1):
            y = TRANCEPT_TOP - 6 + round(step * 6 / span)
            for z in (mid - step, mid + step):
                if TRANCEPT_Z0 <= z <= TRANCEPT_Z1:
                    for x in range(xa, xb + 1):
                        put(x, y, z, 'dark_prismarine')

    # ============ 5. 中殿：外墙 + 坡屋顶 ============
    walls(NAVE_X_OUT0, NAVE_X_OUT1, NAVE_Z0, NAVE_Z1, NAVE_H, 'white_concrete')
    roof_x(NAVE_X_OUT0, NAVE_X_OUT1, NAVE_Z0, NAVE_Z1, NAVE_H, NAVE_RIDGE, ymin=NAVE_H)
    # 中殿两侧侧廊（低一档，单坡顶）
    slab(CORE_X0, NAVE_X_OUT0 - 1, AISLE_TOP, AISLE_TOP, NAVE_Z0, NAVE_Z1, 'white_concrete')
    slab(NAVE_X_OUT1 + 1, CORE_X1, AISLE_TOP, AISLE_TOP, NAVE_Z0, NAVE_Z1, 'white_concrete')
    # 南端墙留主入口洞
    for x in range(NAVE_X_OUT0, NAVE_X_OUT1 + 1):
        for y in range(0, NAVE_RIDGE + 1):
            if NAVE_X_OUT0 + 3 <= x <= NAVE_X_OUT1 - 3 and y <= 22:
                continue
            put(x, y, NAVE_Z1, 'white_concrete')

    # ============ 6. 后殿：北端逐层收进 ============
    for i, z in enumerate(range(APSE_Z0, CORE_Z0)):
        shrink = CORE_Z0 - z
        xa, xb = CORE_X0 + shrink, CORE_X1 - shrink
        if xa > xb:
            break
        top = max(8, APSE_TOP - shrink * 3)
        walls(xa, xb, z, z, top, 'white_concrete')
        ring(xa, xb, z, z, top, 'dark_prismarine')

    # ============ 7. 双塔：4 级明确收分 ============
    for x0, apex in ((TOWER_WEST_X0, TOWER_WEST_APEX),
                     (TOWER_EAST_X1 - TOWER_W + 1, TOWER_EAST_APEX)):
        x1 = x0 + TOWER_W - 1
        z0, z1 = TOWER_Z0, TOWER_Z1
        spire_h = 46
        belfry_top = apex - spire_h          # 钟室顶
        belfry_base = belfry_top - 26        # 钟室底
        shaft_top = belfry_base - 12         # 下段塔身顶（束带层）
        plinth_top = shaft_top - 26          # 塔基座顶

        # —— 第 1 级：塔基座（最宽，带四角扶壁）——
        walls(x0, x1, z0, z1, plinth_top, 'white_concrete')
        for cx in (x0, x1):
            for cz in (z0, z1):
                for dy in range(0, 6):
                    for dx in (-1, 0, 1):
                        for dz in (-1, 0, 1):
                            if 0 <= dx + 1 <= 2 and 0 <= dz + 1 <= 2:
                                px, pz = cx + dx, cz + dz
                                if x0 - 1 <= px <= x1 + 1 and z0 - 1 <= pz <= z1 + 1:
                                    put(px, dy, pz, 'polished_andesite')

        # —— 第 2 级：下段塔身（收进 1 格，四角留扶壁立柱）——
        sx0, sx1, sz0, sz1 = x0 + 1, x1 - 1, z0 + 1, z1 - 1
        walls(sx0, sx1, sz0, sz1, shaft_top, 'white_concrete')
        for cx in (sx0, sx1):
            for cz in (sz0, sz1):
                for y in range(plinth_top, shaft_top + 1):
                    put(cx, y, cz, 'polished_andesite')
        # 束带层：外挑 1 格
        ring(sx0 - 1, sx1 + 1, sz0 - 1, sz1 + 1, shaft_top, 'smooth_quartz')

        # —— 第 3 级：钟室（向外挑出，哥特钟楼的标志性轮廓）——
        bx0, bx1, bz0, bz1 = x0, x1, z0, z1
        for offset, y in ((1, belfry_base), (2, belfry_base + 1)):
            ring(max(bx0 - offset, x0 - 2), min(bx1 + offset, x1 + 2),
                 max(bz0 - offset, z0 - 2), min(bz1 + offset, z1 + 2), y, 'smooth_quartz')
        walls(bx0, bx1, bz0, bz1, belfry_top, 'white_concrete')
        for cx in (bx0, bx1):
            for cz in (bz0, bz1):
                for y in range(belfry_base, belfry_top + 1):
                    put(cx, y, cz, 'polished_andesite')
        # 钟室顶部角部小尖塔（纯体块）
        for cx in (bx0, bx1):
            for cz in (bz0, bz1):
                for dy in range(1, 5):
                    put(cx, belfry_top + dy, cz, 'dark_prismarine')

        # —— 第 4 级：尖顶（八边形收分，逐层缩）——
        for step in range(1, spire_h + 1):
            y = belfry_top + step
            shrink = round(step * ((TOWER_W - 2) / 2) / spire_h * 2)
            xa, xb = bx0 + shrink, bx1 - shrink
            za, zb = bz0 + shrink, bz1 - shrink
            if xa >= xb or za >= zb:
                put((bx0 + bx1) // 2, y, (bz0 + bz1) // 2, 'dark_prismarine')
                continue
            ring(xa, xb, za, zb, y, 'dark_prismarine')
            slab(xa + 1, xb - 1, y, y, za + 1, zb - 1, 'dark_prismarine')

    # ============ 8. 中央塔：5 级渐进，塔根落在交叉脊上 ============
    def band(y, xa, xb, za, zb, name):
        ring(xa, xb, za, zb, y, name)
        slab(xa + 1, xb - 1, y, y, za + 1, zb - 1, 'white_concrete')

    cx, cz = CENTER, 0
    # 级 1：基座 22×18 → 收到 16×12（落在核心交叉脊线上）
    for y in range(LANTERN_BASE, LANTERN_STAGE1 + 1):
        t = (y - LANTERN_BASE) / max(1, LANTERN_STAGE1 - LANTERN_BASE)
        hx = round(11 - 3 * t)
        hz = round(9 - 3 * t)
        if t < 0.08:
            hx, hz = 11, 9
        band(y, cx - hx, cx + hx, cz - hz, cz + hz, 'smooth_quartz')
    # 级 2：过渡体 16×12 → 12×12
    for y in range(LANTERN_STAGE1 + 1, LANTERN_STAGE2 + 1):
        t = (y - LANTERN_STAGE1) / max(1, LANTERN_STAGE2 - LANTERN_STAGE1)
        hx = round(8 - 2 * t)
        hz = 6
        band(y, cx - hx, cx + hx, cz - hz, cz + hz, 'smooth_quartz')
    # 级 3：塔身 12×12 → 10×10（细分为尖顶起点）
    for y in range(LANTERN_STAGE2 + 1, CENTRAL_APEX + 1):
        t = (y - LANTERN_STAGE2) / max(1, CENTRAL_APEX - LANTERN_STAGE2)
        r = max(1, round(5 - 4 * t))
        band(y, cx - r, cx + r, cz - r, cz + r, 'smooth_quartz')

    return b

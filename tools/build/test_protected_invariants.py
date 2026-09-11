"""阶段 0 · 保护性断言：把现有建筑中"绝对不可动"的部分锁死。

重构方案（design/重构方案.md）第 0 阶段。目的：后续任何一次外壳改动，
只要碰到音乐时钟、机房、听音点或连接电路，测试立刻失败——而不是等到实机播放才发现。

本文件只读，改动建筑不会被它自动修正，它只负责报警。
用法：python -m unittest test_protected_invariants   （在 tools/build 目录下）
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_music_hall as B
from hall_connections import generate_connections, verify_rising_signal

# 模块顺序与南/北岸（与设计稿一致）；顺序一旦变化，音乐顺序就错了
EXPECTED_ORDER = [(1, True), (2, False), (3, False), (4, True), (5, True),
                  (6, False), (7, False), (8, True), (9, True), (10, False), (11, False)]
EXPECTED_BASE_Y = {1: 0, 2: 0, 3: 12, 4: 12, 5: 24, 6: 24, 7: 36, 8: 36, 9: 48, 10: 48, 11: 60}
EXPECTED_NOTES = 2307
EXPECTED_MODULE_BLOCKS = 29514
EXPECTED_INPUT_TICKS = {i: 320 * (i - 1) + (2 if i == 11 else 0) for i in range(1, 12)}
EXPECTED_MUSIC_ZERO = {i: 7 + 320 * (i - 1) for i in range(1, 12)}
LISTENING_POINT = (21, 32, 3)          # 玩家耳朵位置；方案里的 (21,32,3.5) 取整
TOTAL_BLOCKS_BEFORE = 100349           # 外壳 + 模块（不含控制电路）的既有规模
# 实测：外壳有 4 处盖住控制红石粉，构建脚本靠"拆除检修开口"处理。
# 位置一旦变化，检修开口清单必须同步更新，否则构筑出来的红石爬升会断。
EXPECTED_APERTURE_DUST = [(10, 10, 4), (11, 34, 4), (32, 22, 3), (32, 46, 3)]


class ProtectedInvariants(unittest.TestCase):
    """一次装载，多个断言共用，避免重复跑十几秒的构建。"""

    @classmethod
    def setUpClass(cls):
        cls.modules, cls.placement = B.load_modules()
        cls.shell = B.make_shell()
        cls.all_blocks = {**cls.modules, **cls.shell}
        cls.control, cls.connection_report = generate_connections(cls.modules, B.transform, B.is_north)
        cls.signal = verify_rising_signal(cls.modules, cls.control, B.transform)
        # 每个模块的实测包围盒（设计坐标）
        cls.envelopes = {}
        for number in range(1, 12):
            tag = str(number).zfill(2)
            pts = [p for p in cls.modules if cls.modules[p][2] == tag]
            cls.envelopes[number] = (
                min(p[0] for p in pts), max(p[0] for p in pts),
                min(p[1] for p in pts), max(p[1] for p in pts),
                min(p[2] for p in pts), max(p[2] for p in pts),
            )

    # ---------- 一、模块与红石时钟 ----------
    def test_note_count_unchanged(self):
        notes = sum(1 for state in self.modules.values() if state[0] == 'note_block')
        self.assertEqual(notes, EXPECTED_NOTES, '音符盒总数变化 = 乐谱被改动')

    def test_module_block_count_unchanged(self):
        self.assertEqual(len(self.modules), EXPECTED_MODULE_BLOCKS,
                         '模块方块总数变化 = 某个模块被移动、旋转或裁剪')

    def test_module_placement_unchanged(self):
        got = [(item['module'], item['north']) for item in self.placement]
        self.assertEqual(got, EXPECTED_ORDER, '模块顺序或南北岸变化 = 音乐顺序被改动')
        for item in self.placement:
            self.assertEqual(item['baseY'], EXPECTED_BASE_Y[item['module']],
                             f"模块 {item['module']} 的楼层基准高度被改动")
            self.assertEqual(item['rotation'], 180 if item['north'] else 0,
                             f"模块 {item['module']} 的旋转被改动")

    def test_every_module_envelope_is_intact(self):
        """模块必须在自己的包围盒内一个不差地存在——少一个方块就是被裁了。"""
        for number, (x0, x1, y0, y1, z0, z1) in self.envelopes.items():
            tag = str(number).zfill(2)
            inside = sum(1 for (x, y, z), s in self.modules.items()
                         if s[2] == tag and x0 <= x <= x1 and y0 <= y <= y1 and z0 <= z <= z1)
            total = sum(1 for s in self.modules.values() if s[2] == tag)
            self.assertEqual(inside, total, f'模块 {number} 有方块跑到包围盒之外')

    def test_music_timing_unchanged(self):
        """时钟：11 个模块收到的输入刻与乐谱零点必须一字不差。"""
        self.assertEqual(self.signal['receivedInputTicks'], EXPECTED_INPUT_TICKS,
                         '模块收到的输入刻变化 = 启动时序被破坏')
        self.assertEqual(self.signal['musicZeroTicks'], EXPECTED_MUSIC_ZERO,
                         '乐谱零点变化 = 音乐会对不齐')
        self.assertEqual(len(self.connection_report['connections']), 10,
                         '启动链的段数变化')

    def test_note_block_has_air_above(self):
        for position, state in self.modules.items():
            if state[0] == 'note_block':
                above = (position[0], position[1] + 1, position[2])
                self.assertNotIn(above, self.all_blocks,
                                 f'音符盒 {position} 正上方被占 = 这只音符会失声')

    # ---------- 二、听音与走线空间 ----------
    def test_listening_point_is_clear(self):
        for dy in (0, 1):
            point = (LISTENING_POINT[0], LISTENING_POINT[1] + dy, LISTENING_POINT[2])
            self.assertNotIn(point, self.all_blocks, f'听音点 {point} 被方块占用')

    def test_listening_point_has_floor(self):
        floor = (LISTENING_POINT[0], LISTENING_POINT[1] - 3, LISTENING_POINT[2])
        self.assertIn(floor, self.all_blocks, f'听音点脚下的悬挑平台 {floor} 消失了')

    def _covered_dust(self, blocks):
        """返回"上方有方块"的控制红石粉位置；这些位置在游戏里会断掉爬升连接。"""
        bad = []
        for position, state in self.control.items():
            if state[0] != 'redstone_wire':
                continue
            above = (position[0], position[1] + 1, position[2])
            if above in blocks:
                bad.append(position)
        return sorted(bad)

    def test_no_dust_is_covered_in_current_build(self):
        """现状：外壳有 4 处盖住红石粉，构建脚本靠"拆除检修开口"处理掉它们。"""
        covered = self._covered_dust(self.shell)
        self.assertEqual(covered, EXPECTED_APERTURE_DUST,
                         '被外壳盖住的红石粉位置变了——检修开口清单要同步更新，'
                         '否则构筑出来的红石爬升会断')

    def test_no_dust_is_covered_after_apertures(self):
        """按构建脚本的做法拆掉检修开口后，红石爬升与音符盒上方必须全部通畅。"""
        apertures = self._aperture_positions()
        cleared = {p: s for p, s in self.shell.items() if p not in apertures}
        merged = {**self.modules, **cleared, **self.control}
        for position in self._covered_dust(merged):
            self.fail(f'拆掉检修开口后，控制红石粉 {position} 上方仍有方块')
        notes_covered = [p for p, s in self.modules.items()
                         if s[0] == 'note_block'
                         and (p[0], p[1] + 1, p[2]) in merged]
        self.assertEqual(notes_covered, [], f'音符盒上方被盖住：{notes_covered[:5]}')

    def _aperture_positions(self):
        """构建脚本预留的检修开口：控制红石粉/中继器/按钮周围 1 格、上方 2 格。"""
        clear = set()
        for (x, y, z), state in self.control.items():
            if state[0] in ('redstone_wire', 'repeater', 'stone_button'):
                for dx in (-1, 0, 1):
                    for dy in (0, 1):
                        for dz in (-1, 0, 1):
                            clear.add((x + dx, y + dy, z + dz))
        return clear

    # ---------- 三、规模不倒退 ----------
    def test_scale_does_not_shrink(self):
        """允许重构把外壳做大，但绝不允许把既有外壳拆小到伤及机房周边。"""
        shell_now = len(self.shell)
        self.assertGreaterEqual(shell_now, 40000,
                                f'外壳从 70835 掉到 {shell_now} = 被大面积拆除，需要人工确认')


if __name__ == '__main__':
    unittest.main()

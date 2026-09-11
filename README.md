# Departures · 水晶教堂红石音乐馆

把《Departures》做成 11 个模块的红石音乐机，装进一座白蓝水晶教堂外壳，并用独立的控制主线统一自动启动。
目标运行版本：**Minecraft Java 26.3-snapshot-9**（见 `design/target_version.json`）。

**当前状态：结构与电路已全部生成并通过静态核验，但尚未在 Minecraft 实机播放验收。**
播放期间不要重复按启动键。

## 目录结构

```
design/          设计文档、目标版本、布局审计结果
  ├─ 水晶音乐馆设计草案.md    空间方案、连接原则、施工与验证顺序（必读）
  ├─ 启动时序核验.md          11 个模块的启动延迟推导与验证边界
  ├─ target_version.json     目标游戏版本（构建脚本强制读取）
  └─ layout_audit.json       各模块坐标/朝向/音符距离，由 audit_layout.py 生成

plan_final/      钢琴 v3 正式乐谱（施工数据源）
  ├─ departures_full_10tps.nbs          整首试听与总校验
  ├─ departures_module_01..11.nbs       逐模块，在 OpenNBS 中导出结构
  ├─ departures_note_schedule.csv       每个音符盒的时间、音高、垫块、右击次数
  ├─ departures_timing_modules.csv      主时间线每段中继器的档位
  ├─ departures_materials.json          精确逻辑材料统计
  └─ README.md                          施工规则（由 build_departures_plan.py 生成）

plan_preview/    用户试听后选定的钢琴 v3 试听文件（与 plan_final 逐事件相同）

nbt_export/      OpenNBS 导出的模块结构（构建输入，11 个）
  ├─ module_01.nbt
  └─ departures_module_02..11.nbt

build/           生成的施工产物
  └─ music_hall/
      ├─ 水晶音乐馆施工图.html      逐层施工图 + 轴测预览 + 材料表（总入口）
      ├─ 材料表.md                  外壳 / 连接 / 模块分列的材料清单
      ├─ build_report.json          方块总数、放置参数、时序核验结果
      ├─ connection_report.json     10 段启动链的延迟预算与路由路径
      ├─ tile_manifest.json         分块结构文件的偏移表
      ├─ structure_tiles/           52 个分块 NBT，供结构方块导入（合计 103029 方块）
      └─ music_hall_reference.nbt   合并参考件；超过单个结构方块加载上限，仅供比对

tools/           全部脚本
  ├─ verify_all.py              一条命令跑完全部核验
  ├─ analyze_midi.py            只读分析 MIDI（音域、和弦、每 16 小节音符数）
  ├─ build_departures_plan.py   生成 plan_final/ 全套 NBS 与 CSV
  ├─ check_piano_final.py       校验 试听版 = 正式版 = 11 模块拼接
  ├─ voicing_ab_record.py       历史记录：音色 A/B 试听的规则（已不可运行）
  ├─ build/                     施工生成与审计
  │   ├─ build_music_hall.py        主构建：变换、拼装、布线、出图（改这里）
  │   ├─ church_shell.py            教堂外壳几何
  │   ├─ hall_connections.py        控制主线路由与延迟预算
  │   ├─ music_hall_viewer.html     施工图模板（占位符由构建脚本填充）
  │   ├─ audit_export_timing.py     从 NBT 反推音符时刻，对比 CSV
  │   ├─ audit_layout.py            模块放置审计（只读）
  │   ├─ test_hall_builder.py       含"11 模块时序必须为 7+320×(i-1)"硬断言
  │   └─ test_structure_bounds.py   NBT size 字段小于实际边界时的显示修正
  └─ viewer/                    独立工具：NBT 逐层施工图查看器（可单独分享）
      ├─ nbt_structure_to_json.py   NBT → JSON / 交互式 HTML
      ├─ open-viewer.bat            把 .nbt 拖到它上面即可出图
      └─ 使用说明.txt
```

## 执行顺序

```bash
# 0. 全量核验（只读，约 40 秒）
python tools/verify_all.py

# 1. 改乐谱：需自备源 MIDI（.mid 不在本仓库内）
python tools/analyze_midi.py path/to/departures.mid
python tools/build_departures_plan.py path/to/departures.mid --output plan_final
python tools/check_piano_final.py

# 2. 改建筑或电路：用 OpenNBS 把 plan_final/*.nbs 导出成 nbt_export/*.nbt，然后重建
python tools/build/music_hall/build_music_hall.py

# 3. 看施工图：直接双击
build/music_hall/水晶音乐馆施工图.html
```

## 施工顺序（详见 design/水晶音乐馆设计草案.md）

1. 先搭 module_01 与 02 及一段控制主线试听，确认单模块完整。
2. 实测 01—11 每个模块"输入→首音"的延迟，反推 L_i；模块 11 启动塔与其余不同，必须单独测。
3. 校准全部时序，重点验证 01→02、05→06、10→11 三个接缝。
4. 按设计稿定位六层模块，逐层验证；不先封外壳。
5. 测试完整歌曲、重复启动锁、曲终复位。
6. 最后完成外墙与穹顶，并复测音符盒上方空气与固定点音量。

## 注意事项

- 各模块乐谱**开头带静音**（首音本地刻 29/3/1/2/1/0/1/4/2/1/14），因此外部输入到乐谱零点的延迟必须实机标定，不能假设 11 个模块相等。
- 全部时序结论来自静态 NBT 与红石上升沿图模型，**没有做 Minecraft 仿真**；红石粉更新顺序、区块加载、脉冲宽度均未验证。
- Java 中继器的 `facing` 指向**输入**侧：`east→输出西`、`west→输出东`、`north→输出南`、`south→输出北`。此规则只适用于中继器。
- 音符盒顶部必须始终留空气；固定听音点设计坐标为 (21,32,3.5)，不是地板方块坐标。
- 48 格是可听距离，不是均匀音量保证；广场与底层入口不保证听全曲。

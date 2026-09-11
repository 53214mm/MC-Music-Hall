"""历史记录：当初为选定音色生成 A/B 试听文件的脚本，现已不能直接运行。

它读取的是已删除的石头版乐谱目录（原 departures_redstone/departures_note_schedule.csv），
产出用户试听后选定的钢琴 v3 —— 也就是现在 plan_preview/ 里的两个文件。
保留本文件只为记录当时的音色决策依据，不参与当前任何构建流程。

关键规则（若将来重做 A/B，照此实现）：
- 音符盒音高 = 垫块基准音 + 右击次数；基准音 Double Bass=30、Harp/Piano=54、Chime=78。
- 低于原版音域的 Double Bass 音（音高 42–53）升八度改为钢琴，其余保留深低音与钟琴。
- 写出 NBS 用 tools/build_departures_plan.py 的 write_nbs。
"""

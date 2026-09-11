# Minecraft 教堂 / 哥特式建筑建造知识笔记

服务于本项目（`design/诊断报告.md`、`design/重构方案.md`）。
每条结论标注来源类型：**[共识]** 多来源一致、**[单源]** 单一来源、**[推导]** 我依据前述规律对本项目做的推理。
方块名保留英文，便于直接对照代码。

检索到的可追溯来源（本文引用）：

- [The Architecture of Builds — Craftdex](https://craftdex.net/articles/the-architecture-of-builds)
- [How to Add Detail to Builds in Minecraft (Trim, Depth & Accents)](https://guide.astroworldmc.com/how-to-add-detail-to-builds)
- [How to Choose a Block Palette in Minecraft](https://guide.astroworldmc.com/how-to-choose-a-block-palette)
- [Common mistakes new builders make — mc-mod.net](https://www.mc-mod.net/common-mistakes-new-builders-make/)
- [Minecraft Building Tips & Tricks: From Beginner to Pro Builder — Switchblade Gaming](https://www.switchbladegaming.com/minecraft/building-tips/)
- [我的世界【建筑基础教程】第三章：建筑的理论](https://3g.7723.cn/strategy/354358.html)
- [我的世界建筑技巧：贴吧大神经验](https://www.mczfw.com/blog/24963.html)
- [後浪云 Minecraft Wiki 教程：屋顶的比例](https://www.nzw6.com/94072.html)
- [我的世界屋顶建造指南](https://www.minecraftzw.com/15479.html)
- [Gothic Tutorial Series: The Pointed Arch — Planet Minecraft](https://www.planetminecraft.com/project/gothic-tutorial-series-pointed-arches/)
- [Neo-Gothic Cathedral — Planet Minecraft](https://www.planetminecraft.com/project/gothic-neogothic-cathedral/)
- [St. Aldren's Church — Planet Minecraft](https://www.planetminecraft.com/project/st-aldren-s-church/)
- [Salisbury Cathedral (1:1 scale) — Cathedral Talk](https://www.cathedraltalk.fm/minecraft/salisburycathedral1-1)
- [Amiens Cathedral (1:1 scale) — Cathedral Talk](https://www.cathedraltalk.fm/minecraft/amienscathedral1-1)
- [【Minecraft·建筑教程】小教堂保姆级教学](https://www.bilibili.com/video/BV1av7s6TEzL/)
- [成为MC建筑大师：从结构开始](https://www.bilibili.com/opus/1040486399048941577)
- [Как построить церковь в Minecraft — IGM.GG](https://igm.gg/media/d/kak-postroit-tserkov-v-minecraft-439d59dc)
- [我的世界【建筑构建与美学进阶技巧】](https://www.gamersky.com/handbook/201805/1054549.shtml)

> 说明：上表中我实际取用了其核心论点的来源，文中以链接直接标注；仅出现在检索结果里、未取用其论点的条目不在此列表内。

---

## 1. 教堂整体体块构成

**[共识]** 教堂之所以一眼可辨，不是因为尖顶，而是因为**体块有等级**：中殿最高最长、侧廊明显低一档、耳堂横向切断中殿、后殿收头、钟楼竖向压制全场。每个体块对应一个真实功能，因此高度差是**结果**而不是装饰。[Craftdex](https://craftdex.net/articles/the-architecture-of-builds)、[建筑基础教程·第三章](https://3g.7723.cn/strategy/354358.html) 都强调这一点：先定体块等级，再谈细节。

**[共识]** 判断是否"盒子拼接"的自检法：把模型压成纯黑剪影，如果只能数出 2–3 个矩形，就是盒子拼接；合格的作品剪影里应有 **4 个以上高度层次**，且每一层的高度起点不同。[Common mistakes](https://www.mc-mod.net/common-mistakes-new-builders-make/)

**[共识]** 避免盒子拼接的三条具体手段：
1. **体块之间要有"咬合"**，不是并排摆——让一个体块插进另一个体块的缺口，或让它们共用一段墙，而不是两个矩形相接。
2. **附属体量必须比主体低**，且低足够多（≥30%），差 2–3 格不算低，会被读成同一个体块。
3. **屋顶是体块的一部分**，不是事后加的盖子。体块的形状由屋面围合出来。

**[推导·本项目]** 现状核心体块 57×76×91 是立方体，前部中殿与核心同高（都在 Y=91 以下被同一道墙包住），耳堂与核心齐平——违反第 2 条和第 3 条。压成剪影后，Z 向能看到的只有"一个 136 长的平顶矩形 + 上面 3 个小凸起"。

## 2. 建筑比例

**[共识]** Minecraft 里最重要的一条比例经验是**不要用 1:1 做主体**。体块的长、宽、高三个数如果互相比值都在 1.5 以内，就会读成"方块/盒子"，无论贴多少装饰。[Craftdex](https://craftdex.net/articles/the-architecture-of-builds)、[建筑的理论](https://3g.7723.cn/strategy/354358.html) 均指出：让三个维度中至少有一个明显压倒其他两个，特征才成立。

**[推导]** 现实哥特教堂中殿剖面的高:宽约 2.5–3.5（Amiens 中殿净高约 42 m、宽约 14.6 m ≈ 2.9），总长:总宽约 3–5。Minecraft 中不必照搬绝对值，但**比值区间可以照搬**，因为比值是视觉感受的直接来源。本项目实测高:宽 = **1.13**，远低于 2.5；总长:总宽 = **1.35**，远低于 3。

**[共识·屋顶]** 屋顶坡度：坡度太平（低于约 30°）远看像平顶，坡度过陡（高于约 60°）在方块里会显得尖细失真。常用区间是**约 40°–50°**，正好对应现实中"陡坡屋顶 + 山墙"的观感。[屋顶的比例](https://www.nzw6.com/94072.html)、[屋顶建造指南](https://www.minecraftzw.com/15479.html)

**[推导]** 40° 坡在方块里的实际做法：**每升高 4 格，向内收 4 格**（45°），或每升 1 格收 1.2 格（40°）。57 格跨的核心做 40° 坡需要升约 24 格；做 45° 则需要约 28 格。这也解释了为什么"给 57 格宽的建筑做一个真正的坡屋顶"必然会把屋脊抬得很高——这是必要的，不是浪费。

**[共识·空与挤]** 跨度多大算空：墙面或屋面的**连续无分割长度超过约 15 格**时，远看就会读成"一面大白墙"；超过 30 格则整个建筑都失去尺度感。解法不是贴装饰，而是插入**分割元素**（束带层、扶壁、窗组、屋檐），把连续面切到 15 格以下。[How to Add Detail](https://guide.astroworldmc.com/how-to-add-detail-to-builds)

**[共识·高与压迫]** 层高比（净高 ÷ 净宽）超过约 2.0 时，室内会显得"井"而不是"厅"；低于约 1.2 则显得压抑。教堂中殿取 **1.4–1.8** 最稳。[建筑的理论](https://3g.7723.cn/strategy/354358.html)

**[推导·本项目]** 中殿净宽 21、净高 56 → 比值 **2.67**，落在"井"的区间；方案中改为 28 宽 × 44 高 = **1.57**，进入舒适区。核心室内 57 宽 × 69 高 = 1.21，偏低但因为是机房大厅可接受——但必须加柱列打破。

## 3. 立面设计

**[共识]** 立面的核心概念是**进深面（depth plane）**：一个立面至少要存在 3 个不同进深的面，凹凸落差**至少 1 格**才算数——只有换色不算层次。[How to Add Detail](https://guide.astroworldmc.com/how-to-add-detail-to-builds)、[贴吧大神经验](https://www.mczfw.com/blog/24963.html)

**[共识]** 制造进深的具体手法（按性价比排序）：
1. **扶壁/壁柱外凸 1–2 格**（最有效，同时提供竖向节奏）
2. **窗洞内凹 1–3 格**（提供阴影，同时让玻璃"陷进去"而不是"贴上去"）
3. **檐口外挑 1 格 + 檐下加深一档材料**（制造水平阴影线）
4. **束带层 / 齿状挑檐（corbel table）**：沿水平方向每 1 格挑出 1 格再收进，形成锯齿阴影
5. **勒脚外凸 1 格**并换深色材料

**[共识]** 避免大面积平墙的可操作判据：**沿任意一条水平线取样材质与进深，变化次数应 ≥6 次**（每 6 格一次节奏变化）。[How to Add Detail](https://guide.astroworldmc.com/how-to-add-detail-to-builds)

**[共识]** 1 格 / 2 格 / 3 格进退的用法差异：
- 1 格：线脚、窗框、勒脚——制造"阴影线"，远看有效
- 2 格：扶壁、壁柱、门洞第一层退进——制造"结构感"
- 3 格：深窗龛、透视门洞（orders）——制造"可以走进去"的空间感

**[推导·本项目]** 现状 `church_shell.py` 的尖拱窗是**同一进深面换色**（`purple_stained_glass` 混在 `light_blue_stained_glass` 里），墙面 1 格厚，玫瑰窗贴在 91 格高的平墙上——三个手法全部违反上述规则，属于"换色冒充层次"。

## 4. 哥特式 / 中世纪特征

**[共识·尖拱]** 尖拱的本质是**两段圆弧相交**。方块里可行的做法是从拱脚起，**每升高 1 格向内收 1 格或每 2 格收 1 格**，到拱顶附近改为每格收 1 格形成"尖"。关键判据：拱的**起点必须是垂直的**（拱脚有一段直墙），否则会读成三角形而不是尖拱。[Gothic Tutorial Series: The Pointed Arch](https://www.planetminecraft.com/project/gothic-tutorial-series-pointed-arches/)

**[共识·飞扶壁]** 飞扶壁要有三个部分才成立：**外墩（pier）— 斜撑（flyer）— 中殿高侧墙的受力点**。只做斜撑不做外墩，会读成"墙上伸出来的棍子"。外墩顶部必须有**小尖塔（pinnacle）压重**，这既是视觉需要也是结构逻辑。[St. Aldren's Church](https://www.planetminecraft.com/project/st-aldren-s-church/)、[Neo-Gothic Cathedral](https://www.planetminecraft.com/project/gothic-neogothic-cathedral/)

**[共识·垂直感]** 垂直感来自**三个重复**：重复的竖肋、重复的尖拱、重复的束带层。单一高塔不产生垂直感，**节奏才产生垂直感**。[建筑的理论](https://3g.7723.cn/strategy/354358.html)

**[共识·对称与不对称]** 哥特教堂平面上高度对称，但**立面上常有受控不对称**：双塔不等高、单塔、或一侧加建礼拜堂。完全对称 + 完全等高会显得呆板；差异不宜大，**1–3 格或一个顶部型制的差别**就足够。[Amiens](https://www.cathedraltalk.fm/minecraft/amienscathedral1-1)、[Salisbury](https://www.cathedraltalk.fm/minecraft/salisburycathedral1-1) 的 1:1 复原讨论中都提到真实教堂的塔楼从未真正等高。

**[共识·轮廓线]** 强轮廓线来自**对比**：明亮的勾边材料紧邻深色屋面或深色塔尖。轮廓线不需要粗，**1 格即可，但必须在颜色上拉开**。[Block Palette](https://guide.astroworldmc.com/how-to-choose-a-block-palette)

## 5. 屋顶和轮廓

**[共识]** 屋顶必须有**层级**：主屋顶（最高最长）、侧屋顶（低 2 格以上，且是单坡或缓坡）、附属屋顶（门廊、后殿、塔楼），三者材质或坡度要能区分。[屋顶建造指南](https://www.minecraftzw.com/15479.html)

**[共识·天际线]** 远景辨识度由四个元素共同塑造：**脊线、山墙、女儿墙、尖顶**。只有尖顶没有脊线，远看就是"平顶 + 插了几根针"。[屋顶的比例](https://www.nzw6.com/94072.html)、[Common mistakes](https://www.mc-mod.net/common-mistakes-new-builders-make/)

**[共识]** 打破大屋面的手段：**老虎窗（dormer）**、**屋脊装饰**、**坡度分段**（下半段陡、上半段缓）。老虎窗每 10–15 格一个，宽 3 格即可，作用是把大屋面"切"成读得懂的小段。

**[推导·本项目]** 这是现状最大的失效点：核心屋面确实做了 `y=91-round(abs(x-21)*.78)` 的坡（约 38°），但**外墙砌到了 Y=91，比屋面还高**，于是侧视轮廓是完整直线。**屋面的造型做了，但没有露面**——这不是造型问题，是立面高度与屋面高度的关系错了。

## 6. 材质搭配

**[共识]** 材质体系应该是**四级**：主材（大面积，占 40–50%）、次材（结构体，占 25–30%）、勾边材（线脚窗框，占 10%）、强调材（屋面塔尖，占 10%）。每级**只承担一种结构角色**。[Block Palette](https://guide.astroworldmc.com/how-to-choose-a-block-palette)

**[共识]** 明度必须拉开档。"很多种材料"不等于"有层次"；三种明度差明显的材料，效果远好于六种明度接近的材料——后者会糊成一片。[Common mistakes](https://www.mc-mod.net/common-mistakes-new-builders-make/)

**[共识·渐变与旧化]** 旧化不是随机撒深色方块（那会变成噪点），而是**沿结构线渐变**：勒脚最深、随高度变浅；檐口下沿加深一道；窗洞内壁用深色加强阴影。渐变方向要跟随重力或光照，不能随机。[How to Add Detail](https://guide.astroworldmc.com/how-to-add-detail-to-builds)

**[推导·本项目]** 现状 `smooth_quartz` 的 `#e1e6e5` 与 `white_concrete` 的 `#e9eff1` 明度差仅约 3%，两者合计占外壳 49.5%——等于整个建筑是一种颜色。而 `dark_prismarine` 以 2 格宽长条铺在屋面上，成为全局最抢眼却没有结构意义的元素，正好是"强调材用错角色"。

## 7. 彩窗与采光

**[共识]** 玻璃在立面上的作用是**被框住的光**。因此必须先有**窗龛（退进）**，玻璃装在退进面上，外侧留 1 格阴影边；直接在外墙面上贴玻璃会读成"墙上开了洞的贴纸"。[How to Add Detail](https://guide.astroworldmc.com/how-to-add-detail-to-builds)

**[共识]** 尺寸经验：单扇窗**宽 3–5 格**是最舒服的区间。宽超过 5 格会变成玻璃幕墙，失去"窗"的读法；高宽比取 **2:1 到 3:1** 最有教堂感。

**[共识·神圣感]** 神圣感来自**明暗对比**而不是亮度：室内暗、窗洞亮、光柱投在地面上。因此外墙不要做发光灯带（会削弱对比），灯应放在室内——高侧窗窗台下、拱廊拱肩处。[建筑的理论](https://3g.7723.cn/strategy/354358.html)

**[推导·本项目]** 现状用 `sea_lantern` 每 12 格在外墙标一道水平线（腰线），属于典型的"外墙灯带"，恰好削弱了明暗对比。方案中应全部移入室内。

## 8. 室内空间

**[共识]** 室内必须与室外结构对应，否则就是"外面大教堂、里面空盒子"。自检法：**在室内数柱子，回到外面数扶壁，两者数量应当一致或成整倍数。**[Craftdex](https://craftdex.net/articles/the-architecture-of-builds)

**[共识·柱列]** 柱列的间距决定室内节奏：间距过大会读成"空旷大厅"，过小会读成"森林"。经验值：柱距约为柱高的 **0.8–1.2 倍**最舒服（例如柱高 10 格，柱距 8–12 格）。

**[共识·拱顶]** 方块里做拱顶的可行做法：柱头顶部用 stairs 做**肋（rib）**，肋之间用 slabs 或完整方块做**填板（web）**，肋交点加深色或加灯。纯用整块方块堆出的"拱"会读成实心天花板。

**[共识·分层]** 大型室内要有**竖向分层**：地面层（拱廊）— 中层回廊（triforium/gallery）— 高侧窗层（clerestory）。三层各占约 1/3、1/6、1/2 的高度。只有地面层 + 一个高得离谱的天花板，是最常见的室内失败。[建筑的理论](https://3g.7723.cn/strategy/354358.html)

**[推导·本项目]** 核心内部 57×76×69 完全无柱无分层；中殿 21 宽 × 56 高、室内无柱列——两条自检全部不通过。

## 9. Minecraft 特有的建造技巧

**[共识]** 方块清单与用途（按塑形能力排序）：

| 方块 | 用途 |
|---|---|
| `stairs` | 尖拱、线脚、柱头、屋檐、台阶、收分 |
| `slabs` | 半格过渡、拱顶填板、窗台、屋脊压顶 |
| `walls` | 栏杆、女儿墙、小尖塔、扶壁顶部（自带连接） |
| `fences` / `iron_bars` | 窗棂、栏杆、细杆、肋 |
| `trapdoors` | 百叶窗、小线脚、窗框细节 |
| `chains` / `lanterns` | 吊灯、拱顶下垂装饰 |
| `buttons` / `levers` | 铆钉、小圆点装饰 |
| `glass_panes` | 窗棂之间的细玻璃 |

来源：[How to Add Detail](https://guide.astroworldmc.com/how-to-add-detail-to-builds)、[建筑构建与美学进阶](https://www.gamersky.com/handbook/201805/1054549.shtml)、[成为MC建筑大师：从结构开始](https://www.bilibili.com/opus/1040486399048941577)

**[共识·细节密度]** 细节密度必须**随距离递减、随高度递减**：
- 地面到人眼高度（约 12 格）：最密，允许 1 格级的装饰
- 12 到 40 格：中等，用 2–3 格级的元素（窗组、束带层）
- 40 格以上：只保留大关系（扶壁节奏、檐口线），不要小装饰

理由：小装饰在远景里会互相抵消成噪点，反而破坏轮廓。[How to Add Detail](https://guide.astroworldmc.com/how-to-add-detail-to-builds)

**[共识·双尺度检查]** 每完成一个阶段必须做两次检查：**退到 100 格以外看剪影**（轮廓是否成立）、**贴到 3 格以内看细节**（是否有内容）。两者冲突时，**以剪影为准**。[Common mistakes](https://www.mc-mod.net/common-mistakes-new-builders-make/)、[Switchblade Gaming](https://www.switchbladegaming.com/minecraft/building-tips/)

## 10. 优秀作品的设计规律

以下 10 条可直接用于本项目，每条附"为什么更好看"。

| # | 规则 | 为什么更好看 | 本项目现状 |
|---|---|---|---|
| 1 | **先做剪影，后做细节**：体块阶段压成纯黑仍要能认出是教堂 | 人眼在远景只解析轮廓；轮廓错了，细节再多也救不回来 | ❌ 剪影是"一个平顶矩形 + 3 个小凸起" |
| 2 | **主体三维比值至少一个维度压倒另两个**（≥2:1） | 比值接近 1:1 会被读成方块，与"建筑"无关 | ❌ 高:宽 = 1.13 |
| 3 | **体块必须有等级，高度差 ≥30%**，且每级功能不同 | 差 2–3 格会被读成同一体块，"等级"不成立 | ❌ 中殿与核心被同一道 91 高的墙包住，无等级 |
| 4 | **外墙顶部必须低于屋脊**，让屋面从侧面可见 | 屋面是轮廓的主要起伏来源；被墙挡住等于没做屋顶 | ❌ 墙 91、屋面 91 且被墙遮住 |
| 5 | **任何立面至少 3 个进深面，落差 ≥1 格** | 只有换色不算层次；进深才产生阴影 | ❌ 窗是同一进深换色，墙 1 格厚 |
| 6 | **连续无分割的墙面/屋面不超过约 15 格** | 超过就失去尺度感，读成"大白墙" | ❌ 屋面连续 57 格，中殿墙面连续 56 格高 |
| 7 | **屋顶要有层级**：主屋顶 / 侧屋顶 / 附属屋顶，坡度或材质可区分 | 单层屋顶 = 单一轮廓 = 远景无信息量 | ❌ 前部屋面接近平顶，与核心屋面同材质逻辑 |
| 8 | **塔楼：塔身高度 ÷ 截面宽 = 3~3.5；尖塔高 ≈ 塔宽 × 2.3 以上** | 低于 3 显笨重，高于 4 显细弱；尖塔是塔的"结论"不是附件 | ⚠️ 现塔 69 高 ÷ 13 宽 = 5.3，偏细；且塔与主体比例失衡 |
| 9 | **室内柱子数 = 室外扶壁数** | 内外结构对应是"建筑"与"布景"的分界 | ❌ 室内 0 柱，室外数十扶壁 |
| 10 | **材质四级、每级一种角色、明度分明** | 材料多但明度接近 = 糊；角色明确才有结构感 | ❌ quartz 与 concrete 明度差 3% 却合计占 49.5% |

### 常见失败方式 · 对应症状 · 最高杠杆的修法

| 失败方式 | 症状 | 修法 |
|---|---|---|
| 火柴盒堆叠 | 只换材质不改体块 | 重做体块等级：主体压倒附属 ≥30%，体块之间咬合而非并排 |
| 立面过平 | 1 格厚墙上贴装饰 | 墙体加到 2–3 格，窗洞内凹，扶壁外凸——先造进深再加装饰 |
| 屋顶太简单 | 平顶或单一坡顶 | 主/侧/附属三级屋面 + 可见檐口 + 老虎窗 |
| 塔楼比例失衡 | 又细又高，像插上去的 | 塔身 3~3.5 比值，尖塔接一段过渡（钟室/角塔），不能直接插 |
| 装饰随机堆积 | 细看很满、远看一团 | 细节密度按高度递减；先做轮廓再决定哪里加装饰 |
| 材质多但结构薄 | 颜色很花、体量很虚 | 四级材质体系；强调色只用于屋面塔尖 |
| 细节多但轮廓差 | 近景惊艳、远景平庸 | 每个阶段先做双尺度检查，剪影优先 |

### 两条来自优秀作品的补充规律

**[共识]** **"一栋建筑只讲一个故事"**：确定一个主导母题（尖拱、竖肋、圆窗），全楼重复它，其余元素让位。母题混乱是大型作品显得业余的主因。[Craftdex](https://craftdex.net/articles/the-architecture-of-builds)

**[推导·本项目]** 本项目最合适的母题是**尖拱**——它与音乐主题（管风琴音箱、谱线）也契合，且可同时用于窗、门洞、柱廊、盲拱、屋面天窗，重复成本低。

---

## 学习结论：本项目要改的四件事（按杠杆排序）

1. **改比例**：高:宽 从 1.13 提到 ≥1.8（收窄 + 拔高）。不动的机房占了 57 格外宽，所以主要靠**拔高**。
2. **改轮廓**：消灭两条平顶长条——外墙顶低于屋脊，屋面必须可见；屋顶分三级。
3. **改进深**：墙体 1 格 → 2–3 格；窗洞内凹 2 格；扶壁外凸 1–2 格；檐口外挑——让每个立面有 3 个以上进深面。
4. **改室内**：加柱列与分层，做到"室内柱数 = 室外扶壁数"，先破除 57×76×69 的真空。

# Echo Castle · Departures Redstone Music Castle

[简体中文](README.md) · [English](README.en.md)

Current complete build: **V20**. This project arranges *Departures* into 11 redstone music modules inside a castle with a chapel, cloisters, towers, and underground maintenance passages. The target game version is Minecraft Java **26.3-snapshot-9**.

## Download and open the building manual

1. Open the [V20 Release page](https://github.com/53214mm/MC-Music-Hall/releases/tag/v20.0.0) and download the attached `Echo-Castle-V20-Full-Build-Pack.zip`. This is the ready-to-use package, not GitHub's automatically generated “Source code” archive. The download uses an ASCII filename; the files inside retain their Chinese names.
2. **Extract the entire ZIP**, then open `release_v20/余响堡_V20施工总册.html`. Keep all four accompanying images; do not download the HTML alone.
3. In “开始与定位” (Start and placement), enter the same world origin for every builder, then start the first construction phase.

Viewing the manual and building by hand require neither Python nor an internet connection. GitHub displays the HTML source rather than running the interactive manual, so download it and open it in a browser.

The manual has five sections: start and placement, construction workbench, music and mechanisms, materials and teamwork, and verification/NBT. **The README is bilingual; the manual interface remains in Chinese.** A ZIP SHA256 checksum file is attached to the Release. The [in-repository ZIP](castle_v3/余响堡_V20完整施工包.zip) is also available as a fallback.

## How to follow the construction grid

- Work through six phases. Within each phase, finish **all support blocks in batch A before components and attachments in batch B**. Each batch proceeds from lower to higher Y levels, then through the areas on the same level.
- The 16×16 grid is a horizontal, top-down slice. North is up, south down, east right, and west left. A small map shows the current area within the whole castle.
- Build only cells marked “本步” (this step). Click a cell to see its world coordinates, material, and Chinese placement instructions. “参考” means a reference block from another batch; “留空” means leave air.
- After checking a page, click “本页核对完成并继续” (mark this page checked and continue). You can undo, export, and merge completion records. The tool does not inspect the game or automatically synchronize other builders' progress.
- Follow the dedicated initial assembly instructions for the shortcut mechanisms. In particular, S3's piston head is an automatically generated part of the final closed state, not a block to place by hand.

See [construction methods and acceptance checks](castle_v3/release_v20/施工方法与验收.md) for the full instructions in Chinese.

## Included in V20

V20 combines the previous main-wall redesign, side-wall buttresses and projecting windows, interiors, lighting, 53 ordinary routes, three shortcuts, and all 11 music modules with their 10 connections. Do not add historical incremental packages on top of it.

| Item | Complete build |
| --- | ---: |
| Non-air block-state cells | 528,573 |
| Finished inventory items | 528,572 items, 88 types |
| Architectural light sources | 543 |
| Note blocks | 2,307 |
| Overall bounding dimensions | 189×170×267 |
| NBT tiles | 324 |

Material totals count finished items, not crafting ingredients. They exclude tools, temporary scaffolding, and wastage. See the [complete materials list](castle_v3/release_v20/全堡材料表.md).

## Verification limits and import safety

The saved model, materials, page coverage, attachment dependencies, and all 324 NBT files have been checked. The page script has passed static and DOM-stub tests. Illustrations are offline renders of vanilla block models, **not in-game screenshots. Real-browser and Minecraft in-game acceptance testing has not been completed.**

The NBT files contain **8,050,137 air cells** and may erase existing terrain or buildings inside their target area. Use them only in a backed-up, separate, empty Creative test world. Do not paste them over a friend's server. Manual construction does not require NBT imports.

In-game checks are still needed for walking every route, all three mechanisms and save/reload behavior, nighttime lighting, individual music modules, and uninterrupted playback of the whole song.

Evidence: [file verification](castle_v3/release_v20/verification.json) · [package checksums](castle_v3/release_v20/SHA256SUMS.json) · [project verification log](castle_v3/验证与进度.md).

## Repository layout

| Path | Purpose |
| --- | --- |
| `castle_v3/release_v20/` | Current complete manual, model, materials, images, and NBT tiles |
| `castle_v3/余响堡_V20完整施工包.zip` | Complete offline package to share with friends |
| Other directories under `castle_v3/` | Earlier models, design studies, and regression-test inputs; not the current building entry point |
| `departures_piano_final/` | Final piano arrangement, NBS files, and note/timing tables |
| `nbt_save/` | Original music-module NBT files, retained as protected inputs |
| `tools/` | Castle generators, grid viewer, rendering, and verification scripts |
| `design/` | Timing analysis, architectural references, and design records |
| `music_hall/`, `departures_redstone/`, and preview directories | Earlier hall and music-arrangement work |
| `share_nbt_viewer/` | Standalone NBT viewer tool |

This layout replaces the old remote entry points under `build/`, `plan_final/`, `plan_preview/`, and `nbt_export/`. Previous versions remain available in Git history.

## Development and rebuilding

Builders only need the ZIP. Generating or verifying the complete project additionally requires Python, Node.js, Pillow, and a local Minecraft JAR for the target version. The repository does not distribute the game JAR. Some historical scripts retain development-machine paths; this is not a fully portable, one-command toolchain.

Before rebuilding, check `JAR` in `tools/vanilla_mesh.py` and point it at your own 26.3-snapshot-9 installation. Do not upload game runtime files. The main V20 scripts are `build_castle_v20.py`, `render_castle_v20.py`, and `verify_castle_v20.py`. The verifier also writes reports, checksums, and the complete ZIP; it is not read-only.

Original attribution records for the music and references remain in the project. This repository does not claim ownership of the original song or Minecraft assets.

# 摆盘工程 / Print profiles

按打印板尺寸区分：小于 256 × 256 mm 不支持；提供 256 mm 与 H 系列大板方案。各机型分别使用 Bambu Studio 02.09.01.70 的官方配置，统一 0.4 mm 喷嘴、Bambu PETG Basic、纹理 PEI、0.20 mm 层高。4 道墙、20% gyroid；有悬垂的零件启用自动树状支撑，外裙边 3 mm。这些是待实测的起始工艺，不代表承重已经验证。

Beds smaller than 256 × 256 mm are unsupported. Profiles cover 256 mm and H-series beds. Each printer uses its own official Bambu Studio 02.09.01.70 preset, a 0.4 mm nozzle, Bambu PETG Basic, Textured PEI, 0.20 mm layers, four walls, 20% gyroid, automatic tree supports where required, and a 3 mm outer brim. These are provisional settings, not a tested load rating.

所有机型统一按稳定着床、强度和打印效率选择方向：薄连接片优先大面平放，镜像件分别检查；比较悬垂高度与接触面积，避免为了减少局部支撑把长件竖高。按零件投影、裙边和支撑间距合盘。各工程的 `layout-validation.json` 记录优化前后的实际切片盘数、时间、总耗材和支撑挤出量；方向搜索与合盘是启发式，不保证全局最优。

All printers use the same layout priorities: stable bed contact, strength and printing efficiency. Thin connectors lie on broad faces, mirrored parts are checked separately, and overhang height and contact area are considered before standing a long part upright. Packing reserves brim and support clearance around projected outlines. Each profile's `layout-validation.json` compares sliced plate count, time, total material and support extrusion before and after the change. Orientation and packing are heuristics, not a proof of a global optimum.

带凸台和导轨的侧板单独比较方向。H2S 单件侧板对比中，低侧放约 3.0 h、3.3 g 支撑；平放约 5.7 h、28.2 g 支撑，因此保留低侧放。以上均为相同工艺的切片估算，未实物验证。

Side panels with rails and protrusions are compared separately. An H2S single-panel comparison estimated 3.0 h and 3.3 g of support in the low side pose, versus 5.7 h and 28.2 g when laid flat, so the low side pose is retained. Both use the same process settings; neither is physically validated.

[配置索引 / Profile index](INDEX.md) · [抽屉修复说明 / Drawer repair](../docs/drawer-repair.md)

两版下载包 / Two download packages:

- `overstack-print-profiles-256.zip`：X2D、P2S 标准板版 / X2D and P2S standard beds.
- `overstack-print-profiles-h-series.zip`：H 系列大板版，内含独立 H2S、H2C、H3C 工程 / Large-bed edition with separate H2S, H2C and H3C projects.

`overstack-print-profiles-preview.zip` 保留为两版合集。 / The preview ZIP contains both editions.

## 打印板尺寸分组 / Build-plate groups

| Group / 分组 | Printer / 切片机型 | Slicing region / 摆盘范围 | Directory / 目录 |
| --- | --- | --- | --- |
| 小于 256 × 256 mm / Smaller beds | A1 mini 等 / e.g. A1 mini | **不支持 / Unsupported** | No project / 不提供工程 |
| 256 mm | X2D | 256 × 256 × 260 mm | `x2d/` |
| 256 mm | P2S | 256 × 256 × 256 mm | `p2s/` |
| H 系列大板 / H-series | H2S | 340 × 320 × 340 mm | `h2s/` |
| H 系列大板 / H-series | H2C | X 25–325, Y 0–320, Z 0–320 mm | `h2c/` |
| H 系列大板 / H-series | H3C | 330 × 320 × 325 mm | `h3c/` |

这里按**用于打印零件的板尺寸**分组，不改变底座收纳的钢板规格：收纳层仍只针对 256 × 256 mm 打印面积级别的钢板。尺寸相近不代表机器配置通用，256 mm 组分别验证 X2D、P2S；其他同尺寸机型仍需重新切片。

These groups describe the beds used to manufacture the parts. They do not change the rack's stored-plate compatibility, which remains the 256 × 256 mm printable-area class. Similar bed sizes do not make printer presets interchangeable: X2D and P2S are validated separately in the 256 mm group.

H2C 保留官方 330 × 320 mm 板配置，但摆盘限制在两喷嘴范围交集（300 × 320 mm，X 从 25 mm 起），并使用较小的 320 mm 高度限制。H2S 使用独立的 340 × 320 mm 配置。范围以当前 Studio 官方预设中的 `printable_area`、`extruder_printable_area`、`extruder_printable_height` 为依据，不修改机器固件参数。

H2C retains its official 330 × 320 mm bed preset, while layouts stay in the intersection of both nozzle regions (300 × 320 mm, starting at X=25) and the smaller 320 mm height limit. H2S uses its own 340 × 320 mm preset. Limits come from Studio's official machine presets.

小于 X2D 的 256 × 256 mm 打印板明确不支持，包含 A1 mini；不提供试件或整层的小板切片配置，也不为其缩放、拆分零件。单抽屉采用新版左右拼接，三抽屉按机型可用范围分别选择方向；旧阻塞状态已由重新检查和切片替代。

Beds smaller than the X2D’s 256 × 256 mm bed, including A1 mini, are unsupported. No specimen or layer profiles are provided for them, and parts are not rescaled or segmented for them. The single drawer uses revised left/right halves; triple-drawer orientations are selected for each printer’s usable area. Fresh checks and slicing replace the former blocked status.

## 组织 / Organization

根目录只放说明和索引；`x2d/`、`p2s/`、`h2s/`、`h2c/`、`h3c/` 内统一使用以下结构，并分别保存 `presets/`。 / The root holds documentation and the index. Each printer directory uses the structure below and its own `presets/`.

- `fit-check/`：先打印试配件。包括孔板、燕尾、板槽、锁片和堆叠脚；只验证局部配合，不验证承重。
- `ams2pro/`：399 mm 宽完整功能层。
- `ams2pro-ht/`：495 mm 宽完整功能层。
- 每个层包包含该层全部零件；五槽层附一对扩展锁片，作为底层时不用。其他层的锁片对应其下方接缝。
- 普通端框为第一轮基线。孔板替换配置、补件包与推荐组合，待基线试装后再发布，不把未验证组合堆进默认工程。

Fit specimens cover the pegboard, dovetail, plate ledges, rear key and stacking foot; see [specimen instructions](../models/fit-check/README.md). Each layer profile is self-contained. Five-slot layers include two optional seam keys; omit them when used as the bottom layer. Other layer keys connect to the layer below. Widths must not be mixed. Plain ends are the initial baseline; pegboard alternatives, spare kits and recommended stacks follow physical validation.

## 状态 / Status

`manifest.json` 是每个包的状态依据：

| Status | Meaning |
| --- | --- |
| `blocked` | 几何/摆放问题未解决；不提供打印工程 / Geometry or placement blocker; no print project |
| `arranged` | 已摆盘，尚未切片 / Arranged only |
| `slice_failed` | 切片失败，不能使用 / Slicing failed; do not print |
| `sliced_not_printed` | 本机全盘切片完成，尚未实际打印 / All plates sliced locally; not physically printed |

所有工程 `makerworld_ready=false`，需完成打印、拆支撑、装配与运动检查，再附实物照片上传 MakerWorld。切片成功不等于实物适配，其他机器/喷嘴/耗材必须重新检查。支撑接触面、首层和接口间隙尤其需要逐盘检查。

All profiles remain `makerworld_ready=false` until print, support-removal, assembly and motion checks are recorded with actual photos. Successful slicing does not prove physical fit or compatibility with other printers, nozzles or filaments.

## 文件 / Files

- `<printer>-04-petg.3mf`（`x2d`、`p2s`、`h2s`、`h2c`、`h3c`）：带设备、材料和工艺设置的 Bambu Studio 项目。与 `models/` 中的装配几何 3MF 分开。
- `manifest.json`：来源文件及 SHA-256、数量、摆放变换、打印条件和验证状态。
- `slice-validation.json`：各机型的实际 G-code 机型、温度、材料及板内范围检查记录。 / Actual G-code metadata and bed-bound checks for every printer.
- `layout-rule-validation.json`：确认已有工程的方向、分盘与位置符合当前规则，保留原始生成来源记录。 / Confirms that orientations, grouping and positions match current rules while preserving generation provenance.
- `layout-validation.json`、`layout-printing-checks.json`：切片对比和当前方向的通用打印检查；不代表实物验证。 / Slice comparisons and manufacturing checks for the current orientations; not physical validation.
- `plate_*.png`、`slice-info.xml`：实际切片产生的预览与耗材/时间估算；不是实拍或实测。

The 3MF is a Bambu Studio project, distinct from the geometry-only assemblies in `models/`. Manifests track source hashes, quantities, transforms and checks. Slice previews and estimates come from Studio, not physical measurements.

## 重建 / Rebuild

以下命令在[源码仓库](https://github.com/overtrue/overstack)根目录运行；ZIP 仅含工程、说明和试件。 / Run these commands from the source checkout; the ZIP contains projects, guides and specimens.

```sh
cad run tools/build_fit_checks.py
cad run tools/build_print_profiles.py --printer x2d --slice
cad run tools/build_print_profiles.py --printer p2s --slice
cad run tools/build_print_profiles.py --printer h2s --slice
cad run tools/build_print_profiles.py --printer h2c --slice
cad run tools/build_print_profiles.py --printer h3c --slice
python3 tools/check_sliced_targets.py
cad run tools/check_print_layout.py --all
cad run tools/check_profile_printing.py
cad run tools/check_print_profiles.py
```

可用 `--only ams2pro/5-slot` 限定范围。生成器从已导出的零件清单读取模型，只旋转和平移，不修改零件几何。使用各机型目录 `presets/` 内固定配置；来源是本机该版本 Studio 的官方机器、PETG 和工艺配置及继承值。升级 Studio 或修改模型后必须重建并重验。

Use `--only ams2pro/5-slot` to limit rebuilding. Parts are only rotated and translated. Each printer's pinned presets come from the installed Studio version's official machine, PETG and process settings with inheritance resolved. Rebuild and revalidate after any geometry or Studio update.

## MakerWorld 发布 / Publishing

按两种宽度分别建立功能模块系列；一个功能模块对应一个完整多盘配置。盘名与物件名沿用零件 ID。新增配置必须有实际工艺/结构区别，不为颜色或同类设备复制相同配置。先发布试配与已实测功能层，最后提供推荐组合。

Organize functional modules by width. Each module has one complete multi-plate baseline profile, with part IDs in plate/object names. Add alternatives only for meaningful geometry or process differences. Publish tested modules first, then tested combinations.

生成下载包：`cad run tools/bundle_print_profiles.py`。只有全盘切片成功的工程会进入预览 ZIP，失败/阻塞项仅保留状态清单。 / Only fully sliced projects enter the preview ZIP; blocked entries retain manifests only.

Studio CLI 空喷嘴列表兼容处理参考 [BambuStudio #12956](https://github.com/bambulab/BambuStudio/issues/12956)。分盘使用 Studio 原生 `--load-assemble-list`，不手工拼接 3MF 网格。

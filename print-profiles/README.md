# 摆盘工程 / Print profiles

当前基线：Bambu Studio 02.09.01.70、X2D 0.4 mm、Bambu PETG Basic、纹理 PEI、0.20 mm 层高。4 道墙、20% gyroid；有悬垂的零件启用自动树状支撑，外裙边 3 mm。这些是待实测的起始工艺，不代表承重已经验证。

Baseline: Bambu Studio 02.09.01.70, X2D 0.4 mm, Bambu PETG Basic, Textured PEI, 0.20 mm layers, four walls, 20% gyroid, automatic tree supports where required, and a 3 mm outer brim. These are provisional settings, not a tested load rating.

[配置索引 / Profile index](INDEX.md)

## 组织 / Organization

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

- `x2d-04-petg.3mf`：带设备、材料和工艺设置的 Bambu Studio 项目。与 `models/` 中的装配几何 3MF 分开。
- `manifest.json`：来源文件及 SHA-256、数量、摆放变换、打印条件和验证状态。
- `plate_*.png`、`slice-info.xml`：实际切片产生的预览与耗材/时间估算；不是实拍或实测。

The 3MF is a Bambu Studio project, distinct from the geometry-only assemblies in `models/`. Manifests track source hashes, quantities, transforms and checks. Slice previews and estimates come from Studio, not physical measurements.

## 重建 / Rebuild

以下命令在[源码仓库](https://github.com/overtrue/stacknest)根目录运行；ZIP 仅含工程、说明和试件。 / Run these commands from the source checkout; the ZIP contains projects, guides and specimens.

```sh
cad run tools/build_fit_checks.py
cad run tools/build_print_profiles.py --slice
cad run tools/check_print_profiles.py
```

可用 `--only ams2pro/5-slot` 限定范围。生成器从已导出的零件清单读取模型，只旋转和平移，不修改零件几何。使用 `presets/` 内固定配置；来源是本机该版本 Studio 的官方 X2D/PETG 配置及继承值。升级 Studio 或修改模型后必须重建并重验。

Use `--only ams2pro/5-slot` to limit rebuilding. Parts are only rotated and translated. Pinned presets come from the installed Studio version's official X2D/PETG settings with inheritance resolved. Rebuild and revalidate after any geometry or Studio update.

## MakerWorld 发布 / Publishing

按两种宽度分别建立功能模块系列；一个功能模块对应一个完整多盘配置。盘名与物件名沿用零件 ID。新增配置必须有实际工艺/结构区别，不为颜色或同类设备复制相同配置。先发布试配与已实测功能层，最后提供推荐组合。

Organize functional modules by width. Each module has one complete multi-plate baseline profile, with part IDs in plate/object names. Add alternatives only for meaningful geometry or process differences. Publish tested modules first, then tested combinations.

生成下载包：`cad run tools/bundle_print_profiles.py`。只有全盘切片成功的工程会进入预览 ZIP，失败/阻塞项仅保留状态清单。 / Only fully sliced projects enter the preview ZIP; blocked entries retain manifests only.

Studio CLI 空喷嘴列表兼容处理参考 [BambuStudio #12956](https://github.com/bambulab/BambuStudio/issues/12956)。分盘使用 Studio 原生 `--load-assemble-list`，不手工拼接 3MF 网格。

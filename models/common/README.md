# 两端通用组件 / Common end components

![Plain and pegboard ends](preview.png)

30 mm / 60 mm 两种高度；相同高度用于 495 mm HT 版和 399 mm 无 HT 版。左右件不可互换。普通版与洞洞板版使用相同定位和连接接口，可以单侧替换。

Two heights, shared by both widths. Left and right parts differ; choose the matching side. Plain and pegboard variants preserve their connection geometry and can be replaced independently.

| Height | Side | Plain | Pegboard |
| --- | --- | --- | --- |
| 30 mm | left | [STL](end_left_30_plain.stl) | [STL](end_left_30_pegboard.stl) |
| 30 mm | right | [STL](end_right_30_plain.stl) | [STL](end_right_30_pegboard.stl) |
| 60 mm | left | [STL](end_left_60_plain.stl) | [STL](end_left_60_pegboard.stl) |
| 60 mm | right | [STL](end_right_60_plain.stl) | [STL](end_right_60_pegboard.stl) |

[Left rear key](lock_left.stl) · [Right rear key](lock_right.stl) · [Fit coupon](pegboard_fit_coupon.stl) · [Pegboard end GLB](pegboard-end.glb)

## SKÅDIS-style hole layout

| Feature | Nominal size |
| --- | --- |
| Vertical slot | 5 × 15 mm, R2.5 |
| Panel thickness | 5 mm |
| Same-row / same-column repeat | 40 mm |
| Alternating row offset | 20 mm horizontally and vertically |
| Clear space behind each slot | At least 20 mm |
| 30 mm end | 6 slots, one row; 7.5 mm top/bottom slot margins |
| 60 mm end | 17 slots, three rows; 2.5 mm top/bottom slot margins |
| Fit coupon | 80 × 80 × 5 mm |

孔阵只适用于各层内部。60 mm 端框可放同列 40 mm 双点配件；30 mm 端框不支持上下双孔挂钩。不要跨层缝安装依赖连续孔距的配件。面板两端保留宽实心边框，洞孔不触及弧形底脚、定位槽、燕尾及后锁片。

Each layer is a separate mounting zone. The tall end includes a 40 mm vertical pair; the low end does not. Do not bridge seams with accessories that require a continuous hole grid. Wide solid end borders retain the corner feet, sockets, dovetails and rear key pockets.

孔位规格依据 [Just Hanging 的配件尺寸说明](https://www.justhangingpegboards.com/pages/pegboard-system)及 [SKÅDIS 风格孔阵生成器的尺寸说明](https://github.com/soloh4cker/skadis_pegboard_studio)。这是按公开名义尺寸独立建模的兼容候选，不是宜家认证。先打印试配板，用实际挂钩检查插入、下挂、卸出和板厚配合；不要直接承诺通配或承重。

Dimensions follow the linked accessory supplier and independent SKÅDIS-style pattern description. Geometry is independently constructed from these dimensions. This is a compatibility candidate, not IKEA certification. Print the coupon and test your hooks for insertion, seating and removal before printing complete ends. No payload rating is established.

## Fitting / 安装

1. Remove devices, empty drawers and take off upper layers. / 移走设备、清空抽屉，拆下上层。
2. Withdraw rear keys and lift the middle out of the end dovetails. / 抽出后锁片，从上方提出中段。
3. Replace the selected end with the matching height and side; plain and pegboard can be mixed. / 换上同高度、同侧洞洞板端框，可左右混用普通版。
4. Lower the middle and upper layers back into place; reinstall rear keys. / 依次放回中段及上层，插回锁片。

Rear keys are removable, not captive. Keep rear access clear. STL coordinates match the wide set; compact assemblies translate right-hand files by −96 mm on X. Reorient each part before slicing; exported geometry is not a sliced print job.

端框是结构件。新洞洞板件已通过 PETG/FDM 通用规则检查（0.4 mm 喷嘴、0.2 mm 层高），但仍需支撑／桥接处理。实物强度、挂钩及设备适配尚未验收。

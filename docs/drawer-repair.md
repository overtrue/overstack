# Drawer repair / 抽屉修复

## HT single drawer / HT 单抽屉

The former front/rear split left about 0.62 mm above part of the dovetail channel and required a tilted print pose near the build-height limit. The revised left/right halves slide together along Y. A continuous spine leaves at least 1.39 mm above the channel, 0.8 mm below it and 2.18 mm at its closed end, as checked on the exported STL. The local interior ridge is 0.8 mm above the otherwise 2 mm floor. The exterior, slide grooves, 180 mm travel and 7 mm lift-out stay unchanged. **Replace both old halves together; old and new halves cannot be mixed.**

原前后拼接在燕尾槽上方局部只剩约 0.62 mm，打印还需要倾斜到接近高度上限。新版改为左右两半沿 Y 方向滑合，连续加强筋经导出 STL 检查确认：槽顶至少 1.39 mm、槽底至少 0.8 mm、封闭端至少 2.18 mm。加强筋在 2 mm 底板内侧凸起 0.8 mm。外廓、滑轨、180 mm 行程与 7 mm 抬出方式不变。**旧两半需成对替换，不可混搭。**

## Triple drawers / 三抽屉

The three drawer STLs are unchanged. At the old 45-degree side-down pose, the generic checker reported a roughly 0.04 mm skin at a sidewall/floor corner. Exported solid probes confirm a continuous 2 mm floor and a full 6 mm sidewall there. A side-down pose rotated 40 degrees on the bed passes the same PETG/FDM check for all three drawers and keeps planar bed contact within a 256 mm build volume. This resolves the orientation-dependent finding without changing storage capacity or weakening the walls.

三只抽屉的 STL 未改动。旧侧放45°方向在侧壁与底板转角处报出约 0.04 mm 薄层；导出实体检查确认该处属于连续 2 mm 底板和 6 mm 侧壁。改为侧放后在板面旋转40°，三只抽屉均通过相同 PETG/FDM 检查，具有平面着床且放得进256 mm打印空间。容量和壁厚不变。

## Verification / 验证

- `tools/verify.py`: 58 closed parts, 1,653 assembly-pair checks / 58个闭合零件、1653对装配检查。
- `tools/verify_drawer_repair.py`: exported joint stock, 161 joining positions, stop/lift-out, solid floors, planar contact, and a deliberately cut roof as a failing control / 导出接缝余料、161个拼接位置、止挡与抬出、实心底板、平面着床，并用挖空槽顶验证检查能发现缺陷。
- `tools/check_printing.py`: all 41 distinct geometries pass PETG/FDM, 0.4 mm nozzle and 0.2 mm layers. Overhang, bridge, gap and knife-edge warnings remain / 41种几何通过通用检查，仍有悬垂、桥接、间隙和尖边提示。
- Printer-specific slicing and archive checks are recorded in [the profile index](https://github.com/overtrue/overstack/blob/main/print-profiles/INDEX.md) / 各机型切片与下载包状态见配置索引。

Physical fit, support removal and load capacity are still unverified. / 实物配合、拆支撑和承重仍未验证。

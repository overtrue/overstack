# HT triple-drawer print checks / HT 三抽屉打印检查

The three drawer STLs are unchanged. At the old 45-degree side-down pose, the generic checker reported a roughly 0.04 mm skin at a sidewall/floor corner. Exported solid probes confirm a continuous 2 mm floor and a full 6 mm sidewall there. A side-down pose rotated 40 degrees on the bed passes the same PETG/FDM check for all three drawers and keeps planar bed contact within a 256 mm build volume. This resolves the orientation-dependent finding without changing storage capacity or weakening the walls.

三只抽屉的 STL 未改动。旧侧放45°方向在侧壁与底板转角处报出约 0.04 mm 薄层；导出实体检查确认该处属于连续 2 mm 底板和 6 mm 侧壁。改为侧放后在板面旋转40°，三只抽屉均通过相同 PETG/FDM 检查，具有平面着床且放得进256 mm打印空间。容量和壁厚不变。

## Verification / 验证

- The full HT assembly contains 48 closed parts. All 1,128 pairs passed the interference check. / HT 总成有 48 个闭合零件，1128 对装配干涉检查通过。
- The exported triple drawers passed the solid-floor, sidewall and planar-contact checks in tools/verify_drawer_repair.py. / 三只抽屉的导出 STL 已检查实心底板、侧壁和平面着床。
- All 35 distinct HT geometries passed the generic PETG/FDM checks at 0.4 mm nozzle and 0.2 mm layers. Overhang, bridge, gap and knife-edge warnings remain. / 35 种几何通过通用 PETG/FDM 检查，仍有悬垂、桥接、间隙和尖边提示。
- Printer-specific slicing and archive checks are recorded in [the profile index](https://github.com/overtrue/overstack/blob/main/print-profiles/INDEX.md) / 各机型切片与下载包状态见配置索引。

Physical fit, support removal and load capacity are still unverified. / 实物配合、拆支撑和承重仍未验证。

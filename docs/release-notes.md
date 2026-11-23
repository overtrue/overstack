按同一套摆盘规则重新检查五种机型的全部 65 个工程：薄连接片平放，长条件避免高立，按轮廓和支撑间距合盘，并比较实际切片时间、耗材和支撑。工程、逐盘预览、对比数据和下载包同步更新；尚未实物验证。 / Rechecked all 65 projects across five printers: flat connecting plates, lower rail orientations and shared plates with support clearance. Compared sliced time, material and support use, and updated projects, plate previews, comparisons and downloads. Physical validation is still pending.

修复 HT 单抽屉拼接槽薄壁：改为左右两半，槽周围加厚，内侧加强筋凸起 0.8 mm；旧前后两半需成对替换。三抽屉模型不变，侧放40°后通过制造检查。41种不同几何均通过 PETG/FDM 检查，装配和运动检查通过；两层按五种机型重新切片，教程和下载包同步更新，尚未实物验证。 / Fixed the HT single-drawer joint with reinforced left/right halves and a local 0.8 mm interior ridge; replace both old front/rear halves. Triple-drawer geometry is unchanged and passes manufacturing checks side-down at 40 degrees. All 41 distinct geometries pass PETG/FDM checks, with assembly and motion checks passed. Both layers are resliced for all five printers, with updated guides and downloads. Physical validation is pending.

Added X2D 0.4 mm / PETG Bambu Studio projects, organized as complete functional layers with named plates, source hashes and slice previews. Small interface specimens cover dovetails, plate ledges, rear keys and stacking feet, alongside the pegboard coupon. Only fully sliced projects enter `overstack-print-profiles-preview.zip`; physical fit and MakerWorld publication remain pending. The former HT single- and triple-drawer blockers are resolved in the latest update above.

Checked both widths and common parts against rebuilt source geometry. Download bundles now check internal documentation links as well as file hashes. Corrected an outdated HT geometry statement in the bilingual documentation.

Replaced the staggered pegboard layout with a straight grid: 12 holes in two rows on 40 mm ends, 18 holes in three rows on 60 mm ends. Every 40/60 mm stacking order keeps the same 20 mm row pitch across seams. Updated the fit coupon, illustrations and downloads. Hook fit, cross-seam loads and full SKÅDIS compatibility remain unverified.

Replaced the 30 mm three-slot layer with a 40 mm five-slot layer in both widths. The five slots use 6 mm pitch with 7 mm top clearance for plates up to 1.5 mm thick; six slots would require at least 46 mm at this spacing. Old 30 mm parts are removed from current downloads. Replace the low end frames and carriers together. Complete stacks now hold 13 plates and measure 309 mm (HT) or 249 mm (AMS-only) high.

Rounded the exposed upper lip ends on both device tops to R3 mm. Updated STL, 3MF and GLB files; all eight tips pass exported-geometry checks and all four revised top parts pass generic PETG/FDM checks. Physical fit and printed surface finish remain untested.

Added a 399 × 287 mm AMS-only set with five/eight-slot plate layers, single/double drawers and a dedicated top. There is no three-drawer option in this width. The 495 mm HT set keeps its existing footprint and joints.

Both widths share the 40/60 mm end frames and rear keys. Pegboard ends use 5 × 15 mm slots in aligned columns, a 5 mm panel, 40 mm horizontal pitch and 20 mm vertical pitch. A fit coupon is included; actual accessory fit and payload remain untested.

Downloads: `overstack-ams2pro+ht.zip` is the original HT set, `overstack-ams2pro.zip` includes the AMS-only set plus common parts, and `overstack-common.zip` contains the common plain/pegboard ends and keys. Open the README inside each package before slicing.

The AMS-only export passes complete assembly and layer-pair checks. All 36 new exported parts pass generic PETG/FDM checks, with support, bridge and knife-edge warnings remaining. X2D/PETG slice coverage is listed in the print-profile index; device-fit and load tests remain pending.

Overstack packages the parametric AMS storage base with 58 numbered parts, six layer assemblies, 12 standalone Chinese/English assembly booklets, exploded illustrations and reproducible source.

All illustrations were rerendered with corrected face normals and soft area lighting. All eight drawers now have 2 mm solid floors. Existing joinery, slide grooves and stops are retained. The model builds without external mesh inputs.

This is a digital prototype, not a print-tested release. Physical fit, device clearance and load capacity remain unverified. Geometry-only 3MF files are not slicer projects. Generic PETG/FDM checks now pass for all 41 distinct geometries; overhang and bridge warnings remain.

Equipment previews / 设备效果图：新增当前紧凑组合和完整组合摆放 AMS 2 Pro、AMS HT 的高清渲染，使用 Engineered Reality 的原尺寸 STEP，并附素材说明。设备源文件不包含在下载包中。 / Added compact and full-stack renders using Engineered Reality’s unscaled STEP assemblies, with asset credits. Device source files are not redistributed.

AMS-only preview / 无 HT 效果图：补充 399 mm 宽紧凑组合摆放 AMS 2 Pro 的高清渲染，并同步中英文 README、素材说明和模型下载包。 / Added an AMS 2 Pro render on the 399 mm compact stack, with bilingual README, asset credits and model download packages updated.

切片方案按两档打包：X2D 256 mm 标准板与 H 系列大板（H2S、H2C 独立工程）。小于 256 × 256 mm 不支持。HT 单抽屉、三抽屉已在本次更新中解除阻塞；尚未实物验证。 / Print profiles are packaged in two editions: X2D 256 mm and H-series, with separate H2S and H2C projects. Smaller beds are unsupported. The latest update resolves the HT single- and triple-drawer blockers; physical validation is pending.

切片目录统一按机型命名，新增 P2S 与 H3C 独立配置。标准板包包含 X2D、P2S，大板包包含 H2S、H2C、H3C。 / Print-profile directories now use printer names. Added separate P2S and H3C profiles: the standard-bed package covers X2D and P2S; the large-bed package covers H2S, H2C and H3C.

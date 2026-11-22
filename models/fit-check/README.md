# 接口试配 / Interface fit specimens

这些小件由 `tools/build_fit_checks.py` 从当前参数模型截取，不是重新估算间隙的替代模型。STL 保留装配坐标；摆盘工程沿用对应正式零件的打印朝向。截取只保留局部接口，不用于承重验证。

These specimens are cropped from the current analytic model. STL files retain assembly coordinates; the print profile follows the corresponding production part's print orientation. They test local fits, not load capacity.

| IDs | 检查 / Check |
| --- | --- |
| FIT02 + FIT03 | 燕尾公母件：从上方装入，检查卡滞和晃动 / Vertical dovetail insertion, binding and play |
| FIT04 | 五槽板托：用实际钢板边缘逐槽检查间隙 / Check each ledge with the actual steel plate edge |
| FIT05 + FIT06 + FIT07 | 上下锁片槽及锁片：两块对齐后从后方插入 / Align upper/lower pockets, insert the key from the rear |
| FIT08 + FIT09 | 弧形底脚和插槽：垂直落座，检查松紧 / Lower the curved foot into its socket |

孔板另用 `models/common/pegboard_fit_coupon.stl` 的 FIT01 试件。不要把锁片向后可拔出误认为自锁；不要敲打接口。完成去毛刺和支撑清理后再记录配合。

Use the separate FIT01 pegboard coupon for hooks. Rear keys are removable, not captive. Deburr and remove supports before judging fit; do not hammer the interfaces together.

[摆盘工程 / Print profiles](../../print-profiles/) · [零件与打印方向 / Parts and orientations](parts.json)

![接口试配盘 / Interface test plate](../../print-profiles/x2d/fit-check/interfaces/plate_1.png)

样件采用左侧接口；不能替代右前插槽和完整层的实际试装。 / Samples use the left-side interfaces; still test the right-front socket and complete layers physically.

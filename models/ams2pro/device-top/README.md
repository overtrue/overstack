# 无 HT 顶件 / AMS-only top

![装配预览 / Assembly preview](preview.png)

只有 AMS 2 Pro 开口，没有 HT 阶梯孔。两片燕尾沿前后方向滑合，再一起落入端框插槽，最后插后锁片。 / One AMS 2 Pro opening, no HT cutout. Slide the two halves together along Y, lower onto the end sockets, then insert the rear keys.

![带编号的爆炸图 / Numbered exploded view](parts-numbered.png)

编号与下表一一对应；左右以面对入口为准。爆炸图只用于辨认零件，不代表装入方向。

Match each callout to its table row. Left/right are viewed from the front. Exploded positions identify parts, not insertion directions.

[GLB](layer-assembly.glb) · [Geometry 3MF](layer-assembly-geometry.3mf) · [BOM](parts.json)

| 编号 / ID | 零件 | STL | X offset |
| --- | --- | --- | ---: |
| [NE01](top_1.stl) | 左顶件 | `top_1.stl` | 0 mm |
| [NE02](top_2.stl) | 右顶件 | `top_2.stl` | 0 mm |
| [NE03](../../common/lock_left.stl) | 左后锁片 | `lock_left.stl` | 0 mm |
| [NE04](../../common/lock_right.stl) | 右后锁片 | `lock_right.stl` | -96 mm |

两端和锁片直接引用通用件。右件保持 HT 版导出坐标，在此装配中向左移动 96 mm；切片前将每件单独落到平台。3MF 是装配几何，不是打印任务。

Common ends and keys are referenced, not duplicated. Right-hand common files retain wide-set coordinates; the assembly moves them left by 96 mm. Reorient and place each part on the bed before slicing. The 3MF is assembly geometry, not a print job.

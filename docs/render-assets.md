# Equipment render assets / 设备渲染素材

The equipment in `showcase-compact.png`, `showcase-full.png` and `showcase-no-ht.png` uses the original, unscaled STEP assemblies by **Engineered Reality**, with rendering materials applied. These are measured community CAD models, not official Bambu Lab CAD or photographs. Spools and build plates are illustrative; the base uses the current exported StackNest parts.

设备效果图使用 **Engineered Reality** 的原始 STEP 装配模型，保持原比例，仅设置渲染材质。这是社区实测模型，不是拓竹官方 CAD 或实拍照片；料盘和打印板为展示模型，底座来自当前 StackNest 导出零件。图中摆放不代表脚垫、通风、开盖净空或承重已实物验证。

| Asset / 素材 | Source / 来源 | Source license / 页面许可 |
| --- | --- | --- |
| AMS 2 Pro Assembly.stp | [Engineered Reality · AMS 2 Pro](https://makerworld.com/en/models/1283144-bambu-ams-2-pro-cad-model-stp-file) | CC BY-NC-SA |
| AMS HT.stp | [Engineered Reality · AMS HT](https://makerworld.com/en/models/1551756-bambu-ams-ht-cad-model-stp-file) | MakerWorld Standard Digital File License |

The original device files and converted meshes are local rendering inputs only, and are not included in the repository or model download packages. The repository's [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) license does not grant rights to these third-party device assets. Refer to the linked source pages for their terms.

设备源文件和转换网格仅作为本地渲染输入，不放入仓库或模型下载包。仓库的 [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/deed.zh) 许可不覆盖这些第三方设备素材，使用条件以来源页面为准。

## Rebuild / 重建

Download the original STEP files using **Download STL/CAD Files**, not the scaled print profile. Save them as `output/device-reference/ams-2-pro.stp` and `output/device-reference/ams-ht.stp`, then run from the repository root:

下载原尺寸 STEP（不要使用缩小版打印配置），按以下路径保存后，在仓库根目录运行：

```sh
cad step export output/device-reference/ams-2-pro.stp output/device-reference/ams-2-pro.glb --tolerance 0.05 --angle 8
cad step export output/device-reference/ams-ht.stp output/device-reference/ams-ht.glb --tolerance 0.05 --angle 8
cad run tools/showcase_scene.py
cad run tools/render_showcase.py --compact --final
cad run tools/render_showcase.py --final
cad run tools/showcase_scene.py --no-ht
cad run tools/render_showcase.py --no-ht --final
```

The compact base uses the 40 mm five-slot layer, 60 mm double-drawer layer and device top (129 mm overall). The full base uses all five storage layers and the top (309 mm overall). Device STEP envelopes are 371 × 281 × 226.5 mm and 114.1 × 282.5 × 245.8 mm; they are not rescaled to the nominal product specifications.

紧凑组合为五槽板层、双抽屉层和顶件，总高 129 mm；完整组合包含五个收纳层和顶件，总高 309 mm。设备 STEP 外廓分别为 371 × 281 × 226.5 mm、114.1 × 282.5 × 245.8 mm，保留原模型尺寸，不强行缩放到产品标称值。

## Source checksums / 源文件校验

```text
fbdf013fca02b9bcbe12bc3d0b5e8defd0f9c902144ceae2208dcd14f6288c9d  ams-2-pro.stp
372a369c8f6470effdb5d8d14a66df865b62fa35e0c01ee4feed94fde89700f1  ams-ht.stp
```

The AMS-only scene uses its own 399 mm-wide five-slot layer, double-drawer layer and top (129 mm overall); the AMS 2 Pro is centred on the single opening. / 无 HT 场景使用独立的 399 mm 宽五槽板层、双抽屉层和顶件，总高 129 mm，AMS 2 Pro 居中摆放于单设备开口上。

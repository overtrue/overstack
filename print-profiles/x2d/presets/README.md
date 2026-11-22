# Pinned baseline presets

Resolved from the official presets bundled with Bambu Studio **02.09.01.70** on macOS:

- `BBL/machine/Bambu Lab X2D 0.4 nozzle.json`
- `BBL/process/0.20mm Standard @BBL X2D.json`
- `BBL/filament/Bambu PETG Basic @BBL X2D 0.4 nozzle.json`

Inheritance is flattened for CLI use. No account or printer-access data is included. The generator explicitly overrides bed type, walls, infill, support and brim settings; nozzle temperatures and machine G-code come from these official presets. These settings require physical validation for StackNest.

固定基线来自上述版本内置官方配置，已展开继承，不含账号或设备访问数据。温度和机器 G-code 使用官方值；生成器显式设置板型、墙数、填充、支撑和裙边。升级版本时重新验证，不能据此直接承诺其他机型兼容。

Upstream: [Bambu Studio profiles](https://github.com/bambulab/BambuStudio/tree/master/resources/profiles/BBL).

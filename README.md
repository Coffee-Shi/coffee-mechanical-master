# Coffee机械大师：表面粗糙度选择

这是一个面向机械设计与制图场景的 Codex Skill。用户可以用自然语言描述表面的用途、配合、运动、密封和加工条件，也可以上传机械图纸或局部截图；Skill 会识别目标表面并推荐合适的 `Ra` 表面粗糙度。

## 能做什么

- 根据非配合面、定位面、运动配合面、轴承面、密封面、液压孔、摩擦面和测量面等功能推荐 `Ra`。
- 识别图纸中已有的粗糙度符号、配合代号、公差和引出位置。
- 区分“读取图上已有标注”和“为尚未标注的表面重新选值”。
- 为推荐值提供典型加工方法、判断依据、关键假设和需要确认的问题。
- 在可用时借助 `cad-viewer` 查看 DXF、STEP/STP、STL、3MF 等文件中的目标几何表面。

## 安装

在 Codex 中直接提出：

```text
从 https://github.com/Coffee-Shi/coffee-surface-roughness-selector
安装 skills/coffee-surface-roughness-selector
```

也可以下载仓库后，将以下目录复制到本机 Codex Skills 目录：

```text
skills/coffee-surface-roughness-selector
```

默认安装位置为：

```text
~/.codex/skills/coffee-surface-roughness-selector
```

## 使用方式

可显式调用：

```text
使用 $coffee-surface-roughness-selector。
这个轴颈与滚动轴承内圈配合，直径 25 mm，中速旋转，推荐什么粗糙度？
```

也可以直接描述问题：

```text
这个液压阀芯在阀体孔内往复运动，要求低泄漏，阀芯外圆和阀孔内表面应该标多少 Ra？
```

图纸场景示例：

```text
请分析我上传的机械图纸。目标是 M4 孔一侧的右端面，告诉我推荐标注的粗糙度，而不是读取其他表面已有的标注。
```

## 输出内容

典型回答包含：

1. 首选粗糙度，例如 `Ra 6.3 μm`。
2. 条件变化时的相邻备选值。
3. 表面功能与选值理由。
4. 建议加工方法。
5. 从文字或图纸中识别出的依据与假设。
6. 会改变推荐结果的少量确认问题。

## 选型原则

- 优先选择能够满足功能要求的最大 `Ra`，避免无依据的过度精加工。
- 粗糙度不能替代尺寸公差、圆度、圆柱度、平面度、同轴度或波纹度。
- 密封和摩擦表面还要考虑纹理方向、润滑、材料、硬度、涂层和配套件要求。
- 不使用固定比例随意换算 `Ra` 与 `Rz`。
- 轴承、密封、液压、量规、高速摩擦和安全关键表面应以现行标准、供应商规范和最终图纸为准。

## 数据基础

Skill 内置了从 `Ra 100 μm` 到 `Ra 0.0063 μm` 的 14 档经验选型资料，并针对源资料中的重复示例和旧式轴承等级增加了防误用提示。原始 PDF 不包含在仓库中。

这些数据用于工程初选，不构成强制性标准或最终验收依据。

## 仓库结构

```text
skills/coffee-surface-roughness-selector/
├── SKILL.md
├── agents/openai.yaml
├── references/
│   ├── drawing-analysis.md
│   ├── roughness-catalog.json
│   └── selection-guide.md
└── scripts/recommend_ra.py
```

`recommend_ra.py` 是确定性查表辅助脚本。它不直接理解任意自然语言，而是由 Codex 根据实际工况选择对应场景。

## 本地验证

运行查表自测：

```bash
python skills/coffee-surface-roughness-selector/scripts/recommend_ra.py --self-test
```

列出支持的确定性查表场景：

```bash
python skills/coffee-surface-roughness-selector/scripts/recommend_ra.py --list-scenarios
```

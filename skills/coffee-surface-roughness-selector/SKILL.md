---
name: coffee-surface-roughness-selector
description: Recommend an Ra surface-roughness value for a mechanical surface from its stated use or an engineering drawing/image, including fits, bearings, seals, friction, fatigue, measuring faces, and feasible finishing methods. Use when the user asks what roughness a particular surface should have or wants an existing roughness callout interpreted. Do not treat the result as overriding the governing drawing, contract, or component-supplier requirement.
---

# Coffee机械大师-表面粗糙度选择

给出一个首选 `Ra` 值（单位 `μm`），并说明功能依据、可行加工方法、关键假设和需要核实的条件。优先选择能够满足功能的最大 `Ra`，避免没有依据的过度精加工。

## 路由

- 只有文字描述时，读取 [references/selection-guide.md](references/selection-guide.md)，按表面功能分类。
- 输入包含图纸、照片、扫描件、PDF 或 CAD 文件时，同时读取 [references/drawing-analysis.md](references/drawing-analysis.md)。
- 需要核对原始 14 档数据、应用示例或旧等级表述时，读取 [references/roughness-catalog.json](references/roughness-catalog.json)。
- 已能把工况归入标准场景时，可运行 `scripts/recommend_ra.py --scenario <场景>`；先用 `--list-scenarios` 查看场景名。脚本只做确定性查表，不能替代工程判断。

## 工作规则

1. 先区分任务是“读取图上已有标注”还是“为未标注表面选择新值”。已有标注不得被静默改写。
2. 明确表面的零件、位置、是否运动接触、配合精度、密封方式、载荷/疲劳、润滑、材料、热处理、加工路线和尺寸范围。用户没有提供全部信息时，先基于明确事实给出暂定推荐，再只追问会改变档位的条件。
3. 多项功能并存时，以最严格的功能为主，但检查该精度是否真的由粗糙度控制。尺寸、形位、公差、波纹度、纹理方向和材料缺陷不能用更小的 Ra 代替。
4. 从参考档位中选择首选值。除非有明确功能或标准依据，不跳过多个等级追求镜面。
5. 对轴承、密封、液压、量规、高速摩擦或安全关键表面，要求用户核对制造标准、配套件供应商规范和最终图纸。

## 回答格式

按以下顺序简洁回答：

- **首选粗糙度：** `Ra X μm`
- **可接受备选：** 仅在假设变化会导致相邻档位时给出
- **为什么：** 说明表面功能和对应档位，不只复述零件名称
- **建议工艺：** 给出与该档位相容的典型工艺，不承诺单靠工艺名称即可达标
- **依据与假设：** 列出从文字或图纸识别出的证据
- **还需确认：** 最多提出 1-3 个会改变推荐的问题；信息充分时省略

如果证据不足，标注“暂定”和置信度。不要用未经确认的 `Ra≈Rz/4`、`Ra≈Rz/7` 等经验式换算；`Ra` 与 `Rz` 的关系依工艺和轮廓而变。

## 边界

参考资料来自用户提供的《表面粗糙度的应用》两页表格，适合作为经验选型起点，不是现行标准全文。源表包含重复示例和 E/D/G 级滚动轴承等旧式表述；遇到这类条件必须说明并要求核对现行轴承或企业标准。

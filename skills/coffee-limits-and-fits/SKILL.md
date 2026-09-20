---
name: coffee-limits-and-fits
description: Use when a user describes or shows a mechanical hole-and-shaft fit and needs a knowledge-base-only recommendation for tolerance grade, fit designation, machining route, compliance check, and relative machining cost. Covers clearance, transition, and interference fits for basic sizes through 3150 mm using the bundled GB/T and JIS-derived references.
---

# Coffee机械大师：极限与配合

仅使用本 Skill 的 `references/` 与 `references/data/` 作答。不要以模型常识、网络检索或经验值补齐缺失的配合、偏差、工艺或成本结论。

## 执行流程

1. 从语言、图纸或图片中提取：基本尺寸、孔/轴表面、相对运动、转速与载荷、润滑、温度、定心要求、拆装频率、转矩是否由过盈传递、材料和现有工艺。
2. 对图纸先识别尺寸和已有标注，再按本知识库决策。不清晰的数字不得猜测，要求用户确认。
3. 若缺少会改变配合类型的关键条件，先问最少数量的澄清问题；不要过早给出唯一结论。
4. 读取 [decision-workflow.md](references/decision-workflow.md) 判定间隙、过渡或过盈配合，再用 [preferred-fits.md](references/preferred-fits.md) 选取有明确应用证据的优先配合。用 [grade-applications.md](references/grade-applications.md) 核对精度档，用 [tolerance-zones.md](references/tolerance-zones.md) 检查大于 500 mm 的公差带是否在该尺寸范围的常用列表内。
5. 有基本尺寸时，运行 `python scripts/fit_lookup.py --diameter-mm <尺寸> --scene "<场景>"`，核对孔、轴的 IT 公差宽度。脚本仅在知识库命中时返回建议。
6. 读取 [machining-and-cost.md](references/machining-and-cost.md)，给出能达到目标 IT 等级的工艺路线、验收方式和相对成本。成本只能表述为表中的相对倍率 1、2.5 或 5，不得换算为货币报价。
7. 若知识库没有匹配场景、尺寸超出表格范围，或证据相互冲突且无法由已知条件消解，只回复：

> 未在知识库中找到合适的公差配合，是否让人工智能自己思考。

用户明确同意后，才可在后续回合使用知识库以外的工程推理，并清楚标注为“AI 扩展推理，非本知识库结论”。

## 回答格式

正常命中时依次输出：

- `推荐标注`：例如 `⌀20 H7/g6`，并说明基孔制或基轴制。
- `公差宽度`：孔和轴各自的 IT 宽度，同时给出 μm 和 mm。不要把公差宽度误当作上、下偏差。
- `选择依据`：对应知识库中的配合特性和应用场景。
- `加工路线`：分孔、轴说明粗加工到终加工，只列知识库明示能达到目标 IT 的方法。
- `符合性检查`：按图样给定的上、下极限验收；如知识库只有 IT 宽度而没有该公差带的数值偏差，明说不能据此编造极限尺寸。
- `成本`：报告相对成本档位及更经济的可达到备选工艺，说明表中倍率是比较值。
- `知识库依据`：列出用到的本地参考文件和来源页。

## 边界

- 标准公差数值覆盖基本尺寸至 3150 mm；IT01、IT0 仅覆盖至 500 mm。
- 本知识库是指定历史版本的冻结摘录，不宣称等同于最新标准全文。
- 表中的 IT 数值是公差宽度；只有同时有基本偏差数值时，才能计算孔、轴的数值极限尺寸。

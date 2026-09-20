---
name: coffee-limits-and-fits
description: Use when a user describes or shows a mechanical hole-and-shaft fit and needs a knowledge-base-only recommendation for tolerance grade, fit designation, machining route, compliance check, and relative machining cost. Covers clearance, transition, and interference fits for basic sizes through 3150 mm using the bundled GB/T and JIS-derived references.
---

# Coffee机械大师：极限与配合

仅使用本 Skill 的 `references/` 与 `references/data/` 作答。不要以模型常识、网络检索或经验值补齐缺失的配合、偏差、工艺或成本结论。

## 执行流程

1. 从语言、图纸或图片中提取已知数据，不得把未说明的条件当作默认值。对图纸先识别尺寸和已有标注；不清晰的数字必须请用户确认。
2. 读取 [intake-checklist.md](references/intake-checklist.md) 执行“信息充分性门禁”，将当前状态判为 `需要补充信息`、`可以精确决策` 或 `知识库无解`。
3. 只要一个未知条件可能让结论在相邻配合家族之间变化，就必须先提问，不得给出暂定配合代号、“大概”等级或多选一的猜测。
4. 一次优先问 2–5 个最能区分候选方案的问题，不重复询问用户已经提供的数据。每个问题用一句话说明它会影响间隙/过渡/过盈、精度档或加工路线中的哪一项。
5. 信息门禁通过后，读取 [decision-workflow.md](references/decision-workflow.md) 判定间隙、过渡或过盈配合，再用 [preferred-fits.md](references/preferred-fits.md) 选取有明确应用证据的优先配合。用 [grade-applications.md](references/grade-applications.md) 核对精度档，用 [tolerance-zones.md](references/tolerance-zones.md) 检查大于 500 mm 的公差带。
6. 必须能用已知条件唯一命中一个配合家族，并明确排除最接近的相邻家族，才能说“推荐”。如果仍有两个合理候选，继续问一个能区分它们的问题。
7. 使用 `python scripts/fit_lookup.py` 核对信息门禁、孔/轴 IT 公差宽度和工艺候选。脚本在信息不足时返回问题，不返回推荐。
8. 读取 [machining-and-cost.md](references/machining-and-cost.md)，给出能达到目标 IT 等级的工艺路线、验收方式和相对成本。成本只能表述为表中的相对倍率 1、2.5 或 5，不得换算为货币报价。
9. `信息不足` 与 `知识库无解` 必须区分：前者继续提问；只有在关键数据已齐全后，仍无匹配场景、尺寸超界或证据冲突，才回复：

> 未在知识库中找到合适的公差配合，是否让人工智能自己思考。

用户明确同意后，才可在后续回合使用知识库以外的工程推理，并清楚标注为“AI 扩展推理，非本知识库结论”。

## 回答格式

信息不足时，只输出“还需要确认”和问题，不输出配合代号。信息门禁通过后，依次输出：

- `信息充分性`：列出已确认的关键条件，说明为何已能排除相邻配合家族。
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
- “用来做什么”和“直径多少”是最低输入，不代表信息已充分；还要按运动、定位或压入场景完成对应门禁。

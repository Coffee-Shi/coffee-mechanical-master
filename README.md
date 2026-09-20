# Coffee机械大师

## 总体介绍

**Coffee机械大师**是一个利用 AI 辅助机械设计、机械制图与制造决策的可扩展 Codex Skill。用户可以直接描述零件、工况和设计目标，也可以上传图纸或局部截图；AI 会理解问题、识别目标表面、检查信息是否充分，并调用对应的专业小 Skill 给出有依据的工程建议。

它使用统一入口 `$coffee-mechanical-master` 管理不同机械专业能力。当前版本包含 2 个小 Skill，后续可继续加入材料选择、形位公差、机械制图检查、加工工艺等新能力，而不需要为每项能力单独安装。

## 能力介绍

- 理解自然语言描述的零件用途、装配关系、运动方式和制造要求；
- 分析机械图纸、局部截图和扫描件，定位用户指定的尺寸或表面；
- 信息不足时主动询问会改变结论的关键条件，不把未知条件当作默认值；
- 自动选择并调用对应的小 Skill，也能联合多个小 Skill 分析同一个机械问题；
- 输出推荐结果、选择依据、加工路线、符合性说明和知识库来源；
- 对超出知识库范围的情况明确说明，不用未经确认的经验值冒充确定结论；
- 支持通过 GitHub 统一维护，并自动更新本机 Codex 中安装的 Skill。

## 包含的小 Skill

### 1. 表面粗糙度选择

根据表面的实际用途、运动接触、配合精度、密封、摩擦、疲劳、润滑和加工条件推荐 `Ra`。可以区分“读取图纸已有标注”和“为未标注表面选择新值”，并给出相容的典型加工方法和需要确认的条件。

适用示例包括轴颈、轴承配合面、液压阀芯、缸孔、密封面、定位面、测量面和普通非配合面。

详细查看：[工作流说明](https://github.com/Coffee-Shi/coffee-mechanical-master/blob/main/references/surface-roughness/workflow.md) · [选型指南](https://github.com/Coffee-Shi/coffee-mechanical-master/blob/main/references/surface-roughness/selection-guide.md) · [图纸分析](https://github.com/Coffee-Shi/coffee-mechanical-master/blob/main/references/surface-roughness/drawing-analysis.md) · [粗糙度数据](https://github.com/Coffee-Shi/coffee-mechanical-master/blob/main/references/surface-roughness/roughness-catalog.json) · [查表脚本](https://github.com/Coffee-Shi/coffee-mechanical-master/blob/main/scripts/roughness/recommend_ra.py)

### 2. 极限与配合

根据孔轴基本尺寸、相对运动、速度、载荷、润滑、温度、定心精度、拆装要求、材料和装配方式，选择公差等级、公差带以及间隙、过渡或过盈配合，并提供知识库支持的加工路线和相对成本。

资料不充分时只提出澄清问题；只有能够唯一确定配合家族并排除相邻候选时，才输出推荐标注。

详细查看：[工作流说明](https://github.com/Coffee-Shi/coffee-mechanical-master/blob/main/references/limits-and-fits/workflow.md) · [信息门禁](https://github.com/Coffee-Shi/coffee-mechanical-master/blob/main/references/limits-and-fits/intake-checklist.md) · [优先配合](https://github.com/Coffee-Shi/coffee-mechanical-master/blob/main/references/limits-and-fits/preferred-fits.md) · [公差数据](https://github.com/Coffee-Shi/coffee-mechanical-master/tree/main/references/limits-and-fits/data) · [查表脚本](https://github.com/Coffee-Shi/coffee-mechanical-master/blob/main/scripts/fits/fit_lookup.py)

当同一个配合面同时需要公差和粗糙度时，Coffee机械大师会先确定配合功能和公差方案，再调用表面粗糙度小 Skill 选择相容的 `Ra`。

## 安装与自动更新

本仓库根目录就是 Skill。为保留自动更新能力，应使用 Git 克隆，而不是下载 ZIP：

```powershell
git clone https://github.com/Coffee-Shi/coffee-mechanical-master.git `
  "$HOME/.codex/skills/coffee-mechanical-master"

powershell -ExecutionPolicy Bypass -File `
  "$HOME/.codex/skills/coffee-mechanical-master/scripts/register-auto-update.ps1"
```

注册脚本创建当前用户计划任务 `CoffeeMechanicalMasterSkillAutoUpdate`，默认每天 09:00 检查一次 `origin/main`。如需更换时间，可向注册脚本传入 `-At "HH:mm"`。只有满足以下条件才更新：

1. 本地没有已跟踪改动；
2. 远端是当前提交的快进版本；
3. 新版本通过 Skill 结构校验、粗糙度自测和公差配合测试。

日志位于：

```text
~/.codex/logs/coffee-mechanical-master-update.log
```

Codex 会自动检测本地 Skill 文件变化；若界面没有及时刷新，重启 Codex。

粗糙度图纸、截图或 CAD 文件查看需要提前安装 [text-to-cad](https://github.com/earthtojake/text-to-cad)。Coffee机械大师会借助它的相关查看能力辅助定位目标表面；其中 `cad-viewer` 主要用于 DXF、STEP/STP、STL、3MF 等 CAD 几何，JPG、PNG 和扫描 PDF 仍由 Codex 视觉能力识别。

取消自动更新：

```powershell
powershell -ExecutionPolicy Bypass -File `
  "$HOME/.codex/skills/coffee-mechanical-master/scripts/unregister-auto-update.ps1"
```

## 使用案例

### 案例 1：选择表面粗糙度

```text
$coffee-mechanical-master
这个轴颈与滚动轴承内圈配合，直径 25 mm，中速旋转、油润滑，
请推荐轴颈表面粗糙度和加工方法。
```

### 案例 2：选择公差等级和配合

```text
$coffee-mechanical-master
直径 20 mm 的阀芯在阀体孔内低速往复运动，油润滑、轻载，
圆柱面主要负责精密导向，密封由密封圈承担。请推荐孔轴配合和加工路线。
```

### 案例 3：同时选择配合与粗糙度

```text
$coffee-mechanical-master 这个液压阀芯直径 20 mm，在阀体孔内低速往复，
请同时推荐孔轴配合、两表面的粗糙度和加工方法。
```

### 案例 4：分析图纸中的指定表面

```text
$coffee-mechanical-master
请分析我上传的机械图纸。目标是 M4 孔所在一侧的最右端外表面，
先确认你识别的具体表面，再推荐粗糙度；不要读取其他表面的已有标注。
```

Coffee机械大师提供的是知识库支持的工程辅助结论，不替代现行标准全文、供应商要求、企业规范、强度校核或最终批准图纸。

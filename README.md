# Coffee机械大师

把“表面粗糙度选择”和“极限与配合”合并为一个 Codex Skill：`coffee-mechanical-master`。界面显示名为 **Coffee机械大师**。

## 能力

- 根据表面用途、运动、密封、配合与图纸信息选择 `Ra`；
- 选择孔轴公差等级、公差带及间隙/过渡/过盈配合；
- 给出知识库支持的加工路线、符合性说明和相对成本；
- 同一配合面需要公差与粗糙度时，先做配合决策，再给出相容的粗糙度；
- 资料不足时先提问，不把未确认条件当作默认值。

知识库分别来自原公开仓库：

- [coffee-surface-roughness-selector](https://github.com/Coffee-Shi/coffee-surface-roughness-selector)
- [coffee-limits-and-fits](https://github.com/Coffee-Shi/coffee-limits-and-fits)

旧仓库保留用于历史追溯；后续功能更新以本仓库为准。

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

取消自动更新：

```powershell
powershell -ExecutionPolicy Bypass -File `
  "$HOME/.codex/skills/coffee-mechanical-master/scripts/unregister-auto-update.ps1"
```

## 使用

```text
$coffee-mechanical-master 这个液压阀芯直径 20 mm，在阀体孔内低速往复，
请同时推荐孔轴配合、两表面的粗糙度和加工方法。
```

也可直接上传机械图纸或局部截图。对于 DXF、STEP/STP、STL、3MF 等 CAD 文件，建议预先安装 `text-to-cad` 中的 `cad-viewer`；普通 JPG、PNG 和扫描 PDF 使用 Codex 视觉能力分析。

## 本地验证

```powershell
py -3 -X utf8 "$PWD/scripts/roughness/recommend_ra.py" --self-test
py -3 -X utf8 -m unittest discover -s "$PWD/scripts/fits" -p "test_*.py"
```

资料用于工程初选，不替代现行标准全文、供应商要求、企业规范或最终批准图纸。

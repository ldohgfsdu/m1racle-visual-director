# M1racle Visual Director — Engraving Edition

**固定风格 · 指定调用 · 直接出图**。本 Skill 专门生成19世纪**钢版雕刻 × 纸币凹版印刷 × Guilloché 防伪曲线**风格，不是通用的“自动选画风”工具。

## 一句话安装

把仓库链接发给支持安装 Skill 的 Agent：

> 帮我安装这个 Skill：https://github.com/ldohgfsdu/m1racle-visual-director

或使用支持多 Agent 的安装器：

```bash
npx skills add https://github.com/ldohgfsdu/m1racle-visual-director -g -y
```

没有 Node.js 时可克隆仓库并使用 `python scripts/install.py --agent codebuddy --scope global`（根据实际 Agent 调整）。安装目录名称必须为 `m1racle-visual-director`。

## 使用示例

**直接文字生图**

> 使用 $m1racle-visual-director，生成一张古代中国山城，16:9，直接出图。

**上传图片转雕刻**

> 使用 $m1racle-visual-director，把这张照片转成蓝色纸币钢版雕刻，保留主体与构图，直接出图。

**只借鉴参考图风格**

> 使用 $m1racle-visual-director，只参考图1的细线和 Guilloché 曲线，画一座新的未来城市，不复制原图建筑。

**黑白版画变体**

> 使用 $m1racle-visual-director，生成古希腊神庙的黑白钢版雕刻。

普通“生成图片”或者“帮我选画风”请求**不应**自动调用此 Skill；宿主 Agent 的真实加载行为需在各自平台测试。

## 特性与边界

- 只支持**固定雕刻风格族**，可选蓝色彩墨或古典黑白，不会自动切水墨/摄影/3D。
- 支持文字生图和参考图再创作、原图改绘、局部编辑与多图合成。
- 显式要求出图且工具可用时**直接生成**，不先做长篇规划，也不强制用户再次说“生成”。
- 不自带图像模型或额度。真实图像工具若要求费用/权限确认，必须遵守。
- 由工具能力决定输入图支持程度、输出分辨率与质量。

## 检查

```bash
python scripts/validate_skill.py
python scripts/test_install.py
```

静态通过不等于端到端生图验收通过。参见 [使用指南](使用指南.md)、[雕刻风格规范](references/banknote-engraving.md)、[24 条案例](evals/cases.json)。

v1.2.0
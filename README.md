# M1racle Visual Director — Engraving Edition

## 在线画廊（手机可直接打开）

真正的浏览器画廊网址（须先在 GitHub 仓库 Settings → Pages 启用 **Deploy from a branch / main / (root)**）：

**https://ldohgfsdu.github.io/m1racle-visual-director/**

注意：GitHub 的 `blob/main/gallery/index.html` 只是代码查看地址，无法预览交互页面。启用 Pages 后无需下载、解压或克隆；保留本地 `gallery/index.html` 供离线使用。本站仅展示两张矢量线条结构示意，不是高精度模型出图成品。


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

v1.3.2

## 离线画廊与参考图规则

- [打开雕刻风格画廊](gallery/index.html)：蓝色纸币凹版、黑白古典钢版两个同族变体，浏览器本地打开 `gallery/index.html`，离线可用。
- 预览 SVG **只是结构示意**，不是经过真实生图测试的高保真样张，不会自动作为模型参考图传入。
- [参考图与模型使用策略](references/reference-selection.md)：保持内容源与风格源分离；模型未经标定时文字优先，不捏造成功率。

## 更新

向有终端权限的 Agent 发送：**“帮我安装或更新这个 Skill：https://github.com/ldohgfsdu/m1racle-visual-director，验收安装路径和离线画廊。”**

- 使用 Skills CLI 时让 Agent 检查当前安装器的更新/覆盖参数，不能假定重新安装一定更新。
- Python 后备流程：在**最新仓库克隆副本**运行 `python scripts/install.py --agent codebuddy --scope global --force`；Agent 名和活动扫描目录应以实际运行环境为准。
- 验证：`python scripts/validate_skill.py`、`python scripts/verify_gallery.py`、`python scripts/test_install.py`，并检查真实 Agent 能指定调用。
- 如果需要桌面画廊快捷方式，可以告诉 Agent：**“帮我在桌面创建当前已安装 Skill 画廊的快捷方式”**。仅针对本机真实路径创建，不使用硬编码作者路径。

# M1racle Visual Director — Engraving Edition

## 在线画廊（手机可直接打开）

真正的浏览器画廊网址（须先在 GitHub 仓库 Settings → Pages 启用 **Deploy from a branch / main / (root)**）：

**https://ldohgfsdu.github.io/m1racle-visual-director/**

注意：GitHub 的 `blob/main/gallery/index.html` 只是代码查看地址，无法预览交互页面。启用 Pages 后无需下载、解压或克隆；保留本地 `gallery/index.html` 供离线使用。本站仅展示两张矢量线条结构示意，不是高精度模型出图成品。


**固定风格 · 指定调用 · 直接出图**。本 Skill 专门生成19世纪**钢版雕刻 × 纸币凹版印刷 × Guilloché 防伪曲线**风格，不是通用的“自动选画风”工具。

## 安装或更新（严格快装）

把本仓库链接发给 Agent，直接说：

> 帮我安装或更新这个 Skill：https://github.com/ldohgfsdu/m1racle-visual-director 。严格遵守仓库的 [INSTALL.md](INSTALL.md)；不要 `git clone`，不要超过规定网络等待预算，不要重复重试。现有有效安装无需重新下载。

**执行入口：** 官方 `scripts/quick_install.py`。优先官方下载 GitHub ZIP；有可达的可信 HTTP(S) 代理则优先使用已配置的环境代理。第三方下载镜像仅在用户明确同意后尝试，且先验证 ZIP 可用。支持 `--mirror-url`、`--archive-file`、`--proxy`。不能从官方源取得安装器或包时，应及时报错停止，不得自动回退到 `git clone`。

**跨 Agent 支持：** Codex、Claude Code、OpenCode、Cursor、CodeBuddy、WorkBuddy、Gemini CLI、GitHub Copilot；真实安装路径以当前宿主扫描目录为准。**在云沙箱安装不等于在手机 App「我的技能」注册。**

本地执行示例（前提：已经从可信来源取得 `quick_install.py`）：

```bash
python quick_install.py --agent codebuddy --force --timeout 8 --max-seconds 24
```

不联网的本地验证：`python quick_install.py --agent codebuddy --doctor`。如果已经有可靠的本地 ZIP：`python quick_install.py --agent codebuddy --force --archive-file /path/to/skill.zip`。

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

v1.4.1

## 离线画廊与参考图规则

- [打开雕刻风格画廊](gallery/index.html)：蓝色纸币凹版、黑白古典钢版两个同族变体，浏览器本地打开 `gallery/index.html`，离线可用。
- 预览 SVG **只是结构示意**，不是经过真实生图测试的高保真样张，不会自动作为模型参考图传入。
- [参考图与模型使用策略](references/reference-selection.md)：保持内容源与风格源分离；模型未经标定时文字优先，不捏造成功率。

## 更新验收

遵守 [INSTALL.md](INSTALL.md) 的单一路径：用户请求更新时重新下载短时 ZIP 并使用 `--force`，验收实际安装目录和画廊链接。禁止回退到长时间 Git 克隆；开发测试 `test_install.py` / `test_quick_install.py` 仅在 CI 运行。

如需桌面画廊快捷方式，请 Agent 使用真实安装目录下的 `gallery/index.html`，不得硬编码设备路径或把 GitHub blob 源码页当作网页。

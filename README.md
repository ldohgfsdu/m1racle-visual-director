# M1racle Visual Director

智能视觉导演：用于 AI Agent 的图片生成与参考图再创作决策 Skill。

## 功能

- 自动判断：文字生图 / 参考图创作 / 整图风格转换 / 局部编辑 / 多图合成
- 解析原图职责：主体、构图、风格、配色、底图
- 按内容、用途和保真约束，从 17 类风格候选中选择合适画风
- 内置 **Guilloché 防伪曲线 + 钢版纸币雕刻** 专项模板
- 提示词组装、图片质量检查、24 个行为测试样例

## 安装

把此仓库克隆到 Agent 的 skills 目录，目录名称要与 `SKILL.md` 的 `name` 一致：`visual-art-director`。

```bash
git clone https://github.com/ldohgfsdu/m1racle-visual-director.git ~/.agents/skills/visual-art-director
```

**Claude Code：** 克隆到 `~/.claude/skills/visual-art-director`。

**Windows：** 将仓库下载后解压，重命名文件夹为 `visual-art-director`，并放入 `C:\Users\<username>\.agents\skills\`（或 Claude Code 的 `.claude\skills\`）。

详细安装说明见 [使用指南](使用指南.md)。

## 使用示例

> 使用 visual-art-director，给古代山城生成 16:9 插图，没有参考图，自动选择视觉风格并直接生图。

> 使用 visual-art-director，参考上传图片的画风绘制全新场景，不要复刻原图地标。

> 使用 visual-art-director，把这张照片改成蓝色纸币钢版雕刻，尽量保留建筑和构图。

## 仓库结构

```text
SKILL.md
agents/openai.yaml
references/
evals/
scripts/validate_skill.py
使用指南.md
```

## 运行静态检查

```bash
python scripts/validate_skill.py
```

> 静态通过仅证明 Skill 结构与规则样例有效，不代表真实 Agent 生图能力已验证。Skill 本身不包含图像模型；需要宿主提供图像生成与编辑工具。

## 版本

1.0.0 · 初版

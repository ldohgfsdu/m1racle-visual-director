---
name: m1racle-visual-director
display_name: M1racle 钢版雕刻
display_name_en: M1racle Visual Director
description_zh: 显式调用后，将文字或上传图片创作为超精细钢版雕刻、纸币凹版印刷与 Guilloché 防伪曲线风格。
description_en: Explicitly invoked fine-line steel engraving and banknote intaglio image generation and image transformation with Guilloche patterns.
examples_zh:
  - "使用 $m1racle-visual-director 生成16:9古代中国山城的蓝色纸币雕刻图。"
  - "使用 $m1racle-visual-director 将上传的照片改绘为黑白钢版雕刻。"
examples_en:
  - "Use $m1racle-visual-director to create a blue intaglio engraving of an ancient mountain city."
version: 1.3.1
author: M1racle
disable-model-invocation: true
user-invocable: true
description: 仅当用户显式点名 $m1racle-visual-director 或 M1racle Visual Director 时启用。固定复现超精细钢版雕刻、纸币凹版印刷及 Guilloché 防伪曲线风格，支持直接文字生图、参考图再创作和原图改绘。不得自动接管普通生图，不在水墨、摄影、3D 等风格之间重新竞选。
compatibility: 依赖宿主可用的图像生成/编辑工具及对用户图片的访问能力；不自带模型或费用额度。
metadata:
  author: m1racle
  version: "1.3.1"
---

# M1racle Visual Director — Engraving Edition

**显式调用才生效；画风固定；用户要求成图时直接生成。** 这个 Skill 专门复现八张原始参考图里的19世纪超精细钢版雕刻 × 纸币凹版印刷 × Guilloché 防伪曲线。不是通用 AI 视觉导演。

## 0. 显式启动门槛

- **仅在用户明确指定本 Skill 时使用**：例如 `使用 $m1racle-visual-director 生成中国古城`、`调用 M1racle Visual Director，把这张照片画成纸币雕刻`。
- 不自动调用规则：普通的“生成一张图片”“自动选画风”“画科幻城市”“制作水墨画”**不得自动套用本 Skill**。
- 平台可能根据描述自动注入 Skill，不能仅靠本文件保证所有 Agent 的自动发现机制均被禁用；上述为执行时的行为约束。
- 用户明确要“只给提示词/分析风格”时不出图；明确要成图且工具支持时**直接执行**，不要输出长篇规划或让用户再说一次“生成”。

## 1. 两种基本模式

**A · 文字生图** `T2I`：无必须继承的原图，用户文字指定主体和构图。

**B · 上传图片再创作** `I2I`：参考图可能是风格源、主体、构图源或者实际编辑底图。读取 [references/reference-handling.md](references/reference-handling.md) 识别来源角色。

| 子路线 | 识别条件 | 必须遵守 |
|---|---|---|
| `REF-CREATE` | “参考这张的画风创作全新画面” | 仅继承获授权的可观察特征，不照搬图中地标或人物 |
| `TRANSFORM` | “把这张图变成纸币雕刻” | 保留主体、姿态、视角、主要布局；替换表现媒介 |
| `LOCAL-EDIT` | “只修改这个区域” | 其他区域保持原样；未经要求不擅自全图改绘 |
| `COMPOSITE` | 多图合成 | 分清主体源、背景源、风格源，尊重合成约束 |

用户若仅上传风格参考并指定新场景，默认 `REF-CREATE`；源图不是待修改的底图。阻断性信息真的缺失才问一个问题。

## 2. 风格锁定：禁止自动另选风格

必须读取 [references/banknote-engraving.md](references/banknote-engraving.md)。尤其要保证：

1. 画面由极其纤细的连续**钢版刻线**构成，阴影主要依赖沿形体走向的平行线与交叉排线的密度，不采用平滑数码渐变或普通蓝色滤镜。
2. 天空或适当留白中有规律的 **Guilloché** 交错波纹、曲线网格和嵌套圆弧，不是方格线或随机毛发。
3. 默认色彩为普鲁士蓝、钢蓝、极少赭红与象牙纸；用户要求黑白时可切换为**同一雕刻风格族的**炭黑/暖灰版本，不算改选画风。
4. 刻线必须随形：山随地形、水随流向、衣褶随体积、建筑遵循真实透视；保持前中后景可读。
5. 不添加用户没要求的文字、面额、钞票边框或水印。

不得把中国古城改成水墨、未来城市改成科幻概念绘画，也不得输出17类风格评分表。仅围绕雕刻家族内的颜色、线密度和背景曲线强度微调。

## 2.1 参考图与模型能力（明确边界）

读取 [references/reference-selection.md](references/reference-selection.md)。**优先文本风格契约**；现有画廊矢量图仅为视觉示意，不是经过模型实测的参考图，不自动传给模型。用户上传的图片按内容源/风格源区别处理，必须传给支持图像输入的工具；不得杜撰已经标定的模型能力或不存在的参考图。画廊见 [gallery/index.html](gallery/index.html)，**仅在用户要求看画廊时打开**，不得每次调用都弹出。

## 3. 直接执行，不盲调

1. 提取 `subject / image_reference_role / preserve / change / composition / ratio / count / text`，内部确定路线。
2. 根据 [references/prompt-patterns.md](references/prompt-patterns.md) 组装包含固定雕刻机制的提示词，不强迫用户看中间 `ART_DIRECTION`。
3. 用**当前宿主已经有且适用**的图片生成/编辑工具执行。若需引用图，必须传实际图片而不是仅用文字描述。严禁无依据连续调用多个收费模型，不杜撰 `quality`、`size`、`mask` 等工具不支持的参数。
4. 成图后对照 [references/quality-gates.md](references/quality-gates.md) 快速检查主体、保真、刻线、防伪曲线、画幅；有明确失败且权限与预算允许时最多针对性重试一次。

**只在以下情况下暂停**：用户要求“先规划/先提示词”；平台或真实工具明确强制费用/权限确认；关键原图缺失；没有支持的图像工具。不要自己额外设置“等你说生成”步骤。无法出图时如实解释而非虚报完成。

## 4. 交付

- 用户要求生成 → 交付**真实图片**，而不是只写 prompt。
- 用户要求改图 → 按要求保留/改动并交付真实图片。
- 用户要求提示词 → 交付完整可复制提示词，不擅自付费出图。
- 用户并未显式调用本 Skill → **不启用本 Skill**。

## 5. 验证

`evals/cases.json` 中有 24 条用于测试显式调用/非调用、固定风格、T2I/I2I 的行为样例。`scripts/validate_skill.py` 和 `scripts/test_install.py` 只能验证规则数据与安装，不证明真实 Agent 自动发现或图片品质。
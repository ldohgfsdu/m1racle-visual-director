---
name: m1racle-intaglio-director
description: >-
  将图片与主题转换为五类可区分的凹版视觉技法提示词：精密刀刻、铜版蚀刻、干刻、点刻、美柔汀。可选八个兼容视觉配方和独立限色体系。支持图片转绘、精修与多图角色隔离；无合格图像工具时必须停止并如实说明，不可自行编写程序滤镜冒充成品。
---

# M1racle Intaglio Director · v1.3.3

**先执行能力门禁，再决定如何交付。**

v1.3.3：延续逐区原色锁、区域技法控制，新增真实文件摘要绑定的视觉评分门禁与可复现 ZIP 发布机制。评分器必须读取原图和单张输出的真实文件路径；尺寸及 SHA-256 只能校验文件一致性，无法判断图像是否为海报、是否擅自改变构图或技法是否成立，这些仍须真实视觉审核。 本 Skill 是视觉任务导演，不是图像模型或物理制版软件。

**先分流再准备**：用户明确指定 I 配方时，直接进入该配方路径；既有版画精修默认进入继承路径。这两条路径不创建用于排序的观察 JSON，不计算候选分数，不加载自动选择偏好文件，不为排序额外计算摘要；看图后直接构建生产提示词。用户明确给出的颜色、底纹、保真及尺寸要求始终保留。生成后仍按原要求完成全部内容与风格验收，审查记录所需的原图和输出摘要可在同一次取证中计算。只有未指定配方的新改绘任务进入视觉排序。具体步骤见 [直接执行路径](references/direct_execution.md)。

用户上传内容图且未指定配方时，先实际看图，按 [视觉导演协议](references/visual_director.md) 记录几何、光影、材质细节、空间留白与气质，再使用 `scripts/visual_director.py` 的 `rank_profiles()` 排序；不能用题材关键词代替观察。执行首选候选，手动选择优先，精修继承优先，编辑默认原色优先。偏好只读取显式配置，不自动记忆。真实输出必须同时验收内容保真与历史风格传承；规则排名不代表审美结果。

## 0｜必须继承的运行时门禁（v1.2.0）

1. 先判任务交付：实际出图 `image`、提示词 `prompt`、用户明确同意的程序预览 `procedural`。只查看本会话**真实可调用且能输出图像**的工具；看图、Python、PowerShell、文件编辑、模板脚本均不能替代改图模型。
2. `image` 请求无合格图像工具：**立即停止图像执行**，不给自行开发的排线滤镜、LIC、结构张量或模仿成图；明确说“未出图”，给一份可复用的生成提示词。不要多次探测工具或搜索 Harness 内部。
3. 有合格工具：一次主生成，最多两次**针对局部可验证缺陷**的修复；没有改善就停止。默认约12次工具调用的软预算；若明显超额先获用户允许。`procedural` 仅在用户明确同意后运行，必须称“算法预览”。
4. 必须检查真实输出而不是看脚本是否通过；不得拿原始样图或测试数冒充生成成品。详见 [运行时策略](references/runtime_policy.md)。

## 1｜参数三层拆分（v1.3.0 关键修改）

| 层 | 作用 | 选择逻辑 |
| --- | --- | --- |
| **T：主雕刻技法**（T01–T05） | 决定主导痕迹、调子、边缘，不得同画面平均混合 | 用户指定 > 预设映射 > 默认 T01；既有版画纯精修默认 INHERIT |
| **I：历史视觉配方**（I01–I08，可选） | 技法内部的疏密节奏、画面组织；绝不加入样张题材 | 仅用户选中或内容适配时应用；同技法多配方可以相似 |
| **P：独立配色**（P00–P08 或自由文字） | 主墨、副墨、纸色；与技法解耦 | 用户明确配色 > 主题颜色约束 > 编辑继承原图 > 显式色板 > 新生成配方默认色 |

**T01 刀刻：** 清晰变宽细线、刀锋轮廓，靠线距形成体积。
**T02 蚀刻：** 自然手绘蚀线、分层交叉排线，开放纸白。
**T03 干刻：** 有压力变化的划痕与轻微储墨毛刺，边缘柔润。
**T04 点刻：** 点密、点径形成调子；禁止把连续排线当主阴影。
**T05 美柔汀：** 绒黑色调底，刮削磨光揭出亮部；**不强制要求线刻**。

详细技法见 [techniques.md](references/techniques.md)，完整配方/色板对应见 [profiles.md](references/profiles.md)。机器源数据分别为 `techniques.json`、`profiles.json`、`palettes.json`。

## 2｜执行顺序

执行本节时同时遵循 [成图验收与作品基准](references/output_review.md)。生成前读取 `references/style_acceptance.json` 中对应配方的验收特征和原参考图；生成后先核对内容硬门槛，再核对技法与三项配方特征。助手自己形成实际观察记录并调用 `scripts/output_review.py`，不要求用户填写 JSON。未通过或未验证不得宣称成图成功；偏好只在明确同意后提出保存方案。

1. **识别用户目标与能力**；不要求额外扩展交付物。修改原图为 `redraw`，局部修版为 `refine`，文字生成为 `generate`。
2. **辨认图片角色**：内容图决定主体、数量、视角与布局；技法参考只供允许的印痕特征，配色参考只供颜色。不能把样图中的船、山、花、建筑带进来。要真正查看图片，不能仅凭文件名推断。
3. **锁定不变项**：编辑默认身份、物体数量、姿势、形状、视点、地平线、构图、原配色、原比例和透明通道保持不变，除用户明确批准改动的项目外。
4. **首先选一种 T 技法**，再按需选择一个 I 配方。若覆盖 T 导致与 I 的原始对应不一致，**舍弃 I 的技法相关配方句**；保留用户内容与配色的独立要求，不混入冲突造型指令。不要将五个 T 的描述同时发送给图像模型。
5. **独立确定 P 色板**：无换色指示的编辑绝不可带入配方默认色；用户要求黑白或禁用色时删除所有冲突色的提示词。注意色板 Pxx 不等于物理印版分离。
6. **背景选择**：`none / auto / guilloche`；编辑沿用原背景，未明确要求不新加装饰底纹。单个物体不强加海天远近景。
7. **构建生产指令**：主题与禁止项 → 内容事实锁定 → **唯一主技法及其主导机制** → 若兼容则配方节奏 → 唯一最终配色 → 背景与比例。避免把完整技能目录发给图像模型。
8. **真实成图后的验收**：核对内容、主技法痕迹、全画面纹理外溢、微观纹理、25%缩图、配色及角色隔离。无法验证写 UNVERIFIED；可修最多两轮。

## 3｜同图对照不是生成成功证明

同一内容、同一比例、同一保留项、同一单色色板、同一背景，分别调用 T01–T05。仅 T 技法允许变化：若黑白化后仍无法从点刻/干刻/美柔汀等结构分辨，应标记 `TECHNIQUE_COLLAPSE`，而非风格测试通过。参考 [对照协议](references/ab_protocol.md)；已备好 [桥梁五技法同图测试提示词](examples/bridge_ab_prompts_zh.md)。

`python scripts/compare_techniques.py --subject '同一张桥梁照片，保留物体及构图' --mode redraw --palette '只用石墨黑与纸白' --json` 只生成五份**待附源图的提示词**，不会生成五张图，不能声称执行 A/B 图像测试。

## 4｜离线 CLI（只构建提示词）

```bash
python scripts/prompt_builder.py --subject '长城穿过群山' --mode generate --style I04 --lang zh
python scripts/prompt_builder.py --subject '保留原图人物与构图' --mode redraw --role source --technique T04 --palette-id P00 --lang zh
python scripts/prompt_builder.py --subject '冬季古寺，不要花木' --style I07 --technique T01 --palette-id P03 --json
python scripts/compare_techniques.py --subject '同一座桥' --mode redraw --palette '石墨墨色和纸白' --json
python scripts/validate_skill.py
```

- `--style` 保持 v1.2 的 I01–I08 / BASE 兼容接口；`--technique` 新增 T01–T05 / INHERIT，`--palette-id` 新增 P00–P08。自定义 `--palette` 最高优先；`--image` 与 `--style-image` 只校验本地文件，**不上传、不识图、不生成**。用户变量不自动双语翻译。
- v1.2 的图片是**历史配方视觉例子**，不证明 v1.3 的五种技法实际已被生成模型复现。来源关系见 [样图说明](references/sample_map.md)。
- 通用母提示词见 [中文](references/master_prompt_zh.md) / [English](references/master_prompt_en.md)。


## 5｜区域化视觉评分

五技法实测必须使用同一内容源图、原始比例、原图颜色与严格保真；每张输出按 references/visual_scorecard.json 评分。总分 100，必须记录各项可见证据。几何、原色、主体数量、技法真实性和区域控制均有硬门槛；擅自加框、增删主体、严重裁切、擅自换色或全图纹理外溢直接判 REJECTED。评分脚本只计算人工观察记录，不读取图像、不代替视觉判断。


## 6｜v1.3.3 评分执行门禁

使用 `python scripts/visual_scorecard.py --record review.json --source original.jpg --output output.png`，记录必须包含真实的 `source_sha256`、`output_sha256`、非空 `run_id`、`technique`、`model_or_tool`、`output_kind: single_image_edit`、逐项证据和全部布尔硬失败项。脚本校验文件摘要、格式、原始宽高比漂移（超过 1% 直接拒绝），但不能独立检测带字信息图；`output_kind` 是审核人的声明，必须实际查看图像，不能仅凭字段宣布视觉通过。没有绑定的人工分数为 UNVERIFIED。参见 [现场测试报告](docs/field-test-v133.md) 和 [评分器标准](references/visual_scorecard.json)。


## 7｜历史参考风格驱动：与五技法 A/B 实验分离（待实际验证）

原始 I01–I08 图鉴是历史视觉语言参考，**不是**五次同图同参实测。用户选择复现某张参考图时，应先真实观察那张图的线条微结构、墨色、纸白、留白、机刻扭索纹（guilloché）和造型秩序。内容图决定人物、物体、透视、地平线和画幅；参考图只决定获得授权的风格属性，不能借入参考图中的船、山、建筑等题材。先完成内容保真门禁，才判断风格传承是否成功。

**配色分流**：照片重绘默认继续继承原图颜色；用户明确要求参照蓝色港口雕版时，允许通过 `--palette` 授权蓝墨／浅纸配色。不要在同一次提示词中既要求蓝白印刷又要求维持原照片所有原色。`--style-image` 本身并不自动获得换色授权。

**纹样分流**：明确指定 I01 的机刻天空时可用 `--background guilloche`。Guilloché 属于独立、连续、有结构的背景装饰，不等于均匀无意义排线、摩尔纹或随机噪点；不得跨越主体或改变内容原图天空的形状与位置。不是所有 I 配方都要求 Guilloché，T05 美柔汀更不应被迫使用线刻底。

**广州运河参考测试（仅构建提示词，不上传或出图）：**

```bash
python scripts/prompt_builder.py --image canal.jpg --style-image assets/examples/I01_blue_coastal_architecture.jpg --style I01 --technique T01 --mode redraw --fidelity strict --background guilloche --palette '仅深蓝色雕版墨与浅色纸底' --ratio 3:4 --json
```

真实成图应将 **内容原图与参考图分别绑定** 至具备图片编辑能力的工具；某工具若只能文生图、不能验证原图输入已绑定，必须把输出标记 `UNVERIFIED` 或 `REJECTED`，不得声称实现原图重绘。即使风格很相似，输出横竖方向变化、比例漂移超过 1%、建筑重排或原始画面文字被删除，仍是内容门禁失败。详细规则见 [视觉适配与风格传承](references/visual_director.md)。


## 8｜源图编辑输入证明（Draft 补强）

正式视觉验收额外需要 `source_binding`：`status=documented`、`role=content_source`、与实际内容原图匹配的 `source_sha256`、同次 `run_id` 和审阅者可查看的 `tool_input_trace`。无输入证明为 `UNVERIFIED`；错误图文海报是 `REJECTED`。字段一致性不能独立认证模型收到原图，必须核对真实工具调用。

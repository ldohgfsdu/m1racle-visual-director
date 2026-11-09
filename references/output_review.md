# 成图验收与真实作品基准

助手负责看原图、实际输出和对应参考图，用户无需填写 JSON。脚本只检查助手观察记录的完整性、文件绑定和验收决策，不能独立识别主体或判断画面漂亮与否。

## 生成前

读取 [八套风格验收特征](style_acceptance.json) 中选中配方的 `required` 与 `reference`。查看原参考图，结合 [技法定义](techniques.md) 确定本次必须保留的刻线节奏、明暗机制、纸白和获授权的底纹。参考图只传承表现语言，不提供物体、构图或默认换色授权。新增特征是待实测的验收标准，不代表历史样图已证明新版技法效果。

在本次任务记录中锁定用户批准的内容事实、修改范围、最终颜色、比例、透明背景与装饰策略。生成后逐项对照该约定；明确要求改色时检查批准后的颜色，不把“保留原色”当作不可更改的规则。

## 生成后

1. 实际读取内容原图和当前输出，检查原生尺寸及约 25% 缩图。
2. 先核对 `identity/count/geometry/composition/color/role_isolation/aspect_ratio/transparency/ornament_policy`。每项记录 PASS、ISSUE 或 UNVERIFIED，以及实际观察和所在区域。不适用的透明或底纹项也应写明原因，例如“原图与输出均无透明通道”。
3. 再核对 `technique/form_following_marks/thumbnail_readability/moire`，以及所选配方的三项特征（如 `I01.1` 到 `I01.3`）。不能只凭提示词内容给 PASS。T 与 I 默认映射冲突时，不能宣称旧 I 风格已得到传承；精修继承且不应用配方时使用 BASE 与 INHERIT。
4. 保存审查记录到用户项目指定的私有证据目录；不要把用户原图、输出或偏好自动提交进本仓库。

记录顶层字段：`source_sha256`、`output_sha256`、`profile`、`technique`、`checks`。摘要必须对应实际文件；`checks` 是以检查项名称为键的对象，每个值例如：

```json
{"status":"ISSUE","evidence":"右侧桥塔向外倾斜，偏离批准的原轮廓","region":"右侧桥塔上半部"}
```

未检查项可省略，门禁会将其计入 UNVERIFIED。运行：

```bash
python scripts/output_review.py --record review.json --source original.png --output generated.png
```

硬门槛 ISSUE 优先返回 REJECTED；硬门槛缺证据返回 UNVERIFIED；内容通过但风格有问题返回 REPAIR_REQUIRED；所有必需项通过才允许声明当前记录通过。脚本成功退出码为 0，未通过为 1，输入无效为 2。原图冒充输出、过期摘要和空白 PASS 依据都会被拒绝。

修复建议只引用已经观察到的问题、对应区域与保留约束。最多一次主生成加两次修复或对照，共享原有预算；修复后必须针对新输出重新生成摘要并复查全部项目，避免局部修复引入新问题。

## 24 场景作品基准

`tests/benchmark_plan.json` 覆盖曲面建筑、工业几何、肖像、植物、拥挤街景、极简物体、多层风景和透明物体，各有高调、低调和混合光线场景。当前全部 UNVERIFIED，未提供或生成实际图片。

执行时由用户提供或明确许可使用原图，登记来源及使用权限。为每个场景分配固定 case ID，每次实际生成另设唯一 run_id，记录原图及输出摘要、工具与模型、实际提示词、T/I/P/G、种子是否可控、所有失败和修复轮次，以及上述审查结果。不要只保留最好的一次。

审美对照使用中性 A/B 标签，暂不展示方案名称；保留标签与真实方案的映射。仅在内容门槛通过的方案之间，请用户选择更喜欢的结果、并记录理由或平局。自动规则分和助手偏好不能替代用户盲评。记录数量只描述已执行的具体场景，不推导普遍成功率。

`scripts.output_review.summarize_benchmark()` 汇总所有给定轮次的状态，不从缺失或失败样本中筛出漂亮的成功率。它接受的是已审查记录的状态摘要，不是另一个独立图像验证器。

## 显式反馈

支持 `insufficient_ornament`、`too_much_ornament`、`prefer_source_colors`、`geometry_changed`、`looks_like_filter`。`feedback_patch()` 仅在明确同意后返回偏好修改提案，永不直接写文件；保存位置和内容须由用户批准。底纹不足只能建议“兼容时优先”，不能无视留白强加底纹。几何变形与滤镜感应进入缺陷修复，不得当作用户偏好长期学习。

本轮交付包含协议、门禁、基准计划及合成记录回归测试；实际图像观察可靠性、24 场景生成效果及审美偏好校准仍未验证。


## v1.3.2 100 分制视觉评分

使用 references/visual_scorecard.json 作为唯一权重来源，按每个项目 0–5 分填写实际观察和证据，再运行：

```bash
python scripts/visual_scorecard.py --record review.json --source original.jpg --output generated.png
```

权重为：几何与构图 20、原图配色 10、主体数量与位置 5、技法真实性 20、区域控制 10、技法区分度 5、空间与氛围 10、缩略图可读性 10、伪影与装饰洁净度 10。所有项必须附证据。几何、原色、主体完整性、技法真实性、区域控制和画面洁净度设硬门槛；擅自加框、增删物体、严重裁切、擅自换色或严重全局纹理外溢直接 REJECTED。85 分及以上且硬门槛通过为 PASS，75–84.9 为 CONDITIONAL，低于 75 或任一硬门槛失败为 REJECTED。缺少观察或证据为 UNVERIFIED。

评分脚本只计算人工观察输入，不具备视觉识别能力；CI 通过不等于图像通过。


## v1.3.3 证据边界

评分记录必须包含 run_id、technique、model_or_tool、output_kind=single_image_edit、source_sha256、output_sha256、逐项可见证据及完整布尔硬失败项。CLI 校验实际文件摘要、PNG/JPEG 固有尺寸和原图宽高比，超过 1% 相对比例漂移直接拒绝。

但相同比例的信息图、错误画面或无效技法不能只靠文件摘要和尺寸识别。必须由实际观看输出的审阅者核对它是否为单张原图编辑、是否多出文字/边框、主体数量与位置、配色和技法质量。评分器是证据绑定的计算器，不是视觉判断器。


## 源图输入绑定证据门禁（2026-11-09，Draft PR）

**不能从原图与输出图的 SHA-256、相同尺寸或主观相似度推断生成器真正接收了原图。** 一张评测海报即使文件有效，也不能当作成功的单幅照片编辑。

在 `visual_scorecard.py` 的审查 JSON 中增加实际图像编辑输入的可追溯声明：

```json
{"source_binding": {
  "status": "documented",
  "role": "content_source",
  "source_sha256": "<实际源图 SHA-256>",
  "run_id": "<本次真实生成运行 ID>",
  "tool_input_trace": "<审阅者可回看的实际工具调用记录位置>"
}}
```

缺少声明或其中 run_id / 摘要不匹配，结果为 `UNVERIFIED`，满分也不能变为 PASS。实测宽高比漂移大于 1% 时，仍然 `REJECTED`。错误报告图须经人工审核标记 `wrong_output_type=true` 或 `unauthorized_report_layout=true`。

**关键边界**：代码只核查字段一致性；`tool_input_trace` 必须来自真实存在、经审阅者检查的工具请求。人为编写任何字符串并不能自动证明模型已经读取原图。生成单张作品与制作评分报告必须严格分离，不能让图像模型生成自己的验收分数。

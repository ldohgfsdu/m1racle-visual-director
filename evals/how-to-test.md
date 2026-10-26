# v1.4.2 验收：点名调用、固定雕刻、实际出图

先运行 `python scripts/validate_skill.py`、`python scripts/test_eval_contract.py`，它们只验证测试数据和评分器，不覆盖模型真实行为。

测试数据为 30 个场景（24 个原场景 + 6 个语义邻近负例）。图生图输入使用 `evals/fixtures/` 中显式标为**合成示意**的 PNG 位图：这些是程序绘制的结构测试输入，不是假称为真实照片或八张原始参考。配套 SVG 只是便于人读的独立矢量示意，不应把它当作原图。运行前须确认宿主可读取 PNG；若不支持，明确记为 BLOCKED_TOOL，不能把无输入当 PASS。每条有 `fixture`、`expected_status`、`required_evidence`、`quality_gate` 和 `pass_criteria`。不得仅凭文本生成或静态检查宣称图像质量已验证。

实际 Agent 运行后，按 `evals/rubric.json` 填写逐条 JSON 结果并执行 `python scripts/check_eval_trace.py --results results.json`。缺少真实工具轨迹或质量门槛证据即 FAIL。

在全新 Agent 会话依次验证：

1. 不提 Skill 名称：“画一张未来城市。” → **不应触发**本雕刻 Skill。
2. 点名：“使用 $m1racle-visual-director，画未来城市，直接出图。” → 直接调用可用生图工具，默认蓝色纸币雕刻。
3. “使用 $m1racle-visual-director，画黑白古典钢版希腊神庙。” → 黑白变体，不是任意选风格。
4. 给一张照片并点名要求钢版改绘 → 图像真实传入图像工具，主体与布局保持。
5. 给一张风格参考并要求全新城市 → 不复刻原图场景。
6. 点名但要求“只写提示词” → 不调用收费工具。
7. 检查工具是否确实有费用或授权前置限制；只有真实限制才允许暂停确认。

必须记录技能是否加载、真实工具调用、图像结果与质量。仅凭类似的回答格式不能判定自动发现成功。
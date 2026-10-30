# v1.3 同图五技法对照协议 / Fixed-variable A/B

## 目的与证据边界

检验 **T01–T05 是否真正构成五种可辨的主导印痕结构**，而不是由于题材、配色、样图不同造成错觉。脚本只生成提示词，不能代替实际图像模型 A/B。

## 测试设计

至少使用三种内容源（建议：建筑/桥梁、肖像、简单静物）。每份内容源：

1. 原图文件与主体约束完全一致；编辑工具的采样条件、画布、源图强度、轮次、背景、长宽比与随机种子（若支持）保持一致。
2. 五次生成的共同参数：`--style BASE --mode redraw --role source --palette '只用石墨黑与纸白' --background none --fidelity strict`。唯一自变量为 `--technique T01` ... `T05`。**不使用 Ixx 配方**，避免重复因素。
3. 对支持同一 seed 的工具，记录 seed；不支持固定 seed 的工具，明确记录未控制的随机性；如有额度，可每种技法重复 2 次观察稳定性，但避免无上限反复挑图。
4. 让评审先不看 T 标签与颜色，以单色输出判断差异。不要只比较原始八张不同题材的样图。

## 评价表（每张图单独登记）

| 检查项 | 标准 | 记录 |
| --- | --- | --- |
| 主体保真 | 数量、身份、构图、视点、轮廓与原图相符 | PASS / ISSUE / UNVERIFIED |
| 主技法识别 | 刀刻=收尖线；蚀刻=交叉蚀线；干刻=绒边划痕；点刻=点群；美柔汀=暗底磨光调子 | PASS / ISSUE / UNVERIFIED |
| 技法互斥 | T04 不靠横排线建调子；T05 不靠交叉排线建调子 | PASS / ISSUE / UNVERIFIED |
| 纹理外溢 | 局部桥梁横纹不扩散到水面、天空、船身 | PASS / ISSUE / UNVERIFIED |
| 两尺度可读 | 100% 的印痕有形体意义；25% 主体仍清楚 | PASS / ISSUE / UNVERIFIED |
| 配色与背景固定 | 均为相同黑白纸墨；无预设色泄漏，无新底纹 | PASS / ISSUE / UNVERIFIED |
| 技法区分稳定性 | 同源图五张盲评能解释各自的构形差异；对随机性有记录 | PASS / ISSUE / UNVERIFIED |

`TECHNIQUE_COLLAPSE`：换 T 后主要变化仍只是颜色、对比、线密或场景内容；应标 ISSUE，不要单靠 prompt 的文字差异标 PASS。

## 运行方式

```bash
python scripts/compare_techniques.py --subject '桥梁、驳船、楼群均按原图保留' --mode redraw --palette '只用石墨黑与纸白' --json
```

把五份提示词与**同一张内容源**分别提交到合格图像模型；脚本输出不含图像，不可作为实测记录。记录格式见 `tests/ab_results_template.json`。

桥梁同图提示词：[examples/bridge_ab_prompts_zh.md](../examples/bridge_ab_prompts_zh.md)。

# 视觉适配与风格传承

先由具备视觉能力的助手实际查看内容图，再记录结构化观察。没有看图能力时如实说明；文字关键词只作为文字任务的有限提示，不冒充视觉分析。离线脚本不会调用视觉模型、上传图片或生成成品。

## 观察协议

JSON 顶层仅包含 `image_sha256`（实际内容图的 SHA-256）和 `observations`。每项观察为 `{"value":0.8,"evidence":"天空位于主体上方，占画面大部"}`。数值范围为 0–1，表示观察到的特征程度，不是置信概率。未知项省略，不填猜测值。

| 组 | 观察字段 | 0 到 1 的含义 |
| --- | --- | --- |
| 几何 | regularity, curvature | 不规则到规则；直线到曲线主导 |
| 光影 | darkness, contrast | 暗部少到多；低到高反差 |
| 细节与材质 | density, softness | 稀疏到拥挤；硬边到柔和连续转折 |
| 空间 | negative_space, depth | 留白少到多；平面到纵深分层 |
| 气质 | monumentality, delicacy | 轻小到纪念性体块；粗重到轻盈细腻 |

规则位于 `visual_matching.json`。初始权重为 30/20/15/15/20，未经过真实作品盲评校准。按观察与各配方目标的距离排序，不使用题材名称。缺少的观察不给正向分；信息不足或所有配方适配偏低时选 BASE。输出分数组件、证据、备选与 low/medium 信息充分度，绝不解释为成功概率或审美胜率。

## 使用

将实际观察保存为仓库以外的 `analysis.json`，避免将用户图片和私有偏好提交到仓库：

```bash
python scripts/prompt_builder.py --image photo.jpg --visual-analysis analysis.json --preferences preferences.json --json
```

偏好文件可省略。支持 `style_selection: "auto"`、`recommendation_count: 1–3`、`render_strategy: "best_first"`，以及 `aesthetic_preference`：

```json
{
  "style_selection": "auto",
  "recommendation_count": 3,
  "render_strategy": "best_first",
  "aesthetic_preference": {
    "detail": "high",
    "geometry_fidelity": "strict",
    "engraving_character": "precise",
    "preferred_visual_identity": ["banknote_engraving", "classical_intaglio"],
    "guilloche": "preferred_when_compatible",
    "color": "adaptive",
    "atmosphere": "elegant_and_detailed"
  }
}
```

高细节、精密刻线、银行券和典雅偏好只提供合计最多 5 分的候选加分，输出单独披露。严格几何保真及自适应颜色沿用编辑默认约束，不授权改构图或换色。偏好仅从用户指定的文件读取，不自动保存或根据一次上传推断永久喜好。

手动 `--style`、`--technique`、`--palette`、`--palette-id` 与 `--background` 优先。精修默认继承现有技法。编辑不自动采用候选色板；无明确改色授权时保留原色。偏好允许底纹且留白充分、细节不拥挤时，才建议背景扭索纹；文字禁止底纹仍优先。

## 真实生成与风格传承

用户未指定配方时，助手默认执行第一候选，无需让用户试八次。实际生成仍须具备合格图像工具。默认一次主生成，最多两次针对已验证缺陷的修复；只有用户允许比较且预算足够时才生成第二、第三候选，共享该预算，不额外增加次数。

生成后分别核对主体身份、数量、轮廓、透视、原色，以及所选配方的刻线节奏、调子、纸白和经授权的底纹。查看 `assets/examples/` 中对应参考图及 `profiles.json` 的原有配方，保持二者稳定；不得将参考图题材带入内容图。手动选 I01 时不能因自动排名改成 I06。T 覆盖与配方不兼容时继续沿用现有冲突处理规则，并如实提示配方未应用。

比较真实输出后才能报告哪个效果更好。当前排序测试仅验证约束与排序行为，真实同图盲评、视觉模型观察可靠性和旧风格传承效果仍未验证。

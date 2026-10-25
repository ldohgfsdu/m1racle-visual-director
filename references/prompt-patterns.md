# 按生成路线组织提示词（工具无关）

以下模板是**结构**而非必须一字不改的英文咒语。优先采用生成模型最能理解的表述；文本与提示词语言可根据用户喜好调整。最终工具若原生支持图像编辑、遮罩或多参考源输入，应使用真实的图像输入而非仅写“see image 1”。

## 1. T2I：仅凭文字从零生成

```text
SUBJECT: [主体、动作、场景、必需元素]
PURPOSE: [用途、受众或渠道]
ART DIRECTION: [一种选定的主要风格；媒介、历史/文化依据及具体制作技法]
COMPOSITION: [主体大小、前中后景、镜头视角、焦点、留白]
LIGHT / LINE: [摄影时描述光源；绘画时描述笔触与线条构建方式]
PALETTE / MATERIAL: [限制色、色彩关系、材质]
OUTPUT: [用户要求的画幅、数量、文字、具体约束]
AVOID: [仅针对这次任务的典型失败]
```

用途为纯提示词时，交付复制即用的自然语言提示词；要生图时实际调用工具。

## 2. REF-CREATE：参考图创作新画面

```text
Create a NEW [output subject] using the attached image(s) ONLY as defined references:
- Image 1 provides: [style qualities such as linework / medium / palette]
- Image 2 provides: [composition rhythm or lighting, if requested]
- The NEW subject must be: [new subject, location, objects, action]
- Retain: [transferrable traits explicitly requested]
- Do NOT carry over: [old location, incidental characters, labels, unrelated source content]
[Composition, selected style details, palette, material, output].
```

**关键**：如果上传的是八张钢版雕刻图，用户要“新画一座古代中国山城”，保留的是精密刻线与纸币曲线，不能把图中的富士山、港湾、雅典城按原样复制到中国场景。

## 3. TRANSFORM：同一场景更换绘画媒介

```text
Transform the ATTACHED SOURCE IMAGE into [new visual style].
Preserve the original subject identity, object count where discernible, pose, camera orientation, principal architecture, relative positions and spatial layout. The source image defines CONTENT and COMPOSITION.
Change ONLY visual rendering: [engraving strokes / brush texture / palette / material / period style].
Protect distinctive details: [observable details important to user].
Avoid adding new central subjects, modifying faces or replacing the location. [Aspect ratio and crop constraints].
```

注意：不能承诺像素级不变，除非有适当的图像编辑与验证工具。

## 4. LOCAL-EDIT：局部变更

```text
Edit the ATTACHED SOURCE IMAGE.
CHANGE: [only the requested region/object, with the exact operation].
PRESERVE: [all unaffected subjects and regions, identities, poses, camera, surrounding composition, lighting consistency].
INTEGRATE: [correct scale, perspective, edges, contact shadow, reflection, occlusion].
Do not restyle, recrop or reconstruct unaffected areas. [Supported mask/region references if tool permits].
```

背景替换不等于重新设计人物。删除路人不能顺便增加虚构招牌。用户没让变的地方优先保持。

## 5. COMPOSITE：多源合成

```text
Compose a new single image from the attached sources with explicit roles:
- Image 1: PRIMARY SUBJECT. Retain [specific unique features].
- Image 2: TARGET SCENE / BACKGROUND. Retain [layout and perspective].
- Image 3: STYLE / LIGHTING REFERENCE, if supplied.
Place the subject at [position, scale, action] in the target scene. Match lighting direction, perspective, depth, color temperature, occlusion and natural contact shadows.
Do not merge unrelated faces, logos or background features. Keep all source roles separate.
[Output specification].
```

## 6. 风格选择后如何写“技术句”

不佳：`beautiful, amazing, epic, hyper detailed, masterpiece`（无法验证、很少能稳定区分风格）。

更佳：`two-ink steel engraving, dense contour-following parallel hatching, shadow built through line density, fine curved Guilloché security patterns in open sky, warm ivory paper`（可以从画面逐项验证）。

不佳：`high-end modern product photo`。

更佳：`single diffused softbox at 45 degrees, accurate matte packaging with controlled specular reflections, neutral light-gray sweep, physically coherent shadows, legible product silhouette`。

不佳：`Chinese style illustration`。

更佳：`fine gongbi outlines, disciplined layered mineral pigments, restrained background ornament, precise silk-textile folds, traditional botanical proportions`。

## 7. 负面约束纪律

- 负面提示词只在相应生成器支持时填写专用 negative 字段；其他情况并入自然语言避免项。
- 不能因为这是版画风格就无条件 `no text`：用户要带文案海报时必须保留文案需求，并检查文字质量。
- 禁止项要具体、短、有助于纠偏。不要为每张图固定附加上百个互相冲突的 negative 词。

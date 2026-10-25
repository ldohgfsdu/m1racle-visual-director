# 提示词策略：固定钢版纸币雕刻

下面只定义内部的提示词结构；用户要求直接生图时无需把这个阶段单独展示。风格基线见 [banknote-engraving.md](banknote-engraving.md)。

## T2I：从文字生成
```text
[USER SUBJECT, CAMERA AND COMPOSITION]. Ultra-fine nineteenth-century steel-plate banknote intaglio engraving. Thousands of crisp continuous burin lines, contour-following parallel hatching and curved cross-hatching, shading solely through line direction, intersection and density. An intricate integrated background of mathematically ordered interwoven Guilloché security curves, looping arcs and waves, not a square grid overlay. Restrained deep Prussian-blue and steel-blue printing inks, subtle terracotta accents on warm ivory paper. Clear subject silhouette, rich atmospheric depth, physically coherent engraved texture and paper impression. [USER CONSTRAINTS, FORMAT, TEXT]. Avoid photographic smooth shading, colored filters, chaotic scribbles, unrequested logos and lettering.
```
If user explicitly requests monochrome, replace palette with charcoal-black and warm gray on ivory; retain the same engraving style family.

## REF-CREATE：参考图风格，新主体
```text
Create a NEW [SUBJECT]. Use the attached reference only for its precise steel engraving linework, hatching density, Guilloché geometry, ink palette and print substrate. Do not copy its incidental buildings, figures, landmarks, typography or original composition unless user authorizes those elements. [FIXED ENGRAVING SPECIFICATION].
```

## TRANSFORM：保留原图内容，替换媒介
```text
Transform the provided SOURCE IMAGE into intricate banknote steel engraving. Preserve the visible subject identities, poses, major architectural structures, camera viewpoint and relative composition. Replace visual shading with razor-fine contour-following hatching, crossing burin lines, limited intaglio inks and suitable Guilloché geometry in negative spaces. Do not add new central subjects or alter source identity.
```

## LOCAL-EDIT：局部修改
```text
Modify only [TARGET REGION/OBJECT] in the SOURCE IMAGE; preserve all unaffected regions, identities and layout. Do not globally restyle other areas or add ornaments unless requested.
```

## COMPOSITE：多源合成
```text
Combine [SUBJECT FROM IMAGE A] and [BACKGROUND FROM IMAGE B] according to [USER PLACEMENT]. Respect source roles and identity locks. Render final composition using the fixed intricate steel engraving / Guilloché treatment if user asked for global style.
```

When image input is required, send the actual image(s) to a capable tool. Never invent tool args such as exact dimensions or quality. If user asked for actual image, call it immediately when permitted.
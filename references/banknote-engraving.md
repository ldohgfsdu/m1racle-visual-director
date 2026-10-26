# 风格卡：Banknote Intaglio × Guilloché × Steel Engraving

## 一、识别条件

本仓库**没有随包提供原始参考位图**；下述是文字化的两种风格规范，不应声称模型已看到八张图。若用户单独上传参考图，才依据可见内容选择：
- **A / 彩色纸币雕刻**：深普鲁士蓝/钢蓝与少量赭红，暖象牙纸底，天空和空白区域有复杂交织 Guilloché 防伪曲线，建筑山川由细密随形排线构成。
- **B / 古典黑白钢版**：炭黑/灰/旧纸米色，人物石雕建筑与云层通过密集交叉排线呈现明暗，戏剧性更强，几何防伪曲线可以减弱。

不把两类误写为一种；用户给了参考图时，以当前参考图可见的具体线条结构优先。

## 二、必须抓住的线条机制

1. **Burín / engraved line**：以超细刻线为基本画素；高亮可以是裸露纸色。
2. **Cross-hatching**：通过疏密/交叉而不是数字渐变来表达暗面。
3. **Contour hatching**：山体沿山脊、海水沿流向、衣纹沿褶皱、瓦片沿屋面排布；不能统一涂同一密度纹理。
4. **Guilloché**：周期交错、连续曲线、环形/波形防伪底纹，有方向与秩序；不是简单棋盘网格或噪声。
5. **Limited inks**：2–3 主油墨色；色彩以印刷叠合体现，不是普通全彩渲染。
6. **Composition**：雄伟主景、近中远景、远景线条密度下降、可读的轮廓。
7. **Printing substrate**：微弱纸纹有助于真实感，但旧纸污迹不是主体。

## 三、彩色版本模板（在 [SUBJECT] 填主题）

```text
[SUBJECT]. A monumental and meticulously balanced scene.

Finely engraved 19th-century steel-plate banknote illustration, traditional intaglio currency printmaking, thousands of razor-fine continuous burin lines, precise contour-following parallel hatching, curved cross-hatching and high-density micro-engraving. All tonal variation is achieved through the density, direction and crossings of engraved ink lines rather than smooth digital shading. Each material follows its own physical structure: flowing horizontal etching for water, sloping contour lines for mountains, precise masonry hatching for architecture, and directional foliage marks for trees.

The sky and open negative spaces are filled with extraordinarily intricate mathematically regular interlaced Guilloché security curves, nested oscillating wave arcs and fine intersecting geometric lattices, incorporated into the composition, never pasted on as an opaque overlay.

Restrained deep Prussian blue and steel-blue engraving inks, very subtle muted terracotta accents, warm ivory uncoated paper. Controlled tonal depth, monumental focal point, sharp legible silhouettes, foreground/midground/background separation, authentic crisp printed lines, delicate paper grain, archival museum-grade craftsmanship.

No incidental words, labels, logos or border ornaments unless explicitly requested. Avoid photographic tonal gradients, modern color fills, blurry or disconnected lines, randomly crosshatched surfaces, thick outlines, halftone-dot screens and digital grunge filters.
```

## 四、黑白版本模板

```text
[SUBJECT]. A dramatic yet orderly classical scene.

Nineteenth-century monochrome steel engraving and copperplate etching, exceptionally fine burin linework, dense contour-following parallel strokes, controlled cross-hatching, deep shadows built from intersecting engraved lines, bright untouched paper highlights. Intricate but restrained ornamental curves in the sky, classical anatomical and architectural draftsmanship, rich atmospheric depth.

Charcoal-black and warm gray ink on aged ivory paper, no modern gradients, no painterly brushwork, no photographic rendering, no heavy grunge. Every detail formed by disciplined printmaking strokes. Museum-quality historical engraved illustration.
```

## 五、失败修正提示

- **生成像简单蓝色滤镜** → `Replace all smooth shaded areas with physically legible micro-engraved lines; shading must be constructed from line density, not tinted photo textures.`
- **天空仅是直线网格** → `Use flowing Guilloché interlaces with curved periodic arcs and nested wave interference, not a square wire grid.`
- **线条像随机毛发** → `The hatching direction follows the shape and perspective of every object; remove chaotic scribbles.`
- **主体被纹理淹没** → `Reduce fine-pattern contrast behind the focal architecture while preserving high-frequency line detail in shadow regions.`
- **生成人物肢体错误** → `Prioritize coherent figure proportions and readable gestures over decorative micro-details.`

## 六、边界

这是**传统雕刻外观的数字模拟**，不是保证物理凹版制版过程，也无法保证每一道线在显微尺寸下都连贯。如果需要真实防伪纹样、可分色制版或矢量曲线，应另行采用绘图/制版软件与可验证输出。


## 七、可复核的线条参数（视觉锚点，而非模型能力保证）

以下为审稿时使用的**设计目标范围**，以输出图的较短边 D 为基准。生成模型不接受或不能精确执行参数时，只保留机制描述；不要虚构毫米制版精度或已标定成功率。

| 项目 | 推荐视觉锚点 | 审稿拒收条件 |
|---|---|---|
| 主体刻线厚度 | 约 0.04%–0.12% × D（D=2048 像素时约 0.8–2.5 px） | 出现大面积厚描边或被低分辨率抹平 |
| 排线间距 | 中间调 3–6 倍线宽，暗部 1.5–3 倍，高光 6–14 倍或留纸 | 各物体表面间距完全均一 |
| 交叉排线 | 两排线族夹角约 30°–70°，服从体积和明暗 | 所有区域套同一 45° 网格 |
| Guilloché | 单带约 3–12 个连续振荡周期；振幅约 0.3%–1.5% × D | 用棋盘直线、噪声或随机弯线代替周期曲线 |
| 印色 | 蓝版以深蓝、钢蓝为主，赭色点缀不超过少量视觉权重；黑白版仅黑/灰/纸色 | 退化为全彩摄影滤镜 |
| 焦点留白 | 焦点周围纹样对比应低于主要轮廓/暗部排线 | 防伪底纹盖住核心主体 |

建议最少以 **100% 显示比例**和整体缩略图各检查一次：前者查线条是否真正存在，后者查主体可读性。这些数字是可操作的人工评审锚点，**不是可由 prompt 保证的像素级约束**。

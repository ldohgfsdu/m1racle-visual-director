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

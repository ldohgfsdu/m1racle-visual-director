# 视觉风格候选库（开放列表，不是固定答案）

**原则**：先看信息表达，再看好不好看。每次仅抽取与任务最相关的 2–3 种候选。风格可以是照片、雕刻、绘画、平面图形或计算机渲染，也可能是无风格的精确图示。不要把“国风”“高级”“电影感”当完整技术描述。

| ID / 主风格 | 适合的目标 | 可观察语言 / 提示词锚点 | 典型风险 |
|---|---|---|---|
| `photo-documentary` 纪实摄影 | 新闻感、真实生活、自然人物 | natural light, candid framing, plausible lens, realistic imperfections | 摆拍、过分磨皮 |
| `photo-studio-product` 棚拍产品 | 电商展示、包装、单品、硬件 | controlled softbox lighting, accurate material, clean reflections | Logo/产品形状被篡改；无中生有接口 |
| `photo-cinematic` 电影写实 | 叙事剧照、宣传场景、强情绪 | purposeful lighting, lens language, color grading, depth layers | 泛滥的镜头光晕、肤质塑料化 |
| `archviz` 建筑可视化 | 房间、建筑、景观方案 | believable scale, coherent materials, measured perspective, daylight | 结构不合理、尺寸幻觉 |
| `editorial-vector` 编辑式矢量插画 | 信息简化、封面、教育卡片 | bold silhouette, restrained palette, clean shapes, visual hierarchy | 缺少细节；不能替代可编辑 SVG |
| `editorial-ink` 编辑式墨线插画 | 文章配图、讽刺/叙事、个性化 | economical ink strokes, selective hatching, bold white space | 混乱笔触、弱主次 |
| `soft-3d` 柔和三维图形 | 消费 App 宣传、友好可视化 | rounded volumes, soft lighting, tactile materials | 玩具化、结构失真 |
| `isometric` 等轴测示意 | 系统概念、空间结构、游戏世界 | clean isometric projection, spatial grouping, clear silhouettes | 透视不一致、无法作为精确工程图 |
| `watercolor-gouache` 水彩/水粉 | 童书、旅行、美食、轻艺术 | pigment granulation, translucent washes, textured edges | 水彩风格遮蔽主体 |
| `ink-wash` 水墨写意 | 东方山水、意境、诗性题材 | varied ink loading, negative space, expressive brush control | “所有中国场景都用水墨”的刻板套用 |
| `gongbi` 工笔重彩 | 东方花鸟/历史装饰、精密线描 | meticulous fine outlines, mineral-pigment palette, layered flat color | 过度繁复、时代服饰错误 |
| `banknote-intaglio` 彩色纸币钢版雕刻 | 纪念性风景、历史建筑、城市、宏大视觉 | ultrafine line engraving, contour hatching, Guilloché, two-ink print | 变成滤镜叠线、全部物体同纹理 |
| `steel-engraving-mono` 单色古典钢版 | 历史叙事、雕塑、英雄史诗、古典人体 | monochrome burin engraving, cross-hatching, engraved chiaroscuro | 模糊铅笔素描、旧纸滤镜喧宾夺主 |
| `woodcut` 木刻/亚麻版画 | 民俗、强烈对比、故事海报 | cut-mark rhythm, bold dark masses, carved negative spaces | 错误地生成纤细铜版线条 |
| `scientific-plate` 科学图谱 | 解剖、生物、标本、科普 | labeled composition if requested, clear structure, disciplined lines | AI 编造器官、标注与结构 |
| `pixel-art` 像素画 | 复古游戏、图标、限定像素美学 | deliberate pixel clusters, palette limits, nearest-neighbor edge logic | 低分辨率糊化伪装像素画 |
| `typographic-poster` 排版海报 | 主题海报、活动公告、视觉口号 | strong typographic hierarchy, careful grid, intentional whitespace | 模型文字拼写、排版不可靠；应优先后期真实排字 |

## 常见任务首选逻辑

- **真实产品销售**：`photo-studio-product`，若需要强调技术构造，可考虑 `isometric`；文字、商标须额外核验。
- **人物生活抓拍**：`photo-documentary`；戏剧化宣传才用 `photo-cinematic`。
- **知识图解/医学结构**：可优先精确图示工具；若明确要求静态艺术图，再考虑 `scientific-plate`；准确性由事实核验决定而非“看起来专业”。
- **历史/城市艺术插画**：在 `steel-engraving-mono`、`banknote-intaglio`、`watercolor-gouache` 等间根据目标质感选择；不是所有历史场景都必须用版画。
- **诗性中国山水**：可能适合 `ink-wash`；用户强调结构与细节时可改 `gongbi` 或雕刻。
- **极简 App 图标**：优先明确的品牌图形、构图和几何规则，必要时 `editorial-vector`；有已批准母标必须锁定。
- **童趣或轻松**：`watercolor-gouache` / `soft-3d`，注意年龄与读者群体。

## 选择优先级示例

用户：“画一个 19 世纪古城供历史展馆使用，像旧纸币一样密密麻麻的线条。”
- 用户强指定画风 → `banknote-intaglio`，无需投票。

用户：“给蛋白粉做一张清楚展示包装的淘宝主图。”
- 真实性 + 识别优先 → `photo-studio-product`；不要选纸币雕刻或水墨。

用户：“给‘机械心脏的未来’做杂志概念封面，主旨偏哲学。”
- 允许 `editorial-ink`、`photo-cinematic`、`soft-3d` 竞争；根据内容/氛围/排字工作流选最合适的一个。

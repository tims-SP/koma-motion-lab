# CORE026：GitHub skill、透明渲染与曲面算法复核

日期：2026-10-31 Asia/Shanghai。项目基线961648f。用户提出搜索GitHub相关skill及资料；本轮完成公开检索、固定commit的目录/README/源码检查和现有研究去重。没有安装skill、运行上游示例或修改渲染器，不能报告集成通过。完整固定commit和文件链接见[结构化来源清单](core026-upstream-survey.json)。

## 判断

应该在M2B1B继续实现前利用已有代码。最直接的收益来自可审查的深度纹理/遮罩/framebuffer实现，其次是按需读取的Three.js skill。安装通用skill本身不会提供角色物理深度、可信侧背资产或自然转头。

优先级是工程判断，尚非集成测试结论。保留既有M2B1A数值/人工验收范围；完整M2B、M3及自然转头仍未通过。

## 候选与取舍

| 候选 | 实际核实内容 | 对当前项目的用途与边界 |
|---|---|---|
| [CloudAI-X/threejs-skills](https://github.com/CloudAI-X/threejs-skills) | 固定0e181866；已读materials、shaders、postprocessing的SKILL.md，目录主要是说明文档 | P0按需参考材质、uniform、framebuffer和输出处理。目标r186，项目r180；不能照抄版本特有API。原画像素算术特意关闭颜色管理，不能盲目套用通用sRGB/线性/PBR模板 |
| [gkjohnson/three-depthpeeling-demo](https://github.com/gkjohnson/three-depthpeeling-demo) | 固定e6b57e1f；index.html明确引用three@0.180.0，与项目一致。index.js实际切换深度纹理、逐层render target及discard | P0优先复现深度buffer/透明层剥离机制。它没有解决PSD Multiply、原生clip、角色深度真值或无限层预算；先做小fixture，不整套替换角色renderer |
| [Live2D/CubismWebFramework](https://github.com/Live2D/CubismWebFramework) | 固定d4da0aa0；实际查看cubismrenderer_webgl.ts的clipping context、mask buffer及offscreen路径 | P0参考遮罩上下文与分组framebuffer的分离结构。Cubism模型/运行时专用，不能据此声称复现Inox ClipToLower或自动转换现有资产 |
| [stevinz/three-wboit](https://github.com/stevinz/three-wboit) | 固定d44c9450；package1.0.15；README明确近似性质、接近不透明仍偏透明，源码用加权积累混合 | 仅作对照。peerDependencies允许旧版起算不等于已测r180，更不等于原画保真。11项Multiply与艺术覆盖顺序不能直接交给近似OIT |
| [google/monster-mash](https://github.com/google/monster-mash) | 固定eb2869ad；可将草图鼓成3D并动画，C++/Emscripten；DefEngARAPL暴露ARAP、region inequality、深度求解约束 | P1在M2B完成后的M3曲面候选中参考。不是现成动漫脸重建器；应提取膨胀/形变方法，不能假设直接得到Aka鼻眼深度和原画UV保真 |
| [facebookresearch/AnimatedDrawings](https://github.com/facebookresearch/AnimatedDrawings) | 固定b8596848；有实际NumPy/SciPy ARAP求解器和tests；仓库已在2025-09-03归档 | P1参考小型2D约束形变实现，尤其源平面残差处理；不承担3D头部深度和自然转头 |
| [shitagaki-lab/see-through](https://github.com/shitagaki-lab/see-through) | 固定df019de5，与CORE023已经锁定的版本相同；RGBA补全/语义拆层、伪深度，作者明确不包含rigging | P2沿用既有资产候选轨道，不重开来源研究。现有62张真实源层优先；CORE023官方推理因匿名ZeroGPU配额失败，仍没有PSD结果 |
| [SparcAI-Inc/Bunraku](https://github.com/SparcAI-Inc/Bunraku) | 固定b9cc7904，递归tree只有readme.md；论文/项目演示可读 | 暂作研究方向，当前核对的仓库没有可执行推理/训练代码，不能视为可下载即跑的生产方案 |
| [JudyZZ/threejs-parallax-skill](https://github.com/JudyZZ/threejs-parallax-skill) | 固定2e9e083c；PlaneGeometry叠层、鼠标平移、renderOrder，明确depthWrite=false、depthTest=false | 排除为角色深度方案；可用于背景/卡片视差，不用于证明自然转头或遮挡完成 |

## 核心限制

1. 当前[Three.js OITPassNode文档](https://threejs.org/docs/pages/OITPassNode.html)仅把NormalBlending且无transmission的透明材质纳入OIT。它是当前文档中的TSL方案；本地锁定r180包没有对应文件。不能因为搜索到新API就改依赖版本或宣称可直接导入。
2. 加权OIT对颜色与透明度作近似，追求原画逐像素还原时必须先比较。当前11项Multiply依赖前序可见背景、25项逻辑pass含明确晚画，不能统一改为无顺序近似混合。
3. Depth peeling按几何深度分离片元，也不能自动知道艺术覆盖例外。重复透明几何、共面、epsilon、有限剥层数量与性能均需实际像素测试，不能把demo存在当成角色集成通过。
4. 通用skill中的sRGB/线性颜色、tone mapping、ShaderMaterial模板只对其声明的管线成立。现有默认原画合同是固定原始RGBA算术及effective RGB量化；保持旧CPU/浏览器阈值，再决定明确的颜色空间变更。
5. 伪深度、绘制顺序和约束膨胀分别是候选依据，不是实测物理深度。原生raw yaw也不是物理角度。

混合方程依据[W3C Compositing and Blending Level1固定2024-03-21版本](https://www.w3.org/TR/2024/CRD-compositing-1-20240321/)。透明排序的基础限制参照[Three.js官方透明说明](https://threejs.org/manual/pages/transparency.html)。

## 接下来具体怎么用

1. M2B1B先固定读取上述r180深度示例的index.js/index.html，仅提取可重分配深度纹理与render target管理方式。用本地three依赖和程序化测试卡片，避免引入机器人/无人机资产及其PBR/色调映射默认设置。
2. 对照三个路径：错误关闭depth-test；现有有序Normal/Multiply加有效alpha核心深度；显式有限层数depth-peeling。测试卡片有透明孔和半透明边缘，前后提交顺序故意反转，独立计算预期RGB/alpha。记录GPU draw、剥层预算、耗时及真实反例。
3. 当前原画有序合成保留为基准。只有有实际反例证明普通深度路径不足时，才扩大depth-peeling集成；WBOIT仅比较其误差，不默认成为生产替代。
4. 参考Cubism遮罩上下文分离，结合已锁定Inox原生Composite方程，明确艺术覆盖与原生语义差异；不混用不同模型体系的遮罩定义。
5. fixture成功后再接入19接收面/62来源/25逻辑pass，并复跑旧默认四图、alpha/ID、M2B1A眼动和人工查看。旧阈值不放宽，实际下载干净CI证据后才讨论M2B总验收。
6. M2B通过后，M3的第二组曲面方案优先研究Monster Mash的膨胀/深度约束与ARAP；是否采用取决于有限原生姿态下鼻眼/轮廓残差和实际转头画面。已有See-through配额失败保留历史状态，不冒充新完成的资产生成。

这次检索调整的是复用顺序与实现依据，没有改变已验收范围，也没有把“找到skill/论文”计入目标完成度。

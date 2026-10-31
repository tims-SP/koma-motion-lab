# M2-A2：只实现core025.js

只创建experiments/reference-factory/core025.js，建议≤350行。不要写捕获程序、QA或新传输格式；不要读SDK/旧引擎源码；不安装、不联网、不委派、不后台、不提交。M1已真实通过，A1已提供config/core025-render.json及HTML。

先读config和CORE-025-M2-split-orders.md的固定API，再集中写文件。原M2目标及数值门槛不变。

1. import Three.js。fetch config及其source_assembly，检查响应ok、canvas1630及62层。逐层使用source_texture.file / clean_texture.file的PNG（URL='/' + file），THREE.TextureLoader。设置NoColorSpace、premultiplyAlpha=true、flipY=true、LinearFilter、generateMipmaps=false；不做bin打包、Python解码、额外依赖或备选方案。
2. A1的HTML已有canvas#stage，必须传入 `canvas: document.getElementById('stage')` 复用该节点，不再添加第二张canvas。全局ColorManagement.enabled=false；WebGLRenderer({canvas:stage,antialias:false,alpha:false,preserveDrawingBuffer:true})，DPR1，NoToneMapping，outputColorSpace=LinearSRGBColorSpace。RawShaderMaterial直接输出源sRGB数值，不加colorspace转换/光照，不再次对已预乘的纹理RGB乘alpha。
3. 每层bounds上建格距≤12源像素的规则三角网格。X=(sx−815)/815，Y=(815−sy)/815，UV=[(sx-left)/width,1−(sy-top)/height]，Z=h(X,Y)+order*0.001。h公式严格按原M2工单和config：a1*exp(-(X/sx1)^2-((Y+yoffset1)/sy1)^2)+a2*exp(-(X/sx2)^2-((Y+yoffset2)/sy2)^2)。为每个几何保留curved与flat(order*0.001)坐标缓存。总共62个共享geometry，两版本重复使用，不复制成124几何。
4. 每版本每层两个mesh：opaque core alpha≥0.9999，写depth且不混合；soft fringe 0<alpha<0.9999，depthTest=true、depthWrite=false、NormalBlending、premultipliedAlpha=true。shader互相discard另一部分。按原order确定软边顺序。两版本分别124个绘制mesh，场景缓存248个mesh，但只激活选中的版本。所有部件在共同head group。
5. 固定正交相机按config初始化，看原点。render(opts)严格验证version/source|clean、yaw[-15,15]有限、depth/curved|flat、background/white|black、pass/beauty|silhouette|part_id|wireframe、size/640|1630。修改head的Y旋转，切换几何缓存和材质pass，设置canvas尺寸，实际renderer.render后返回split-order规定的矩阵、landmarks和计数。不要移动相机或对整图做CSS变换。
6. beauty用纹理预乘RGB；silhouette用vec3(alpha)；part_id用确定的每层颜色乘alpha；wireframe启用材质wireframe并保留alpha裁剪。opaque core输出alpha1；fringe保留实际alpha。纹理读取和材质属性必须一致，避免双预乘。
7. 按config的7个source_xy和所属order算局部XYZ、经过head矩阵变换后world_xyz，再用固定camera投影得到pixel_xy；声明NOT_VISIBILITY_TESTED。返回camera_matrix/projection_matrix/group_matrix均为真实column-major数组。
8. 实现exportGeometry，返回split-order固定schema，positions必须来自canonical CURVED缓存，不能取最后flat渲染状态。实现metadata实际Three revision/renderer/计数/PNG transport/DERIVED_REFERENCE。
9. 所有124张PNG准备好后初始化clean、0°、curved、white、beauty、1630，再设置core025Ready=true。不做requestAnimationFrame动画循环，输出canvas不叠标签。异常记录core025Error并抛出。
10. 仅运行 `node --check core025.js` 做语法检查。浏览器执行由下一B工单负责，不要在本工单自行发明capture或QA。完成汇报实际文件和syntax exit，不声称GPU通过。

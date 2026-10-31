# M2拆分执行：目标与门槛不变

上一大工单的执行进程已无法查询，本地无core025.js/capture/qa/config输出，也没有GPU验收结果。当前以M1提交f44b669恢复，M2仍IN_PROGRESS；不把规划日志当代码完成。

M2目标、公式、源图保护与门槛沿用CORE-025-M2-mcode-order.md。拆分为以下小任务，每次仅创建明确文件，依次或按无文件依赖的范围执行：

1. A1只创建config/core025-render.json与core025.html，配置静态核对后保存检查点；此时尚无渲染结果。
2. A2只创建core025.js，加载62层PNG，生成62个共享几何、source/clean两组两pass材质，实现下述固定API。使用THREE.TextureLoader直接读M1的PNG；不新增bin传输格式/解码程序/依赖。
3. B只创建capture_core025.mjs，按固定API捕获anchors并真实运行。
4. C只创建qa_core025.py，独立读取实际结果并执行原门槛；失败明确返修。通过后写M2结果并提交。

## 固定API（A2和B共同遵守）

`window.core025Ready=true`表示纹理和场景完成初始化。

`window.core025.render({version,yaw_deg,depth,background,pass,size})` 同步渲染并返回：

- camera_matrix/projection_matrix/group_matrix：Three.js column-major的16数数组；
- landmarks：以name为键，值含source_xy、world_xyz、pixel_xy及visibility=NOT_VISIBILITY_TESTED；
- geometry_count=62，active_draw_mesh_count=124。

`window.core025.exportGeometry()`返回 `{canvas:[1630,1630],layers:[{order,name,bounds,positions,uv,indices}]}`；positions为未旋转的canonical curved几何，不能因最后一次flat消融而输出平面数据。每数组为普通JSON数字数组。

`window.core025.metadata`包含three_revision、renderer、geometry_count、active_draw_mesh_count、transport=PNG、authority=DERIVED_REFERENCE。共享62个geometry；两版本可缓存248个mesh对象，但每次只激活一组124个draw mesh。

## 固定捕获manifest（B和C共同遵守）

out/core025/render/manifest.json结构：

`{schema,inputs:{assembly_sha256,config_sha256,scene_sha256,capture_sha256},environment,geometry:{file:"geometry.json",sha256},captures:[{id,file,params,sha256,repeat_sha256,pose}]}`。

id任意但必须唯一，QA用params选中截图，不依赖猜测文件名。file相对render目录；pose为render的真实返回值。4张0°截图必须有repeat_sha256，其他截图可为null。保存真实PNG哈希和当前输入文件哈希。

captures包括：source/clean各white/black的0°beauty；clean curved −15/0/+15分别beauty、silhouette、part_id、wireframe；clean flat +15 beauty。各截图size1630；silhouette用black，其余用white。共17个capture条目，不以重复截图凑数量。

捕获文件只含canvas，不叠UI标签；审阅拼图另做。页面自身不做动画循环，连续视频另由M3逐帧驱动。

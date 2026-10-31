# CORE-026 M1：默认坐标对应与首轮真实参考

日期2026-10-31。状态：62部件默认源坐标对应PASS；真实原生9姿态捕获/哈希/目视PASS；高清细部参考、19特征与接收/遮挡约束尚待完成，M1整体未放行。

## 默认坐标对应

源像素对应沿用已验收M1A：58项唯一、4项重复。监工编写并实际运行verify_core026_registration.py，直接读取原始UV、网格顶点、纹理尺寸/透明边距及完整祖先scale/Rz/translation；不会把zsort当真实深度。

只有58个唯一纹理部件参与估计一次全局偏移，实际worldXY-sourceXY中位数为[-896.9999934,-2587.999977]，所有参与顶点残差中位数0.707131源像素、最大3.905123源像素。未逐部件拟合移动来消除误差。原UV、原图均未修改。

用上述同一个偏移区分4个重复画片：

| PSD order | 选择的原生UUID | 正确候选偏移误差/源像素 | 错误候选偏移误差/源像素 |
|---:|---:|---:|---:|
| 7 | 1625707572 | <0.001 | 56.000 |
| 8 | 4212602175 | <0.001 | 56.000 |
| 9 | 1096045651 | 0.707 | 69.502 |
| 10 | 4217689816 | 0.707 | 68.502 |

62个部件最终对应62个不同原生UUID。原来的raster-only配置保持4项UNRESOLVED，因为仅靠重复纹理确实不能确定；新增default-registration.json用独立空间证据选择实例，不回写伪造的raster唯一性。文本摘要在evidence/core026-M1/default-registration-summary.json；完整顶点坐标只在ignored out中，可由脚本复现。

职责：mcode注册程序尝试未产出可验收文件，不计为完成；该程序属于Codex独立源坐标验收。它不实现新渲染器、不恢复3D，也没有据此接受HeadYaw动态GPU对应。

## 首轮真实原生CI

- 代码512d3f2ea51b85ce38062bd7956fa80ee23eb073。
- [Actions 41116198599](https://github.com/tims-SP/koma-motion-lab/actions/runs/41116198599)，job124270963962，全部步骤success。
- [Owner-only Draft Release](https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-a5e625495c0e1b679d8c)，真实归档步骤成功并返回URL；CORE026-native-reference.zip与SHA256SUMS.txt。
- 9个raw yaw=-1到+1，pitch raw0，原生完整模型/完整头部，固定相机scale0.15、位置0；dt0不代表物理平衡。
- Codex从真实CI日志取回无损审阅ZIP，SHA b2eda609c31ea96cbd189c076137f48524321c6c3b6488e3d4c0575b712e8303；实际1396800字节。
- 独立读取9张720×880 PNG，对照最终manifest的9项full SHA全部一致；从每张原PNG按固定ROI重裁，9项head SHA也全部一致。9个头部像素指纹均不同。
- 实际看了9姿态接触图：两耳与完整头部存在，眼/脸缘/头发出现连续相对变化；只能作为有限的原生2D运动约束，不能标定物理±15°或宣称3D自然转头。
- 两个既有工厂回归run41115461156、41116198362均实际success，CORE025的艺术FAIL保持不变。

源证据在evidence/core026-M1/first-native-ci-acceptance.json。媒体未加入git或Actions artifact；只在ignored out和Draft Release。

## 下一准确步骤

首轮全身视图中的头部宽约150像素，不足以精确校准小部件。mcode已增加--head-view Python捕获选项，源补丁通过环境变量选择固定相机scale0.4、位置[82,1773]；该值依据原生camera.matrix的加法平移和上面的统一默认坐标估计，未改变任何原始网格/UV。完整画布720×880中固定ROI[34,114,686,766]得到652×652头部图，所有姿态相同。

高清模式实际源补丁、py_compile、--help与YAML检查通过；mcode因步数限制退出不算它已执行GL。接下来由真实CI验证高清捕获，监工检查裁切/纹理/19特征，再完成局部接收与遮挡约束。M2尚未开始。

# M2-C：只实现并运行qa_core025.py

**当前验收入口已改为监工独立实现** `verify_core025_supervisor.py`，真实17图已运行PASS。mcode的C编写尝试超时、无可验收文件；不再等待其自动评分脚本。保留本文件作为原始门槛记录，实际恢复命令以docs/STATUS.md为准。场景/捕获仍由mcode实现。

依赖真实17张anchors截图/manifest/geometry.json已由B产生。只新建experiments/reference-factory/qa_core025.py，建议≤250行；输出out/core025/render/qa.json和review-sheet.png。仅用既有Python/NumPy/Pillow，不安装、不联网、不委派、不后台、不改阈值、原图、场景或M1、不git提交。

独立从磁盘读取实际JSON/PNG；不要import场景实现或用配置值代替实测。读取split-order规定的固定schema，按capture.params选择截图；源像素参考取assembly.comparisons[version].cpu_composite.file。ROOT=自己的文件所在reference-factory目录。

1. 验证manifest中assembly/config/scene/capture及geometry SHA与当前实际文件一致，验证17张PNG的SHA与尺寸1630一致。全部数字有限，id唯一。四个0°front条目repeat_sha256必须与sha256相同。
2. geometry.layers必须62项，order唯一1..62，name/bounds匹配assembly。position长度能组成N×3、uv组成N×2、indices为合法整数三角索引，所有值有限。每层实际边界须包含原bounds四边。
3. 实际XY反推sourceX=815+815*X、sourceY=815−815*Y，与UV重建的left+u*width、top+(1−v)*height比较，最大误差≤0.001源像素。Z与config指定h(X,Y)+order*0.001最大误差≤1e−5世界单位。
4. Face(order13)内部Z范围>0.02；中心化XYZ做SVD拟合最佳平面，最大点到平面距离>0.005。记录真实值，证明不是只有层偏移的平面卡片。
5. 选source/clean各white/black的0°curved beauty图，共4张，与对应M1透明CPU参考按同底合成后比较。前景=CPU alpha>0；RGB MAE≤1.0/255，任一通道差>16的像素比例≤0.001。记录最大误差与尺寸，不放宽阈值。CPU全透明区域也记录背景误差，防止新杂色。
6. 所有实际camera_matrix和projection_matrix保持固定；将column-major group_matrix按Fortran顺序reshape，核对是请求角度的+Y旋转矩阵，元素误差≤1e−6。从实际pose.landmarks.pixel_xy比较clean curved+15与flat+15，换算640尺寸后的平均位移>0.5px，两图片哈希不同。
7. 输出qa.json：每项硬门禁的实测/阈值/结果、失败清单、overall数值门禁状态、visual_gate=NOT_REVIEWED、production_gate=NOT_ACCEPTED。失败必须非0退出；不能因某图缺失跳过该门禁。
8. review-sheet.png包含0°source参考/GPU/差异×8、0°clean参考/GPU/差异×8、clean −15/0/+15 beauty、clean −15/0/+15 wireframe。逐格标注放在图片外，不覆盖角色，不拉伸宽高比。
9. 实际前台运行python qa_core025.py，保留真实exit。若失败，反馈具体门禁与实际值，不改A2/B或降低阈值。目视检查由监工完成，本工单不能自行把visual_gate置PASS。

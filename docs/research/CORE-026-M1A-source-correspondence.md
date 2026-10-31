# CORE-026 M1A：源像素对应验收

日期2026-10-31（Asia/Shanghai）。mcode已通过官方CLI登录成功并完成源审计返修；此前be21250中的认证阻塞为历史启动记录，当前已解除。

本子项PASS，M1整体尚未完成，深度/遮挡修正尚未实现。

## 实际执行与独立复核

mcode实现audit_core026.py和core026-part-correspondence.json；Codex独立编写verify_core026_supervisor.py，并实际运行：

1. python audit_core026.py --audit：exit0，62层、58个唯一对应、4个未解决。
2. python audit_core026.py --verify-source：exit0，SOURCE_ONLY_PASS，0问题。
3. python verify_core026_supervisor.py：exit0；独立重读完整INX内嵌TGA与186张PNG、冻结的10个旧源码/配置/锁文件；58条mcode已验证记录均获独立像素支持。

原始PSD、INX、VRM哈希保持正确。实际Head:: Yaw-Pitch min[-1,-1]、max[1,1]、defaults[0,0]、轴9×3和114绑定均核对通过。

## 实际发现

不能直接比较原始RGBA文件字节：INX纹理使用预乘RGB，PSD原始层为straight RGB。裁到alpha>0范围后，62层的alpha逐像素完全一致；round(PSD_RGB*alpha/255)与INX_RGB在可见像素最大差均<=1，未翻转、镜像、缩放或只取不透明内区。

58层对应唯一的真实纹理所有者UUID。PSD中的左右标签与INX的角色左右标签相反；例如PSD order1 Fox: Ear L实际匹配Ear:: Right UUID3453251657。继续沿用同名配对会接错耳朵/眼睛。

4项仍为UNRESOLVED：order7/8共享native texture49/54的相同画片，order9/10共享texture48/53的相同画片。均保留两个实际候选；后续必须用位置、祖先变换和绑定区分，不能用像素重复证据假装唯一绑定。

本次VERIFIED只表示raster-content identity，所有记录spatial_registration=NOT_TESTED。没有因此接受原生网格与PSD坐标的配准，也没有把原生yaw转换成物理角度。

## 恢复与下一工作

机器证据在experiments/reference-factory/evidence/core026-M1/。M1A可重复运行上述3命令。真实9姿态、19特征槽位与局部接收/遮挡关系仍待M1后续完成；M1门禁尚未放行，不进入盲调Z。

正在检查原生捕获的新工作流与辅助程序，修正路径和归档契约后运行真实CI；媒体只存ignored out与owner-only Draft Release。

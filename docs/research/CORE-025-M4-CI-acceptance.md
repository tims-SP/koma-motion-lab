# CORE-025 M4：干净环境复现与归档

日期2026-10-30。代码提交：`c876100f6c0eea0623e3cbb60e06152b86d1b472`。

- [Actions run 41084893009](https://github.com/tims-SP/koma-motion-lab/actions/runs/41084893009)，job124163345904，全部步骤success。
- [Owner-only Draft Release](https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-38eb4ff6aa4c88363e39)：CI归档步骤真实成功并返回该URL。文件名CORE025-layered-turn-evidence.zip，另附SHA256SUMS.txt；源/派生图片、几何、原始97帧、视频及解码审阅图保留在该包内。Git与Actions artifact只存文本证据。
- mcode实现/修改场景、捕获、CI和恢复说明；Codex监工独立编写数值验收/编码解码程序，并看实际Work解码图。没有把mcode超时或未完成的尝试算成通过。

## 实际通过项

49个回归测试（3.211秒）；锁定原始来源获取；62原生层导出；M1默认姿态合成/阴影裁剪；M2真实17图、曲面/UV/矩阵与同进程重复；M3真实97帧、固定相机、0°回程、H.264编码/ffprobe计数和13张解码抽帧；原有45结构图独立进程重复及视频检查。

CI四项0°RGB MAE与Work一致，分别为0.04887765、0.04891336、0.04247065、0.04246367（0..255数值域）；最大通道差2，>16比例0。UV反推最大误差0.00004828源像素。

CI M3引用的M2完整manifest SHA为`af703c0b78304b0ef9a101ea3a31a4635bb3c23b2f328bc2465282c3224dbe77`，与本次Work捕获的完整manifest一致。这是这两个环境样本间的实测结果，不声称任意平台普遍字节确定性。

CI视频H.264、640×640、24fps、97帧、4.041667秒，438568字节，SHA`dc428ec847c318bd09021b7d63756697c2f93725e9f2e51d64fd6a529a6b5df2`；Work版本444005字节，SHA`e5b91cb05797eb5f255c59e4577f31744807dce00b8fd36b21dab04cf3a08e19`。不同编码环境的MP4字节不同，没有把视频哈希相同当成门禁。

机器验收证据：experiments/reference-factory/evidence/core025-M4-2026-10-30/ci-acceptance.json。

## 明确不通过项

**艺术级转头FAIL、生产NOT_ACCEPTED。** Work版13张真实解码抽帧和局部图已目视检查，当前更像浅表面视差摆动，面部仍过于正面。CI复现数值链路不会自动推翻该视觉判断。完整Inochi默认姿态、全局闭合UV、侧背素材、骨骼蒙皮、IK及360°未验收。

本轮完成的是可复现、可恢复的原型与诚实的质量判定；下一轮应先校准逐部件头型和遮挡，而不是继续扩大角度并把它称为自然转头。

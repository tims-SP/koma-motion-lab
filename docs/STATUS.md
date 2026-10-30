# 当前恢复入口

## 目标与分工

当前分支 `feature/koma-25d-core-021`；mcode执行，Codex下工单、验收与提交。CORE-025复现与归档已完成，艺术门禁FAIL保留；当前启动CORE-026分部件深度、附着与遮挡校准。详细[CORE-026计划](plans/CORE-026-depth-and-occlusion-plan.md)与[首项M1工单](plans/CORE-026-M1-mcode-order.md)。M1启动源检查PASS，mcode两次执行均exit3要求重新登录，当前BLOCKED_AUTH；M2–M5尚未执行。

## 已完成

- CORE-024：提交 `494d50b01c7594d631c5a93da0dd469f44b5dbb8`；CI run 41043343409通过。原生62层导出像素一致；侧脸C的W245仅临时抠图预览。
- 全量资产生成尚未完成；侧面拆层、背面、连续UV与生产绑定仍未验收。

## 当前任务

- CORE-025-M1：PASS（默认姿态组装与指定9层阴影裁剪，限原型）。[监工验收](research/CORE-025-M1-supervisor-acceptance.md)：source白底MAE0.125177/255、黑底0.144745/255，独立Pillow复合最大差1色阶；49测试及真实准备均exit0。保留颈部源图软边和微小游离片段为待修整项。
- CORE-025-M2：数值/映射原型PASS。A1配置、A2场景、B真实17图均完成；实际C入口为监工独立编写的verify_core025_supervisor.py，真实运行PASS。mcode的旧C编写尝试未产出可验收文件，不计为完成。
- M2实际0°四种MAE<0.05/255，62个非平面几何、UV/公式/矩阵/哈希均PASS。[监工报告](research/CORE-025-M2-supervisor-acceptance.md)。艺术级转头仍NOT_ACCEPTED。
- CORE-025-M3：97帧/24fps/4.041667秒H.264已真实生成并解码抽检，数值链路PASS；**艺术级转头FAIL**，主要仍像浅表面摆动。[目视与数值报告](research/CORE-025-M3-supervisor-acceptance.md)。实际入口为capture_core025_video.mjs与监工verify_core025_video.py。
- CORE-025-M4：PASS（数值复现/归档）。[Actions 41084893009](https://github.com/tims-SP/koma-motion-lab/actions/runs/41084893009)对代码提交`c876100f6c0eea0623e3cbb60e06152b86d1b472`实际复现全部流程；49回归、M1重建、17图、97帧编码/解码与45图独立进程复现均通过。[Draft Release](https://github.com/tims-SP/koma-motion-lab/releases/tag/untagged-38eb4ff6aa4c88363e39)已归档原始来源与媒体。**艺术级转头FAIL保持不变**。

## 干净环境恢复

```bash
git checkout feature/koma-25d-core-021
cd experiments/reference-factory
python -m pip install -r requirements.txt
npm ci --no-audit --no-fund
npx playwright install chromium
python prepare.py
python native_layers.py
```

然后运行 `python prepare_core025.py` 重建M1，再依次执行 `node capture_core025.mjs --anchors`、`python verify_core025_supervisor.py`、`node capture_core025_video.mjs`、`python verify_core025_video.py`。本地已有源码缓存时不重新下载模型或请求生图。所有媒体在out/和Draft Release，git只存文本。

M1检查点提交：`f44b669add0dd425b3848667fbfac71121f613a7`。对应Actions run 41048675339已通过49个回归测试及既有结构工厂；完整M1/M2/M3干净环境流水线接入仍属于M4，不能把旧工厂归档当成CORE025转头成品。

若后续编辑时执行环境丢失登录，使用官方 `mcode login --region cn --no-browser` 启动授权；不读取认证文件，不将授权码/URL/令牌放进git。已有代码的确定性复现不需要mcode或模型登录，直接执行上面的恢复命令；A1至M4已经完成，不从A1重新开工。

## 本轮结束时的恢复位置

CORE-025执行链路已跑通并归档，不重跑A1、不重新生成源资产。详细[干净环境验收](research/CORE-025-M4-CI-acceptance.md)及[M3视觉失败与下一任务](research/CORE-025-M3-supervisor-acceptance.md)。后续重点为经过可靠斜面/原生形变对照的逐部件头型深度与遮挡校准；侧背、骨骼蒙皮、IK和360°仍未完成。

2026-10-31：已保存CORE-026规划及明确M1工单。恢复后先审计原生raw yaw/pitch与62层对应，再真实捕获9个完整头部姿态；旧ear-only证据不能当全头参考。M1通过后才实施分部件接收曲面/局部合成、A两组深度与必要的B形变残差。当前实现/捕获均NOT_TESTED，不把计划当成完成。

最新[启动检查](research/CORE-026-M1-start-preflight.md)：原始哈希、62层、11Multiply、9裁剪与实际原生114绑定已由监工验证；mcode认证阻塞发生在实现开始前。官方登录完成后重发M1 A/B子工单；不重跑CORE025，不越过M1进入盲调深度。

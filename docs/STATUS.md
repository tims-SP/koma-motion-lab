# 当前恢复入口

## 目标与分工

当前分支 `feature/koma-25d-core-021`；mcode执行，Codex下工单、验收与提交。目标为CORE-025：原生62部件的前视复原与±15°轻量曲面转头。详细步骤见[执行计划](plans/CORE-025-execution-plan.md)。

## 已完成

- CORE-024：提交 `494d50b01c7594d631c5a93da0dd469f44b5dbb8`；CI run 41043343409通过。原生62层导出像素一致；侧脸C的W245仅临时抠图预览。
- 全量资产生成尚未完成；侧面拆层、背面、连续UV与生产绑定仍未验收。

## 当前任务

- CORE-025-M1：PASS（默认姿态组装与指定9层阴影裁剪，限原型）。[监工验收](research/CORE-025-M1-supervisor-acceptance.md)：source白底MAE0.125177/255、黑底0.144745/255，独立Pillow复合最大差1色阶；49测试及真实准备均exit0。保留颈部源图软边和微小游离片段为待修整项。
- CORE-025-M2：BLOCKED_AUTH。上轮执行会话不可查询且未留下曲面代码；2026-10-30重试时mcode CLI明确要求登录。已启动官方中国区授权，授权信息只在会话中展示，不写入仓库。M1已完成提交不受影响。
- M2恢复后按[拆分工单](plans/CORE-025-M2-split-orders.md)执行：[A1固定配置与HTML](plans/CORE-025-M2-A1-setup-order.md)→[A2场景](plans/CORE-025-M2-A2-renderer-order.md)→[B捕获](plans/CORE-025-M2-B-capture-order.md)→[C独立QA](plans/CORE-025-M2-C-QA-order.md)。M2当前没有已验收代码或截图；不得把规划日志计为实现。
- CORE-025-M3/M4：TODO，分别为连续转头抽帧、Actions复现与Draft Release归档。

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

然后运行 `python prepare_core025.py` 重建M1。M2实现完成前不声称有转头视频。本地已有源码缓存时不重新下载模型或请求生图。所有媒体在out/和Draft Release，git只存文本。

M1检查点提交：`f44b669add0dd425b3848667fbfac71121f613a7`。对应Actions run 41048675339已通过49个回归测试及既有结构工厂；完整M1/M2/M3干净环境流水线接入仍属于M4，不能把旧工厂归档当成CORE025转头成品。

若执行环境丢失登录，使用官方 `mcode login --region cn --no-browser` 启动授权；不读取认证文件，不将授权码/URL/令牌放进git。授权恢复后先让mcode完成A1两个小文件，再依次执行上述文件工单。M3/M4明确工单也已保存。

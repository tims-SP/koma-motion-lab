# 当前恢复入口

## 目标与分工

当前分支 `feature/koma-25d-core-021`；mcode执行，Codex下工单、验收与提交。目标为CORE-025：原生62部件的前视复原与±15°轻量曲面转头。详细步骤见[执行计划](plans/CORE-025-execution-plan.md)。

## 已完成

- CORE-024：提交 `494d50b01c7594d631c5a93da0dd469f44b5dbb8`；CI run 41043343409通过。原生62层导出像素一致；侧脸C的W245仅临时抠图预览。
- 全量资产生成尚未完成；侧面拆层、背面、连续UV与生产绑定仍未验收。

## 当前任务

- CORE-025-M1：IN_PROGRESS，执行[明确工单](plans/CORE-025-M1-mcode-order.md)。尚无通过声明。
- CORE-025-M2/M3/M4：TODO，分别为Three.js前视/曲面、连续转头抽帧、Actions复现与Draft Release归档。

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

M1脚本提交后再增加其运行命令。本地已有源码缓存时不重新下载模型或请求生图。所有媒体在out/和Draft Release，git只存文本。

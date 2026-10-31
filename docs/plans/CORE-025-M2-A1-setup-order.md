# M2-A1：只创建固定配置与HTML

执行mcode；监工Codex核对并保存。读AGENTS.md后直接写以下2文件；不推演场景、不创建JS/捕获/QA、不安装/联网/委派/后台/git提交。

## 1 config/core025-render.json

路径在experiments/reference-factory内。精确写入以下有效JSON：

```json
{
  "schema": "koma-core025-render/1",
  "source_assembly": "/out/core025/assembly/assembly.json",
  "canvas": [1630, 1630],
  "center": [815, 815],
  "grid_step_px": 12,
  "depth": {
    "a1": 0.12, "sx1": 0.75, "sy1": 0.85, "yoffset1": 0.10,
    "a2": 0.02, "sx2": 0.15, "sy2": 0.15, "yoffset2": 0.28,
    "layer_offset": 0.001
  },
  "camera": {
    "left": -1, "right": 1, "top": 1, "bottom": -1,
    "near": 0.1, "far": 20,
    "position": [0, 0, 5], "target": [0, 0, 0]
  },
  "alpha_core_cut": 0.9999,
  "yaw_range": [-15, 15],
  "sizes": [1630, 640],
  "versions": ["source", "clean"],
  "anchors": [
    {"name": "nose", "order": 21, "source_xy": [815, 1040]},
    {"name": "eyeL", "order": 28, "source_xy": [660, 1000]},
    {"name": "eyeR", "order": 38, "source_xy": [960, 1000]},
    {"name": "earRootL", "order": 1, "source_xy": [550, 700]},
    {"name": "earRootR", "order": 2, "source_xy": [1070, 700]},
    {"name": "neck", "order": 11, "source_xy": [810, 1400]},
    {"name": "leaf", "order": 62, "source_xy": [780, 480]}
  ]
}
```

## 2 core025.html

同在reference-factory根目录：HTML5、UTF-8、标题CORE-025 layered surface prototype、body margin0、canvas display:block；module script的src为/core025.js。可使用data:,作为favicon。禁止叠在canvas上的标题/工具条/水印；禁止CSS对canvas约束max-width或缩放。

## 3 静态核对

Python读取JSON，检查canvas、depth.layer_offset及7个anchors字段等于上述值。汇报两个真实文件与parse exit0即可；JS尚未创建，不能声称已渲染。保存检查点后再执行A2明确工单。

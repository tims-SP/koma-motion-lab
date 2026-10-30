# CORE-025-M1 / mcode执行工单

先读根AGENTS.md及CORE-025-execution-plan.md。本工单为明确实现要求；执行代码由mcode编写，Codex独立验收和提交。禁止委派、安装依赖、模型/生图请求、访问认证文件、git提交/推送。使用现有python/NumPy/Pillow/psd-tools。禁止后台任务和用tail掩盖退出码。最多32步；集中写文件，避免逐行反复edit。

## 允许新建的文件

- `experiments/reference-factory/prepare_core025.py`
- `experiments/reference-factory/config/core025-layer-contract.json`
- `experiments/reference-factory/tests/test_core025_blend.py`
- `docs/research/CORE-025-M1-results.md`
- 输出仅写 `experiments/reference-factory/out/core025/assembly/`。

不要修改CORE-024及更早代码、原图、依赖锁。只实现本工单M1，不先写M2浏览器代码。

## 步骤1：验证真实输入

项目根目录 `/workspace/scratch/9cd8ec77aca4/koma-motion-lab`。脚本ROOT必须是自己的文件所在目录，即experiments/reference-factory。读取其out/source/tutorial-aka.psd，核对sources.lock.json及固定SHA `979fa62702b25f8af25414637d9ba6c36cbc9eb03bfa0c454470c73bdf51e55e`。读取out/core024/native-v2/native-export.json与layers；与实际PSD SDK重新枚举叶层和topil()核对62/62名字、顺序、bounds、RGBA一致。任何错位、漏层或输入哈希不符：非0退出。当前源只支持NORMAL/MULTIPLY、opacity255、无mask/clipping；遇到不支持的源属性必须报错，不能静默忽略。

## 步骤2：固定部件合同

config/core025-layer-contract.json 写入schema、PSD哈希、canvas[1630,1630]、源坐标为像素EDGE/像素中心i+0.5、默认顺序bottom-to-top、source/clean版本说明。列出62层的order/name/原始bounds/原始blend/semantic_family，禁止只写模糊的自动分类说明。

semantic_family明确规则：1–2 ear；3–10 rear_hair；11–12 neck；13–20 face_base；21 nose；22–23 mouth；24–33和58 left_eye；34–43和59 right_eye；44–47 side_hair；48–57 front_hair；60–61 eyebrow；62 leaf。

clean修整只允许9层阴影alpha乘以指定基础层的alpha（按全画布正确对齐）：6→5，12→11，14/15/16/17/18/19/20→13。60/61眉毛仍按multiply合成，禁止当作外溢阴影裁掉。保留source版本所有原始alpha，不能覆盖源文件。

## 步骤3：实现有透明度的source-over及multiply

在NumPy浮点中，颜色0..1、非预乘Cb、Cs，背景alpha Ab、源alpha As：

normal时 `effective_source_rgb=Cs`；multiply时 `effective_source_rgb=Cs*(1-Ab+Ab*Cb)`。
`Ao=As+Ab*(1-As)`，`premult_out=As*effective_source_rgb+(1-As)*Ab*Cb`，`Co=premult_out/Ao`（Ao=0安全置0）。来源W3C compositing-1；本任务按PSD源的sRGB数值域合成，不经过光照或线性化。

将11层multiply转换成对默认下层等效的NORMAL纹理：RGB用effective_source_rgb量化round到uint8，alpha保留当前版本的As；NORMAL层RGB原样，alpha只允许9层clean阴影按上述合同修改。每层导出与原bounds同尺寸RGBA，写入 source/layers/ 与 clean/layers/，记录源PNG SHA与派生PNG SHA、原blend、baked_blend=NORMAL、默认下层依赖的局限。每一步CPU累积必须用实际导出的量化纹理重合成，以便后续GPU可以复现；不准用未量化浮点参考伪装导出贴图效果。

## 步骤4：输出CPU参考和测量

每个版本导出1630×1630 source-cpu.png/clean-cpu.png透明合成及白底、黑底、棋盘QA。创建 labeled comparison-sheet.png 与9阴影层修整前后的对照（可使用contact sheet）。从PSD重新 `psd.composite(force=True, alpha=0.0, color=(1,1,1))` 取SDK参考，不使用不透明缓存代替透明真值。

source-cpu在白底与黑底分别对SDK参考计算前景RGB MAE、最大单通道误差、>16像素比例；alpha计算MAE。前景=两图alpha>0的并集。M1数值门槛：两底前景RGB MAE各≤0.5/255，alpha MAE≤0.5/255；超限应原样报告FAIL并退出非0，禁止放宽阈值。

assembly.json记录62层完整metadata、两版本派生纹理相对URL、canvas、合成公式/数值域、source/clean权威级别、9层修改的像素数及alpha总和下降、11层multiply的烘焙说明。qa.json记录输入/输出哈希、全部数值、退出条件、source_composition_gate和clean_visual_gate=NOT_REVIEWED。后者由监工看图后决定，mcode不要代替目视验收。

## 步骤5：数学回归与真实执行

新增3个有独立预期值的unittest：半透明红normal覆盖半透明蓝→RGBA(2/3,0,1/3,0.75)；半透明红multiply覆盖半透明蓝→RGBA(1/3,0,1/3,0.75)；透明背景上multiply红应仍为红而非黑。测试调用实现函数，预期值直接写定，不用同一公式生成预期。

前台运行 `python -m unittest discover -s tests -p test_core025_blend.py -v`，然后 `python prepare_core025.py`。记录真实退出码。若FAIL先定位并修代码，不得静默跳过。实际结果与边界写中文短报告CORE-025-M1-results.md（避免凭空填写画布尺寸）。完成后列出实际修改文件和结果，不触碰其他阶段。

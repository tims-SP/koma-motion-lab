# CORE-026 M1B：真实原生参考捕获程序检查点

日期2026-10-31。状态：首轮真实原生CI及独立PNG哈希/目视检查PASS；新增高清模式等待真实CI验收，M1整体未放行。最新[实际参考与源坐标报告](CORE-026-M1-default-space-and-native-reference.md)。

mcode编写源补丁、原生捕获程序与工作流。Codex独立验收发现并修正集成契约问题：

- patch辅助移到experiments/reference-factory/tools/core026，统一工作流路径；日志artifact路径改为实际logs子目录。
- 上游原始clap CLI只有一个位置参数，即INX文件；移除mcode虚构的--inx/--head-yaw/--width等参数，姿态改由源补丁实际读取的KOMA_HEAD_YAW环境变量设置。
- 源INX严格按大端JSON段长度解析，递归统计真实节点；核验默认值、完整轴点及源补丁报告；移除真实ear-only环境变量。
- 实际X11截图尺寸异常时失败，禁止无声缩放后冒充原尺寸。
- 使用完整的renderer initialized标记、准确窗口名及窗口移动成功检查。
- 审阅ZIP在进程清理和最终manifest写盘之后创建，嵌入真实且完整的最终manifest字节，去掉占位副本；bundle哈希独立输出，避免自引用。
- 删除媒体Actions artifact；只有manifest、源补丁报告与实际原生日志进入文本artifact，PNG/ZIP媒体进入owner-only Draft Release。

独立实际检查：两个Python辅助py_compile、捕获程序--help、YAML解析、仅文本artifact与Draft语义检查通过。对缓存的锁定上游main.rs执行真实补丁，exit0，9处精确替换；确认保留完整渲染/物理初始化、固定720×880初始FBO、raw pitch0、相机scale0.15、dt0，未加ear-only过滤。dt0不代表物理平衡，原生参数不代表物理角度。

本地没有cargo/Xvfb，没有伪造本地GL成功。新工作流发布后通过限定分支/路径push触发编译和9姿态真实捕获；后续须检查实际退出码、PNG、接触图及文件SHA。完成前不得写自然转头或M1整体PASS。

M1A源对应已提交a6226cc。下一步：查看koma-26-native-reference.yml的实际run；失败先修复精确报错，成功后独立读取9姿态、固定默认配准、19特征槽位和接收/遮挡约束。

# M1第一轮返修：停止错误探针，直接实现既定公式

前次stream `out/core025-M1-stream.jsonl` 已由监工中止，CLI exit130；尚未实现任何M1正式代码，不能计为已完成。

监工已定位你 /tmp/probe_order.py 的错误，别再调查层序、ICC或猜测源PNG预乘：

1. acc_rgb 内存中是0..1的预乘RGB，a也是0..1，参考ref是0..255。
2. 因此白底参考表达式应为 `(acc_rgb + (1-a[...,None]))*255`，黑底是 `acc_rgb*255`。你写的 `rgb*a + 255*(1-a)` 同时多乘了一次alpha且混用数值单位，所以MAE164完全不能代表源图问题。
3. order1确为bottom，62确为top。ICC不存在。原始RGBA读取与bounds在CORE024已经真实核对，不必再试反转顺序，不必再做十轮探针。

继续按CORE-025-M1-mcode-order.md实现所有允许文件。先写blend函数及3个固定预期测试并真实执行，再写真实准备脚本。代码内统一0..1直到明确量化/输出比较时才乘255。累计缓冲可以用straight RGB+alpha或premult RGB+alpha，但变量名注明，禁止混淆。实际导出的NORMAL纹理重合成后再与SDK比。

当前没有 prepare_core025.py，你应直接创建，不要继续寻找。集中用完整文件写入，不要用大量read/bash探针耗尽步数。禁止后台任务/联网/安装/git提交。真实测试和脚本完成后再写报告，优先产出可验收代码。

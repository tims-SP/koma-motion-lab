# M2-B：只实现并运行capture_core025.mjs

依赖A2的core025.js已通过语法检查并保存。只新建experiments/reference-factory/capture_core025.mjs，建议≤180行；输出out/core025/render/。禁止修改场景、M1、配置或锁文件，禁止安装/联网/委派/后台/git提交。只支持一个明确参数--anchors；未知或缺少参数报错。

1. 复用既有capture.mjs中的Vite/Playwright启动方式。ROOT=本文件所在reference-factory目录。Vite绑定127.0.0.1:4175 strictPort。Chromium使用已装的headless浏览器、--no-sandbox、--use-angle=swiftshader、--enable-unsafe-swiftshader，页面1630×1630/DPR1。
2. 访问/core025.html，等待core025Ready为true（60秒）。收集pageerror、console.error、加载失败及HTTP≥400（可忽略favicon），任一实际错误使捕获失败。不要用静态PNG替代渲染。
3. 先获取core025.metadata，调用exportGeometry保存geometry.json。固定API和JSON结构见CORE-025-M2-split-orders.md；不要猜字段或改API。
4. 逐个调用render再canvas.screenshot：source/clean各white/black，yaw0、curved、beauty、size1630，共4张；每张同参数立即再渲染/截图计算repeat_sha256。重复PNG无需存盘，但记录真实SHA。
5. clean/curved/yaw−15/0/+15各捕获beauty、silhouette、part_id、wireframe；silhouette背景black，其余white，size1630，共12张。再捕获clean/flat/+15/white/beauty，合计17个条目。
6. 唯一id、文件名用ASCII；QA按params识别，不依赖文件名猜角度。每个条目保存{id,file,params,sha256,repeat_sha256,pose}，pose直接使用真实render返回值。所有图片是canvas截图，不加标签。
7. manifest.json按split-order schema保存实际输入assembly/config/core025.js/本捕获脚本SHA，environment=真实metadata+Node/Chromium版本，geometry文件SHA与17 captures。所有file相对render目录。不要写qa.json或任何质量PASS。
8. finally关闭browser与server。实际前台运行node capture_core025.mjs --anchors，保留真实退出码；失败保留日志并仅修捕获代码，若场景报错则原样反馈给监工，不悄悄修改A2。完成报告实际捕获数量/文件，GPU质量验收由C完成。

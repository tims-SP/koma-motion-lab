# A2运行前返修：只改core025.js的3处

已有场景代码已通过监工node --check。第一次实际捕获因当前Work缺少Playwright Chromium而未启动，监工正在恢复锁定浏览器；不能声称GPU通过。

只改experiments/reference-factory/core025.js，不动捕获、QA、配置或M1：

1. 当前main尾部只设置window.core025和core025Ready，没有实际初始渲染。在设置core025Ready=true之前，调用现有render：`render({version:'clean',yaw_deg:0,depth:'curved',background:'white',pass:'beauty',size:CANVAS});`。这样Ready意味着初始化渲染已真实发生。
2. FRAG shader的core/fringe互斥discard应作用于所有pass。移除uMode<2.5条件及wireframe只判断a<=0的特殊分支，统一：core且a<uAlphaCut时discard；fringe且(a<=0或a>=uAlphaCut)时discard。其余RGB计算不变，防止wireframe两个pass在软边重复覆盖。
3. DoubleSide材质设置forceSinglePass:true，保持原本opaque/fringe的depthTest/depthWrite/预乘语义不变。

集中一次修改，运行node --check core025.js，汇报真实exit。不要重新研究GLSL/alpha公式，不运行捕获、不安装、不后台、不委派、不联网、不提交。

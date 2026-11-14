# 执行与失败记录

1. 初始目录为空，不是 Git 仓库；`dotnet --info` 报 `zsh:1: command not found: dotnet`。克隆上游并将其作为当前仓库根目录，commit 固定为源码分析所记版本。临时安装官方 .NET SDK 10.0.404；无系统 SDK 或永久 PATH 修改。
2. 未安装 wasm-tools。实际 Debug build 和 Release publish 成功，采用预构建 runtime；保留 publish.log 的优化提示，不把它等同于 AOT 已验证。
3. PoC 初始 csproj 把 Compile Remove 放错 PropertyGroup，restore 报完整错误：
   `/Users/hocgin/Projects/_Web/imewlconverter-web/poc/wasm/WasmPoc.csproj(6,14): error MSB4066: The attribute "Remove" in element <Compile> is unrecognized.`
   已移至 ItemGroup。属于 PoC 文件语法错误，不是原引擎 WASM 兼容问题。
4. 初次自动化等待只看 Complete，Progress<T> 延迟消息可能覆盖最终状态；PoC 进度回调增加 `if (!busy) return`。矩阵脚本最初也曾读到尚未渲染的空结果而抛 `SyntaxError: Unexpected end of JSON input`，已改为等待对应 from/to 的非空 JSON 和按钮恢复。后续完整九项矩阵重新执行，未用该失败轮次宣称成功。
5. Firefox 首轮会话已建立，但脚本使用非标准 GET /session/:id 查询能力，返回 `RuntimeError: HTTP method not allowed`。改为读取 POST /session 返回的 capabilities，重启本次临时 driver 后完整重跑。是自动化脚本问题，不是转换问题。
6. Safari 用本机 safaridriver 27 创建 session，最终返回 session not created / finding or launching a compatible local Safari RWIApplication 超时。完整响应保存在 safari-session.json；未改动系统自动化权限，未通过 Chromium/WebKit 替身冒充 Safari 成功。
7. Firefox 初始未安装，随后从 Mozilla 官方下载 Firefox 160 到 /tmp，Geckodriver 0.36.0；SCEL 下载/高级测试/三档真实词库均完成。Geckodriver 日志的浏览器实验 featureId 和 sandbox_extension 提示没有阻止页面转换；页面错误数组为空。
8. 已知原引擎 Big5 内容错误：native/chromium/firefox 的相同检查均为 expected 中國、actual い瓣、correct false。没有将“无异常”记为正确。
9. 浏览器运行时确认 wasmEnableThreads=false；Zstd 存在 Thread.Start 引用，但只验证本次非并行压缩路径。不声称线程 API 可在浏览器任意使用。
10. Ego Lite 提示工具可更新，本次没有升级，继续使用当前版本完成验证；报告保留实际 Chromium User-Agent。
11. 最终 `git diff -- src` 为空，所有新实现和验证资料在 poc/wasm。SDK/NuGet 缓存、编译输出和临时浏览器不属于产品源码。

各阶段结果以 compatibility.md、performance.md 及 JSON/构建日志为准。现有日志中 NU1510（CodePages 冗余显式引用）和上游源码生成器 CS8632 nullable 警告已保留，没有通过禁用警告或移除格式规避。

## 续测记录

Safari 初次原生 app 状态读取也曾超时，随后启动完成。通过 CUA 的真实 Safari 界面加载原静态 PoC，显示 54/46 格式；原生文件选择器选入唐诗 SCEL，实际转换 3,563 条（70ms）并下载 160,107 bytes，哈希与 CLI 一致。通过开发者控制台将页面高级检查/指标导出为本地 JSON，19 项与 native 完全相同（Big5 错误仍存在）。控制台两个 404 已完整写入 safari-scel-rime.json。WebDriver 初次失败未删除，未更改系统远程自动化或 Apple Events 权限。

Firefox 续测使用专用 driver 4447、临时 profile 和独立报告目录 firefox-memory/，通过 capabilities 的浏览器 PID 与 OS PPID 树隔离进程。235 次采样，实际平均间隔约 126 ms；50 MB 转换与下载阶段采样最高 RSS 合计 3,789,111,296 bytes（10 个进程）。这个值包含共享页重复计数、浏览器固定开销和此前测试缓存，不能当作独占物理内存或连续精确峰值。三档完整下载均再次等于 CLI，原有性能基线未覆盖。浏览器测试进程和本次 driver 均已关闭，静态 HTTP 服务保持可用。

iOS Simulator 清点无已启动设备（booted 列表为空）；本次没有启动移动设备测试，iOS Safari 继续明确标记为未验证。

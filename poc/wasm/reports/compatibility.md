# WebAssembly 兼容性验证报告

验证日期：2026-11-14（Asia/Singapore）。上游 commit：`501a1b77d46187e0b5072f8a27550fa77454c7d1`。
结论范围：.NET 10 的解释执行 Blazor WebAssembly，Release IL 裁剪；未测试 AOT、native relink、多线程、全部格式的全量样本。

## 已执行阶段

1. Debug 构建、Release 发布成功。没有预装 SDK，已在 `/tmp/imewl-dotnet` 安装 SDK 10.0.404，运行时 10.0.15。`wasm-tools` workload 未安装，SDK 使用预构建 WASM runtime，发布提示“不进行 [native] 优化”，并非构建失败。不能据此宣布 AOT 兼容。
2. Python `http.server` 仅提供静态 `wwwroot`，服务器不执行 .NET 或转换。Chromium、Firefox、Safari 均运行 C#，初始化 54 个 Importer、46 个 Exporter。引用完整 Application → Core/Formats/CodeData/Abstractions，没有删减格式。
3. Chromium 的 9 个真实转换方向均下载文件并与原 CLI 对比：8 项字节一致；Rime → SCEL 因随机元数据，重新导入并比较全部词条、编码、解析后的词频，一致。详见 `conversion-comparison.json`。
4. 高级功能以浏览器实际执行、输出断言和原生对照验证；已知 Big5 词表导入错误独立记录。
5. Chromium、Firefox 都执行 1/10/50 MB 真实词库测试并下载，完整输出 SHA-256 与 CLI 一致。Safari WebDriver 尝试失败后，通过真实 Safari 原生界面完成 SCEL 下载和 19 项高级检查；Safari 三档性能、iOS Safari 未执行。

## 模块与格式矩阵

“通过”限表中样本/调用路径；注册成功不代表该格式所有操作都兼容。完整矩阵对照限 Chromium；Safari 真实 SCEL 下载及 19 项高级检查另有独立证据。

| 模块/格式 | 编译 | 浏览器运行 | 转换正确性 | 问题与证据 |
|---|---|---|---|---|
| Abstractions | 通过 | Chromium/Firefox/Safari 通过 | 接口、模型被真实使用 | Stream 接口直接复用 |
| Core | 通过 | Chromium/Firefox/Safari 通过 | 词条处理服务通过 | ConversionPipeline 输入仍依赖路径，未直接使用其文件分支 |
| Formats | 完整项目通过 | 全部 54/46 注册成功 | 仅以下方向已验证 | 其余格式未验证，不能称全格式兼容 |
| CodeData | 通过 | Chromium/Firefox/Safari 通过 | 拼音/五笔86编码实测通过 | 其他码表生成器未逐一验证 |
| Application | 通过 | Bootstrap 通过 | 与 CLI 对照 | CLI/拆分/路径探测分支未在浏览器验证 |
| SCEL → Rime | 通过 | Chromium、Firefox、Safari | 3,563 条，字节等于 CLI | 输出是 TSV 数据，无 YAML 头 |
| Rime → SCEL | 通过 | Chromium；三浏览器小样往返 | 12 条，完整语义等于 CLI | 随机元数据；SCEL 导入词频为 0，是原引擎行为 |
| SCEL → TXT(word) | 通过 | Chromium | 3,563 条，字节等于 CLI | TXT 是无拼音逐行词表 |
| TXT(word) → Rime | 通过 | Chromium；三浏览器编码小样 | 60 条，字节等于 CLI | 显式选择生成拼音，直接导出无编码词条会被 Rime 跳过 |
| Gboard(text) → Rime | 通过 | Chromium | 2 条，字节等于 CLI | 原文本 shortcut 为 UserDefine，需生成拼音匹配 CLI 推断 |
| Rime → Gboard(text) | 通过 | Chromium | 12 条，字节等于 CLI | gboard 不是 ZIP 容器读写 |
| Gboard(binary) → Rime | 通过 | Chromium；三浏览器往返 | 真实词库 3 条，字节等于 CLI | ID 为 gboardbin |
| Rime → Gboard(binary) | 通过 | Chromium；三浏览器往返 | 12 条，语义/字节等于 CLI | 未在真实 Gboard App 安装测试 |
| QPYD → Rime | 通过 | Chromium | 1,657 条，字节等于 CLI | 实际覆盖 SharpZipLib 解压 |
| libimebin 托管 Zstd 往返 | 通过 | Chromium/Firefox/Safari | 两条样本词/编码/词频与原生对照一致 | 未验证所有压缩级别、并行压缩或超大 libime 文件 |
| 其他已注册格式 | 通过 | 构造/枚举通过 | 未验证 | 不能由 54/46 的数量推断解析正确 |

本次六个指定转换方向均由当前上游支持，没有需要标记为“原项目不支持”的方向。
注意：完整 Rime YAML 元数据、import_tables 依赖词库解析，Gboard ZIP 解包不在现有对应解析器的实现范围，不能把这些限制归为 WASM 失败。

## 高级功能

| 功能 | 实际结果 | 限定 |
|---|---|---|
| 多文件导入与合并 | 浏览器 File API 选择两份真实 SCEL，345,742 条；下载与 CLI 字节一致 | 简单拼接，未自动去重 |
| 词条过滤 | 三条中按长度筛为两条，三种浏览器内容断言通过 | 其他过滤组合未遍历 |
| 词频保留/生成 | 原 99 保留，缺失/0 生成 1 | SCEL 导入本身丢弃原词频；LLM 词频不在纯本地范围 |
| 拼音/五笔86 | 中国 → zhong guo / khlg，中文 → zhong wen / khyy | 双拼、其他五笔版本等未测 |
| 简繁 | 中国 ↔ 中國 | 非完整语言学质量评估 |
| GBK/GB2312/Big5/UTF-8 编码器 | 四种编码器双向转换通过 | 与格式是否使用编码选项分开评估 |
| GBK/GB2312/UTF-8 纯词表导入 | 内容正确 | 自动探测，不代表显式选项生效 |
| Big5 纯词表导入 | **内容错误**，與原生 .NET 一致 | 选项被忽略，Big5 被按 GB18030 解码，属已有格式行为 |
| 二进制导入/导出 | SCEL/Gboardbin/libimebin 小样通过 | SCEL 不保留词频；未在原输入法软件安装 |
| 预取消令牌 | OperationCanceledException 通过 | 只验证转换入口预取消 |
| 页面处理中取消 | **未达到可用要求** | 500 ms 定时点击实际到 2713.8 ms，状态已 Complete；见 chromium-ui-cancellation.json |
| 进度报告 | 收到 Import、Filter、Rank、Export 等消息 | CPU 同步段阻塞页面，不能称持续实时进度 |

## 依赖与动态行为检查

- 完整 NuGet 直接/传递清单：`dependencies.txt`；browser-wasm 实际解析出的 40 个库及依赖边/运行/native 资源：`resolved-wasm-assets.json`。其中浏览器包图未解析到 NuGet native 资源。
- SDK 解析后 DI/DI.Abstractions 实际使用 **10.0.15**（上游要求 10.0.7，被 Blazor 版本统一）；CodePages 显式引用 10.0.7，并有 NU1510 冗余引用警告。
- `assembly-audit.json` 通过 PE 元数据逐程序集扫描非框架依赖的 P/Invoke 与相关方法引用；未发现这些程序集的 P/Invoke。这个检查不覆盖运行时所有 .NET 框架内部实现，也不是全路径动态行为证明。
- SharpZipLib 1.4.2：真实 QPYD 解压、ZIP 写入再读取断言通过。
- UTF.Unknown 2.5.1：浏览器 `CharsetDetector.DetectFromStream` 真正执行并探测为 utf-8。文件路径探测 helper 未验证。
- ZstdSharp.Port 0.8.8：实际 libimebin 压缩及解压成功；是托管 unsafe 方法，不是直接调用本机 libzstd。程序集有 Thread.Start 引用，当前单线程压缩路径成功，不能宣布多线程路径可用。
- DI 包含 Reflection.Emit/Expression 相关引用；默认容器在当前无 WASM 线程 runtime 内初始化及解析成功，说明被测试路径不要求动态生成可执行机器码。不能仅凭该引用判失败，也不能凭一次启动批准全部反射用法。
- System.CommandLine 包含 Process.Start 引用，PoC 只调用 Application Bootstrap，不在浏览器执行 CLI 启动/建议/控制台分支。
- MinVer、Roslyn SourceGenerators 是构建工具，不需要在浏览器加载。格式注册为构建期生成；CodeData 资源裁剪后真实被拼音/五笔加载。

## 浏览器与网络证据

- Chromium 156（Ego Lite），Release 发布产物，完整矩阵、下载、内容对照、性能、取消测试。
- Firefox 160，临时下载的官方版本、headless WebDriver；SCEL 下载等于 CLI、高级检查、1/10/50 MB 完整下载等于 CLI。Firefox 不支持本次 Long Tasks API，指标 0 **不是不卡顿的证明**。
- Safari 27：原 `safari-session.json` 的 WebDriver 会话确曾超时，保留该失败记录。续测通过原生 Safari 界面实际加载 Release 静态产物、选择本地 SCEL、转换和下载；3,563 条的完整下载与 CLI 字节一致。高级 19 项结果与原生对照一致（包含同一个 Big5 内容错误）。见 `safari-scel-rime.json`、`safari-advanced.json`、`advanced-comparison.json`。没有开启 JavaScript from Apple Events 或修改远程自动化设置。**三档性能和完整九方向矩阵仍未在 Safari 验证**。
- Safari 控制台实际观察到两个 404：`favicon.ico` 和打开开发者工具时请求的 `dotnet.runtime.js.map`；无对应 C# 转换异常。不能沿用 Chromium 控制台零错误的结论描述 Safari。
- iOS Safari：**未验证**。
- `chromium-events.json`：禁用该页面 HTTP 缓存后的加载和一次真实转换，70 个本站请求全部 GET，无 POST/请求正文，无失败网络请求，无控制台 error/未捕获异常。未安装转换服务，所有 C# 运行于浏览器；本地文件通过 InputFile/OpenReadStream 获取，不发送到 HTTP 服务器。
- `firefox-*.json` 的 metrics.errors 是页面错误/未处理 rejection 捕获；Geckodriver 自身日志包含浏览器实验配置提示，不能混同为转换异常。

## 最终技术判断

1. **能在浏览器运行**：已通过三种浏览器的真实 SCEL 转换和 CLI 内容对照，九方向矩阵限 Chromium；现有路径式 CLI/ConversionPipeline 不能原封不动作为 File API 入口。
2. **可直接引用全部核心项目**：本次无须修改或复制原引擎。全部模块编译成功；只对已测试功能作运行保证，未覆盖全部格式/功能。
3. **已验证格式**：上表九个方向，以及 libimebin/SCEL/Gboardbin 往返；高级功能见单独限定。
4. **需改造处**：流式 pipeline 入口、后台执行与可中断循环、编码选项、Rime YAML 容器、Gboard ZIP；不是为“让构建通过”而删除功能。
5. **未发现不可解决的关键阻断**：仅限实测范围。Safari 三档性能/iOS、全部格式、AOT 未验证；不作“所有浏览器均兼容”的结论。
6. **静态托管形态可行**：普通静态 HTTP 已实测，不依赖服务端 .NET。可把 wwwroot 作为 Cloudflare Pages 输出目录；**未实际部署 Cloudflare Pages**，其压缩/MIME/缓存行为仍需上线前验证。
7. **已验证功能不需要服务端补充**：本次没有服务端转换。大词库可暂时引导使用本地 CLI；现有数据不能证明有必要保留上传式服务端转换，也不能承诺所有超大文件都能在手机浏览器处理。
8. **建议继续正式网页版开发，但设验收门槛**：核心路线已成立；先处理 Worker/取消/大文件内存，再补 Safari 大文件/iOS 及完整格式回归。当前 PoC 不是已满足生产大文件体验的产品。

续测内存证据：Firefox 专用浏览器 PID 树采样、1/10/50 MB 再次下载的 CLI 哈希比较均已完成，见 performance.md 的“续测：Firefox 专用进程树 RSS 采样”。这个 RSS 合计不等于去重物理内存峰值；Chromium/Safari 总 RSS 峰值仍未取得可靠隔离测量。

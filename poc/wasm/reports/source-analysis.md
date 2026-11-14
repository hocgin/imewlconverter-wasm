# 源码检查（编写 PoC 前）

上游 https://github.com/studyzy/imewlconverter ，commit `501a1b77d46187e0b5072f8a27550fa77454c7d1`。
空工作区已克隆上游到仓库根目录。全部验证代码限定在 poc/，不修改 src/。

- Abstractions/Contracts/IFormatImporter.cs: ImportAsync(Stream, ImportOptions?, CancellationToken)。
- IFormatExporter.cs: ExportAsync(IReadOnlyList<WordEntry>, Stream, ExportOptions?, CancellationToken)。
- Core/Pipeline/ConversionPipeline.cs: 两种输入分支都 File.OpenRead；合并分支支持 OutputStream；逐文件分支 File.Create。不能直接接浏览器 File API。
- Core/Pipeline/EntryTransformationService.cs: 已抽离 Filter → ChineseConvert → Rank → CodeGen → RemoveEmpty；PoC 只添加内存流编排，直接调用此服务，未复制算法。
- Formats: 完整项目引用，不剔除格式；SourceGenerators/FormatRegistrationGenerator 在构建期生成 AddAllFormats 和 Metadata，非运行时扫描程序集。DI 常规类型注册有构造函数反射，需实际 trimmed Release 验证。
- Application/Bootstrap/ImeWlConverterBootstrapper: 可直接 AddImeWlConverter；Application 同时引入 System.CommandLine，不代表 CLI 功能都适用浏览器。
- Cmd/Program.cs: CLI 是 Application/Cli/CliApp 的薄壳，作为原生 .NET 对照。
- CodeData/EmbeddedResourceProvider: typeof(...).Assembly.GetManifestResourceStream，Lazy 表加载。无外部码表下载；需验证资源裁剪后仍存在。
- 文件系统依赖：ConversionPipeline、FileOperationHelper、FormatDetectionService.DetectByContent、MergeSplitService、用户自定义码表路径。浏览器本地虚拟 FS 与用户磁盘不同；PoC 不使用这些路径处理用户文件。
- 初步检索上述模块未发现 DllImport、LibraryImport、Process.Start、Assembly.Load、Reflection.Emit；LazyThreadSafetyMode 并不要求启动线程。异步方法也不保证让出 UI 主线程。
- SCEL ParseBinary 内 input.CopyTo + MemoryStream，再创建词条列表；未逐条检查 ct，捕获并跳过部分解析错误。必须比较内容，不能仅依赖 ErrorCount。
- Shared/TextFormatImporter/TextFormatExporter 使用 FileEncoding，忽略 options.EncodingName；NoPinyinWordOnly 自动 UTF-8/GB18030，不能显式 Big5。这是已有实现限制。
- RimeExporter 输出 tab-separated 数据，无 YAML 头。PoC 的 .dict.yaml 下载保持引擎原始行为，不声称为完整可安装 Rime 词库。
- Gboard `gboard` 是纯文本 TSV，注释写 zip 但实现未解压；`gboardbin`（实际 ID 以运行枚举为准）另有二进制格式。ZIP 必须单独评估，不能把扩展名识别当解压成功。

直接依赖：Core: DI.Abstractions 10.0.7, SharpZipLib 1.4.2, UTF.Unknown 2.5.1；Formats: DI.Abstractions 10.0.7, SharpZipLib 1.4.2, ZstdSharp.Port 0.8.8；Application: DI 10.0.7, System.CommandLine beta4；CodeData: DI.Abstractions 10.0.7。恢复后保存完整直接/传递依赖清单。
ZstdSharp.Unsafe.Methods 是托管移植的 unsafe API，命名含 libzstd 不能据此认定 P/Invoke；必须真实压缩/解压。CodePages 由运行时及 PoC 显式包引用提供。源码生成器 Roslyn/MinVer 只在构建期执行，不是浏览器运行依赖。

后续证据以 compatibility.md、performance.md 和原始日志为准；本文件只记录源码事实，不宣布运行兼容。

## 恢复/发布后的补充审计

完整解析依赖保存在 dependencies.txt 和 resolved-wasm-assets.json；非框架运行程序集 PE 元数据扫描在 assembly-audit.json。源码初步检索无 P/Invoke 并不等于依赖中无可选动态行为：DI 确有 Reflection.Emit 引用，ZstdSharp 有 Thread.Start 引用，System.CommandLine 有 Process.Start 引用，详见 compatibility.md 的实测路径与限制。

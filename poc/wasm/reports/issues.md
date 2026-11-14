# 问题与最小改造建议

仅修改 PoC；上游 src/ 无改动，`git diff -- src` 为空。下列方案是建议，未声称已实施。

| 问题 | 根因和证据 | 影响 | 是否可解决 / 推荐方案 | 难度 |
|---|---|---|---|---|
| ConversionPipeline 输入为文件路径 | 合并/逐文件分支 File.OpenRead | File API 无法直接提供用户本地路径；内存虚拟 FS 额外复制 | 可解决：新增流源 overload；当前 PoC 用很薄的 StreamConverter 调真实 Importer、EntryTransformationService、Exporter | 低 |
| 大词库冻结页面 | 解析、转换、排序大量同步循环；Async 不意味着后台执行 | 50 MB Chromium 单长任务 13.6s，取消按钮/实时进度不可用 | 推荐将转换 runtime 放入 Web Worker；添加逐批 ct 检查和可让出执行权的批处理；取消可用 worker 消息/终止重建；不可仅 Task.Run 当作后台证明 | 中至高，须测消息传输和 Stream 生命周期 |
| 取消不完整 | SCEL 不检查 ct；词频/CodeGeneration 等循环也未完整观察 ct；同步段阻塞事件派发 | SCEL 500ms 点击延迟到完成后的 2713.8ms；预取消通过不等于处理中取消 | 循环检查 token + Worker 执行；若单线程 worker 消息也阻塞，需要批间让出或外部终止 worker。保持 CLI 默认行为 | 中 |
| 内存较高 | InputFile→MemoryStream、SCEL 内部再次复制、所有词条实体/列表、导出 byte[]、JS 下载 ArrayBuffer；排序再分配 | 50 MB 约 1.30 GB WASM 线性内存；手机容量未测 | 优先移除冗余全量拷贝、逐批/流式导入、限制同时驻留文件；对必须全量排序格式明确内存预算；大文件暂可用本地 CLI | 中至高 |
| Big5 导入乱码 / 显式编码未生效 | TextFormat 基类忽略 EncodingName；word 自动 UTF-8/GB18030 | Big5 编码器本身正常，纯词表实际解码错误；native 与 WASM 相同 | Import/ExportOptions.EncodingName 优先于格式默认；没显式值才探测；针对格式保持默认编码不变 | 低至中 |
| Rime .dict.yaml 不完整 | RimeExporter 只输出 TSV，Importer 不解析 import_tables | 文件可下载并与 CLI 相同，但不能宣称是完整可直接安装的 Rime YAML 词库 | 格式层增加可选 YAML 元数据头及头部处理；import_tables 需要多文件输入解析；PoC 保留原行为并标注 | 低（头）至中（依赖表） |
| Gboard ZIP 未实现 | gboard 实现只是 TSV；扩展名识别把 .zip 映射为 gboard | ZIP 内容不能直接用文本 Importer，当作文本可能无异常却零条 | 容器适配层使用 SharpZipLib/System.IO.Compression 提取 TSV，基于 magic+内容探测；不能把任意 ZIP 一律识别为 Gboard | 低至中 |
| SCEL 词频丢失/静默略过错误 | ReadAPinyinWord 固定 Rank=0；解析循环 catch 后继续 | 往返词频不等于源；ErrorCount 不是完备正确性证据 | 格式算法语义单独修复并加真实样本回归；PoC 不重写算法；本次对比重新导入后词条语义 | 中，涉及格式兼容 |
| 完整依赖包含浏览器无效分支 | System.CommandLine Process.Start；Zstd Thread.Start；DI 动态代码实现 | 当前所用路径正常，不代表全部调用可用 | 保持默认注册，针对实际用到的分支测试；可将 Bootstrap/通用应用能力与 CLI 包拆分以缩小产物，但非本次运行必需 | 低至中 |
| Safari 自动化与覆盖不足 | WebDriver 等待 RWI 超时；已通过原生 UI 补测 | Safari 的 SCEL 转换/下载与高级检查已通过；大文件/iOS 仍未知 | 保留原生 UI 证据；继续补 Safari 大文件测试或修复自动化环境；不以启用额外系统权限作为默认操作 | 核心验证已完成，其余测试成本未评估 |
| wasm-tools/AOT 未验证 | 本机只安装 SDK，使用预构建解释 runtime | 不可声称 native relink/AOT/多线程兼容 | 可选下一阶段安装 wasm-tools 并独立回归；不作为纯静态部署的前置条件 | 未评估 |

## ConversionPipeline 的最小流式演进

建议引入 `ConversionSource(Name, OpenReadAsync)` 作为**来源抽象**，以及接受这些来源和 `Stream output` 的 ExecuteAsync overload。流的所有权用接口约定清楚：打开工厂产生的输入由管道关闭；调用方提供的输出由调用方关闭。

1. 现有路径式 ExecuteAsync 只把每个路径适配为 `File.OpenRead` 的来源，再进入同一内部执行方法。
2. 新流式 overload 把浏览器已读取的流/流工厂传入同一内部方法；进度/错误展示使用 Name，不能把它当真实磁盘路径。
3. 保留现有 filter factory、EntryTransformationService、导出元数据注入和 ConversionResult 组装；不复制转换流程、不修改格式算法。
4. 逐文件输出另用 `OpenOutputAsync(name)` sink，默认仍适配原 File.Create，CLI 行为不变。
5. 浏览器生命周期不要持有过期 IBrowserFile JS 引用；Worker 与 UI 交接优先 Transferable 数据，评估内存后确定实际管道方式。

PoC 为避免改动原代码，暂用 `StreamConverter.cs` 实现入口编排；它不声称完整替代旧 ConversionPipeline 的逐文件输出、错误策略或去重能力。

续测确认：Safari SCEL 完整下载等于 CLI，19 项检查与 native 一致；旧的 Safari WebDriver 超时属于自动化通路问题，不能再用于表示浏览器引擎尚未运行。两个 404（favicon、可选 sourcemap）不影响已验证转换，但已记入 console 问题。

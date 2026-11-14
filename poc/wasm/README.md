# imewlconverter .NET 10 浏览器 WebAssembly PoC

**实测结论：核心路线可行。** 完整引用原项目，Chromium/Firefox/Safari 运行真实 C# SCEL 转换并下载，与原 CLI 对照一致。未改动 `src/`，未复制引擎源码、未使用后端转换、未上传词库。

已注册 54 个 Importer、46 个 Exporter；这不代表全部格式均已验证。50 MB 实测需要约 1.30 GB WASM 线性内存，Chromium 主线程阻塞约 13.6 秒。Safari 大文件/iOS 尚未验证，当前 PoC 不代表生产体验已达标。

## 报告入口

- [源码分析](reports/source-analysis.md)：Stream、路径依赖、注册、编码、资源。
- [兼容性报告与八项技术结论](reports/compatibility.md)：模块/格式矩阵、浏览器状态、运行证据、依赖审计。
- [性能报告](reports/performance.md)：1/10/50 MB、条数、时间、内存口径、CLI 对照、产物体积。
- [问题及最小改造清单](reports/issues.md)：原因、影响、建议、难度，包含 Pipeline 流式 overload 设计。
- [执行与失败记录](reports/execution-notes.md)：环境限制、验证脚本问题及修复。

## 构建、静态运行、发布

需要 .NET **10 SDK**、Python 3。先执行 `git submodule update --init --recursive`，以下命令均在仓库根目录执行：

```sh
dotnet build poc/wasm/WasmPoc.csproj -c Debug
dotnet publish poc/wasm/WasmPoc.csproj -c Release -o artifacts/publish
python3 -m http.server 8765 --bind 127.0.0.1 --directory artifacts/publish/wwwroot
```

浏览器打开 <http://127.0.0.1:8765>。本次机器 SDK 初始不存在，临时安装于 `/tmp/imewl-dotnet`；当前会话可先执行：

```sh
export PATH="/tmp/imewl-dotnet:$PATH"
```

临时目录可能被系统清理，届时需重新安装 SDK。预构建解释 WASM runtime 已成功发布，不要求 `wasm-tools`；如计划 AOT/native relink，应另行安装 workload 并回归，不能使用本次结果代替验证。

页面无 ASP.NET Core 宿主，不使用 `dotnet run` 提供转换。发布目录中的 `wwwroot` 是静态部署根目录，不需要上传 DLL 到服务器执行。Cloudflare Pages 可配置上述 publish 命令、输出 `artifacts/publish/wwwroot`；本次**未实际部署 Cloudflare**，需自行在构建环境准备 SDK。也可本地发布后上传此目录。使用根路径部署（index.html 的 base href 为 `/`）。

## 手动验证

1. 选择 `upstream/imewlconverter/src/ImeWlConverterCoreTest/Test/唐诗300首【官方推荐】.scel`，自动识别 scel，输出 rime，开始转换、下载。应导入/导出 3,563 条。
2. Rime → SCEL 可选 `rime_luna_pinyin_export.txt`，手动选择输入 rime，输出 scel。支持导出，不能沿用旧版本“不支持”的结论。
3. TXT 指输入/输出 `word`（每行一词）。TXT → Rime 必须选择生成拼音，否则无编码词条会被原 exporter 跳过。
4. Gboard 文本为 `gboard`；实际二进制 user_dict_3_3 为 `gboardbin`。`.zip` 的扩展名识别不等于 ZIP 解包支持。文本 shortcut → Rime 若要匹配 CLI 默认推断，请选择生成拼音。
5. 多选两个同格式文件会合并导入，未自动去重。混合格式多文件不是本 PoC 的操作方式。
6. “运行高级自检”执行真实引擎调用。19 项中包含 **已知 Big5 内容错误**，请检查 `correct:false`，不能因没有 exception 判断全部通过。预取消通过不等于处理中取消可用。

输出 `.dict.yaml` 保留上游 Rime exporter 原始 TSV 行，**没有 YAML 元数据头**；没有声称可直接安装到真实 Rime。输出 SCEL/Gboardbin 也未在对应输入法 App 内安装验收。

## 原生 CLI 与语义对照

```sh
dotnet build upstream/imewlconverter/src/ImeWlConverterCmd -c Release
dotnet build poc/wasm/baseline -c Release
# 与浏览器同样的词条级调用，用于确认原生行为和依赖元数据
dotnet poc/wasm/baseline/bin/Release/net10.0/Baseline.dll
dotnet poc/wasm/baseline/bin/Release/net10.0/Baseline.dll audit
# 原项目 CLI 真正转换
dotnet upstream/imewlconverter/src/ImeWlConverterCmd/bin/Release/net10.0/ImeWlConverterCmd.dll \
  -i scel -o rime -O /tmp/cli-result.dict.yaml --json \
  'upstream/imewlconverter/src/ImeWlConverterCoreTest/Test/唐诗300首【官方推荐】.scel'
python3 poc/wasm/scripts/cli-matrix.py
```

`cli-matrix.py` 在浏览器矩阵产物存在时逐项比较。SCEL 不比较随机元数据，而是用原 importer 重新解析两份产物，比较完整词条/编码/可解析词频。对照程序位于 `baseline/`，不参与浏览器执行。

## 复现真实大词库测试

```sh
curl -fsSL https://raw.githubusercontent.com/amzxyz/rime-wanxiang/c36653e7c454bfb30f8e634054970d3abefa036c/dicts/jichu.dict.yaml \
  -o /tmp/imewl-jichu.dict.yaml
python3 poc/wasm/scripts/prepare-benchmarks.py /tmp/imewl-jichu.dict.yaml
python3 poc/wasm/scripts/cli-benchmarks.py
```

脚本验证源 SHA-256 后按完整词条行截取，未生成或重复填充词条。`cli-benchmarks.py` 的 RSS 采集使用 macOS `/usr/bin/time -l`；其他系统需调整采集方式。派生大文件置于 `artifacts/fixtures`，不属于部署内容。大产物在本地保留并被 `.gitignore` 忽略；JSON 中保留哈希、条数、错误和测量数据。

浏览器使用 File API 选择这些本地切片，输入/输出 rime、生成编码 Pinyin。Firefox 与 Chromium 均实际下载并比较 SHA-256。`scripts/write-performance-report.py` 根据已存在的测量 JSON 生成性能报告，不执行转换，也不伪造缺失结果。

## 自动化复现

Chromium 脚本使用 ego-browser 技能接口（需要已运行 Ego Lite）：

```sh
ego-browser skill
ego-browser nodejs < poc/wasm/scripts/chromium-matrix.mjs
ego-browser nodejs < poc/wasm/scripts/chromium-benchmarks.mjs
```

脚本默认以当前目录作为仓库根目录，可用 `IMEWL_ROOT` 覆盖。先创建一次 TaskSpace，并设置 `export EGO_TASK_SPACE_ID=<本次ID>`，所有轮次复用同一空间。运行前启动上面的静态服务器；矩阵脚本不使用 mock 或网络转换。

Firefox 脚本使用标准 WebDriver HTTP。当前官方 Firefox 160 安装于 `/tmp/imewl-firefox/Firefox.app`，Geckodriver 0.36.0 位于 `/tmp/imewl-geckodriver/`，均为临时测试工具：

```sh
/tmp/imewl-geckodriver/geckodriver --port 4446
# 另一个终端
python3 poc/wasm/scripts/firefox-webdriver.py
```

其他环境需调整脚本中的 Firefox binary 路径；它创建临时浏览器配置，读取本地文件并保存下载到 `reports/firefox-downloads`。Safari session 创建失败的原始响应保留在 `reports/safari-session.json`；续测经原生界面跑通 SCEL → Rime 并下载，与 CLI 完全一致，19 项高级检查与原生对照相同。Safari 三档性能、iOS Safari 未执行。

## 代码边界

- `Program.cs`：注册 CodePages、直接调用上游 AddImeWlConverter。
- `StreamConverter.cs`：内存流入口编排，调用原 Importer/EntryTransformationService/Exporter，不含格式算法。
- `Pages/ConverterTest.razor`：InputFile、选择器、结果、下载、错误详情。
- `AdvancedChecks.cs`：真实引擎的小样断言，包含已知不正确内容检查。
- `wwwroot/poc.js`：本地 Blob 下载、资源/线性内存/长任务度量，不发送词库内容。
- `baseline/`、`scripts/`、`reports/`：原生对照、复现和证据。

本项目继承上游 GPL-3.0 许可；第三方测试语料来源及哈希单独记录。未在本次任务中部署公网服务、上传用户词库或实现正式产品。

## 续测：Safari 与进程内存

Safari 27 使用原生界面（CUA）选取仓库真实 SCEL，实际 Blob 下载文件与 CLI 字节一致；通过开发者工具导出高级检查 JSON，保存在 reports/safari-advanced.json。控制台有 favicon 和可选 runtime sourcemap 两个 404，已如实记录。未启用 Apple Events JavaScript 或远程自动化设置。

Firefox 进程树内存采样可运行 `python3 poc/wasm/scripts/firefox-memory-probe.py`，它为本次测试启动专用端口 4447 的 Geckodriver 和临时 Firefox profile，在 reports/firefox-memory 下保存各档结果与约 100 ms 间隔的 RSS 样本；只统计该 Firefox 根 PID 及其 PPID 子进程，排除驱动与其他浏览器。多进程 RSS 合计可能重复计算共享页面，不是去重物理占用或连续精确峰值。

## 仓库迁移

本目录从 `imewlconverter-web/poc/wasm` 迁移而来。上游引擎现在位于 `upstream/imewlconverter` Git 子模块，固定为原验证提交 `501a1b77d46187e0b5072f8a27550fa77454c7d1`。项目引用和可执行脚本已切换到子模块；`reports/` 保留迁移前的原始证据，内含原机器路径及历史日志，不代表迁移后重新执行了全部浏览器测试。

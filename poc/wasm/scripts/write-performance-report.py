from pathlib import Path
import json
poc=Path(__file__).resolve().parents[1];p=poc/'reports';load=lambda n:json.loads((p/n).read_text())
cli=load('cli-performance.json');fixtures=load('benchmark-fixtures.json')['fixtures'];lines=[]
for i,mb in enumerate([1,10,50]):
 c=load(f'chromium-bench-{mb}MB.json');f=load(f'firefox-bench-{mb}MB.json');cr=json.loads(c['result']);fr=json.loads(f['result']);n=cli[i];fixture=fixtures[i]
 lines.append(f"| {mb} MB | {fixture['bytes']:,} | {cr['Imported']:,}/{cr['Exported']:,} | {cr['ElapsedMs']/1000:.3f} / {c['wallMs']/1000:.3f} | {fr['ElapsedMs']/1000:.3f} / {f['wallMs']/1000:.3f} | {n['wallMsIncludingProcessStartup']/1000:.3f} | {c['metrics']['wasmLinearBytes']/1e6:.1f} / {f['metrics']['wasmLinearBytes']/1e6:.1f} | {n['maxRSSBytes']/1e6:.1f} | {c['metrics']['maxLongTaskMs']/1000:.3f} |")
s=load('artifact-sizes.json');cold=load('chromium-cold-load.json');initial=load('firefox-initial.json')
text=f'''# 性能与产物报告

验证日期：2026-11-14（Asia/Singapore）。Apple M4 Pro / 24 GiB RAM / macOS 27.0 (26A428) arm64；.NET SDK 10.0.404 / runtime 10.0.15；Release、IL trimming、解释执行，未 AOT、未 native relink，单线程 runtime（SIMD 已开）。

浏览器：Chromium 156（Ego Lite、有浏览器扩展）；Firefox 160（官方临时下载安装，headless）。普通 Python HTTP/1.0 静态服务器、127.0.0.1，无网络带宽限制模拟。不同测试单次采样、不同热身与后台负载，不能当作稳定基准或不同引擎的普遍排名。

## 数据集与正确性

原项目没有 50 MB 测试文件。采用真实 [万象基础词库](https://github.com/amzxyz/rime-wanxiang/blob/c36653e7c454bfb30f8e634054970d3abefa036c/dicts/jichu.dict.yaml)的完整 TSV 词条行前缀，分别接近十进制 1,000,000 / 10,000,000 / 50,000,000 bytes。未随机生成词条，未重复拼接填充。省略 YAML 头与注释，保留原词条/编码/词频。来源 commit、源文件 SHA-256、每个切片 SHA-256/行数在 benchmark-fixtures.json。真实词条可含相同文字的不同编码，不人为去重。

转换统一为 Rime → Rime，显式 Pinyin 目标（已有 Pinyin code 原样保留），缺失/0 词频遵循原引擎生成默认 1。每档浏览器使用全新页面和 runtime。两浏览器均通过 File API 选入样本，生成并实际下载完整文件；三档输出 SHA-256 均与 CLI 一致。正确性不是由计数或 preview 推断。

## 实测

浏览器列为“引擎毫秒表 / 自动化墙钟”；引擎计时包含内存流导入、转换、导出及 ToArray，**不包含 File API 读入及下载**。Chromium 墙钟从开始按钮派发到结果；Firefox 墙钟还包含 WebDriver 文件选择/格式设置，均不含下载。CLI 为独立进程完整墙钟，包含启动和磁盘 IO，不是可直接相除的同口径引擎计时。

| 档位 | 实际字节数 | 导入/导出条数 | Chromium 秒（引擎/墙钟） | Firefox 秒（引擎/墙钟） | CLI 秒（进程全程） | WASM 线性内存 MB（Chromium/Firefox） | CLI 峰值 RSS MB | Chromium 最长长任务秒 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(lines)}

三档未发生 OOM；不代表更大词库或移动设备安全。Chromium 10 MB 已出现约 3.3 秒长任务，50 MB 约 13.6 秒，页面有实测卡顿。Firefox 本次不支持 Long Tasks API，采集值 0 不可解释为不卡顿。没有测帧率；iOS Safari 内存与交互完全未验证。

### 内存口径

WASM 列读取当前 runtime 的 Module.HEAPU8.byteLength，是本次新 runtime **已分配线性内存的高水位**（该测试中不缩小），不是总浏览器进程峰值 RSS。managed GC.GetTotalMemory(false) / HeapSizeBytes 为转换返回时快照，保存在原始 JSON，**不是托管内存峰值**。performance.memory 只描述 JS heap，不能代替 .NET/WASM 内存。

Chromium 总进程 RSS 峰值、托管精确峰值仍未取得可靠隔离测量；不将线性内存或 JS heap 伪装成总峰值。Firefox 续测新增独立进程树 RSS 采样（含下载），见后文；它也不是去重物理内存峰值。CLI 峰值 RSS 来自 macOS /usr/bin/time -l。

## 加载与发布大小

- Chromium：禁用当前页面 HTTP 缓存后导航到 C# OnAfterRender 完成约 **{cold['metrics']['loadMs']:.1f} ms**；resource encodedBodySize 合计 **{cold['metrics']['resourceBytes']:,} bytes**；transferSize 合计 **{cold['transferBytes']:,} bytes**。这是本机静态 HTTP 的冷资源加载，不能推断公网首开耗时。
- Firefox 首次本会话加载 **{initial['loadMs']:.1f} ms**；资源 body **{initial['resourceBytes']:,} bytes**。Firefox 未主动禁用所有跨会话缓存，不能与 Chromium 当成完全同口径冷启动比较。
- 发布 wwwroot 总计 **{s['publishTotalBytesIncludingCompressionVariants']:,} bytes**，含 .br/.gz 等预压缩变体；文件数 {s['files']}。
- _framework 非压缩变体文件总计 **{s['frameworkUncompressedBytes']:,} bytes**；对这些文件逐个 gzip 计算为 **{s['frameworkGzipBytes']:,} bytes**。后者是离线计算，**不是 CDN 实际下载测量**。
- 简单 HTTP 服务不协商 .br/.gz，本次浏览器 body 下载约 12.58 MB。完整发布目录与实际首屏请求集合不同，不能混用两个大小。
- 静态服务器进程为 Python，无 ASP.NET Core，无服务端 .NET runtime。Cloudflare Pages 未部署，CDN 压缩和缓存策略未实测。

## 证据与局限

- chromium-bench-*MB.json、firefox-bench-*MB.json：条数/引擎时间/内存/错误/下载哈希。
- cli-performance.json、cli-bench-*MB.stderr：CLI 墙钟与峰值 RSS。
- benchmark-comparison.json：Chromium 与 CLI 完整产物比较；Firefox 对比在各档 JSON 的 equalToCLI。
- chromium-ui-cancellation.json：500 ms 点击实际在约 2713.8 ms，转换已完成。
- artifact-sizes.json、chromium-cold-load.json：资源与产物原始度量。

性能数据仅覆盖 Rime → Rime 的三档真实语料，以及额外的 13 MB 真实 SCEL 多文件测试；不能外推所有二进制格式的同等性能。Safari 大文件/iOS 未实测、AOT 未实测、并行压缩未实测、网络限速首开未实测。
'''
if (p/'safari-scel-rime.json').exists():
 safari=load('safari-scel-rime.json');sa=load('safari-advanced.json')
 text+=f"""
## 续测：真实 Safari

Safari 27 原生 UI 已实际读取本地 SCEL 并下载：3,563 条，转换约 {safari['engineElapsedMs']} ms，{safari['downloadBytes']:,} bytes，完整文件字节/哈希与 CLI 一致。19 项高级检查与 native 相同，包括同一个 Big5 内容错误。WebDriver 的初次 RWI 超时记录保留，原生 UI 路线不依赖该通路。

页面 C# 首次渲染诊断值约 {sa['metrics']['loadMs']} ms，未禁用缓存，不作为严格冷加载基准；诊断在高级检查/开发者工具打开后导出，其资源总量不能当作首屏下载大小。Safari 的 1/10/50 MB 测试、峰值内存未执行；iOS Safari 未执行。控制台有 favicon.ico 与可选 dotnet.runtime.js.map 的两个 404，已记录，未观察到 C# 转换异常。
"""
if (p/'firefox-memory/summary.json').exists():
 mem=load('firefox-memory/summary.json');memory_rows=[]
 for mb in [1,10,50]:
  peak=mem['peaks'][f'{mb}MB/convert_and_download'];m=load(f'firefox-memory/firefox-bench-{mb}MB.json')
  memory_rows.append(f"| {mb} MB | {peak['summedRSSBytes']/1e6:.1f} | {peak['processCount']} | {m['metrics']['wasmLinearBytes']/1e6:.1f} | {'一致' if m.get('equalToCLI') else '不一致/未验证'} |")
 text+=f"""
## 续测：Firefox 专用进程树 RSS 采样

启动专用 Geckodriver（4447）和新的临时 Firefox profile，只统计 capabilities 中 moz:processID 及 OS PPID 子进程，不包含驱动进程、其他浏览器或 Safari。按 SCEL、高级检查、1/10/50 MB 顺序运行；每档导航到新页面，**没有为每档重新启动 Firefox 进程**，因此包含浏览器固定开销、缓存及此前步骤尚未回收的内存。

采样目标 100 ms，实际平均 {mem['actualMeanIntervalMs']:.1f} ms、最大间隔 {mem['maxIntervalMs']:.1f} ms，共 {mem['samples']} 个样本。以下为每档 File API 读入、转换、下载期间采到的最高**多进程 RSS 合计**；共享页面可能被多个进程重复计数，不能解读为独占物理占用，也不是连续精确峰值。由于口径不同，不能直接与单进程 CLI 峰值 RSS 作倍数比较。

| 档位 | 采样最高 RSS 合计 MB | 峰值时进程数 | 本次 WASM 线性内存 MB | 完整下载对照 CLI |
|---|---:|---:|---:|---|
{chr(10).join(memory_rows)}

未发生 OOM。本次带采样负载的运行保存在独立 firefox-memory/ 下，没有覆盖上方原性能基线。50 MB 的 WASM 线性内存在不同 Firefox 运行中约 1.30–1.39 GB，进一步说明单次数字不应当作稳定容量上界。浏览器初始加载时自身已有较高 RSS 合计，不能把整个进程树内存全归于词库数据。

复现：`python3 poc/wasm/scripts/firefox-memory-probe.py`。原始进程树采样在 `firefox-memory/samples.csv`，各阶段高点在 `firefox-memory/summary.json`。三档输出均再次下载并与 CLI 哈希一致。
"""
(p/'performance.md').write_text(text)

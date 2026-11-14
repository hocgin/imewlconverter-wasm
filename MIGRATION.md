# WASM 仓库迁移验证

日期：2026-11-14。

## 迁移范围

从 `imewlconverter-web/poc/wasm` 迁移源码、原生对照程序、自动化脚本及历史报告。未迁移编译缓存、发布目录、临时浏览器下载目录和大型性能词库；原目录保留。

上游通过 `upstream/imewlconverter` Git 子模块引用，URL 为 `https://github.com/studyzy/imewlconverter.git`，提交固定为 `501a1b77d46187e0b5072f8a27550fa77454c7d1`。子模块无源码改动。

修改 WASM 和 baseline 的 ProjectReference，以及脚本中的上游 CLI / 测试文件路径。Chromium 脚本使用当前工作目录（或 `IMEWL_ROOT`），TaskSpace 通过 `EGO_TASK_SPACE_ID` 指定。历史报告逐文件核对，内容与原目录一致。

## 本次实际验证

使用本机临时 .NET SDK 10.0.404：

```sh
make DOTNET=/tmp/imewl-dotnet/dotnet build
make DOTNET=/tmp/imewl-dotnet/dotnet publish
make DOTNET=/tmp/imewl-dotnet/dotnet check
```

- Debug 构建、Release 静态发布、baseline 和原 CLI 构建成功。
- 重新执行 9 个原生 CLI 转换，与迁移前保存的实际浏览器下载产物逐条比较，词条、编码和可解析词频均一致。SCEL 随机元数据采用语义比较。
- 重新执行 19 项原生高级检查，已知 Big5 内容错误仍为 `correct:false`，未宣称全部内容正确。
- 所有 Python 脚本通过语法解析，所有 Chromium `.mjs` 脚本通过 `node --check`。
- 通过普通 Python 静态 HTTP 服务读取发布首页、`poc.js` 和 `blazor.webassembly.js`，均为 HTTP 200；发布目录包含实际 WASM 文件。
- `git diff --check` 通过，子模块工作区干净。

本次详细构建日志、原生高级检查和转换对照 JSON 位于忽略的 `artifacts/verification/`。`make check` 可重新生成原生对照结果。

本次没有重新执行浏览器完整运行矩阵和 1/10/50 MB 性能测试；相关结论仍来自 `poc/wasm/reports/` 的迁移前证据。静态 HTTP 检查不等同于浏览器运行测试。

发布仍使用预构建解释 WASM runtime，未验证 AOT/native relink。保留 CodePages 冗余包引用的 NU1510、上游生成器的 CS8632，以及缺少可选 wasm-tools 的发布提示。

# imewlconverter-wasm

基于深蓝词库转换引擎制作 .NET 10 WebAssembly，供纯浏览器本地词库转换使用。转换过程不依赖后端，不上传词库文件。

## 获取与构建

```sh
git clone --recurse-submodules https://github.com/hocgin/imewlconverter-wasm.git
cd imewlconverter-wasm
make publish
make serve
```

需要 .NET 10 SDK 和 Python 3。已有克隆先执行 `make init`。浏览器访问 <http://127.0.0.1:8765>；静态部署目录为 `artifacts/publish/wwwroot`。可通过 `make DOTNET=/path/to/dotnet publish` 指定 SDK。

## 目录

- `upstream/imewlconverter/`：[上游仓库](https://github.com/studyzy/imewlconverter)的 Git 子模块，固定为兼容性验证时的 `501a1b77d46187e0b5072f8a27550fa77454c7d1`，不修改引擎源码。
- `poc/wasm/`：从 `imewlconverter-web/poc/wasm` 迁移的 Blazor WASM 宿主、内存流适配及原生对照程序。
- `poc/wasm/scripts/`：转换对照、性能测量及浏览器复现脚本。
- `poc/wasm/reports/`：原验证报告和原始证据，保留历史路径和测量时间。

详见 [PoC 使用说明](poc/wasm/README.md)、[兼容性报告](poc/wasm/reports/compatibility.md)和[性能报告](poc/wasm/reports/performance.md)。目前仍是验证宿主；大文件会占用较多内存、阻塞主线程，Big5 导入存在已记录的上游内容错误。

## 验证与更新

`make build` 验证 Debug 构建，`make check` 构建原生基线和上游 CLI 并执行对照。高级检查包含已知 Big5 内容错误，请检查输出中的 `correct`，不能只检查进程退出状态。浏览器复现方式见 PoC 说明。

`make check` 将本次结果写入 `artifacts/verification/`，与已保留的浏览器产物比较，不覆盖历史报告。本次迁移的构建与对照结果见 [迁移验证记录](MIGRATION.md)。

更新上游时，在子模块中检出所需提交，重新构建和回归后记录新的子模块提交。仓库不依赖原 `imewlconverter-web` 目录；原目录保留用于核对迁移。

继承上游 GPL-3.0 许可，见 [LICENSE](LICENSE)。第三方测试语料来源与哈希保留在报告中。

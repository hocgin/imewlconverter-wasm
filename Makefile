DOTNET ?= dotnet
PYTHON ?= python3
PROJECT := poc/wasm/WasmPoc.csproj
export DOTNET
PUBLISH := $(CURDIR)/artifacts/publish

.PHONY: init build publish serve baseline cli check
init:
	git submodule update --init --recursive

build:
	$(DOTNET) build $(PROJECT) -c Debug

publish:
	$(DOTNET) publish $(PROJECT) -c Release -o "$(PUBLISH)"

serve:
	$(PYTHON) -m http.server 8765 --bind 127.0.0.1 --directory "$(PUBLISH)/wwwroot"

baseline:
	$(DOTNET) build poc/wasm/baseline/Baseline.csproj -c Release

cli:
	$(DOTNET) build upstream/imewlconverter/src/ImeWlConverterCmd -c Release

check: baseline cli
	mkdir -p artifacts/verification
	cp poc/wasm/reports/browser-* artifacts/verification/
	$(DOTNET) poc/wasm/baseline/bin/Release/net10.0/Baseline.dll > artifacts/verification/native-advanced.json
	POC_REPORT_DIR="$(CURDIR)/artifacts/verification" $(PYTHON) poc/wasm/scripts/cli-matrix.py

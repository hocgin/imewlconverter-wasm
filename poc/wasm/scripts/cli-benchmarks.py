from pathlib import Path
import subprocess,json,time,hashlib,re,os,shutil
root=Path(__file__).resolve().parents[3];poc=root/'poc/wasm';rows=[];dotnet=os.environ.get('DOTNET') or shutil.which('dotnet') or '/tmp/imewl-dotnet/dotnet'
for mb in [1,10,50]:
 src=poc/f'artifacts/fixtures/real-{mb}MB.dict.yaml';out=poc/f'reports/cli-bench-{mb}MB.dict.yaml'
 cmd=['/usr/bin/time','-l',dotnet,str(root/'upstream/imewlconverter/src/ImeWlConverterCmd/bin/Release/net10.0/ImeWlConverterCmd.dll'),'-i','rime','-o','rime','-t','pinyin','-O',str(out),'--json',str(src)]
 start=time.perf_counter();p=subprocess.run(cmd,text=True,capture_output=True);elapsed=(time.perf_counter()-start)*1000
 (poc/f'reports/cli-bench-{mb}MB.stderr').write_text(p.stderr);(poc/f'reports/cli-bench-{mb}MB.json').write_text(p.stdout)
 rss=re.search(r'(\d+)\s+maximum resident set size',p.stderr)
 rows.append({'mb':mb,'wallMsIncludingProcessStartup':elapsed,'maxRSSBytes':int(rss[1]) if rss else None,'exitCode':p.returncode,'outputSHA256':hashlib.sha256(out.read_bytes()).hexdigest() if out.exists() else None})
(poc/'reports/cli-performance.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))

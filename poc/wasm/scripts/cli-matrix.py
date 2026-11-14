from pathlib import Path
import subprocess,json,hashlib,collections,os,shutil
root=Path(__file__).resolve().parents[3];out=Path(os.environ.get('POC_REPORT_DIR', str(root/'poc/wasm/reports')));out.mkdir(parents=True,exist_ok=True);dotnet=os.environ.get('DOTNET') or shutil.which('dotnet') or '/tmp/imewl-dotnet/dotnet';cli=root/'upstream/imewlconverter/src/ImeWlConverterCmd/bin/Release/net10.0/ImeWlConverterCmd.dll';baseline=root/'poc/wasm/baseline/bin/Release/net10.0/Baseline.dll';test=root/'upstream/imewlconverter/src/ImeWlConverterCoreTest/Test'
cases=[('scel-rime','scel','rime',test/'唐诗300首【官方推荐】.scel','.dict.yaml'),('rime-scel','rime','scel',test/'rime_luna_pinyin_export.txt','.scel'),('scel-word','scel','word',test/'唐诗300首【官方推荐】.scel','.txt'),('word-rime','word','rime',test/'纯汉字.txt','.dict.yaml'),('gboard-rime','gboard','rime',test/'GBoard_dictionary.txt','.dict.yaml'),('rime-gboard','rime','gboard',test/'rime_luna_pinyin_export.txt','.txt'),('gboardbin-rime','gboardbin','rime',test/'gboard_user_dict.dict','.dict.yaml'),('rime-gboardbin','rime','gboardbin',test/'rime_luna_pinyin_export.txt','.dict'),('qpyd-rime','qpyd','rime',test/'成语.qpyd','.dict.yaml')]
report=[]
for name,frm,to,source,ext in cases:
 dest=out/('cli-'+name+ext);args=[dotnet,str(cli),'-i',frm,'-o',to,'-O',str(dest),'--json',str(source)]
 r=subprocess.run(args,text=True,capture_output=True);(out/('cli-'+name+'.json')).write_text(r.stdout);(out/('cli-'+name+'.stderr')).write_text(r.stderr)
 browser=out/('browser-'+name+ext)
 row={'name':name,'command':args,'exitCode':r.returncode}
 if r.returncode==0 and browser.exists():
  row['byteEqual']=dest.read_bytes()==browser.read_bytes()
  # Canonical import removes random binary metadata, preserving words, codes and parsed frequencies.
  a=subprocess.check_output([dotnet,str(baseline),'canonical',to,str(dest)],text=True);b=subprocess.check_output([dotnet,str(baseline),'canonical',to,str(browser)],text=True)
  ja=json.loads(a);jb=json.loads(b);row.update(semanticEqual=ja==jb,cliEntries=len(ja),browserEntries=len(jb))
  if ja!=jb:
   row['cliFirst']=ja[:5];row['browserFirst']=jb[:5]
 report.append(row)
(out/'conversion-comparison.json').write_text(json.dumps(report,indent=2,ensure_ascii=False));print(json.dumps(report,indent=2,ensure_ascii=False))
if not all(row.get('semanticEqual') is True for row in report):
 raise SystemExit('Conversion comparison failed or browser reference output is missing')

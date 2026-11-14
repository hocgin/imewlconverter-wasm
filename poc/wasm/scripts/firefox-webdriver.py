from pathlib import Path
import urllib.request,urllib.error,json,time,hashlib,os
root=Path(__file__).resolve().parents[3];baseline_reports=root/'poc/wasm/reports';reports=Path(os.environ.get('POC_REPORT_DIR',str(baseline_reports)));reports.mkdir(parents=True,exist_ok=True);download=reports/'firefox-downloads';download.mkdir(exist_ok=True)
def marker(case,phase):
 path=os.environ.get('POC_MEMORY_MARKER')
 if path:
  f=Path(path);tmp=f.with_suffix('.tmp');tmp.write_text(json.dumps({'case':case,'phase':phase}));tmp.replace(f)
def request(method,path,data=None):
 req=urllib.request.Request(os.environ.get('WEBDRIVER_URL','http://localhost:4446')+path,data=json.dumps(data).encode() if data is not None else None,method=method,headers={'Content-Type':'application/json'})
 try:
  with urllib.request.urlopen(req,timeout=240) as r:return json.load(r)['value']
 except urllib.error.HTTPError as e:raise RuntimeError(e.read().decode())
cap={'capabilities':{'alwaysMatch':{'browserName':'firefox','moz:firefoxOptions':{'binary':os.environ.get('FIREFOX_BINARY','/tmp/imewl-firefox/Firefox.app/Contents/MacOS/firefox'),'args':['-headless'],'prefs':{'browser.download.folderList':2,'browser.download.dir':str(download),'browser.download.useDownloadDir':True,'browser.helperApps.neverAsk.saveToDisk':'application/octet-stream','pdfjs.disabled':True}}}}}
session=request('POST','/session',cap);sid=session['sessionId'];prefix='/session/'+sid
(reports/'firefox-capabilities.json').write_text(json.dumps(session,indent=2))
def js(script,args=[]):return request('POST',prefix+'/execute/sync',{'script':script,'args':args})
def wait(script,timeout=180):
 start=time.monotonic()
 while time.monotonic()-start<timeout:
  try:
   value=js(script)
   if value:return value
  except Exception:pass
  time.sleep(.15)
 raise TimeoutError(script)
def load():
 request('POST',prefix+'/url',{'url':'http://127.0.0.1:8765/'});wait('return !!document.querySelector("#initialized")');return js('return pocMetrics()')
def convert(files,frm,to,code='NoCode'):
 el=request('POST',prefix+'/element',{'using':'css selector','value':'input[type=file]'})['element-6066-11e4-a52e-4f735466cecf']
 request('POST',prefix+'/element/'+el+'/value',{'text':'\n'.join(map(str,files))})
 js('for(const [id,value] of Object.entries(arguments[0])){const e=document.getElementById(id);e.value=value;e.dispatchEvent(new Event("change",{bubbles:true}));}',[{'input-format':frm,'output-format':to,'code':code}])
 js('pocResetPerf();document.querySelector("#convert").click()')
 wait('return !!document.querySelector("#result").textContent || !!document.querySelector("#errors").textContent')
 r=js('return {result:document.querySelector("#result").textContent,error:document.querySelector("#errors").textContent,metrics:pocMetrics()}')
 return r
try:
 marker('initial','load');initial=load();(reports/'firefox-initial.json').write_text(json.dumps(initial,indent=2))
 marker('SCEL','convert_and_download');r=convert([root/'upstream/imewlconverter/src/ImeWlConverterCoreTest/Test/唐诗300首【官方推荐】.scel'],'scel','rime');(reports/'firefox-scel-rime.json').write_text(json.dumps(r,indent=2));print('SCEL',r)
 dest=download/'converted.dict.yaml';dest.unlink(missing_ok=True);js('document.querySelector("#download").click()');start=time.monotonic()
 while not dest.exists() and time.monotonic()-start<30:time.sleep(.1)
 compare={'downloaded':dest.exists(),'equalToCLI':dest.exists() and dest.read_bytes()==(baseline_reports/'cli-scel-rime.dict.yaml').read_bytes()};(reports/'firefox-download-comparison.json').write_text(json.dumps(compare,indent=2))
 marker('advanced','checks');js('document.querySelector("#advanced").click()');wait('return document.querySelector("#progress").textContent==="Advanced complete"');r=js('return {result:document.querySelector("#result").textContent,error:document.querySelector("#errors").textContent,metrics:pocMetrics()}');(reports/'firefox-advanced.json').write_text(json.dumps(r,indent=2));print('advanced recorded')
 for mb in [1,10,50]:
  marker(f'{mb}MB','load');load();marker(f'{mb}MB','convert_and_download');start=time.monotonic();r=convert([root/f'poc/wasm/artifacts/fixtures/real-{mb}MB.dict.yaml'],'rime','rime','Pinyin');r['wallMs']=(time.monotonic()-start)*1000;r['mb']=mb
  if not r['error']:
   dest.unlink(missing_ok=True);js('document.querySelector("#download").click()');start=time.monotonic()
   expected=json.loads(r['result'])['outputBytes']
   while (not dest.exists() or dest.stat().st_size!=expected) and time.monotonic()-start<120:time.sleep(.1)
   r['outputSHA256']=hashlib.sha256(dest.read_bytes()).hexdigest();r['equalToCLI']=dest.read_bytes()==(baseline_reports/f'cli-bench-{mb}MB.dict.yaml').read_bytes()
  (reports/f'firefox-bench-{mb}MB.json').write_text(json.dumps(r,indent=2));print('bench',mb,r)
finally:
 marker('cleanup','close');request('DELETE',prefix)

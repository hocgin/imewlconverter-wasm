"""Sample a dedicated Firefox browser's PID subtree RSS; no unrelated browser processes.
Run on macOS with Firefox/geckodriver paths as used by firefox-webdriver.py.
RSS is summed across processes and includes shared-page double counting, not physical footprint.
"""
from pathlib import Path
import subprocess,json,time,os,csv,urllib.request
root=Path(__file__).resolve().parents[3];reports=root/'poc/wasm/reports/firefox-memory';reports.mkdir(exist_ok=True)
(reports/'firefox-capabilities.json').unlink(missing_ok=True)
marker=reports/'phase.json';marker.write_text(json.dumps({'case':'startup','phase':'startup'}))
driver_log=(reports/'driver.log').open('w');run_log=(reports/'run.log').open('w')
driver=subprocess.Popen([os.environ.get('GECKODRIVER','/tmp/imewl-geckodriver/geckodriver'),'--port','4447'],stdout=driver_log,stderr=subprocess.STDOUT,start_new_session=True)
run=None;peaks={};rows=[];gaps=[];started=time.monotonic();last_sample=None;browser_pid=None
try:
 for attempt in range(100):
  try:
   urllib.request.urlopen('http://localhost:4447/status',timeout=1).close();break
  except Exception:
   if driver.poll() is not None:raise RuntimeError('geckodriver exited; see driver.log')
   time.sleep(.1)
 else:raise TimeoutError('geckodriver status unavailable')
 env=dict(os.environ,WEBDRIVER_URL='http://localhost:4447',POC_REPORT_DIR=str(reports),POC_MEMORY_MARKER=str(marker),PYTHONUNBUFFERED='1')
 run=subprocess.Popen(['python3',str(root/'poc/wasm/scripts/firefox-webdriver.py')],env=env,stdout=run_log,stderr=subprocess.STDOUT)
 while run.poll() is None:
  if browser_pid is None:
   cap=reports/'firefox-capabilities.json'
   if cap.exists():
    try:browser_pid=json.loads(cap.read_text())['capabilities']['moz:processID']
    except (ValueError,KeyError):pass
  if browser_pid is not None:
   table={}
   for line in subprocess.check_output(['ps','-axo','pid=,ppid=,rss='],text=True).splitlines():
    fields=line.split()
    if len(fields)==3:pid,ppid,rss=map(int,fields);table[pid]=(ppid,rss)
   descendants={browser_pid};changed=True
   while changed:
    added={pid for pid,(ppid,rss) in table.items() if ppid in descendants and pid not in descendants};changed=bool(added);descendants.update(added)
   now=time.monotonic()
   if last_sample is not None:gaps.append((now-last_sample)*1000)
   last_sample=now;phase=json.loads(marker.read_text());rss=sum(table[pid][1]*1024 for pid in descendants if pid in table)
   row={'elapsedMs':(now-started)*1000,**phase,'browserPID':browser_pid,'processCount':sum(pid in table for pid in descendants),'summedRSSBytes':rss,'rootRSSBytes':table.get(browser_pid,(0,0))[1]*1024}
   rows.append(row)
   key=phase['case']+'/'+phase['phase']
   if rss>peaks.get(key,{}).get('summedRSSBytes',-1):peaks[key]=row
  time.sleep(.1)
 exit_code=run.wait()
 summary={'exitCode':exit_code,'samplingTargetMs':100,'actualMeanIntervalMs':sum(gaps)/len(gaps) if gaps else None,'maxIntervalMs':max(gaps) if gaps else None,'browserPID':browser_pid,'samples':len(rows),'scope':'one new temporary Firefox profile, browser PID plus current OS PPID descendants; geckodriver and unrelated apps excluded','metric':'sampled sum of per-process RSS, shared pages may be counted more than once; not unique physical footprint or exact continuous peak','peaks':peaks}
 (reports/'summary.json').write_text(json.dumps(summary,indent=2))
 with (reports/'samples.csv').open('w') as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]) if rows else ['elapsedMs']);writer.writeheader();writer.writerows(rows)
 print(json.dumps(summary,indent=2))
 if exit_code:raise RuntimeError('Firefox verification failed; inspect run.log')
finally:
 if run and run.poll() is None:run.terminate();run.wait(timeout=10)
 driver.terminate()
 try:driver.wait(timeout=10)
 except subprocess.TimeoutExpired:driver.kill();driver.wait()
 driver_log.close();run_log.close()

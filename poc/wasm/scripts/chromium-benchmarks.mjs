const fs=await import('node:fs/promises'),crypto=await import('node:crypto');
const root=process.env.IMEWL_ROOT || process.cwd(),out=root+'/poc/wasm/reports',p=(await taskSpace(Number(process.env.EGO_TASK_SPACE_ID || (() => { throw new Error('Set EGO_TASK_SPACE_ID to your current Ego TaskSpace ID'); })()))).page('p1');
const rows=[];
for(const mb of [1,10,50]){
 // Fresh navigation per file so each linear-memory high-water belongs to one conversion.
 await p.reload();await p.waitForSelector('#initialized');
 const source=root+'/poc/wasm/artifacts/fixtures/real-'+mb+'MB.dict.yaml';
 await p.setInputFiles('input[type=file]',[source]);await p.selectOption('#input-format','rime');await p.selectOption('#output-format','rime');await p.selectOption('#code','Pinyin');
 await p.evaluate(()=>pocResetPerf());const start=Date.now();await p.click('#convert');
 await p.waitForFunction(()=>!!document.querySelector('#result').textContent||!!document.querySelector('#errors').textContent,undefined,{timeout:240000});
 const r=await p.evaluate(()=>({result:document.querySelector('#result').textContent,error:document.querySelector('#errors').textContent,metrics:pocMetrics()}));r.mb=mb;r.wallMs=Date.now()-start;
 if(!r.error){const promise=p.waitForEvent('download',{timeout:120000});await p.click('#download');const d=await promise;await d.saveAs(out+'/browser-bench-'+mb+'MB.dict.yaml');const data=await fs.readFile(out+'/browser-bench-'+mb+'MB.dict.yaml');r.outputSHA256=crypto.createHash('sha256').update(data).digest('hex');}
 await fs.writeFile(out+'/chromium-bench-'+mb+'MB.json',JSON.stringify(r,null,2));rows.push(r);console.log(r);
}

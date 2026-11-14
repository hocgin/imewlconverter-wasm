const fs=await import('node:fs/promises');const root=process.env.IMEWL_ROOT || process.cwd(),out=root+'/poc/wasm/reports';const p=(await taskSpace(Number(process.env.EGO_TASK_SPACE_ID || (() => { throw new Error('Set EGO_TASK_SPACE_ID to your current Ego TaskSpace ID'); })()))).page('p1');
await p.reload();await p.waitForSelector('#initialized');
// Gboard shortcuts are UserDefine codes. Match CLI's inferred pinyin generation explicitly.
await p.setInputFiles('input[type=file]',[root+'/upstream/imewlconverter/src/ImeWlConverterCoreTest/Test/GBoard_dictionary.txt']);await p.selectOption('#input-format','gboard');await p.selectOption('#output-format','rime');await p.selectOption('#code','Pinyin');
await p.click('#convert');await p.waitForFunction(()=>!!document.querySelector('#result').textContent,undefined,{timeout:60000});
let r=await p.evaluate(()=>({result:document.querySelector('#result').textContent,error:document.querySelector('#errors').textContent,metrics:pocMetrics()}));
await fs.writeFile(out+'/chromium-gboard-rime.json',JSON.stringify(r,null,2));let promise=p.waitForEvent('download');await p.click('#download');let d=await promise;await d.saveAs(out+'/browser-gboard-rime.dict.yaml');console.log(r);
await p.setInputFiles('input[type=file]',[root+'/upstream/imewlconverter/src/ImeWlConverterCoreTest/Test/唐诗300首【官方推荐】.scel',root+'/upstream/imewlconverter/src/ImeWlConverterCoreTest/Test/诗词名句大全.scel']);await p.selectOption('#input-format','scel');await p.selectOption('#code','NoCode');await p.evaluate(()=>pocResetPerf());
await p.click('#convert');await p.waitForFunction(()=>{const s=document.querySelector('#result').textContent;return s&&JSON.parse(s).from==='scel'&&!document.querySelector('#convert').disabled;},undefined,{timeout:120000});
r=await p.evaluate(()=>({result:document.querySelector('#result').textContent,error:document.querySelector('#errors').textContent,metrics:pocMetrics()}));
await fs.writeFile(out+'/chromium-multifile.json',JSON.stringify(r,null,2));promise=p.waitForEvent('download');await p.click('#download');d=await promise;await d.saveAs(out+'/browser-multifile.dict.yaml');console.log(r);

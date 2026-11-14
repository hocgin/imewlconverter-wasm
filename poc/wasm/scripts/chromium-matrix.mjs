// Run with: ego-browser nodejs < this-file (update root and space ID for a new checkout/session).
const fs=await import('node:fs/promises');
const root=process.env.IMEWL_ROOT || process.cwd(),out=root+'/poc/wasm/reports';
const p=(await taskSpace(Number(process.env.EGO_TASK_SPACE_ID || (() => { throw new Error('Set EGO_TASK_SPACE_ID to your current Ego TaskSpace ID'); })()))).page('p1');
await p.reload();await p.waitForSelector('#initialized');
const cases=[
 ['scel-rime','scel','rime',root+'/upstream/imewlconverter/src/ImeWlConverterCoreTest/Test/唐诗300首【官方推荐】.scel','NoCode','.dict.yaml'],
 ['rime-scel','rime','scel',root+'/upstream/imewlconverter/src/ImeWlConverterCoreTest/Test/rime_luna_pinyin_export.txt','NoCode','.scel'],
 ['scel-word','scel','word',root+'/upstream/imewlconverter/src/ImeWlConverterCoreTest/Test/唐诗300首【官方推荐】.scel','NoCode','.txt'],
 ['word-rime','word','rime',root+'/upstream/imewlconverter/src/ImeWlConverterCoreTest/Test/纯汉字.txt','Pinyin','.dict.yaml'],
 ['gboard-rime','gboard','rime',root+'/upstream/imewlconverter/src/ImeWlConverterCoreTest/Test/GBoard_dictionary.txt','Pinyin','.dict.yaml'],
 ['rime-gboard','rime','gboard',root+'/upstream/imewlconverter/src/ImeWlConverterCoreTest/Test/rime_luna_pinyin_export.txt','NoCode','.txt'],
 ['gboardbin-rime','gboardbin','rime',root+'/upstream/imewlconverter/src/ImeWlConverterCoreTest/Test/gboard_user_dict.dict','NoCode','.dict.yaml'],
 ['rime-gboardbin','rime','gboardbin',root+'/upstream/imewlconverter/src/ImeWlConverterCoreTest/Test/rime_luna_pinyin_export.txt','NoCode','.dict'],
 ['qpyd-rime','qpyd','rime',root+'/upstream/imewlconverter/src/ImeWlConverterCoreTest/Test/成语.qpyd','NoCode','.dict.yaml']
];
for(const [name,from,to,file,code,extension] of cases){
 await p.setInputFiles('input[type=file]',[file]);await p.selectOption('#input-format',from);await p.selectOption('#output-format',to);await p.selectOption('#code',code);
 await p.click('#convert');await p.waitForFunction(({from,to})=>{const s=document.querySelector('#result').textContent;return document.querySelector('#errors').textContent || (s && JSON.parse(s).from===from && JSON.parse(s).to===to && !document.querySelector('#convert').disabled);},{from,to},{timeout:120000});
 const r=await p.evaluate(()=>({result:document.querySelector('#result').textContent,error:document.querySelector('#errors').textContent,metrics:pocMetrics()}));
 await fs.writeFile(out+'/chromium-'+name+'.json',JSON.stringify(r,null,2));
 if(r.error){console.log({name,error:r.error});continue;}
 const promise=p.waitForEvent('download');await p.click('#download');const download=await promise;await download.saveAs(out+'/browser-'+name+extension);
 const parsed=JSON.parse(r.result);delete parsed.preview;console.log({name,result:parsed});
}
await p.click('#advanced');await p.waitForFunction(()=>document.querySelector('#progress').textContent==='Advanced complete',undefined,{timeout:60000});
await fs.writeFile(out+'/chromium-advanced.json',JSON.stringify(await p.evaluate(()=>({result:document.querySelector('#result').textContent,error:document.querySelector('#errors').textContent,metrics:pocMetrics()})),null,2));

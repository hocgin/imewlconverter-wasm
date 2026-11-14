// Diagnostic instrumentation: linear memory committed high-water, not total browser RSS.
window.pocLongTasks=[];
try{new PerformanceObserver(list=>{for(const e of list.getEntries())pocLongTasks.push(e.duration);}).observe({type:'longtask',buffered:true});}catch{}
window.pocResetPerf=()=>{pocLongTasks.length=0;};
window.pocErrors=[];
addEventListener('error',e=>pocErrors.push(String(e.error||e.message)));
addEventListener('unhandledrejection',e=>pocErrors.push(String(e.reason)));
window.pocReady=()=>{window.pocLoadMs=performance.now();};
window.pocDownload=async(name,reference)=>{
 const data=await reference.arrayBuffer(); const url=URL.createObjectURL(new Blob([data]));
 const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),10000);
};
window.pocMetrics=()=>({loadMs:window.pocLoadMs,resourceBytes:performance.getEntriesByType('resource').reduce((s,r)=>s+r.encodedBodySize,0),userAgent:navigator.userAgent,errors:pocErrors,jsHeap:performance.memory?.usedJSHeapSize??null,wasmLinearBytes:typeof getDotnetRuntime==="function"?getDotnetRuntime(0).Module.HEAPU8.byteLength:null,longTaskCount:pocLongTasks.length,maxLongTaskMs:pocLongTasks.length?Math.max(...pocLongTasks):0});

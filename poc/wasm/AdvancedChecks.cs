using System.Text;
using System.Text.Json;
using ImeWlConverter.Abstractions.Enums;
using ImeWlConverter.Abstractions.Options;
using ImeWlConverter.Abstractions.Models;
namespace WasmPoc;
public static class AdvancedChecks
{
 public static async Task<string> Run(StreamConverter c)
 {
  var rows=new List<object>();
  async Task Check(string name,Func<Task<object>> run){try{rows.Add(new{name,status="executed",detail=await run()});}catch(Exception ex){rows.Add(new{name,status="failed",error=ex.ToString()});}}
  static void Assert(bool condition,string message){if(!condition)throw new Exception(message);}
  static MemoryStream Input(string s)=>new(Encoding.UTF8.GetBytes(s));
  static string Text(ConversionOutput r)=>Encoding.UTF8.GetString(r.Data);
  var defaults=new ConversionOptions();
  await Check("merge_filter_rank_progress",async()=>{
   var messages=new List<string>();var p=new InlineProgress(x=>messages.Add(x.Message??""));
   var r=await c.ConvertAsync([Input("中国\tzhong guo\t99\n"),Input("中文\tzhong wen\t0\n英文a\tying wen\t5\n")],"rime","rime",defaults,new(){WordLengthTo=2},p);
   Assert(r.Imported==3&&r.Exported==2&&Text(r).Contains("中国\tzhong guo\t99")&&Text(r).Contains("中文\tzhong wen\t1")&&messages.Count>0,"merge/filter/rank/progress mismatch");
   return new{r.Imported,r.Exported,output=Text(r),messages,duplicatePolicy="concatenation; no automatic deduplication"};
  });
  foreach(var code in new[]{CodeType.Pinyin,CodeType.Wubi86})await Check("generate_"+code,async()=>{
   var r=await c.ConvertAsync([Input("中国\n中文\n")],"word","rime",new(){CodeGeneration=new(){TargetCodeType=code}});
   Assert(r.Exported==2&&!Text(r).Contains("\t\t"),"missing codes");
   Assert(code==CodeType.Pinyin?Text(r).Contains("zhong guo"):Text(r).Contains("中国\tkh"),"unexpected code");return new{output=Text(r)};
  });
  foreach(var mode in new[]{ChineseConversionMode.SimplifiedToTraditional,ChineseConversionMode.TraditionalToSimplified})await Check("Chinese_"+mode,async()=>{
   var simplified=mode==ChineseConversionMode.SimplifiedToTraditional;
   var r=await c.ConvertAsync([Input((simplified?"中国":"中國")+"\tzhong guo\t12\n")],"rime","rime",new(){ChineseConversion=mode});
   Assert(Text(r).Contains(simplified?"中國":"中国"),"Chinese conversion mismatch");return new{output=Text(r)};
  });
  foreach(var name in new[]{"GBK","GB2312","Big5","UTF-8"})await Check("encoding_provider_"+name,()=>{
   var e=Encoding.GetEncoding(name);var value=name=="Big5"?"中國詞庫":"中国词库";var bytes=e.GetBytes(value);Assert(e.GetString(bytes)==value,"encoding roundtrip");return Task.FromResult<object>(new{hex=Convert.ToHexString(bytes),value});
  });
  foreach(var name in new[]{"GBK","GB2312","Big5","UTF-8"})await Check("word_import_"+name,async()=>{
   var expected=name=="Big5"?"中國":"中国";using var stream=new MemoryStream(Encoding.GetEncoding(name).GetBytes(expected+"\n"));
   var r=await c.Importers.Single(x=>x.Metadata.Id=="word").ImportAsync(stream,new(){EncodingName=name});
   return new{expected,actual=r.Entries.FirstOrDefault()?.Word,correct=r.Entries.FirstOrDefault()?.Word==expected};
  });
  foreach(var id in new[]{"scel","gboardbin","libimebin"})await Check("binary_roundtrip_"+id,async()=>{
   var r=await c.ConvertAsync([Input("中国\tzhong guo\t99\n中文\tzhong wen\t12\n")],"rime",id,defaults);
   using var stream=new MemoryStream(r.Data);var back=await c.Importers.Single(x=>x.Metadata.Id==id).ImportAsync(stream);
   Assert(back.Entries.Count==2&&back.Entries.Any(x=>x.Word=="中国")&&back.Entries.Any(x=>x.Word=="中文"),"binary roundtrip mismatch");
   return new{bytes=r.Data.Length,words=back.Entries.Select(x=>new{x.Word,code=x.Code?.GetPrimaryCode(" "),x.Rank})};
  });
  await Check("pre_cancelled_token",async()=>{
   using var ct=new CancellationTokenSource();ct.Cancel();try{await c.ConvertAsync([Input("中国\n")],"word","rime",defaults,ct:ct.Token);}catch(OperationCanceledException){return new{cancelled=true,scope="before import only; not mid-SCEL/UI cancellation"};}throw new Exception("ignored cancellation");
  });
  await Check("SharpZipLib",()=>{
   var bytes=Encoding.UTF8.GetBytes("真实压缩测试 中国词库");using var ms=new MemoryStream();
   using(var zip=new ICSharpCode.SharpZipLib.Zip.ZipOutputStream(ms)){zip.IsStreamOwner=false;zip.PutNextEntry(new("dict.txt"));zip.Write(bytes);zip.CloseEntry();zip.Finish();}
   ms.Position=0;using var input=new ICSharpCode.SharpZipLib.Zip.ZipInputStream(ms);input.GetNextEntry();using var output=new MemoryStream();input.CopyTo(output);Assert(bytes.SequenceEqual(output.ToArray()),"zip mismatch");return Task.FromResult<object>(new{bytes=ms.Length});
  });
  await Check("UTF.Unknown_stream",()=>{
   using var input=Input("中国词库转换技术验证，中文编码探测。中国词库转换技术验证，中文编码探测。");
   var detected=UtfUnknown.CharsetDetector.DetectFromStream(input);var name=detected.Detected?.EncodingName;
   Assert(name?.Contains("utf",StringComparison.OrdinalIgnoreCase)==true,"UTF-8 detection failed: "+name);return Task.FromResult<object>(new{encoding=name});
  });
  return JsonSerializer.Serialize(rows,new JsonSerializerOptions{WriteIndented=true});
 }
 private sealed class InlineProgress(Action<ProgressInfo> action):IProgress<ProgressInfo>{public void Report(ProgressInfo value)=>action(value);}
}
